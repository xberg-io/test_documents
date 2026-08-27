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
import json
import sys
from typing import Any

from corpus_tools.pool import THIRD_PARTY_SOURCE_JOBS, add_jobs_argument, run_parallel
from corpus_tools.regression import MANIFEST, fetch_direct, fetch_shard


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
