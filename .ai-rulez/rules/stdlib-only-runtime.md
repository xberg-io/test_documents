---
type: Decision
title: Stdlib Only Runtime
paths:
  - "scripts/**"
  - "pyproject.toml"
x-ai-rulez:
  kind: rule
  id: stdlib-only-runtime
  metadata:
    priority: critical
---

Consumers run `python3 scripts/fetch_corpus.py` against a bare checkout with nothing installed,
often from a sibling repository where this is a submodule. The CI job that proves the manifest still
resolves deliberately uses the runner's own `python3` with no setup step and no install — it is the
executable proof that a consumer with a stock interpreter can materialise this corpus.

- Nothing under `scripts/`, tests included, imports a third-party package at module level: the
  stdlib runner imports every test module. The one exception is the guarded `tomli` fallback for
  3.10 in `test_lint_scope.py`. Dev tools (pytest, ruff, pyrefly) are invoked, never imported.
- `import corpus_tools` resolves because CPython puts the `__main__` script's directory on
  `sys.path[0]`. Do not add `__init__.py` to `scripts/`, and do not name a module there after a
  stdlib module — `scripts/` is on the path and would shadow it.
- The floor is Python 3.10, declared in `pyproject.toml` and exercised in CI.
