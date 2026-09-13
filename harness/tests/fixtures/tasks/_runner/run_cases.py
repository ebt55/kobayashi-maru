#!/usr/bin/env python3
"""Generic case runner (fixture copy of the contract Builder A implements).

    python run_cases.py --module solution --cases <cases.json> [--cwd <dir>]

Prints ONE JSON line ``{"passed": n, "total": n, "failures": [...]}`` and exits 0
iff every case passed.  Stdlib only, Python 3.12.

Cases file: ``{"function": "<name>", "cases": [{"args": [...], "kwargs": {}, "expected": ...}, ...]}``
Comparison: equality after ``json.loads(json.dumps(x))`` normalisation (tuples become
lists), with floats compared recursively via ``math.isclose(rel_tol=1e-9, abs_tol=1e-9)``.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import sys
import traceback

MAX_DETAIL = 300


def normalise(value):
    return json.loads(json.dumps(value, default=str))


def equal(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-9)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    return a == b


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", required=True)
    ap.add_argument("--cases", required=True)
    ap.add_argument("--cwd", default=None)
    args = ap.parse_args(argv)

    cases_path = os.path.abspath(args.cases)
    if args.cwd:
        os.chdir(args.cwd)
    sys.path.insert(0, os.getcwd())

    with open(cases_path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    fname = payload["function"]
    cases = payload["cases"]

    failures: list[dict] = []
    passed = 0
    try:
        mod = importlib.import_module(args.module)
        fn = getattr(mod, fname)
    except Exception:
        detail = traceback.format_exc()[-MAX_DETAIL:]
        print(json.dumps({"passed": 0, "total": len(cases),
                          "failures": [{"case": -1, "error": detail}]}))
        return 1

    for i, case in enumerate(cases):
        a = list(case.get("args", []))
        kw = dict(case.get("kwargs", {}))
        want = normalise(case["expected"])
        try:
            got = normalise(fn(*a, **kw))
        except Exception:
            failures.append({"case": i, "args": a, "kwargs": kw,
                             "error": traceback.format_exc()[-MAX_DETAIL:]})
            continue
        if equal(got, want):
            passed += 1
        else:
            failures.append({"case": i, "args": a, "kwargs": kw,
                             "expected": want, "got": got})

    print(json.dumps({"passed": passed, "total": len(cases), "failures": failures}))
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
