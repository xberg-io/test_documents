---
priority: critical
---

# Fixture bytes are load-bearing

Never reformat, "fix", or normalise anything outside `scripts/`. A corpus document's exact bytes
are what it tests: malformed XML that must stay malformed, a legacy encoding whose declaration must stay
wrong, a Python fixture whose unused imports are the entire point of the fixture.

The damage is silent — the file still parses, the tests that read it still pass, and the corpus now
disagrees with the ground truth describing it.

- Run formatters scoped: `uv run ruff format scripts`, never a bare `.` with `--fix`.
- `poly.toml` and `pyproject.toml` both exclude every corpus directory, and
  `[tool.ruff] force-exclude = true` is what stops an explicitly-named path from bypassing that.
  `scripts/tests/test_lint_scope.py` asserts this behaviourally against the real binary and checks
  the two exclude lists still agree.
- Adding a top-level corpus directory means adding it to **both** files. The sync test will tell
  you if you forget.
- After any formatting run, `git status --porcelain -- . ':!scripts'` must be empty.
