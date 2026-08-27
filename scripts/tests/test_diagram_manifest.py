"""Invariants for `diagrams/manifest.json` and the fixtures it indexes.

The manifest is the corpus's answer key, and an answer key that disagrees with the files on
disk is worse than no answer key: it makes a scorer report numbers nobody can act on. These
run in CI, need no Graphviz, and cover the two ways it has already gone wrong once -- a
fixture path that does not exist, and a geometry-only variant that still states its answer.

Some fixtures are corpus binaries and so are absent from a fresh checkout. For those the question
is not whether the file is on disk but whether `corpus.lock.json` pins it, because that is what
decides whether a consumer who fetches the corpus gets it.

Two cross-checks need tools and live elsewhere: `scripts/check_diagram_ground_truth.py` re-derives
the Graphviz graphs with the renderer, and `scripts/build_diagram_pdfs.py --check` rebuilds the
PDFs and compares the bytes.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from build_diagram_pdfs import RECIPES
from corpus_tools import paths
from publish_corpus import load_patterns, matches_corpus_pattern
from strip_svg_graph_metadata import referenced_ids, strip

ROOT = paths.REPO_ROOT
MANIFEST = json.loads((ROOT / "diagrams" / "manifest.json").read_text(encoding="utf-8"))
FIXTURES = MANIFEST["fixtures"]
PATTERNS = load_patterns(ROOT)
PINNED = json.loads((ROOT / "corpus.lock.json").read_text(encoding="utf-8"))["objects"]


def is_bucket_managed(path: str) -> bool:
    """A corpus binary is absent from a fresh checkout, so it is pinned rather than committed."""
    return matches_corpus_pattern(path, PATTERNS)


COMMENT = re.compile(r"//.*")
GT_NODE = re.compile(r'^\s*"([^"]+)"\s*\[', re.M)
GT_EDGE = re.compile(r'"([^"]+)"\s*-[->]\s*"([^"]+)"')
XML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
ATTRIBUTE = re.compile(r'[\w:.-]+="([^"]*)"')


def ground_truths(fixture: dict) -> list[Path]:
    return [ROOT / graph["ground_truth"] for graph in fixture["graphs"]]


class FixtureFilesTest(unittest.TestCase):
    def test_should_index_a_committed_file_that_exists(self) -> None:
        for fixture in FIXTURES:
            if is_bucket_managed(fixture["path"]):
                continue
            with self.subTest(fixture["path"]):
                self.assertTrue((ROOT / fixture["path"]).is_file())

    def test_should_index_a_corpus_binary_that_the_lock_file_pins(self) -> None:
        # The PDFs are not in git, so CI checks out a tree without them and "does the file exist"
        # is the wrong question. The one that matters is whether a consumer who fetches the corpus
        # gets them, and that is decided by corpus.lock.json.
        for fixture in FIXTURES:
            if not is_bucket_managed(fixture["path"]):
                continue
            with self.subTest(fixture["path"]):
                self.assertTrue(
                    fixture["path"] in PINNED,
                    f"{fixture['path']} is not in corpus.lock.json; publish it before pushing",
                )

    def test_should_point_at_a_ground_truth_that_exists(self) -> None:
        for fixture in FIXTURES:
            for path in ground_truths(fixture):
                with self.subTest(str(path)):
                    self.assertTrue(path.is_file())

    def test_should_point_at_a_source_that_exists_when_it_claims_one(self) -> None:
        for fixture in FIXTURES:
            source = fixture.get("source")
            if source:
                with self.subTest(source):
                    self.assertTrue((ROOT / source).is_file())

    def test_should_ship_the_geometry_variant_it_names(self) -> None:
        for fixture in FIXTURES:
            variant = fixture.get("geometry_only_variant")
            if variant:
                with self.subTest(variant):
                    self.assertTrue((ROOT / variant).is_file())

    def test_should_index_every_svg_that_ships_under_diagrams(self) -> None:
        indexed = {f["path"] for f in FIXTURES}
        indexed |= {f["geometry_only_variant"] for f in FIXTURES if f.get("geometry_only_variant")}
        on_disk = {str(path.relative_to(ROOT)) for path in (ROOT / "diagrams" / "svg").glob("*.svg")}
        self.assertEqual(set(), on_disk - indexed, "fixture on disk that the manifest does not index")

    def test_should_build_every_pdf_it_indexes_and_index_every_pdf_it_builds(self) -> None:
        # A PDF cannot be reviewed by reading it, so the only thing standing between the manifest
        # and a file nobody can account for is the recipe that produced it.
        indexed = {f["path"] for f in FIXTURES if f["path"].startswith("diagrams/pdf/")}
        self.assertEqual(indexed, set(RECIPES))

    def test_should_build_every_pdf_from_a_source_the_manifest_agrees_with(self) -> None:
        for fixture in FIXTURES:
            source, _renderer = RECIPES.get(fixture["path"], (None, None))
            if source is None:
                continue
            with self.subTest(fixture["path"]):
                self.assertEqual(fixture["source"], source)


class GroundTruthAgreementTest(unittest.TestCase):
    def test_should_record_the_node_and_edge_counts_its_ground_truth_holds(self) -> None:
        for fixture in FIXTURES:
            for graph in fixture["graphs"]:
                text = COMMENT.sub("", (ROOT / graph["ground_truth"]).read_text(encoding="utf-8"))
                with self.subTest(graph["ground_truth"]):
                    self.assertEqual(graph["nodes"], len(GT_NODE.findall(text)))
                    self.assertEqual(graph["edges"], len(GT_EDGE.findall(text)))

    def test_should_write_an_undirected_ground_truth_as_a_graph_not_a_digraph(self) -> None:
        for fixture in FIXTURES:
            for graph in fixture["graphs"]:
                raw = (ROOT / graph["ground_truth"]).read_text(encoding="utf-8")
                body = COMMENT.sub("", raw)
                with self.subTest(graph["ground_truth"]):
                    if graph["directed"]:
                        self.assertRegex(body, r"^digraph\b")
                        self.assertNotIn(" -- ", body)
                    else:
                        self.assertRegex(body, r"^graph\b")
                        self.assertNotIn("->", body)

    def test_should_leave_a_negative_with_no_graph_and_a_stated_reason(self) -> None:
        negatives = [f for f in FIXTURES if f.get("negative")]
        self.assertTrue(negatives)
        for fixture in negatives:
            with self.subTest(fixture["path"]):
                self.assertEqual([], fixture["graphs"])
                self.assertTrue(fixture["reason"])
                # The empty file keeps "not a diagram" and "not yet annotated" apart: the
                # reason in the manifest is what says which one this is.
                self.assertEqual("", (ROOT / fixture["ground_truth"]).read_text(encoding="utf-8"))

    def test_should_name_every_ground_truth_node_in_the_drawing_it_answers_for(self) -> None:
        # The Graphviz fixtures get their ground truth re-derived from source by
        # scripts/check_diagram_ground_truth.py. The hand-authored ones have no source to derive
        # from, so this is what stands between them and a label that was mistyped into the answer
        # key -- an answer nothing in the file can ever produce, and a permanent lost point.
        for fixture in FIXTURES:
            if is_bucket_managed(fixture["path"]) or not fixture["path"].endswith(".svg"):
                continue
            body = (ROOT / fixture["path"]).read_text(encoding="utf-8")
            for graph in fixture["graphs"]:
                text = COMMENT.sub("", (ROOT / graph["ground_truth"]).read_text(encoding="utf-8"))
                for label in GT_NODE.findall(text):
                    for word in label.replace("\\n", " ").split():
                        with self.subTest(fixture=fixture["path"], word=word):
                            self.assertIn(word, body)

    def test_should_write_a_comment_that_cannot_be_misread_as_a_node_or_an_edge(self) -> None:
        # Consumers parse these files line by line and do not all strip `//` comments -- the
        # scorer on xberg#1410 does not, and a prose comment mentioning `a -> b` was read as a
        # real edge, which is how graphviz_large came to report one more edge than it draws.
        # Cheaper to keep the comments free of DOT syntax than to rely on every reader.
        for fixture in FIXTURES:
            for graph in fixture["graphs"]:
                path = ROOT / graph["ground_truth"]
                for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    comment = line.partition("//")[2]
                    with self.subTest(f"{graph['ground_truth']}:{number}"):
                        for token in ("->", "--", "["):
                            self.assertNotIn(token, comment)


class GeometryVariantTest(unittest.TestCase):
    """A geometry-only variant must not state the answer anywhere a parser can reach it."""

    def variants(self):
        for fixture in FIXTURES:
            variant = fixture.get("geometry_only_variant")
            if variant:
                yield fixture, (ROOT / variant).read_text(encoding="utf-8")

    def test_should_be_exactly_what_stripping_its_parent_produces(self) -> None:
        # The strongest statement available, and the one that does not depend on knowing how a
        # given producer encodes its answer: the committed variant is the tool's output, not
        # something hand-edited that merely looks stripped.
        for fixture, body in self.variants():
            parent = (ROOT / fixture["path"]).read_text(encoding="utf-8")
            with self.subTest(fixture["geometry_only_variant"]):
                self.assertEqual(strip(parent), body)

    def test_should_have_nothing_left_to_strip(self) -> None:
        for fixture, body in self.variants():
            with self.subTest(fixture["geometry_only_variant"]):
                self.assertEqual(body, strip(body))

    def test_should_carry_no_identifier_that_could_name_an_element(self) -> None:
        # Mermaid puts both endpoints of every edge in id="L_start_auth_0" and data-id, using
        # its own node ids rather than the labels, so a label-based check cannot see it.
        for fixture, body in self.variants():
            referenced = referenced_ids(body)
            declared = set(re.findall(r'\sid="([^"]*)"', body))
            with self.subTest(fixture["geometry_only_variant"]):
                self.assertEqual(set(), declared - referenced)
                self.assertNotIn("data-id=", body)

    def test_should_carry_no_xml_comments(self) -> None:
        # Graphviz and PlantUML both restate the whole edge list in comments.
        for fixture, body in self.variants():
            with self.subTest(fixture["path"]):
                self.assertEqual([], XML_COMMENT.findall(body))

    def test_should_not_name_a_ground_truth_node_in_any_attribute(self) -> None:
        for fixture, body in self.variants():
            labels = set()
            for graph in fixture["graphs"]:
                text = COMMENT.sub("", (ROOT / graph["ground_truth"]).read_text(encoding="utf-8"))
                labels.update(GT_NODE.findall(text))
            values = ATTRIBUTE.findall(body)
            for label in labels:
                with self.subTest(fixture=fixture["path"], label=label):
                    self.assertFalse(
                        [v for v in values if label.lower() in v.lower()],
                        "a node label leaked into an attribute value",
                    )

    def test_should_keep_every_node_label_as_rendered_text(self) -> None:
        # Stripping must remove metadata only. If a label vanished from the drawing itself the
        # variant would be measuring a different graph.
        for fixture, body in self.variants():
            if fixture["path"].endswith("mermaid_flow.svg"):
                continue  # mermaid wraps labels in HTML, which splits them across elements
            for graph in fixture["graphs"]:
                text = COMMENT.sub("", (ROOT / graph["ground_truth"]).read_text(encoding="utf-8"))
                for label in GT_NODE.findall(text):
                    # A multi-line label is one node but several <text> elements, so each line
                    # is looked for on its own.
                    for word in label.replace("\\n", " ").split():
                        with self.subTest(fixture=fixture["path"], word=word):
                            self.assertIn(word, body)


if __name__ == "__main__":
    unittest.main()
