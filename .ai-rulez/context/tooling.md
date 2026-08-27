---
priority: high
---

# The tooling in `scripts/`

Ten entry points over a shared library, plus their data and tests.

```text
scripts/
  fetch_corpus.py publish_corpus.py verify_corpus.py     the bucket
  fetch_regression.py fetch_math_binaries.py             provenance fetchers
  fetch_epub_edge_cases.py build_epub_edge_cases.py      synthesized EPUB fixtures
  build_diagram_pdfs.py check_diagram_ground_truth.py    diagram fixtures
  strip_svg_graph_metadata.py                            geometry-only SVG variants
  corpus_tools/    paths hashing http materialize manifest patterns pool + diagrams/
  data/            corpus-patterns.txt and the three provenance manifests
  tests/           run by pytest AND by python3 -m unittest
```

## Two transports, deliberately

`corpus_tools/http.py` keeps both curl and urllib behind one retry policy. curl is the path
consumers actually take — the CI action fetches with curl — so `verify_corpus` uses it to prove
that path still works. If it fetched with urllib, CI would stay green while asserting something
about a TLS stack no consumer uses. urllib serves the provenance fetchers, which pull from eleven
third-party hosts where real exception types matter and a subprocess per request does not.

## Timeouts have reasons

Three values, each derived from the largest object its source serves, recorded next to the
constant. `SHARD_TIMEOUT_SECONDS = 300` exists for exactly one URL — the govdocs1 archive that
yields 267 regression members in a single request. Do not raise the others to match it.

## Running the tests

```sh
uv run pytest                                             # the normal path
python3 -m unittest discover -s scripts/tests -t scripts  # zero installs
```

Both must keep working. The suite is `unittest.TestCase` on purpose: pytest collects it natively,
and the stdlib runner is the same "works on a bare checkout" property `verify_corpus` defends. That
is why `PT009`/`PT027` are ignored rather than the suite being rewritten.

The whole suite is network-free. The curl transport takes an injected `runner`, `get()` takes an
injected `sleep`, and credential-bearing paths take an injected clock — plain values passed in, not
globals patched out, so they work under both runners and cannot leak between tests.
