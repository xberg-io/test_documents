# Diagram fixtures

Fixtures for node/edge recovery — xberg-io/xberg#579. `manifest.json` is the index: it says what
each file is, where it came from, why it is in the set, and what the correct answer is.

Ground truth lives in `ground_truth/dot/<stem>.dot`, written as a Graphviz graph keyed **by node
label** rather than by generated id, so it does not depend on how any one recogniser numbers its
output. It records what the file draws, not what any implementation currently returns.

## Two classes of fixture

`manifest.json` tags every fixture `class: "A"` or `class: "B"`, and the class decides how it
should be scored.

**Class A — the file states its graph.** ODF `draw:connector` carries `draw:start-shape` and
`draw:end-shape`; PowerPoint `p:cxnSp` carries `<a:stCxn id= idx=/>`; SmartArt carries
`dgm:ptLst`/`dgm:cxnLst`; `.drawio` edges carry `source=`/`target=`; a fenced ` ```mermaid ` block
is the graph in plain text. Recovery is lossless, so a correct implementation scores **exactly
1.0**. A miss here is a bug, not a threshold to tune.

**Class B — geometry only.** SVG and vector PDF give you shapes, strokes and text positions, and
the graph has to be inferred. Scoring is precision/recall against a threshold.

One Class A fixture ships today: `src/libreoffice_connectors.fodg`. Everything else is Class B.

## The metadata problem

Every diagram tool writes the graph it just laid out back into its own output, each in its own
way:

```xml
<!-- graphviz: the node id, the whole edge, and both again in comments -->
<g id="edge1" class="edge"><title>a&#45;&gt;b</title><path d="M63,-234.8C63,-227.2 63,-208.2"/></g>
<!-- a&#45;&gt;b -->

<!-- mermaid: both endpoints, twice -->
<path id="L_start_auth_0" data-id="L_start_auth_0" class="flowchart-link" d="..."/>

<!-- plantuml: both endpoints, twice -->
<g id="Read config-to-Open input" class="link">
<!--link Read config to Open input-->
```

That is the complete edge list, verbatim, in the file — and xberg's SVG extractor already collects
`<title>` (`SVG_TEXT_ELEMENTS` in `extraction/xml.rs`). A recogniser that reads it scores 4/4 nodes
and 4/4 edges on every Graphviz fixture without inspecting a single coordinate.

Reading it is not cheating: when a file states its graph, using it is the correct and exact thing
to do — that is what Class A *is*. It is simply a different capability from inferring a graph from
geometry, and measuring the two together measures neither. So each affected fixture ships twice, as
emitted and stripped:

```sh
python3 scripts/strip_svg_graph_metadata.py \
  diagrams/svg/graphviz_flow.svg diagrams/svg/graphviz_flow_geometry.svg
