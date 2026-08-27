---
priority: high
---

# Serving a second, private corpus

The same tooling serves corpora whose index lives outside this repository. `fetch_corpus.py` takes
`--manifest`, `--root` and `--auth`; `publish_corpus.py` takes `--manifest`, `--root` and
`--patterns`. Every one defaults to this repository's value, so the public commands are unchanged.

Convention for a private set, kept in a private repo:

```text
<private-repo>/internal_test_documents/<namespace>/corpus.lock.json   committed
<private-repo>/internal_test_documents/<namespace>/data/…             gitignored, materialised
```

Objects are content-addressed, so several manifests can describe subsets of one bucket at no extra
storage cost — a small curated manifest for CI (GitHub's per-repo Actions cache is 10 GB) and a full
one for local runs. Nothing may assume one manifest per bucket.

## Authentication

`--auth` is opt-in; anonymous is the default and must stay that way, because the credential-free
fetch is exactly what this repo's CI proves. `AdcCredential` shells out to
`gcloud auth print-access-token` rather than importing `google.auth`, since the package is
stdlib-only and workload-identity federation in CI populates ADC the same way a local login does.
It re-acquires as the token ages: WIF tokens last an hour and cannot be extended, and a large fetch
on a slow runner can outlive one.

## Why an anchored pattern beats an extension list

A private corpus should use a single anchored pattern such as `data/*` rather than enumerating
extensions. An extension list silently under-publishes whatever it forgot — publish exits 0 having
examined most of the tree — and the files it misses are disproportionately the interesting ones.
`data/*` cannot under-publish, and it keeps the corpus's own README, checksum file and CSV manifest
out of the bucket, where they do not belong: prose stays in git, bytes go to the bucket.

Always cross-check the generated manifest against the corpus's own checksum file and **report the
number of hashes compared**. A run comparing zero files and one comparing all of them both exit 0.
