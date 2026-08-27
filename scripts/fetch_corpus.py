#!/usr/bin/env python3
"""Materialise corpus binaries from the public bucket into their working-tree paths.

The local counterpart of the xberg-io/actions/fetch-test-documents CI action: same manifest,
same anonymous HTTPS, no credentials or SDK. Needed because several consumers pull fixtures in
with include_bytes!/include_str!, so the files must exist on disk before `cargo build` runs.

    python3 scripts/fetch_corpus.py                      # everything
    python3 scripts/fetch_corpus.py --include 'pdf/**'   # just the PDFs

Already-correct files are left alone, so re-running costs one hash per file and no network.
"""

import argparse
import sys
from pathlib import Path

from corpus_tools.hashing import BYTES_PER_MIB, sha256_bytes, sha256_file
from corpus_tools.http import (
    BUCKET_OBJECT_TIMEOUT_SECONDS,
    DEFAULT_RETRY,
    AdcCredential,
    CurlTransport,
    HttpError,
    RetryPolicy,
    Transport,
    get,
)
from corpus_tools.manifest import DEFAULT_BUCKET, MANIFEST_FILENAME, lock_objects, object_url
from corpus_tools.paths import REPO_ROOT
from corpus_tools.patterns import matches_any
from corpus_tools.pool import add_jobs_argument, map_parallel

MAX_REPORTED_FAILURES = 20


def fetch_one(
    bucket: str,
    root: Path,
    rel_path: str,
    sha256: str,
    *,
    transport: Transport | None = None,
    retry: RetryPolicy = DEFAULT_RETRY,
) -> str | None:
    """Materialise one object. transport/retry are injectable so tests need no network or backoff."""
    destination = root / rel_path
    if destination.is_file() and sha256_file(destination) == sha256:
        return None

    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        payload = get(
            object_url(bucket, sha256),
            timeout=BUCKET_OBJECT_TIMEOUT_SECONDS,
            transport=transport if transport is not None else CurlTransport(),
            retry=retry,
        )
    except HttpError as error:
        return f"{rel_path}: {error.reason}"

    actual = sha256_bytes(payload)
    if actual != sha256:
        return f"{rel_path}: expected {sha256} but bucket served {actual}"
    destination.write_bytes(payload)
    return None


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", default=DEFAULT_BUCKET, help="GCS bucket name, without gs://")
    add_jobs_argument(parser)
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="glob matched against manifest paths; repeatable. Defaults to everything.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help=f"lock file to read (default: <repo>/{MANIFEST_FILENAME})",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="where to materialise files (default: this repository)",
    )
    parser.add_argument(
        "--auth",
        action="store_true",
        help="authenticate with Application Default Credentials, for a private bucket",
    )
    return parser.parse_args(argv)


def build_transport(args: argparse.Namespace) -> CurlTransport:
    """~keep Anonymous unless --auth. Extracted so the choice is testable without a network."""
    return CurlTransport(credential=AdcCredential()) if args.auth else CurlTransport()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # ~keep Both default to this repository, so `python3 scripts/fetch_corpus.py` with no flags is
    # byte-for-byte the command ~14 places in the xberg repo tell people to run.
    root = args.root.resolve() if args.root else REPO_ROOT
    manifest_path = args.manifest.resolve() if args.manifest else REPO_ROOT / MANIFEST_FILENAME
    transport = build_transport(args)
    objects = lock_objects(manifest_path)
    wanted = {
        rel_path: entry["sha256"]
        for rel_path, entry in objects.items()
        if not args.include or matches_any(rel_path, args.include)
    }
    if not wanted:
        print(f"no path in {manifest_path} matched {args.include}", file=sys.stderr)
        return 1

    total_bytes = sum(objects[rel_path]["size"] for rel_path in wanted)
    print(f"fetching {len(wanted)} path(s) / {total_bytes / BYTES_PER_MIB:.1f} MiB into {root}")

    failures: list[str] = []
    results = map_parallel(
        lambda item: fetch_one(args.bucket, root, *item, transport=transport),
        wanted.items(),
        jobs=args.jobs,
    )
    failures = [failure for failure in results if failure is not None]

    print(f"{len(wanted) - len(failures)}/{len(wanted)} present")
    for failure in failures[:MAX_REPORTED_FAILURES]:
        print(f"  {failure}", file=sys.stderr)
    if len(failures) > MAX_REPORTED_FAILURES:
        print(f"  ... and {len(failures) - MAX_REPORTED_FAILURES} more", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
