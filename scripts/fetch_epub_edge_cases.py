#!/usr/bin/env python3
"""Fetch or build the EPUB edge-case corpus.

`EPUB_EDGE_CASES.md` lists one or more EPUB files for each defect that
xberg-io/xberg pull request #1498 fixes. The bytes are gitignored like every
other corpus binary, so this script puts each file at the repository path it
belongs at, from the source that `scripts/data/epub-edge-cases.json` records:

- `url`: a published file, downloaded as is.
- `members`: an EPUB that the source publishes as an unpacked directory (the
  epubcheck test suite). Each member is downloaded from a pinned commit and the
  container is written by `build_epub_edge_cases.pack`, so the result is
  deterministic.
- `generated`: a synthesized file from `scripts/build_epub_edge_cases.py`.

Every entry carries the sha256 and size of the file the corpus was validated
against. A result whose digest does not match is written to `<path>.mismatch`
and reported, rather than replacing a good file. Publish the bytes the usual
way afterwards:

    python3 scripts/fetch_epub_edge_cases.py
    python3 scripts/publish_corpus.py --bucket xberg-test-documents
"""

import argparse
import functools
import json
import sys
from pathlib import Path
from typing import Any

import build_epub_edge_cases
from corpus_tools import paths
from corpus_tools.http import SOURCE_FILE_TIMEOUT_SECONDS, UrllibTransport, get
from corpus_tools.materialize import materialize_one
from corpus_tools.pool import add_jobs_argument, run_parallel

REPO_ROOT = paths.REPO_ROOT
MANIFEST = Path(__file__).resolve().parent / "data" / "epub-edge-cases.json"


TRANSPORT = UrllibTransport()


def fetch(url: str) -> bytes:
    return get(url, timeout=SOURCE_FILE_TIMEOUT_SECONDS, transport=TRANSPORT)


def materialize(path: str, entry: dict[str, Any], generated: dict[str, bytes]) -> bytes:
    if "url" in entry:
        return fetch(entry["url"])
    if "members" in entry:
        members = [(name, fetch(url)) for name, url in entry["members"].items() if name != "mimetype"]
        return build_epub_edge_cases.pack(members)
    if entry.get("generated"):
        return generated[path]
    raise ValueError(f"{path}: entry has no url, members or generated source")


def fetch_one(path: str, entry: dict[str, Any], force: bool, generated: dict[str, bytes]) -> tuple[str, str]:
    """Return (path, status). Status is ok, skipped, mismatch or an error."""
    status = materialize_one(
        REPO_ROOT / path,
        entry["sha256"],
        lambda: materialize(path, entry, generated),
        force=force,
    )
    return path, status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_jobs_argument(parser)
    parser.add_argument("--force", action="store_true", help="rewrite files that already match")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    generated = build_epub_edge_cases.build_all()
    counts: dict[str, int] = {}
    problems: list[str] = []

    calls = [
        functools.partial(fetch_one, path, entry, args.force, generated) for path, entry in sorted(manifest.items())
    ]
    for path, status in run_parallel(calls, jobs=args.jobs):
        key = status.split()[0]
        counts[key] = counts.get(key, 0) + 1
        if key in {"error", "mismatch"}:
            problems.append(f"  {path}: {status}")

    print(f"{len(manifest)} files: " + ", ".join(f"{n} {k}" for k, n in sorted(counts.items())))
    if problems:
        print("\nNeeds attention:", file=sys.stderr)
        print("\n".join(problems), file=sys.stderr)
        print(
            "\nA source that moved or changed needs its entry in scripts/data/epub-edge-cases.json updated,"
            "\nand EPUB_EDGE_CASES.md updated with it.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
