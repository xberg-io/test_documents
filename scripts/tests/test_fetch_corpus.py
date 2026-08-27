"""Driving fetch_corpus.main end to end, without a network.

~keep Only fetch_one was covered before, so the parts that decide WHAT gets fetched and WHERE it
lands were untested: disabling the --include filter and ignoring --root both survived the suite. A
broken filter quietly pulls the whole ~580 MiB corpus into every consumer's CI; a broken --root
writes into the wrong tree. Both are silent, and both are the reason these flags exist.
"""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import fetch_corpus
from corpus_tools.hashing import sha256_bytes
from corpus_tools.manifest import CorpusObject as Object
from corpus_tools.manifest import build_manifest, write_manifest
from corpus_tools.paths import REPO_ROOT

BODIES = {
    "pdf/one.pdf": b"first pdf",
    "pdf/nested/two.pdf": b"second pdf",
    "images/logo.png": b"a png",
}


class RecordingTransport:
    """Serves the object whose sha256 is asked for, and remembers what was requested."""

    def __init__(self) -> None:
        self.by_digest = {sha256_bytes(body): body for body in BODIES.values()}
        self.requested: list[str] = []

    def fetch(self, url: str, *, timeout: float) -> bytes:
        digest = url.rsplit("/", 1)[-1]
        self.requested.append(digest)
        return self.by_digest[digest]


class FetchCorpusMainTest(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = TemporaryDirectory()
        self.root = Path(self._directory.name)
        self.manifest = self.root / "corpus.lock.json"
        write_manifest(
            build_manifest([Object(path=p, sha256=sha256_bytes(b), size=len(b)) for p, b in BODIES.items()]),
            self.manifest,
        )
        self.transport = RecordingTransport()
        self._original = fetch_corpus.build_transport
        fetch_corpus.build_transport = lambda _args: self.transport
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        fetch_corpus.build_transport = self._original
        self._directory.cleanup()

    def _run(self, *extra: str) -> int:
        destination = self.root / "tree"
        return fetch_corpus.main(
            ["--manifest", str(self.manifest), "--root", str(destination), "--bucket", "b", *extra]
        )

    def test_should_materialise_every_pinned_object_by_default(self) -> None:
        self.assertEqual(self._run(), 0)

        written = sorted(str(p.relative_to(self.root / "tree")) for p in (self.root / "tree").rglob("*") if p.is_file())
        self.assertEqual(written, sorted(BODIES))

    def test_should_write_each_object_at_the_path_the_manifest_names(self) -> None:
        self._run()

        for relative, body in BODIES.items():
            with self.subTest(path=relative):
                self.assertEqual((self.root / "tree" / relative).read_bytes(), body)

    def test_should_fetch_only_what_the_include_glob_selects(self) -> None:
        # ~keep The mutant that survived: dropping the filter fetches everything and still exits 0.
        self.assertEqual(self._run("--include", "pdf/**"), 0)

        written = sorted(str(p.relative_to(self.root / "tree")) for p in (self.root / "tree").rglob("*") if p.is_file())
        self.assertEqual(written, ["pdf/nested/two.pdf", "pdf/one.pdf"])
        self.assertEqual(len(self.transport.requested), 2)

    def test_should_materialise_into_the_root_it_was_given_and_nowhere_else(self) -> None:
        """~keep Ignoring --root also survived, and the consequence is not abstract.

        Mutating it to REPO_ROOT while proving this test could fail wrote three files straight into
        the working tree, where corpus patterns match them and .gitignore hides them — so they were
        invisible to `git status` and would have been picked up by the next publish. Assert against
        REPO_ROOT specifically, not cwd, because that is where a broken --root actually lands.
        """
        self._run()

        self.assertTrue((self.root / "tree" / "pdf/one.pdf").is_file())
        for relative in BODIES:
            with self.subTest(path=relative):
                self.assertFalse((REPO_ROOT / relative).exists(), f"{relative} leaked into the repository")

    def test_should_report_a_glob_that_matched_nothing_rather_than_fetching_everything(self) -> None:
        result = self._run("--include", "absent/**")

        self.assertEqual(result, 1)
        self.assertEqual(self.transport.requested, [])

    def test_should_not_refetch_an_object_that_is_already_on_disk(self) -> None:
        self._run()
        before = len(self.transport.requested)

        self._run()

        self.assertEqual(len(self.transport.requested), before, "a second run must cost no network")

    def test_should_report_failure_when_the_bucket_serves_the_wrong_bytes(self) -> None:
        class WrongBytesTransport:
            def fetch(self, url: str, *, timeout: float) -> bytes:
                return b"not what was pinned"

        fetch_corpus.build_transport = lambda _args: WrongBytesTransport()

        self.assertEqual(self._run(), 1)

    def test_should_read_the_manifest_it_was_pointed_at(self) -> None:
        # ~keep --manifest and --root are independent on purpose: an index committed in one repo
        # can materialise files into a tree in another.
        subset = self.root / "subset.lock.json"
        objects = json.loads(self.manifest.read_text(encoding="utf-8"))["objects"]
        one = next(iter(objects))
        write_manifest({"schema": 1, "objects": {one: objects[one]}}, subset)

        result = fetch_corpus.main(["--manifest", str(subset), "--root", str(self.root / "tree"), "--bucket", "b"])

        self.assertEqual(result, 0)
        self.assertEqual(len(self.transport.requested), 1)
