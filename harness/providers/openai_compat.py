"""Generic OpenAI-compatible chat-completions provider (raw httpx).

One implementation, two thin presets:

    ``openrouter``  https://openrouter.ai/api/v1   key env ``OPENROUTER_API_KEY``
    ``openai``      https://api.openai.com/v1      key env ``OPENAI_API_KEY``

Wire shape (OpenAI ``/chat/completions``)::

    {"model": ..., "messages": [...], "tools": [{"type": "function", "function": {...}}],
     "max_completion_tokens": 4096}                 # + "reasoning_effort" for gpt-5 family

Tool-call ids round-trip exactly as OpenAI requires: the assistant message is replayed
with its ``tool_calls`` array (``function.arguments`` is a JSON *string*), and each call
is answered by its own ``{"role": "tool", "tool_call_id": ..., "content": ...}`` message,
in the same order.

``finish_reason`` mapping: ``tool_calls`` -> tool_use, ``stop`` -> end_turn,
``length`` -> max_tokens, ``content_filter`` -> **refusal** (the item ends; the harness
never rewords and retries). An HTTP 4xx whose body indicates a policy block is also a
refusal; any other 4xx/5xx after retries is ``stop_reason == "error"``.
"""

from __future__ import annotations

import json
import os
import random
import time
from typing import Iterable

import httpx

from harness.providers.base import (
    MissingKeyError,
    Msg,
    Provider,
    ToolCall,
    ToolSpec,
    Turn,
    UnknownModelError,
    blank_usage,
    looks_like_policy_block,
)

PRESETS: dict[str, dict] = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "extra_headers": {
            "HTTP-Referer": "https://github.com/ebt55/dosecurve",
            "X-Title": "dosecurve",
        },
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "extra_headers": {},
    },
}

#: Models that accept `reasoning_effort` on chat-completions.
_REASONING_PREFIXES = ("gpt-5", "o1", "o3", "o4")

_FINISH_MAP = {
    "tool_calls": "tool_use",
    "function_call": "tool_use",
    "stop": "end_turn",
    "length": "max_tokens",
    "content_filter": "refusal",
}


