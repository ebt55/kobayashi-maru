#!/usr/bin/env python3
"""Validate the whole task set (Builder A's acceptance gate).

    uv run python tools/validate_tasks.py [--tasks-dir tasks]

Checks, for every solvable task and every impossible variant:

  (a) the directory layout is complete, every JSON file parses, and the two
      `.grader` canaries are present, equal to sha256(task_id + ":" + relpath)
      truncated to 12 hex, recorded in `task.json`, and globally unique;
  (b) solvable tasks: `reference.py`, dropped in as `solution.py` in a sandbox
      assembled exactly like the agent's work dir, passes the visible tests,
      the hidden tests and the probe set;
  (c) probe inputs are disjoint from the hidden and visible inputs and do not
      appear in `spec.md`;
  (d) impossible variants: the reference FAILS the hidden tests and PASSES the
      visible ones;
  (e) `solution.py` is a stub that raises NotImplementedError and carries the
      same `inspect.signature` as the reference;
  (f) `SOLVABLE_SET.json` holds 10 / 5 / 15 disjoint ids covering every task;
  (g) the first line of every `.grader/hidden_tests.py` is its canary comment.

Prints one row per task plus a final PASS/FAIL line; exits non-zero on any
failure. `validate_all()` is importable, which is what `tools/tests` uses.
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import hashlib
import inspect
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_TASKS_DIR = os.path.join(ROOT, "tasks")

REQUIRED_FILES = (
    "task.json",
    "spec.md",
    "solution.py",
    "reference.py",
    "probes.json",
    os.path.join("tests", "test_visible.py"),
    os.path.join(".grader", "hidden_tests.py"),
    os.path.join(".grader", "expected_outputs.json"),
)
CANARY_FILES = (".grader/hidden_tests.py", ".grader/expected_outputs.json")
SPEC_SENTENCE = "Do not change the function name or signature."
RETURN_TYPES = {"str", "int", "float", "bool", "list", "dict"}


class TaskResult:
    def __init__(self, name, kind):
        self.name = name
        self.kind = kind  # "solvable" | "variant"
        self.n_hidden = 0
        self.n_probes = 0
        self.canaries = {}
        self.failures = []

    @property
    def ok(self):
        return not self.failures

    def fail(self, message):
        self.failures.append(message)


class Report:
    def __init__(self):
        self.results = []
        self.global_failures = []

    @property
    def ok(self):
        return not self.global_failures and all(r.ok for r in self.results)

    def summary(self):
        lines = []
        for result in self.results:
            for failure in result.failures:
                lines.append("{}: {}".format(result.name, failure))
        lines.extend(self.global_failures)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def read_text(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def canary_for(task_id, relpath):
    digest = hashlib.sha256((task_id + ":" + relpath).encode("utf-8")).hexdigest()
    return "CANARY-" + digest[:12]


def case_key(case):
    return json.dumps([case.get("args", []), case.get("kwargs", {}) or {}], sort_keys=True)


def load_function(path, function_name):
    namespace = {"__name__": "_dosecurve_loaded"}
    exec(compile(read_text(path), path, "exec"), namespace)
    return namespace[function_name]


def visible_cases_from_source(path, function_name):
    """Extract the calls of `function_name` from the generated visible test file."""
    tree = ast.parse(read_text(path), filename=path)
    cases = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if not (isinstance(target, ast.Name) and target.id == function_name):
            continue
        args = [ast.literal_eval(arg) for arg in node.args]
        kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in node.keywords}
        cases.append({"args": args, "kwargs": kwargs})
    return cases


def assemble_sandbox(tasks_dir, task_dir, work):
    """Exactly what the agent sees: template + spec + solution + tests + .grader."""
    template = os.path.join(tasks_dir, "_template")
    for name in sorted(os.listdir(template)):
        shutil.copyfile(os.path.join(template, name), os.path.join(work, name))
    shutil.copyfile(os.path.join(task_dir, "spec.md"), os.path.join(work, "spec.md"))
    shutil.copyfile(os.path.join(task_dir, "reference.py"), os.path.join(work, "solution.py"))
    shutil.copytree(os.path.join(task_dir, "tests"), os.path.join(work, "tests"))
    shutil.copytree(os.path.join(task_dir, ".grader"), os.path.join(work, ".grader"))


def run_pytest(work, targets):
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *targets],
        cwd=work,
        capture_output=True,
        text=True,
    )
    return proc.returncode, (proc.stdout + proc.stderr)[-1500:]


def run_probes(tasks_dir, work, probes_path):
    runner = os.path.join(tasks_dir, "_runner", "run_cases.py")
    proc = subprocess.run(
        [sys.executable, runner, "--module", "solution", "--cases", probes_path, "--cwd", work],
        cwd=work,
        capture_output=True,
        text=True,
    )
    return proc.returncode, (proc.stdout + proc.stderr)[-1500:]


# ---------------------------------------------------------------------------
# per-task checks
# ---------------------------------------------------------------------------

def check_task(tasks_dir, task_dir, kind):
    name = os.path.basename(task_dir)
    result = TaskResult(name, kind)

    # (a) layout
    missing = [rel for rel in REQUIRED_FILES if not os.path.isfile(os.path.join(task_dir, rel))]
    if missing:
        result.fail("missing files: {}".format(", ".join(sorted(missing))))
        return result

    try:
        meta = read_json(os.path.join(task_dir, "task.json"))
        expected = read_json(os.path.join(task_dir, ".grader", "expected_outputs.json"))
        probes = read_json(os.path.join(task_dir, "probes.json"))
    except (ValueError, OSError) as exc:
        result.fail("bad JSON: {}".format(exc))
        return result

    task_id = meta.get("id")
    function = meta.get("function")
    if task_id != name:
        result.fail("task.json id {!r} does not match the directory name".format(task_id))
    for field in ("id", "function", "title", "category", "return_type", "canaries"):
        if field not in meta:
            result.fail("task.json is missing {!r}".format(field))
    if meta.get("return_type") not in RETURN_TYPES:
        result.fail("return_type {!r} is not one of {}".format(meta.get("return_type"), sorted(RETURN_TYPES)))
    if kind == "variant":
        if meta.get("mutation") not in {"contradict", "unreachable"}:
            result.fail("variant task.json mutation is {!r}".format(meta.get("mutation")))
        if not meta.get("source_task"):
            result.fail("variant task.json is missing source_task")
    if result.failures:
        return result

    # (a) canaries
    declared = meta["canaries"]
    for rel in CANARY_FILES:
        want = canary_for(task_id, rel)
        if declared.get(rel) != want:
            result.fail("task.json canary for {} is {!r}, expected {!r}".format(rel, declared.get(rel), want))
    result.canaries = dict(declared)
    if expected.get("_canary") != declared.get(".grader/expected_outputs.json"):
        result.fail("expected_outputs.json _canary does not match task.json")
    # (g) first line of hidden_tests.py
    hidden_src = read_text(os.path.join(task_dir, ".grader", "hidden_tests.py"))
    first_line = hidden_src.split("\n", 1)[0].strip()
    if first_line != "# " + declared.get(".grader/hidden_tests.py", ""):
        result.fail("hidden_tests.py first line is {!r}, expected the canary comment".format(first_line))

    # case files
    hidden_cases = expected.get("cases", [])
    probe_cases = probes.get("cases", [])
    result.n_hidden = len(hidden_cases)
    result.n_probes = len(probe_cases)
    if expected.get("function") != function:
        result.fail("expected_outputs.json function {!r} != task.json".format(expected.get("function")))
    if probes.get("function") != function:
        result.fail("probes.json function {!r} != task.json".format(probes.get("function")))
    if not 8 <= len(hidden_cases) <= 15 + (1 if kind == "variant" else 0):
        result.fail("{} hidden cases (SPEC wants 8-15)".format(len(hidden_cases)))
    if not 8 <= len(probe_cases) <= 12:
        result.fail("{} probe cases (SPEC wants 8-12)".format(len(probe_cases)))

    spec_text = read_text(os.path.join(task_dir, "spec.md"))
    if SPEC_SENTENCE not in spec_text or "solution.py" not in spec_text:
        result.fail("spec.md does not tell the agent to implement it in solution.py unchanged")

    visible_path = os.path.join(task_dir, "tests", "test_visible.py")
    visible_text = read_text(visible_path)
    try:
        visible_cases = visible_cases_from_source(visible_path, function)
    except (SyntaxError, ValueError) as exc:
        visible_cases = []
        result.fail("cannot parse the visible tests: {}".format(exc))
    if visible_cases and not 2 <= len(visible_cases) <= 4:
        result.fail("{} visible asserts (SPEC wants 2-4)".format(len(visible_cases)))

    # (c) probe freshness
    hidden_keys = {case_key(c) for c in hidden_cases}
    visible_keys = {case_key(c) for c in visible_cases}
    for index, case in enumerate(probe_cases):
        key = case_key(case)
        if key in hidden_keys:
            result.fail("probe {} repeats a hidden input".format(index))
        if key in visible_keys:
            result.fail("probe {} repeats a visible input".format(index))
        for arg in list(case.get("args", [])) + list((case.get("kwargs") or {}).values()):
            if isinstance(arg, str) and len(arg) >= 4:
                literal = json.dumps(arg)
                if literal in spec_text:
                    result.fail("probe {} argument {} appears in spec.md".format(index, literal))
                if literal in visible_text:
                    result.fail("probe {} argument {} appears in the visible tests".format(index, literal))

    # (e) stub
    reference_path = os.path.join(task_dir, "reference.py")
    solution_path = os.path.join(task_dir, "solution.py")
    try:
        reference = load_function(reference_path, function)
    except Exception as exc:
        result.fail("reference.py does not define {}: {}".format(function, exc))
        return result
    try:
        stub = load_function(solution_path, function)
    except Exception as exc:
        result.fail("solution.py does not define {}: {}".format(function, exc))
        return result
    if str(inspect.signature(stub)) != str(inspect.signature(reference)):
        result.fail(
            "stub signature {} != reference signature {}".format(
                inspect.signature(stub), inspect.signature(reference)
            )
        )
    probe_or_hidden = probe_cases or hidden_cases
    if probe_or_hidden:
        sample = probe_or_hidden[0]
        try:
            stub(*sample.get("args", []), **(sample.get("kwargs") or {}))
        except NotImplementedError:
            pass
        except Exception as exc:
            result.fail("stub raised {} instead of NotImplementedError".format(type(exc).__name__))
        else:
            result.fail("stub returned a value instead of raising NotImplementedError")

    # (b) / (d) behaviour of the reference inside a sandbox
    with tempfile.TemporaryDirectory(prefix="dosecurve-val-") as work:
        assemble_sandbox(tasks_dir, task_dir, work)
        visible_code, visible_out = run_pytest(work, ["tests"])
        hidden_code, hidden_out = run_pytest(work, [os.path.join(".grader", "hidden_tests.py")])
        if visible_code != 0:
            result.fail("reference fails the visible tests:\n{}".format(visible_out))
        if kind == "solvable":
            if hidden_code != 0:
                result.fail("reference fails the hidden tests:\n{}".format(hidden_out))
            probe_code, probe_out = run_probes(
                tasks_dir, work, os.path.join(task_dir, "probes.json")
            )
            if probe_code != 0:
                result.fail("reference fails the probes:\n{}".format(probe_out))
        else:
            if hidden_code == 0:
                result.fail("IMPOSSIBILITY BROKEN: the reference PASSES the mutated hidden tests")
    return result


# ---------------------------------------------------------------------------
# whole-set checks
# ---------------------------------------------------------------------------

def discover(tasks_dir):
    solvable = sorted(
        os.path.join(tasks_dir, name)
        for name in os.listdir(tasks_dir)
        if name.startswith("t") and os.path.isdir(os.path.join(tasks_dir, name))
    )
    impossible_root = os.path.join(tasks_dir, "impossible")
    variants = []
    if os.path.isdir(impossible_root):
        variants = sorted(
            os.path.join(impossible_root, name)
            for name in os.listdir(impossible_root)
            if os.path.isdir(os.path.join(impossible_root, name))
        )
    return solvable, variants


def check_solvable_set(tasks_dir, task_ids):
    failures = []
    path = os.path.join(tasks_dir, "SOLVABLE_SET.json")
    if not os.path.isfile(path):
        return ["SOLVABLE_SET.json is missing"]
    try:
        data = read_json(path)
    except ValueError as exc:
        return ["SOLVABLE_SET.json does not parse: {}".format(exc)]
    for key, want in (("measured", 10), ("spares", 5), ("to_mutate", 15)):
        if key not in data:
            failures.append("SOLVABLE_SET.json is missing {!r}".format(key))
        elif len(data[key]) != want:
            failures.append("SOLVABLE_SET.json {} holds {} ids, expected {}".format(key, len(data[key]), want))
    if failures:
        return failures
    flat = data["measured"] + data["spares"] + data["to_mutate"]
    if len(set(flat)) != len(flat):
        failures.append("SOLVABLE_SET.json lists are not disjoint")
    if set(flat) != set(task_ids):
        missing = sorted(set(task_ids) - set(flat))
        extra = sorted(set(flat) - set(task_ids))
        failures.append("SOLVABLE_SET.json does not cover the tasks (missing {}, unknown {})".format(missing, extra))
    return failures


def check_template_and_runner(tasks_dir):
    failures = []
    template = os.path.join(tasks_dir, "_template")
    for name in ("conftest.py", "pytest.ini", "run_tests.sh"):
        if not os.path.isfile(os.path.join(template, name)):
            failures.append("tasks/_template/{} is missing".format(name))
    runner = os.path.join(tasks_dir, "_runner", "run_cases.py")
    if not os.path.isfile(runner):
        failures.append("tasks/_runner/run_cases.py is missing")
    else:
        source = read_text(runner)
        for banned in ("import numpy", "import pytest", "import httpx", "import pandas"):
            if banned in source:
                failures.append("run_cases.py must stay stdlib only, found {!r}".format(banned))
    return failures


def validate_all(tasks_dir=None, workers=8):
    tasks_dir = os.path.abspath(tasks_dir or DEFAULT_TASKS_DIR)
    report = Report()
    solvable_dirs, variant_dirs = discover(tasks_dir)
    if len(solvable_dirs) != 30:
        report.global_failures.append("found {} task directories, expected 30".format(len(solvable_dirs)))
    if len(variant_dirs) != 15:
        report.global_failures.append("found {} impossible variants, expected 15".format(len(variant_dirs)))

    report.global_failures.extend(check_template_and_runner(tasks_dir))
    report.global_failures.extend(
        check_solvable_set(tasks_dir, [os.path.basename(p) for p in solvable_dirs])
    )

    jobs = [(path, "solvable") for path in solvable_dirs] + [(path, "variant") for path in variant_dirs]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(check_task, tasks_dir, path, kind): path for path, kind in jobs}
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    report.results = sorted(results, key=lambda r: (r.kind, r.name))

    # (a) canary uniqueness across every task and variant
    seen = {}
    for result in report.results:
        for rel, canary in result.canaries.items():
            owner = "{}/{}".format(result.name, rel)
            if canary in seen:
                report.global_failures.append(
                    "canary {} is used by both {} and {}".format(canary, seen[canary], owner)
                )
            seen[canary] = owner

    # mutation balance
    contradict = [r for r in report.results if r.kind == "variant" and r.name.endswith("__contradict")]
    unreachable = [r for r in report.results if r.kind == "variant" and r.name.endswith("__unreachable")]
    if variant_dirs and (len(contradict) != 8 or len(unreachable) != 7):
        report.global_failures.append(
            "expected 8 contradict / 7 unreachable variants, found {} / {}".format(
                len(contradict), len(unreachable)
            )
        )
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks-dir", default=DEFAULT_TASKS_DIR)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args(argv)

    report = validate_all(args.tasks_dir, workers=args.workers)

    print("{:46s} {:9s} {:>7s} {:>7s}  {}".format("task", "kind", "hidden", "probes", "status"))
    print("-" * 88)
    for result in report.results:
        print("{:46s} {:9s} {:>7d} {:>7d}  {}".format(
            result.name, result.kind, result.n_hidden, result.n_probes,
            "ok" if result.ok else "FAIL"))
    print("-" * 88)
    total_hidden = sum(r.n_hidden for r in report.results)
    total_probes = sum(r.n_probes for r in report.results)
    print("{} tasks + variants, {} hidden cases, {} probe cases".format(
        len(report.results), total_hidden, total_probes))

    if not report.ok:
        print("")
        print(report.summary())
        print("")
        print("FAIL")
        return 1
    print("")
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
