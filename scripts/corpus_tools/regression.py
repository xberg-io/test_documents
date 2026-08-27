"""Fetch the regression corpus: direct files, plus members taken from published shards.

~keep The shard path exists because govdocs1 publishes archives rather than individual files. One
download yields 267 members, which is why SHARD_TIMEOUT_SECONDS is five times the others.
"""

import io
import zipfile
from pathlib import Path
from typing import Any

from corpus_tools import paths
from corpus_tools.http import SHARD_TIMEOUT_SECONDS, SOURCE_FILE_TIMEOUT_SECONDS, UrllibTransport, get
from corpus_tools.materialize import STATUS_SKIPPED, is_current, materialize_one, write_verified

REPO_ROOT = paths.REPO_ROOT
MANIFEST = paths.REGRESSION_MANIFEST_PATH


TRANSPORT = UrllibTransport()


def fetch_direct(path: str, entry: dict[str, Any], force: bool) -> list[tuple[str, str]]:
    status = materialize_one(
        REPO_ROOT / path,
        entry["sha256"],
        lambda: get(entry["url"], timeout=SOURCE_FILE_TIMEOUT_SECONDS, transport=TRANSPORT),
        force=force,
    )
    return [(path, status)]


def fetch_shard(url: str, members: list[tuple[str, dict[str, Any]]], force: bool) -> list[tuple[str, str]]:
    """Download one archive and take every member wanted from it."""
    wanted = [(p, e) for p, e in members if force or not is_current(REPO_ROOT / p, e["sha256"])]
    if not wanted:
        return [(p, STATUS_SKIPPED) for p, _ in members]
    try:
        blob = get(url, timeout=SHARD_TIMEOUT_SECONDS, transport=TRANSPORT)
    except Exception as error:  # noqa: BLE001 - one bad shard must not abort the whole run
        return [(p, f"error {type(error).__name__}: {error}") for p, _ in wanted]

    results: list[tuple[str, str]] = []
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        by_basename = {Path(n).name: n for n in archive.namelist()}
        for path, entry in wanted:
            name = by_basename.get(entry["member"])
            if name is None:
                results.append((path, f"error member {entry['member']} not in shard"))
                continue
            results.append((path, write_verified(REPO_ROOT / path, archive.read(name), entry["sha256"])))
    return results
