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

<!-- mermaid: both endpoints twice over, then every waypoint as base64 JSON -->
<path id="L_start_auth_0" data-id="L_start_auth_0" data-points="W3sieCI6..." class="flowchart-link"/>

<!-- plantuml: both endpoints four times over -->
<g id="Read config-to-Open input" class="link" data-entity-1="ent0002" data-entity-2="ent0003">
<!--link Read config to Open input-->
<?plantuml-src _pSf...?>   <!-- and the entire source, raw-deflated -->
```

That is the complete edge list, verbatim, in the file — and xberg's SVG extractor already collects
`<title>` (`SVG_TEXT_ELEMENTS` in `extraction/xml.rs`). A recogniser that reads it scores full marks
on every Graphviz fixture without inspecting a single coordinate.

The last of those is the one worth dwelling on. A `<?plantuml-src?>` processing instruction is not
readable prose and does not show up in a grep for node names, but it decodes to the complete source
— comments included. A file can look clean and still be handing over the whole answer.

Reading it is not cheating: when a file states its graph, using it is the correct and exact thing
to do — that is what Class A *is*. It is simply a different capability from inferring a graph from
geometry, and measuring the two together measures neither. So each affected fixture ships twice, as
emitted and stripped:

```sh
python3 scripts/strip_svg_graph_metadata.py \
  diagrams/svg/graphviz_flow.svg diagrams/svg/graphviz_flow_geometry.svg
