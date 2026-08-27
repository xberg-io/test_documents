#!/usr/bin/env python3
"""Publish corpus binaries to the public GCS bucket.

The corpus binaries are not in git: they are working-tree files matched by
scripts/data/corpus-patterns.txt and ignored by .gitignore. This script hashes
their real content, writes corpus.lock.json, and uploads each unique object
once to gs://<bucket>/objects/<sha256>. Safe to re-run: existing objects are
skipped, and the lock file is byte-identical across runs when nothing in the
corpus changed.

Run it locally after adding or changing a fixture, then commit the refreshed
corpus.lock.json. CI cannot do this: a checkout contains no binaries at all.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Protocol

MANIFEST_SCHEMA_VERSION = 1
MANIFEST_FILENAME = "corpus.lock.json"
PATTERNS_FILENAME = "scripts/data/corpus-patterns.txt"
OBJECTS_PREFIX = "objects"
EXTRA_ROOT_FILES = (
    "ATTRIBUTIONS.md",
    "LICENSES.md",
    "ground_truth/corpus_manifest.json",
)
# ~keep: license-restricted corpus cache and local agent state must never reach the public bucket
FORBIDDEN_PREFIXES = (".corpus-cache/", ".basemind/")
# ~keep Pruned from the walk so a forbidden or irrelevant tree is never even considered; the
# FORBIDDEN_PREFIXES guard still runs afterwards as the check that actually fails the publish.
SKIPPED_DIRECTORIES = frozenset({".corpus-cache", ".basemind", ".github", "__pycache__", ".pytest_cache"})
READ_CHUNK_SIZE = 1024 * 1024
BYTES_PER_MIB = 1024 * 1024
STAGING_DIR_PREFIX = ".corpus-publish-staging-"
# ~keep Bounds the argv of a single `gcloud storage cp`; gcloud parallelises within one invocation.
UPLOAD_BATCH_SIZE = 250
# ~keep Outside OBJECTS_PREFIX and EXTRA_ROOT_FILES, so the probe can never shadow a corpus key.
WRITE_PROBE_KEY = "_write-probe/last-publish.txt"


class GuardViolation(RuntimeError):
    """Raised when a forbidden path would be included in the publish set."""


class CorpusFileTracked(RuntimeError):
    """Raised when a file matching a corpus pattern has been committed to git."""


class EmptyCorpus(RuntimeError):
    """Raised when enumeration yields no objects at all."""


class WriteProbeFailed(RuntimeError):
    """Raised when the credentials in use cannot demonstrably write to the bucket."""


@dataclass(frozen=True)
class CorpusObject:
    path: str
    sha256: str
    size: int


class StorageBackend(Protocol):
    def existing_keys(self, prefix: str) -> set[str]: ...

    def matches_remote(self, local_path: Path, key: str) -> bool: ...

    def upload(self, local_path: Path, key: str) -> None: ...

    def upload_directory(self, local_directory: Path, key_prefix: str) -> None: ...

    def read_text(self, key: str) -> str | None: ...


class GCloudStorageBackend:
    """Shells out to `gcloud storage`; avoids a hard dependency on google-cloud-storage."""

    def __init__(self, bucket: str) -> None:
        self.bucket = bucket

    def _uri(self, key: str) -> str:
        return f"gs://{self.bucket}/{key}"

    def existing_keys(self, prefix: str) -> set[str]:
        # ~keep One listing for the whole prefix rather than `objects describe` per object: each
        # gcloud invocation costs ~1.5s of interpreter startup, which dominated the 489-object
        # publish far more than the 570 MiB of actual transfer did.
        result = subprocess.run(
            ["gcloud", "storage", "ls", f"{self._uri(prefix)}/**"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return set()
        bucket_uri = f"gs://{self.bucket}/"
        return {line[len(bucket_uri) :] for line in result.stdout.split() if line.startswith(bucket_uri)}

    def matches_remote(self, local_path: Path, key: str) -> bool:
        """Compare by GCS's own md5, so an unchanged file is never rewritten."""
        result = subprocess.run(
            ["gcloud", "storage", "objects", "describe", self._uri(key), "--format=value(md5_hash)"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return False
        remote_md5 = result.stdout.strip()
        if not remote_md5:
            return False
        digest = hashlib.md5(local_path.read_bytes(), usedforsecurity=False).digest()
        local_md5 = base64.b64encode(digest).decode()
        return remote_md5 == local_md5

    def upload(self, local_path: Path, key: str) -> None:
        subprocess.run(["gcloud", "storage", "cp", str(local_path), self._uri(key)], check=True)

    def upload_directory(self, local_directory: Path, key_prefix: str) -> None:
        # ~keep Explicit source list, never `cp --recursive <dir>`: recursive copy appends the source
        # directory's own name to the destination, so the objects would land under
        # objects/<staging-dir-name>/<sha256>. Naming each file puts it at objects/<sha256>.
        sources = sorted(local_directory.iterdir())
        for start in range(0, len(sources), UPLOAD_BATCH_SIZE):
            batch = sources[start : start + UPLOAD_BATCH_SIZE]
            subprocess.run(
                ["gcloud", "storage", "cp", *(str(path) for path in batch), f"{self._uri(key_prefix)}/"],
                check=True,
            )

    def read_text(self, key: str) -> str | None:
        result = subprocess.run(
            ["gcloud", "storage", "cat", self._uri(key)],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout if result.returncode == 0 else None


class LocalDirBackend:
    """Copies into a local directory tree; a fake bucket for tests, never a real endpoint."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def matches_remote(self, local_path: Path, key: str) -> bool:
        destination = self.root / key
        return destination.is_file() and destination.read_bytes() == local_path.read_bytes()

    def existing_keys(self, prefix: str) -> set[str]:
        base = self.root / prefix
        if not base.is_dir():
            return set()
        return {str(path.relative_to(self.root)) for path in base.rglob("*") if path.is_file()}

    def upload(self, local_path: Path, key: str) -> None:
        destination = self.root / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(local_path.read_bytes())

    def upload_directory(self, local_directory: Path, key_prefix: str) -> None:
        for source in sorted(local_directory.iterdir()):
            self.upload(source, f"{key_prefix}/{source.name}")

    def read_text(self, key: str) -> str | None:
        destination = self.root / key
        return destination.read_text() if destination.is_file() else None


def repo_root() -> Path:
    output = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], check=True, capture_output=True, text=True
    ).stdout.strip()
    return Path(output)


def load_patterns(root: Path) -> list[str]:
    text = (root / PATTERNS_FILENAME).read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]


def matches_corpus_pattern(rel_path: str, patterns: list[str]) -> bool:
    # ~keep gitattributes/gitignore semantics, which these patterns were lifted from: a pattern
    # containing '/' is anchored to the repo root, one without matches a basename at any depth.
    basename = rel_path.rsplit("/", 1)[-1]
    return any(fnmatch(rel_path, p) if "/" in p else fnmatch(basename, p) for p in patterns)


def corpus_paths(root: Path, patterns: list[str]) -> list[str]:
    """The publish set: working-tree files matching a corpus pattern.

    ~keep Walks the working tree rather than asking git, because these files are deliberately
    untracked — they live in the bucket, and .gitignore keeps them out of the repo.
    """
    found: list[str] = []
    for directory, subdirectories, filenames in os.walk(root):
        subdirectories[:] = [
            name
            for name in subdirectories
            if name != ".git" and not name.startswith(STAGING_DIR_PREFIX) and name not in SKIPPED_DIRECTORIES
        ]
        base = Path(directory).relative_to(root)
        for filename in filenames:
            rel_path = str(base / filename) if str(base) != "." else filename
            if matches_corpus_pattern(rel_path, patterns):
                found.append(rel_path)
    # ~keep An empty result means the corpus was never materialised (a bare checkout, a bad cwd),
    # not that it is genuinely empty. Without this the run would write an empty corpus.lock.json
    # and unpin every consumer from every object.
    if not found:
        raise EmptyCorpus(
            f"no working-tree file matched any pattern in {PATTERNS_FILENAME}; refusing to publish an "
            "empty manifest. Fetch the corpus first, or check that the patterns still describe it."
        )
    return sorted(found)


def guard_against_tracked_corpus_files(root: Path, paths: list[str]) -> None:
    """The corpus must stay out of git; a tracked match means a binary was committed by mistake."""
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--", *paths],
        capture_output=True,
        text=True,
        check=False,
    )
    tracked = sorted(line for line in result.stdout.splitlines() if line)
    if tracked:
        raise CorpusFileTracked(
            "corpus file(s) are tracked in git and must be removed from the index: " + ", ".join(tracked[:10])
        )


def guard_against_forbidden_paths(paths: list[str]) -> None:
    offenders = [path for path in paths if any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)]
    if offenders:
        raise GuardViolation("refusing to run: forbidden path(s) would be included: " + ", ".join(offenders))


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(READ_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_objects(root: Path, paths: list[str]) -> list[CorpusObject]:
    """Hash real working-tree bytes — the only source of truth for what gets published."""
    objects = []
    for rel_path in paths:
        full_path = root / rel_path
        if not full_path.is_file():
            raise FileNotFoundError(f"corpus path has no content on disk: {rel_path}")
        objects.append(CorpusObject(path=rel_path, sha256=sha256_of(full_path), size=full_path.stat().st_size))
    return objects


def build_manifest(objects: list[CorpusObject]) -> dict:
    ordered_objects = {
        obj.path: {"sha256": obj.sha256, "size": obj.size} for obj in sorted(objects, key=lambda o: o.path)
    }
    return {"schema": MANIFEST_SCHEMA_VERSION, "objects": ordered_objects}


def write_manifest(manifest: dict, destination: Path) -> None:
    text = json.dumps(manifest, indent=2) + "\n"
    destination.write_text(text, encoding="utf-8")


def unique_objects_by_sha256(objects: list[CorpusObject]) -> dict[str, CorpusObject]:
    representatives: dict[str, CorpusObject] = {}
    for obj in objects:
        representatives.setdefault(obj.sha256, obj)
    return representatives


@contextmanager
def staged_by_sha256(root: Path, objects: dict[str, CorpusObject]) -> Iterator[Path]:
    """Flat directory of the given objects named by sha256, so one recursive copy uploads them all.

    Entries are hardlinks where the filesystem allows it, so staging 570 MiB costs no disk. The
    directory is created under `root` to keep the link target on the same device.
    """
    with tempfile.TemporaryDirectory(dir=root, prefix=STAGING_DIR_PREFIX) as staging_name:
        staging = Path(staging_name)
        for sha256, obj in objects.items():
            source = root / obj.path
            destination = staging / sha256
            try:
                os.link(source, destination)
            except OSError:
                shutil.copyfile(source, destination)
        yield staging


def upload_unique_objects(
    root: Path, backend: StorageBackend, representatives: dict[str, CorpusObject], *, dry_run: bool
) -> tuple[list[str], list[str]]:
    """Returns (uploaded, skipped) sha256 lists. In dry-run mode nothing is checked or uploaded."""
    if dry_run:
        return sorted(representatives), []

    present = backend.existing_keys(OBJECTS_PREFIX)
    missing = {sha256: obj for sha256, obj in representatives.items() if f"{OBJECTS_PREFIX}/{sha256}" not in present}
    skipped = sorted(sha256 for sha256 in representatives if sha256 not in missing)
    if not missing:
        return [], skipped

    with staged_by_sha256(root, missing) as staging:
        backend.upload_directory(staging, OBJECTS_PREFIX)
    return sorted(missing), skipped


def upload_extra_files(root: Path, backend: StorageBackend, *, dry_run: bool) -> tuple[list[str], list[str]]:
    """Returns (uploaded, unchanged) keys.

    Unlike objects/, these keys are mutable — a licence notice can genuinely change — so they are
    compared by content rather than by mere presence. Rewriting an identical file would churn a new
    object version on every run for no benefit.
    """
    uploaded: list[str] = []
    unchanged: list[str] = []
    for rel_path in EXTRA_ROOT_FILES:
        full_path = root / rel_path
        if not full_path.is_file():
            raise FileNotFoundError(f"required attribution file missing: {rel_path}")
        key = Path(rel_path).name
        if dry_run:
            uploaded.append(key)
            continue
        if backend.matches_remote(full_path, key):
            unchanged.append(key)
            continue
        backend.upload(full_path, key)
        uploaded.append(key)
    return uploaded, unchanged


def format_mib(size_bytes: int) -> str:
    return f"{size_bytes / BYTES_PER_MIB:.2f}"


def verify_write_access(backend: StorageBackend) -> str:
    """Write a freshly-tokened probe object and read it back, proving this run can actually write.

    ~keep A publish in which every object is already present uploads nothing, so a green run would
    otherwise say nothing about whether these credentials can write at all — the next real corpus
    change would be the first thing to ever exercise the write path, and would discover a broken
    one at the worst moment. The token is generated per run, so a probe left behind by an earlier
    run can never satisfy the read-back.
    """
    token = secrets.token_hex(16)
    payload = f"{token} run={os.environ.get('GITHUB_RUN_ID', 'local')}\n"

    with tempfile.TemporaryDirectory() as staging:
        probe = Path(staging) / "probe.txt"
        probe.write_text(payload)
        try:
            backend.upload(probe, WRITE_PROBE_KEY)
        except subprocess.CalledProcessError as error:
            raise WriteProbeFailed(f"could not write {WRITE_PROBE_KEY}: {error}") from error

    read_back = backend.read_text(WRITE_PROBE_KEY)
    if read_back is None:
        raise WriteProbeFailed(f"wrote {WRITE_PROBE_KEY} but could not read it back")
    if read_back.strip() != payload.strip():
        raise WriteProbeFailed(f"{WRITE_PROBE_KEY} read back as {read_back.strip()!r}, expected {payload.strip()!r}")
    return token


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", help="GCS bucket name, without the gs:// prefix")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be uploaded; performs no network calls and uploads nothing",
    )
    args = parser.parse_args(argv)
    if not args.dry_run and not args.bucket:
        parser.error("--bucket is required unless --dry-run is given")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = repo_root()

    paths = corpus_paths(root, load_patterns(root))
    guard_against_forbidden_paths(paths + list(EXTRA_ROOT_FILES))
    guard_against_tracked_corpus_files(root, paths)

    objects = resolve_objects(root, paths)
    representatives = unique_objects_by_sha256(objects)
    manifest = build_manifest(objects)

    total_size = sum(obj.size for obj in objects)
    print(f"{len(objects)} paths / {len(representatives)} unique objects / {format_mib(total_size)} MiB")

    # ~keep The manifest write stays behind this branch: --dry-run promises to change nothing, and
    # corpus.lock.json is load-bearing (consumers hash it to key their fetch cache).
    if args.dry_run:
        print(
            f"dry-run: would upload {len(representatives)} unique object(s) and {len(EXTRA_ROOT_FILES)} attribution file(s)"
        )
        print("dry-run: no bucket contacted, nothing uploaded, corpus.lock.json untouched")
        return 0

    write_manifest(manifest, root / MANIFEST_FILENAME)

    backend = GCloudStorageBackend(args.bucket)
    probe_token = verify_write_access(backend)
    print(f"write probe: wrote and read back {WRITE_PROBE_KEY} (token {probe_token[:8]})")

    uploaded, skipped = upload_unique_objects(root, backend, representatives, dry_run=False)
    print(f"objects: uploaded {len(uploaded)}, already present {len(skipped)}")

    extra_uploaded, extra_unchanged = upload_extra_files(root, backend, dry_run=False)
    print(f"attribution files: uploaded {len(extra_uploaded)}, unchanged {len(extra_unchanged)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
