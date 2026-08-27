"""Rendering a diagram source to a normalised, deterministic PDF.

~keep The font allowlist below is a licence-compliance mechanism, not a style choice, and
ATTRIBUTIONS.md cites it. Its comment travels with it.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from corpus_tools.paths import REPO_ROOT

ROOT = REPO_ROOT

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


def embedded_families_from_dump(dump: str) -> set[str]:
    """~keep Split out from embedded_families so the parsing can be tested without qpdf installed.

    The check only runs behind a renderer-dependent build, so it never executes in CI — and the
    PDFs it guards go to a world-readable bucket.
    """
    return set(EMBEDDED_FONT.findall(dump))


def embedded_families(path: Path) -> set[str]:
    listing = subprocess.run(["mutool", "info", "-F", str(path)], capture_output=True, text=True, check=False)
    return embedded_families_from_dump(listing.stdout)


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
