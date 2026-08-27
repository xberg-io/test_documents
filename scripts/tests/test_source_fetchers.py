"""The provenance fetchers, and the shard path that carries 267 objects on one download.

~keep These had no tests. The shard logic in particular is the highest-risk untested code left:
govdocs1 publishes archives rather than files, so one download yields hundreds of corpus objects,
and members are located by BASENAME inside the archive — a real collision hazard that nothing was
checking. The reviewers' mutant, deleting the missing-member branch, survived the whole suite.

Network-free: every fetch goes through an injected transport, so what is exercised is the zip
handling and the status vocabulary rather than a mock returning what it was told to.
"""

import io
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from corpus_tools import regression
from corpus_tools.hashing import sha256_bytes
from corpus_tools.materialize import STATUS_OK, STATUS_SKIPPED

MEMBER_BODY = b"a regression document"
MEMBER_SHA256 = sha256_bytes(MEMBER_BODY)


def shard_bytes(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)
    return buffer.getvalue()


class StubTransport:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.calls = 0

    def fetch(self, url: str, *, timeout: float) -> bytes:
        self.calls += 1
        return self.payload


class FailingTransport:
    def fetch(self, url: str, *, timeout: float) -> bytes:
        message = "upstream is down"
        raise ConnectionResetError(message)


class RegressionFetcherTest(unittest.TestCase):
    """~keep The tree has to outlive the call, so the temporary directory is torn down by the test
    framework rather than by the helper that made it — an earlier version returned the path from
    inside a `with` block and every assertion read a directory that no longer existed."""

    def setUp(self) -> None:
        self._directory = TemporaryDirectory()
        self.root = Path(self._directory.name)
        self._original_root = regression.REPO_ROOT
        self._original_transport = regression.TRANSPORT
        regression.REPO_ROOT = self.root
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        regression.REPO_ROOT = self._original_root
        regression.TRANSPORT = self._original_transport
        self._directory.cleanup()

    def _run(self, transport: object, members: list[tuple[str, dict]], *, force: bool = False):
        regression.TRANSPORT = transport
        return self.root, regression.fetch_shard("https://example.invalid/shard.zip", members, force)


class ShardFetchTest(RegressionFetcherTest):
    def test_should_take_a_member_out_of_the_archive_and_verify_it(self) -> None:
        transport = StubTransport(shard_bytes({"000/doc.pdf": MEMBER_BODY}))
        entry = {"sha256": MEMBER_SHA256, "member": "doc.pdf"}

        root, results = self._run(transport, [("regression/doc.pdf", entry)])

        self.assertEqual(results, [("regression/doc.pdf", STATUS_OK)])
        self.assertEqual((root / "regression/doc.pdf").read_bytes(), MEMBER_BODY)

    def test_should_locate_a_member_by_basename_because_shards_nest_their_paths(self) -> None:
        # ~keep The archive stores `000/nested/doc.pdf`; the manifest names only `doc.pdf`.
        transport = StubTransport(shard_bytes({"000/nested/doc.pdf": MEMBER_BODY}))
        entry = {"sha256": MEMBER_SHA256, "member": "doc.pdf"}

        _, results = self._run(transport, [("regression/doc.pdf", entry)])

        self.assertEqual(results, [("regression/doc.pdf", STATUS_OK)])

    def test_should_report_a_member_the_shard_does_not_contain(self) -> None:
        # ~keep The branch whose deletion survived the whole suite. An upstream that reorganised
        # its archive would otherwise report success having written nothing.
        transport = StubTransport(shard_bytes({"000/other.pdf": MEMBER_BODY}))
        entry = {"sha256": MEMBER_SHA256, "member": "absent.pdf"}

        _, results = self._run(transport, [("regression/absent.pdf", entry)])

        self.assertEqual(len(results), 1)
        self.assertIn("not in shard", results[0][1])

    def test_should_write_a_sidecar_when_a_member_does_not_match_its_pin(self) -> None:
        transport = StubTransport(shard_bytes({"000/doc.pdf": b"different bytes"}))
        entry = {"sha256": MEMBER_SHA256, "member": "doc.pdf"}

        root, results = self._run(transport, [("regression/doc.pdf", entry)])

        self.assertIn("mismatch got", results[0][1])
        self.assertFalse((root / "regression/doc.pdf").exists())
        self.assertTrue((root / "regression/doc.pdf.mismatch").exists())

    def test_should_not_download_the_shard_when_every_member_is_already_current(self) -> None:
        # ~keep A shard is hundreds of megabytes. Re-downloading it to discover nothing changed is
        # the difference between a fast no-op and a very slow one.
        transport = StubTransport(shard_bytes({"000/doc.pdf": MEMBER_BODY}))
        entry = {"sha256": MEMBER_SHA256, "member": "doc.pdf"}

        target = self.root / "regression/doc.pdf"
        target.parent.mkdir(parents=True)
        target.write_bytes(MEMBER_BODY)
        regression.TRANSPORT = transport

        results = regression.fetch_shard("https://example.invalid/s.zip", [("regression/doc.pdf", entry)], False)

        self.assertEqual(results, [("regression/doc.pdf", STATUS_SKIPPED)])
        self.assertEqual(transport.calls, 0)

    def test_should_report_every_wanted_member_when_the_shard_download_fails(self) -> None:
        entry = {"sha256": MEMBER_SHA256, "member": "doc.pdf"}

        _, results = self._run(FailingTransport(), [("regression/a.pdf", entry), ("regression/b.pdf", entry)])

        self.assertEqual(len(results), 2)
        for _, status in results:
            self.assertIn("error", status)
            self.assertIn("ConnectionResetError", status)


class DirectFetchTest(RegressionFetcherTest):
    def test_should_return_a_list_so_the_pool_stays_homogeneous(self) -> None:
        # ~keep fetch_direct and fetch_shard feed one pool. Same shape means no isinstance at the
        # call site to tell a single result from a batch of them.
        regression.TRANSPORT = StubTransport(MEMBER_BODY)

        results = regression.fetch_direct(
            "regression/doc.pdf", {"sha256": MEMBER_SHA256, "url": "https://example.invalid/d"}, False
        )

        self.assertIsInstance(results, list)
        self.assertEqual(results, [("regression/doc.pdf", STATUS_OK)])
        self.assertEqual((self.root / "regression/doc.pdf").read_bytes(), MEMBER_BODY)
