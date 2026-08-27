"""The check that stands between a broken bucket and every consumer's CI.

~keep This module had no tests at all, which is the wrong place for a coverage hole: it is the ONLY
thing this repository's CI actually proves. Every mutation the reviewers tried survived — dropping
the Content-Length comparison, and replacing the deterministic sample with `items[:count]`. Both
leave the job green while it verifies nothing, and green is exactly what everyone reads it as.

Network-free: `head_batch` and `check_content` take their bytes from a stub transport, so what is
exercised is the interpretation of a curl result, which is where the logic actually lives.
"""

import unittest

from corpus_tools.corpus import verify as verify_corpus
from corpus_tools.http import HeadResult, HttpError

DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
BUCKET = "example-bucket"


class StubTransport:
    """Returns canned head results / payloads. Deliberately not a mock framework."""

    def __init__(self, head_results: list[HeadResult] | None = None, payload: bytes = b"") -> None:
        self.head_results = head_results or []
        self.payload = payload
        self.head_calls = 0

    def head_many(self, urls, *, timeout):
        self.head_calls += 1
        return self.head_results


class EvenlySpacedTest(unittest.TestCase):
    def test_should_pick_the_same_sample_every_run_so_a_failure_is_reproducible(self) -> None:
        items = [f"{index:064d}" for index in range(100)]

        self.assertEqual(verify_corpus.evenly_spaced(items, 5), verify_corpus.evenly_spaced(items, 5))

    def test_should_spread_the_sample_across_the_whole_list_rather_than_taking_a_prefix(self) -> None:
        # ~keep `items[:count]` passes a naive count assertion and samples only the beginning, so
        # a bucket that lost its later objects would still report a clean run.
        items = [f"{index:064d}" for index in range(100)]

        sample = verify_corpus.evenly_spaced(items, 5)

        self.assertEqual(len(sample), 5)
        self.assertNotEqual(sample, items[:5])
        self.assertGreater(items.index(sample[-1]), 50)

    def test_should_return_everything_when_the_sample_is_larger_than_the_corpus(self) -> None:
        items = [DIGEST_A, DIGEST_B]

        self.assertEqual(sorted(verify_corpus.evenly_spaced(items, 10)), sorted(items))


class HeadBatchTest(unittest.TestCase):
    def _batch(self, results: list[HeadResult]) -> list[str]:
        original = verify_corpus.TRANSPORT
        verify_corpus.TRANSPORT = StubTransport(results)
        try:
            return verify_corpus.head_batch(BUCKET, [DIGEST_A, DIGEST_B], {DIGEST_A: 10, DIGEST_B: 20})
        finally:
            verify_corpus.TRANSPORT = original

    def _url(self, digest: str) -> str:
        return f"https://storage.googleapis.com/{BUCKET}/objects/{digest}"

    def test_should_report_nothing_when_every_object_matches_its_pin(self) -> None:
        failures = self._batch(
            [
                HeadResult(self._url(DIGEST_A), 200, 10),
                HeadResult(self._url(DIGEST_B), 200, 20),
            ]
        )

        self.assertEqual(failures, [])

    def test_should_report_an_object_the_bucket_no_longer_serves(self) -> None:
        failures = self._batch(
            [
                HeadResult(self._url(DIGEST_A), 404, None),
                HeadResult(self._url(DIGEST_B), 200, 20),
            ]
        )

        self.assertEqual(len(failures), 1)
        self.assertIn("404", failures[0])
        self.assertIn(DIGEST_A, failures[0])

    def test_should_report_an_object_whose_size_disagrees_with_the_manifest(self) -> None:
        # ~keep This is the assertion the reviewers deleted and nothing noticed. A size mismatch
        # means the bucket is serving different bytes than corpus.lock.json pins.
        failures = self._batch(
            [
                HeadResult(self._url(DIGEST_A), 200, 999),
                HeadResult(self._url(DIGEST_B), 200, 20),
            ]
        )

        self.assertEqual(len(failures), 1)
        self.assertIn("pinned size 10", failures[0])
        self.assertIn("999", failures[0])

    def test_should_report_an_object_whose_response_never_parsed(self) -> None:
        # ~keep curl can exit 0 with a response missing from the write-out. Counting that as fine
        # is how a missing object reads as success.
        failures = self._batch(
            [
                HeadResult(self._url(DIGEST_A), None, None),
                HeadResult(self._url(DIGEST_B), 200, 20),
            ]
        )

        self.assertEqual(len(failures), 1)
        self.assertIn("no response parsed", failures[0])

    def test_should_report_a_whole_batch_when_the_transport_fails(self) -> None:
        class FailingTransport:
            def head_many(self, urls, *, timeout):
                raise HttpError("a batch of 2", "curl failed: network down")

        original = verify_corpus.TRANSPORT
        verify_corpus.TRANSPORT = FailingTransport()
        try:
            failures = verify_corpus.head_batch(BUCKET, [DIGEST_A, DIGEST_B], {DIGEST_A: 10, DIGEST_B: 20})
        finally:
            verify_corpus.TRANSPORT = original

        self.assertEqual(len(failures), 1)
        self.assertIn("batch of 2", failures[0])


class ReportTest(unittest.TestCase):
    def test_should_return_the_failure_count_so_the_exit_code_is_meaningful(self) -> None:
        self.assertEqual(verify_corpus.report("metadata", 10, ["a: bad", "b: bad"]), 2)

    def test_should_return_zero_when_everything_passed(self) -> None:
        self.assertEqual(verify_corpus.report("metadata", 10, []), 0)

    def test_should_cap_how_many_failures_it_prints_without_losing_the_count(self) -> None:
        failures = [f"{index}: bad" for index in range(verify_corpus.MAX_REPORTED_FAILURES + 5)]

        self.assertEqual(verify_corpus.report("metadata", 100, failures), len(failures))
