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
*   A record node's label carries port names and field separators. One record is one node,
    so its key is the field texts as one multi-line label.

Needs Graphviz on PATH, which is a fixture-regeneration dependency rather than a CI one -- it
reports that it skipped instead of failing when Graphviz is absent.

Usage:
    python3 scripts/check_diagram_ground_truth.py
"""

import argparse
import shutil
import sys

from corpus_tools.diagrams.ground_truth import ENGINES, drawn_graph, recorded_graph, report_difference


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="STEM",
        help="check only this fixture stem; repeatable. Defaults to every fixture.",
    )
    args = parser.parse_args(argv)

    if shutil.which("dot") is None:
        print("graphviz is not installed, skipping the ground-truth cross-check")
        return 0

    selected = {stem: engine for stem, engine in ENGINES.items() if not args.only or stem in args.only}
    if not selected:
        print(f"no fixture stem matched {args.only}; known stems: {', '.join(sorted(ENGINES))}", file=sys.stderr)
        return 1

    failures = 0
    for stem, engine in sorted(selected.items()):
        drawn_nodes, drawn_edges = drawn_graph(stem, engine)
        recorded_nodes, recorded_edges = recorded_graph(stem)
        if drawn_nodes == recorded_nodes and drawn_edges == recorded_edges:
            print(f"ok   {stem:24s} nodes {len(recorded_nodes):3d}  edges {len(recorded_edges):3d}")
            continue
        failures += 1
        print(f"FAIL {stem}")
        # ~keep Nodes are strings and edges are pairs, so they cannot share a loop variable
        # without collapsing to a union that sorted() will not accept.
        report_difference("nodes", drawn_nodes, recorded_nodes)
        report_difference("edges", drawn_edges, recorded_edges)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
