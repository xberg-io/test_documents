"""Tests for `strip_svg_graph_metadata.py`.

The script exists to stop a fixture from stating its own answer, so what these assert is that
the answer really is gone and that nothing the renderer reads went with it. The dividing line
is load-bearing versus not: an id something points at, an attribute or a class an embedded
stylesheet selects on, and the two processing instructions a reader acts on all stay, because
removing them would change a pixel. Everything else is the producer talking about its own
graph.
"""

from __future__ import annotations

import unittest

from strip_svg_graph_metadata import strip

GRAPHVIZ_NODE = (
    '<g id="node1" class="node">\n<title>a</title>\n<polygon fill="#a6cee3" stroke="black" points="0,0 1,1"/>\n</g>\n'
)
GRAPHVIZ_EDGE = (
    '<g id="edge1" class="edge">\n'
    "<title>a&#45;&gt;b</title>\n"
    '<path fill="none" stroke="black" d="M63,-234.8C63,-227.16 63,-208.24"/>\n'
    "</g>\n"
)
GRAPHVIZ_CLUSTER = (
    '<g id="clust1" class="cluster">\n'
    "<title>cluster_ingest</title>\n"
    '<polygon fill="#eef6fb" stroke="black" points="8,-148 8,-297 84,-297"/>\n'
    "</g>\n"
)
GRAPHVIZ_ROOT = '<g id="graph0" class="graph" transform="scale(1 1)">\n<title>whole_graph</title>\n'

MERMAID_EDGE = (
    '<path d="M1,2L3,4" id="L_start_auth_0" data-id="L_start_auth_0"'
    ' class="flowchart-link" marker-end="url(#my-svg_flowchart-v2-pointEnd)"/>'
)
PLANTUML_EDGE = (
    '<g id="Read config-to-Open input" class="link" data-source-line="4">'
    '<path d="M1,2L3,4" fill="none" style="stroke:#181818;"/></g>'
)
PLANTUML_LINK = (
    '<g class="link" data-entity-1="ent0002" data-entity-2="ent0003"'
    ' data-link-type="dependency" data-source-line="4"><path d="M1,2L3,4"/></g>'
)
# The first 32 characters of the blob plantuml_activity.svg carries: its own input, raw
# deflated and 6-bit encoded, which decodes to every node and every edge of the diagram.
PLANTUML_SOURCE = "<?plantuml-src LOun3i8m34NtdCBgL91w1IQOaRY1bJXjL69NJX0z?>"
MERMAID_WAYPOINTS = (
    '<path d="M1,2L3,4" class="edge-thickness-normal" data-edge="true" data-et="edge"'
    ' data-points="W3sieCI6MTc4LjY4NzUsInkiOjQ3LjV9XQ=="/>'
)
# Mermaid ships 4.4 KB of CSS, so most of its vocabulary is load-bearing. This is the shape of
# it: `.node` and `.flowchart-link` are styled, `.default` and `.nodes` are not.
MERMAID_STYLESHEET = (
    "<style>#my-svg .node rect{fill:#ECECFF;stroke-width:1.5px;}"
    "#my-svg .flowchart-link{stroke:#333333;}#my-svg .label text,#my-svg span{fill:#333;}</style>"
)
LIBREOFFICE_SHAPES = (
    '<g class="com.sun.star.drawing.CustomShape"><rect class="BoundingBox" x="0" y="0"/></g>'
    '<g class="com.sun.star.drawing.ConnectorShape"><path d="M1,2L3,4"/></g>'
)


class TitleStrippingTest(unittest.TestCase):
    def test_should_remove_the_node_id_from_a_node_group(self) -> None:
        self.assertNotIn("<title>", strip(GRAPHVIZ_NODE))

    def test_should_remove_the_edge_endpoints_from_an_edge_group(self) -> None:
        stripped = strip(GRAPHVIZ_EDGE)
        self.assertNotIn("a&#45;&gt;b", stripped)
        self.assertNotIn("<title>", stripped)

    def test_should_remove_the_cluster_name_so_a_container_is_not_labelled_as_one(self) -> None:
        self.assertNotIn("cluster_ingest", strip(GRAPHVIZ_CLUSTER))

    def test_should_keep_the_root_title_that_names_the_whole_drawing(self) -> None:
        self.assertIn("<title>whole_graph</title>", strip(GRAPHVIZ_ROOT + GRAPHVIZ_NODE))


