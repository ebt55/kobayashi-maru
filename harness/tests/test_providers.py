"""Provider wire shapes and key handling -- no network, no API key."""

from __future__ import annotations

import json

import pytest

from harness.agent import TOOLS
from harness.providers import build_provider
from harness.providers.anthropic_provider import AnthropicProvider
from harness.providers.base import (
    MissingKeyError,
    Msg,
    ToolCall,
    ToolSpec,
    UnknownModelError,
    looks_like_policy_block,
)
from harness.providers.fake_provider import FakeProvider
from harness.providers.ollama_provider import OllamaProvider
from harness.providers.openai_compat import PRESETS, OpenAICompatProvider, make
from harness.config import RunConfig


CONVO = [
    Msg(role="user", content="do the item"),
    Msg(role="assistant", content="looking",
        tool_calls=[ToolCall(id="call_1", name="bash", args={"command": "ls"})]),
    Msg(role="tool", content="solution.py\ntests", tool_call_id="call_1", tool_name="bash"),
    Msg(role="assistant", content="",
        tool_calls=[ToolCall(id="call_2", name="submit", args={"summary": "done"})]),
    Msg(role="tool", content="Item submitted.", tool_call_id="call_2", tool_name="submit"),
]


# ------------------------------------------------------------------ tool schemas

def test_the_five_tools_and_their_required_args():
    assert [t.name for t in TOOLS] == ["bash", "read_file", "write_file", "run_tests", "submit"]
    by_name = {t.name: t for t in TOOLS}
    assert by_name["bash"].parameters["required"] == ["command"]
    assert by_name["read_file"].parameters["required"] == ["path"]
    assert by_name["write_file"].parameters["required"] == ["path", "content"]
    assert by_name["run_tests"].parameters["required"] == []
    assert by_name["submit"].parameters["required"] == ["summary"]


def test_tool_spec_renders_both_dialects():
    spec = ToolSpec("bash", "run it", {"type": "object", "properties": {}})
    assert spec.anthropic() == {"name": "bash", "description": "run it",
                                "input_schema": {"type": "object", "properties": {}}}
    oa = spec.openai()
    assert oa["type"] == "function" and oa["function"]["name"] == "bash"
    assert "parameters" in oa["function"]


# ------------------------------------------------------------------ serialisation

def test_anthropic_serialisation_blocks_and_grouped_tool_results():
    api = AnthropicProvider._to_api(CONVO)
    assert api[0] == {"role": "user", "content": "do the item"}
    assistant = api[1]
    assert assistant["role"] == "assistant"
    assert assistant["content"][0] == {"type": "text", "text": "looking"}
    assert assistant["content"][1] == {"type": "tool_use", "id": "call_1", "name": "bash",
                                       "input": {"command": "ls"}}
    # tool results become a user message of tool_result blocks
    assert api[2]["role"] == "user"
    assert api[2]["content"][0]["type"] == "tool_result"
    assert api[2]["content"][0]["tool_use_id"] == "call_1"
    # an assistant turn with no text still carries its tool_use block
    assert api[3]["content"][0] == {"type": "tool_use", "id": "call_2", "name": "submit",
                                    "input": {"summary": "done"}}


def test_ollama_serialisation_matches_the_verified_shape():
    api = OllamaProvider._to_api(CONVO)
    assert api[1] == {
        "role": "assistant", "content": "looking",
        "tool_calls": [{"id": "call_1",
                        "function": {"index": 0, "name": "bash",
                                     "arguments": {"command": "ls"}}}],
    }
    # the tool result is its own message with tool_name + tool_call_id
    assert api[2] == {"role": "tool", "content": "solution.py\ntests",
                      "tool_name": "bash", "tool_call_id": "call_1"}


def test_openai_serialisation_roundtrips_ids_and_stringified_arguments():
    api = OpenAICompatProvider._to_api("RULES", CONVO)
    assert api[0] == {"role": "system", "content": "RULES"}
    assistant = api[2]
    assert assistant["tool_calls"][0]["id"] == "call_1"
    assert assistant["tool_calls"][0]["type"] == "function"
    assert json.loads(assistant["tool_calls"][0]["function"]["arguments"]) == {"command": "ls"}
    assert api[3] == {"role": "tool", "tool_call_id": "call_1",
                      "content": "solution.py\ntests"}
    # an assistant turn with no text sends content: null, as OpenAI requires
    assert api[4]["content"] is None


