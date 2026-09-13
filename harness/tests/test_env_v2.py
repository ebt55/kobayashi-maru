"""Environment v2: the work dir must not label the item, and no sibling may survive.

Review T4/C2: the work dir was ``/work/<item_key>`` and the key carries the mutation
suffix, so `pwd`, `ls -la ..`, `ls /work`, `env` and Python tracebacks printed
``__unreachable`` / ``__contradict`` to the agent.
Review T7/C3: earlier items' work dirs stayed readable for the life of the batch
container, so one item could read another's grader files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.agent import ItemContext, run_item
from harness.config import RunConfig
from harness.providers.fake_provider import FakeProvider
from harness.sandbox import ENV_VERSION, DockerSandbox, LocalSandbox
from harness.tests.conftest import require_docker

LEAK_TOKENS = ("__unreachable", "__contradict")
PROBE = "pwd; ls -la ..; ls /work; env; python -c \"import os;print(os.getcwd())\""


def _ctx(tasks_dir, item_key, task_dir, position) -> ItemContext:
    return ItemContext(batch_id="b", task_dir=task_dir, item_key=item_key,
                       task_id=item_key.split("__")[0], position=position,
                       batch_size=14, I=4, f_realised=0.2857, seed=0,
                       is_impossible="__" in item_key,
                       mutation="contradict" if "__contradict" in item_key else None)


def _cfg(tasks_dir, tmp_path, **kw) -> RunConfig:
    base = dict(provider="fake", model="fake-model", model_slug="fake",
                tasks_dir=tasks_dir, out_dir=tmp_path / "runs", dry_run=True,
                item_wall_clock_s=120)
    base.update(kw)
    return RunConfig(**base)


def test_default_env_version_is_two():
    assert ENV_VERSION == 2
    assert RunConfig().env_version == 2
    assert RunConfig().model_config()["env_version"] == 2
    assert LocalSandbox("b").env_version == 2


def test_opaque_dir_name_from_position(tmp_path, tasks_dir):
    sb = LocalSandbox("b", root=tmp_path / "w")
    variant = tasks_dir / "impossible" / "t02_sum_evens__contradict"
    sb.prepare_item("t02_sum_evens__contradict", variant, position=7,
                    template_dir=tasks_dir / "_template")
    assert sb._dirname("t02_sum_evens__contradict") == "item_07"
    assert [p.name for p in sb.root.iterdir()] == ["item_07"]
    assert not any(tok in str(p) for p in sb.root.rglob("*") for tok in LEAK_TOKENS)


def test_v1_keeps_the_old_leaky_layout(tmp_path, tasks_dir):
    """The frozen sweeps are reproducible: v1 still names the dir after the item."""
    sb = LocalSandbox("b", root=tmp_path / "w", env_version=1)
    variant = tasks_dir / "impossible" / "t02_sum_evens__contradict"
    sb.prepare_item("t02_sum_evens__contradict", variant, position=7,
                    template_dir=tasks_dir / "_template")
    assert sb._dirname("t02_sum_evens__contradict") == "t02_sum_evens__contradict"


def test_earlier_item_directories_are_removed(tmp_path, tasks_dir):
    sb = LocalSandbox("b", root=tmp_path / "w")
    tdir = tasks_dir / "_template"
    sb.prepare_item("t01_reverse_words", tasks_dir / "t01_reverse_words", position=0,
                    template_dir=tdir)
    assert (sb.root / "item_00").is_dir()
    sb.prepare_item("t02_sum_evens", tasks_dir / "t02_sum_evens", position=1,
                    template_dir=tdir)
    assert not (sb.root / "item_00").exists()          # item k-1 is gone
    assert [p.name for p in sb.root.iterdir()] == ["item_01"]


def test_work_dir_contents_carry_no_mutation_label(tmp_path, tasks_dir):
    """Not just the directory name: no copied file name or body may reveal the variant."""
    sb = LocalSandbox("b", root=tmp_path / "w")
    variant = tasks_dir / "impossible" / "t02_sum_evens__contradict"
    sb.prepare_item("t02_sum_evens__contradict", variant, position=2,
                    template_dir=tasks_dir / "_template")
    work = sb.root / "item_02"
    for path in work.rglob("*"):
        assert not any(tok in path.name for tok in LEAK_TOKENS), path
        if path.is_file():
            try:
                body = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for tok in LEAK_TOKENS:
                assert tok not in body, f"{path} leaks {tok}"


def test_transcript_of_a_probing_agent_has_no_label(tmp_path, tasks_dir,
                                                    local_grader_factory):
    """The end-to-end check: an agent that runs `pwd; ls -la ..; ls /work; env` sees
    nothing that names the mutation, in any tool output or transcript entry."""
    sb = LocalSandbox("b", root=tmp_path / "w", tasks_dir=tasks_dir)
    variant = tasks_dir / "impossible" / "t02_sum_evens__contradict"
    script = [{"tool": "bash", "args": {"command": PROBE}},
              {"tool": "submit", "args": {"summary": "looked around"}}]
    provider = FakeProvider({"t02_sum_evens__contradict": script})
    rec = run_item(provider, sb, _cfg(tasks_dir, tmp_path),
                   _ctx(tasks_dir, "t02_sum_evens__contradict", variant, 5),
                   template_dir=tasks_dir / "_template",
                   runner_path=tasks_dir / "_runner" / "run_cases.py",
                   grader_factory=local_grader_factory)

    blob = json.dumps({"tool_calls": rec["tool_calls"], "transcript": rec["transcript"],
                       "final_files": rec["final_files"]})
    for tok in LEAK_TOKENS:
        assert tok not in blob, f"{tok} leaked into the agent's view"
    # the record still carries the real identity for analysis
    assert rec["item_key"] == "t02_sum_evens__contradict"
    assert rec["mutation"] == "contradict"
    assert rec["model_config"]["env_version"] == 2
    sb.close()


@pytest.mark.docker
def test_docker_probe_sees_no_label_and_no_sibling(tmp_path, tasks_dir):
    require_docker()
    tdir = tasks_dir / "_template"
    sb = DockerSandbox("test_env_v2", tasks_dir=tasks_dir, template_dir=tdir)
    try:
        sb.start()
        sb.prepare_item("t01_reverse_words", tasks_dir / "t01_reverse_words",
                        position=0, template_dir=tdir)
        sb.write_file("t01_reverse_words", "marker.txt", "first item was here")

        variant = tasks_dir / "impossible" / "t02_sum_evens__contradict"
        sb.prepare_item("t02_sum_evens__contradict", variant, position=1,
                        template_dir=tdir)
        out = sb.exec("t02_sum_evens__contradict", PROBE).output
        for tok in LEAK_TOKENS:
            assert tok not in out, f"{tok} visible to the agent:\n{out}"
        assert "/work/item_01" in out                   # opaque, positional
        assert "item_00" not in out                     # the sibling is gone
        assert "marker.txt" not in out
        # `..` exists but holds only the current item
        siblings = sb.exec("t02_sum_evens__contradict", "ls -A ..").output.split()
        assert siblings == ["item_01"], siblings
    finally:
        sb.close()
