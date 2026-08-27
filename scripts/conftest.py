"""Put scripts/ on sys.path so the tests import the tooling the way the entry points do.

~keep `python3 scripts/fetch_corpus.py` gets scripts/ on sys.path[0] for free, because CPython
puts the __main__ script's directory there. pytest does not run the entry points, so it needs
this. With scripts/tests/__init__.py present and no scripts/__init__.py, pytest's own rootdir
walk already lands on scripts/ — this is the belt to that braces, and it is also what keeps
`--import-mode=importlib` working, where the automatic insertion does not happen.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
