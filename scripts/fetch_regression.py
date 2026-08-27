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

import argparse
import collections
import functools
import io
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

from corpus_tools import paths
from corpus_tools.http import SHARD_TIMEOUT_SECONDS, SOURCE_FILE_TIMEOUT_SECONDS, UrllibTransport, get
from corpus_tools.materialize import STATUS_SKIPPED, is_current, materialize_one, write_verified
from corpus_tools.pool import THIRD_PARTY_SOURCE_JOBS, add_jobs_argument, run_parallel

REPO_ROOT = paths.REPO_ROOT
MANIFEST = Path(__file__).resolve().parent / "data" / "regression-objects.json"


TRANSPORT = UrllibTransport()


def fetch_direct(path: str, entry: dict[str, Any], force: bool) -> list[tuple[str, str]]:
    status = materialize_one(
        REPO_ROOT / path,
        entry["sha256"],
        lambda: get(entry["url"], timeout=SOURCE_FILE_TIMEOUT_SECONDS, transport=TRANSPORT),
        force=force,
    )
    return [(path, status)]


def fetch_shard(url: str, members: list[tuple[str, dict[str, Any]]], force: bool) -> list[tuple[str, str]]:
    """Download one archive and take every member wanted from it."""
    wanted = [(p, e) for p, e in members if force or not is_current(REPO_ROOT / p, e["sha256"])]
    if not wanted:
        return [(p, STATUS_SKIPPED) for p, _ in members]
    try:
        blob = get(url, timeout=SHARD_TIMEOUT_SECONDS, transport=TRANSPORT)
    except Exception as error:  # noqa: BLE001 - one bad shard must not abort the whole run
        return [(p, f"error {type(error).__name__}: {error}") for p, _ in wanted]

    results: list[tuple[str, str]] = []
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        by_basename = {Path(n).name: n for n in archive.namelist()}
        for path, entry in wanted:
            name = by_basename.get(entry["member"])
            if name is None:
                results.append((path, f"error member {entry['member']} not in shard"))
                continue
            results.append((path, write_verified(REPO_ROOT / path, archive.read(name), entry["sha256"])))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_jobs_argument(parser, default=THIRD_PARTY_SOURCE_JOBS)
    parser.add_argument("--force", action="store_true", help="re-download files that already match")
    parser.add_argument("--include", default="", help="only paths starting with this prefix")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    if args.include:
        manifest = {k: v for k, v in manifest.items() if k.startswith(args.include)}
        if not manifest:
            print(f"nothing matches --include {args.include}", file=sys.stderr)
            return 1

    shards: dict[str, list[tuple[str, dict[str, Any]]]] = collections.defaultdict(list)
    direct: list[tuple[str, dict[str, Any]]] = []
    for path, entry in sorted(manifest.items()):
        (shards[entry["url"]].append((path, entry)) if "member" in entry else direct.append((path, entry)))

    counts: collections.Counter[str] = collections.Counter()
    problems: list[str] = []

    def record(path: str, status: str) -> None:
        counts[status.split(maxsplit=1)[0]] += 1
        if status.split(maxsplit=1)[0] in {"error", "mismatch"}:
            problems.append(f"  {path}: {status}")

    calls = [functools.partial(fetch_direct, p, e, args.force) for p, e in direct]
    calls += [functools.partial(fetch_shard, url, members, args.force) for url, members in shards.items()]
    # ~keep Both fetchers return a list of results: a direct file yields one, a shard yields one
    # per member taken from it. Same shape means one homogeneous pool and no isinstance at the
    # call site to tell the two apart.
    for outcome in run_parallel(calls, jobs=args.jobs):
        for path, status in outcome:
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
