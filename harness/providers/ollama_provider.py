"""Ollama provider -- raw httpx against POST /api/chat, stream: false.

WIRE SHAPE, verified live against `llama3.1:8b` on Ollama 0.32.15 (2026-09-13). The
request body is::

    {"model": "llama3.1:8b", "messages": [...], "tools": [...], "stream": false,
     "options": {"num_ctx": 8192}, "keep_alive": "10m"}          # + "think": false for qwen3*

The assistant turn comes back as (note: `arguments` is a JSON OBJECT, not a string, and
`function` carries an `index`)::

    {"message": {"role": "assistant", "content": "",
                 "tool_calls": [{"id": "call_7q5nckpy",
                                 "function": {"index": 0, "name": "bash",
                                              "arguments": {"command": "ls"}}}]},
     "done_reason": "stop", "prompt_eval_count": 235, "eval_count": 35}

The assistant turn is echoed back verbatim, and each tool result goes back as its OWN
message -- THIS is the shape that worked (HTTP 200, model continued correctly)::

    {"role": "tool", "content": "<tool output text>",
     "tool_name": "bash", "tool_call_id": "call_7q5nckpy"}

A model may emit SEVERAL tool calls in one turn (llama3.1:8b did on the very first probe),
so the agent loop must execute them in order and reply with one `tool` message per call.
"""

from __future__ import annotations

import json
import random
import time
from typing import Iterable

import httpx

from harness.providers.base import (
    Msg,
    Provider,
    ToolCall,
    ToolSpec,
    Turn,
    blank_usage,
)

DEFAULT_HOST = "http://127.0.0.1:11434"


class OllamaProvider(Provider):
    name = "ollama"

    def __init__(self, model: str, host: str = DEFAULT_HOST, num_ctx: int = 8192,
                 keep_alive: str = "10m", temperature: float | None = None,
                 timeout_s: float = 900.0, retries: int = 2, **_kw) -> None:
        super().__init__(model)
        self.host = host.rstrip("/")
        self.num_ctx = num_ctx
        self.keep_alive = keep_alive
        self.temperature = temperature
        self.retries = retries
        self._client = httpx.Client(timeout=timeout_s)

    def close(self) -> None:
        self._client.close()

    # -- serialisation ---------------------------------------------------
    @staticmethod
    def _to_api(messages: Iterable[Msg]) -> list[dict]:
        out: list[dict] = []
        for m in messages:
            if m.role == "tool":
                entry = {"role": "tool", "content": m.content or ""}
                if m.tool_name:
                    entry["tool_name"] = m.tool_name
                if m.tool_call_id:
                    entry["tool_call_id"] = m.tool_call_id
                out.append(entry)
            elif m.role == "assistant":
                entry = {"role": "assistant", "content": m.content or ""}
                if m.tool_calls:
                    entry["tool_calls"] = [
                        {"id": tc.id,
                         "function": {"index": i, "name": tc.name, "arguments": tc.args}}
                        for i, tc in enumerate(m.tool_calls)
                    ]
                out.append(entry)
            else:
                out.append({"role": m.role, "content": m.content or ""})
        return out

    def _body(self, system: str, messages: Iterable[Msg], tools: list[ToolSpec]) -> dict:
        options = {"num_ctx": self.num_ctx}
        if self.temperature is not None:
            options["temperature"] = self.temperature
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *self._to_api(messages)],
            "tools": [t.openai() for t in tools],
            "stream": False,
            "options": options,
            "keep_alive": self.keep_alive,
        }
        if self.model.startswith("qwen3"):
            # Reasoning mode OFF (plan section 8 / IG runbook): qwen3 otherwise emits a
            # long <think> stream that blows the 10 GB card's KV budget.
            body["think"] = False
        return body

    # -- the one method --------------------------------------------------
    def chat(self, system: str, messages: Iterable[Msg], tools: list[ToolSpec]) -> Turn:
        body = self._body(system, messages, tools)
        last_err = ""
        data = None
        for attempt in range(self.retries + 1):
            try:
                resp = self._client.post(f"{self.host}/api/chat", json=body)
            except httpx.HTTPError as exc:
                last_err = f"{type(exc).__name__}: {exc}"
            else:
                if resp.status_code == 200:
                    data = resp.json()
                    break
                last_err = f"HTTP {resp.status_code}: {resp.text[:500]}"
                if resp.status_code < 500 and resp.status_code != 429:
                    break
            if attempt < self.retries:
                time.sleep(min(2.0 * (2 ** attempt) + random.uniform(0, 1), 30.0))
        if data is None:
            return Turn("", [], "error", blank_usage(), None,
                        {"category": "api_error", "explanation": last_err[:500]})

        msg = data.get("message") or {}
        text = (msg.get("content") or "").strip()
        calls: list[ToolCall] = []
        for i, raw in enumerate(msg.get("tool_calls") or []):
            fn = raw.get("function") or {}
            args = fn.get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"_raw": args}
            calls.append(ToolCall(id=raw.get("id") or f"call_{i}",
                                  name=fn.get("name") or "", args=dict(args or {})))

        done_reason = data.get("done_reason") or "stop"
        if done_reason == "length":
            stop = "max_tokens"
        elif calls:
            stop = "tool_use"
        else:
            stop = "end_turn"

        usage = {
            "input_tokens": int(data.get("prompt_eval_count") or 0),
            "output_tokens": int(data.get("eval_count") or 0),
            "cache_read_input_tokens": 0,
            "total_duration_ns": int(data.get("total_duration") or 0),
        }
        return Turn(text, calls, stop, usage, raw=None)

    # -- provenance ------------------------------------------------------
    def show(self) -> dict:
        """POST /api/show -- recorded in batch.json (details / quantization / size)."""
        try:
            resp = self._client.post(f"{self.host}/api/show", json={"model": self.model},
                                     timeout=60.0)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            return {"error": f"{type(exc).__name__}: {exc}"}
        details = data.get("details") or {}
        info = data.get("model_info") or {}
        return {
            "details": details,
            "quantization_level": details.get("quantization_level"),
            "parameter_size": details.get("parameter_size"),
            "family": details.get("family"),
            "format": details.get("format"),
            "capabilities": data.get("capabilities"),
            "context_length": info.get(f"{details.get('family', '')}.context_length"),
            "parameters": (data.get("parameters") or "")[:2000],
        }

    def describe(self) -> dict:
        return {"host": self.host, "num_ctx": self.num_ctx, "keep_alive": self.keep_alive,
                "think": False if self.model.startswith("qwen3") else None,
                "ollama_show": self.show()}


def reachable(host: str = DEFAULT_HOST, timeout_s: float = 3.0) -> bool:
    try:
        r = httpx.get(f"{host.rstrip('/')}/api/version", timeout=timeout_s)
        return r.status_code == 200
    except Exception:
        return False
