---
type: Decision
title: Python Conventions
paths:
  - "scripts/**"
  - "pyproject.toml"
x-ai-rulez:
  kind: rule
  id: python
  metadata:
    priority: high
---

- Python 3.10+, type hints on public APIs, no `Any` where a precise type, generic or `Protocol` fits.
- Ruff for lint and format; Pyrefly (`pyrefly check`) is the only type checker. Do not add mypy, pyright or their config.
- Tests are `unittest.TestCase` classes under `scripts/tests/`, run by `uv run pytest` and the zero-install
  `python3 -m unittest discover -s scripts/tests -t scripts`; never convert them to function-based tests.
- `uv` with the committed `uv.lock`.
- Specific exceptions only, never a bare `except:`; `pathlib.Path` over `os.path`; dataclasses for known schemas (the tools are stdlib-only: `stdlib-only-runtime` rule).
