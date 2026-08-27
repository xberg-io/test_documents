#!/usr/bin/env python3
"""Remove the answer from a rendered SVG, leaving a geometry-only fixture behind.

    python3 scripts/strip_svg_graph_metadata.py parent.svg geometry.svg

The full specification of what is removed and what is deliberately preserved lives in the
docstring of corpus_tools/diagrams/svg_metadata.py, and is printed by --help below.
"""

import argparse
import sys
from pathlib import Path

from corpus_tools.diagrams import svg_metadata
from corpus_tools.diagrams.svg_metadata import strip, with_trailing_newline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=svg_metadata.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("source", type=Path, help="the rendered SVG to strip")
    parser.add_argument("destination", type=Path, help="where to write the geometry-only fixture")
    args = parser.parse_args(argv)

    original = args.source.read_text(encoding="utf-8")
    stripped = strip(original)
    # ~keep Refuse to write a geometry fixture identical to its parent. diagrams/README.md
    # regenerates the whole set in a bare shell loop, so silently writing a byte-identical copy
    # would produce a Class-A/geometry pair that measures nothing — and nothing downstream would
    # notice, because a variant that states no metadata trivially passes the manifest checks.
    if stripped == with_trailing_newline(original):
        print(f"{args.source}: nothing to strip, it states no graph metadata", file=sys.stderr)
        return 1
    args.destination.write_text(stripped, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
