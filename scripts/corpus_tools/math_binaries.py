"""Fetch the math corpus binaries from their original upstream sources."""

from typing import Any

from corpus_tools import paths
from corpus_tools.http import SOURCE_FILE_TIMEOUT_SECONDS, UrllibTransport, get
from corpus_tools.materialize import materialize_one

REPO_ROOT = paths.REPO_ROOT
MANIFEST = paths.MATH_MANIFEST_PATH


TRANSPORT = UrllibTransport()


def fetch_one(path: str, entry: dict[str, Any], force: bool) -> tuple[str, str]:
    """Return (path, status). Status is ok, skipped, mismatch or an error."""
    status = materialize_one(
        REPO_ROOT / path,
        entry["sha256"],
        lambda: get(entry["url"], timeout=SOURCE_FILE_TIMEOUT_SECONDS, transport=TRANSPORT),
        force=force,
    )
    return path, status
