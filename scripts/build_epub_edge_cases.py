#!/usr/bin/env python3
"""Build the synthesized EPUB edge cases.

Each file reproduces one defect that xberg-io/xberg pull request #1498 fixes,
for a case that no public EPUB exhibits. `EPUB_EDGE_CASES.md` records which
cases those are and why. Every other file in that corpus is a published
document fetched by `scripts/fetch_epub_edge_cases.py`.

The output is deterministic: every ZIP member is stored uncompressed with a
fixed timestamp, so the same source always yields the same sha256, and
`scripts/data/epub-edge-cases.json` can pin the bytes. `scripts/tests/test_epub_edge_cases.py`
checks that pin against a fresh build.

    python3 scripts/build_epub_edge_cases.py            # write every file
    python3 scripts/build_epub_edge_cases.py --list     # print path and sha256
"""

import argparse
import sys

from corpus_tools.epub.build import REPO_ROOT, build_all
from corpus_tools.hashing import sha256_bytes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list", action="store_true", help="print path, size and sha256 without writing")
    args = parser.parse_args(argv)
    for path, data in build_all().items():
        digest = sha256_bytes(data)
        if args.list:
            print(f"{path}\t{len(data)}\t{digest}")
            continue
        target = REPO_ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(f"wrote {path} ({len(data)} bytes, {digest[:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
