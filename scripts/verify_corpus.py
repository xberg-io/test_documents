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

from __future__ import annotations

import argparse
import sys

from corpus_tools.hashing import sha256_bytes
from corpus_tools.http import (
    BUCKET_HEAD_TIMEOUT_SECONDS,
    BUCKET_OBJECT_TIMEOUT_SECONDS,
    CurlTransport,
    HttpError,
    get,
)
from corpus_tools.manifest import MANIFEST_FILENAME, lock_pins, object_url
from corpus_tools.paths import REPO_ROOT
from corpus_tools.pool import DEFAULT_JOBS, add_jobs_argument, map_parallel

# ~keep One curl process per batch rather than per object: process startup dominates a HEAD
# request, and curl reuses the connection across URLs given in a single invocation. The batching
# itself now lives in CurlTransport.head_many; what stays here is the INTERPRETATION of a result —
# mapping a URL back to its pin and phrasing the failure — which is corpus knowledge, not transport.
HTTP_OK = 200
HEAD_BATCH_SIZE = 64
MAX_REPORTED_FAILURES = 20
TRANSPORT = CurlTransport()


def head_batch(bucket: str, batch: list[str], pins: dict[str, int]) -> list[str]:
    urls = [object_url(bucket, sha256) for sha256 in batch]
    try:
        results = TRANSPORT.head_many(urls, timeout=BUCKET_HEAD_TIMEOUT_SECONDS)
    except HttpError as error:
        return [f"curl failed for a batch of {len(batch)}: {error.reason}"]

    failures: list[str] = []
    # ~keep strict=True: head_many returns exactly one result per URL, including a placeholder
    # for a response that never parsed. A length mismatch means that contract broke, and
    # silently zipping short would report a missing object as fine.
    for sha256, result in zip(batch, results, strict=True):
        if result.status is None:
            failures.append(f"{sha256}: no response parsed")
        elif result.status != HTTP_OK:
            failures.append(f"{sha256}: HTTP {result.status}")
        elif result.content_length is not None and result.content_length != pins[sha256]:
            failures.append(f"{sha256}: pinned size {pins[sha256]} but bucket serves {result.content_length}")
    return failures


def check_content(bucket: str, sha256: str) -> list[str]:
    try:
        payload = get(object_url(bucket, sha256), timeout=BUCKET_OBJECT_TIMEOUT_SECONDS, transport=TRANSPORT)
    except HttpError as error:
        return [f"{sha256}: {error.reason}"]
    actual = sha256_bytes(payload)
    return [] if actual == sha256 else [f"{sha256}: content hashes to {actual}"]


def evenly_spaced(items: list[str], count: int) -> list[str]:
    if count >= len(items):
        return items
    stride = len(items) / count
    return [items[int(index * stride)] for index in range(count)]


def report(label: str, total: int, failures: list[str]) -> int:
    print(f"{label}: {total - len(failures)}/{total} ok")
    for failure in failures[:MAX_REPORTED_FAILURES]:
        print(f"  {failure}", file=sys.stderr)
    if len(failures) > MAX_REPORTED_FAILURES:
        print(f"  ... and {len(failures) - MAX_REPORTED_FAILURES} more", file=sys.stderr)
    return len(failures)


def verify_metadata(bucket: str, pins: dict[str, int], *, jobs: int = DEFAULT_JOBS) -> int:
    ordered = sorted(pins)
    batches = [ordered[start : start + HEAD_BATCH_SIZE] for start in range(0, len(ordered), HEAD_BATCH_SIZE)]
    failures: list[str] = []
    for batch_failures in map_parallel(lambda batch: head_batch(bucket, batch, pins), batches, jobs=jobs):
        failures += batch_failures
    return report("metadata", len(ordered), failures)


def verify_content(bucket: str, pins: dict[str, int], sample: int, *, jobs: int = DEFAULT_JOBS) -> int:
    sampled = evenly_spaced(sorted(pins), sample)
    failures: list[str] = []
    for object_failures in map_parallel(lambda sha256: check_content(bucket, sha256), sampled, jobs=jobs):
        failures += object_failures
    return report("content", len(sampled), failures)


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
