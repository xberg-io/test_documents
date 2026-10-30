---
type: Concept
title: Area Map
x-ai-rulez:
  kind: context
  id: area-map
  metadata:
    priority: high
---

A fixture corpus, not a codebase, and a git submodule of several xberg-io repositories. Every top-level
directory except `scripts/` holds documents whose exact bytes are the assertion. The ~610 MiB of binaries are not in
git: they live content-addressed at `objects/<sha256>` in the public bucket `gs://xberg-test-documents`, and
`corpus.lock.json` pins every working-tree path to its sha256 and size. Fetch with
`python3 scripts/fetch_corpus.py [--include 'pdf/**']`; fetched files stay untracked.

- `<format>/` (`pdf_scanned/`, `office/`, `html/`, ...) — corpus documents (`corpus-curator` agent)
- `ground_truth/` — expected outputs per format
- `corpus.lock.json` — the manifest; its bytes key consumers' caches (`manifest-byte-stability` rule)
- `scripts/` — the stdlib-only fetch/publish/verify tools (`corpus-tooling` skill; private corpora: `private-corpus`)
- `*.md` at the root — licensing, attribution and provenance records

Tasks: `mise run check` (everything CI runs except the bucket check), `mise run format` (`scripts/` only;
fails on any unstaged change outside `scripts/`, `.ai-rulez/` and the lint config). The bucket check is
`python3 scripts/verify_corpus.py --bucket xberg-test-documents` (network), as verify-corpus.yaml runs it.

CI cannot publish: publishing is a local maintainer action that commits a refreshed `corpus.lock.json`. CI proves every
pinned object is still fetchable anonymously. Consumer CI fetches through `xberg-io/actions/fetch-test-documents@v1`,
which runs no Python from here; developers in consumer repos run `python3 test_documents/scripts/fetch_corpus.py`.
