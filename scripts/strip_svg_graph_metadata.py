#!/usr/bin/env python3
"""Remove the answer from a rendered SVG, leaving a geometry-only fixture behind.

Every diagram tool writes the graph it just laid out back into its own output, each in its
own way:

    graphviz    <g id="node1" class="node"><title>a</title>            the node id
                <g id="edge1" class="edge"><title>a&#45;&gt;b</title>   the whole edge
                <!-- a&#45;&gt;b -->                                    the whole edge, again
    mermaid     <path id="L_start_auth_0" data-id="L_start_auth_0">     both endpoints
    plantuml    <g id="Read config-to-Open input" class="link">         both endpoints
                <!--link Read config to Open input-->                   both endpoints, again

A recogniser that reads those scores perfectly without inspecting a single coordinate, so a
fixture carrying them cannot measure geometry recovery.

Reading them is not cheating -- when a file states its graph, using it is the correct and
exact thing to do, and that is what the Class A fixtures are for. It is simply a different
capability from inferring a graph from shapes and strokes, and measuring the two together
measures neither. So each fixture whose producer states its answer ships twice: as emitted,
and stripped.

Two rules, and both are producer-agnostic rather than a list of the dialects seen so far:

1.  Drop `<title>` inside an element group. The root `<title>` names the whole drawing, which
    a hand-drawn diagram would plausibly carry too, so it stays. Clusters count as elements:
    a cluster is a rectangle that is deliberately *not* a node, and `<title>cluster_ingest</title>`
    announces exactly that, which is the judgement the cluster fixtures exist to test.

2.  Drop every `id` that nothing in the document refers to, and every `data-id`. An id no
    `url(#...)`, `href="#..."` or stylesheet selector points at has no effect on rendering --
    it is there purely to say which element this is, and that is the answer.

3.  Drop every XML comment. Graphviz and PlantUML both restate the entire edge list in
    comments as well, so stripping only the titles and the ids leaves the answer sitting in
    the file in plain text. The producer banner goes with them; provenance belongs in
    `diagrams/manifest.json`, which is where a reader should be looking for it anyway.

What deliberately stays is anything that gives an element's *type* without naming its
endpoints: `class="node"`, `class="flowchart-link"`, `class="com.sun.star.drawing.ConnectorShape"`.
Knowing a stroke is some connector still leaves you to work out what it connects, which is
the whole task.

Usage:
    python3 scripts/strip_svg_graph_metadata.py diagrams/svg/graphviz_flow.svg \
        diagrams/svg/graphviz_flow_geometry.svg
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TITLE = re.compile(r"[ \t]*<title>.*?</title>\n?", re.DOTALL)
ELEMENT_GROUP = re.compile(r'(<g id="[^"]*" class="(?:node|edge|cluster)">)(.*?)(</g>)', re.DOTALL)

COMMENT = re.compile(r"[ \t]*<!--.*?-->\n?", re.DOTALL)
ID_ATTRIBUTE = re.compile(r'\s+id="([^"]*)"')
DATA_ID_ATTRIBUTE = re.compile(r'\s+data-id="[^"]*"')
FRAGMENT_REFERENCE = re.compile(r'(?:url\(\s*#|(?:xlink:)?href="#)([^)"\s]+)')
STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL)
STYLE_SELECTOR = re.compile(r"#([A-Za-z_][\w:.-]*)")


def referenced_ids(svg: str) -> set[str]:
    """Every id the document itself points at, so removing the rest changes no pixels."""
    ids = set(FRAGMENT_REFERENCE.findall(svg))
    for block in STYLE_BLOCK.findall(svg):
        ids.update(STYLE_SELECTOR.findall(block))
    return ids


def strip(svg: str) -> str:
    without_titles = ELEMENT_GROUP.sub(lambda m: m.group(1) + TITLE.sub("", m.group(2)) + m.group(3), svg)
    keep = referenced_ids(without_titles)
    without_ids = ID_ATTRIBUTE.sub(lambda m: m.group(0) if m.group(1) in keep else "", without_titles)
    return COMMENT.sub("", DATA_ID_ATTRIBUTE.sub("", without_ids))


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    source, destination = Path(sys.argv[1]), Path(sys.argv[2])
    original = source.read_text(encoding="utf-8")
    stripped = strip(original)
    if stripped == original:
        print(f"{source}: nothing to strip, it states no graph metadata", file=sys.stderr)
        return 1
    destination.write_text(stripped, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
