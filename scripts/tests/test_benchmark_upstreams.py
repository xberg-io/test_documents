"""Pinned upstream acquisition must fail closed without downloading real documents."""

import json
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from corpus_tools.benchmark_inventory import build_inventory
from corpus_tools.benchmark_upstreams import (
    INVENTORY_PATH,
    AssetPin,
    fetch_one,
    load_inventory,
    safe_cache_root,
    validate_pin,
)
from corpus_tools.hashing import sha256_bytes
from corpus_tools.http import RetryPolicy

PAYLOAD = b"%PDF-1.4\nsynthetic integrity control"
REVISION = "54a96a6fb6a2bd3b297e59869491db4d3625b711"


class StubTransport:
    def __init__(self, payload=PAYLOAD):
        self.payload = payload
        self.calls = 0

    def fetch(self, url, *, timeout):
        self.calls += 1
        return self.payload


def pin():
    upstream = "bench_data/pdfs/old_scans/example.pdf"
    return AssetPin(
        path=f"olmocr-issue2331/{upstream}",
        sha256=sha256_bytes(PAYLOAD),
        size=len(PAYLOAD),
        url=f"https://huggingface.co/datasets/allenai/olmOCR-bench/resolve/{REVISION}/{upstream}",
        source="olmocr-issue2331",
        kind="pdf",
        upstream_path=upstream,
        group="old_scans",
        record_id="0123456789",
    )


