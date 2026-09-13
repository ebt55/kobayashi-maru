"""One real item per hosted provider (marked ``live`` -- spends hosted tokens).

Four items total, one fixture task each, to confirm the request/response shape end to
end. Skips any provider whose key is absent. Never run in bulk: the pilot is the
orchestrator's call.
"""

from __future__ import annotations

import os

import pytest

from harness.agent import ItemContext, run_item
from harness.config import RunConfig, load_env
from harness.grade import docker_grader_factory
from harness.providers.anthropic_provider import AnthropicProvider
from harness.providers.base import MissingKeyError
from harness.providers.openai_compat import make
from harness.records import RECORD_KEYS, validate_record
from harness.sandbox import DockerSandbox
from harness.tests.conftest import require_docker

pytestmark = pytest.mark.live

CASES = [
    ("openai", "gpt-5.6-luna", "OPENAI_API_KEY"),
    ("anthropic", "claude-haiku-4-5-20251001", "ANTHROPIC_API_KEY"),
    ("openrouter", "z-ai/glm-5.3-flash", "OPENROUTER_API_KEY"),
    ("openrouter", "deepseek/deepseek-v4.1-flash", "OPENROUTER_API_KEY"),
]


def _provider(kind: str, model: str):
    if kind == "anthropic":
        return AnthropicProvider(model=model, max_tokens=4096)
    return make(kind, model=model, max_tokens=4096)


@pytest.mark.parametrize("kind,model,key_env", CASES,
                         ids=[f"{k}:{m}" for k, m, _ in CASES])
def test_one_live_item(kind, model, key_env, tasks_dir, tmp_path):
    load_env()
    if not (os.environ.get(key_env) or "").strip():
        pytest.skip(f"{key_env} is not set")
    require_docker()

    try:
        provider = _provider(kind, model)
    except MissingKeyError as exc:
        pytest.skip(str(exc))

    cfg = RunConfig(provider=kind, model=model, model_slug=model.split("/")[-1],
                    tasks_dir=tasks_dir, out_dir=tmp_path / "runs",
                    max_turns=12, item_wall_clock_s=420)
    sandbox = DockerSandbox(f"live_{kind}_{abs(hash(model)) % 10**6}", tasks_dir=tasks_dir,
                            template_dir=tasks_dir / "_template")
    try:
        sandbox.start()
        ctx = ItemContext(batch_id=f"{cfg.model_slug}_baseline_I0_s0",
                          task_dir=tasks_dir / "t01_reverse_words",
                          item_key="t01_reverse_words", task_id="t01_reverse_words",
                          position=0, batch_size=1, I=0, f_realised=0.0, seed=0)
        rec = run_item(provider, sandbox, cfg, ctx,
                       template_dir=tasks_dir / "_template",
                       runner_path=tasks_dir / "_runner" / "run_cases.py",
                       grader_factory=docker_grader_factory())
    finally:
        sandbox.close()
        try:
            provider.close()
        except Exception:
            pass

    validate_record(rec)
    assert set(rec) == set(RECORD_KEYS)
    print(
        f"\n[live {kind}/{model}] stop={rec['provider_stop_reason']} "
        f"submitted={rec['submitted']} n_turns={rec['n_turns']} "
        f"duration={rec['duration_s']}s usage={rec['usage']} "
        f"tools={[t['tool'] for t in rec['tool_calls']]} "
        f"fresh_hidden={rec['fresh_grade']['hidden_pass']} "
        f"probe={rec['fresh_grade']['probe_pass']} "
        f"refusal={rec['refusal_details']} error={rec['error']}"
    )
    assert rec["error"] is None, rec["error"]
    assert rec["provider_stop_reason"] in {"end_turn", "max_turns", "timeout", "refusal"}
    assert rec["usage"]["input_tokens"] > 0
    assert rec["n_turns"] >= 1
