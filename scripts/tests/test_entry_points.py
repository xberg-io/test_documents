"""Every entry point must still start, from anywhere, on a bare interpreter.

~keep This exists because the risk it covers is real and everything else misses it. The unit tests
import `corpus_tools` directly, so they never exercise the path a consumer takes; this repository's
CI runs exactly one of the ten tools; and around fourteen places in the xberg repo tell developers
to run `python3 test_documents/scripts/fetch_corpus.py` when a fixture is missing.

It has already earned its place. Moving the EPUB tools into a subpackage left two names unimported
and a `__file__`-relative data path pointing two directories too deep — `ruff` reported nothing, the
whole unit suite stayed green, and `fetch_epub_edge_cases.py` raised NameError at import.

Run from a temporary directory on purpose: a tool that only works when the current directory happens
to be the repository is broken for every consumer, and running from inside the repo hides that.
"""

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from corpus_tools import paths

ENTRY_POINTS = sorted(path.name for path in paths.SCRIPTS_DIR.glob("*.py") if path.name != "conftest.py")

EXPECTED_ENTRY_POINT_COUNT = 10


class EntryPointTest(unittest.TestCase):
    def test_should_still_have_every_frozen_entry_point(self) -> None:
        # ~keep These filenames are referenced by path from other repositories. Losing one is a
        # cross-repo break, and gaining one deserves a moment's thought about the same contract.
        self.assertEqual(len(ENTRY_POINTS), EXPECTED_ENTRY_POINT_COUNT, ENTRY_POINTS)

    def test_should_answer_help_from_an_unrelated_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as elsewhere:
            for name in ENTRY_POINTS:
                with self.subTest(entry_point=name):
                    result = subprocess.run(
                        [sys.executable, str(paths.SCRIPTS_DIR / name), "--help"],
                        cwd=elsewhere,
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    self.assertEqual(
                        result.returncode,
                        0,
                        f"{name} --help exited {result.returncode}:\n{result.stderr[-800:]}",
                    )
                    self.assertIn("usage:", result.stdout)

    def test_should_resolve_every_data_file_the_tools_read(self) -> None:
        # ~keep A `__file__`-relative data path silently points somewhere else the moment its module
        # moves, and finding nothing does not raise — it just yields an empty corpus.
        for label, path in (
            ("patterns", paths.PATTERNS_PATH),
            ("epub manifest", paths.EPUB_MANIFEST_PATH),
            ("math manifest", paths.MATH_MANIFEST_PATH),
            ("regression manifest", paths.REGRESSION_MANIFEST_PATH),
            ("lock file", paths.LOCK_PATH),
        ):
            with self.subTest(data_file=label):
                self.assertTrue(path.is_file(), f"{label} does not exist at {path}")

    def test_should_keep_the_scripts_directory_importable_without_a_package_marker(self) -> None:
        # ~keep scripts/__init__.py would stop pytest prepending scripts/ to sys.path, which is what
        # lets the tests import the tooling the way the entry points do.
        self.assertFalse((paths.SCRIPTS_DIR / "__init__.py").exists())
        self.assertTrue((paths.SCRIPTS_DIR / "tests" / "__init__.py").exists())

    def test_should_import_nothing_third_party_at_runtime(self) -> None:
        """~keep The tools run on a bare checkout with nothing installed. A third-party import here
        breaks every consumer, and it would break them at import time rather than at use."""
        allowed_first_party = {"corpus_tools", *(Path(name).stem for name in ENTRY_POINTS)}
        offenders: list[str] = []
        for source in [*paths.SCRIPTS_DIR.glob("*.py"), *(paths.SCRIPTS_DIR / "corpus_tools").rglob("*.py")]:
            # ~keep Parsed, not grepped: a docstring line beginning "from the content instead..."
            # reads as an import to a string match, and a test that cries wolf gets disabled.
            tree = ast.parse(source.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = [alias.name.split(".")[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    modules = [(node.module or "").split(".")[0]] if node.level == 0 else []
                else:
                    continue
                for module in modules:
                    if module in allowed_first_party or module in sys.stdlib_module_names:
                        continue
                    offenders.append(f"{source.relative_to(paths.REPO_ROOT)}:{node.lineno}: {module}")

        self.assertEqual(offenders, [], "third-party imports in the runtime tooling")