class IdentifierStrippingTest(unittest.TestCase):
    def test_should_remove_a_mermaid_edge_id_naming_both_endpoints(self) -> None:
        stripped = strip(MERMAID_EDGE)
        self.assertNotIn("L_start_auth_0", stripped)
        self.assertNotIn("data-id", stripped)

    def test_should_remove_a_plantuml_edge_id_naming_both_endpoints(self) -> None:
        self.assertNotIn("Read config-to-Open input", strip(PLANTUML_EDGE))

    def test_should_keep_an_id_the_document_points_at_with_url(self) -> None:
        marker = '<marker id="arrow"/><path marker-end="url(#arrow)" d="M1,2L3,4"/>\n'
        self.assertEqual(marker, strip(marker))

    def test_should_keep_an_id_the_document_points_at_with_href(self) -> None:
        used = '<path id="outline" d="M1,2"/><use xlink:href="#outline"/>\n'
        self.assertEqual(used, strip(used))

    def test_should_keep_an_id_pointed_at_in_every_spelling_a_reference_takes(self) -> None:
        # Quoting inside url() and single-quoted attributes are both legal, and an id missed
        # here is an id stripped out from under a reference that still points at it.
        for reference in (
            '<path marker-end="url(#arrow)"/>',
            "<path marker-end='url(#arrow)'/>",
            '<path marker-end="url( #arrow )"/>',
            "<path marker-end=\"url('#arrow')\"/>",
            "<path marker-end='url(\"#arrow\")'/>",
            '<use href="#arrow"/>',
            "<use href='#arrow'/>",
            '<use xlink:href="#arrow"/>',
            "<use xlink:href='#arrow'/>",
        ):
            document = f'<marker id="arrow"/>{reference}\n'
            with self.subTest(reference):
                self.assertEqual(document, strip(document))

    def test_should_keep_an_id_a_stylesheet_selector_points_at(self) -> None:
        styled = '<style>#my-svg .node rect{fill:#fff}</style><svg id="my-svg"><g class="node"/></svg>'
        self.assertIn('id="my-svg"', strip(styled))

    def test_should_keep_an_opaque_id_that_names_nothing_but_is_referenced(self) -> None:
        # LibreOffice numbers its shapes id1..idN and refers to them from clip paths.
        libreoffice = '<clipPath id="id3"><rect/></clipPath><g clip-path="url(#id3)"/>\n'
        self.assertEqual(libreoffice, strip(libreoffice))


class DataAttributeStrippingTest(unittest.TestCase):
    def test_should_remove_a_plantuml_link_adjacency_pair(self) -> None:
        stripped = strip(PLANTUML_LINK)
        self.assertNotIn("ent0002", stripped)
        self.assertNotIn("ent0003", stripped)

    def test_should_remove_the_source_line_a_link_was_written_on(self) -> None:
        # The line number indexes straight into the sibling `.puml`, which states the edge.
        self.assertNotIn("data-source-line", strip(PLANTUML_LINK))

    def test_should_remove_the_mermaid_waypoints_that_give_an_edge_its_endpoints(self) -> None:
        stripped = strip(MERMAID_WAYPOINTS)
        self.assertNotIn("data-points", stripped)
        self.assertNotIn("data-edge", stripped)
        self.assertIn('d="M1,2L3,4"', stripped)

    def test_should_keep_a_data_attribute_a_stylesheet_selects_on(self) -> None:
        # Mermaid themes its shapes with `[data-look="neo"]`, so this one does reach the pixels.
        themed = '<style>.node[data-look="neo"] rect{fill:#fff}</style><g class="node" data-look="neo"/>\n'
        self.assertEqual(themed, strip(themed))

    def test_should_keep_a_data_attribute_selected_on_through_a_namespace_prefix(self) -> None:
        for selector in ('[svg|data-look="neo"]', '[*|data-look="neo"]'):
            themed = f'<style>.node{selector}{{fill:#fff}}</style><g class="node" data-look="neo"/>\n'
            with self.subTest(selector):
                self.assertEqual(themed, strip(themed))

    def test_should_not_read_the_dash_match_operator_as_a_namespace_prefix(self) -> None:
        # `[data-look|="neo"]` matches "neo" and "neo-dark"; the bar is an operator, not a prefix.
        themed = '<style>.node[data-look|="neo"]{fill:#fff}</style><g class="node" data-look="neo"/>\n'
        self.assertEqual(themed, strip(themed))


