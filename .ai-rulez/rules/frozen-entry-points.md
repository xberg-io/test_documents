---
type: Decision
title: Frozen Entry Points
paths:
  - "scripts/*.py"
  - "scripts/corpus_tools/**"
x-ai-rulez:
  kind: rule
  id: frozen-entry-points
  metadata:
    priority: critical
---

The ten `scripts/*.py` entry points are referenced **by path** from other repositories — most of
all `scripts/fetch_corpus.py`, which appears as a literal string in over a dozen Rust source and test
files in `xberg` plus its agent skill docs, telling developers what to run when a fixture is missing.

- Never rename or move an entry point. Move implementation into `scripts/corpus_tools/` instead and
  leave a thin `main()` behind.
- Consumers pass flags, and those are frozen: `fetch_corpus.py --include '<glob>'` (sceptre's
  `setup` task and `rasterize.py`, xberg's docs; the `fetch-test-documents` action's `include` input
  mirrors its matching), `publish_corpus.py --bucket <name> [--dry-run]` and
  `verify_corpus.py --bucket <name>` (xberg's `test-corpus` skill). Never rename or remove them,
  change how `--include` matches, or change a default. Adding an optional flag is safe.
- Each entry point keeps its own module docstring, because that docstring *is* its `--help`.
- `scripts/tests/test_entry_points.py` runs every entry point's `--help` from a temp directory and
  pins `EXPECTED_ENTRY_POINT_COUNT = 10`; a new entry point updates that constant deliberately.
