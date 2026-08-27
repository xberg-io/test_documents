---
priority: critical
---

# The tools import nothing but the standard library

Consumers run `python3 scripts/fetch_corpus.py` against a bare checkout with nothing installed,
often from a sibling repository where this is a submodule. The CI job that proves the manifest still
resolves deliberately uses the runner's own `python3` with no setup step and no install — it is the
executable proof that a consumer with a stock interpreter can materialise this corpus.

- Nothing under `scripts/` outside `scripts/tests/` may import a third-party package.
- Dev tooling (pytest, ruff) and the pyrefly type-checker are fine: it is never imported by the tools.
- `import corpus_tools` resolves because CPython puts the `__main__` script's directory on
  `sys.path[0]`. Do not add `__init__.py` to `scripts/`, and do not name a module there after a
  stdlib module — `scripts/` is on the path and would shadow it.
- The floor is Python 3.10, declared in `pyproject.toml` and exercised in CI.