class ClassStrippingTest(unittest.TestCase):
    def test_should_remove_the_graphviz_partition_of_nodes_edges_and_clusters(self) -> None:
        # Graphviz has no stylesheet at all, so class="node" is pure commentary -- and it is the
        # answer: five <g class="node"> against four <g class="edge"> is the score, before a
        # single coordinate has been read.
        stripped = strip(GRAPHVIZ_NODE + GRAPHVIZ_EDGE + GRAPHVIZ_CLUSTER + GRAPHVIZ_ROOT)
        for token in ('class="node"', 'class="edge"', 'class="cluster"', 'class="graph"'):
            self.assertNotIn(token, stripped)

    def test_should_remove_the_libreoffice_partition_of_connectors_and_shapes(self) -> None:
        stripped = strip(LIBREOFFICE_SHAPES)
        self.assertNotIn("ConnectorShape", stripped)
        self.assertNotIn("CustomShape", stripped)
        self.assertIn('d="M1,2L3,4"', stripped)

    def test_should_remove_the_plantuml_class_that_says_which_strokes_are_links(self) -> None:
        self.assertNotIn('class="link"', strip(PLANTUML_LINK))

    def test_should_keep_a_class_a_stylesheet_selects_on_because_it_reaches_the_pixels(self) -> None:
        stripped = strip(MERMAID_STYLESHEET + '<g class="node"/><path class="flowchart-link"/>\n')
        self.assertIn('class="node"', stripped)
        self.assertIn('class="flowchart-link"', stripped)

    def test_should_judge_a_multi_token_class_one_token_at_a_time(self) -> None:
        # Mermaid writes class="node default" and class="basic label-container"; `.node` is
        # styled and the rest is not, so the attribute survives with only what renders.
        stripped = strip(MERMAID_STYLESHEET + '<g class="node default"/>\n')
        self.assertIn('<g class="node"/>', stripped)
        self.assertNotIn("default", stripped)

    def test_should_remove_the_attribute_outright_when_no_token_survives(self) -> None:
        stripped = strip(MERMAID_STYLESHEET + '<g class="basic label-container"/>\n')
        self.assertIn("<g/>", stripped)
        self.assertNotIn("class=", stripped.split("</style>")[1])

    def test_should_keep_a_class_named_by_a_compound_or_combinator_selector(self) -> None:
        for selector in (".marker.cross", ".marker .cross", ".marker>.cross", ".marker,.cross"):
            styled = f'<style>{selector}{{fill:#333;}}</style><g class="marker cross"/>\n'
            with self.subTest(selector):
                self.assertEqual(styled, strip(styled))

    def test_should_keep_a_class_whose_name_is_escaped_in_the_selector(self) -> None:
        # A dotted class can only be selected on with the dots escaped, and the escaped
        # selector names the unescaped attribute token.
        styled = (
            "<style>.com\\.sun\\.star\\.drawing\\.ConnectorShape{stroke:#333;}</style>"
            '<g class="com.sun.star.drawing.ConnectorShape"/>\n'
        )
        self.assertEqual(styled, strip(styled))

    def test_should_keep_a_class_named_with_hyphens_underscores_and_digits(self) -> None:
        styled = '<style>.edge-thickness_2{stroke-width:1px;}</style><g class="edge-thickness_2"/>\n'
        self.assertEqual(styled, strip(styled))

    def test_should_not_read_a_decimal_in_a_declaration_as_a_class_selector(self) -> None:
        # `stroke-width:1.5px` would hand a `.5px` class to anything scanning the whole block.
        styled = '<style>.kept{stroke-width:1.5px;}</style><g class="kept 5px"/>\n'
        self.assertIn('class="kept"', strip(styled))

    def test_should_not_read_an_id_or_an_element_name_as_a_class(self) -> None:
        styled = '<style>#my-svg rect{fill:#fff;}</style><g class="my-svg rect"/>\n'
        self.assertNotIn("class=", strip(styled).split("</style>")[1])


