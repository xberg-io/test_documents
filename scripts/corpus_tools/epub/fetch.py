"""Fetch-or-build each EPUB edge case from the source its manifest records."""

from corpus_tools import paths
from corpus_tools.epub import build as build_epub_edge_cases
from corpus_tools.http import SOURCE_FILE_TIMEOUT_SECONDS, UrllibTransport, get
from corpus_tools.materialize import materialize_one

REPO_ROOT = paths.REPO_ROOT
MANIFEST = Path(__file__).resolve().parent / "data" / "epub-edge-cases.json"


TRANSPORT = UrllibTransport()


def fetch(url: str) -> bytes:
    return get(url, timeout=SOURCE_FILE_TIMEOUT_SECONDS, transport=TRANSPORT)


def materialize(path: str, entry: dict[str, Any], generated: dict[str, bytes]) -> bytes:
    if "url" in entry:
        return fetch(entry["url"])
    if "members" in entry:
        members = [(name, fetch(url)) for name, url in entry["members"].items() if name != "mimetype"]
        return build_epub_edge_cases.pack(members)
    if entry.get("generated"):
        return generated[path]
    raise ValueError(f"{path}: entry has no url, members or generated source")


def fetch_one(path: str, entry: dict[str, Any], force: bool, generated: dict[str, bytes]) -> tuple[str, str]:
    """Return (path, status). Status is ok, skipped, mismatch or an error."""
    status = materialize_one(
        REPO_ROOT / path,
        entry["sha256"],
        lambda: materialize(path, entry, generated),
        force=force,
    )
    return path, status
