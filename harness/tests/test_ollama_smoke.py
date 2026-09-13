"""Live Ollama smoke test: one fixture item with llama3.1:8b (marked ``ollama``).

Cheap model on purpose -- this checks the wire shape and the tool loop, not behaviour.
Skips when Ollama is unreachable or the model is not pulled.
"""

from __future__ import annotations

import pytest

from harness.agent import ItemContext, run_item
from harness.config import RunConfig
from harness.grade import docker_grader_factory
from harness.providers.ollama_provider import OllamaProvider, reachable
from harness.records import RECORD_KEYS, validate_record
from harness.sandbox import DockerSandbox
from harness.tests.conftest import require_docker

pytestmark = pytest.mark.ollama

MODEL = "llama3.1:8b"


def test_ollama_item_runs_end_to_end(tasks_dir, tmp_path):
    if not reachable():
        pytest.skip("Ollama is not reachable at 127.0.0.1:11434")
    require_docker()

    provider = OllamaProvider(model=MODEL, num_ctx=8192)
    show = provider.show()
    if show.get("error"):
        pytest.skip(f"{MODEL} not available: {show['error']}")
    assert show["details"]["family"] == "llama"
    assert show["quantization_level"]

    cfg = RunConfig(provider="ollama", model=MODEL, model_slug="llama31-8b",
                    tasks_dir=tasks_dir, out_dir=tmp_path / "runs",
                    max_turns=12, item_wall_clock_s=420, num_ctx=8192)
    sandbox = DockerSandbox("test_ollama_smoke", tasks_dir=tasks_dir,
                            template_dir=tasks_dir / "_template")
    try:
        sandbox.start()
        ctx = ItemContext(batch_id="llama31-8b_baseline_I0_s0",
                          task_dir=tasks_dir / "t01_reverse_words",
                          item_key="t01_reverse_words", task_id="t01_reverse_words",
                          position=0, batch_size=1, I=0, f_realised=0.0, seed=0)
        rec = run_item(provider, sandbox, cfg, ctx,
                       template_dir=tasks_dir / "_template",
                       runner_path=tasks_dir / "_runner" / "run_cases.py",
                       grader_factory=docker_grader_factory())
    finally:
        sandbox.close()
        provider.close()

    validate_record(rec)
    assert set(rec) == set(RECORD_KEYS)
    # The tool loop must have exchanged real turns with the model and logged usage.
    assert rec["n_turns"] >= 1
    assert rec["provider_stop_reason"] in {"end_turn", "max_turns", "timeout"}
    assert rec["usage"]["input_tokens"] > 0
    assert rec["usage"]["output_tokens"] > 0
    assert rec["error"] is None
    assert rec["model_config"]["num_ctx"] == 8192
    assert rec["model_config"]["think"] is None     # think: false is a qwen3-only flag
    assert rec["fresh_grade"] is not None
    print(f"\n[ollama smoke] n_turns={rec['n_turns']} duration={rec['duration_s']}s "
          f"submitted={rec['submitted']} tools={[t['tool'] for t in rec['tool_calls']]} "
          f"fresh_hidden={rec['fresh_grade']['hidden_pass']} usage={rec['usage']}")
