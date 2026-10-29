#!/usr/bin/env bash
#MISE description="Format the tooling sources — scripts/ only, never the corpus"
set -euo pipefail

# ~keep `scripts` passed explicitly rather than `.`, and force-exclude means even an explicit
# corpus path is refused. Belt and braces.
uv run ruff check --fix scripts
uv run ruff format scripts
poly fmt .

# ~keep The tripwire. If any of the above ever reaches outside scripts/, this turns a silently
# corrupted fixture into a visible failure at the moment it happens.
outside=(-- ':!scripts' ':!.ai-rulez' ':!pyproject.toml' ':!poly.toml')
if ! git diff --quiet "${outside[@]}"; then
  echo "ERROR: formatting modified files outside scripts/:" >&2
  git diff --name-only "${outside[@]}" >&2
  exit 1
fi
