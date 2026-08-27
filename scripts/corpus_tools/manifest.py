"""corpus.lock.json: the shape it has, and the bytes it must keep.

~keep The serialisation here is a CROSS-REPO CONTRACT, not an implementation detail. Consumers
fetch the corpus through xberg-io/actions/fetch-test-documents, which hashes this file to key its
object cache (scripts/compute-cache-key.sh). Change the key order, the indent, or the trailing
newline and every consumer's cache is invalidated at once, and what the manifest pins changes with
it. Two lines decide those bytes: the `sorted(..., key=lambda o: o.path)` in build_manifest and the
`json.dumps(manifest, indent=2) + "\\n"` in write_manifest. scripts/tests/test_manifest.py proves
the pair round-trips the committed file byte for byte.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from corpus_tools.hashing import sha256_file

MANIFEST_SCHEMA_VERSION = 1
MANIFEST_FILENAME = "corpus.lock.json"
OBJECTS_PREFIX = "objects"
DEFAULT_BUCKET = "xberg-test-documents"


@dataclass(frozen=True)
class CorpusObject:
    path: str
    sha256: str
    size: int


def object_url(bucket: str, sha256: str) -> str:
    return f"https://storage.googleapis.com/{bucket}/{OBJECTS_PREFIX}/{sha256}"


def load_lock(manifest_path: Path) -> dict:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def lock_objects(manifest_path: Path) -> dict[str, dict]:
    return load_lock(manifest_path)["objects"]


def lock_pins(manifest_path: Path) -> dict[str, int]:
    """Map sha256 -> size. Duplicate paths collapse onto one object, which is the point."""
    return {entry["sha256"]: entry["size"] for entry in lock_objects(manifest_path).values()}


def resolve_objects(root: Path, paths: list[str]) -> list[CorpusObject]:
    """Hash real working-tree bytes — the only source of truth for what gets published."""
    objects = []
    for rel_path in paths:
        full_path = root / rel_path
        if not full_path.is_file():
            raise FileNotFoundError(f"corpus path has no content on disk: {rel_path}")
        objects.append(CorpusObject(path=rel_path, sha256=sha256_file(full_path), size=full_path.stat().st_size))
    return objects


def build_manifest(objects: list[CorpusObject]) -> dict:
    ordered_objects = {
        obj.path: {"sha256": obj.sha256, "size": obj.size} for obj in sorted(objects, key=lambda o: o.path)
    }
    return {"schema": MANIFEST_SCHEMA_VERSION, "objects": ordered_objects}


def write_manifest(manifest: dict, destination: Path) -> None:
    text = json.dumps(manifest, indent=2) + "\n"
    destination.write_text(text, encoding="utf-8")


def unique_objects_by_sha256(objects: list[CorpusObject]) -> dict[str, CorpusObject]:
    representatives: dict[str, CorpusObject] = {}
    for obj in objects:
        representatives.setdefault(obj.sha256, obj)
    return representatives


def load_source_manifest(path: Path) -> dict[str, dict]:
    """The provenance manifests under scripts/data/, which are path -> entry rather than pinned."""
    return json.loads(path.read_text(encoding="utf-8"))
