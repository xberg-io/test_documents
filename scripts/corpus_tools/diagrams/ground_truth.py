"""Re-derive each Graphviz fixture's graph and diff it against the hand-written ground truth."""

import re
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import TypeVar

from corpus_tools.paths import REPO_ROOT

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

T = TypeVar("T", bound="str | tuple[str, str]")

ROOT = REPO_ROOT
SOURCES = ROOT / "diagrams" / "src"
GROUND_TRUTH = ROOT / "ground_truth" / "dot"

PLAIN_TOKEN = re.compile(r'"[^"]*"|\S+')
PORT = re.compile(r"<\w+>")
COMMENT = re.compile(r"//.*")
GT_NODE = re.compile(r'^\s*"([^"]+)"\s*\[', re.MULTILINE)
GT_EDGE = re.compile(r'"([^"]+)"\s*-[->]\s*"([^"]+)"')


def joined_record_fields(label: str) -> str:
    """One record is one node, so its key is its field texts as one multi-line label."""
    if "<" not in label:
        return label
    return "\\n".join(PORT.sub("", field).strip() for field in label.split("|"))


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


def report_difference(name: str, drawn: Sequence[T], recorded: Sequence[T]) -> None:
    print(f"     {name} drawn but not in ground truth: {sorted(set(drawn) - set(recorded))}")
    print(f"     {name} in ground truth but not drawn: {sorted(set(recorded) - set(drawn))}")
