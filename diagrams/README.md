# Diagram fixtures

Vector diagrams for node/edge recovery (xberg-io/xberg#579). A vector diagram
carries its own graph, so recovery from one is exact rather than probabilistic,
and these fixtures are what say whether it actually is.

## Why generated, not hand-drawn

Hand-written SVG exercises almost none of what a real diagram tool emits. The
four SVGs already in `xml/` have no transform chain, no arrowheads, no double
borders and no curved connectors, and a recogniser can pass all four while being
wrong about every file a user would actually bring.

Rendering a known graph through Graphviz fixes that, and it also gives ground
truth for free: the source `.dot` **is** the correct answer, so the corpus
measures recovery rather than freezing whatever it currently produces.

## Layout

| file | exercises |
|---|---|
| `graphviz_flow.svg` | box, diamond and ellipse nodes; arrowheads; edge labels; a dashed edge; root `translate` with negative coordinates |
| `graphviz_states.svg` | `doublecircle` (one node drawn as two concentric outlines); a pair of antiparallel edges between adjacent nodes |
| `graphviz_network.svg` | undirected `--` edges, so no arrowhead anywhere; `neato` layout |
| `graphviz_bidirectional.svg` | `dir=both` and `dir=back` |
| `nested_transforms.svg` | hand-authored: nested `translate`/`scale` groups plus a viewBox that differs from the viewport, so nothing sits at the coordinate it is written at |
| `src/*.dot` | the Graphviz sources, so every SVG above is regenerable |

`ground_truth/dot/<stem>.dot` holds the graph each fixture draws, keyed by node
label rather than by generated id so it does not depend on any one recogniser's
numbering. Two entries are deliberately empty, `data_dashboard` and
`simple_svg`: those files are a bar chart and a two-shape drawing, they are not
diagrams, and recovering a graph from either would be a false positive.

Ground truth also covers `xml/org_chart.svg` and `xml/flowchart.svg`, which stay
where they are.

## Regenerate

```
brew install graphviz     # or apt-get install graphviz
cd diagrams/src
for f in graphviz_flow graphviz_states graphviz_bidirectional; do
  dot -Tsvg "$f.dot" -o "../$f.svg"
done
neato -Tsvg graphviz_network.dot -o ../graphviz_network.svg
```

Output is stable for a given Graphviz version. This was built with 15.1.1;
a different version may lay the graphs out differently, which changes
coordinates but not the graph, and the ground truth is written in terms of the
graph.

`nested_transforms.svg` is hand-authored and is not regenerated.

## Not included

A vector PDF of the same graph (`dot -Tpdf`) would exercise the PDF path, but
`*.pdf` is excluded from git here and lives in the corpus bucket, so it has to
go through `scripts/publish_corpus.py`. Happy to supply the file for a
maintainer to publish.
