"""Reference-only upstream pins, separate from the redistributable bucket lock."""

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from corpus_tools.hashing import sha256_file
from corpus_tools.http import DEFAULT_RETRY, SOURCE_FILE_TIMEOUT_SECONDS, RetryPolicy, Transport, UrllibTransport, get
from corpus_tools.manifest import validate_manifest_path
from corpus_tools.materialize import STATUS_SKIPPED, materialize_one
from corpus_tools.paths import DATA_DIR

INVENTORY_PATH = DATA_DIR / "benchmark-upstreams.json"
FORMAT = "xberg-benchmark-upstreams"
CONTENT_RIGHTS = "reference/unreviewed"
SOURCES: dict[str, dict[str, object]] = {
    "parsebench-tables": {
        "dataset": "llamaindex/ParseBench",
        "dataset_revision": "2805a1d940f95a203e0ae4b88be9934f7765b3fc",
        "evaluator": "run-llama/ParseBench",
        "evaluator_revision": "328c71109e0b955f66583c33ec95ac52d9749db4",
        "pdf_count": 503,
        "jsonl_count": 1,
        "groups": {"table": {"pdf_count": 503, "test_rows": 503}},
        "annotations_license": "Apache-2.0",
        "annotations_license_url": "https://www.apache.org/licenses/LICENSE-2.0",
        "attribution": (
            "Boyang Zhang, Sebastián G. Acosta, Preston Carlson, Sacha Bron, Pierre-Loïc Doulcet, "
            "Daniel B. Ospina, and Simon Suo / ParseBench"
        ),
        "database_license": "not separately specified",
        "content_rights": CONTENT_RIGHTS,
        "redistribution": "reference-only",
    },
    "olmocr-issue2331": {
        "dataset": "allenai/olmOCR-bench",
        "dataset_revision": "54a96a6fb6a2bd3b297e59869491db4d3625b711",
        "evaluator": "allenai/olmocr",
        "evaluator_revision": "f7cfe4c22098b154c76b6ec950d1c0a464eecf8d",
        "pdf_count": 984,
        "jsonl_count": 5,
        "groups": {
            "arxiv_math": {"pdf_count": 522, "test_rows": 2927},
            "old_scans_math": {"pdf_count": 36, "test_rows": 458},
            "old_scans": {"pdf_count": 98, "test_rows": 526},
            "long_tiny_text": {"pdf_count": 62, "test_rows": 442},
            "headers_footers": {"pdf_count": 266, "test_rows": 760},
        },
        "annotations_license": "not separately specified",
        "database_license": "ODC-BY-1.0",
        "database_license_url": "https://opendatacommons.org/licenses/by/1-0/",
        "attribution": "Allen Institute for AI / olmOCR-bench",
        "content_rights": CONTENT_RIGHTS,
        "redistribution": "reference-only",
    },
}


@dataclass(frozen=True)
class AssetPin:
    path: str
    sha256: str
    size: int
    url: str
    source: str
    kind: str
    upstream_path: str
    group: str
    record_id: str | None = None


def _mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError("expected an object with string keys")
    return value


def _text(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("expected a nonempty string")
    return value


def _integer(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("expected a positive integer")
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path: Path) -> dict[str, object]:
    return _mapping(json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object))


def upstream_url(source: str, upstream_path: str) -> str:
    descriptor = SOURCES[source]
    return (
        f"https://huggingface.co/datasets/{descriptor['dataset']}/resolve/"
        f"{descriptor['dataset_revision']}/{quote(upstream_path, safe='/')}"
    )


def validate_pin(pin: AssetPin) -> None:
    validate_manifest_path(pin.path)
    validate_manifest_path(pin.upstream_path)
    if any(ord(character) < 32 for character in pin.path):
        raise ValueError("control character in asset path")
    if pin.source not in SOURCES or pin.path != f"{pin.source}/{pin.upstream_path}":
        raise ValueError("asset path does not match source namespace")
    groups = _mapping(SOURCES[pin.source]["groups"])
    if pin.group not in groups or pin.kind not in {"pdf", "jsonl"}:
        raise ValueError("unexpected asset kind or group")
    if pin.url != upstream_url(pin.source, pin.upstream_path):
        raise ValueError("asset URL does not match pinned upstream revision and path")
    if len(pin.sha256) != 64 or any(character not in "0123456789abcdef" for character in pin.sha256):
        raise ValueError("invalid asset SHA-256")
    _integer(pin.size)
    _validate_asset_shape(pin)


