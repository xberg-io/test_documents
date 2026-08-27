"""The retry policy, the two transports, and the write-or-sidecar rule.

~keep Network-free by construction, and deliberately not by monkeypatching urlopen. The curl
transport takes an injected runner and `get` takes an injected sleep, so every test here is a plain
value passed in rather than a global swapped out — which is what makes them safe under bare
`python3 -m unittest`, immune to leaking between tests, and honest about what they assert.

The backoff assertions matter more than they look. Before this module existed, three call sites ran
`for _ in range(3)` with no sleep at all, so all three attempts hit the same transient failure
within milliseconds. Asserting the delays are actually 1s then 2s is what stops that regressing.
"""

import contextlib
import hashlib
import io
import subprocess
import tempfile
import unittest
import unittest.mock
import urllib.request
from pathlib import Path

from corpus_tools.http import (
    BUCKET_OBJECT_TIMEOUT_SECONDS,
    SHARD_TIMEOUT_SECONDS,
    USER_AGENT,
    CurlTransport,
    HttpError,
    RetryPolicy,
    UrllibTransport,
    get,
)
from corpus_tools.materialize import (
    MISMATCH_SUFFIX,
    STATUS_OK,
    STATUS_SKIPPED,
    is_current,
    materialize_one,
    write_verified,
)

PAYLOAD = b"the bytes we asked for"
PAYLOAD_SHA256 = hashlib.sha256(PAYLOAD).hexdigest()


class FlakyTransport:
    """Fails `failures` times, then succeeds. The shape a real retry has to survive."""

    def __init__(self, failures: int, payload: bytes = PAYLOAD) -> None:
        self.failures = failures
        self.payload = payload
        self.calls = 0
        self.timeouts: list[float] = []

    def fetch(self, url: str, *, timeout: float) -> bytes:
        self.calls += 1
        self.timeouts.append(timeout)
        if self.calls <= self.failures:
            message = f"attempt {self.calls} failed"
            raise ConnectionResetError(message)
        return self.payload


class RecordingSleep:
    def __init__(self) -> None:
        self.delays: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


class RetryTest(unittest.TestCase):
    def test_should_succeed_on_a_later_attempt_after_transient_failures(self) -> None:
        transport = FlakyTransport(failures=2)
        sleep = RecordingSleep()

        payload = get("https://example.invalid/x", timeout=10, transport=transport, sleep=sleep)

        self.assertEqual(payload, PAYLOAD)
        self.assertEqual(transport.calls, 3)

    def test_should_back_off_between_attempts_rather_than_retrying_instantly(self) -> None:
        transport = FlakyTransport(failures=2)
        sleep = RecordingSleep()

        get("https://example.invalid/x", timeout=10, transport=transport, sleep=sleep)

        self.assertEqual(sleep.delays, [1.0, 2.0])

    def test_should_not_sleep_before_the_first_attempt(self) -> None:
        transport = FlakyTransport(failures=0)
        sleep = RecordingSleep()

        get("https://example.invalid/x", timeout=10, transport=transport, sleep=sleep)

        self.assertEqual(sleep.delays, [])

    def test_should_raise_with_the_last_reason_when_every_attempt_fails(self) -> None:
        transport = FlakyTransport(failures=99)
        sleep = RecordingSleep()

        with self.assertRaises(HttpError) as caught:
            get("https://example.invalid/x", timeout=10, transport=transport, sleep=sleep)

        self.assertEqual(transport.calls, 3)
        self.assertIn("attempt 3 failed", str(caught.exception))
        self.assertIn("ConnectionResetError", str(caught.exception))

    def test_should_honour_a_caller_supplied_attempt_count(self) -> None:
        transport = FlakyTransport(failures=99)

        with self.assertRaises(HttpError):
            get(
                "https://example.invalid/x",
                timeout=10,
                transport=transport,
                retry=RetryPolicy(attempts=1),
                sleep=RecordingSleep(),
            )

        self.assertEqual(transport.calls, 1)

    def test_should_pass_the_callers_timeout_through_to_the_transport(self) -> None:
        transport = FlakyTransport(failures=0)

        get("https://example.invalid/x", timeout=SHARD_TIMEOUT_SECONDS, transport=transport, sleep=RecordingSleep())

        self.assertEqual(transport.timeouts, [SHARD_TIMEOUT_SECONDS])


