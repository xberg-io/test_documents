"""Parallelism: order, defaults, and the one default that is not a round number.

~keep This module had no tests, and all three obvious mutations survived the rest of the suite:
reversing map_parallel's output, forcing DEFAULT_JOBS to 1, and making add_jobs_argument ignore its
`default`. Each is silent — the fetchers still work, just wrongly — and the third one specifically
would get the regression fetcher rate-limited by third-party hosts with no local symptom at all.
"""

import argparse
import time
import unittest

from corpus_tools.pool import (
    DEFAULT_JOBS,
    THIRD_PARTY_SOURCE_JOBS,
    add_jobs_argument,
    map_parallel,
    run_parallel,
)


class MapParallelTest(unittest.TestCase):
    def test_should_yield_results_in_input_order_even_when_later_items_finish_first(self) -> None:
        # ~keep Order preservation is load-bearing, not incidental: two callers build a per-item
        # failure list from this, and a stable order is what makes a failing run reproducible for
        # whoever reads the output. Varying the latency is what makes the test able to fail — with
        # uniform work, a completion-ordered implementation would pass by luck.
        def slow_for_early_items(item: int) -> int:
            time.sleep(0.02 if item < 2 else 0.0)
            return item

        results = list(map_parallel(slow_for_early_items, [0, 1, 2, 3, 4], jobs=5))

        self.assertEqual(results, [0, 1, 2, 3, 4])

    def test_should_apply_the_function_to_every_item_exactly_once(self) -> None:
        seen: list[int] = []

        results = list(map_parallel(lambda item: (seen.append(item), item * 2)[1], range(20), jobs=4))

        self.assertEqual(sorted(seen), list(range(20)))
        self.assertEqual(results, [item * 2 for item in range(20)])

    def test_should_propagate_an_exception_from_a_worker(self) -> None:
        def explode(item: int) -> int:
            if item == 3:
                message = "item 3 is bad"
                raise ValueError(message)
            return item

        with self.assertRaises(ValueError):
            list(map_parallel(explode, range(6), jobs=2))

    def test_should_handle_an_empty_input_without_starting_work(self) -> None:
        self.assertEqual(list(map_parallel(lambda item: item, [], jobs=4)), [])


class RunParallelTest(unittest.TestCase):
    def test_should_run_every_thunk_exactly_once(self) -> None:
        calls: list[int] = []

        results = list(run_parallel([lambda index=index: (calls.append(index), index)[1] for index in range(10)]))

        self.assertEqual(sorted(calls), list(range(10)))
        self.assertEqual(sorted(results), list(range(10)))

    def test_should_propagate_an_exception_from_a_thunk(self) -> None:
        def explode() -> int:
            message = "boom"
            raise RuntimeError(message)

        with self.assertRaises(RuntimeError):
            list(run_parallel([explode]))


class JobsArgumentTest(unittest.TestCase):
    def test_should_default_to_the_shared_job_count(self) -> None:
        parser = argparse.ArgumentParser()
        add_jobs_argument(parser)

        self.assertEqual(parser.parse_args([]).jobs, DEFAULT_JOBS)

    def test_should_honour_a_caller_supplied_default(self) -> None:
        # ~keep The regression fetcher passes THIRD_PARTY_SOURCE_JOBS. If add_jobs_argument ignored
        # its `default`, that fetcher would silently go to 8 against gutenberg, arxiv and ebi.ac.uk,
        # which throttle bulk clients — a failure with no local symptom whatsoever.
        parser = argparse.ArgumentParser()
        add_jobs_argument(parser, default=THIRD_PARTY_SOURCE_JOBS)

        self.assertEqual(parser.parse_args([]).jobs, THIRD_PARTY_SOURCE_JOBS)

    def test_should_let_the_command_line_override_the_default(self) -> None:
        parser = argparse.ArgumentParser()
        add_jobs_argument(parser, default=THIRD_PARTY_SOURCE_JOBS)

        self.assertEqual(parser.parse_args(["--jobs", "3"]).jobs, 3)

    def test_should_keep_the_third_party_default_below_the_bucket_default(self) -> None:
        # ~keep If these ever equalise, either the throttling concern went away or someone
        # "tidied" the constant. Both deserve a failing test rather than a silent change.
        self.assertLess(THIRD_PARTY_SOURCE_JOBS, DEFAULT_JOBS)
