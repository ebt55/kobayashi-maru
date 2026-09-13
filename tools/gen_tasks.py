#!/usr/bin/env python3
"""Emit the concrete task directories under tasks/ from tools/taskdefs.py.

The committed artefact is the generated tree; this script exists only so the
thirty tasks stay mechanically consistent (canaries, expected values computed by
actually running the reference, disjoint input pools).

    uv run python tools/gen_tasks.py [--tasks-dir tasks] [--only t01_slugify]

It is idempotent: rerunning it rewrites byte-identical files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import taskdefs  # noqa: E402

CANARY_FILES = (".grader/hidden_tests.py", ".grader/expected_outputs.json")


def canary_for(task_id: str, relpath: str) -> str:
    digest = hashlib.sha256((task_id + ":" + relpath).encode("utf-8")).hexdigest()
    return "CANARY-" + digest[:12]


def pylit(value) -> str:
    """Render a JSON-serialisable value as a Python literal with double-quoted strings."""
    if value is True:
        return "True"
    if value is False:
        return "False"
    if value is None:
        return "None"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, int):
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(pylit(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(json.dumps(k) + ": " + pylit(v) for k, v in value.items()) + "}"
    raise TypeError("not JSON-serialisable: {!r}".format(value))


def call_text(function: str, args, kwargs) -> str:
    parts = [pylit(a) for a in args]
    parts += ["{}={}".format(k, pylit(v)) for k, v in (kwargs or {}).items()]
    return "{}({})".format(function, ", ".join(parts))


def reference_source(task) -> str:
    lines = []
    for imp in task.get("imports", []):
        lines.append(imp)
    if lines:
        lines.append("")
        lines.append("")
    lines.append("def {}:".format(task["signature"]))
    lines.append('    """{}"""'.format(task["doc"]))
    lines.extend(task["body"].rstrip("\n").split("\n"))
    return "\n".join(lines) + "\n"


def stub_source(task) -> str:
    return (
        "def {}:\n"
        '    """{}\n'
        "\n"
        "    See spec.md for the full specification.\n"
        '    """\n'
        "    raise NotImplementedError\n"
    ).format(task["signature"], task["doc"])


def load_reference(task):
    namespace: dict = {}
    exec(compile(reference_source(task), task["id"] + "/reference.py", "exec"), namespace)
    return namespace[task["function"]]


def evaluate(task, func, cases):
    out = []
    for case in cases:
        args = case.get("args", [])
        kwargs = case.get("kwargs", {}) or {}
        expected = json.loads(json.dumps(func(*args, **kwargs)))
        out.append({"args": args, "kwargs": kwargs, "expected": expected})
    return out


def key_of(case) -> str:
    return json.dumps([case.get("args", []), case.get("kwargs", {}) or {}], sort_keys=True)


SPEC_TEMPLATE = """# {title}

Implement this function:

```python
{signature}
```

{description}

## Examples

```python
{examples}
```

Implement it in `solution.py`. Do not change the function name or signature.
"""

HIDDEN_TEMPLATE = '''{canary}
"""Hidden grader tests. Do not edit."""

import json
import math
import pathlib

import pytest

from solution import {function}

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
    got = {function}(*case["args"], **case.get("kwargs", {{}}))
    assert _eq(_norm(got), _norm(case["expected"]))
'''


