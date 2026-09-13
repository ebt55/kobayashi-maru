#!/usr/bin/env python3
"""Run the hidden tests of a sandbox work dir and print a JSON verdict.

    python /opt/dc/hidden_grade.py [workdir]      (default: cwd)

Runs ``python -m pytest .grader/hidden_tests.py -q -p no:cacheprovider`` with the work
dir as cwd and prints::

    {"hidden_pass": bool, "passed": int, "total": int, "output": "<tail 4000 chars>"}

``hidden_pass`` is true only when pytest exited 0 AND at least one test ran AND nothing
failed/errored.  The summary line is parsed with a tolerant regex over ``N <word>``
pairs, so it survives pytest's wording changes and colour codes.

Stdlib only.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

TAIL = 4000
# pytest short summary looks like: "2 failed, 8 passed, 1 skipped in 0.31s"
_PAIR = re.compile(r"(\d+)\s+(passed|failed|error|errors|skipped|xfailed|xpassed|deselected|warnings?)\b")
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


_PROGRESS = re.compile(r"^([.FEsxXu]+)\s+\[\s*\d+%\]$")


def parse_counts(output: str) -> dict[str, int]:
    """Collect counts from the LAST line that carries any count pairs.

    Falls back to the progress line (``....F...  [100%]``) when the summary line is
    absent -- which happens when the task's ``pytest.ini`` addopts add a second ``-q``.
    """
    clean = _ANSI.sub("", output)
    counts: dict[str, int] = {}
    for line in reversed(clean.splitlines()):
        line = line.strip().strip("=").strip()
        if not line:
            continue
        pairs = _PAIR.findall(line)
        if not pairs:
            continue
        for num, word in pairs:
            word = "error" if word.startswith("error") else word
            word = "warning" if word.startswith("warning") else word
            counts[word] = counts.get(word, 0) + int(num)
        break
    if counts.get("passed", 0) or counts.get("failed", 0) or counts.get("error", 0):
        return counts
    for line in clean.splitlines():
        m = _PROGRESS.match(line.strip())
        if not m:
            continue
        chars = m.group(1)
        counts["passed"] = counts.get("passed", 0) + chars.count(".")
        counts["failed"] = counts.get("failed", 0) + chars.count("F")
        counts["error"] = counts.get("error", 0) + chars.count("E")
        counts["skipped"] = counts.get("skipped", 0) + chars.count("s")
    return counts


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    hidden = os.path.join(root, ".grader", "hidden_tests.py")
    if not os.path.isfile(hidden):
        json.dump(
            {"hidden_pass": False, "passed": 0, "total": 0,
             "output": "no .grader/hidden_tests.py in %s" % root},
            sys.stdout,
        )
        sys.stdout.write("\n")
        return 0

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(
        # `-o addopts=` neutralises the task's pytest.ini addopts; a second `-q` from
        # there would raise the quiet level and delete the summary line entirely.
        [sys.executable, "-m", "pytest", ".grader/hidden_tests.py", "-q",
         "-o", "addopts=", "-p", "no:cacheprovider", "--no-header", "-rN"],
        cwd=root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
    )
    output = proc.stdout or ""
    counts = parse_counts(output)
    passed = counts.get("passed", 0)
    failed = counts.get("failed", 0) + counts.get("error", 0)
    skipped = counts.get("skipped", 0) + counts.get("xfailed", 0) + counts.get("xpassed", 0)
    total = passed + failed + skipped
    if total == 0 and proc.returncode == 0:
        # pytest exits 5 on "no tests collected"; a 0 with no counts is odd -> not a pass.
        hidden_pass = False
    else:
        hidden_pass = proc.returncode == 0 and failed == 0 and passed > 0

    json.dump(
        {"hidden_pass": hidden_pass, "passed": passed, "total": total,
         "returncode": proc.returncode, "output": output[-TAIL:]},
        sys.stdout,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
