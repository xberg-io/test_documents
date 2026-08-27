"""Which producer draws which fixture, and how one gets built.

~keep Deliberately free of subprocess calls at import time: test_diagram_manifest imports RECIPES
in CI, where no renderer is installed.
"""

from collections.abc import Callable
from pathlib import Path

from corpus_tools.diagrams.render import (
    ROOT,
    check_fonts_are_redistributable,
    normalise,
    render_chrome,
    render_graphviz,
    render_libreoffice,
    render_rsvg,
)

Renderer = Callable[[Path, Path], None]

# One entry per fixture: where it lands, what it is drawn from, and which PDF writer draws it.
# The writer is the axis this set exists to cover -- cairo, Skia and LibreOffice emit the same
# drawing as very different content streams -- so it is named in the file name too.
RECIPES: dict[str, tuple[str, Renderer]] = {
    "diagrams/pdf/cairo_graphviz_flow.pdf": ("diagrams/src/graphviz_flow.dot", render_graphviz),
    "diagrams/pdf/cairo_graphviz_ortho.pdf": ("diagrams/src/graphviz_ortho.dot", render_graphviz),
    "diagrams/pdf/cairo_graphviz_large.pdf": ("diagrams/src/graphviz_large.dot", render_graphviz),
    "diagrams/pdf/cairo_two_diagrams.pdf": ("diagrams/svg/two_diagrams.svg", render_rsvg),
    "diagrams/pdf/cairo_negative_pie_chart.pdf": ("diagrams/svg/negative_pie_chart.svg", render_rsvg),
    "diagrams/pdf/skia_mermaid_flow.pdf": ("diagrams/svg/mermaid_flow.svg", render_chrome),
    "diagrams/pdf/skia_mixed_page.pdf": ("diagrams/svg/mixed_page.svg", render_chrome),
    "diagrams/pdf/skia_negative_ruled_table.pdf": ("diagrams/svg/negative_ruled_table.svg", render_chrome),
    "diagrams/pdf/skia_multipage_report.pdf": ("diagrams/src/multipage_report.html", render_chrome),
    "diagrams/pdf/libreoffice_connectors.pdf": ("diagrams/src/libreoffice_connectors.fodg", render_libreoffice),
}


def build(target: str, workspace: Path) -> Path:
    source, renderer = RECIPES[target]
    raw = workspace / "raw.pdf"
    finished = workspace / Path(target).name
    renderer(ROOT / source, raw)
    normalise(raw, finished)
    check_fonts_are_redistributable(finished)
    return finished
