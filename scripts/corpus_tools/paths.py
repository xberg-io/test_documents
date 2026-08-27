"""Every path the tooling resolves, derived once.

~keep Before this module, nine files each computed the repo root with their own
`Path(__file__).resolve().parent.parent`, so the arithmetic was correct only for a file at one
particular depth — and moving a file silently broke it, because a wrong root does not raise, it
just finds nothing. Deriving everything from this module's own location means the depth is written
down once, here, and no other module ever counts parents again.
"""

import subprocess
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = PACKAGE_DIR.parent
REPO_ROOT = SCRIPTS_DIR.parent
DATA_DIR = SCRIPTS_DIR / "data"

LOCK_PATH = REPO_ROOT / "corpus.lock.json"
PATTERNS_PATH = DATA_DIR / "corpus-patterns.txt"
EPUB_MANIFEST_PATH = DATA_DIR / "epub-edge-cases.json"
MATH_MANIFEST_PATH = DATA_DIR / "math-binaries.json"
REGRESSION_MANIFEST_PATH = DATA_DIR / "regression-objects.json"


def git_repo_root() -> Path:
    """The root according to git, which is not always REPO_ROOT.

    ~keep The publisher asks git rather than deriving from __file__, and keeps doing so. The two
    answers differ when the tool is run by path against a different working tree, and the publisher
    feeds this straight to `git -C` for its tracked-file guard — so the guard must be asking about
    the same repository git is. Everything that just needs "where does the corpus live" wants
    REPO_ROOT instead.
    """
    output = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], check=True, capture_output=True, text=True
    ).stdout.strip()
    return Path(output)
