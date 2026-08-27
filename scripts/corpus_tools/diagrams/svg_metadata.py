"""Remove the answer from a rendered SVG, leaving a geometry-only fixture behind.

Every diagram tool writes the graph it just laid out back into its own output, each in its
own way:

    graphviz    <g id="node1" class="node"><title>a</title>            the node id
                <g id="edge1" class="edge"><title>a&#45;&gt;b</title>   the whole edge
                <!-- a&#45;&gt;b -->                                    the whole edge, again
    mermaid     <path id="L_start_auth_0" data-id="L_start_auth_0">     both endpoints
                data-points="W3s...XQ=="                                every waypoint, base64 JSON
    plantuml    <g id="Read config-to-Open input" class="link">         both endpoints
                <!--link Read config to Open input-->                   both endpoints, again
                <g class="link" data-entity-1="ent0002"                 an adjacency list, plus a
                    data-entity-2="ent0003" data-source-line="4">       line number into the source
                <?plantuml-src LOun3i8m...?>                            the entire source, deflated
    libreoffice <g class="com.sun.star.drawing.ConnectorShape">         edge against node, the
                <g class="com.sun.star.drawing.CustomShape">            whole partition

A recogniser that reads those scores perfectly without inspecting a single coordinate, so a
fixture carrying them cannot measure geometry recovery.

Reading them is not cheating -- when a file states its graph, using it is the correct and
exact thing to do, and that is what the Class A fixtures are for. It is simply a different
capability from inferring a graph from shapes and strokes, and measuring the two together
measures neither. So each fixture whose producer states its answer ships twice: as emitted,
and stripped.

Five rules, all producer-agnostic rather than a list of the dialects seen so far. Each one
removes something the renderer never reads, so the drawing is untouched by construction:

1.  Drop `<title>` inside an element group. The root `<title>` names the whole drawing, which
    a hand-drawn diagram would plausibly carry too, so it stays. Clusters count as elements:
    a cluster is a rectangle that is deliberately *not* a node, and `<title>cluster_ingest</title>`
    announces exactly that, which is the judgement the cluster fixtures exist to test.

2.  Drop every `id` that nothing in the document refers to, and every `data-*` attribute no
    stylesheet selects on. An id no `url(#...)`, `href="#..."` or stylesheet selector points at
    has no effect on rendering -- it is there purely to say which element this is, and that is
    the answer. `data-*` is the same case with the spec on its side: it is defined as private
    author metadata, so nothing outside the document can be relying on it. Mermaid's
    `[data-look="neo"]` is the exception that earns the qualifier -- an attribute selector makes
    that one load-bearing, exactly as a `url(#...)` makes an id load-bearing.

3.  Drop every XML comment. Graphviz and PlantUML both restate the entire edge list in
    comments as well, so stripping only the titles and the ids leaves the answer sitting in
    the file in plain text. The producer banner goes with them; provenance belongs in
    `diagrams/manifest.json`, which is where a reader should be looking for it anyway.

4.  Drop every processing instruction except the XML declaration. A PI addresses some
    processor other than the renderer, which is the definition of out-of-band author data --
    the same category as a comment, and treated the same way. PlantUML uses one to embed its
    whole input, raw-deflated and 6-bit encoded, so the file that states nothing in plain text
    still carries every node and every edge; its version banner is a producer banner and goes
    with the comments.

5.  Drop every `class` token no embedded stylesheet selects on, judged one token at a time --
    `class="basic label-container"` is two independent decisions, and an attribute whose every
    token goes is removed rather than left empty. A class nothing selects on has no effect on
    rendering; it is there purely to say what this element is, and for the graph vocabulary
    that *is* the answer. This rule replaces the earlier claim that a class gives an element's
    *type* without naming its endpoints, which was wrong: Graphviz writes `class="node"`,
    `class="edge"` and `class="cluster"`, and that partition is the whole judgement the
    fixtures exist to measure. Each `<g class="node">` wraps its own shape and its own
    `<text>`, so the node set, every node's extent and every node's label association are
    exact lookups; `class="cluster"` announces "this rectangle is deliberately not a node",
    which is the same statement as the `<title>cluster_ingest</title>` rule 1 already strips.
    LibreOffice partitions the same way with `com.sun.star.drawing.ConnectorShape` against
    `com.sun.star.drawing.CustomShape`. What survives is the genuine half of the old reasoning:
    a class an embedded stylesheet actually selects on is load-bearing and stays, exactly as
    `url(#...)` makes an id load-bearing and `[data-look="neo"]` makes that attribute
    load-bearing. Mermaid keeps most of its vocabulary that way.

Output ends in a newline. Several producers do not terminate their last line, and a fixture
that has to be compared byte for byte should not differ from its sibling on that.

Usage:
    python3 scripts/strip_svg_graph_metadata.py diagrams/svg/graphviz_flow.svg \
        diagrams/svg/graphviz_flow_geometry.svg
"""

import re

TITLE = re.compile(r"[ \t]*<title>.*?</title>\n?", re.DOTALL)
ELEMENT_GROUP = re.compile(r'(<g id="[^"]*" class="(?:node|edge|cluster)">)(.*?)(</g>)', re.DOTALL)

