---
priority: high
---

# What this repository is

A fixture corpus, not a codebase. Every top-level directory except `scripts/` holds documents that
exist precisely because of their exact bytes — malformed XML, legacy encodings, deliberate typos,
hand-authored whitespace, deliberately unused imports. They are inputs to other repositories' tests,
and their content is the assertion.

## The binaries are not in git

~580 MiB of corpus binaries live in the public GCS bucket `gs://xberg-test-documents`, stored
content-addressed at `objects/<sha256>`. `corpus.lock.json` at the repo root maps every
working-tree path to its sha256 and size. A fresh clone contains the manifest and the prose, not
the documents.

```sh
python3 scripts/fetch_corpus.py                      # everything
python3 scripts/fetch_corpus.py --include 'pdf/**'   # a subset
```

`.gitignore` keeps fetched files untracked, so neither this repo nor a superproject goes dirty
after a fetch. Its pattern list is mirrored in `scripts/data/corpus-patterns.txt`, which is what the
publisher enumerates; `scripts/tests/test_publish_corpus.py` fails if the two drift apart.

## Consumers

This repo is a **git submodule** of `xberg`, `xberg-enterprise` and `sceptre`. CI in those repos
materialises fixtures with the `xberg-io/actions/fetch-test-documents@v1` action, which reads
`corpus.lock.json` with bash and `jq` and fetches with `curl` — it never runs any Python from here.

`corpus.lock.json`'s **exact bytes** are a cross-repo contract: that action hashes the file to key
its object cache. A formatter touching it, or a change to key order, indent, or the trailing
newline, invalidates every consumer's cache at once and changes what the manifest pins.

## Publishing

CI cannot publish. A checkout has no binaries to upload, so publishing is a local maintainer action
that commits a refreshed `corpus.lock.json`. What CI *can* do — and what actually protects
consumers — is prove every pinned object is still fetchable anonymously. That needs no credentials,
which is the point.
