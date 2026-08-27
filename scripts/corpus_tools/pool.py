"""One place to decide how much of the network to use at once.

~keep The concurrency limit was configured three different ways: a MAX_WORKERS constant in
fetch_corpus and verify_corpus, and a --jobs flag defaulting to 8 in two fetchers and 6 in a third.
Nothing recorded why 6, so it read like a typo. It is not — see DEFAULT_JOBS below.
"""

import argparse
import concurrent.futures
from collections.abc import Callable, Iterable, Iterator
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")

DEFAULT_JOBS = 8

# ~keep The regression corpus keeps a lower default, and the reason is real rather than historical:
# its ~1,500 requests go to gutenberg.org, ebi.ac.uk and arxiv.org, all of which throttle or block
# bulk clients. Everything else here talks to one GCS bucket, which does not care. The honest fix
# is a per-host limit rather than a global one; until then this is the number and this is why.
THIRD_PARTY_SOURCE_JOBS = 6


def add_jobs_argument(parser: argparse.ArgumentParser, *, default: int = DEFAULT_JOBS) -> None:
    """Add the --jobs flag, so every tool spells it and documents it identically."""
    parser.add_argument(
        "--jobs",
        type=int,
        default=default,
        help=f"parallel transfers (default {default})",
    )


def map_parallel(function: Callable[[T], R], items: Iterable[T], *, jobs: int = DEFAULT_JOBS) -> Iterator[R]:
    """Apply `function` across `items`, yielding results in input order.

    ~keep Order-preserving because two callers report a per-item failure list and a stable order
    makes a failing run reproducible for whoever reads it.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        yield from pool.map(function, items)


def run_parallel(calls: Iterable[Callable[[], R]], *, jobs: int = DEFAULT_JOBS) -> Iterator[R]:
    """Run each thunk, yielding results as they complete rather than in order."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = [pool.submit(call) for call in calls]
        for future in concurrent.futures.as_completed(futures):
            yield future.result()