def test_openrouter_preset_headers_and_key_env():
    preset = PRESETS["openrouter"]
    assert preset["base_url"] == "https://openrouter.ai/api/v1"
    assert preset["api_key_env"] == "OPENROUTER_API_KEY"
    assert preset["extra_headers"]["HTTP-Referer"] == "https://github.com/ebt55/dosecurve"
    assert preset["extra_headers"]["X-Title"] == "dosecurve"
    assert PRESETS["openai"]["base_url"] == "https://api.openai.com/v1"
    assert PRESETS["openai"]["api_key_env"] == "OPENAI_API_KEY"


def test_reasoning_effort_only_for_the_gpt5_family(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-used")
    p = OpenAICompatProvider(model="gpt-5.6-luna", base_url="https://example.invalid/v1",
                             api_key_env="OPENAI_API_KEY", reasoning_effort="low",
                             verify_model=False)
    assert p._body("RULES", CONVO, TOOLS)["reasoning_effort"] == "low"

    # gpt-5 family + function tools on /v1/chat/completions requires an EXPLICIT
    # reasoning_effort; the harness defaults it to "none" (see the note in _body).
    d = OpenAICompatProvider(model="gpt-5.6-luna", base_url="https://example.invalid/v1",
                             api_key_env="OPENAI_API_KEY", verify_model=False)
    assert d._body("RULES", CONVO, TOOLS)["reasoning_effort"] == "none"

    q = OpenAICompatProvider(model="z-ai/glm-5.3-flash", base_url="https://example.invalid/v1",
                             api_key_env="OPENAI_API_KEY", reasoning_effort="low",
                             verify_model=False)
    assert "reasoning_effort" not in q._body("RULES", CONVO, TOOLS)


def test_ollama_think_false_only_for_qwen3():
    q = OllamaProvider(model="qwen3:14b")
    assert q._body("RULES", CONVO, TOOLS)["think"] is False
    assert q._body("RULES", CONVO, TOOLS)["options"]["num_ctx"] == 8192
    assert q._body("RULES", CONVO, TOOLS)["keep_alive"] == "10m"
    assert q._body("RULES", CONVO, TOOLS)["stream"] is False
    q.close()

    l = OllamaProvider(model="llama3.1:8b", num_ctx=4096)
    body = l._body("RULES", CONVO, TOOLS)
    assert "think" not in body
    assert body["options"]["num_ctx"] == 4096
    assert body["messages"][0] == {"role": "system", "content": "RULES"}
    l.close()


# ------------------------------------------------------------------ key handling

def test_missing_key_message_is_clear(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(MissingKeyError) as exc:
        AnthropicProvider(model="claude-haiku-4-5-20251001")
    assert "ANTHROPIC_API_KEY" in str(exc.value) and ".env" in str(exc.value)

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(MissingKeyError) as exc:
        make("openrouter", model="z-ai/glm-5.3-flash")
    assert "OPENROUTER_API_KEY" in str(exc.value)

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(MissingKeyError):
        make("openai", model="gpt-5.6-luna")


def test_fake_provider_needs_no_key(monkeypatch):
    for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    cfg = RunConfig(provider="fake", dry_run=True)
    provider = build_provider(cfg, scripts={})
    assert isinstance(provider, FakeProvider)


def test_unknown_model_error_lists_close_ids():
    err = UnknownModelError("anthropic", "claude-haiku-4-5",
                            ["claude-haiku-4-5-20251001", "claude-sonnet-5", "claude-opus-5"])
    assert "claude-haiku-4-5-20251001" in str(err)
    assert len(err.closest) <= 10


def test_policy_block_sniffer():
    assert looks_like_policy_block('{"error": {"code": "content_filter"}}')
    assert looks_like_policy_block("request blocked by our moderation system")
    assert not looks_like_policy_block('{"error": {"code": "rate_limit_exceeded"}}')


# ------------------------------------------------------------------ fake replay

def test_fake_provider_replays_per_item():
    scripts = {
        "a": [{"tool": "bash", "args": {"command": "ls"}},
              {"tool": "submit", "args": {"summary": "a done"}}],
        "b": [{"tool": "submit", "args": {"summary": "b done"}}],
    }
    p = FakeProvider(scripts)
    p.begin_item("a")
    t1 = p.chat("RULES", [], TOOLS)
    assert t1.stop_reason == "tool_use" and t1.tool_calls[0].name == "bash"
    t2 = p.chat("RULES", [], TOOLS)
    assert t2.tool_calls[0].name == "submit"
    p.begin_item("b")
    t3 = p.chat("RULES", [], TOOLS)
    assert t3.tool_calls[0].args == {"summary": "b done"}
