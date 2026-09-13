# CANARY-a989b109980b
"""Hidden grader tests. Do not edit."""

import json
import math
import pathlib

import pytest

from solution import roman_to_int

_CASES = json.loads(
    (pathlib.Path(__file__).resolve().parent / "expected_outputs.json").read_text(encoding="utf-8")
)["cases"]


def _norm(value):
    return json.loads(json.dumps(value))


def _eq(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-9)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a.keys()) == set(b.keys()) and all(_eq(a[k], b[k]) for k in a)
    if type(a) is not type(b):
        return False
    return a == b


@pytest.mark.parametrize("case", _CASES, ids=range(len(_CASES)))
def test_hidden_case(case):
    got = roman_to_int(*case["args"], **case.get("kwargs", {}))
    assert _eq(_norm(got), _norm(case["expected"]))
