"""The corpus must be unreachable by the formatters, and that has to be tested, not configured.

This repo is a fixture corpus. Every directory except scripts/ holds documents whose exact bytes
are the thing under test — malformed XML, legacy encodings, deliberate typos, hand-authored
whitespace, deliberately unused imports. A formatter that "fixes" one of them destroys a fixture,
and the damage is silent: the file still parses, the tests that read it still pass, and the corpus
now disagrees with the ground truth that describes it. It has happened once already, which is why
`9f9e3d4 fix: keep poly from rewriting corpus fixtures (#9)` exists.

Two layers are asserted here, and the first matters more:

  * Behavioural — shell out to the REAL ruff and prove it refuses each canary file. This tests the
    property that matters (ruff will not touch this file) rather than a proxy for it (a string is
    present in a list). It fails if force-exclude is dropped, if include is widened, if an
    extend-exclude entry is deleted, or if a ruff upgrade changes exclusion semantics — which is
    exactly when you want to be told.
  * Declarative — poly.toml and pyproject.toml must agree about what the corpus is, so adding a
    corpus directory to one and forgetting the other is a test failure rather than a live hazard.

~keep Nothing here is skipped when ruff is missing. A skipped guard is a green run that proved
nothing, and this is the guard that stands between a formatter and 580 MiB of fixtures.
"""

import shutil
import subprocess
import sys
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10, where tomllib is not yet stdlib
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
POLY_TOML = REPO_ROOT / "poly.toml"

# ~keep One file per hazard class, not a sample. code/hello.py is the only .py outside scripts/ and
# its two unused imports are the entire point of the fixture — F401 is a SAFE fix, so a bare
# `ruff check --fix .` deletes them. The notebooks are here because `ruff format` handles .ipynb
# natively: without the "*.ipynb" exclude it rewrites four of these and fails to parse three more.
# data_formats/pyproject.toml is a fixture that ruff would otherwise resolve as a config root.
CANARY_FILES = (
    "code/hello.py",
    "jupyter/mime.ipynb",
    "jupyter/math/eseries_37d1f4.ipynb",
    "jupyter/math/SymPy_9b271e.ipynb",
    "vendored/markitdown/test_notebook.ipynb",
)

REFUSAL = "No Python files found under the given path(s)"


def ruff_command() -> list[str]:
    """Locate ruff without assuming how the suite was invoked.

    ~keep The suite must run two ways: `uv run pytest` and, with zero installs, `python3 -m unittest
    discover -s scripts/tests -t scripts`. Under the latter the interpreter is the system one, so
    `sys.executable -m ruff` fails even though a perfectly good ruff sits in .venv/bin. Look there
    first, then on PATH, then fall back to the current interpreter. Deliberately NOT a skip: a
    skipped canary is a green run that proved nothing, so with no ruff anywhere this fails loudly.
    """
    local = REPO_ROOT / ".venv" / "bin" / "ruff"
    if local.is_file():
        return [str(local)]
    on_path = shutil.which("ruff")
    if on_path:
        return [on_path]
    return [sys.executable, "-m", "ruff"]