COMMENT = re.compile(r"[ \t]*<!--.*?-->\n?", re.DOTALL)
# `xml-stylesheet` is the one PI a renderer does read, so it is spared alongside the declaration.
PROCESSING_INSTRUCTION = re.compile(r"[ \t]*<\?(?!xml(?:-stylesheet)?[\s?]).*?\?>\n?", re.DOTALL)
ID_ATTRIBUTE = re.compile(r'\s+id="([^"]*)"')
DATA_ATTRIBUTE = re.compile(r'\s+(data-[\w:.-]+)="[^"]*"')
CLASS_ATTRIBUTE = re.compile(r'\s+class="([^"]*)"')
FRAGMENT_REFERENCE = re.compile(r"""(?:url\(\s*["']?#|(?:xlink:)?href\s*=\s*["']#)([^)"'\s]+)""")
STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL)
STYLE_SELECTOR = re.compile(r"#([A-Za-z_][\w:.-]*)")
STYLE_ATTRIBUTE_SELECTOR = re.compile(r"\[\s*(?:(?:[A-Za-z_][\w.-]*|\*)\s*\|(?!=)\s*)?([A-Za-z_][\w:.-]*)")

# A CSS identifier: letters, digits, hyphen, underscore, any non-ASCII, and backslash escapes,
# never opening on a digit -- which is what keeps `0.5` in a declaration from reading as `.5`.
CSS_IDENTIFIER = r"-?(?:[_a-zA-Z]|\\[^\n]|[^\x00-\x7f])(?:[-\w]|\\[^\n]|[^\x00-\x7f])*"
STYLE_CLASS_SELECTOR = re.compile(rf"\.({CSS_IDENTIFIER})")
CSS_ESCAPE = re.compile(r"\\(?:([0-9a-fA-F]{1,6})[ \t\n]?|(.))", re.DOTALL)


def referenced_ids(svg: str) -> set[str]:
    """Every id the document itself points at, so removing the rest changes no pixels."""
    ids = set(FRAGMENT_REFERENCE.findall(svg))
    for block in STYLE_BLOCK.findall(svg):
        ids.update(STYLE_SELECTOR.findall(block))
    return ids


def selected_attributes(svg: str) -> set[str]:
    """Every attribute an embedded stylesheet matches on, which makes it affect rendering."""
    names: set[str] = set()
    for block in STYLE_BLOCK.findall(svg):
        names.update(STYLE_ATTRIBUTE_SELECTOR.findall(block))
    return names


def selector_text(stylesheet: str) -> str:
    """The stylesheet with every declaration block dropped, leaving only what selects.

    Declarations are where the false positives live: `stroke-width:1.5px` has a dot in it and
    `url(logo.png)` has a dot followed by letters, and neither is a class selector.
    """
    kept: list[str] = []
    depth = 0
    for character in stylesheet:
        if character == "{":
            depth += 1
        elif character == "}":
            depth = max(0, depth - 1)
        elif depth == 0:
            kept.append(character)
    return "".join(kept)


def unescape_css_identifier(name: str) -> str:
    r"""`com\.sun\.star` in a selector is the class token `com.sun.star` in the document."""
    return CSS_ESCAPE.sub(lambda m: chr(int(m.group(1), 16)) if m.group(1) else m.group(2), name)


def selected_classes(svg: str) -> set[str]:
    """Every class token an embedded stylesheet matches on, which makes it reach the pixels.

    Compound (`.a.b`), descendant (`.a .b`), child (`.a>.b`) and list (`.a,.b`) selectors all
    fall out of scanning for the tokens themselves rather than trying to parse the selector.
    """
    names: set[str] = set()
    for block in STYLE_BLOCK.findall(svg):
        for name in STYLE_CLASS_SELECTOR.findall(selector_text(block)):
            names.add(unescape_css_identifier(name))
    return names


def without_unselected_classes(svg: str, keep: set[str]) -> str:
    """Judge one token at a time, and drop the attribute outright when nothing survives."""

    def rewrite(match: re.Match[str]) -> str:
        tokens = match.group(1).split()
        kept = [token for token in tokens if token in keep]
        if kept == tokens:
            return match.group(0)
        return f' class="{" ".join(kept)}"' if kept else ""

    return CLASS_ATTRIBUTE.sub(rewrite, svg)


def with_trailing_newline(svg: str) -> str:
    return svg if svg.endswith("\n") else svg + "\n"


def strip(svg: str) -> str:
    without_titles = ELEMENT_GROUP.sub(lambda m: m.group(1) + TITLE.sub("", m.group(2)) + m.group(3), svg)
    keep_ids = referenced_ids(without_titles)
    without_ids = ID_ATTRIBUTE.sub(lambda m: m.group(0) if m.group(1) in keep_ids else "", without_titles)
    keep_attributes = selected_attributes(without_ids)
    without_data = DATA_ATTRIBUTE.sub(lambda m: m.group(0) if m.group(1) in keep_attributes else "", without_ids)
    without_classes = without_unselected_classes(without_data, selected_classes(without_data))
    return with_trailing_newline(PROCESSING_INSTRUCTION.sub("", COMMENT.sub("", without_classes)))