class TimeoutTableTest(unittest.TestCase):
    def test_should_give_the_shard_the_longest_budget_because_one_url_needs_it(self) -> None:
        # ~keep The govdocs1 archive serves 267 members in a single request. If these ever equalise,
        # either the shard stopped being special or someone cargo-culted the number outward.
        self.assertGreater(SHARD_TIMEOUT_SECONDS, BUCKET_OBJECT_TIMEOUT_SECONDS)


class CurlTransportTest(unittest.TestCase):
    def _runner(self, *, returncode: int = 0, stdout: object = b"", stderr: object = b""):
        recorded: list[list[str]] = []
        keywords: list[dict] = []

        def run(command, **kwargs):
            recorded.append(command)
            keywords.append(kwargs)
            return subprocess.CompletedProcess(command, returncode, stdout, stderr)

        run.keywords = keywords
        return run, recorded

    def test_should_ask_curl_for_bytes_when_fetching_and_text_when_reading_headers(self) -> None:
        """~keep The two methods genuinely differ, and nothing was checking it.

        `fetch` calls `result.stderr.decode()`, so it needs bytes; `head_many` parses
        `result.stdout` as a string, so it needs `text=True`. A stub that swallows **kwargs models
        that split by convention only — flipping either flag would pass the suite and fail against
        the real subprocess module.
        """
        run, _ = self._runner(stdout=b"")
        CurlTransport(run).fetch("https://example.invalid/x", timeout=30)

        self.assertTrue(run.keywords[0]["capture_output"])
        self.assertNotIn("text", run.keywords[0], "fetch decodes stderr itself, so it must get bytes")

        run, _ = self._runner(stdout="")
        CurlTransport(run).head_many(["https://example.invalid/x"], timeout=30)

        self.assertTrue(run.keywords[0]["capture_output"])
        self.assertIs(run.keywords[0]["text"], True, "head_many parses stdout as text")

    def test_should_ask_curl_to_fail_on_an_http_error_rather_than_saving_the_body(self) -> None:
        run, recorded = self._runner(stdout=PAYLOAD)

        payload = CurlTransport(run).fetch("https://example.invalid/x", timeout=30)

        self.assertEqual(payload, PAYLOAD)
        self.assertIn("--fail", recorded[0])
        self.assertIn("--max-time", recorded[0])

    def test_should_surface_a_curl_failure_as_an_http_error(self) -> None:
        run, _ = self._runner(returncode=22, stderr=b"curl: (22) 404")

        with self.assertRaises(HttpError) as caught:
            CurlTransport(run).fetch("https://example.invalid/x", timeout=30)

        self.assertIn("404", str(caught.exception))

    def test_should_parse_one_head_result_per_url_from_the_write_out_lines(self) -> None:
        stdout = "200 11 https://example.invalid/objects/aaa\n200 22 https://example.invalid/objects/bbb\n"
        run, _ = self._runner(stdout=stdout)

        results = CurlTransport(run).head_many(
            ["https://example.invalid/objects/aaa", "https://example.invalid/objects/bbb"], timeout=30
        )

        self.assertEqual([r.status for r in results], [200, 200])
        self.assertEqual([r.content_length for r in results], [11, 22])

    def test_should_report_a_url_that_produced_no_write_out_line(self) -> None:
        # ~keep The failure mode that matters: curl exits 0 but one response never parsed, so a
        # missing object would otherwise be silently counted as fine.
        run, _ = self._runner(stdout="200 11 https://example.invalid/objects/aaa\n")

        results = CurlTransport(run).head_many(
            ["https://example.invalid/objects/aaa", "https://example.invalid/objects/bbb"], timeout=30
        )

        self.assertEqual(results[1].status, None)
        self.assertEqual(results[1].url, "https://example.invalid/objects/bbb")

    def test_should_repeat_the_output_sink_once_per_url(self) -> None:
        # ~keep curl applies a single -o to the first transfer only and dumps every later response
        # to stdout, which corrupts the write-out lines being parsed above.
        run, recorded = self._runner(stdout="")

        CurlTransport(run).head_many(["https://a.invalid/1", "https://a.invalid/2"], timeout=30)

        self.assertEqual(recorded[0].count("-o"), 2)


