"""Checks for the EPUB edge-case corpus that need no network.

The manifest pins every file by sha256. For synthesized files the pin must
match a fresh build, so a change to the generator that alters the bytes has to
update the manifest in the same commit. Every manifest path must be a corpus
binary (published to the bucket, never committed) and must be documented in
`EPUB_EDGE_CASES.md`.
"""

import hashlib
import io
import json
import re
import unittest
import zipfile

import build_epub_edge_cases
from corpus_tools import paths
from corpus_tools.patterns import load_patterns, matches_corpus_pattern

SCRIPTS_DIR = paths.SCRIPTS_DIR
REPO_ROOT = paths.REPO_ROOT
MANIFEST = SCRIPTS_DIR / "data" / "epub-edge-cases.json"
PROVENANCE = REPO_ROOT / "EPUB_EDGE_CASES.md"
SOURCE_KINDS = ("url", "members", "generated")


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


class ManifestTests(unittest.TestCase):
    def test_every_entry_names_exactly_one_source(self) -> None:
        for path, entry in load_manifest().items():
            kinds = [kind for kind in SOURCE_KINDS if kind in entry]
            self.assertEqual(len(kinds), 1, f"{path}: expected one of {SOURCE_KINDS}, found {kinds}")
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$", path)
            self.assertGreater(entry["size"], 0, path)

    def test_every_path_is_a_corpus_binary_under_the_edge_case_directory(self) -> None:
        patterns = load_patterns(REPO_ROOT)
        for path in load_manifest():
            self.assertTrue(path.startswith(f"{build_epub_edge_cases.CORPUS_DIR}/"), path)
            self.assertTrue(matches_corpus_pattern(path, patterns), f"{path} is not a corpus binary")

    def test_generated_entries_match_the_manifest_and_builders_agree(self) -> None:
        manifest = load_manifest()
        generated = {path for path, entry in manifest.items() if entry.get("generated")}
        self.assertEqual(generated, set(build_epub_edge_cases.BUILDERS))

    def test_every_path_is_documented(self) -> None:
        text = PROVENANCE.read_text(encoding="utf-8")
        for path in load_manifest():
            self.assertIn(f"`{path}`", text, f"{path} is missing from {PROVENANCE.name}")

    def test_member_urls_are_pinned_to_a_commit(self) -> None:
        for path, entry in load_manifest().items():
            for name, url in entry.get("members", {}).items():
                self.assertRegex(url, r"/[0-9a-f]{40}/", f"{path}: {name} is not pinned to a commit")
                self.assertTrue(url.endswith(name), f"{path}: {name} does not match its URL")


class BuilderTests(unittest.TestCase):
    def test_build_is_deterministic_and_matches_the_pins(self) -> None:
        first = build_epub_edge_cases.build_all()
        second = build_epub_edge_cases.build_all()
        self.assertEqual(first, second)
        manifest = load_manifest()
        for path, data in first.items():
            digest = hashlib.sha256(data).hexdigest()
            self.assertEqual(digest, manifest[path]["sha256"], f"{path}: rebuild the file and update the manifest")
            self.assertEqual(len(data), manifest[path]["size"], path)

    def test_every_build_is_an_epub_container(self) -> None:
        for path, data in build_epub_edge_cases.build_all().items():
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                names = archive.namelist()
                self.assertEqual(names[0], "mimetype", path)
                self.assertEqual(archive.read("mimetype"), b"application/epub+zip", path)
                self.assertIn("META-INF/container.xml", names, path)
                self.assertIn("OEBPS/content.opf", names, path)

    def test_each_synthesized_case_carries_its_trigger(self) -> None:
        built = build_epub_edge_cases.build_all()
        prefix = build_epub_edge_cases.CORPUS_DIR

        def member(path: str, name: str) -> bytes:
            with zipfile.ZipFile(io.BytesIO(built[f"{prefix}/{path}"])) as archive:
                return archive.read(name)

        self.assertIn(b"&nbsp;", member("entities/synthetic_entity_style.epub", "OEBPS/chapter1.xhtml"))
        self.assertTrue(
            member("entities/synthetic_bom_prelude.epub", "OEBPS/chapter1.xhtml").startswith(b"\xef\xbb\xbf<?xml")
        )
        deep = member("depth/synthetic_nested_30000.epub", "OEBPS/deep.xhtml")
        self.assertEqual(deep.count(b"<span>"), 30_000)
        self.assertIn(
            b'href="https://example.org/remote.xhtml"',
            member("unsafe-href/synthetic_remote_url_spine_item.epub", "OEBPS/content.opf"),
        )
        self.assertIn(
            b'<meta name="cover" content="cover-page"/>',
            member("metadata/synthetic_cover_meta_xhtml.epub", "OEBPS/content.opf"),
        )
        self.assertIn(b'opf:role="ill"', member("metadata/synthetic_dublin_core_epub2.epub", "OEBPS/content.opf"))
        latin1 = member("encoding/synthetic_latin1.epub", "OEBPS/chapter1.xhtml")
        self.assertIn(b'encoding="iso-8859-1"', latin1)
        with self.assertRaises(UnicodeDecodeError):
            latin1.decode("utf-8")
        self.assertTrue(member("encoding/synthetic_utf16le.epub", "OEBPS/chapter1.xhtml").startswith(b"\xff\xfe"))
        self.assertTrue(member("encoding/synthetic_utf16be.epub", "OEBPS/chapter1.xhtml").startswith(b"\xfe\xff"))
        self.assertIn(b'encoding="iso-8859-1"', member("encoding/synthetic_opf_latin1.epub", "OEBPS/content.opf"))
        opf = member("media-types/synthetic_media_type_labels.epub", "OEBPS/content.opf").decode("utf-8")
        for _slug, label in build_epub_edge_cases.MEDIA_TYPE_LABELS:
            self.assertIn(f'media-type="{label}"', opf)
        self.assertEqual(len(re.findall(r"<itemref ", opf)), len(build_epub_edge_cases.MEDIA_TYPE_LABELS))
