"""Generate metadata pins from verified staging and immutable Hugging Face tree evidence."""

import hashlib
import json
from pathlib import Path
from typing import cast

from corpus_tools.benchmark_upstreams import CONTENT_RIGHTS, FORMAT, SOURCES, load_inventory, read_json, upstream_url
from corpus_tools.hashing import sha256_file
from corpus_tools.manifest import validate_manifest_path

PARSEBENCH_TREE_SHA256 = "03c69e34c5026f0bc7102d681aec574e5a1f9c93a212d428f6be5171fff16003"
PARSEBENCH_JSONL_SHA256 = "66129fcc9e68ae0bf40e7d41f540002ceff9bedf46d6dafff2321ba2b7ab5231"
OLMOCR_TREE_SHA256 = {
    "arxiv_math": "fa67c004da51d5146c6652e3dee9d8a0d53bbfe79dbf4553c2a6414c15cff780",
    "old_scans_math": "36270774b7da800144cb4c589e6d40f66b3fe50b829c3d2eca4c54626214cfbd",
    "old_scans": "5ffffd1233544058b0e07dee5ff581e881b0b818a8b3bc66128fc12a452ae9b3",
    "long_tiny_text": "fc718dce1c23c5ddbd9f06679f6bcb95e28dd4500e510f292cf148517e52dc61",
    "headers_footers": "97b6eaeb6aa298fc81c43370e02a4fc3165ad2fdc2261f63c5b2bd1de72a53c9",
}
OLMOCR_BENCH_TREE_SHA256 = "41f60caa7836fa5ef3bd8b2ebbeae6c9fcde73daa23f1d8931d7f682009a4824"


def _rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise ValueError("expected a nonempty array of metadata objects")
    return cast("list[dict[str, object]]", value)


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("expected metadata object")
    return cast("dict[str, object]", value)