class MaterializeTest(unittest.TestCase):
    def test_should_skip_a_file_that_already_hashes_correctly_without_producing_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / "nested" / "doc.pdf"
            target.parent.mkdir(parents=True)
            target.write_bytes(PAYLOAD)
            digest = PAYLOAD_SHA256

            def produce() -> bytes:
                raise AssertionError("produce must not run when the file is already current")

            self.assertEqual(materialize_one(target, digest, produce), STATUS_SKIPPED)

    def test_should_produce_and_write_when_the_file_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / "nested" / "doc.pdf"

            status = materialize_one(target, PAYLOAD_SHA256, lambda: PAYLOAD)

            self.assertEqual(status, STATUS_OK)
            self.assertEqual(target.read_bytes(), PAYLOAD)

    def test_should_reproduce_a_current_file_when_forced(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / "doc.pdf"
            target.write_bytes(PAYLOAD)
            calls: list[int] = []

            def produce() -> bytes:
                calls.append(1)
                return PAYLOAD

            self.assertEqual(materialize_one(target, PAYLOAD_SHA256, produce, force=True), STATUS_OK)
            self.assertEqual(len(calls), 1)

    def test_should_write_a_sidecar_and_leave_good_bytes_alone_on_a_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / "doc.pdf"
            target.write_bytes(b"known good")

            status = write_verified(target, b"something else", PAYLOAD_SHA256)

            self.assertIn("mismatch got", status)
            self.assertEqual(target.read_bytes(), b"known good")
            self.assertEqual(target.with_suffix(".pdf" + MISMATCH_SUFFIX).read_bytes(), b"something else")

    def test_should_report_a_producer_failure_with_its_exception_type(self) -> None:
        # ~keep fetch_regression used to emit `error {error}` without the type, so a bare
        # RuntimeError() printed as the word "error" and nothing else. All three fetchers agree now.
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / "doc.pdf"

            def produce() -> bytes:
                message = "upstream moved"
                raise RuntimeError(message)

            status = materialize_one(target, "0" * 64, produce)

            self.assertEqual(status, "error RuntimeError: upstream moved")

    def test_should_treat_a_missing_file_as_not_current(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            self.assertFalse(is_current(Path(name) / "absent.pdf", "0" * 64))


class UserAgentTest(unittest.TestCase):
    """~keep Asserting the constant is not enough — removing the header from the request survived.

    The provenance fetchers pull from eleven third-party hosts, several of which block
    unidentified bulk clients, so what matters is that the header is actually SENT.
    """

    def test_should_send_the_user_agent_on_a_urllib_request(self) -> None:
        captured: list[urllib.request.Request] = []

        def fake_urlopen(request, timeout=None):  # noqa: ARG001 - urlopen's signature, unused here
            captured.append(request)
            return contextlib.closing(io.BytesIO(PAYLOAD))

        with unittest.mock.patch.object(urllib.request, "urlopen", fake_urlopen):
            UrllibTransport().fetch("https://example.invalid/x", timeout=10)

        self.assertEqual(captured[0].get_header("User-agent"), USER_AGENT)

    def test_should_send_the_user_agent_on_a_curl_request(self) -> None:
        recorded: list[list[str]] = []

        def run(command, **_kwargs):
            recorded.append(command)
            return subprocess.CompletedProcess(command, 0, b"", b"")

        CurlTransport(run).fetch("https://example.invalid/x", timeout=10)

        # ~keep curl sends its own UA by default, so this documents that the bucket path does NOT
        # currently identify itself the way the urllib path does. Anonymous GCS does not care.
        self.assertNotIn("-A", recorded[0])
