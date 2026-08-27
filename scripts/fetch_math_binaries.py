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
import urllib.request
from pathlib import Path

from corpus_tools import paths
from corpus_tools.hashing import sha256_bytes, sha256_file
from corpus_tools.pool import add_jobs_argument, run_parallel

REPO_ROOT = paths.REPO_ROOT
MANIFEST = Path(__file__).resolve().parent / "data" / "math-binaries.json"
TIMEOUT = 120
RETRIES = 3


def fetch_one(path: str, entry: dict, force: bool) -> tuple[str, str]:
    """Return (path, status). Status is ok, skipped, mismatch or an error."""
    target = REPO_ROOT / path
    if target.exists() and not force:
        digest = sha256_file(target)
        if digest == entry["sha256"]:
            return path, "skipped"

    last_error = ""
    for attempt in range(1, RETRIES + 1):
        try:
            request = urllib.request.Request(entry["url"], headers={"User-Agent": "xberg-test-documents"})
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                payload = response.read()
            break
        except Exception as error:  # noqa: BLE001 - any failure is worth one more try
            last_error = f"{type(error).__name__}: {error}"
            if attempt == RETRIES:
                return path, f"error {last_error}"
    else:  # pragma: no cover - the loop always breaks or returns
        return path, f"error {last_error}"

    digest = sha256_bytes(payload)
    target.parent.mkdir(parents=True, exist_ok=True)
    if digest != entry["sha256"]:
        (target.with_suffix(target.suffix + ".mismatch")).write_bytes(payload)
        return path, f"mismatch got {digest[:12]} want {entry['sha256'][:12]}"

    target.write_bytes(payload)
    return path, "ok"


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
