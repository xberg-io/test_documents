---
type: Decision
title: Fixture Bytes Are Load Bearing
x-ai-rulez:
  kind: rule
  id: fixture-bytes-are-load-bearing
  metadata:
    priority: critical
---

Never reformat, "fix" or normalise anything outside `scripts/`: a corpus document's exact bytes are what it
tests, and the damage is silent (the file still parses, the corpus now disagrees with its ground truth).

- Run formatters scoped (`uv run ruff format scripts`), never a bare `.` with `--fix`.
- A new top-level corpus directory goes into the excludes of **both** `poly.toml` and `pyproject.toml`;
  `scripts/tests/test_lint_scope.py` checks they agree.
- After any formatting run, `git status --porcelain -- . ':!scripts'` must be empty.
