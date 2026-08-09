#!/usr/bin/env python3
"""Check every Graphviz diagram fixture's ground truth against what Graphviz actually drew.

The ground truth under `ground_truth/dot/` is written by hand, keyed by node label, and it is
what the whole diagram corpus is measured against -- so a transcription slip in it is worse
than a bug, because it silently redefines "correct". This re-derives the graph from the
committed `.dot` source using `dot -Tplain`, which reports the labels and edges as Graphviz
itself resolved them, and diffs that against the ground truth.

Two things the raw `-Tplain` output does not say, and this accounts for:

*   `dir=back` draws the arrowhead at the tail, so the edge reads the other way round. A
    recogniser working from geometry sees only where the arrowhead is, so the ground truth
    records the drawn direction and the declaration order is discarded.
*   A record node's label carries port names and field separators. One record is one node, so
    its key is the field texts joined with " | ".

Needs Graphviz on PATH, which is a fixture-regeneration dependency rather than a CI one -- it
reports that it skipped instead of failing when Graphviz is absent.

Usage:
    python3 scripts/check_diagram_ground_truth.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

# Engine per fixture: the layout Graphviz was invoked with, which has to match how the
# committed SVG was rendered or the comparison is against a different drawing.
ENGINES = {
    "graphviz_bidirectional": "dot",
    "graphviz_cjk": "dot",
    "graphviz_clusters": "dot",
    "graphviz_flow": "dot",
    "graphviz_large": "dot",
    "graphviz_network": "neato",
    "graphviz_ortho": "dot",
    "graphviz_record": "dot",
    "graphviz_selfloop": "neato",
    "graphviz_states": "dot",
}

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "diagrams" / "src"
GROUND_TRUTH = ROOT / "ground_truth" / "dot"

PLAIN_TOKEN = re.compile(r'"[^"]*"|\S+')
PORT = re.compile(r"<\w+>")
COMMENT = re.compile(r"//.*")
GT_NODE = re.compile(r'^\s*"([^"]+)"\s*\[', re.M)
GT_EDGE = re.compile(r'"([^"]+)"\s*-[->]\s*"([^"]+)"')


def joined_record_fields(label: str) -> str:
    """One record is one node, so its key is the field texts joined with " | "."""
    if "<" not in label:
        return label
    return " | ".join(PORT.sub("", field).strip() for field in label.split("|"))


def reversed_edges(source: Path) -> set[tuple[str, str]]:
    """Edges declared with dir=back, which Graphviz draws pointing the other way."""
    text = COMMENT.sub("", source.read_text(encoding="utf-8"))
    declarations = re.findall(r"(\w+)\s*->\s*(\w+)\s*\[([^\]]*)\]", text)
    return {(tail, head) for tail, head, attrs in declarations if "dir=back" in attrs}


def drawn_graph(stem: str, engine: str) -> tuple[list[str], list[tuple[str, str]]]:
    source = SOURCES / f"{stem}.dot"
    plain = subprocess.run([engine, "-Tplain", str(source)], capture_output=True, text=True, check=True).stdout
    flipped = reversed_edges(source)
    labels: dict[str, str] = {}
    nodes: list[str] = []
    edges: list[tuple[str, str]] = []
    for line in plain.splitlines():
        fields = [token[1:-1] if token.startswith('"') else token for token in PLAIN_TOKEN.findall(line)]
        if fields[0] == "node":
            labels[fields[1]] = joined_record_fields(fields[6])
            nodes.append(labels[fields[1]])
        elif fields[0] == "edge":
            tail, head = fields[1], fields[2]
            if (tail, head) in flipped:
                tail, head = head, tail
            edges.append((labels[tail], labels[head]))
    return sorted(nodes), sorted(edges)


def recorded_graph(stem: str) -> tuple[list[str], list[tuple[str, str]]]:
    text = COMMENT.sub("", (GROUND_TRUTH / f"{stem}.dot").read_text(encoding="utf-8"))
    return sorted(GT_NODE.findall(text)), sorted(GT_EDGE.findall(text))


def main() -> int:
    if shutil.which("dot") is None:
        print("graphviz is not installed, skipping the ground-truth cross-check")
        return 0
    failures = 0
    for stem, engine in sorted(ENGINES.items()):
        drawn_nodes, drawn_edges = drawn_graph(stem, engine)
        recorded_nodes, recorded_edges = recorded_graph(stem)
        if drawn_nodes == recorded_nodes and drawn_edges == recorded_edges:
            print(f"ok   {stem:24s} nodes {len(recorded_nodes):3d}  edges {len(recorded_edges):3d}")
            continue
        failures += 1
        print(f"FAIL {stem}")
        for name, drawn, recorded in (
            ("nodes", drawn_nodes, recorded_nodes),
            ("edges", drawn_edges, recorded_edges),
        ):
            print(f"     {name} drawn but not in ground truth: {sorted(set(drawn) - set(recorded))}")
            print(f"     {name} in ground truth but not drawn: {sorted(set(recorded) - set(drawn))}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
