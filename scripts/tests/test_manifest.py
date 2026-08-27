"""corpus.lock.json's bytes are a cross-repo contract, and nothing else tests the write path.

~keep Consumers fetch through xberg-io/actions/fetch-test-documents, which hashes this file to key
its object cache. If build_manifest's ordering or write_manifest's serialisation drifts, every
consumer's cache is invalidated at once and what the manifest pins changes with it.

Nothing catches that today. The publisher's own tests exercise `--dry-run`, which deliberately
never writes the manifest, and CI cannot publish at all — the corpus binaries are not in git, so a
checkout has nothing to upload. The write path therefore runs only on a maintainer's machine, and
only when it is already too late to notice.

The fix is cheap because the round trip is exact: parse the committed manifest, feed its objects
back through the real build_manifest and write_manifest, and require the bytes to match. No
network, no corpus binaries, no credentials — just the file that is already in git.
"""

import json
import tempfile
import unittest
from pathlib import Path

from corpus_tools.manifest import (
    MANIFEST_SCHEMA_VERSION,
    CorpusObject,
    build_manifest,
    lock_objects,
    lock_pins,
    object_url,
    unique_objects_by_sha256,
    write_manifest,
)
from corpus_tools.paths import LOCK_PATH


def committed_objects() -> list[CorpusObject]:
    return [
        CorpusObject(path=path, sha256=entry["sha256"], size=entry["size"])
        for path, entry in lock_objects(LOCK_PATH).items()
    ]


class LockRoundTripTest(unittest.TestCase):
    def test_should_reproduce_the_committed_manifest_byte_for_byte(self) -> None:
        objects = committed_objects()
        self.assertGreater(len(objects), 0, "the committed manifest is empty, so this proves nothing")

        with tempfile.TemporaryDirectory() as name:
            destination = Path(name) / "corpus.lock.json"
            write_manifest(build_manifest(objects), destination)

            self.assertEqual(
                destination.read_bytes(),
                LOCK_PATH.read_bytes(),
                "build_manifest/write_manifest no longer reproduce corpus.lock.json byte for byte. "
                "Every consumer's fetch cache is keyed on these bytes.",
            )

    def test_should_sort_objects_by_path_regardless_of_input_order(self) -> None:
        objects = committed_objects()
        manifest = build_manifest(list(reversed(objects)))

        self.assertEqual(list(manifest["objects"]), sorted(manifest["objects"]))

    def test_should_serialise_with_two_space_indent_and_a_trailing_newline(self) -> None:
        # ~keep The two properties that decide the bytes, asserted directly so a reviewer does not
        # have to infer them from the golden comparison above.
        raw = LOCK_PATH.read_bytes()

        self.assertTrue(raw.endswith(b"\n"))
        self.assertIn(b'\n  "objects": {', raw)

    def test_should_pin_the_schema_version_the_consumers_expect(self) -> None:
        self.assertEqual(json.loads(LOCK_PATH.read_text(encoding="utf-8"))["schema"], MANIFEST_SCHEMA_VERSION)


class LockReadersTest(unittest.TestCase):
    def test_should_collapse_duplicate_paths_onto_one_pinned_object(self) -> None:
        objects = lock_objects(LOCK_PATH)
        pins = lock_pins(LOCK_PATH)
        distinct_digests = {entry["sha256"] for entry in objects.values()}

        self.assertEqual(len(pins), len(distinct_digests))
        self.assertLessEqual(len(pins), len(objects))

    def test_should_agree_with_unique_objects_by_sha256_about_how_many_blobs_exist(self) -> None:
        self.assertEqual(len(unique_objects_by_sha256(committed_objects())), len(lock_pins(LOCK_PATH)))

    def test_should_build_the_public_object_url_consumers_fetch(self) -> None:
        digest = "a" * 64

        self.assertEqual(
            object_url("xberg-test-documents", digest),
            f"https://storage.googleapis.com/xberg-test-documents/objects/{digest}",
        )
