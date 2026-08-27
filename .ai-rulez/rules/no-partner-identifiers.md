---
priority: critical
---

# This repository is public

`xberg-io/test_documents` is a public repository, and the tooling here also serves private corpora
belonging to design partners whose filenames identify them and name their documents.

Nothing identifying a private corpus may land here — not in code, tests, fixtures, docstrings,
comments, commit messages, PR descriptions, or documentation. Use neutral placeholders throughout:
`<namespace>`, `internal-corpus`, `acme/foo.pdf`.

Private manifests, pattern files and sample documents belong in the private repository that owns
them. This repository supplies only the mechanism.

Before committing work that touched the private path, grep for the partner's identifiers and
confirm the result is empty.
