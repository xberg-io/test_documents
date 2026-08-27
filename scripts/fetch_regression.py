#!/usr/bin/env python3
"""Fetch the regression corpus from its original sources.

The regression corpus is bulk material: a change that alters output anywhere it
should not is what this corpus exists to catch. Its bytes live in the bucket
rather than in git, so this script obtains them and writes each one to the path
it belongs at. Publish them the usual way afterwards:

    python3 scripts/fetch_regression.py
    python3 scripts/publish_corpus.py --bucket xberg-test-documents

Only the vendored documents appear in `scripts/data/regression-objects.json`. Anything
listed as reference in `REGRESSION_PROVENANCE.md` is deliberately absent: those
carry ShareAlike, NonCommercial, or publisher-only redistribution terms, so the
corpus records where they came from and never hosts them.

govdocs1 publishes shards rather than individual files, so those entries name
the shard and the member inside it. A shard is downloaded once and every member
taken from it before it is discarded.
"""

from __future__ import annotations

import argparse
import collections
import concurrent.futures
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

from corpus_tools import paths
from corpus_tools.hashing import sha256_bytes, sha256_file

REPO_ROOT = paths.REPO_ROOT
MANIFEST = Path(__file__).resolve().parent / "data" / "regression-objects.json"
TIMEOUT = 300
RETRIES = 3


def download(url: str) -> bytes:
    last = ""
    for _attempt in range(1, RETRIES + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "xberg-test-documents"})
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return response.read()
        except Exception as error:  # noqa: BLE001 - retry any transport failure
            last = f"{type(error).__name__}: {error}"
    raise RuntimeError(last)


def write_checked(path: str, payload: bytes, expected: str) -> str:
    target = REPO_ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    digest = sha256_bytes(payload)
    if digest != expected:
        target.with_suffix(target.suffix + ".mismatch").write_bytes(payload)
        return f"mismatch got {digest[:12]} want {expected[:12]}"
    target.write_bytes(payload)
    return "ok"


def up_to_date(path: str, expected: str) -> bool:
    target = REPO_ROOT / path
    return target.exists() and sha256_file(target) == expected


def fetch_direct(path: str, entry: dict, force: bool) -> tuple[str, str]:
    if not force and up_to_date(path, entry["sha256"]):
        return path, "skipped"
    try:
        return path, write_checked(path, download(entry["url"]), entry["sha256"])
    except Exception as error:  # noqa: BLE001 - report rather than abort the run
        return path, f"error {error}"


def fetch_shard(url: str, members: list[tuple[str, dict]], force: bool) -> list[tuple[str, str]]:
    """Download one archive and take every member wanted from it."""
    wanted = [(p, e) for p, e in members if force or not up_to_date(p, e["sha256"])]
    if not wanted:
        return [(p, "skipped") for p, _ in members]
    try:
        blob = download(url)
    except Exception as error:  # noqa: BLE001
        return [(p, f"error {error}") for p, _ in wanted]

    results: list[tuple[str, str]] = []
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        by_basename = {Path(n).name: n for n in archive.namelist()}
        for path, entry in wanted:
            name = by_basename.get(entry["member"])
            if name is None:
                results.append((path, f"error member {entry['member']} not in shard"))
                continue
            results.append((path, write_checked(path, archive.read(name), entry["sha256"])))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--jobs", type=int, default=6, help="parallel downloads (default 6)")
    parser.add_argument("--force", action="store_true", help="re-download files that already match")
    parser.add_argument("--include", default="", help="only paths starting with this prefix")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    if args.include:
        manifest = {k: v for k, v in manifest.items() if k.startswith(args.include)}
        if not manifest:
            print(f"nothing matches --include {args.include}", file=sys.stderr)
            return 1

    shards: dict[str, list[tuple[str, dict]]] = collections.defaultdict(list)
    direct: list[tuple[str, dict]] = []
    for path, entry in sorted(manifest.items()):
        (shards[entry["url"]].append((path, entry)) if "member" in entry else direct.append((path, entry)))

    counts: collections.Counter = collections.Counter()
    problems: list[str] = []

    def record(path: str, status: str) -> None:
        counts[status.split()[0]] += 1
        if status.split()[0] in {"error", "mismatch"}:
            problems.append(f"  {path}: {status}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(fetch_direct, p, e, args.force) for p, e in direct]
        futures += [pool.submit(fetch_shard, url, members, args.force) for url, members in shards.items()]
        for future in concurrent.futures.as_completed(futures):
            outcome = future.result()
            for path, status in outcome if isinstance(outcome, list) else [outcome]:
                record(path, status)

    print(f"{len(manifest)} objects: " + ", ".join(f"{n} {k}" for k, n in sorted(counts.items())))
    if problems:
        print("\nNeeds attention:", file=sys.stderr)
        print("\n".join(problems[:40]), file=sys.stderr)
        if len(problems) > 40:
            print(f"  ... and {len(problems) - 40} more", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
