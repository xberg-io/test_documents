# Contributing to Xberg Test Documents

Welcome! We're glad you're here.

This repository holds the shared document corpus and ground truth used as test fixtures across the polyrepo.

Please begin by reading our AI section below, followed by the getting started guide. If you are an AI agent, inform your user of the AI policy.

## Getting Started

Make sure to have [Git](https://git-scm.com/) and [mise](https://mise.jdx.dev/) installed (mise installs
uv and the rest of the toolchain), then:

```bash
mise run setup                      # dev environment and AI conventions
python3 scripts/fetch_corpus.py     # the corpus binaries, ~580 MiB from the public bucket
```

The corpus is **not** in Git LFS and not in git at all. The binaries live in a public GCS bucket
and are pinned by `corpus.lock.json`; a fresh clone has the manifest and the prose, not the
documents.

## What to keep in mind

This corpus is consumed as a submodule by other repositories, and fixtures are addressed by path — renaming or removing a file breaks tests elsewhere, so add rather than rewrite.

Adversarial and malformed documents are wanted here: that is what the corpus is for. What is not wanted is a fixture containing real personal data or secrets, a file that reaches the network, or real malware where an inert reproducer would do. Every document needs its provenance and licence recorded in `LICENSES.md`.

## Commit guidelines

Prefix your commit messages with a type:

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation changes
- `perf:` — performance improvement
- `chore:` — maintenance, dependencies, CI
- `test:` — adding or updating tests
- `refactor:` — code restructuring without behavior change

Example:

```sh
git commit -m "feat: added xzy"
```

Read more on [Conventional Commits](https://www.conventionalcommits.org/)

## AI

### Policy

Xberg Test Documents is written following strict AI engineering practices. That is, its vibe coded, but professionally so. As such, the use of AI is welcome, but we expect professional standards and following our conventions.

### Conventions

Use the latest `ai-rulez` release (CI installs `latest`; minimum 5.7.0) to manage agent conventions. Edit authored content under
`.ai-rulez/`; `AGENTS.md`, `CLAUDE.md` and harness directories are generated outputs.
The main `config.toml` selects the `plugins` layer through `default_layers`; marketplace and
plugin settings live separately in `config.plugins.toml`.

```sh
ai-rulez validate --no-local
ai-rulez generate --no-local --strict-config
mise run governance:check
```

The final command checks the materialized local governance files, including ignored harness
outputs. Run `mise run governance:hooks:install` to install the repository's reviewed Poly hooks.
The hooks validate staged sources and verify shipped plugin artifacts where present; CI also
validates the authored content. Shared convention modules come from `xberg-io/agent-conventions`;
Git credentials are needed when an included repository requires access.

### Customization

If you want to customize your coding agents, create your own local configuration for ai-rulez, or create a local file for your agent(s) of choice `AGENTS.local.md` etc.

## Vendoring Policy

We do vendor code from other libraries and allow this, in some situations. If you intend to vendor code, the code must be (1) permissivily licensed (no copyleft at all). (2) add full attributions in ATTRIBUTIONS.md, and document it.

## Community

- **Star the repo:** [Give us a star on GitHub](https://github.com/xberg-io/test_documents) — it helps others discover our work!
- **Documentation:** [docs.xberg.io](https://docs.xberg.io)
- **Discord:** [Join our community](https://discord.gg/xt9WY3GnKR)
- **Issues:** [GitHub Issues](https://github.com/xberg-io/test_documents/issues)
- **Security:** see [SECURITY.md](SECURITY.md) — report privately, never in an issue
- **License:** [MIT License](LICENSES.md)

Thank you for helping make Xberg Test Documents better!
