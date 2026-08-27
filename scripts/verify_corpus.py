#!/usr/bin/env python3
"""Verify every object pinned by corpus.lock.json is fetchable from the public bucket.

Anonymous HTTPS via curl — no credentials, no SDK, no Python dependencies — because that is
exactly the path consumers take. Two modes:

  --bucket B              HEAD every object; fail on a non-200 or a Content-Length that
                          disagrees with the pinned size.
  --bucket B --sample N   download N objects in full and check their sha256.

A full-body check of every object would move ~578 MiB per run, so the cheap metadata check
covers all of them and the expensive hash check covers a deterministic sample (evenly spaced
over the sorted sha256 list, so it is reproducible yet not always the same handful).
"""

import argparse
import sys

from corpus_tools.corpus.verify import verify_content, verify_metadata
from corpus_tools.manifest import MANIFEST_FILENAME, lock_pins
from corpus_tools.paths import REPO_ROOT
from corpus_tools.pool import add_jobs_argument


# ~keep One curl process per batch rather than per object: process startup dominates a HEAD
# request, and curl reuses the connection across URLs given in a single invocation. The batching
# itself now lives in CurlTransport.head_many; what stays here is the INTERPRETATION of a result —
# mapping a URL back to its pin and phrasing the failure — which is corpus knowledge, not transport.
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", required=True, help="GCS bucket name, without the gs:// prefix")
    add_jobs_argument(parser)
    parser.add_argument(
        "--sample",
        type=int,
        default=0,
        help="download this many objects in full and verify their sha256 instead of HEADing all",
    )
    args = parser.parse_args(argv)

    root = REPO_ROOT
    pins = lock_pins(root / MANIFEST_FILENAME)
    if not pins:
        print(f"{MANIFEST_FILENAME} pins no objects", file=sys.stderr)
        return 1

    failures = (
        verify_content(args.bucket, pins, args.sample, jobs=args.jobs)
        if args.sample
        else verify_metadata(args.bucket, pins, jobs=args.jobs)
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
