---
priority: critical
---

# Entry-point paths are a cross-repo API

The ten `scripts/*.py` entry points are referenced **by path** from other repositories — most of
all `scripts/fetch_corpus.py`, which appears as a literal string in around fourteen Rust source and
test files in `xberg` plus its agent skill docs, telling developers what to run when a fixture is
missing.

- Never rename or move an entry point. Move implementation into `scripts/corpus_tools/` instead and
  leave a thin `main()` behind.
- Adding an optional flag is safe: no consumer passes flags. Changing a default is not.
- Each entry point keeps its own module docstring, because that docstring *is* its `--help`.
- Verify with a smoke test from a foreign directory on a bare interpreter:
  `cd /tmp && python3 <abs>/scripts/<tool>.py --help`. This repo's CI runs only `verify_corpus.py`,
  so nothing else catches an import that breaks the other nine.