def _validate_asset_shape(pin: AssetPin) -> None:
    if pin.source == "parsebench-tables":
        valid = (
            pin.upstream_path.startswith("docs/table/") and pin.upstream_path.endswith(".pdf")
            if pin.kind == "pdf"
            else pin.upstream_path == "table.jsonl"
        )
        id_length = 20
    else:
        valid = (
            pin.upstream_path.startswith(f"bench_data/pdfs/{pin.group}/") and pin.upstream_path.endswith(".pdf")
            if pin.kind == "pdf"
            else pin.upstream_path == f"bench_data/{pin.group}.jsonl"
        )
        id_length = 10
    if not valid:
        raise ValueError("unexpected upstream asset path")
    if pin.kind == "pdf" and (
        not isinstance(pin.record_id, str)
        or len(pin.record_id) != id_length
        or any(character not in "0123456789abcdef" for character in pin.record_id)
    ):
        raise ValueError("invalid opaque PDF record id")
    if pin.kind == "jsonl" and pin.record_id is not None:
        raise ValueError("JSONL assets do not have PDF record ids")


def _parse_pin(path: str, value: object) -> AssetPin:
    entry = _mapping(value)
    if entry.get("content_rights") != CONTENT_RIGHTS:
        raise ValueError("asset content rights must remain reference/unreviewed")
    pin = AssetPin(
        path=path,
        sha256=_text(entry["sha256"]),
        size=_integer(entry["size"]),
        url=_text(entry["url"]),
        source=_text(entry["source"]),
        kind=_text(entry["kind"]),
        upstream_path=_text(entry["upstream_path"]),
        group=_text(entry["group"]),
        record_id=_text(entry["id"]) if entry.get("id") is not None else None,
    )
    validate_pin(pin)
    return pin


def load_inventory(path: Path = INVENTORY_PATH) -> list[AssetPin]:
    value = read_json(path)
    if value.get("format") != FORMAT or value.get("schema_version") != 1:
        raise ValueError("unsupported benchmark upstream descriptor")
    if value.get("sources") != SOURCES:
        raise ValueError("sources must match the complete pinned benchmark inventory")
    objects = _mapping(value["objects"])
    if not objects:
        raise ValueError("empty upstream inventory")
    pins = [_parse_pin(path, entry) for path, entry in objects.items()]
    if len({pin.path.casefold() for pin in pins}) != len(pins):
        raise ValueError("duplicate case-insensitive asset path")
    _validate_counts(pins)
    return pins


def _validate_counts(pins: list[AssetPin]) -> None:
    counts = Counter((pin.source, pin.kind, pin.group) for pin in pins)
    ids = [(pin.source, pin.record_id) for pin in pins if pin.kind == "pdf"]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate PDF record id")
    for source, descriptor in SOURCES.items():
        for group, expected_value in _mapping(descriptor["groups"]).items():
            expected = _mapping(expected_value)
            if counts[source, "pdf", group] != expected["pdf_count"] or counts[source, "jsonl", group] != 1:
                raise ValueError(f"incomplete inventory count for {source}/{group}")


def safe_cache_root(root: Path) -> Path:
    resolved = root.expanduser().resolve()
    if any((parent / ".git").exists() for parent in (resolved, *resolved.parents)):
        raise ValueError("reference-only cache must be outside every Git working tree")
    return resolved


def _destination(root: Path, pin: AssetPin) -> Path:
    root = safe_cache_root(root)
    validate_pin(pin)
    destination = root / pin.path
    sidecar = destination.with_suffix(destination.suffix + ".mismatch")
    if any(not path.resolve().is_relative_to(root) for path in (destination, sidecar)):
        raise ValueError("asset path escapes cache through a symlink")
    return destination


def fetch_one(
    pin: AssetPin,
    root: Path,
    *,
    verify_only: bool = False,
    transport: Transport | None = None,
    retry: RetryPolicy = DEFAULT_RETRY,
) -> str:
    destination = _destination(root, pin)
    if destination.is_file():
        if destination.stat().st_size == pin.size and sha256_file(destination) == pin.sha256:
            return STATUS_SKIPPED
        if verify_only:
            return "mismatch existing file does not match pin"
    elif verify_only:
        return "missing file"

    def produce() -> bytes:
        payload = get(
            pin.url,
            timeout=SOURCE_FILE_TIMEOUT_SECONDS,
            transport=transport if transport is not None else UrllibTransport(),
            retry=retry,
        )
        if len(payload) != pin.size:
            raise ValueError(f"size mismatch: expected {pin.size}, received {len(payload)}")
        return payload

    return materialize_one(destination, pin.sha256, produce, force=True)