def _string(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("expected metadata string")
    return value


def _checked_path(root: Path, relative: str) -> Path:
    validate_manifest_path(relative)
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("staged asset escapes root through symlink")
    return path


def _tree(path: Path, expected: str) -> dict[str, dict[str, object]]:
    if sha256_file(path) != expected:
        raise ValueError("upstream tree metadata changed")
    rows = _rows(json.loads(path.read_text(encoding="utf-8")))
    result = {_string(row["path"]): row for row in rows if row.get("type") == "file"}
    if len(result) != sum(row.get("type") == "file" for row in rows):
        raise ValueError("duplicate upstream tree file")
    return result


def _check_original(path: Path, tree: dict[str, object]) -> tuple[str, int]:
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if len(payload) != tree["size"]:
        raise ValueError("upstream asset size mismatch")
    if "lfs" in tree:
        if digest != _object(tree["lfs"])["oid"]:
            raise ValueError("upstream LFS hash mismatch")
    else:
        git_blob = b"blob " + str(len(payload)).encode() + b"\0" + payload
        if hashlib.sha1(git_blob, usedforsecurity=False).hexdigest() != tree["oid"]:
            raise ValueError("upstream Git blob hash mismatch")
    return digest, len(payload)


def _entry(
    source: str, upstream: str, kind: str, *, group: str, digest: str, size: int, record_id: str | None
) -> dict[str, object]:
    return {
        "sha256": digest,
        "size": size,
        "url": upstream_url(source, upstream),
        "source": source,
        "kind": kind,
        "upstream_path": upstream,
        "group": group,
        "id": record_id,
        "content_rights": CONTENT_RIGHTS,
    }


def _stage(root: Path, source: str) -> dict[str, object]:
    stage = read_json(root / "stage.json")
    if any(stage.get(key) != SOURCES[source][key] for key in ("dataset_revision", "evaluator_revision")):
        raise ValueError("staging revisions differ from pinned upstream")
    return stage


def _parsebench(root: Path) -> dict[str, dict[str, object]]:
    source = "parsebench-tables"
    stage = _stage(root, source)
    tree = _tree(root / "hf-table-tree.json", PARSEBENCH_TREE_SHA256)
    jsonl = root / "table.jsonl"
    if sha256_file(jsonl) != PARSEBENCH_JSONL_SHA256:
        raise ValueError("pinned ParseBench JSONL changed")
    raw_rows = [read_json_line(line) for line in jsonl.read_text(encoding="utf-8").splitlines()]
    ids = {_string(row["pdf"]): hashlib.sha256(_string(row["id"]).encode()).hexdigest()[:20] for row in raw_rows}
    if len(ids) != 503 or len(raw_rows) != 503 or len(tree) != 503:
        raise ValueError("ParseBench source count mismatch")
    objects = {}
    for row in _rows(stage["records"]):
        upstream = _string(_object(row["upstream"])["pdf"])
        record_id = _string(row["id"])
        if ids.get(upstream) != record_id:
            raise ValueError("ParseBench stage identity mismatch")
        metadata = _object(row["pdf"])
        path = _checked_path(root, _string(metadata["file"]))
        digest, size = _check_original(path, tree[upstream])
        if digest != metadata["sha256"] or size != metadata["bytes"]:
            raise ValueError("ParseBench stage checksum mismatch")
        _add(
            objects,
            source,
            upstream,
            _entry(source, upstream, "pdf", group="table", digest=digest, size=size, record_id=record_id),
        )
    objects[f"{source}/table.jsonl"] = _entry(
        source,
        "table.jsonl",
        "jsonl",
        group="table",
        digest=PARSEBENCH_JSONL_SHA256,
        size=jsonl.stat().st_size,
        record_id=None,
    )
    return objects


def read_json_line(line: str) -> dict[str, object]:
    return _object(json.loads(line))


def _add(objects: dict[str, dict[str, object]], source: str, upstream: str, entry: dict[str, object]) -> None:
    key = f"{source}/{upstream}"
    if key in objects:
        raise ValueError("duplicate staged asset")
    objects[key] = entry


def _olmocr(root: Path) -> dict[str, dict[str, object]]:
    source = "olmocr-issue2331"
    stage = _stage(root, source)
    tree: dict[str, dict[str, object]] = {}
    for group, digest in OLMOCR_TREE_SHA256.items():
        tree.update(_tree(root / f"{group}-tree.json", digest))
    objects = {}
    for row in _rows(stage["records"]):
        upstream = _string(row["file"])
        record_id = hashlib.sha1(upstream.encode(), usedforsecurity=False).hexdigest()[:10]
        if record_id != row["id"]:
            raise ValueError("olmOCR stage identity mismatch")
        digest, size = _check_original(_checked_path(root, upstream), tree[upstream])
        if digest != row["sha256"] or size != row["bytes"]:
            raise ValueError("olmOCR stage checksum mismatch")
        group = Path(upstream).parts[2]
        _add(
            objects,
            source,
            upstream,
            _entry(source, upstream, "pdf", group=group, digest=digest, size=size, record_id=record_id),
        )
    annotation_tree = _tree(root / "bench-root-tree.json", OLMOCR_BENCH_TREE_SHA256)
    for group in OLMOCR_TREE_SHA256:
        upstream = f"bench_data/{group}.jsonl"
        path = _checked_path(root, upstream)
        digest, size = _check_original(path, annotation_tree[upstream])
        expected = _object(_object(SOURCES[source]["groups"])[group])["test_rows"]
        if len(path.read_text(encoding="utf-8").splitlines()) != expected:
            raise ValueError("olmOCR raw test count mismatch")
        _add(
            objects,
            source,
            upstream,
            _entry(source, upstream, "jsonl", group=group, digest=digest, size=size, record_id=None),
        )
    return objects


def build_inventory(parsebench: Path, olmocr: Path, destination: Path) -> int:
    """Reproduce the inventory without copying document or annotation contents."""
    objects = {**_parsebench(parsebench), **_olmocr(olmocr)}
    descriptor = {"format": FORMAT, "schema_version": 1, "sources": SOURCES, "objects": dict(sorted(objects.items()))}
    text = json.dumps(descriptor, indent=2, ensure_ascii=False) + "\n"
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    try:
        count = len(load_inventory(temporary))
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return count