class UpstreamAcquisitionTest(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.transport = StubTransport()

    def fetch(self, asset=None, *, verify_only=False):
        return fetch_one(
            asset or pin(), self.root, verify_only=verify_only, transport=self.transport, retry=RetryPolicy(attempts=1)
        )

    def test_fetches_verified_original_bytes_and_then_skips_network(self):
        self.assertEqual(self.fetch(), "ok")
        self.assertEqual((self.root / pin().path).read_bytes(), PAYLOAD)
        self.assertEqual(self.fetch(), "skipped")
        self.assertEqual(self.transport.calls, 1)

    def test_changed_upstream_cannot_replace_an_existing_file(self):
        target = self.root / pin().path
        target.parent.mkdir(parents=True)
        target.write_bytes(b"existing local bytes")
        self.transport.payload = b"%PDF-changed upstream bytes!!"
        status = self.fetch()
        self.assertTrue(status.startswith(("error ", "mismatch ")), status)
        self.assertEqual(target.read_bytes(), b"existing local bytes")

    def test_wrong_hash_with_matching_size_is_not_materialized(self):
        self.transport.payload = b"X" * len(PAYLOAD)
        self.assertTrue(self.fetch().startswith("mismatch "))
        self.assertFalse((self.root / pin().path).exists())

    def test_wrong_size_is_not_materialized(self):
        self.assertTrue(self.fetch(replace(pin(), size=len(PAYLOAD) + 1)).startswith("error "))
        self.assertFalse((self.root / pin().path).exists())

    def test_missing_verify_only_file_is_a_failure_without_network(self):
        self.assertTrue(self.fetch(verify_only=True).startswith("missing "))
        self.assertEqual(self.transport.calls, 0)

    def test_verify_only_rejects_corrupt_existing_bytes(self):
        target = self.root / pin().path
        target.parent.mkdir(parents=True)
        target.write_bytes(b"corrupt")
        self.assertTrue(self.fetch(verify_only=True).startswith("mismatch "))
        self.assertEqual(self.transport.calls, 0)

    def test_traversal_is_rejected_before_network(self):
        with self.assertRaisesRegex(ValueError, "relative|path"):
            self.fetch(replace(pin(), path="../outside.pdf"))
        self.assertEqual(self.transport.calls, 0)

    def test_symlink_escape_is_rejected_before_network(self):
        with TemporaryDirectory() as outside:
            (self.root / "olmocr-issue2331").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                self.fetch()
        self.assertEqual(self.transport.calls, 0)

    def test_mismatch_sidecar_cannot_escape_cache_through_a_symlink(self):
        target = self.root / pin().path
        target.parent.mkdir(parents=True)
        with TemporaryDirectory() as outside:
            victim = Path(outside) / "untouched"
            victim.write_bytes(b"unchanged")
            target.with_suffix(".pdf.mismatch").symlink_to(victim)
            self.transport.payload = b"X" * len(PAYLOAD)
            with self.assertRaisesRegex(ValueError, "symlink"):
                self.fetch()
            self.assertEqual(victim.read_bytes(), b"unchanged")
        self.assertEqual(self.transport.calls, 0)

    def test_public_fetch_api_also_rejects_repository_destination(self):
        (self.root / ".git").mkdir()
        with self.assertRaisesRegex(ValueError, "Git"):
            self.fetch()
        self.assertEqual(self.transport.calls, 0)

    def test_mutable_upstream_revision_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "pinned"):
            validate_pin(replace(pin(), url=pin().url.replace(REVISION, "main")))

    def test_wrong_upstream_path_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "pinned|path"):
            validate_pin(replace(pin(), upstream_path="bench_data/pdfs/old_scans/different.pdf"))

    def test_repository_destination_is_rejected(self):
        (self.root / ".git").mkdir()
        with self.assertRaisesRegex(ValueError, "Git"):
            safe_cache_root(self.root / "raw-data")

    def test_empty_inventory_cannot_pass(self):
        manifest = self.root / "empty.json"
        manifest.write_text(
            json.dumps({"format": "xberg-benchmark-upstreams", "schema_version": 1, "sources": {}, "objects": {}})
        )
        with self.assertRaisesRegex(ValueError, "sources|empty"):
            load_inventory(manifest)

    def test_duplicate_json_paths_are_rejected_before_collapsing(self):
        manifest = self.root / "duplicate.json"
        manifest.write_text('{"objects": {"same.pdf": {}, "same.pdf": {}}}')
        with self.assertRaisesRegex(ValueError, "duplicate"):
            load_inventory(manifest)

    def test_committed_inventory_has_every_pdf_and_jsonl(self):
        inventory = load_inventory()
        self.assertEqual(len(inventory), 1493)
        self.assertEqual(sum(asset.kind == "pdf" for asset in inventory), 1487)
        self.assertEqual(sum(asset.kind == "jsonl" for asset in inventory), 6)
        self.assertEqual(sum(asset.source == "parsebench-tables" for asset in inventory), 504)
        self.assertEqual(sum(asset.source == "olmocr-issue2331" for asset in inventory), 989)

    def test_changed_source_revision_cannot_relabel_pinned_assets(self):
        value = json.loads(INVENTORY_PATH.read_text())
        value["sources"]["olmocr-issue2331"]["dataset_revision"] = "0" * 40
        manifest = self.root / "changed-source.json"
        manifest.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "sources"):
            load_inventory(manifest)

    def test_duplicate_pdf_ids_cannot_fill_the_census(self):
        value = json.loads(INVENTORY_PATH.read_text())
        objects = [
            entry
            for entry in value["objects"].values()
            if entry["kind"] == "pdf" and entry["source"] == "olmocr-issue2331"
        ]
        objects[1]["id"] = objects[0]["id"]
        manifest = self.root / "duplicate-ids.json"
        manifest.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "duplicate PDF"):
            load_inventory(manifest)

    def test_generator_rejects_changed_upstream_tree_before_writing_inventory(self):
        stage = self.root / "parsebench-stage"
        stage.mkdir()
        stage.joinpath("stage.json").write_text(
            json.dumps(
                {
                    "dataset_revision": "2805a1d940f95a203e0ae4b88be9934f7765b3fc",
                    "evaluator_revision": "328c71109e0b955f66583c33ec95ac52d9749db4",
                }
            )
        )
        stage.joinpath("hf-table-tree.json").write_text("[]")
        output = self.root / "inventory.json"
        with self.assertRaisesRegex(ValueError, "tree metadata changed"):
            build_inventory(stage, self.root / "olmocr-stage", output)
        self.assertFalse(output.exists())

    def test_missing_inventory_object_cannot_look_complete(self):
        value = json.loads(INVENTORY_PATH.read_text())
        del value["objects"][next(iter(value["objects"]))]
        manifest = self.root / "missing.json"
        manifest.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "count"):
            load_inventory(manifest)
