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
import json
import subprocess
import sys
from pathlib import Path

from corpus_tools.hashing import sha256_bytes
from corpus_tools.paths import REPO_ROOT
from corpus_tools.pool import DEFAULT_JOBS, add_jobs_argument, map_parallel

MANIFEST_FILENAME = "corpus.lock.json"
OBJECTS_PREFIX = "objects"
REQUEST_TIMEOUT_SECONDS = 60
# ~keep One curl process per batch rather than per object: process startup dominates a HEAD
# request, and curl reuses the connection across URLs given in a single invocation.
HEAD_BATCH_SIZE = 64
MAX_REPORTED_FAILURES = 20


def object_url(bucket: str, sha256: str) -> str:
    return f"https://storage.googleapis.com/{bucket}/{OBJECTS_PREFIX}/{sha256}"


def load_pins(root: Path) -> dict[str, int]:
    """Map sha256 -> size. Duplicate paths collapse onto one object, which is the point."""
    manifest = json.loads((root / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    return {entry["sha256"]: entry["size"] for entry in manifest["objects"].values()}


def head_batch(bucket: str, batch: list[str], pins: dict[str, int]) -> list[str]:
    command = ["curl", "-sS", "--head", "--max-time", str(REQUEST_TIMEOUT_SECONDS)]
    command += ["-w", "%{http_code} %header{content-length} %{url_effective}\n"]
    for sha256 in batch:
        # ~keep -o must repeat per URL; curl applies a single -o to the first transfer only and
        # dumps every later response to stdout, which corrupts the write-out lines we parse.
        command += ["-o", "/dev/null", object_url(bucket, sha256)]

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return [f"curl failed for a batch of {len(batch)}: {result.stderr.strip()}"]

    failures: list[str] = []
    seen: set[str] = set()
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) != 3:
            continue
        status, content_length, url = fields
        sha256 = url.rsplit("/", 1)[-1]
        seen.add(sha256)
        if status != "200":
            failures.append(f"{sha256}: HTTP {status}")
        elif content_length.isdigit() and int(content_length) != pins[sha256]:
            failures.append(f"{sha256}: pinned size {pins[sha256]} but bucket serves {content_length}")
    failures += [f"{sha256}: no response parsed" for sha256 in batch if sha256 not in seen]
    return failures


def check_content(bucket: str, sha256: str) -> list[str]:
    result = subprocess.run(
        ["curl", "-sS", "--fail", "--max-time", str(REQUEST_TIMEOUT_SECONDS), object_url(bucket, sha256)],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return [f"{sha256}: download failed: {result.stderr.decode().strip()}"]
    actual = sha256_bytes(result.stdout)
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
    pins = load_pins(root)
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
