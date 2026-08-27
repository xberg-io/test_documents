"""Unit tests for the corpus publisher. Run with `python3 -m unittest discover -s scripts`."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from corpus_tools import paths
from corpus_tools.corpus.backends import LocalDirBackend
from corpus_tools.corpus.publish import (
    EXTRA_ROOT_FILES,
    STAGING_DIR_PREFIX,
    WRITE_PROBE_KEY,
    CorpusFileTracked,
    EmptyCorpus,
    GuardViolation,
    WriteProbeFailed,
    corpus_paths,
    guard_against_forbidden_paths,
    guard_against_tracked_corpus_files,
    staged_by_sha256,
    upload_extra_files,
    upload_unique_objects,
    verify_write_access,
)
from corpus_tools.hashing import sha256_file
from corpus_tools.http import RetryPolicy
from corpus_tools.manifest import (
    OBJECTS_PREFIX,
    CorpusObject,
    build_manifest,
    unique_objects_by_sha256,
)
from corpus_tools.patterns import PATTERNS_FILENAME, load_patterns, matches_any, matches_corpus_pattern
from fetch_corpus import fetch_one

REPO_ROOT = paths.REPO_ROOT


def corpus_object(root: Path, rel_path: str, content: bytes) -> CorpusObject:
    full_path = root / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(content)
    return CorpusObject(path=rel_path, sha256=sha256_file(full_path), size=len(content))


class GuardTests(unittest.TestCase):
    def test_should_reject_license_restricted_corpus_cache_paths(self) -> None:
        with self.assertRaises(GuardViolation) as caught:
            guard_against_forbidden_paths(["pdf/ok.pdf", ".corpus-cache/restricted.pdf"])
        self.assertIn(".corpus-cache/restricted.pdf", str(caught.exception))

    def test_should_accept_paths_outside_the_forbidden_prefixes(self) -> None:
        guard_against_forbidden_paths(["pdf/ok.pdf", "images/ok.png"])


class PatternMatchingTests(unittest.TestCase):
    """Patterns carry gitattributes semantics: bare globs match a basename at any depth."""

    def test_should_match_a_bare_extension_glob_at_any_depth(self) -> None:
        self.assertTrue(matches_corpus_pattern("pdf/nested/deep/memo.pdf", ["*.pdf"]))
        self.assertTrue(matches_corpus_pattern("memo.pdf", ["*.pdf"]))

    def test_should_anchor_a_pattern_containing_a_slash_to_the_repo_root(self) -> None:
        pattern = ["ground_truth/structured/parsebench/*.jsonl"]
        self.assertTrue(matches_corpus_pattern("ground_truth/structured/parsebench/run.jsonl", pattern))
        self.assertFalse(matches_corpus_pattern("jsonl/elsewhere.jsonl", pattern))

    def test_should_not_match_a_text_file_that_merely_shares_a_stem(self) -> None:
        self.assertFalse(matches_corpus_pattern("ground_truth/pdf/memo.md", ["*.pdf"]))


class EnumerationTests(unittest.TestCase):
    """Enumeration walks the real working tree — these files are deliberately untracked."""

    def _tree(self, root: Path, relative_paths: list[str]) -> None:
        (root / PATTERNS_FILENAME).parent.mkdir(parents=True, exist_ok=True)
        (root / PATTERNS_FILENAME).write_text("# comment\n\n*.pdf\n*.png\n", encoding="utf-8")
        for rel_path in relative_paths:
            full_path = root / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_bytes(b"x")

    def test_should_find_matching_files_at_any_depth_sorted_by_path(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self._tree(root, ["z/last.pdf", "a/first.pdf", "images/logo.png", "notes/readme.md"])

            self.assertEqual(
                corpus_paths(root, load_patterns(root)),
                ["a/first.pdf", "images/logo.png", "z/last.pdf"],
            )

    def test_should_refuse_to_publish_when_the_corpus_was_never_materialised(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self._tree(root, ["notes/readme.md"])

            with self.assertRaises(EmptyCorpus):
                corpus_paths(root, load_patterns(root))

    def test_should_never_enumerate_the_license_restricted_corpus_cache(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self._tree(root, ["pdf/ok.pdf", ".corpus-cache/restricted.pdf"])

            self.assertEqual(corpus_paths(root, load_patterns(root)), ["pdf/ok.pdf"])

    def test_should_ignore_comments_and_blank_lines_in_the_pattern_file(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self._tree(root, ["pdf/ok.pdf"])

            self.assertEqual(load_patterns(root), ["*.pdf", "*.png"])


class VirtualenvGuardTests(unittest.TestCase):
    """A dev virtualenv at the repo root is a publish hazard, not just clutter.

    ~keep The patterns are gitignore-shaped: one without '/' matches a basename at ANY depth, and
    the list contains *.png, *.jpg, *.pdf, *.zip, *.tar and *.gz. Installed packages ship exactly
    those as bundled assets, and corpus_paths() walks the working tree rather than asking git, so
    nothing about .venv/ being untracked keeps it out. Adopting uv is what made this reachable.
    """

    def _tree(self, root: Path, relative_paths: list[str]) -> None:
        (root / PATTERNS_FILENAME).parent.mkdir(parents=True, exist_ok=True)
        (root / PATTERNS_FILENAME).write_text("*.pdf\n*.png\n", encoding="utf-8")
        for rel_path in relative_paths:
            full_path = root / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_bytes(b"x")

    def test_should_prune_the_virtualenv_from_the_walk_before_the_guard_ever_runs(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self._tree(root, ["pdf/ok.pdf", ".venv/lib/python3.12/site-packages/pkg/logo.png"])

            self.assertEqual(corpus_paths(root, load_patterns(root)), ["pdf/ok.pdf"])

    def test_should_refuse_to_publish_anything_under_a_virtualenv(self) -> None:
        # ~keep The pruning above means this can only be reached by a caller passing paths in
        # directly, which is precisely why the guard exists as a second line rather than a duplicate.
        with self.assertRaises(GuardViolation) as caught:
            guard_against_forbidden_paths([".venv/lib/python3.12/site-packages/pkg/logo.png"])

        self.assertIn(".venv/", str(caught.exception))

    def test_should_ignore_every_tool_cache_directory_the_dev_toolchain_creates(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self._tree(
                root,
                [
                    "pdf/ok.pdf",
                    ".ruff_cache/0.14/report.png",
                    ".mypy_cache/3.12/cached.pdf",
                    ".pytest_cache/v/cache/sample.png",
                ],
            )

            self.assertEqual(corpus_paths(root, load_patterns(root)), ["pdf/ok.pdf"])


class TrackedCorpusGuardTests(unittest.TestCase):
    """A corpus binary committed to git would silently re-grow the repo it was just purged from."""

    def _repo(self, root: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)

    def test_should_reject_a_corpus_file_that_was_committed_to_git(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self._repo(root)
            (root / "pdf").mkdir()
            (root / "pdf/memo.pdf").write_bytes(b"x")
            subprocess.run(["git", "add", "-f", "pdf/memo.pdf"], cwd=root, check=True)

            with self.assertRaises(CorpusFileTracked) as caught:
                guard_against_tracked_corpus_files(root, ["pdf/memo.pdf"])

            self.assertIn("pdf/memo.pdf", str(caught.exception))

    def test_should_accept_corpus_files_that_are_untracked(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self._repo(root)
            (root / "pdf").mkdir()
            (root / "pdf/memo.pdf").write_bytes(b"x")

            guard_against_tracked_corpus_files(root, ["pdf/memo.pdf"])


class PatternSyncTests(unittest.TestCase):
    """.gitignore and the publisher must agree, or a published file could still land in git."""

    def test_should_ignore_every_pattern_the_publisher_enumerates(self) -> None:
        patterns = load_patterns(REPO_ROOT)
        ignored = {
            line.strip()
            for line in (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        }

        self.assertEqual([p for p in patterns if p not in ignored], [])


class ManifestTests(unittest.TestCase):
    def test_should_order_manifest_entries_by_path_for_byte_stable_output(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            objects = [
                corpus_object(root, "z/last.bin", b"z"),
                corpus_object(root, "a/first.bin", b"a"),
            ]
            manifest = build_manifest(objects)
        self.assertEqual(list(manifest["objects"]), ["a/first.bin", "z/last.bin"])
        self.assertEqual(manifest["objects"]["a/first.bin"]["size"], 1)

    def test_should_collapse_duplicate_content_to_one_representative_object(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            objects = [
                corpus_object(root, "a/copy.bin", b"same"),
                corpus_object(root, "b/copy.bin", b"same"),
                corpus_object(root, "c/other.bin", b"different"),
            ]
            representatives = unique_objects_by_sha256(objects)
        self.assertEqual(len(representatives), 2)


class StagingTests(unittest.TestCase):
    def test_should_stage_each_object_under_its_sha256_without_copying_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            obj = corpus_object(root, "pdf/memo.pdf", b"memo bytes")
            with staged_by_sha256(root, {obj.sha256: obj}) as staging:
                staged = staging / obj.sha256
                self.assertEqual(staged.read_bytes(), b"memo bytes")
                self.assertEqual(staged.stat().st_ino, (root / obj.path).stat().st_ino)
                staging_root = staging
            self.assertFalse(staging_root.exists())

    def test_should_remove_the_staging_directory_when_upload_raises(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            obj = corpus_object(root, "pdf/memo.pdf", b"memo bytes")
            with self.assertRaises(RuntimeError), staged_by_sha256(root, {obj.sha256: obj}):
                raise RuntimeError("upload failed")
            self.assertEqual([path.name for path in root.glob(f"{STAGING_DIR_PREFIX}*")], [])


class UploadTests(unittest.TestCase):
    def test_should_upload_every_object_when_the_bucket_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as name, tempfile.TemporaryDirectory() as bucket_name:
            root = Path(name)
            objects = [corpus_object(root, "a.bin", b"a"), corpus_object(root, "b.bin", b"b")]
            representatives = unique_objects_by_sha256(objects)
            backend = LocalDirBackend(Path(bucket_name))

            uploaded, skipped = upload_unique_objects(root, backend, representatives, dry_run=False)

            self.assertEqual(uploaded, sorted(representatives))
            self.assertEqual(skipped, [])
            for sha256, obj in representatives.items():
                self.assertEqual(
                    (Path(bucket_name) / OBJECTS_PREFIX / sha256).read_bytes(), (root / obj.path).read_bytes()
                )

    def test_should_skip_objects_already_present_in_the_bucket(self) -> None:
        with tempfile.TemporaryDirectory() as name, tempfile.TemporaryDirectory() as bucket_name:
            root = Path(name)
            already = corpus_object(root, "a.bin", b"a")
            fresh = corpus_object(root, "b.bin", b"b")
            representatives = unique_objects_by_sha256([already, fresh])
            backend = LocalDirBackend(Path(bucket_name))
            backend.upload(root / already.path, f"{OBJECTS_PREFIX}/{already.sha256}")

            uploaded, skipped = upload_unique_objects(root, backend, representatives, dry_run=False)

            self.assertEqual(uploaded, [fresh.sha256])
            self.assertEqual(skipped, [already.sha256])

    def test_should_contact_no_backend_at_all_in_dry_run_mode(self) -> None:
        class ExplodingBackend:
            def existing_keys(self, prefix: str) -> set[str]:
                raise AssertionError("dry-run must not list the bucket")

            def matches_remote(self, local_path: Path, key: str) -> bool:
                raise AssertionError("dry-run must not inspect the bucket")

            def upload(self, local_path: Path, key: str) -> None:
                raise AssertionError("dry-run must not upload")

            def upload_directory(self, local_directory: Path, key_prefix: str) -> None:
                raise AssertionError("dry-run must not upload")

        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            representatives = unique_objects_by_sha256([corpus_object(root, "a.bin", b"a")])

            uploaded, skipped = upload_unique_objects(root, ExplodingBackend(), representatives, dry_run=True)

        self.assertEqual(uploaded, sorted(representatives))
        self.assertEqual(skipped, [])


class ExtraFileTests(unittest.TestCase):
    """The licence/manifest files at the bucket root are mutable, unlike content-addressed objects."""

    def _corpus_with_extras(self, root: Path) -> None:
        for rel_path in EXTRA_ROOT_FILES:
            full_path = root / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"contents of {rel_path}\n", encoding="utf-8")

    def test_should_not_rewrite_an_attribution_file_whose_content_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as name, tempfile.TemporaryDirectory() as bucket_name:
            root, bucket = Path(name), Path(bucket_name)
            self._corpus_with_extras(root)
            backend = LocalDirBackend(bucket)

            first_uploaded, first_unchanged = upload_extra_files(root, backend, dry_run=False)
            second_uploaded, second_unchanged = upload_extra_files(root, backend, dry_run=False)

        self.assertEqual(len(first_uploaded), len(EXTRA_ROOT_FILES))
        self.assertEqual(first_unchanged, [])
        self.assertEqual(second_uploaded, [])
        self.assertEqual(len(second_unchanged), len(EXTRA_ROOT_FILES))

    def test_should_reupload_an_attribution_file_after_its_content_changes(self) -> None:
        with tempfile.TemporaryDirectory() as name, tempfile.TemporaryDirectory() as bucket_name:
            root, bucket = Path(name), Path(bucket_name)
            self._corpus_with_extras(root)
            backend = LocalDirBackend(bucket)
            upload_extra_files(root, backend, dry_run=False)

            (root / "ATTRIBUTIONS.md").write_text("a new attribution was added\n", encoding="utf-8")
            uploaded, unchanged = upload_extra_files(root, backend, dry_run=False)

            self.assertEqual(uploaded, ["ATTRIBUTIONS.md"])
            self.assertEqual(len(unchanged), len(EXTRA_ROOT_FILES) - 1)
            self.assertEqual((bucket / "ATTRIBUTIONS.md").read_text(), "a new attribution was added\n")

    def test_should_fail_loudly_when_a_required_attribution_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as name, tempfile.TemporaryDirectory() as bucket_name:
            root = Path(name)
            with self.assertRaises(FileNotFoundError):
                upload_extra_files(root, LocalDirBackend(Path(bucket_name)), dry_run=False)


class WriteProbeTests(unittest.TestCase):
    """A publish that uploads nothing must still prove the credentials can write."""

    def test_should_write_the_probe_object_and_return_its_token(self) -> None:
        with tempfile.TemporaryDirectory() as bucket_name:
            bucket = Path(bucket_name)

            token = verify_write_access(LocalDirBackend(bucket))

            self.assertIn(token, (bucket / WRITE_PROBE_KEY).read_text())

    def test_should_place_the_probe_outside_the_content_addressed_object_prefix(self) -> None:
        self.assertFalse(WRITE_PROBE_KEY.startswith(f"{OBJECTS_PREFIX}/"))
        self.assertNotIn(WRITE_PROBE_KEY, EXTRA_ROOT_FILES)

    def test_should_use_a_fresh_token_per_run_so_a_stale_probe_cannot_satisfy_it(self) -> None:
        with tempfile.TemporaryDirectory() as bucket_name:
            backend = LocalDirBackend(Path(bucket_name))

            first = verify_write_access(backend)
            second = verify_write_access(backend)

            self.assertNotEqual(first, second)

    def test_should_raise_when_the_upload_is_rejected(self) -> None:
        class RejectingBackend(LocalDirBackend):
            def upload(self, local_path: Path, key: str) -> None:
                raise subprocess.CalledProcessError(1, ["gcloud", "storage", "cp"])

        with tempfile.TemporaryDirectory() as bucket_name, self.assertRaises(WriteProbeFailed):
            verify_write_access(RejectingBackend(Path(bucket_name)))

    def test_should_raise_when_the_write_is_silently_dropped(self) -> None:
        class SilentlyDiscardingBackend(LocalDirBackend):
            def upload(self, local_path: Path, key: str) -> None:
                return None

        with tempfile.TemporaryDirectory() as bucket_name, self.assertRaises(WriteProbeFailed) as caught:
            verify_write_access(SilentlyDiscardingBackend(Path(bucket_name)))

        self.assertIn("could not read it back", str(caught.exception))

    def test_should_raise_when_the_object_read_back_is_not_the_one_written(self) -> None:
        class StaleReadBackend(LocalDirBackend):
            def read_text(self, key: str) -> str | None:
                return "a token from some earlier run\n"

        with tempfile.TemporaryDirectory() as bucket_name, self.assertRaises(WriteProbeFailed) as caught:
            verify_write_access(StaleReadBackend(Path(bucket_name)))

        self.assertIn("read back as", str(caught.exception))


class FetchTests(unittest.TestCase):
    """The local counterpart of the CI fetch action; consumers include_bytes! these files."""

    def test_should_leave_a_file_alone_when_it_already_hashes_correctly(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "pdf").mkdir()
            target = root / "pdf/memo.pdf"
            target.write_bytes(b"already here")
            digest = sha256_file(target)

            # ~keep A bucket name that cannot resolve: if the skip path is broken this raises
            # rather than silently re-downloading, which is what we actually want to detect.
            failure = fetch_one("bucket.invalid", root, "pdf/memo.pdf", digest)

            self.assertIsNone(failure)
            self.assertEqual(target.read_bytes(), b"already here")

    def test_should_report_a_failure_when_the_object_cannot_be_downloaded(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            # ~keep One attempt, no backoff: this asserts the failure is REPORTED rather than
            # raised, and paying the real retry schedule to learn that only slows the suite.
            failure = fetch_one(
                "bucket.invalid",
                Path(name),
                "pdf/missing.pdf",
                "0" * 64,
                retry=RetryPolicy(attempts=1),
            )

            self.assertIsNotNone(failure)
            self.assertIn("pdf/missing.pdf", failure)

    def test_should_treat_a_double_star_glob_as_everything_beneath_a_directory(self) -> None:
        self.assertTrue(matches_any("pdf/nested/memo.pdf", ["pdf/**"]))
        self.assertTrue(matches_any("pdf/memo.pdf", ["pdf/**"]))
        self.assertFalse(matches_any("images/logo.png", ["pdf/**"]))


if __name__ == "__main__":
    unittest.main()
