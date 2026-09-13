# CANARY-e9790db66a98
import json
import os

import pytest

from solution import sum_evens

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "expected_outputs.json"), "r", encoding="utf-8") as _fh:
    _DATA = json.load(_fh)
CASES = _DATA["cases"]


@pytest.mark.parametrize("case", CASES, ids=[str(i) for i in range(len(CASES))])
def test_hidden(case):
    got = sum_evens(*case.get("args", []), **case.get("kwargs", {}))
    assert got == case["expected"]
