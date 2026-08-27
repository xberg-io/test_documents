#!/usr/bin/env python3
"""Fetch the math corpus binaries from their original sources.

The binary formats that carry mathematics are gitignored, like every other
corpus binary, so they cannot travel in a pull request. This script downloads
them from the sources recorded in `MATH_PROVENANCE.md` and writes each one to
the repository path it belongs at.

Run it once, then publish the bytes the usual way:

    python3 scripts/fetch_math_binaries.py
    python3 scripts/publish_corpus.py --bucket xberg-test-documents

`publish_corpus.py` scans the working tree, so the files have to be in place
before it runs. It writes `corpus.lock.json` itself.

Every entry carries the sha256 of the file this corpus was validated against.
A download whose digest does not match is written to `<path>.mismatch` and
reported, rather than replacing a good file with a source that has changed.
"""

from __future__ import annotations

import argparse
import functools
import json
import sys
from pathlib import Path
from typing import Any

from corpus_tools import paths
from corpus_tools.http import SOURCE_FILE_TIMEOUT_SECONDS, UrllibTransport, get
from corpus_tools.materialize import materialize_one
from corpus_tools.pool import add_jobs_argument, run_parallel

REPO_ROOT = paths.REPO_ROOT
MANIFEST = Path(__file__).resolve().parent / "data" / "math-binaries.json"


TRANSPORT = UrllibTransport()


def fetch_one(path: str, entry: dict[str, Any], force: bool) -> tuple[str, str]:
    """Return (path, status). Status is ok, skipped, mismatch or an error."""
    status = materialize_one(
        REPO_ROOT / path,
        entry["sha256"],
        lambda: get(entry["url"], timeout=SOURCE_FILE_TIMEOUT_SECONDS, transport=TRANSPORT),
        force=force,
    )
    return path, status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_jobs_argument(parser)
    parser.add_argument("--force", action="store_true", help="re-download files that already match")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    counts: dict[str, int] = {}
    problems: list[str] = []

    calls = [functools.partial(fetch_one, path, entry, args.force) for path, entry in sorted(manifest.items())]
    for path, status in run_parallel(calls, jobs=args.jobs):
        key = status.split()[0]
        counts[key] = counts.get(key, 0) + 1
        if key in {"error", "mismatch"}:
            problems.append(f"  {path}: {status}")

    print(f"{len(manifest)} binaries: " + ", ".join(f"{n} {k}" for k, n in sorted(counts.items())))
    if problems:
        print("\nNeeds attention:", file=sys.stderr)
        print("\n".join(problems), file=sys.stderr)
        print(
            "\nA source that moved or changed needs its entry in scripts/data/math-binaries.json updated,"
            "\nand MATH_PROVENANCE.md updated with it.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
