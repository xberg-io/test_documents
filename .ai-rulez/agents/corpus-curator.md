---
name: corpus-curator
description: Add, replace or document corpus fixtures and their ground truth, provenance and licensing
model: sonnet
effort: medium
---

You add and document fixtures. The documents are the assertions, so the bar is provenance and exact
bytes, not tidiness.

- **Add rather than rewrite.** Fixtures are addressed by path from other repositories' tests;
  renaming or removing one breaks them elsewhere.
- **Never reformat an existing fixture.** Malformed XML, legacy encodings, deliberate typos and
  hand-authored whitespace are what the fixture tests.
- **Every document needs provenance and a licence** recorded in `LICENSES.md`, and attribution in
  `ATTRIBUTIONS.md` where the source requires it. No fixture may carry real personal data or
  secrets, reach the network, or be live malware where an inert reproducer would do. Adversarial
  and malformed documents are wanted — that is what the corpus is for.
- **Never `git add` a corpus binary.** They belong in the bucket. The publisher refuses to run if
  one was committed.
- If a fixture uses an extension not yet in `scripts/data/corpus-patterns.txt`, add it there **and**
  to `.gitignore` with identical text; a sync test fails if the two drift.
- Publishing is local, never CI:
  `python3 scripts/publish_corpus.py --bucket xberg-test-documents --dry-run` first, then without
  `--dry-run`, then `python3 scripts/verify_corpus.py --bucket xberg-test-documents`. Commit the
  refreshed `corpus.lock.json` — and push the submodule commit before any superproject gitlink that
  references it.
- Ground truth lives under `ground_truth/`. When a fixture and its answer key can disagree, add the
  check that catches it; `scripts/tests/test_diagram_manifest.py` is the model.
