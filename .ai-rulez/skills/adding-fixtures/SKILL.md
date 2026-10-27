---
type: Playbook
title: Adding Fixtures
description: "Add or replace a corpus fixture: licence and attribution records, patterns/.gitignore sync, lint excludes, local publish, lock commit, submodule push order. Use when adding or replacing corpus documents."
paths:
  - "LICENSES.md"
  - "ATTRIBUTIONS.md"
  - "*_PROVENANCE.md"
  - "corpus.lock.json"
  - "scripts/data/corpus-patterns.txt"
  - ".gitignore"
  - "ground_truth/**"
x-ai-rulez:
  kind: skill
  id: adding-fixtures
  metadata:
    name: adding-fixtures
---

# Adding or replacing a fixture

- **Add rather than rewrite.** Other repositories' tests address fixtures by path. Never reformat an
  existing fixture: malformed XML, legacy encodings, deliberate typos and hand-authored whitespace are
  what it tests.
- **Provenance and licence** go in `LICENSES.md`, attribution in `ATTRIBUTIONS.md` where the source
  requires it. No real personal data or secrets, nothing that reaches the network, no live malware
  where an inert reproducer would do. Adversarial and malformed documents are wanted.
- **Never `git add` a corpus binary.** It belongs in the bucket; the publisher refuses to run if one
  is tracked.
- A new extension goes into `scripts/data/corpus-patterns.txt` **and** `.gitignore` with identical
  text (`PatternSyncTests` in `scripts/tests/test_publish_corpus.py`). A new top-level corpus
  directory goes into the excludes of both `poly.toml` and `pyproject.toml`; `test_lint_scope.py`
  checks they agree, but cannot see a directory that has no tracked files.
- Ground truth lives under `ground_truth/`. When a fixture and its answer key can disagree, add the
  check that catches it; `scripts/tests/test_diagram_manifest.py` is the model.

## Publishing

Local, never CI, and from a fully fetched tree: the publisher refuses to unpin lock entries missing
from the working tree (`--allow-removals` only for a deliberate removal).

```sh
python3 scripts/publish_corpus.py --bucket xberg-test-documents --dry-run
python3 scripts/publish_corpus.py --bucket xberg-test-documents
python3 scripts/verify_corpus.py --bucket xberg-test-documents
```

Commit the refreshed `corpus.lock.json`, and push the submodule commit before any superproject
gitlink that references it.
