"""Serving a second, private corpus from the same tooling — and refusing to serve it publicly.

~keep Every fixture here is a neutral placeholder (internal-corpus, acme/foo.pdf). The corpus this
mechanism exists for is a design partner's, and its filenames identify the partner and name their
documents. This repository is public, so nothing about it appears here, in any form.

The guards under test are not defensive programming. The public bucket is world-readable and its
objects cannot be recalled once served, so publishing the wrong root to it is not a mistake anyone
fixes forward. And corpus patterns use gitignore semantics — a bare `*.zip` matches a basename at
ANY depth — so a --root aimed one level too high silently sweeps in whatever lives beside the
corpus. Both failures are silent and both are permanent, which is why they fail loudly instead.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path

import fetch_corpus
from corpus_tools.http import (
    ACCESS_TOKEN_MAX_AGE_SECONDS,
    AdcCredential,
    CredentialError,
    CurlTransport,
    HttpError,
    get,
)
from corpus_tools.manifest import (
    DEFAULT_BUCKET,
    MANIFEST_FILENAME,
    build_manifest,
    lock_objects,
    resolve_objects,
    write_manifest,
)
from corpus_tools.paths import REPO_ROOT
from corpus_tools.patterns import PATTERNS_FILENAME, load_patterns, matches_corpus_pattern
from publish_corpus import (
    PublishTargetRefused,
    corpus_paths,
    guard_against_publishing_private_corpus_publicly,
    guard_against_root_outside_the_corpus,
    parse_args,
    resolve_targets,
)

PRIVATE_BUCKET = "internal-corpus"


def private_tree(root: Path, relative_paths: list[str], patterns: str = "data/*\n") -> Path:
    """A corpus root shaped like the real one: a data/ subtree plus prose beside it."""
    patterns_path = root / "corpus-patterns.txt"
    patterns_path.write_text(patterns, encoding="utf-8")
    for rel_path in relative_paths:
        target = root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(rel_path.encode())
    return patterns_path


class TargetResolutionTest(unittest.TestCase):
    def test_should_default_every_target_to_this_repository(self) -> None:
        args = parse_args(["--dry-run"])
        root, manifest, patterns = resolve_targets(args)

        self.assertTrue((root / MANIFEST_FILENAME).is_file())
        self.assertEqual(manifest, root / MANIFEST_FILENAME)
        self.assertEqual(patterns.name, "corpus-patterns.txt")

    def test_should_select_root_manifest_and_patterns_independently(self) -> None:
        args = parse_args(
            [
                "--dry-run",
                "--root",
                "/tmp/corpus",
                "--manifest",
                "/tmp/elsewhere/corpus.lock.json",
                "--patterns",
                "/tmp/other/patterns.txt",
            ]
        )
        root, manifest, patterns = resolve_targets(args)

        self.assertEqual(root, Path("/tmp/corpus").resolve())
        self.assertEqual(manifest, Path("/tmp/elsewhere/corpus.lock.json").resolve())
        self.assertEqual(patterns, Path("/tmp/other/patterns.txt").resolve())


DEFAULT_MANIFEST = REPO_ROOT / MANIFEST_FILENAME
DEFAULT_PATTERNS = REPO_ROOT / PATTERNS_FILENAME
FOREIGN_ROOT = Path("/tmp/internal-corpus").resolve()
FOREIGN_MANIFEST = FOREIGN_ROOT / "corpus.lock.json"
FOREIGN_PATTERNS = FOREIGN_ROOT / "corpus-patterns.txt"


class PublicBucketGuardTest(unittest.TestCase):
    """Each of the three targets selects the byte set, so each must be checked independently."""

    def test_should_refuse_a_foreign_root_aimed_at_the_public_bucket(self) -> None:
        with self.assertRaises(PublishTargetRefused) as caught:
            guard_against_publishing_private_corpus_publicly(
                FOREIGN_ROOT, DEFAULT_MANIFEST, DEFAULT_PATTERNS, DEFAULT_BUCKET
            )

        self.assertIn(DEFAULT_BUCKET, str(caught.exception))
        self.assertIn("--root", str(caught.exception))

    def test_should_refuse_a_foreign_manifest_aimed_at_the_public_bucket(self) -> None:
        with self.assertRaises(PublishTargetRefused) as caught:
            guard_against_publishing_private_corpus_publicly(
                REPO_ROOT, FOREIGN_MANIFEST, DEFAULT_PATTERNS, DEFAULT_BUCKET
            )

        self.assertIn("--manifest", str(caught.exception))

    def test_should_refuse_a_foreign_pattern_file_aimed_at_the_public_bucket(self) -> None:
        # ~keep The gap this closes: root and manifest both look like the defaults, but a pattern
        # file containing `*` sweeps the entire working tree into a world-readable bucket.
        with self.assertRaises(PublishTargetRefused) as caught:
            guard_against_publishing_private_corpus_publicly(
                REPO_ROOT, DEFAULT_MANIFEST, Path("/tmp/everything.txt").resolve(), DEFAULT_BUCKET
            )

        self.assertIn("--patterns", str(caught.exception))

    def test_should_allow_a_foreign_root_aimed_at_a_private_bucket(self) -> None:
        guard_against_publishing_private_corpus_publicly(
            FOREIGN_ROOT, FOREIGN_MANIFEST, FOREIGN_PATTERNS, PRIVATE_BUCKET
        )

    def test_should_allow_this_repository_to_publish_to_the_public_bucket(self) -> None:
        guard_against_publishing_private_corpus_publicly(REPO_ROOT, DEFAULT_MANIFEST, DEFAULT_PATTERNS, DEFAULT_BUCKET)


class RootAboveCorpusGuardTest(unittest.TestCase):
    """The check that catches aiming one level too high, where publishing is irreversible."""

    def test_should_refuse_a_root_above_where_the_named_targets_put_the_corpus(self) -> None:
        # ~keep The real mistake, exactly as it would be typed: the corpus is in a subdirectory and
        # the parent holds unrelated archives that `*.zip` matches at any depth.
        with self.assertRaises(PublishTargetRefused) as caught:
            guard_against_root_outside_the_corpus(
                Path("/tmp/downloads"),
                [
                    Path("/tmp/downloads/internal-corpus/corpus.lock.json"),
                    Path("/tmp/downloads/internal-corpus/corpus-patterns.txt"),
                ],
                allow_external=False,
            )

        self.assertIn("any depth", str(caught.exception))
        self.assertIn("/tmp/downloads/internal-corpus", str(caught.exception))

    def test_should_refuse_when_only_the_pattern_file_reveals_the_tighter_root(self) -> None:
        # ~keep With --manifest omitted it is derived FROM the root, so it can never disagree with
        # it. Only the explicitly-named pattern file shows where the corpus really is.
        with self.assertRaises(PublishTargetRefused):
            guard_against_root_outside_the_corpus(
                Path("/tmp/downloads"),
                [Path("/tmp/downloads/internal-corpus/corpus-patterns.txt")],
                allow_external=False,
            )

    def test_should_allow_targets_that_sit_directly_in_the_root(self) -> None:
        guard_against_root_outside_the_corpus(
            Path("/tmp/internal-corpus"),
            [
                Path("/tmp/internal-corpus/corpus.lock.json"),
                Path("/tmp/internal-corpus/corpus-patterns.txt"),
            ],
            allow_external=False,
        )

    def test_should_allow_the_default_publish_where_nothing_was_named_explicitly(self) -> None:
        guard_against_root_outside_the_corpus(REPO_ROOT, [], allow_external=False)

    def test_should_allow_an_external_root_when_explicitly_permitted(self) -> None:
        guard_against_root_outside_the_corpus(
            Path("/tmp/downloads"),
            [Path("/tmp/downloads/internal-corpus/corpus-patterns.txt")],
            allow_external=True,
        )


class AnchoredPatternTest(unittest.TestCase):
    """An anchored `data/*` cannot under-publish the way an extension list can."""

    def test_should_select_every_file_beneath_the_data_subtree(self) -> None:
        patterns = ["data/*"]
        for rel_path in ("data/a/one.pdf", "data/b/nested/two.geojson", "data/c/three.sqlite"):
            with self.subTest(path=rel_path):
                self.assertTrue(matches_corpus_pattern(rel_path, patterns))

    def test_should_leave_the_prose_beside_the_corpus_out_of_the_publish_set(self) -> None:
        # ~keep README/CHECKSUMS/MANIFEST.csv belong in git next to the manifest, not in the bucket
        # as corpus objects. An extension list containing *.csv and *.json would have swept them in.
        patterns = ["data/*"]
        for rel_path in ("README.md", "CHECKSUMS.sha256", "MANIFEST.csv", "manifest-summary.json"):
            with self.subTest(path=rel_path):
                self.assertFalse(matches_corpus_pattern(rel_path, patterns))

    def test_should_enumerate_exactly_the_data_subtree_from_a_real_directory(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            patterns_path = private_tree(
                root,
                ["data/one.pdf", "data/nested/two.csv", "data/nested/three.geojson", "README.md", "MANIFEST.csv"],
            )

            found = corpus_paths(root, load_patterns(root, patterns_path))

            self.assertEqual(found, ["data/nested/three.geojson", "data/nested/two.csv", "data/one.pdf"])


class MultipleManifestsTest(unittest.TestCase):
    """Two manifests over one content-addressed store — a curated CI subset and the full set."""

    def test_should_describe_a_subset_without_duplicating_any_object(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            patterns_path = private_tree(root, ["data/a.pdf", "data/b.pdf", "data/c.pdf"])
            full_paths = corpus_paths(root, load_patterns(root, patterns_path))

            full = resolve_objects(root, full_paths)
            curated = resolve_objects(root, full_paths[:2])

            full_manifest = build_manifest(full)
            curated_manifest = build_manifest(curated)

            self.assertEqual(len(curated_manifest["objects"]), 2)
            self.assertEqual(len(full_manifest["objects"]), 3)
            for path, entry in curated_manifest["objects"].items():
                self.assertEqual(entry["sha256"], full_manifest["objects"][path]["sha256"])

    def test_should_round_trip_a_manifest_written_outside_the_repository(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            patterns_path = private_tree(root, ["data/a.pdf", "data/b.pdf"])

            objects = resolve_objects(root, corpus_paths(root, load_patterns(root, patterns_path)))
            destination = root / "corpus.lock.json"
            write_manifest(build_manifest(objects), destination)

            self.assertEqual(set(lock_objects(destination)), {"data/a.pdf", "data/b.pdf"})


class AdcCredentialTest(unittest.TestCase):
    def _runner(self, *, returncode: int = 0, stdout: str = "ya29.token\n", stderr: str = ""):
        calls: list[list[str]] = []

        def run(command, **_kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, returncode, stdout, stderr)

        return run, calls

    def test_should_send_a_bearer_header_only_when_a_credential_is_supplied(self) -> None:
        run, calls = self._runner()
        anonymous_run, anonymous_calls = self._runner()

        CurlTransport(anonymous_run).fetch("https://example.invalid/x", timeout=30)
        CurlTransport(run, credential=AdcCredential(run)).fetch("https://example.invalid/x", timeout=30)

        self.assertNotIn("-H", anonymous_calls[0])
        self.assertIn("Authorization: Bearer ya29.token", calls[-1])

    def test_should_reuse_a_token_within_its_lifetime_rather_than_shelling_out_per_object(self) -> None:
        run, calls = self._runner()
        now = 0.0
        credential = AdcCredential(run, clock=lambda: now)

        credential.token()
        credential.token()

        self.assertEqual(len([c for c in calls if "print-access-token" in c]), 1)

    def test_should_refresh_a_token_before_a_long_transfer_can_outlive_it(self) -> None:
        # ~keep The reason this class exists. A WIF token lasts an hour and cannot be extended, and
        # the private corpus is 15.26 GB — long enough on a slow runner to 401 mid-fetch if the
        # credential were minted once at startup.
        run, calls = self._runner()
        elapsed = [0.0]
        credential = AdcCredential(run, clock=lambda: elapsed[0])

        credential.token()
        elapsed[0] = ACCESS_TOKEN_MAX_AGE_SECONDS + 1
        credential.token()

        self.assertEqual(len([c for c in calls if "print-access-token" in c]), 2)

    def test_should_date_a_token_from_after_acquisition_not_before(self) -> None:
        # ~keep gcloud can take a second or two. Stamping the age from before the call shortens the
        # token's usable life by exactly the acquisition time, which is the wrong direction to err
        # in when the whole point is surviving a 15 GB transfer.
        now = [0.0]
        calls: list[list[str]] = []

        def slow_gcloud(command, **_kwargs):
            calls.append(command)
            now[0] += 5.0  # acquisition genuinely takes time
            return subprocess.CompletedProcess(command, 0, "ya29.token\n", "")

        credential = AdcCredential(slow_gcloud, clock=lambda: now[0])

        credential.token()

        self.assertEqual(credential._acquired_at, 5.0, "the token must be dated from after gcloud returned")
        self.assertEqual(len(calls), 1)

    def test_should_not_retry_a_credential_failure_across_every_object(self) -> None:
        # ~keep A missing ADC login fails identically every time. Retrying turns one clear message
        # into attempts x objects subprocesses and seconds of backoff before saying the same thing.
        run, _ = self._runner(returncode=1, stderr="ERROR: (gcloud.auth) not logged in")
        transport = CurlTransport(run, credential=AdcCredential(run))
        attempts: list[float] = []

        with self.assertRaises(CredentialError):
            get(
                "https://example.invalid/o",
                timeout=30,
                transport=transport,
                sleep=attempts.append,
            )

        self.assertEqual(attempts, [], "a credential failure must not sleep for a retry")

    def test_should_explain_how_to_authenticate_when_no_credential_is_available(self) -> None:
        run, _ = self._runner(returncode=1, stderr="ERROR: (gcloud.auth) not logged in")

        with self.assertRaises(HttpError) as caught:
            AdcCredential(run).token()

        self.assertIn("application-default login", str(caught.exception))


class FetchTransportSelectionTest(unittest.TestCase):
    """--auth must be opt-in, or the credential-free proof this repo's CI runs means nothing."""

    def test_should_build_an_anonymous_transport_by_default(self) -> None:
        transport = fetch_corpus.build_transport(fetch_corpus.parse_args([]))

        self.assertIsNone(transport._credential)

    def test_should_build_a_credentialed_transport_only_when_auth_is_requested(self) -> None:
        transport = fetch_corpus.build_transport(fetch_corpus.parse_args(["--auth"]))

        self.assertIsInstance(transport._credential, AdcCredential)
