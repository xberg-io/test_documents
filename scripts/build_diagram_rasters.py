#!/usr/bin/env python3
"""Regenerate the raster diagram fixtures, byte for byte.

A raster diagram is the case where nothing is left. Vector PDF at least keeps path operators
and positioned glyphs; a PNG keeps pixels, so both the shapes and the text have to be recovered
from the image before a graph can be inferred at all. These fixtures exist so that work can be
measured against the same ground truth the SVG and PDF copies are measured against, which is
what makes the three comparable.

Two engines, for the same reason the PDF set has two. librsvg does not render `<foreignObject>`,
so a cairo copy of the Mermaid fixture would carry the whole drawing with none of its labels.
Chrome renders it. The engine each fixture goes through is in its filename, because it is the
engine and not the source that decides the pixels.

Scale is 2x. A diagram's caption is set around 12px, which lands near the floor of what OCR
reads reliably at 1:1, and a benchmark should not be measuring a resampling artefact.

Determinism comes free here, unlike the PDF set. Neither renderer writes a `tIME` chunk or any
other clock-derived data, so two runs agree byte for byte with no normalisation step. `--check`
rebuilds and compares, so the command recorded in `manifest.json` is a claim that can be tested
rather than a note about what someone once ran. The claim is machine-local in the same way the
PDF one is: rasterising text needs fonts, and a machine with different font files draws
different pixels. Reproducing across machines is what the content-addressed bucket and
`corpus.lock.json` are for.

Unlike the PDFs, no font is redistributed. A PNG holds an image of text, not the outlines that
drew it, so the `fsType` embedding question the PDF builder has to answer does not arise. That
is why `graphviz_cjk` can ship as raster while it cannot ship as PDF.

Usage:
    python3 scripts/build_diagram_rasters.py            # build all
    python3 scripts/build_diagram_rasters.py --check    # verify, changing nothing
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

from build_diagram_pdfs import chrome_binary, run

ROOT = Path(__file__).resolve().parent.parent

# Every fixture is drawn at twice its intrinsic size. See the module docstring.
SCALE = 2

Renderer = Callable[[Path, Path], None]

VIEWPORT = re.compile(r'\b(width|height)="([0-9.]+)')
VIEWBOX = re.compile(r'viewBox="[-0-9.]+ [-0-9.]+ ([0-9.]+) ([0-9.]+)"')


def intrinsic_size(source: Path) -> tuple[int, int]:
    """The size Chrome must be told to open, since a screenshot has no intrinsic one.

    `width`/`height` win where the document states them, and the viewBox stands in where it does
    not, which is the same order a browser resolves them in.
    """
    text = source.read_text(encoding="utf-8", errors="replace")
    stated = dict(VIEWPORT.findall(text[: text.find(">", text.find("<svg"))] if "<svg" in text else ""))
    if "width" in stated and "height" in stated:
        return int(float(stated["width"])), int(float(stated["height"]))
    box = VIEWBOX.search(text)
    if box:
        return int(float(box.group(1))), int(float(box.group(2)))
    raise RuntimeError(f"{source.name} states neither a viewport nor a viewBox")


def render_rsvg(source: Path, target: Path) -> None:
    run(["rsvg-convert", "--zoom", str(SCALE), str(source), "-o", str(target)])


def render_chrome(source: Path, target: Path) -> None:
    width, height = intrinsic_size(source)
    run(
        [
            chrome_binary(),
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            # A screenshot of an SVG is otherwise composited onto transparency, and a diagram
            # read off a transparent background is a different image from the one a reader sees.
            "--default-background-color=ffffffff",
            f"--force-device-scale-factor={SCALE}",
            f"--window-size={width},{height}",
            f"--screenshot={target}",
            source.as_uri(),
        ]
    )


# The set is chosen rather than exhaustive, on the same principle as the PDF set: each entry has
# to measure something the others do not. `exercises` in the manifest says what, per fixture.
RECIPES: dict[str, tuple[str, Renderer]] = {
    "diagrams/png/cairo_graphviz_flow.png": ("diagrams/svg/graphviz_flow.svg", render_rsvg),
    "diagrams/png/cairo_graphviz_ortho.png": ("diagrams/svg/graphviz_ortho.svg", render_rsvg),
    "diagrams/png/cairo_graphviz_cjk.png": ("diagrams/svg/graphviz_cjk.svg", render_rsvg),
    "diagrams/png/cairo_graphviz_large.png": ("diagrams/svg/graphviz_large.svg", render_rsvg),
    "diagrams/png/cairo_graphviz_selfloop.png": ("diagrams/svg/graphviz_selfloop.svg", render_rsvg),
    "diagrams/png/cairo_plantuml_swimlane.png": ("diagrams/svg/plantuml_swimlane.svg", render_rsvg),
    "diagrams/png/cairo_two_diagrams.png": ("diagrams/svg/two_diagrams.svg", render_rsvg),
    "diagrams/png/cairo_mixed_page.png": ("diagrams/svg/mixed_page.svg", render_rsvg),
    "diagrams/png/cairo_icon_nodes.png": ("diagrams/svg/icon_nodes.svg", render_rsvg),
    "diagrams/png/cairo_negative_pie_chart.png": ("diagrams/svg/negative_pie_chart.svg", render_rsvg),
    "diagrams/png/skia_negative_ruled_table.png": ("diagrams/svg/negative_ruled_table.svg", render_chrome),
    "diagrams/png/skia_mermaid_flow.png": ("diagrams/svg/mermaid_flow.svg", render_chrome),
}


def build(target: str, workspace: Path) -> Path:
    source, renderer = RECIPES[target]
    finished = workspace / Path(target).name
    renderer(ROOT / source, finished)
    if not finished.is_file() or finished.stat().st_size == 0:
        raise RuntimeError("renderer produced nothing")
    return finished


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="rebuild and compare, changing nothing on disk")
    parser.add_argument("--only", action="append", default=[], help="build one target (repeatable)")
    arguments = parser.parse_args(argv)

    targets = arguments.only or sorted(RECIPES)
    unknown = [target for target in targets if target not in RECIPES]
    if unknown:
        print(f"unknown target(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    (ROOT / "diagrams" / "png").mkdir(parents=True, exist_ok=True)
    failures = []
    for target in targets:
        with tempfile.TemporaryDirectory() as directory:
            try:
                finished = build(target, Path(directory))
            except (RuntimeError, FileNotFoundError, subprocess.SubprocessError) as error:
                print(f"fail {target}: {error}", file=sys.stderr)
                failures.append(target)
                continue
            destination = ROOT / target
            if arguments.check:
                if not destination.is_file():
                    print(f"fail {target}: not built yet", file=sys.stderr)
                    failures.append(target)
                elif sha256_of(destination) != sha256_of(finished):
                    print(f"fail {target}: rebuilt bytes differ from the committed file", file=sys.stderr)
                    failures.append(target)
                else:
                    print(f"ok   {target}")
            else:
                shutil.copyfile(finished, destination)
                print(f"ok   {target}  {sha256_of(destination)[:12]}  {destination.stat().st_size} bytes")

    if failures:
        print(f"\n{len(failures)} of {len(targets)} failed", file=sys.stderr)
        return 1
    print(f"\n{len(targets)} of {len(targets)} ok", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
