#!/usr/bin/env python3
"""Snapshot walk of a sandbox work dir (SPEC.md section 3, "Snapshot walk").

Covered set: every file under ``tests/`` and ``.grader/``, plus ``conftest.py``,
``pytest.ini``, ``pyproject.toml`` (if present), ``run_tests.sh`` and ``solution.py``.
Paths are POSIX-relative to the work dir.

Prints one JSON object:
    {"hashes": {relpath: sha256}, "contents": {relpath: text (<=20000 chars) | "<binary>"}}

Usage:  python /opt/dc/snapshot.py [workdir]      (default: cwd)

Stdlib only; baked into the image so the agent's container never needs network.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

MAX_CHARS = 20000
DIRS = ("tests", ".grader")
TOP_FILES = ("conftest.py", "pytest.ini", "pyproject.toml", "run_tests.sh", "solution.py")


def _walk(root: str) -> list[str]:
    found: list[str] = []
    for d in DIRS:
        base = os.path.join(root, d)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(n for n in dirnames if n != "__pycache__")
            for name in sorted(filenames):
                if name.endswith(".pyc"):
                    continue
                full = os.path.join(dirpath, name)
                found.append(os.path.relpath(full, root).replace(os.sep, "/"))
    for name in TOP_FILES:
        full = os.path.join(root, name)
        if os.path.isfile(full):
            found.append(name)
    return sorted(set(found))


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    hashes: dict[str, str] = {}
    contents: dict[str, str] = {}
    for rel in _walk(root):
        full = os.path.join(root, rel.replace("/", os.sep))
        try:
            with open(full, "rb") as fh:
                raw = fh.read()
        except OSError as exc:  # unreadable -> record the fact, keep going
            hashes[rel] = "<unreadable>"
            contents[rel] = "<unreadable: %s>" % exc.__class__.__name__
            continue
        hashes[rel] = hashlib.sha256(raw).hexdigest()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            contents[rel] = "<binary>"
            continue
        contents[rel] = text[:MAX_CHARS]
    json.dump({"hashes": hashes, "contents": contents}, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
