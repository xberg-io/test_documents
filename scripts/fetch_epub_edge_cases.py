#!/usr/bin/env python3
"""Fetch or build the EPUB edge-case corpus.

`EPUB_EDGE_CASES.md` lists one or more EPUB files for each defect that
xberg-io/xberg pull request #1498 fixes. The bytes are gitignored like every
other corpus binary, so this script puts each file at the repository path it
belongs at, from the source that `scripts/data/epub-edge-cases.json` records:

- `url`: a published file, downloaded as is.
- `members`: an EPUB that the source publishes as an unpacked directory (the
  epubcheck test suite). Each member is downloaded from a pinned commit and the
  container is written by `build_epub_edge_cases.pack`, so the result is
  deterministic.
- `generated`: a synthesized file from `scripts/build_epub_edge_cases.py`.

Every entry carries the sha256 and size of the file the corpus was validated
against. A result whose digest does not match is written to `<path>.mismatch`
and reported, rather than replacing a good file. Publish the bytes the usual
way afterwards:

    python3 scripts/fetch_epub_edge_cases.py
    python3 scripts/publish_corpus.py --bucket xberg-test-documents
"""

import argparse
import concurrent.futures
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

import build_epub_edge_cases

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(__file__).resolve().parent / "data" / "epub-edge-cases.json"
TIMEOUT = 120
RETRIES = 3
USER_AGENT = "xberg-test-documents"


def download(url: str) -> bytes:
    last_error = ""
    for _attempt in range(RETRIES):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return response.read()
        except Exception as error:  # noqa: BLE001 - any transport failure is worth one more try
            last_error = f"{type(error).__name__}: {error}"
    raise RuntimeError(last_error)


def materialize(path: str, entry: dict, generated: dict[str, bytes]) -> bytes:
    if "url" in entry:
        return download(entry["url"])
    if "members" in entry:
        members = [(name, download(url)) for name, url in entry["members"].items() if name != "mimetype"]
        return build_epub_edge_cases.pack(members)
    if entry.get("generated"):
        return generated[path]
    raise ValueError(f"{path}: entry has no url, members or generated source")


def fetch_one(path: str, entry: dict, force: bool, generated: dict[str, bytes]) -> tuple[str, str]:
    """Return (path, status). Status is ok, skipped, mismatch or an error."""
    target = REPO_ROOT / path
    if target.exists() and not force:
        if hashlib.sha256(target.read_bytes()).hexdigest() == entry["sha256"]:
            return path, "skipped"
    try:
        payload = materialize(path, entry, generated)
    except Exception as error:  # noqa: BLE001 - reported per file below
        return path, f"error {type(error).__name__}: {error}"

    digest = hashlib.sha256(payload).hexdigest()
    target.parent.mkdir(parents=True, exist_ok=True)
    if digest != entry["sha256"]:
        target.with_suffix(target.suffix + ".mismatch").write_bytes(payload)
        return path, f"mismatch got {digest[:12]} want {entry['sha256'][:12]}"
    target.write_bytes(payload)
    return path, "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--jobs", type=int, default=8, help="parallel downloads (default 8)")
    parser.add_argument("--force", action="store_true", help="rewrite files that already match")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    generated = build_epub_edge_cases.build_all()
    counts: dict[str, int] = {}
    problems: list[str] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [
            pool.submit(fetch_one, path, entry, args.force, generated) for path, entry in sorted(manifest.items())
        ]
        for future in concurrent.futures.as_completed(futures):
            path, status = future.result()
            key = status.split()[0]
            counts[key] = counts.get(key, 0) + 1
            if key in {"error", "mismatch"}:
                problems.append(f"  {path}: {status}")

    print(f"{len(manifest)} files: " + ", ".join(f"{n} {k}" for k, n in sorted(counts.items())))
    if problems:
        print("\nNeeds attention:", file=sys.stderr)
        print("\n".join(problems), file=sys.stderr)
        print(
            "\nA source that moved or changed needs its entry in scripts/data/epub-edge-cases.json updated,"
            "\nand EPUB_EDGE_CASES.md updated with it.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
