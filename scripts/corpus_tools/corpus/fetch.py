"""Materialising pinned objects from the bucket into a working tree."""

from pathlib import Path

from corpus_tools.hashing import sha256_bytes, sha256_file
from corpus_tools.http import (
    BUCKET_OBJECT_TIMEOUT_SECONDS,
    DEFAULT_RETRY,
    CurlTransport,
    HttpError,
    RetryPolicy,
    Transport,
    get,
)
from corpus_tools.manifest import object_url, validate_manifest_path

MAX_REPORTED_FAILURES = 20


def fetch_one(
    bucket: str,
    root: Path,
    rel_path: str,
    sha256: str,
    *,
    transport: Transport | None = None,
    retry: RetryPolicy = DEFAULT_RETRY,
) -> str | None:
    """Materialise one object. transport/retry are injectable so tests need no network or backoff."""
    root = root.resolve()
    destination = root / validate_manifest_path(rel_path)
    if not destination.resolve().is_relative_to(root):
        raise ValueError(f"manifest path escapes the corpus root through a symlink: {rel_path!r}")
    if destination.is_file() and sha256_file(destination) == sha256:
        return None

    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        payload = get(
            object_url(bucket, sha256),
            timeout=BUCKET_OBJECT_TIMEOUT_SECONDS,
            transport=transport if transport is not None else CurlTransport(),
            retry=retry,
        )
    except HttpError as error:
        return f"{rel_path}: {error.reason}"

    actual = sha256_bytes(payload)
    if actual != sha256:
        return f"{rel_path}: expected {sha256} but bucket served {actual}"
    destination.write_bytes(payload)
    return None