def ruff(*arguments: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [*ruff_command(), *arguments],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if "No module named ruff" in result.stderr:
        raise AssertionError(
            "ruff is not installed, so the corpus-protection canaries cannot run. Run `uv sync --group dev`."
        )
    return result


def corpus_directories_from_poly() -> set[str]:
    """The directories poly.toml excludes, as bare names.

    ~keep poly anchors some entries with a leading slash ("/office/**"). ruff's globset SILENTLY
    IGNORES a leading slash, so the two files cannot be compared as raw strings — normalise to bare
    directory names on both sides or the comparison is vacuous.
    """
    config = tomllib.loads(POLY_TOML.read_text(encoding="utf-8"))
    excluded = config["discovery"]["exclude"]
    return {entry[:-3].lstrip("/") for entry in excluded if entry.endswith("/**")}


def ruff_excluded_directories() -> set[str]:
    config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return {entry for entry in config["tool"]["ruff"]["extend-exclude"] if not entry.startswith("*")}


class RuffRefusesCorpusFilesTest(unittest.TestCase):
    """The behavioural layer: ask the real binary, believe only what it says."""

    def test_should_refuse_to_format_a_corpus_fixture_named_explicitly(self) -> None:
        for relative_path in CANARY_FILES:
            with self.subTest(path=relative_path):
                self.assertTrue(
                    (REPO_ROOT / relative_path).is_file(),
                    f"{relative_path} is missing, so this test would pass without proving anything",
                )
                result = ruff("format", "--check", relative_path)
                self.assertIn(
                    REFUSAL,
                    result.stdout + result.stderr,
                    f"ruff format processed the corpus fixture {relative_path} instead of refusing it. "
                    "Check force-exclude and extend-exclude in pyproject.toml.",
                )

    def test_should_refuse_to_lint_a_corpus_fixture_named_explicitly(self) -> None:
        for relative_path in CANARY_FILES:
            with self.subTest(path=relative_path):
                result = ruff("check", "--no-fix", relative_path)
                self.assertIn(
                    REFUSAL,
                    result.stdout + result.stderr,
                    f"ruff check reached the corpus fixture {relative_path}",
                )

    def test_should_reach_no_file_outside_scripts_when_run_over_the_whole_repo(self) -> None:
        result = ruff("check", "--no-fix", "--output-format", "concise", ".")
        offenders = {
            line.split(":", 1)[0]
            for line in result.stdout.splitlines()
            if ":" in line and not line.startswith(("warning:", "error:", "Found ", "[*]"))
        }
        outside = sorted(path for path in offenders if not path.startswith("scripts/"))
        self.assertEqual(outside, [], f"ruff reported findings outside scripts/: {outside}")

    def test_should_keep_force_exclude_enabled_so_an_explicit_path_cannot_bypass_the_list(self) -> None:
        # ~keep Asserted separately from the behavioural tests because it is the single setting that
        # makes them pass. Verified by experiment: with force-exclude off, `ruff format --check
        # jupyter/mime.ipynb` reports "1 file already formatted" — it read and would rewrite the
        # fixture. Exclusions alone only apply while walking directories.
        config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
        self.assertIs(config["tool"]["ruff"]["force-exclude"], True)

    def test_should_exclude_jupyter_notebooks_by_glob(self) -> None:
        # ~keep Belt to the jupyter/ directory exclude's braces: notebooks live under vendored/ too,
        # and `ruff format` reads .ipynb natively.
        config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
        self.assertIn("*.ipynb", config["tool"]["ruff"]["extend-exclude"])


class ExcludeListsAgreeTest(unittest.TestCase):
    """The declarative layer: poly.toml and pyproject.toml must describe the same corpus."""

    def test_should_exclude_from_ruff_every_corpus_directory_poly_excludes(self) -> None:
        missing = sorted(corpus_directories_from_poly() - ruff_excluded_directories())
        self.assertEqual(
            missing,
            [],
            f"poly.toml treats these as corpus but pyproject.toml does not exclude them from ruff: {missing}",
        )

    def test_should_exclude_from_poly_every_directory_ruff_excludes(self) -> None:
        missing = sorted(ruff_excluded_directories() - corpus_directories_from_poly())
        self.assertEqual(
            missing,
            [],
            f"pyproject.toml excludes these from ruff but poly.toml would still format them: {missing}",
        )

    def test_should_leave_only_scripts_unexcluded(self) -> None:
        """~keep Derived from git, not os.listdir.

        Only ~30 of the 53 top-level directories contain tracked files; the rest hold bucket-managed
        binaries absent from a fresh clone. A filesystem-derived expectation is therefore vacuously
        satisfied in CI, where none of them exist.
        """
        tracked = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        )
        top_level = {
            entry.split("/", 1)[0]
            for entry in tracked.stdout.decode().split("\0")
            if "/" in entry and not entry.startswith(".")
        }
        self.assertEqual(
            sorted(top_level - corpus_directories_from_poly()),
            ["scripts"],
            "a top-level directory holding tracked files is neither scripts/ nor excluded as corpus",
        )


class RuffConfigsAgreeTest(unittest.TestCase):
    """poly runs ruff with its own config, so the two must be kept in step by hand.

    ~keep Verified rather than assumed: before poly.toml carried a [lint.python.ruff] block, a file
    containing `from __future__ import annotations` was clean to `poly lint` and a TID251 error to
    `uv run ruff check`. Nothing surfaced that disagreement, and the repo's own commit hook and its
    CI gate were enforcing different rules.
    """

    def _poly_ruff(self) -> dict:
        return tomllib.loads(POLY_TOML.read_text(encoding="utf-8"))["lint"]["python"]["ruff"]

    def _pyproject_ruff(self) -> dict:
        return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["tool"]["ruff"]["lint"]

    def test_should_select_the_same_rules_in_both_configs(self) -> None:
        self.assertEqual(self._poly_ruff()["select"], self._pyproject_ruff()["select"])

    def test_should_ignore_the_same_rules_in_both_configs(self) -> None:
        self.assertEqual(sorted(self._poly_ruff()["ignore"]), sorted(self._pyproject_ruff()["ignore"]))

    def test_should_apply_the_same_per_file_ignores_in_both_configs(self) -> None:
        poly_per_file = tomllib.loads(POLY_TOML.read_text(encoding="utf-8"))["per-file-ignores"]
        for pattern, codes in self._pyproject_ruff()["per-file-ignores"].items():
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, poly_per_file)
                self.assertEqual(sorted(poly_per_file[pattern]), sorted(codes))

    def test_should_agree_on_the_complexity_and_docstring_limits(self) -> None:
        poly_ruff, pyproject_ruff = self._poly_ruff(), self._pyproject_ruff()

        self.assertEqual(poly_ruff["mccabe_max_complexity"], pyproject_ruff["mccabe"]["max-complexity"])
        self.assertEqual(poly_ruff["pydocstyle_convention"], pyproject_ruff["pydocstyle"]["convention"])
        self.assertEqual(poly_ruff["pylint_max_args"], pyproject_ruff["pylint"]["max-args"])

    def test_should_record_that_the_future_import_ban_lives_only_in_pyproject(self) -> None:
        """~keep poly cannot express it, and silently ignores the key if you try.

        `banned-api` is a ruff *setting*, not a rule code, and poly's [lint.python.ruff] has no key
        for it — an added `flake8_tidy_imports_banned_api` is accepted without complaint and has no
        effect. So the ban is enforced by the `uv run ruff check .` step in test-unit.yml and not by
        `poly lint`. This test exists so that asymmetry is written down rather than rediscovered.
        """
        banned = self._pyproject_ruff()["flake8-tidy-imports"]["banned-api"]

        self.assertIn("__future__.annotations", banned)
        self.assertNotIn("flake8_tidy_imports_banned_api", self._poly_ruff())
