#!/usr/bin/env python3
"""Generic case runner (SPEC.md Sec 1).

Used by the host-side validator and by the harness's fresh re-grade inside a
Linux container (Python 3.12, stdlib only -- do NOT add third-party imports).

    python run_cases.py --module solution --cases <path/to/cases.json> [--cwd <dir>]

Reads a cases file of the shape

    {"function": "<name>", "cases": [{"args": [...], "kwargs": {...}, "expected": ...}, ...]}

imports <module> from --cwd (default: the current directory, inserted at
sys.path[0]), calls the function once per case, and compares the returned value
with `expected` using the SPEC Sec 1 normalisation: both sides are put through a
json round-trip (so tuples become lists) and then compared recursively, with
floats compared by math.isclose(rel_tol=1e-9, abs_tol=1e-9).

An exception raised by a case counts as a failure for that case only.

Prints exactly one JSON line to stdout:

    {"passed": n, "total": n, "failures": [{"index": i, "args": ..., "kwargs": ...,
                                            "expected": "<repr>", "got": "<repr>|EXC: ..."}]}

Exit code 0 if every case passed, else 1.

There is no per-case timeout: the task functions are tiny and pure. Protection
against a pathological infinite loop in a submitted solution is the caller's
job -- the harness wraps this whole process in an external timeout (and the
container is run with --network none), which is also why no signal handling is
used here (it must work identically on Windows and Linux).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

MAX_REPR = 300


def normalise(value):
    """SPEC Sec 1 normalisation: json round-trip (tuples -> lists)."""
    return json.loads(json.dumps(value))


def values_equal(a, b):
    """Recursive comparison; floats via math.isclose(rel_tol=1e-9, abs_tol=1e-9)."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-9)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(values_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a.keys()) == set(b.keys()) and all(values_equal(a[k], b[k]) for k in a)
    if type(a) is not type(b):
        return False
    return a == b


def compare(got, expected):
    """Compare a returned value against an expected value after normalisation."""
    try:
        got_n = normalise(got)
    except (TypeError, ValueError):
        return False
    return values_equal(got_n, normalise(expected))


def clip(text):
    text = str(text)
    return text if len(text) <= MAX_REPR else text[:MAX_REPR]


def run(module_name, cases_path, cwd):
    with open(cases_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    function_name = data["function"]
    cases = data["cases"]

    work_dir = os.path.abspath(cwd)
    if sys.path and sys.path[0] == work_dir:
        pass
    else:
        sys.path.insert(0, work_dir)

    failures = []
    try:
        module = __import__(module_name)
        func = getattr(module, function_name)
    except Exception as exc:  # import or attribute failure: every case fails
        detail = "EXC: {}: {}".format(type(exc).__name__, exc)
        for index, case in enumerate(cases):
            failures.append(
                {
                    "index": index,
                    "args": case.get("args", []),
                    "kwargs": case.get("kwargs", {}),
                    "expected": clip(repr(case.get("expected"))),
                    "got": clip(detail),
                }
            )
        return {"passed": 0, "total": len(cases), "failures": failures}

    passed = 0
    for index, case in enumerate(cases):
        args = case.get("args", [])
        kwargs = case.get("kwargs", {}) or {}
        expected = case.get("expected")
        try:
            got = func(*args, **kwargs)
        except Exception as exc:
            failures.append(
                {
                    "index": index,
                    "args": args,
                    "kwargs": kwargs,
                    "expected": clip(repr(expected)),
                    "got": clip("EXC: {}: {}".format(type(exc).__name__, exc)),
                }
            )
            continue
        if compare(got, expected):
            passed += 1
        else:
            failures.append(
                {
                    "index": index,
                    "args": args,
                    "kwargs": kwargs,
                    "expected": clip(repr(expected)),
                    "got": clip(repr(got)),
                }
            )
    return {"passed": passed, "total": len(cases), "failures": failures}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run a JSON case file against a module.")
    parser.add_argument("--module", default="solution", help="module to import (default: solution)")
    parser.add_argument("--cases", required=True, help="path to the cases JSON file")
    parser.add_argument("--cwd", default=".", help="directory inserted at sys.path[0] (default: .)")
    args = parser.parse_args(argv)

    summary = run(args.module, args.cases, args.cwd)
    sys.stdout.write(json.dumps(summary) + "\n")
    sys.stdout.flush()
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