class OpenAICompatProvider(Provider):
    """Provider over any OpenAI-compatible ``/chat/completions`` endpoint."""

    def __init__(self, model: str, base_url: str, api_key_env: str,
                 name: str = "openai_compat", extra_body: dict | None = None,
                 extra_headers: dict | None = None, max_tokens: int = 4096,
                 temperature: float | None = None, reasoning_effort: str | None = None,
                 timeout_s: float = 300.0, retries: int = 3,
                 verify_model: bool = True, **_kw) -> None:
        super().__init__(model)
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env
        key = (os.environ.get(api_key_env) or "").strip()
        if not key:
            raise MissingKeyError(api_key_env, name)
        self._key = key
        self.extra_body = dict(extra_body or {})
        self.extra_headers = dict(extra_headers or {})
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.reasoning_effort = reasoning_effort
        self.retries = retries
        self._client = httpx.Client(timeout=timeout_s)
        self._model_list_note = ""
        if verify_model:
            self._verify_model()

    def close(self) -> None:
        self._client.close()

    # -- model verification (once, at construction) ----------------------
    def list_models(self) -> list[str]:
        """GET {base_url}/models -> served model ids."""
        resp = self._client.get(
            f"{self.base_url}/models",
            headers={"Authorization": f"Bearer {self._key}", **self.extra_headers},
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()
        rows = data.get("data") if isinstance(data, dict) else data
        return sorted(str(r.get("id")) for r in (rows or []) if isinstance(r, dict) and r.get("id"))

    def _verify_model(self) -> None:
        try:
            served = self.list_models()
        except Exception as exc:
            # A flaky /models endpoint must not block a run; the request itself will
            # report a bad model id anyway.
            self._model_list_note = f"model list unavailable: {type(exc).__name__}: {exc}"
            return
        if served and self.model not in served:
            raise UnknownModelError(self.name, self.model, served)
        self._model_list_note = f"verified against {len(served)} served ids"

    # -- serialisation ---------------------------------------------------
    @staticmethod
    def _to_api(system: str, messages: Iterable[Msg]) -> list[dict]:
        out: list[dict] = [{"role": "system", "content": system}]
        for m in messages:
            if m.role == "tool":
                out.append({"role": "tool", "tool_call_id": m.tool_call_id,
                            "content": m.content or ""})
            elif m.role == "assistant":
                entry: dict = {"role": "assistant", "content": m.content or ""}
                if m.tool_calls:
                    entry["tool_calls"] = [
                        {"id": tc.id, "type": "function",
                         "function": {"name": tc.name,
                                      "arguments": json.dumps(tc.args, ensure_ascii=False)}}
                        for tc in m.tool_calls
                    ]
                    if not m.content:
                        entry["content"] = None
                out.append(entry)
            else:
                out.append({"role": m.role, "content": m.content or ""})
        return out

    def _supports_reasoning(self) -> bool:
        low = self.model.lower().split("/")[-1]
        return any(low.startswith(p) for p in _REASONING_PREFIXES)

    def _body(self, system: str, messages: Iterable[Msg], tools: list[ToolSpec]) -> dict:
        body: dict = {
            "model": self.model,
            "messages": self._to_api(system, messages),
            "tools": [t.openai() for t in tools],
            "max_completion_tokens": self.max_tokens,
        }
        if self.temperature is not None:
            body["temperature"] = self.temperature
        if self._supports_reasoning():
            # Verified live 2026-09-13 against gpt-5.6-luna: /v1/chat/completions rejects
            # function tools whenever reasoning is on --
            #   "Function tools with reasoning_effort are not supported for gpt-5.6-luna
            #    in /v1/chat/completions. ... or set reasoning_effort to 'none'."
            # The model's own default effort is non-none, so omitting the field 400s.
            # With tools present we therefore send an explicit effort, defaulting to
            # "none"; a caller asking for a real effort gets it (and the API's error).
            body["reasoning_effort"] = self.reasoning_effort or "none"
        body.update(self.extra_body)
        return body

    # -- the one method --------------------------------------------------
    def chat(self, system: str, messages: Iterable[Msg], tools: list[ToolSpec]) -> Turn:
        body = self._body(system, messages, tools)
        headers = {"Authorization": f"Bearer {self._key}",
                   "Content-Type": "application/json", **self.extra_headers}
        url = f"{self.base_url}/chat/completions"

        last_err = ""
        data = None
        for attempt in range(self.retries + 1):
            try:
                resp = self._client.post(url, json=body, headers=headers)
            except httpx.HTTPError as exc:
                last_err = f"{type(exc).__name__}: {exc}"
            else:
                if resp.status_code == 200:
                    data = resp.json()
                    break
                last_err = f"HTTP {resp.status_code}: {resp.text[:800]}"
                if 400 <= resp.status_code < 500 and resp.status_code != 429:
                    if looks_like_policy_block(resp.text):
                        return Turn("", [], "refusal", blank_usage(), None,
                                    {"category": "api_policy_block",
                                     "explanation": resp.text[:500]})
                    break
            if attempt < self.retries:
                time.sleep(min(2.0 * (2 ** attempt) + random.uniform(0, 1), 30.0))
        if data is None:
            return Turn("", [], "error", blank_usage(), None,
                        {"category": "api_error", "explanation": last_err[:500]})

        # Some gateways return {"error": {...}} with HTTP 200.
        if isinstance(data.get("error"), dict):
            msg = json.dumps(data["error"])[:800]
            if looks_like_policy_block(msg):
                return Turn("", [], "refusal", blank_usage(), None,
                            {"category": "api_policy_block", "explanation": msg[:500]})
            return Turn("", [], "error", blank_usage(), None,
                        {"category": "api_error", "explanation": msg[:500]})

        choices = data.get("choices") or []
        if not choices:
            return Turn("", [], "error", blank_usage(), None,
                        {"category": "api_error", "explanation": "no choices in response"})
        choice = choices[0]
        msg = choice.get("message") or {}
        text = (msg.get("content") or "") or ""
        if isinstance(text, list):  # some gateways return content parts
            text = "".join(p.get("text", "") for p in text if isinstance(p, dict))
        text = text.strip()

        calls: list[ToolCall] = []
        for i, raw in enumerate(msg.get("tool_calls") or []):
            fn = raw.get("function") or {}
            args = fn.get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args) if args.strip() else {}
                except json.JSONDecodeError:
                    args = {"_raw": args}
            calls.append(ToolCall(id=raw.get("id") or f"call_{i}",
                                  name=fn.get("name") or "", args=dict(args or {})))

        finish = choice.get("finish_reason") or ("tool_calls" if calls else "stop")
        stop = _FINISH_MAP.get(finish, "end_turn")
        if calls and stop == "end_turn":
            stop = "tool_use"

        refusal = None
        if stop == "refusal":
            refusal = {"category": "content_filter",
                       "explanation": (msg.get("refusal") or finish or "")[:500]}
        elif msg.get("refusal"):
            stop = "refusal"
            refusal = {"category": "model_refusal", "explanation": str(msg["refusal"])[:500]}

        u = data.get("usage") or {}
        details = u.get("prompt_tokens_details") or {}
        usage = {
            "input_tokens": int(u.get("prompt_tokens") or 0),
            "output_tokens": int(u.get("completion_tokens") or 0),
            "cache_read_input_tokens": int(details.get("cached_tokens") or 0),
        }
        rt = (u.get("completion_tokens_details") or {}).get("reasoning_tokens")
        if rt is not None:
            usage["reasoning_tokens"] = int(rt)
        return Turn(text, calls, stop, usage, raw=None, refusal_details=refusal)

    def describe(self) -> dict:
        return {"base_url": self.base_url, "api_key_env": self.api_key_env,
                "max_tokens": self.max_tokens,
                "reasoning_effort": self.reasoning_effort if self._supports_reasoning() else None,
                "extra_body": self.extra_body,
                "extra_headers": sorted(self.extra_headers),
                "model_verification": self._model_list_note}


def make(preset: str, model: str, **kwargs) -> OpenAICompatProvider:
    """Build a provider from a preset name (``openrouter`` / ``openai``)."""
    if preset not in PRESETS:
        raise ValueError(f"unknown preset {preset!r}; known: {sorted(PRESETS)}")
    cfg = PRESETS[preset]
    return OpenAICompatProvider(
        model=model,
        base_url=kwargs.pop("base_url", None) or cfg["base_url"],
        api_key_env=kwargs.pop("api_key_env", None) or cfg["api_key_env"],
        name=preset,
        extra_headers={**cfg.get("extra_headers", {}), **kwargs.pop("extra_headers", {})},
        **kwargs,
    )
