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
import subprocess
import sys
from pathlib import Path

from corpus_tools.corpus.backends import GCloudStorageBackend
from corpus_tools.corpus.publish import (
    EXTRA_ROOT_FILES,
    WRITE_PROBE_KEY,
    PublishTargetRefused,
    corpus_paths,
    describe_publish_set,
    format_mib,
    guard_against_forbidden_paths,
    guard_against_publishing_private_corpus_publicly,
    guard_against_root_outside_the_corpus,
    guard_against_tracked_corpus_files,
    resolve_targets,
    upload_extra_files,
    upload_unique_objects,
    verify_write_access,
)
from corpus_tools.manifest import (
    MANIFEST_FILENAME,
    build_manifest,
    resolve_objects,
    unique_objects_by_sha256,
    write_manifest,
)
from corpus_tools.paths import git_repo_root
from corpus_tools.patterns import PATTERNS_FILENAME, load_patterns


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
