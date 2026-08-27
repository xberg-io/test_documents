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

import argparse
import base64
import hashlib
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol

from corpus_tools.hashing import BYTES_PER_MIB
from corpus_tools.manifest import (
    DEFAULT_BUCKET,
    MANIFEST_FILENAME,
    OBJECTS_PREFIX,
    CorpusObject,
    build_manifest,
    resolve_objects,
    unique_objects_by_sha256,
    write_manifest,
)
from corpus_tools.paths import git_repo_root
from corpus_tools.patterns import PATTERNS_FILENAME, load_patterns, matches_corpus_pattern

EXTRA_ROOT_FILES = (
    "ATTRIBUTIONS.md",
    "LICENSES.md",
    "ground_truth/corpus_manifest.json",
)
# ~keep: license-restricted corpus cache, local agent state and the dev virtualenv must never
# reach the public bucket. .venv/ is here because the patterns are gitignore-shaped: a pattern
# without '/' matches a basename at any depth, and a virtualenv ships .png/.pdf/.zip assets inside
# installed packages. Pruning it below is the first line; this is the check that fails the publish.
FORBIDDEN_PREFIXES = (".corpus-cache/", ".basemind/", ".venv/")
# ~keep Pruned from the walk so a forbidden or irrelevant tree is never even considered; the
# FORBIDDEN_PREFIXES guard still runs afterwards as the check that actually fails the publish.
SKIPPED_DIRECTORIES = frozenset(
    {".corpus-cache", ".basemind", ".github", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv"}
)
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


def corpus_paths(root: Path, patterns: list[str], patterns_source: str | Path = PATTERNS_FILENAME) -> list[str]:
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
            f"no working-tree file matched any pattern in {patterns_source}; refusing to publish an "
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


class PublishTargetRefused(RuntimeError):
    """Raised when the requested root/manifest/bucket combination is not safe to publish."""


def resolve_targets(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    """Work out (root, manifest, patterns), defaulting to this repository.

    ~keep All three default to today's values, so `publish_corpus.py --bucket xberg-test-documents`
    behaves exactly as before. Only a caller that passes one of the flags gets anything new.
    """
    root = args.root.resolve() if args.root else git_repo_root()
    manifest = args.manifest.resolve() if args.manifest else root / MANIFEST_FILENAME
    patterns = args.patterns.resolve() if args.patterns else root / PATTERNS_FILENAME
    return root, manifest, patterns


def guard_against_publishing_private_corpus_publicly(
    root: Path, manifest: Path, patterns: Path, bucket: str | None
) -> None:
    """Refuse a non-default root, manifest OR pattern file aimed at the public bucket.

    ~keep The public bucket is world-readable and its objects cannot be recalled once served, so
    this fails loudly rather than being caught in review. All THREE targets are checked, not just
    the root: the pattern file selects the byte set as directly as the root does, so
    `--patterns /tmp/everything.txt` containing `*` would otherwise sweep the whole working tree
    into a world-readable bucket while root and manifest still looked like the defaults.
    """
    if bucket != DEFAULT_BUCKET:
        return
    repository_root = git_repo_root()
    for label, actual, expected in (
        ("--root", root, repository_root),
        ("--manifest", manifest, repository_root / MANIFEST_FILENAME),
        ("--patterns", patterns, repository_root / PATTERNS_FILENAME),
    ):
        if actual != expected:
            raise PublishTargetRefused(
                f"refusing to publish with {label} {actual} to the public bucket {DEFAULT_BUCKET}. "
                f"That bucket serves {repository_root} anonymously to the whole internet, and "
                f"{label} selects a different corpus than the one it is meant to serve."
            )


def guard_against_root_outside_the_corpus(root: Path, explicit_targets: list[Path], *, allow_external: bool) -> None:
    """Refuse a --root that sits above where the explicitly-named targets say the corpus is.

    ~keep This catches aiming one level too high. Corpus patterns use gitignore semantics, so a
    bare `*.zip` matches a basename at ANY depth: a root above the corpus silently sweeps in
    whatever else lives beside it, and publishing is not reversible.

    Comparing root against the MANIFEST's directory was a tautology. resolve_targets derives the
    manifest from the root when --manifest is omitted, so manifest.parent == root by construction
    and the check could not fire in the very case it existed for. What actually pins down where
    the corpus lives is whichever paths the caller named explicitly: if they all sit inside one
    subdirectory of root, that subdirectory is the corpus and root is too high.
    """
    if allow_external or not explicit_targets:
        return
    parents = {target.parent for target in explicit_targets}
    if len(parents) != 1:
        return
    corpus_directory = parents.pop()
    if corpus_directory == root or root not in corpus_directory.parents:
        return
    raise PublishTargetRefused(
        f"--root {root} sits above the corpus, which the paths you named put at {corpus_directory}. "
        "Corpus patterns match basenames at any depth, so a root above the corpus can sweep in "
        f"unrelated files. Use --root {corpus_directory}, or pass --allow-external-root if this "
        "is deliberate."
    )


def describe_publish_set(root: Path, paths: list[str], objects: list[CorpusObject]) -> str:
    """A summary a human can sanity-check at a glance before anything is uploaded."""
    extensions: dict[str, int] = {}
    for rel_path in paths:
        suffix = Path(rel_path).suffix.lower().lstrip(".") or "(none)"
        extensions[suffix] = extensions.get(suffix, 0) + 1
    top = sorted(extensions.items(), key=lambda item: (-item[1], item[0]))[:8]
    total = sum(obj.size for obj in objects)
    return (
        f"  root       {root}\n"
        f"  files      {len(paths)}\n"
        f"  bytes      {total} ({format_mib(total)} MiB)\n"
        f"  extensions {', '.join(f'{name} {count}' for name, count in top)}"
    )


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bucket", help="GCS bucket name, without the gs:// prefix")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be uploaded; performs no network calls and uploads nothing",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="corpus root to enumerate (default: this repository)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help=f"where to write the lock file (default: <root>/{MANIFEST_FILENAME})",
    )
    parser.add_argument(
        "--patterns",
        type=Path,
        default=None,
        help=f"pattern file selecting corpus paths (default: <root>/{PATTERNS_FILENAME})",
    )
    parser.add_argument(
        "--allow-external-root",
        action="store_true",
        help="permit a --root that is not the manifest's own directory",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="skip the confirmation prompt shown before publishing a non-default root",
    )
    args = parser.parse_args(argv)
    if not args.dry_run and not args.bucket:
        parser.error("--bucket is required unless --dry-run is given")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root, manifest_path, patterns_path = resolve_targets(args)

    # ~keep Compare RESOLVED targets, not which flags were typed. `--root .` from the repo root is
    # semantically the default, and keying off `args.root is None` would silently drop both the
    # tracked-corpus guard and the attribution refresh for a command that means exactly the same
    # thing as passing no flags at all.
    try:
        repository_root: Path | None = git_repo_root()
    except subprocess.CalledProcessError:
        repository_root = None
    is_default_root = (
        repository_root is not None
        and root == repository_root
        and manifest_path == repository_root / MANIFEST_FILENAME
        and patterns_path == repository_root / PATTERNS_FILENAME
    )

    # ~keep A refusal here is a designed outcome, not a crash. Print the reason and exit 1 rather
    # than showing a traceback, so the message a maintainer needs is the whole output.
    try:
        guard_against_publishing_private_corpus_publicly(root, manifest_path, patterns_path, args.bucket)
        explicit_targets = [target.resolve() for target in (args.manifest, args.patterns) if target is not None]
        guard_against_root_outside_the_corpus(root, explicit_targets, allow_external=args.allow_external_root)
    except PublishTargetRefused as refusal:
        print(f"refused: {refusal}", file=sys.stderr)
        return 1

    paths = corpus_paths(root, load_patterns(root, patterns_path), patterns_path)
    # ~keep The attribution files are THIS repository's licence notices, and they sit beside its
    # corpus rather than inside it. A corpus root elsewhere has its own provenance kept with its own
    # manifest, so requiring them there would fail a publish after 15 GB was already uploaded.
    extra_files = list(EXTRA_ROOT_FILES) if is_default_root else []
    guard_against_forbidden_paths(paths + extra_files)
    if is_default_root:
        # ~keep Only meaningful for this repository, where corpus binaries are deliberately
        # untracked. A corpus root outside a git working tree has nothing to ask git about.
        guard_against_tracked_corpus_files(root, paths)

    objects = resolve_objects(root, paths)
    representatives = unique_objects_by_sha256(objects)
    manifest = build_manifest(objects)

    total_size = sum(obj.size for obj in objects)
    print(f"{len(objects)} paths / {len(representatives)} unique objects / {format_mib(total_size)} MiB")

    if not is_default_root:
        # ~keep A count and a byte total are the two numbers that make a wrongly aimed root obvious at
        # a glance. An exit code does not distinguish 4,412 files from 4,419.
        print("publishing a non-default corpus root:")
        print(describe_publish_set(root, paths, objects))
        print(f"  manifest   {manifest_path}")
        print(f"  patterns   {patterns_path}")
        print(f"  bucket     {args.bucket or '(dry run)'}")
        if not args.dry_run and not args.yes and not _confirmed():
            print("aborted; nothing was uploaded", file=sys.stderr)
            return 1

    # ~keep The manifest write stays behind this branch: --dry-run promises to change nothing, and
    # corpus.lock.json is load-bearing (consumers hash it to key their fetch cache).
    if args.dry_run:
        print(
            f"dry-run: would upload {len(representatives)} unique object(s) and {len(extra_files)} attribution file(s)"
        )
        print(f"dry-run: no bucket contacted, nothing uploaded, {manifest_path.name} untouched")
        return 0

    write_manifest(manifest, manifest_path)

    backend = GCloudStorageBackend(args.bucket)
    probe_token = verify_write_access(backend)
    print(f"write probe: wrote and read back {WRITE_PROBE_KEY} (token {probe_token[:8]})")

    uploaded, skipped = upload_unique_objects(root, backend, representatives, dry_run=False)
    print(f"objects: uploaded {len(uploaded)}, already present {len(skipped)}")

    if extra_files:
        extra_uploaded, extra_unchanged = upload_extra_files(root, backend, dry_run=False)
        print(f"attribution files: uploaded {len(extra_uploaded)}, unchanged {len(extra_unchanged)}")

    return 0


def _confirmed() -> bool:
    """~keep Interactive by design; --yes is the non-interactive path for scripted publishes."""
    try:
        answer = input("proceed? [y/N] ").strip().lower()
    except EOFError:
        return False
    return answer in {"y", "yes"}


if __name__ == "__main__":
    sys.exit(main())
