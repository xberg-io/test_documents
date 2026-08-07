# xberg PDF→Markdown benchmark corpus

Ground truth for the xberg PDF→Markdown benchmark. **Every document here is reproduced from a pinned
upstream source and gated against an independent text oracle** — see `ground_truth/corpus_manifest.json`
for per-document provenance and verdicts. Do not hand-edit GT; change the builder and re-run.

## Getting the documents

**The binary documents are not in this repository.** Git tracks only text — ground truth, manifests
and scripts. The binaries live in the public bucket `gs://xberg-test-documents`, content-addressed by
sha256 and pinned by `corpus.lock.json`, which maps each path to the object that belongs there.

In CI, use the shared action, which fetches only what a job needs and caches on the manifest:

```yaml
- uses: xberg-io/actions/fetch-test-documents@v1
  with:
    include: |
      pdf/fake_memo.pdf
```

Locally, or anywhere else, read `corpus.lock.json` and fetch over plain HTTPS — the bucket is
world-readable, so no credentials or SDK are involved:

```text
https://storage.googleapis.com/xberg-test-documents/objects/<sha256>
```

`python3 scripts/verify_corpus.py --bucket xberg-test-documents` checks that every pinned object is
still served with the pinned size; add `--sample N` to download some in full and verify their hashes.

### Adding or changing a document

Put the file in its directory (`.gitignore` keeps it out of git), then publish it and commit the
refreshed pin:

```text
python3 scripts/publish_corpus.py --bucket xberg-test-documents
git add corpus.lock.json && git commit
```

This needs write access to the bucket, so CI cannot do it — a CI checkout contains no binaries to
publish. Outside contributors should open a pull request describing the fixture; a maintainer
publishes it. `scripts/corpus-patterns.txt` declares which files count as corpus binaries.

## Reproduce

The corpus builder lives in the **xberg** repository, not here:

```text
python tools/benchmark-harness/scripts/build_corpus.py --stage all
```

This is the ONLY sanctioned way to modify the corpus. It acquires the pinned sources, normalizes GT to
canonical GFM, gates each doc, and writes `pdf/`, `ground_truth/pdf/<stem>.{md,txt}`, the fixtures, and
this file. Re-running with the same pins is deterministic.

## Sources

| dataset | license | GT provenance | role |
|---|---|---|---|
| [lazyc/READoc](https://huggingface.co/datasets/lazyc/READoc) @`HEAD` | MIT | arXiv GT = author LaTeX→pandoc (no tables); GitHub GT = author README rendered to PDF | document |
| [llamaindex/ParseBench](https://huggingface.co/datasets/llamaindex/ParseBench) @`HEAD` | Apache-2.0 | only table.jsonl ships expected_markdown (HTML tables); human-verified | page |
| [bsmock/FinTabNet.c](https://huggingface.co/datasets/bsmock/FinTabNet.c) @`HEAD` | CDLA-Permissive-2.0 | financial-statement table crops; GT = canonicalized cell structure rendered to GFM | page |
| [federalregister.gov](https://www.federalregister.gov) @`2026-07-` | US-PD (17 U.S.C. §105) | OFR/GPO full-text XML → GFM (headings, label blocks, GPOTABLE pipe tables) | document |

Excluded on purpose: **OmniDocBench** (research-only / non-commercial — incompatible with this MIT repo)
and **Nougat** (weights CC-BY-NC; corpus not distributed).

## How the data was modified

Upstream GT is not committed verbatim — it is normalized to canonical GFM so it can be scored
consistently. The transforms are declared once in `scripts/normalize_gt.py` and applied by
`build_corpus.py`; this section and the per-doc `transforms` field in the manifest are generated from
the build ledger, so they always match what actually ran.

| transform | applies to | what it changes |
|---|---|---|
| `math_display` | ReaDoc arXiv | display math \[…\] → $$…$$ |
| `math_inline` | ReaDoc arXiv | inline math \(…\) → $…$ |
| `double_bold` | ReaDoc arXiv | merge pandoc doubled bold ****  (bold-close+bold-open) |
| `trailing_ws` | all sources | strip trailing whitespace |
| `blank_runs` | all sources | collapse >2 blank lines to one |

Applied this build:

- **2577** documents had at least one normalization applied.
- `math_inline`: 231969 substitutions across the corpus.
- `math_display`: 26997 substitutions across the corpus.
- `trailing_ws`: 26990 substitutions across the corpus.
- `double_bold`: 3490 substitutions across the corpus.
- `html_to_gfm`: 503 substitutions across the corpus.

## Layout

- `pdf/<stem>.pdf` — source document.
- `ground_truth/pdf/<stem>.md` — normalized canonical-GFM GT (scored by the harness).
- `ground_truth/pdf/<stem>.txt` — plaintext GT (text-F1).
- `ground_truth/corpus_manifest.json` — immutable manifest: per-doc hashes, source+license+revision,
  transforms, oracle verdict+scores, cohorts, size tier, tune/eval role; one frozen top-level hash.

## Manifest, cohorts, tiers, roles

See the plan and `corpus_manifest.json`. Cohorts tag execution mode (native-clean / native-corrupt-font
/ selective-OCR / forced-OCR) and diagnostic strata (tables, multicolumn, formulas, …). Size tiers
`smoke ⊂ core ⊂ extended` and a `tune`/`eval` role per doc support fast iteration without overfitting.
