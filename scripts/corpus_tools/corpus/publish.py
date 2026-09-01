"""Enumerating the publish set, guarding it, and getting it into the bucket.

~keep The guards here are not defensive programming. The public bucket is world-readable and its
objects cannot be recalled once served, and corpus patterns use gitignore semantics — a bare
`*.zip` matches a basename at ANY depth — so a root aimed one level too high sweeps in whatever
lives beside the corpus. Both failures are silent and both are permanent.
"""

import argparse
import os
import secrets
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from corpus_tools.corpus.backends import StorageBackend
from corpus_tools.hashing import BYTES_PER_MIB
from corpus_tools.manifest import DEFAULT_BUCKET, MANIFEST_FILENAME, OBJECTS_PREFIX, CorpusObject, lock_objects
from corpus_tools.paths import git_repo_root
from corpus_tools.patterns import PATTERNS_FILENAME, matches_corpus_pattern

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
# ~keep Outside OBJECTS_PREFIX and EXTRA_ROOT_FILES, so the probe can never shadow a corpus key.
WRITE_PROBE_KEY = "_write-probe/last-publish.txt"
# ~keep Enough dropped paths to recognise which fixture family went missing without burying the
# remedy at the end of a thousand-line refusal.
DROPPED_PATHS_SHOWN = 10


class GuardViolation(RuntimeError):
    """Raised when a forbidden path would be included in the publish set."""


class CorpusFileTracked(RuntimeError):
    """Raised when a file matching a corpus pattern has been committed to git."""


class EmptyCorpus(RuntimeError):
    """Raised when enumeration yields no objects at all."""


class WriteProbeFailed(RuntimeError):
    """Raised when the credentials in use cannot demonstrably write to the bucket."""


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


def guard_against_dropping_manifest_paths(
    manifest_path: Path, manifest: dict[str, Any], *, allow_removals: bool
) -> None:
    """Refuse a publish that would unpin paths the existing lock file still holds.

    ~keep The manifest is rebuilt from whatever the working tree happens to hold, and a corpus
    checkout is routinely partial -- several fixture families are materialised by their own fetch
    script, so publishing before they are present silently deletes their entries and every consumer
    stops seeing those fixtures. Nothing else catches it: the objects stay in the bucket, the run
    reports success, and the loss is a deletion buried in a thousand-line JSON diff. Re-run
    `python3 scripts/fetch_corpus.py` first, or pass --allow-removals for a deliberate removal.
    """
    if allow_removals or not manifest_path.exists():
        return
    try:
        existing = set(lock_objects(manifest_path))
    except (OSError, ValueError, KeyError):
        # ~keep An unreadable or malformed lock file is not something this guard can reason about,
        # and refusing here would block the very publish that repairs it.
        return
    dropped = sorted(existing - set(manifest["objects"]))
    if not dropped:
        return
    shown = "\n".join(f"  {rel_path}" for rel_path in dropped[:DROPPED_PATHS_SHOWN])
    remainder = len(dropped) - DROPPED_PATHS_SHOWN
    if remainder > 0:
        shown += f"\n  ... and {remainder} more"
    raise PublishTargetRefused(
        f"refusing to publish: {len(dropped)} path(s) in {manifest_path.name} are missing from the "
        f"working tree, so this run would unpin them for every consumer:\n{shown}\n"
        "Run `python3 scripts/fetch_corpus.py` to materialise them, or pass --allow-removals if "
        "the removal is deliberate."
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
