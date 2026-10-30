# Reference-only benchmark upstreams

`scripts/data/benchmark-upstreams.json` records immutable source URLs, SHA-256, size, and identity
for 1,493 upstream files. It contains no PDF, HTML oracle, raw test, or derived ground-truth content.
It is a separate acquisition descriptor, not `corpus.lock.json` or a change to the curated corpus.

| Namespace | Dataset revision | PDFs | Original JSONL files | Raw rows |
|---|---|---:|---:|---:|
| `parsebench-tables` | `llamaindex/ParseBench@2805a1d940f95a203e0ae4b88be9934f7765b3fc` | 503 | 1 | 503 |
| `olmocr-issue2331` | `allenai/olmOCR-bench@54a96a6fb6a2bd3b297e59869491db4d3625b711` | 984 | 5 | 5,113 |

The associated evaluator pins are `run-llama/ParseBench@328c71109e0b955f66583c33ec95ac52d9749db4`
and `allenai/olmocr@f7cfe4c22098b154c76b6ec950d1c0a464eecf8d`. Acquisition does not execute them,
normalize their oracles, inject baseline tests, or score extraction.

## Rights and attribution

[ParseBench](https://huggingface.co/datasets/llamaindex/ParseBench/tree/2805a1d940f95a203e0ae4b88be9934f7765b3fc)
annotations are Apache-2.0. That is not treated as a redistribution grant for its third-party PDFs.

The [pinned olmOCR dataset card](https://huggingface.co/datasets/allenai/olmOCR-bench/blob/54a96a6fb6a2bd3b297e59869491db4d3625b711/README.md)
states ODC-BY-1.0. [Section 2.4 of that database license](https://opendatacommons.org/licenses/by/1-0/)
excludes copyright over individual contents. The dataset combines arXiv papers, Internet Archive
material, Library of Congress scans, and internally sourced documents. Repository hosting, age,
and source categories alone do not establish per-file rights. No public-domain subset is declared
without a documented grant or public-domain determination for each file.

All indexed assets therefore remain `reference/unreviewed`, with `redistribution=reference-only`.
Nothing here authorizes publishing PDFs, raw tests, or derived content to Git or the public bucket.
Database attribution is to Allen Institute for AI / olmOCR-bench; annotation attribution is to the
ParseBench authors, with source links above. See [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

## Acquisition

Python 3.10+ and the standard library suffice. All URLs contain the immutable dataset revision;
the existing corpus HTTP transport, retries, hashing, safe relative paths, and materialization
helpers are reused. Existing correct files are verified and skipped without network access.
Mismatched upstream bytes never replace a local file; the existing `.mismatch` evidence behavior
is retained. The default cache is `~/.cache/xberg/reference-benchmarks`.

```sh
python3 scripts/fetch_benchmark_upstreams.py --source parsebench-tables
python3 scripts/fetch_benchmark_upstreams.py --source olmocr-issue2331 --root /external/cache
python3 scripts/fetch_benchmark_upstreams.py --source olmocr-issue2331 --root /external/cache --verify-only
```

Omit `--source` to acquire both sets; repeat it to select sources explicitly. `--jobs` controls
parallel transfers. A missing/corrupt file in `--verify-only` mode causes a nonzero exit, with no
network access. The tool rejects a cache within any Git working tree, including its own checkout.
It never uploads or modifies the bucket lock. An empty or incomplete inventory cannot pass.

Files retain original upstream paths below the namespace:

```text
<cache>/parsebench-tables/table.jsonl
<cache>/parsebench-tables/docs/table/<upstream filename>.pdf
<cache>/olmocr-issue2331/bench_data/<group>.jsonl
<cache>/olmocr-issue2331/bench_data/pdfs/<group>/<upstream filename>.pdf
```

The five olmOCR groups are `arxiv_math` (522 PDFs / 2,927 rows), `old_scans_math` (36 / 458),
`old_scans` (98 / 526), `long_tiny_text` (62 / 442), and `headers_footers` (266 / 760).
The last group includes seven explicit baseline rows; those remain raw upstream data, not seven
extra PDFs or a separate category. The full upstream benchmark also includes other groups; this
index covers only the five listed groups. The original JSONL files and PDFs are fetched byte-for-byte.

## Descriptor and regeneration

The isolated format is `format="xberg-benchmark-upstreams", schema_version=1`. `sources` contains
the dataset/evaluator identities and revisions, expected file/group counts, annotation/database
license scope, and reference-only policy. `objects` maps the namespaced relative path to
`sha256`, `size`, exact `url`, `source`, `kind` (`pdf`/`jsonl`), original `upstream_path`, `group`,
opaque PDF `id` (null for JSONL), and `content_rights`. Consumers can read these pins directly;
they need not copy a machine-specific stage manifest or duplicate download logic.

The inventory is generated, not hand-edited. A maintainer with the verified external stage roots
can reproduce it without downloads or inference:

```sh
python3 scripts/fetch_benchmark_upstreams.py --build-from-stages /external/parsebench-stage /external/olmocr-stage
```

The generator verifies fixed source/evaluator revisions, independently hash-pinned Hugging Face
tree metadata, original Git-blob or LFS hashes, SHA-256/size of every staged file, JSONL row counts,
complete group counts, and unique identities. ParseBench's table JSONL SHA-256 is
`66129fcc9e68ae0bf40e7d41f540002ceff9bedf46d6dafff2321ba2b7ab5231`.
Only metadata fields enter the generated descriptor. Regenerating with unchanged source bytes
produces identical inventory bytes. A new revision requires an explicit reviewed update to the
source/proof pins and regenerated inventory; acquisition never follows a mutable `main` branch.

Network-free controls run with either repository test runner:

```sh
python3 -m unittest discover -s scripts/tests -t scripts -p test_benchmark_upstreams.py -v
```
