"""Which working-tree paths are corpus, and which manifest paths a caller asked for.

~keep Two predicates that look alike and are not, which is exactly why they belong side by side.

matches_corpus_pattern answers "is this file corpus?" using gitignore semantics, because the
pattern list was lifted verbatim from the old .gitattributes filter: a pattern containing '/' is
anchored to the repo root, one without matches a BASENAME AT ANY DEPTH. That last clause is sharp
— `*.zip` matches a zip anywhere below the root, including inside a directory nobody meant to
publish — and it is why the publisher prunes and guards rather than trusting the walk.

matches_any answers "did the caller's --include glob select this manifest path?" using plain
fnmatch against the whole path. It is deliberately looser and has nothing to do with gitignore.
"""

from fnmatch import fnmatch
from pathlib import Path

PATTERNS_FILENAME = "scripts/data/corpus-patterns.txt"


def load_patterns(root: Path, patterns_path: Path | None = None) -> list[str]:
    """Read the pattern list, dropping comments and blanks.

    ~keep patterns_path is what lets a private corpus bring its own list. It stays optional and
    defaults to the repo's own, so every existing caller is unaffected.
    """
    source = patterns_path if patterns_path is not None else root / PATTERNS_FILENAME
    text = source.read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]


def matches_corpus_pattern(rel_path: str, patterns: list[str]) -> bool:
    # ~keep gitattributes/gitignore semantics, which these patterns were lifted from: a pattern
    # containing '/' is anchored to the repo root, one without matches a basename at any depth.
    basename = rel_path.rsplit("/", 1)[-1]
    return any(fnmatch(rel_path, p) if "/" in p else fnmatch(basename, p) for p in patterns)


def matches_any(rel_path: str, patterns: list[str]) -> bool:
    # ~keep '**' is not special to fnmatch, whose '*' already crosses '/', so 'pdf/**' and 'pdf/*'
    # both mean "anything under pdf/". Callers write the glob they'd write for the CI action.
    return any(fnmatch(rel_path, pattern) for pattern in patterns)