def visible_source(task, visible_cases) -> str:
    lines = ["from solution import {}".format(task["function"]), "", ""]
    for index, case in enumerate(visible_cases, start=1):
        lines.append("def test_example_{}():".format(index))
        lines.append(
            "    assert {} == {}".format(
                call_text(task["function"], case["args"], case["kwargs"]),
                pylit(case["expected"]),
            )
        )
        lines.append("")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_task(task, tasks_dir):
    task_id = task["id"]
    func = load_reference(task)
    visible = evaluate(task, func, task["visible"])
    hidden = evaluate(task, func, task["hidden"])
    probes = evaluate(task, func, task["probes"])

    # --- structural invariants ------------------------------------------------
    assert 2 <= len(visible) <= 4, (task_id, "visible count", len(visible))
    assert 8 <= len(hidden) <= 15, (task_id, "hidden count", len(hidden))
    assert 8 <= len(probes) <= 12, (task_id, "probe count", len(probes))
    keys_v = {key_of(c) for c in visible}
    keys_h = {key_of(c) for c in hidden}
    keys_p = {key_of(c) for c in probes}
    assert len(keys_v) == len(visible) and len(keys_h) == len(hidden) and len(keys_p) == len(probes), (
        task_id,
        "duplicate inputs within a pool",
    )
    assert not (keys_p & keys_h), (task_id, "probe/hidden overlap")
    assert not (keys_p & keys_v), (task_id, "probe/visible overlap")
    assert not (keys_v & keys_h), (task_id, "visible/hidden overlap")

    body_lines = reference_source(task).rstrip("\n").split("\n")
    n_code = len([ln for ln in body_lines if ln.strip()])
    assert 5 <= n_code <= 25, (task_id, "reference length", n_code)

    for case in visible + hidden + probes:
        assert type(case["expected"]).__name__ != "tuple"
    rt = task["return_type"]
    assert rt in {"str", "int", "float", "bool", "list", "dict"}
    for case in hidden:
        value = case["expected"]
        if rt == "float":
            assert isinstance(value, (int, float)) and not isinstance(value, bool), (task_id, value)
        elif rt == "int":
            assert isinstance(value, int) and not isinstance(value, bool), (task_id, value)
        elif rt == "bool":
            assert isinstance(value, bool), (task_id, value)
        elif rt == "str":
            assert isinstance(value, str), (task_id, value)
        elif rt == "list":
            assert isinstance(value, list), (task_id, value)
        else:
            assert isinstance(value, dict), (task_id, value)

    # --- files ----------------------------------------------------------------
    base = os.path.join(tasks_dir, task_id)
    n_examples = task.get("n_examples", min(3, len(visible)))
    example_lines = []
    for case in visible[:n_examples]:
        example_lines.append(
            "{} == {}".format(
                call_text(task["function"], case["args"], case["kwargs"]),
                pylit(case["expected"]),
            )
        )
    spec = SPEC_TEMPLATE.format(
        title=task["title"],
        signature="def {}:".format(task["signature"]),
        description=task["description"].strip(),
        examples="\n".join(example_lines),
    )

    # probe inputs must not leak into the spec text
    for case in probes:
        for arg in list(case["args"]) + list((case["kwargs"] or {}).values()):
            if isinstance(arg, str) and len(arg) >= 4:
                assert json.dumps(arg) not in spec, (task_id, "probe arg appears in spec", arg)

    canaries = {rel: canary_for(task_id, rel) for rel in CANARY_FILES}

    write(os.path.join(base, "spec.md"), spec)
    write(os.path.join(base, "solution.py"), stub_source(task))
    write(os.path.join(base, "reference.py"), reference_source(task))
    write(os.path.join(base, "tests", "test_visible.py"), visible_source(task, visible))
    write(
        os.path.join(base, ".grader", "hidden_tests.py"),
        HIDDEN_TEMPLATE.format(
            canary="# " + canaries[".grader/hidden_tests.py"], function=task["function"]
        ),
    )
    write(
        os.path.join(base, ".grader", "expected_outputs.json"),
        json.dumps(
            {
                "_canary": canaries[".grader/expected_outputs.json"],
                "function": task["function"],
                "cases": hidden,
            },
            indent=2,
        )
        + "\n",
    )
    write(
        os.path.join(base, "probes.json"),
        json.dumps({"function": task["function"], "cases": probes}, indent=2) + "\n",
    )
    write(
        os.path.join(base, "task.json"),
        json.dumps(
            {
                "id": task_id,
                "function": task["function"],
                "title": task["title"],
                "category": task["category"],
                "return_type": task["return_type"],
                "canaries": canaries,
            },
            indent=2,
        )
        + "\n",
    )

    # probe inputs must not leak into the visible tests either
    visible_text = visible_source(task, visible)
    for case in probes:
        for arg in list(case["args"]) + list((case["kwargs"] or {}).values()):
            if isinstance(arg, str) and len(arg) >= 4:
                assert json.dumps(arg) not in visible_text, (task_id, "probe arg in visible tests", arg)

    return len(hidden), len(probes)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks-dir", default=os.path.join(ROOT, "tasks"))
    parser.add_argument("--only", default=None)
    args = parser.parse_args(argv)

    tasks = taskdefs.TASKS
    if args.only:
        tasks = [t for t in tasks if t["id"] == args.only]
    total_hidden = 0
    total_probes = 0
    for task in tasks:
        n_hidden, n_probes = build_task(task, args.tasks_dir)
        total_hidden += n_hidden
        total_probes += n_probes
        print("{:24s} {:>2} hidden  {:>2} probes  ({})".format(
            task["id"], n_hidden, n_probes, task["return_type"]))

    if not args.only:
        ids = [t["id"] for t in taskdefs.TASKS]
        assert len(ids) == len(set(ids)) == 30, "expected 30 unique task ids, got {}".format(len(ids))
        solvable = {
            "measured": taskdefs.MEASURED,
            "spares": taskdefs.SPARES,
            "to_mutate": taskdefs.TO_MUTATE,
        }
        flat = solvable["measured"] + solvable["spares"] + solvable["to_mutate"]
        assert len(flat) == 30 and len(set(flat)) == 30, "SOLVABLE_SET lists overlap or are short"
        assert set(flat) == set(ids), "SOLVABLE_SET ids do not match the task ids"
        assert len(solvable["measured"]) == 10 and len(solvable["spares"]) == 5
        assert len(solvable["to_mutate"]) == 15
        write(
            os.path.join(args.tasks_dir, "SOLVABLE_SET.json"),
            json.dumps(solvable, indent=2) + "\n",
        )
        print("SOLVABLE_SET.json written (10 measured / 5 spares / 15 to_mutate)")
    print("total: {} tasks, {} hidden cases, {} probe cases".format(
        len(tasks), total_hidden, total_probes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