class CommentStrippingTest(unittest.TestCase):
    def test_should_remove_a_graphviz_comment_restating_an_edge(self) -> None:
        self.assertNotIn("a&#45;&gt;b", strip("<!-- a&#45;&gt;b -->\n" + GRAPHVIZ_EDGE))

    def test_should_remove_a_plantuml_comment_restating_an_edge(self) -> None:
        commented = "<!--link Read config to Open input-->" + PLANTUML_EDGE
        self.assertNotIn("Read config", strip(commented))

    def test_should_remove_the_producer_banner_because_provenance_lives_in_the_manifest(self) -> None:
        banner = "<!-- Generated by graphviz version 15.1.1 -->\n<svg/>"
        self.assertEqual("<svg/>\n", strip(banner))


class ProcessingInstructionStrippingTest(unittest.TestCase):
    def test_should_remove_the_source_plantuml_embeds_in_its_own_output(self) -> None:
        stripped = strip(PLANTUML_SOURCE + "<svg/>")
        self.assertNotIn("plantuml-src", stripped)
        self.assertNotIn("LOun3i8m34NtdCBgL91w1IQOaRY1bJXjL69NJX0z", stripped)

    def test_should_remove_the_producer_version_banner(self) -> None:
        self.assertEqual("<svg/>\n", strip("<?plantuml 1.2026.0?><svg/>"))

    def test_should_keep_the_stylesheet_instruction_that_does_reach_the_renderer(self) -> None:
        # `xml-stylesheet` is the one PI that is not out-of-band author data: it attaches a
        # stylesheet, so dropping it would restyle the drawing.
        linked = '<?xml-stylesheet type="text/css" href="s.css"?>\n<svg/>\n'
        self.assertEqual(linked, strip(linked))

    def test_should_keep_the_xml_declaration_that_says_how_to_read_the_file(self) -> None:
        declared = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n<svg/>\n'
        self.assertEqual(declared, strip(declared))


class PreservationTest(unittest.TestCase):
    def test_should_preserve_every_byte_of_geometry(self) -> None:
        stripped = strip(GRAPHVIZ_NODE + GRAPHVIZ_EDGE + GRAPHVIZ_CLUSTER)
        self.assertIn('points="0,0 1,1"', stripped)
        self.assertIn('d="M63,-234.8C63,-227.16 63,-208.24"', stripped)
        self.assertIn('points="8,-148 8,-297 84,-297"', stripped)

    def test_should_keep_the_geometry_of_an_element_whose_class_was_its_only_label(self) -> None:
        for original in (GRAPHVIZ_NODE, GRAPHVIZ_EDGE, MERMAID_EDGE, PLANTUML_EDGE):
            stripped = strip(original)
            with self.subTest(original[:40]):
                self.assertNotIn("class=", stripped)
                self.assertRegex(stripped, r'(?:points|d)="[^"]+"')

    def test_should_keep_the_text_a_node_is_labelled_with(self) -> None:
        labelled = '<g id="node1" class="node"><title>a</title><text>Start</text></g>'
        self.assertIn("<text>Start</text>", strip(labelled))

    def test_should_leave_a_hand_authored_svg_without_graph_metadata_untouched(self) -> None:
        hand_authored = '<svg><rect x="0" y="0"/><text>Start</text></svg>\n'
        self.assertEqual(hand_authored, strip(hand_authored))

    def test_should_end_with_a_newline_that_the_producer_may_have_omitted(self) -> None:
        self.assertEqual("<svg/>\n", strip("<svg/>"))


if __name__ == "__main__":
    unittest.main()
