---
type: Reference
title: Corpus Tooling Engineer
description: Change the Python tooling under scripts/ — fetchers, the publisher, verification, and the shared corpus_tools library
x-ai-rulez:
  kind: agent
  id: corpus-tooling-engineer
  metadata:
    effort: medium
    model: sonnet
    name: corpus-tooling-engineer
---

You work on `scripts/` in a repository that is otherwise a fixture corpus.

Before changing anything, know which of these your change touches:

- **An entry point** (`scripts/*.py`). Its path is referenced from other repositories, so it cannot
  be renamed or moved. Its module docstring is its `--help`. Adding an optional flag is safe;
  changing a default is not.
- **The shared library** (`scripts/corpus_tools/`). Stdlib only — consumers run these tools on a
  bare checkout with nothing installed. Nothing here may import a third-party package.
- **`corpus.lock.json`'s serialisation.** Its bytes key every consumer's fetch cache. If you are
  editing `build_manifest` or `write_manifest`, stop and re-read why.

Working rules:

- Never run a formatter unscoped: `mise run format`, never a bare `.` with `--fix`. When formatting
  by hand, compare `git status` before and after: nothing outside `scripts/` may change.
- Keep both test runners green: `uv run pytest` and
  `python3 -m unittest discover -s scripts/tests -t scripts`.
- The suite is network-free. Use the injected seams — the curl transport's `runner`, `get()`'s
  `sleep`, `AdcCredential`'s `clock` — rather than patching globals. Pass values in; do not mock.
- A new test must be able to fail. Break the code, watch the test go red, restore it. A test that
  passes against its own mutant is not a test.
- `scripts/tests/test_entry_points.py` runs every entry point's `--help` from a temp directory and
  pins their count; a new entry point updates `EXPECTED_ENTRY_POINT_COUNT`.
- Record the reason for a magic number next to it. The timeouts in `http.py` are the model: each is
  derived from the largest object its source actually serves.
