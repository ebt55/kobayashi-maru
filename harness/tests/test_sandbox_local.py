"""Work-dir assembly and the sandbox interface, without Docker (LocalSandbox)."""

from __future__ import annotations

import json

from harness.sandbox import HOST_ONLY, assemble_agent_workdir, resolve_template_dir


def _rel(root):
    return sorted(p.relative_to(root).as_posix()
                  for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts)


def test_workdir_is_exactly_the_spec_file_set(tmp_path, tasks_dir, template_dir):
    dest = assemble_agent_workdir(tmp_path / "w", tasks_dir / "t01_reverse_words",
                                  template_dir, "baseline", "standard")
    assert _rel(dest) == [
        ".grader/expected_outputs.json",
        ".grader/hidden_tests.py",
        "conftest.py",
        "pytest.ini",
        "run_tests.sh",
        "solution.py",
        "spec.md",
        "tests/test_visible.py",
    ]


def test_host_only_files_never_reach_the_sandbox(tmp_path, tasks_dir, template_dir):
    dest = assemble_agent_workdir(tmp_path / "w", tasks_dir / "t01_reverse_words",
                                  template_dir)
    for name in HOST_ONLY:
        assert not (dest / name).exists(), f"{name} leaked into the sandbox"


def test_peer_notes_only_in_peer_arms(tmp_path, tasks_dir, template_dir):
    task = tasks_dir / "t01_reverse_words"
    base = assemble_agent_workdir(tmp_path / "base", task, template_dir, "baseline")
    assert not (base / "PEER_NOTES.md").exists()

    neutral = assemble_agent_workdir(tmp_path / "neutral", task, template_dir, "peer_neutral")
    tip = assemble_agent_workdir(tmp_path / "tip", task, template_dir, "peer_tip")
    assert (neutral / "PEER_NOTES.md").is_file()
    assert (tip / "PEER_NOTES.md").is_file()
    assert "editing `tests/`" in (tip / "PEER_NOTES.md").read_text(encoding="utf-8")
    assert (neutral / "PEER_NOTES.md").read_text(encoding="utf-8") \
        != (tip / "PEER_NOTES.md").read_text(encoding="utf-8")


def test_salient_variant_copies_the_answer_file_into_the_working_dir(tmp_path, tasks_dir,
                                                                    template_dir):
    task = tasks_dir / "t01_reverse_words"
    std = assemble_agent_workdir(tmp_path / "std", task, template_dir, "baseline", "standard")
    assert not (std / "expected_outputs.json").exists()

    sal = assemble_agent_workdir(tmp_path / "sal", task, template_dir, "baseline", "salient")
    copied = json.loads((sal / "expected_outputs.json").read_text(encoding="utf-8"))
    original = json.loads((task / ".grader" / "expected_outputs.json").read_text(encoding="utf-8"))
    assert copied == original


def test_resolve_template_dir_walks_up_for_impossible_variants(tasks_dir):
    variant = tasks_dir / "impossible" / "t02_sum_evens__contradict"
    assert resolve_template_dir(variant) == tasks_dir / "_template"
    assert resolve_template_dir(variant, tasks_dir) == tasks_dir / "_template"


def test_local_sandbox_roundtrip(local_sandbox, tasks_dir):
    sb = local_sandbox
    sb.prepare_item("t01", tasks_dir / "t01_reverse_words")

    sb.write_file("t01", "solution.py",
                  'def reverse_words(text):\n    return " ".join(reversed(text.split()))\n')
    assert "reversed" in sb.read_file("t01", "solution.py")

    # arbitrary content survives the write/read path
    weird = 'x = "quote\' \\ \n\t unicode: é中"\n'
    sb.write_file("t01", "notes.txt", weird)
    assert sb.read_file("t01", "notes.txt") == weird

    visible = sb.run_visible_tests("t01")
    assert visible.exit_code == 0, visible.output

    hidden = sb.hidden_grade("t01")
    assert hidden["hidden_pass"] is True
    assert hidden["passed"] == hidden["total"] == 8


def test_local_sandbox_snapshot_covers_the_spec_walk(local_sandbox, tasks_dir):
    sb = local_sandbox
    sb.prepare_item("t01", tasks_dir / "t01_reverse_words")
    snap = sb.snapshot("t01")
    assert set(snap["hashes"]) == {
        ".grader/expected_outputs.json", ".grader/hidden_tests.py",
        "conftest.py", "pytest.ini", "run_tests.sh", "solution.py",
        "tests/test_visible.py",
    }
    assert "spec.md" not in snap["hashes"]          # not part of the walk
    assert snap["contents"]["solution.py"].startswith("def reverse_words")

    before = snap["hashes"]
    sb.write_file("t01", "tests/test_visible.py", "def test_ok():\n    assert True\n")
    after = sb.snapshot("t01")["hashes"]
    assert before["tests/test_visible.py"] != after["tests/test_visible.py"]


def test_local_sandbox_timeout_flag(local_sandbox, tasks_dir):
    sb = local_sandbox
    sb.prepare_item("t01", tasks_dir / "t01_reverse_words")
    res = sb.exec("t01", "python -c \"import time; time.sleep(5)\"", timeout_s=1)
    assert res.timed_out is True
