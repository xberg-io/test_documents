#!/usr/bin/env python3
"""Acquire pinned reference-only benchmarks outside Git, without bucket publication.

Fetch original bytes from immutable upstream revisions or verify an existing external
cache. The descriptor contains hashes and provenance only, not PDFs or raw ground truth.
Use --build-from-stages PARSEBENCH OLMOCR to regenerate it from verified external staging.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

from corpus_tools.benchmark_inventory import build_inventory
from corpus_tools.benchmark_upstreams import INVENTORY_PATH, SOURCES, fetch_one, load_inventory, safe_cache_root
from corpus_tools.pool import THIRD_PARTY_SOURCE_JOBS, add_jobs_argument, map_parallel


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=sorted(SOURCES), action="append", help="repeatable; default: both sources")
    parser.add_argument("--root", type=Path, help="external cache; default: ~/.cache/xberg/reference-benchmarks")
    parser.add_argument("--manifest", type=Path, default=INVENTORY_PATH)
    parser.add_argument("--verify-only", action="store_true", help="verify all selected local files without network")
    parser.add_argument("--build-from-stages", nargs=2, type=Path, metavar=("PARSEBENCH", "OLMOCR"))
    add_jobs_argument(parser, default=THIRD_PARTY_SOURCE_JOBS)
    args = parser.parse_args(argv)
    try:
        if args.build_from_stages:
            if args.source or args.root or args.verify_only:
                parser.error("--build-from-stages cannot be combined with acquisition options")
            count = build_inventory(args.build_from_stages[0], args.build_from_stages[1], args.manifest)
            print(f"generated {count} metadata pins at {args.manifest}")
            return 0
        return _acquire(args)
    except (OSError, ValueError, KeyError) as error:
        print(f"benchmark upstreams: {error}", file=sys.stderr)
        return 1


def _acquire(args: argparse.Namespace) -> int:
    if args.jobs < 1:
        raise ValueError("jobs must be positive")
    root = safe_cache_root(args.root or Path.home() / ".cache/xberg/reference-benchmarks")
    pins = [pin for pin in load_inventory(args.manifest) if not args.source or pin.source in args.source]
    if not pins:
        raise ValueError("empty upstream selection")
    results = list(map_parallel(lambda pin: fetch_one(pin, root, verify_only=args.verify_only), pins, jobs=args.jobs))
    counts = Counter(status.split()[0] for status in results)
    failures = [
        (pin.path, status) for pin, status in zip(pins, results, strict=True) if status not in {"ok", "skipped"}
    ]
    print(f"{len(results)}/{len(pins)} checked; statuses={dict(counts)}; root={root}")
    for path, status in failures[:20]:
        print(f"  {path}: {status}", file=sys.stderr)
    return 1 if failures or len(results) != len(pins) else 0


if __name__ == "__main__":
    sys.exit(main())
