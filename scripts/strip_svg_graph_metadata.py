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
from corpus_tools.diagrams.svg_metadata import strip


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=svg_metadata.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("source", type=Path, help="the rendered SVG to strip")
    parser.add_argument("destination", type=Path, help="where to write the geometry-only fixture")
    args = parser.parse_args(argv)

    args.destination.write_text(strip(args.source.read_text(encoding="utf-8")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