```

The stripper works on two producer-agnostic rules rather than a list of the dialects seen so far:
drop `<title>` inside an element group, and drop every identifier the document itself never refers
to. What stays is anything giving an element's *type* without naming its endpoints — `class="node"`,
`class="com.sun.star.drawing.ConnectorShape"` — because knowing a stroke is some connector still
leaves you the whole job of working out what it connects. XML comments go entirely; provenance
belongs in `manifest.json`, which is where a reader should be looking for it.

The `*_geometry.svg` variants share the ground truth of their originals: same answer, arrived at a
harder way, and identical to the pixel — the stripped file renders to a byte-identical PNG.
`manifest.json` marks which fixtures need one with `states_graph_in_metadata`.

Two producers need no variant. LibreOffice numbers its shapes `id1`..`id9` and says only what kind
of shape each one is; PlantUML's swimlane output carries no id, no class and no comment at all.
Both are honest by construction.

## What each fixture exercises

Positives, by producer:

| file | producer | n/e | exercises |
|---|---|---|---|
| `svg/graphviz_flow.svg` | Graphviz | 4/4 | box, diamond and ellipse nodes; arrowheads; edge labels; a dashed edge; root `translate` with negative coordinates |
| `svg/graphviz_states.svg` | Graphviz | 4/4 | `doublecircle` — one node drawn as two concentric outlines; a pair of antiparallel edges |
| `svg/graphviz_network.svg` | Graphviz | 5/4 | undirected `--` edges, so no arrowhead anywhere; `neato` layout |
| `svg/graphviz_bidirectional.svg` | Graphviz | 3/3 | `dir=both` and `dir=back` — the arrowhead at the tail, so the edge reads the other way round |
| `svg/graphviz_clusters.svg` | Graphviz | 5/4 | two cluster containers that are **not** nodes; an edge crossing a container boundary |
| `svg/graphviz_selfloop.svg` | Graphviz | 4/5 | self-loops, one labelled; two edges that cross in mid-drawing and share no endpoint |
| `svg/graphviz_ortho.svg` | Graphviz | 5/5 | orthogonal elbow routing, the default in every non-Graphviz tool |
| `svg/graphviz_record.svg` | Graphviz | 3/2 | `shape=record`: one outline divided by internal rules, edges anchored to a named port |
| `svg/graphviz_cjk.svg` | Graphviz | 5/4 | stroke-only nodes with no fill at all; Japanese, Korean, Hebrew and Arabic labels |
| `svg/graphviz_large.svg` | Graphviz | 128/141 | scale, for the perf and memory profiling the review asked for |
| `svg/mermaid_flow.svg` | Mermaid 11.16.0 | 6/6 | a 4.4 KB CSS block, ten `<marker>` defs, HTML labels in `<foreignObject>`, and edge labels on an opaque background box that looks exactly like a small node |
| `svg/plantuml_activity.svg` | PlantUML 1.2026.0 | 5/4 | rounded activity shapes; unlabelled `(*)` terminals |
| `svg/plantuml_swimlane.svg` | PlantUML 1.2026.0 | 5/4 | three swimlane bands that are **not** nodes |
| `svg/libreoffice_connectors.svg` | LibreOffice 26.2.5.2 | 4/3 | `draw:custom-shape` enhanced geometry; glued connectors that stop a few units short of the outline, so endpoints match only by proximity |
| `src/libreoffice_connectors.fodg` | hand-authored | 4/3 | **Class A** — `draw:start-shape`/`draw:end-shape` name the endpoints outright |
| `svg/nested_transforms.svg` | hand-authored | 4/3 | nested `translate`/`scale` groups plus a viewBox that differs from the viewport, so nothing sits at the coordinate it is written at |
| `svg/icon_nodes.svg` | hand-authored | 4/3 | the AWS/Azure house style: a node is an icon glyph with its caption underneath and no outline at all |
| `svg/mixed_page.svg` | hand-authored | 3/2 | a whole page — heading, prose, a ruled table, and one figure. Recovery has to be selective *within* the page |
| `xml/org_chart.svg` | hand-authored | 9/3 | multi-line labels, six isolated nodes |
| `xml/flowchart.svg` | hand-authored | 4/3 | `marker-end` arrowheads, annotations outside every shape |

`src/` holds every source — `.dot`, `.mmd`, `.puml`, `.fodg` — so all of the above is regenerable.

## Ground-truth conventions

- **Keyed by node label.** A recogniser's own numbering never enters into it.
- **Only labelled nodes.** An unlabelled decoration — PlantUML's start/stop markers, an arrowhead,
  a pie chart's leader dot — has no key and is not a node, and an edge joining one is not an edge.
- **Containers are not nodes.** Cluster rectangles, swimlane bands and lane headers are absent from
  the ground truth however closed their outlines look.
- **One record is one node.** Its key is the field texts as one multi-line label, the same way
  `org_chart.dot` keys a two-line box, because splitting a record into one node per field is the
  failure that fixture exists to catch.
- **Direction as drawn.** `dir=back` puts the arrowhead at the tail, so the ground truth records
  what the drawing shows, not the order the source declared.
- **Undirected stays undirected** — `graph` and `--`, never restated as a `digraph`.
- **Comments carry no DOT syntax.** Not every consumer strips `//`, so a comment mentioning
  `a -> b` gets scored as an edge. `test_diagram_manifest.py` enforces this.

## Negatives

Six fixtures have `"negative": true`, an empty ground-truth file and a stated `reason` in the
manifest. Recovering anything from them is a false positive, and that is worth a test of its own.
The empty file plus the reason is what keeps "not a diagram" and "not yet annotated" from being the
same bytes.

- `svg/negative_ruled_table.svg` — **the most dangerous one.** A table drawn as ruling lines has the
  same signature as a diagram: closed rectangular regions with text inside, joined by straight
  strokes running from the edge of one region to the next. Whatever rejects it also has to leave
  table detection working.
- `svg/negative_pie_chart.svg` — each label sits in a rounded box joined to its slice by a
  two-segment leader line ending in a dot, which is exactly the shape of a labelled node wired up
  by an elbow connector.
- `svg/negative_form.svg` — captions beside empty boxes, section rules, checkboxes, a signature
  line. The rules run right up to the boxes, which is what an edge looks like.
- `xml/data_dashboard.svg` — a bar chart. Closed outlines and straight strokes, but the strokes are
  axes and gridlines.
