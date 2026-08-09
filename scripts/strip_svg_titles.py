#!/usr/bin/env python3
"""Strip <title> elements from a Graphviz SVG to produce a geometry-only fixture.

`dot -Tsvg` writes the graph it just laid out back into the output as metadata: one
`<title>` per node holding the node id, and one per edge holding `src-&gt;dst`. That is
the complete answer, verbatim, in the file. A recogniser that reads titles scores
perfectly on such a fixture without inspecting a single coordinate, so a title-bearing
SVG cannot measure geometry recovery.

Using the titles is not wrong -- when a file states its graph, reading it is the correct
and exact thing to do. It is simply a different capability from inferring a graph from
shapes and strokes, and the two have to be measured apart. So each Graphviz fixture ships
twice: as emitted, and with titles removed.

Usage:
    python3 scripts/strip_svg_titles.py diagrams/svg/graphviz_flow.svg \
        diagrams/svg/graphviz_flow_geometry.svg
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# The root <title> names the graph, not a node or an edge, and a real hand-drawn diagram
# would plausibly carry one. Only the per-element titles inside <g class="node"> and
# <g class="edge"> leak the answer, and those are the ones removed.
TITLE = re.compile(r"[ \t]*<title>.*?</title>\n?", re.DOTALL)
ELEMENT_GROUP = re.compile(r'(<g id="[^"]*" class="(?:node|edge)">)(.*?)(</g>)', re.DOTALL)


def strip(svg: str) -> str:
    return ELEMENT_GROUP.sub(lambda m: m.group(1) + TITLE.sub("", m.group(2)) + m.group(3), svg)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    source, destination = Path(sys.argv[1]), Path(sys.argv[2])
    original = source.read_text(encoding="utf-8")
    stripped = strip(original)
    if stripped == original:
        print(f"{source}: no element titles found, nothing to strip", file=sys.stderr)
        return 1
    destination.write_text(stripped, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
