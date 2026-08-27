"""Shared implementation behind the corpus tools in scripts/.

~keep Two constraints make this package work, and both are easy to break by accident.

Stdlib only, no install step. Consumers run `python3 scripts/fetch_corpus.py` against a bare
checkout with nothing installed — several of them from a sibling repo, where this directory is a
git submodule. CPython puts the __main__ script's directory on sys.path[0], which is the whole
reason `import corpus_tools` resolves there. Adding a third-party import to this package breaks
every one of those callers. (The one way the sys.path[0] trick does not apply is
PYTHONSAFEPATH=1 / `python3 -P` / `-I`, which suppress it. Do not paper over that with a
copy-pasted bootstrap in ten entry points; run the tools normally.)

Do not name a module in scripts/ after a stdlib module. scripts/ is on sys.path, so a file there
shadows the real one for every tool. Inside this package it is safe — `corpus_tools/http.py` does
not shadow stdlib `http`, because Python 3 imports are absolute.
"""
