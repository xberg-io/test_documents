#!/usr/bin/env python3
"""Regenerate the vector-PDF diagram fixtures, byte for byte.

PDF is where diagram recovery is hardest: the container keeps no `class="node"`, no `<title>`,
no element ids -- only path operators and positioned glyphs -- so a fixture here measures
geometry inference with nothing left to fall back on. That also makes the files impossible to
review by eye, which is why they are built by a recorded command rather than by hand.

Every producer stamps a creation timestamp into the PDF `Info` dictionary, so two runs of the
same command never agree byte for byte. `qpdf --empty --pages` rebuilds the document from its
pages alone and leaves the `Info` dictionary behind, and `--deterministic-id` derives the file id
from the content instead of the clock. The pair is what makes `--check` meaningful.

The `--check` claim is bounded, and worth stating plainly: it proves the committed PDF is still
what the recorded command produces *here*. PDFs embed subsetted fonts, so the same command on a
machine with different font files produces different bytes. Reproducing across machines is what
the content-addressed bucket and `corpus.lock.json` are for; this script is what keeps a fixture
honest about the command that made it.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
)


def chrome_binary() -> str:
    """Chrome is the only Skia PDF writer available, and it moves around between platforms."""
    override = os.environ.get("CHROME")
    candidates = (override, *CHROME_CANDIDATES) if override else CHROME_CANDIDATES
    for candidate in candidates:
        resolved = shutil.which(candidate) or (candidate if Path(candidate).is_file() else None)
        if resolved:
            return resolved
    raise FileNotFoundError("no Chrome or Chromium found; set CHROME to its path")


def run(argv: list[str]) -> None:
    result = subprocess.run(argv, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{argv[0]} failed: {result.stderr.strip() or result.stdout.strip()}")


def render_graphviz(source: Path, destination: Path) -> None:
    run(["dot", "-Tpdf", str(source), "-o", str(destination)])


def render_rsvg(source: Path, destination: Path) -> None:
    run(["rsvg-convert", "-f", "pdf", str(source), "-o", str(destination)])


def render_chrome(source: Path, destination: Path) -> None:
    run(
        [
            chrome_binary(),
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={destination}",
            source.resolve().as_uri(),
        ]
    )


def render_libreoffice(source: Path, destination: Path) -> None:
    run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(destination.parent), str(source)])
    produced = destination.parent / f"{source.stem}.pdf"
    produced.replace(destination)


def normalise(source: Path, destination: Path) -> None:
    """Strip the clock out of the file so the same drawing always hashes the same."""
    run(["qpdf", "--empty", "--deterministic-id", "--pages", str(source), "1-z", "--", str(destination)])


# A PDF carries subsetted outlines of whatever fonts the renderer reached for, and this corpus is
# published to a public bucket -- so the embedding permission of those fonts is ours to check, not
# the renderer's. Each family below was verified by reading the OS/2 fsType bit of the system font
# it comes from: Helvetica and Liberation Sans are 0 (installable), Times New Roman and Trebuchet
# MS are 8 (editable). Both values permit embedding. macOS's CJK faces do not -- Songti reports
# fsType 2, "restricted", which forbids embedding without the owner's permission -- which is why
# there is no CJK fixture here and why this list is an allowlist rather than a blocklist.
EMBEDDABLE_FAMILIES = frozenset({"Helvetica", "Helvetica-Bold", "LiberationSans", "TimesNewRomanPSMT", "TrebuchetMS"})

EMBEDDED_FONT = re.compile(r'"[A-Z]{6}\+([^"]+)"')


def embedded_families(path: Path) -> set[str]:
    listing = subprocess.run(["mutool", "info", "-F", str(path)], capture_output=True, text=True)
    return set(EMBEDDED_FONT.findall(listing.stdout))


def check_fonts_are_redistributable(path: Path) -> None:
    if shutil.which("mutool") is None:
        print(f"warn {path.name}: mutool absent, embedded fonts unchecked", file=sys.stderr)
        return
    restricted = sorted(embedded_families(path) - EMBEDDABLE_FAMILIES)
    if restricted:
        raise RuntimeError(
            f"embeds {', '.join(restricted)}, which is not on the redistributable allowlist. "
            "Check the source font's OS/2 fsType before adding it to EMBEDDABLE_FAMILIES."
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

    (ROOT / "diagrams" / "pdf").mkdir(parents=True, exist_ok=True)
    failures = []
    for target in targets:
        with tempfile.TemporaryDirectory() as directory:
            try:
                finished = build(target, Path(directory))
            except (RuntimeError, FileNotFoundError) as error:
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
