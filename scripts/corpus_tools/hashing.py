"""One sha256 implementation.

~keep There were three: two identical chunked readers in fetch_corpus and publish_corpus, each
carrying its own READ_CHUNK_SIZE, and a whole-file `hashlib.sha256(path.read_bytes())` in
build_diagram_pdfs. The digests agreed, so nothing ever caught the difference — but the corpus
contains a 62 MiB object, and slurping is a peak-memory cost paid for no reason. Chunked wins.
"""

import hashlib
from pathlib import Path

READ_CHUNK_SIZE = 1024 * 1024
BYTES_PER_MIB = 1024 * 1024


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(READ_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()
