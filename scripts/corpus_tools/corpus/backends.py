"""Where published objects actually go.

~keep LocalDirBackend exists so the publisher's upload path can be tested without a bucket or
credentials. It is a test double that lives in production code on purpose: the Protocol is the
seam, and having a second real implementation is what keeps that seam honest.
"""

import base64
import hashlib
import subprocess
from pathlib import Path
from typing import Protocol

# ~keep Bounds the argv of a single `gcloud storage cp`; gcloud parallelises within one invocation.
UPLOAD_BATCH_SIZE = 250


class StorageBackend(Protocol):
    def existing_keys(self, prefix: str) -> set[str]: ...

    def matches_remote(self, local_path: Path, key: str) -> bool: ...

    def upload(self, local_path: Path, key: str) -> None: ...

    def upload_directory(self, local_directory: Path, key_prefix: str) -> None: ...

    def read_text(self, key: str) -> str | None: ...


class GCloudStorageBackend:
    """Shells out to `gcloud storage`; avoids a hard dependency on google-cloud-storage."""

    def __init__(self, bucket: str) -> None:
        self.bucket = bucket

    def _uri(self, key: str) -> str:
        return f"gs://{self.bucket}/{key}"

    def existing_keys(self, prefix: str) -> set[str]:
        # ~keep One listing for the whole prefix rather than `objects describe` per object: each
        # gcloud invocation costs ~1.5s of interpreter startup, which dominated the 489-object
        # publish far more than the 570 MiB of actual transfer did.
        result = subprocess.run(
            ["gcloud", "storage", "ls", f"{self._uri(prefix)}/**"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return set()
        bucket_uri = f"gs://{self.bucket}/"
        return {line[len(bucket_uri) :] for line in result.stdout.split() if line.startswith(bucket_uri)}

    def matches_remote(self, local_path: Path, key: str) -> bool:
        """Compare by GCS's own md5, so an unchanged file is never rewritten."""
        result = subprocess.run(
            ["gcloud", "storage", "objects", "describe", self._uri(key), "--format=value(md5_hash)"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return False
        remote_md5 = result.stdout.strip()
        if not remote_md5:
            return False
        digest = hashlib.md5(local_path.read_bytes(), usedforsecurity=False).digest()
        local_md5 = base64.b64encode(digest).decode()
        return remote_md5 == local_md5

    def upload(self, local_path: Path, key: str) -> None:
        subprocess.run(["gcloud", "storage", "cp", str(local_path), self._uri(key)], check=True)

    def upload_directory(self, local_directory: Path, key_prefix: str) -> None:
        # ~keep Explicit source list, never `cp --recursive <dir>`: recursive copy appends the source
        # directory's own name to the destination, so the objects would land under
        # objects/<staging-dir-name>/<sha256>. Naming each file puts it at objects/<sha256>.
        sources = sorted(local_directory.iterdir())
        for start in range(0, len(sources), UPLOAD_BATCH_SIZE):
            batch = sources[start : start + UPLOAD_BATCH_SIZE]
            subprocess.run(
                ["gcloud", "storage", "cp", *(str(path) for path in batch), f"{self._uri(key_prefix)}/"],
                check=True,
            )

    def read_text(self, key: str) -> str | None:
        result = subprocess.run(
            ["gcloud", "storage", "cat", self._uri(key)],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout if result.returncode == 0 else None


class LocalDirBackend:
    """Copies into a local directory tree; a fake bucket for tests, never a real endpoint."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def matches_remote(self, local_path: Path, key: str) -> bool:
        destination = self.root / key
        return destination.is_file() and destination.read_bytes() == local_path.read_bytes()

    def existing_keys(self, prefix: str) -> set[str]:
        base = self.root / prefix
        if not base.is_dir():
            return set()
        return {str(path.relative_to(self.root)) for path in base.rglob("*") if path.is_file()}

    def upload(self, local_path: Path, key: str) -> None:
        destination = self.root / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(local_path.read_bytes())

    def upload_directory(self, local_directory: Path, key_prefix: str) -> None:
        for source in sorted(local_directory.iterdir()):
            self.upload(source, f"{key_prefix}/{source.name}")

    def read_text(self, key: str) -> str | None:
        destination = self.root / key
        return destination.read_text() if destination.is_file() else None
