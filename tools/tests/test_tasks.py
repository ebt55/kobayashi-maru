"""CI-style verification of the task set: `uv run pytest tools/tests -q`.

Everything here goes through `tools/validate_tasks.py`, so the gate the human
runs by hand and the gate CI runs are the same code.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

import pytest

from tools.validate_tasks import (
    DEFAULT_TASKS_DIR,
    assemble_sandbox,
    check_solvable_set,
    check_template_and_runner,
    discover,
    read_json,
    validate_all,
)


@pytest.fixture(scope="module")
def report():
    return validate_all(DEFAULT_TASKS_DIR)


def test_task_set_validates(report):
    assert report.ok, "\n" + report.summary()


def test_thirty_solvable_tasks_and_fifteen_variants():
    solvable, variants = discover(DEFAULT_TASKS_DIR)
    assert len(solvable) == 30
    assert len(variants) == 15
    contradict = [p for p in variants if p.endswith("__contradict")]
    unreachable = [p for p in variants if p.endswith("__unreachable")]
    assert len(contradict) == 8
    assert len(unreachable) == 7


def test_template_and_runner_present():
    assert check_template_and_runner(DEFAULT_TASKS_DIR) == []


def test_solvable_set_is_disjoint_and_complete():
    solvable, _ = discover(DEFAULT_TASKS_DIR)
    ids = [os.path.basename(path) for path in solvable]
    assert check_solvable_set(DEFAULT_TASKS_DIR, ids) == []
    data = read_json(os.path.join(DEFAULT_TASKS_DIR, "SOLVABLE_SET.json"))
    assert len(set(data["measured"]) & set(data["spares"])) == 0
    assert len(set(data["measured"]) & set(data["to_mutate"])) == 0
    assert len(set(data["spares"]) & set(data["to_mutate"])) == 0
    types = set()
    for task_id in data["to_mutate"]:
        meta = read_json(os.path.join(DEFAULT_TASKS_DIR, task_id, "task.json"))
        types.add(meta["return_type"])
    assert types == {"str", "int", "float", "bool", "list", "dict"}, types


def test_every_canary_is_unique():
    solvable, variants = discover(DEFAULT_TASKS_DIR)
    seen = set()
    for path in solvable + variants:
        meta = read_json(os.path.join(path, "task.json"))
        for canary in meta["canaries"].values():
            assert canary not in seen, canary
            seen.add(canary)
    assert len(seen) == 90


def _run_cases(work, cases_path):
    runner = os.path.join(DEFAULT_TASKS_DIR, "_runner", "run_cases.py")
    proc = subprocess.run(
        [sys.executable, runner, "--module", "solution", "--cases", cases_path, "--cwd", work],
        cwd=work,
        capture_output=True,
        text=True,
    )
    lines = [line for line in proc.stdout.strip().split("\n") if line.strip()]
    assert len(lines) == 1, proc.stdout + proc.stderr
    return proc.returncode, json.loads(lines[0])


def test_run_cases_contract_on_a_reference_and_on_a_stub():
    task_dir = os.path.join(DEFAULT_TASKS_DIR, "t03_roman_to_int")
    probes = os.path.join(task_dir, "probes.json")

    with tempfile.TemporaryDirectory(prefix="dosecurve-runner-") as work:
        assemble_sandbox(DEFAULT_TASKS_DIR, task_dir, work)  # reference as solution.py
        code, summary = _run_cases(work, probes)
        assert code == 0
        assert summary["passed"] == summary["total"] > 0
        assert summary["failures"] == []

        # a wrong solution fails every case, and each failure carries its evidence
        with open(os.path.join(work, "solution.py"), "w", encoding="utf-8", newline="\n") as handle:
            handle.write("def roman_to_int(roman: str) -> int:\n    return -1\n")
        code, summary = _run_cases(work, probes)
        assert code == 1
        assert summary["passed"] == 0
        assert len(summary["failures"]) == summary["total"]
        first = summary["failures"][0]
        assert set(first) == {"index", "args", "kwargs", "expected", "got"}
        assert len(first["expected"]) <= 300 and len(first["got"]) <= 300

        # an exception in one case is a failure for that case only, not a crash
        with open(os.path.join(work, "solution.py"), "w", encoding="utf-8", newline="\n") as handle:
            handle.write(
                "def roman_to_int(roman: str) -> int:\n"
                "    if roman == 'VII':\n"
                "        raise ValueError('boom')\n"
                "    return -1\n"
            )
        code, summary = _run_cases(work, probes)
        assert code == 1
        assert any(f["got"].startswith("EXC: ValueError") for f in summary["failures"])
