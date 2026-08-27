"""Hash, compare, write — or write a .mismatch sidecar and say so.

~keep This is the duplication issue #11 describes in prose but gives no module. The same shape
appeared three times: fetch_math_binaries fused it into its fetch_one, fetch_epub_edge_cases had it
as a separate fetch_one, and fetch_regression split it across write_checked and up_to_date. All
three produced the same four-word status vocabulary and the same sidecar behaviour, and all three
differed slightly in how they said "error".

That last difference mattered: fetch_regression reported `error {error}` while the other two
reported `error {type}: {error}`, so a bare `RuntimeError()` from the regression fetcher printed as
the word "error" and nothing else. They agree now.
"""

from collections.abc import Callable
from pathlib import Path

from corpus_tools.hashing import sha256_bytes, sha256_file

MISMATCH_SUFFIX = ".mismatch"
DIGEST_PREFIX_LENGTH = 12

STATUS_OK = "ok"
STATUS_SKIPPED = "skipped"


def is_current(target: Path, expected_sha256: str) -> bool:
    return target.is_file() and sha256_file(target) == expected_sha256


def write_verified(target: Path, payload: bytes, expected_sha256: str) -> str:
    """Write `payload` to `target` only if it hashes as expected.

    ~keep On a mismatch the bytes go to a `.mismatch` sidecar and the target is left ALONE. A
    source that silently changed upstream must not overwrite a known-good fixture, and keeping the
    downloaded bytes is what lets a maintainer diff them and decide whether the pin or the source
    is wrong.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    digest = sha256_bytes(payload)
    if digest != expected_sha256:
        target.with_suffix(target.suffix + MISMATCH_SUFFIX).write_bytes(payload)
        return f"mismatch got {digest[:DIGEST_PREFIX_LENGTH]} want {expected_sha256[:DIGEST_PREFIX_LENGTH]}"
    target.write_bytes(payload)
    return STATUS_OK


def materialize_one(
    target: Path,
    expected_sha256: str,
    produce: Callable[[], bytes],
    *,
    force: bool = False,
) -> str:
    """Put the expected bytes at `target`, producing them only if they are not already there.

    Returns one of: "ok", "skipped", "mismatch got X want Y", or "error <Type>: <message>".
    `produce` is whatever gets the bytes — an HTTP fetch, a zip member, a deterministic build —
    which is the only thing that differed between the three copies this replaces.
    """
    if not force and is_current(target, expected_sha256):
        return STATUS_SKIPPED
    try:
        payload = produce()
    except Exception as error:  # noqa: BLE001 - reported per file so one bad source cannot abort the run
        return f"error {type(error).__name__}: {error}"
    return write_verified(target, payload, expected_sha256)
