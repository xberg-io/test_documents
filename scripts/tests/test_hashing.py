"""The chunked reader must agree with the whole-file one it replaced.

~keep build_diagram_pdfs hashed with `hashlib.sha256(path.read_bytes())` while fetch_corpus and
publish_corpus used a chunked reader. Collapsing them onto the chunked version is a real behaviour
change — lower peak memory, which matters because the corpus holds a 62 MiB object — and the only
thing that makes it safe is that the digests are identical. That is asserted here rather than
assumed, including across the chunk boundary, which is the one place a chunked reader can go wrong.
"""

import hashlib
import tempfile
import unittest
from pathlib import Path

from corpus_tools.hashing import READ_CHUNK_SIZE, sha256_bytes, sha256_file
from corpus_tools.paths import REPO_ROOT

EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class Sha256FileTest(unittest.TestCase):
    def test_should_agree_with_a_whole_file_read_on_a_committed_fixture(self) -> None:
        fixture = REPO_ROOT / "diagrams" / "src" / "graphviz_bidirectional.dot"
        self.assertTrue(fixture.is_file(), "fixture missing, so this test would prove nothing")

        self.assertEqual(sha256_file(fixture), hashlib.sha256(fixture.read_bytes()).hexdigest())

    def test_should_hash_an_empty_file_to_the_known_empty_digest(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / "empty"
            target.write_bytes(b"")

            self.assertEqual(sha256_file(target), EMPTY_SHA256)

    def test_should_agree_with_a_whole_file_read_across_the_chunk_boundary(self) -> None:
        # ~keep Sizes either side of READ_CHUNK_SIZE and exactly on it: a chunked reader that drops
        # or double-counts the final partial chunk still passes on small inputs.
        for size in (READ_CHUNK_SIZE - 1, READ_CHUNK_SIZE, READ_CHUNK_SIZE + 1, READ_CHUNK_SIZE * 2 + 7):
            with self.subTest(size=size), tempfile.TemporaryDirectory() as name:
                target = Path(name) / "payload"
                payload = bytes(range(256)) * (size // 256) + b"\x00" * (size % 256)
                target.write_bytes(payload)

                self.assertEqual(sha256_file(target), hashlib.sha256(payload).hexdigest())
                self.assertEqual(sha256_bytes(payload), hashlib.sha256(payload).hexdigest())


class RepoRootTest(unittest.TestCase):
    def test_should_resolve_the_repo_root_from_the_package_location(self) -> None:
        self.assertTrue((REPO_ROOT / "corpus.lock.json").is_file())
        self.assertTrue((REPO_ROOT / "scripts" / "corpus_tools" / "paths.py").is_file())
