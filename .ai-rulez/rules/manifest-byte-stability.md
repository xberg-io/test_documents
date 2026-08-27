---
priority: critical
---

# corpus.lock.json's bytes are the contract

`xberg-io/actions/fetch-test-documents` hashes this file to key its object cache. Two lines decide
its bytes: the `sorted(..., key=lambda o: o.path)` in `build_manifest` and the
`json.dumps(manifest, indent=2) + "\n"` in `write_manifest`.

- Never let a formatter near it — `poly.toml` excludes it explicitly.
- Never change key order, indent, or the trailing newline. Doing so invalidates every consumer's
  cache at once and changes what the manifest pins.
- `scripts/tests/test_manifest.py` round-trips the committed file byte for byte with no network and
  no corpus binaries. That test is the only thing exercising the write path, because `--dry-run`
  deliberately never writes and CI cannot publish at all.
- After a real publish, `git diff corpus.lock.json` should show only intended pin changes.
