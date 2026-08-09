# Diagram fixtures

Fixtures for node/edge recovery — xberg-io/xberg#579. `manifest.json` is the index: it says what
each file is, where it came from, why it is in the set, and what the correct answer is.

Ground truth lives in `ground_truth/dot/<stem>.dot`, written as a Graphviz graph keyed **by node
label** rather than by generated id, so it does not depend on how any one recogniser numbers its
output. It records what the file draws, not what any implementation currently returns.

## Two classes of fixture

`manifest.json` tags every fixture `class: "A"` or `class: "B"`, and the class decides how it
should be scored.

**Class A — the file states its graph.** PowerPoint `p:cxnSp` connectors carry `stCxnId`/`endCxnId`;
SmartArt carries `dgm:ptLst`/`dgm:cxnLst`; ODF `draw:connector` carries `draw:start-shape` and
`draw:end-shape`; `.drawio` edges carry `source=`/`target=`; a fenced ` ```mermaid ` block is the
graph in plain text. Recovery is lossless, so a correct implementation scores **exactly 1.0**.
A miss here is a bug, not a threshold to tune.

**Class B — geometry only.** SVG and vector PDF give you shapes, strokes and text positions, and the
graph has to be inferred. Scoring is precision/recall against a threshold. Everything in this
directory today is Class B.

## The titles problem

`dot -Tsvg` writes the graph it just laid out back into its own output:

```xml
<g id="edge1" class="edge">
<title>a&#45;&gt;b</title>
<path fill="none" stroke="black" d="M63,-234.8C63,-227.16 63,-217.55 63,-208.24"/>
```

One `<title>` per node holding the node id, one per edge holding `src->dst`. That is the complete
edge list, verbatim, in the file — and xberg's SVG extractor already collects `<title>`
(`SVG_TEXT_ELEMENTS` in `extraction/xml.rs`). A recogniser that reads titles scores 4/4 nodes and
4/4 edges on every Graphviz fixture without inspecting a single coordinate.

Reading them is not cheating: when a file states its graph, using it is the correct and exact thing
to do. It is simply a different capability from inferring a graph from geometry, and measuring the
two together measures neither. So each Graphviz fixture ships twice — as emitted, and with the
element titles removed:

```text
scripts/strip_svg_titles.py diagrams/svg/graphviz_flow.svg diagrams/svg/graphviz_flow_geometry.svg
```

The `*_geometry.svg` variants share the ground truth of their originals: same answer, arrived at a
harder way. `manifest.json` marks which is which with `states_graph_in_metadata`.

## What each fixture exercises

| file | exercises |
|---|---|
| `svg/graphviz_flow.svg` | box, diamond and ellipse nodes; arrowheads; edge labels; a dashed edge; root `translate` with negative coordinates |
| `svg/graphviz_states.svg` | `doublecircle` — one node drawn as two concentric outlines; a pair of antiparallel edges between adjacent nodes |
| `svg/graphviz_network.svg` | undirected `--` edges, so no arrowhead anywhere; `neato` layout |
| `svg/graphviz_bidirectional.svg` | `dir=both` and `dir=back` |
| `svg/*_geometry.svg` | the same four graphs with the answer removed from the metadata |
| `svg/nested_transforms.svg` | hand-authored: nested `translate`/`scale` groups plus a viewBox that differs from the viewport, so nothing sits at the coordinate it is written at |
| `src/*.dot` | the Graphviz sources, so every fixture above is regenerable |

Two fixtures outside this directory are covered by the same ground truth and listed in the
manifest: `xml/org_chart.svg` (multi-line labels, six isolated nodes) and `xml/flowchart.svg`
(`marker-end` arrowheads, annotations outside every shape).

## Negatives

Three fixtures have `"negative": true` and no ground-truth graph. Recovering anything from them is a
false positive, and that is worth a test of its own.

- `xml/data_dashboard.svg` — a bar chart. Closed outlines and straight strokes, but the strokes are
  axes and gridlines.
- `xml/simple_svg.svg` — two unconnected shapes and a label.
- `images/5_level_paging_and_5_level_ept_intel_revision_1_1_may_2017.svg` — despite the filename,
  an **inferno flame graph**: 77 nested `<rect>`s, 81 `<text>` labels, a CSS `<style>` block, an
  ECMAScript `<script>` and a gradient `<defs>`. Adjacency is stack containment, not connection, and
  there is not one connector in the file. It is the hardest negative in the corpus, it was already
  shipping, and the only thing missing was the assertion that recovery returns nothing.

## Regenerate

```sh
brew install graphviz     # or apt-get install graphviz
cd diagrams/src
for f in graphviz_flow graphviz_states graphviz_bidirectional; do
  dot -Tsvg "$f.dot" -o "../svg/$f.svg"
done
neato -Tsvg graphviz_network.dot -o ../svg/graphviz_network.svg
cd ../..
for f in graphviz_flow graphviz_states graphviz_bidirectional graphviz_network; do
  python3 scripts/strip_svg_titles.py "diagrams/svg/$f.svg" "diagrams/svg/${f}_geometry.svg"
done
```

Output is stable for a given Graphviz version; these were built with **15.1.1**. A different version
may lay the graphs out differently, which changes coordinates but not the graph — and the ground
truth is written in terms of the graph.

`nested_transforms.svg` is hand-authored and is not regenerated.

## Why generated rather than hand-drawn

Hand-written SVG exercises almost none of what a real diagram tool emits. The four SVGs that were
already in `xml/` have no transform chain, no arrowheads, no double borders and no curved
connectors, so a recogniser can pass all four while being wrong about every file a user would
actually bring. Running recovery over real `dot -Tsvg` output found four defects those four fixtures
could not reach: every arrowhead read as a node; every edge terminating on the arrowhead rather than
the shape behind it; `doublecircle` split into two concentric nodes; and the midpoint of a straight
two-point connector computed as its endpoint, so straight edges could never carry a label at all.

Rendering a known graph through Graphviz also gives ground truth for free — the source `.dot` **is**
the correct answer — so the corpus measures recovery rather than freezing whatever the code
currently returns.

## Not yet here

Vector PDF, PowerPoint/ODF connectors, SmartArt, and the diagram-native formats (`.drawio`,
`.excalidraw`, `.bpmn`, `.vsdx`, `.graphml`) are all still missing, as are the non-Graphviz SVG
producers — Mermaid, draw.io, PlantUML, Excalidraw — whose geometry idioms differ sharply from
Graphviz's. So are the feature cases that break naive recovery hardest: cluster and swimlane
containers that are not nodes, orthogonal elbow routing, self-loops, crossing-but-unconnected edges,
icon nodes, and edge labels drawn on an opaque background box. See the plan on xberg-io/xberg#1410.