- `xml/simple_svg.svg` — two unconnected shapes and a label.
- `images/5_level_paging_and_5_level_ept_intel_revision_1_1_may_2017.svg` — despite the filename,
  an **inferno flame graph**: 77 nested `<rect>`s, 81 `<text>` labels, a CSS `<style>` block, an
  ECMAScript `<script>` and a gradient `<defs>`. Adjacency is stack containment, not connection, and
  there is not one connector in the file. It was already shipping; the only thing missing was the
  assertion that recovery returns nothing.

`svg/mixed_page.svg` is the seventh case and the awkward one: a negative and a positive in the same
file, so the answer cannot be decided per file.

## Regenerate

```sh
brew install graphviz               # 15.1.1
brew install --cask libreoffice     # 26.2.5.2
curl -sLO https://github.com/plantuml/plantuml/releases/download/v1.2026.0/plantuml-1.2026.0.jar

cd diagrams/src
for f in graphviz_flow graphviz_states graphviz_bidirectional \
         graphviz_clusters graphviz_ortho graphviz_record graphviz_cjk graphviz_large; do
  dot -Tsvg "$f.dot" -o "../svg/$f.svg"
done
for f in graphviz_network graphviz_selfloop; do
  neato -Tsvg "$f.dot" -o "../svg/$f.svg"
done
cd ../..

npx @mermaid-js/mermaid-cli@11.16.0 \
  -i diagrams/src/mermaid_flow.mmd -o diagrams/svg/mermaid_flow.svg -b transparent
java -jar plantuml-1.2026.0.jar -tsvg -o "$PWD/diagrams/svg" diagrams/src/*.puml
soffice --headless --convert-to svg --outdir diagrams/svg diagrams/src/libreoffice_connectors.fodg

for f in graphviz_flow graphviz_states graphviz_bidirectional graphviz_network \
         graphviz_clusters graphviz_ortho graphviz_record graphviz_cjk graphviz_large \
         graphviz_selfloop mermaid_flow plantuml_activity; do
  python3 scripts/strip_svg_graph_metadata.py \
    "diagrams/svg/$f.svg" "diagrams/svg/${f}_geometry.svg"
done

python3 scripts/check_diagram_ground_truth.py   # ground truth still matches what was drawn
python3 -m unittest discover -s scripts         # manifest still matches the files
```

Output is stable for a given tool version; a different version may lay a graph out differently,
which changes coordinates but not the graph — and the ground truth is written in terms of the
graph. The four Graphviz fixtures added before this set regenerate byte-identically under 15.1.1.

`nested_transforms.svg`, `icon_nodes.svg`, `mixed_page.svg` and the three `negative_*.svg` are
hand-authored and are not regenerated.

## Checks

`scripts/test_diagram_manifest.py` runs in CI with no renderer installed and asserts that every
indexed path exists, that the node and edge counts in the manifest match the ground truth, that an
undirected graph is written as one, that every negative has an empty ground truth and a reason, and
that each `*_geometry.svg` is byte-for-byte what stripping its parent produces — which is the only
check that does not depend on knowing how a given producer encodes its answer.

`scripts/check_diagram_ground_truth.py` needs Graphviz and re-derives each graph from its `.dot`
source with `dot -Tplain`, diffing it against the hand-written ground truth. It reports a skip
rather than failing when Graphviz is absent.

## Why generated rather than hand-drawn

Hand-written SVG exercises almost none of what a real diagram tool emits. The four SVGs originally
in `xml/` have no transform chain, no arrowheads, no double borders and no curved connectors, so a
recogniser can pass all four while being wrong about every file a user would actually bring.
Running recovery over real `dot -Tsvg` output found four defects those fixtures could not reach:
every arrowhead read as a node; every edge terminating on the arrowhead rather than the shape
behind it; `doublecircle` split into two concentric nodes; and the midpoint of a straight two-point
connector computed as its endpoint, so straight edges could never carry a label at all.

Rendering a known graph also gives ground truth for free — the source **is** the correct answer —
so the corpus measures recovery rather than freezing whatever the code currently returns.

## Not yet here

Vector PDF, PowerPoint and SmartArt connectors, DOCX canvas and VML, XLSX drawings, and the
diagram-native formats (`.drawio`, `.excalidraw`, `.bpmn`, `.vsdx`, `.graphml`) are all still
missing, as is draw.io's SVG dialect with its embedded `mxGraphModel`, and Excalidraw's, where one
logical stroke becomes many wobbly subpaths. So is a multi-page document with the diagram on page
N, which is what the `page` and `bbox` slots in the manifest exist for. See the plan on
xberg-io/xberg#1410.
