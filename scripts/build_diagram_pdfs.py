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

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from corpus_tools.diagrams.recipes import RECIPES, build
from corpus_tools.diagrams.render import ROOT
from corpus_tools.hashing import sha256_file


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
                elif sha256_file(destination) != sha256_file(finished):
                    print(f"fail {target}: rebuilt bytes differ from the committed file", file=sys.stderr)
                    failures.append(target)
                else:
                    print(f"ok   {target}")
            else:
                shutil.copyfile(finished, destination)
                print(f"ok   {target}  {sha256_file(destination)[:12]}  {destination.stat().st_size} bytes")

    if failures:
        print(f"\n{len(failures)} of {len(targets)} failed", file=sys.stderr)
        return 1
    print(f"\n{len(targets)} of {len(targets)} ok", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