```

The stripper works on five producer-agnostic rules rather than a list of the dialects seen so far.
Drop `<title>` inside an element group. Drop every XML comment. Drop every processing instruction
except the XML declaration. And then the three that share one test — drop every identifier, every
`data-*` attribute and every `class` token that nothing in the document itself refers to. That test
is the whole design: an attribute no `url(#...)`, no `href="#..."` and no stylesheet selector points
at cannot affect a single pixel, so removing it is provably safe, and the only reason it is in the
file is to say which element this is. Which is the answer.

The last rule replaced an earlier one that kept `class` outright, on the reasoning that a class
gives an element's *type* without naming its endpoints. That holds for one class read in isolation
and collapses across a file. `graphviz_clusters.svg` carries 5 `class="node"`, 4 `class="edge"` and
2 `class="cluster"` against a ground truth of exactly 5 nodes, 4 edges and 2 clusters, and each
`<g class="node">` wraps that node's own shape *and* its own label — so node recall, node extent and
label association are all lookups, and `class="cluster"` hands over the is-this-a-node judgement
that the cluster fixture exists to pose. Type per element, applied to every element, is the graph's
partition.

What survives is whatever the document actually uses. Mermaid's stylesheet selects on
`[data-look="neo"]`, `.flowchart-link` and `.labelBkg`, so those stay — load-bearing exactly as
`url(#...)` makes an id load-bearing. Graphviz ships no `<style>` at all, so nothing of its
vocabulary survives. Provenance goes with the comments; it belongs in `manifest.json`, which is
where a reader should be looking for it.

The `*_geometry.svg` variants share the ground truth of their originals: same answer, arrived at a
harder way, and identical to the pixel — the stripped file renders to a byte-identical PNG.
`manifest.json` marks which fixtures need one with `states_graph_in_metadata`.

Every producer in the set needs a variant. Two were once believed not to, and both beliefs were
wrong in the same way — the answer was in a place nobody had looked.

PlantUML's swimlane output carries no id, no class and no comment anywhere, and shipped without a
variant on that basis. The graph was in a `<?plantuml-src?>` processing instruction the whole time.
LibreOffice numbers its shapes `id1`..`id9` and was said to give only each shape's kind — but it
tags exactly 4 groups `...CustomShape` and exactly 3 `...ConnectorShape`, against a ground truth of
exactly 4 nodes and 3 edges. Both now ship stripped, and rules 4 and 5 are those two lessons.

## What each fixture exercises

Positives, by producer:

| file | producer | n/e | exercises |
|---|---|---|---|
| `svg/graphviz_flow.svg` | Graphviz | 4/4 | box, diamond and ellipse nodes; arrowheads; edge labels; a dashed edge; a root `translate` that shifts every coordinate in the file |
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
| `svg/two_diagrams.svg` | hand-authored | 3/2 + 4/3 | **two** graphs on one page, sharing no node and no edge, separated only by whitespace and a caption |
| `xml/org_chart.svg` | hand-authored | 9/3 | multi-line labels, six isolated nodes, `marker-end` arrowheads |
| `xml/flowchart.svg` | hand-authored | 4/3 | `marker-end` arrowheads, annotations outside every shape |

`src/` holds every source — `.dot`, `.mmd`, `.puml`, `.fodg`, `.html` — so all of the above is
regenerable.

## Vector PDF

PDF is where recovery is hardest, and the reason is structural: a page holds path operators and
positioned glyphs and nothing else. No element ids, no `<title>`, no `class`. Everything the
[metadata problem](#the-metadata-problem) is about is destroyed by the container itself, so these
files need no `_geometry` variant — they are geometry-only by construction, and they are the
strictest Class B measurement in the set.

Seven of them redraw a graph that also ships as SVG, against the same ground truth. Scoring the pair
apart separates what an implementation knows about graphs from what it knows about SVG.

| file | writer | drawn from | n/e | exercises |
|---|---|---|---|---|
| `pdf/cairo_graphviz_flow.pdf` | cairo | `src/graphviz_flow.dot` | 4/4 | the SVG fixture's graph in a different container |
| `pdf/cairo_graphviz_ortho.pdf` | cairo | `src/graphviz_ortho.dot` | 5/5 | elbows as bare `m`/`l` runs with no element boundary to group them |
| `pdf/cairo_graphviz_large.pdf` | cairo | `src/graphviz_large.dot` | 128/141 | scale, where cost is content-stream parsing rather than graph size |
| `pdf/cairo_two_diagrams.pdf` | cairo | `svg/two_diagrams.svg` | 3/2 + 4/3 | two graphs on one page |
| `pdf/skia_mermaid_flow.pdf` | Skia | `svg/mermaid_flow.svg` | 6/6 | the drawing that scored 0/6 as SVG, so the PDF says whether that was the dialect or the geometry |
| `pdf/skia_mixed_page.pdf` | Skia | `svg/mixed_page.svg` | 3/2 | prose, a ruled table and one figure, in the container where xberg already runs table detection |
| `pdf/skia_multipage_report.pdf` | Skia | `src/multipage_report.html` | 5/5 | **four pages, diagram on page 3.** Pages 1, 2 and 4 must yield nothing |
| `pdf/libreoffice_connectors.pdf` | LibreOffice | `src/libreoffice_connectors.fodg` | 4/3 | the same drawing whose `.fodg` source is Class A and scores exactly 1.0 |

Mermaid is the one producer that cannot go through cairo: it puts every label in a
`<foreignObject>` of HTML, which librsvg does not render at all, so a cairo copy would have a graph
and no text in it. Chrome renders it, which is also why Chrome is here as a second writer.

### Determinism

Every producer stamps a creation timestamp into the PDF `Info` dictionary, so two runs of the same
command never agree byte for byte. Each fixture is therefore rebuilt from its pages alone:

```sh
qpdf --empty --deterministic-id --pages raw.pdf 1-z -- diagrams/pdf/<name>.pdf
```

That drops the `Info` dictionary and derives the file id from the content instead of the clock.
`scripts/build_diagram_pdfs.py` runs both halves, and `--check` rebuilds and compares, so the
command recorded in `manifest.json` is a claim that can be tested rather than a note about what
someone once ran. The check is machine-local — PDFs embed subsetted fonts, so a machine with
different font files produces different bytes; reproducing across machines is what the
content-addressed bucket and `corpus.lock.json` are for.

PDFs are corpus binaries: they are **not** in git. `python3 scripts/fetch_corpus.py` brings them
down, and `corpus.lock.json` pins each one by sha256.

### Embedded fonts

A PDF carries subsetted outlines of whatever fonts the renderer reached for, so publishing one
redistributes font data. Each family here was checked against the OS/2 `fsType` bit of the system
font it came from — where a font states its own embedding terms. Helvetica and Liberation Sans
report 0 (installable), Times New Roman and Trebuchet MS report 8 (editable); all four permit it.
`build_diagram_pdfs.py` holds that allowlist and fails a build that reaches outside it. The check
reads the built PDF with `mutool`; where `mutool` is absent it warns and passes rather than
silently vouching for fonts it never looked at.

That check is why there is no CJK PDF. macOS's Songti reports `fsType` 2 — restricted, embedding
forbidden without the owner's permission — so `graphviz_cjk` ships as SVG only. Rendering it needs
an open-licensed CJK face (Noto Sans CJK) installed; macOS has none, and LibreOffice bundles Noto
for Arabic and Hebrew but not for CJK.

## Raster

Raster is where nothing is left. Vector PDF still holds path operators and positioned glyphs;
a PNG holds pixels, so the shapes and the text both have to be recovered from the image before
a graph can be inferred at all. Ten of these redraw a graph that also ships as SVG, against the
same ground truth, so the three containers can be scored apart.

| file | engine | drawn from | n/e | exercises |
|---|---|---|---|---|
| `png/cairo_graphviz_flow.png` | cairo | `svg/graphviz_flow.svg` | 4/4 | the baseline graph with nothing left to read but pixels |
| `png/cairo_graphviz_ortho.png` | cairo | `svg/graphviz_ortho.svg` | 5/5 | an elbow as a run of dark pixels, with not even a path operator to group it |
| `png/cairo_graphviz_cjk.png` | cairo | `svg/graphviz_cjk.svg` | 5/4 | **CJK, Hebrew and Arabic, which cannot ship as PDF** |
| `png/cairo_graphviz_large.png` | cairo | `svg/graphviz_large.svg` | 128/141 | 10566x2230, larger than most detector input windows, so tiling is forced |
| `png/cairo_graphviz_selfloop.png` | cairo | `svg/graphviz_selfloop.svg` | 4/5 | self-loops and crossing unconnected edges, where tracing strokes joins what the drawing keeps apart |
| `png/cairo_plantuml_swimlane.png` | cairo | `svg/plantuml_swimlane.svg` | 5/4 | large closed regions that are not nodes |
| `png/cairo_two_diagrams.png` | cairo | `svg/two_diagrams.svg` | 3/2 + 4/3 | two graphs in one image, so recovery must partition before it reports |
| `png/cairo_mixed_page.png` | cairo | `svg/mixed_page.svg` | 3/2 | prose, a ruled table and one figure, where the table is the false positive |
| `png/cairo_icon_nodes.png` | cairo | `svg/icon_nodes.svg` | 4/3 | icon glyphs with captions underneath and no outline anywhere, which SVG recovery scores 0/4 on |
| `png/skia_mermaid_flow.png` | Skia | `svg/mermaid_flow.svg` | 6/6 | HTML labels, which cairo does not draw |
| `png/cairo_negative_pie_chart.png` | cairo | `svg/negative_pie_chart.svg` | none | a chart is what a pixel recogniser is most likely to call a graph |
| `png/skia_negative_ruled_table.png` | Skia | `svg/negative_ruled_table.svg` | none | so is a ruled table |

The engine is in the filename because the engine, not the source, decides the pixels. Mermaid
cannot go through cairo for the same reason it cannot in [the PDF set](#vector-pdf): librsvg does
not render `<foreignObject>`, so a cairo copy carries the whole drawing and none of its labels.
That failure is silent, since the file is valid and only the text is missing, so
`test_diagram_manifest.py` asserts that any fixture drawn from a `<foreignObject>` source is built
by Skia.

Everything is drawn at 2x. A caption set around 12px sits near the floor of what OCR reads
reliably at 1:1, and a benchmark should not be measuring a resampling artefact.

### Determinism

Neither engine writes a `tIME` chunk or anything else derived from the clock, so unlike the PDFs
there is no normalisation step: two runs agree byte for byte on their own.

```sh
python3 scripts/build_diagram_rasters.py           # build
python3 scripts/build_diagram_rasters.py --check   # rebuild and compare, changing nothing
```

The `--check` claim is bounded the same way the PDF one is. It proves the committed PNG is still
what the recorded command produces *here*; rasterising text needs fonts, so the same command on a
machine with different font files draws different pixels. Reproducing across machines is what the
content-addressed bucket and `corpus.lock.json` are for.

No font is redistributed. A PNG holds an image of text rather than the outlines that drew it, so
the `fsType` question the [PDF builder](#embedded-fonts) has to answer does not arise here. That is
why `graphviz_cjk` ships as raster while it cannot ship as PDF.

PNGs are corpus binaries: they are **not** in git. `python3 scripts/fetch_corpus.py` brings them
down, and `corpus.lock.json` pins each one by sha256.

## Ground-truth conventions

- **Keyed by node label.** A recogniser's own numbering never enters into it.
- **Shape as drawn, not as declared.** `shape=` records the outline the file actually draws, to the
  nearest thing DOT can say: a Graphviz `circle` stays `circle` and not the `ellipse` element it is
  emitted as, a Mermaid stadium and a PlantUML activity are `box style=rounded`, a `doublecircle` is
  one node with two concentric outlines rather than two nodes. Where DOT has no equivalent the
  nearest shape is used and the difference belongs in the fixture's manifest note. This rule exists
  because its absence is how `graphviz_states` came to claim four ellipses it never drew.
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
- **One file, many graphs.** A document holding more than one graph gets `<stem>.g0.dot`,
  `<stem>.g1.dot`, and it is `manifest.json` that says so — the file layout is not load-bearing.
- **Where it is, not just what it is.** `page` is 1-based and `bbox` is `[x0, y0, x1, y1]` across
  the graph's node outlines, in SVG user space or in points from the top-left of the PDF page.
  Both run y downwards; PDF user space runs y upwards, so raw PDF coordinates need flipping. It is
  recorded only where the page holds more than the graph, because that is the only time it tells a
  right answer apart from one that is right by accident.

## Negatives

Eight fixtures have `"negative": true`, an empty ground-truth file and a stated `reason` in the
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
- `pdf/skia_negative_ruled_table.pdf` — the ruled table in the container where it does the most
  damage. A PDF table is ruling strokes and positioned glyphs with nothing to say it is a table,
  which is the same evidence a box-and-connector recogniser reads.
- `pdf/cairo_negative_pie_chart.pdf` — the pie chart in PDF, so the false positive it already
  produces as SVG can be measured in both containers rather than argued about in one.

Two more cases are the awkward ones, where the answer cannot be decided per file:
`svg/mixed_page.svg` and `pdf/skia_mixed_page.pdf` hold a negative and a positive on the same page,
and `pdf/skia_multipage_report.pdf` holds three pages that must yield nothing and one that must
yield a graph.

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
         graphviz_selfloop mermaid_flow plantuml_activity plantuml_swimlane \
         libreoffice_connectors; do
  python3 scripts/strip_svg_graph_metadata.py \
    "diagrams/svg/$f.svg" "diagrams/svg/${f}_geometry.svg"
done

python3 scripts/build_diagram_pdfs.py           # needs qpdf, and Chrome for the skia_* fixtures
python3 scripts/build_diagram_rasters.py        # raster fixtures, needs rsvg-convert and Chrome
python3 scripts/check_diagram_ground_truth.py   # ground truth still matches what was drawn
python3 -m unittest discover -s scripts         # manifest still matches the files
```

Output is stable for a given tool version; a different version may lay a graph out differently,
which changes coordinates but not the graph — and the ground truth is written in terms of the
graph. The four Graphviz fixtures added before this set regenerate byte-identically under 15.1.1.

`nested_transforms.svg`, `icon_nodes.svg`, `mixed_page.svg`, `two_diagrams.svg` and the three
`negative_*.svg` are hand-authored and are not regenerated.

## Checks

`scripts/test_diagram_manifest.py` runs in CI with no renderer installed. It asserts that every
committed fixture exists and every corpus binary is pinned in `corpus.lock.json` — the right
question for a file that is deliberately not in git is whether a consumer who fetches the corpus
gets it. It also asserts that the node and edge counts in the manifest match the ground truth, that
an undirected graph is written as one, that every negative has an empty ground truth and a reason,
that every ground-truth label appears as text in the drawing it answers for, that every PDF the
manifest indexes has a build recipe and vice versa, and that each `*_geometry.svg` is byte-for-byte
what stripping its parent produces — the only check that does not depend on knowing how a given
producer encodes its answer.

Two checks need tools and so are not in CI. `scripts/build_diagram_rasters.py --check` needs rsvg-convert and Chrome and rebuilds each PNG,
comparing bytes against the published file.

`scripts/check_diagram_ground_truth.py` needs Graphviz
and re-derives each graph from its `.dot` source with `dot -Tplain`, diffing it against the
hand-written ground truth; `scripts/build_diagram_pdfs.py --check` needs qpdf and the renderers and
proves each committed PDF is still what its recorded command produces. Both report a skip or a
clear failure rather than pretending, and the Graphviz one exits 0 when Graphviz is absent.

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

PowerPoint and SmartArt connectors, DOCX canvas and VML, XLSX drawings, and the diagram-native
formats (`.drawio`, `.excalidraw`, `.bpmn`, `.vsdx`, `.graphml`) are all still missing — every one
of them Class A, where the file states its graph and a correct implementation has to score exactly
1.0. So is draw.io's SVG dialect with its embedded `mxGraphModel`, and Excalidraw's, where one
logical stroke becomes many wobbly subpaths.

Two Class B gaps are deliberate rather than pending. Nothing here is real-world third-party work;
every fixture is authored in this repo, which keeps licensing simple but means no fixture has the
messiness of a diagram someone actually drew. And there is no fixture whose labels are outlined
into curves — the Illustrator and matplotlib export where the graph is fully recoverable and not
one label is — because the ground-truth format is keyed by label and cannot express "these five
nodes, names unknowable". That is a scoring-model question first and a fixture second.

See the plan on xberg-io/xberg#1410.
