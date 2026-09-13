"""Anthropic provider -- official `anthropic` Python SDK 1.x, manual tool loop.

Manual (not `client.beta.messages.tool_runner`) because every request and every tool
result has to be logged into the item record, and the same loop has to serve Ollama and
the OpenAI-compatible providers.

Shapes used (from the bundled claude-api skill, python/README.md + tool-use.md):
  * ``system`` is a list of one text block carrying ``cache_control: {"type": "ephemeral"}``
    so the RULES prefix is cached across the whole batch.
  * ``tools`` entries are ``{"name", "description", "input_schema"}``.
  * an assistant turn is replayed as ``{"role": "assistant", "content": [blocks...]}``
    with ``{"type": "tool_use", "id", "name", "input"}`` blocks;
  * tool results go back in a ``user`` message as ``{"type": "tool_result",
    "tool_use_id", "content"}`` blocks.
  * ``stop_reason == "refusal"`` carries ``stop_details.category`` / ``.explanation``.
No ``thinking`` parameter: the agent model is `claude-haiku-4-5`, chosen for cost by the plan.
"""

from __future__ import annotations

import random
import time
from typing import Iterable

from harness.providers.base import (
    MissingKeyError,
    Msg,
    Provider,
    ProviderError,
    ToolCall,
    ToolSpec,
    Turn,
    UnknownModelError,
    blank_usage,
)

ENV_KEY = "ANTHROPIC_API_KEY"
#: This account serves the dated id, not the bare alias -- `--model` is a pass-through
#: string and is checked once against `client.models.list()` at construction.
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_STOP_MAP = {
    "end_turn": "end_turn",
    "tool_use": "tool_use",
    "max_tokens": "max_tokens",
    "stop_sequence": "end_turn",
    "refusal": "refusal",
    "pause_turn": "tool_use",
}


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, model: str = DEFAULT_MODEL, max_tokens: int = 4096,
                 temperature: float | None = None, sdk_retries: int = 4,
                 own_retries: int = 2, timeout_s: float = 300.0,
                 verify_model: bool = True, cache_last_user: bool = False, **_kw) -> None:
        super().__init__(model)
        import os

        key = (os.environ.get(ENV_KEY) or "").strip()
        if not key:
            raise MissingKeyError(ENV_KEY, "anthropic")
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise ProviderError("the `anthropic` package is not installed") from exc
        self._anthropic = anthropic
        self._client = anthropic.Anthropic(max_retries=sdk_retries, timeout=timeout_s)
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.own_retries = own_retries
        # Continuous arm only: also put a cache breakpoint on the last user block, so the
        # whole growing conversation prefix is cached, not just the system prompt. OFF by
        # default -- the per-item arms send a fresh short context and would only pay the
        # cache-write premium. Leaving it off keeps their request bytes unchanged.
        self.cache_last_user = bool(cache_last_user)
        self._model_list_note = ""
        if verify_model:
            self._verify_model()

    # -- model verification (once, at construction) ----------------------
    def list_models(self) -> list[str]:
        return sorted(m.id for m in self._client.models.list(limit=100))

    def _verify_model(self) -> None:
        try:
            served = self.list_models()
        except Exception as exc:
            self._model_list_note = f"model list unavailable: {type(exc).__name__}: {exc}"
            return
        if served and self.model not in served:
            raise UnknownModelError("anthropic", self.model, served)
        self._model_list_note = f"verified against {len(served)} served ids"

    # -- serialisation ---------------------------------------------------
    @staticmethod
    def _to_api(messages: Iterable[Msg]) -> list[dict]:
        out: list[dict] = []
        pending_results: list[dict] = []

        def flush() -> None:
            if pending_results:
                out.append({"role": "user", "content": list(pending_results)})
                pending_results.clear()

        for m in messages:
            if m.role == "tool":
                pending_results.append({
                    "type": "tool_result",
                    "tool_use_id": m.tool_call_id,
                    "content": m.content or "",
                })
                continue
            flush()
            if m.role == "assistant":
                blocks: list[dict] = []
                if m.content:
                    blocks.append({"type": "text", "text": m.content})
                for tc in m.tool_calls:
                    blocks.append({"type": "tool_use", "id": tc.id,
                                   "name": tc.name, "input": tc.args})
                if not blocks:
                    blocks.append({"type": "text", "text": "(no content)"})
                out.append({"role": "assistant", "content": blocks})
            else:
                out.append({"role": "user", "content": m.content or ""})
        flush()
        return out

    @staticmethod
    def _mark_last_user_cacheable(api_messages: list[dict]) -> list[dict]:
        """Put a cache breakpoint on the final user turn (continuous arm).

        Caching is a prefix match, so a breakpoint at the end of the conversation so far
        caches everything before it; the next call re-reads that prefix instead of paying
        full input price for it.
        """
        for msg in reversed(api_messages):
            if msg.get("role") != "user":
                continue
            content = msg.get("content")
            if isinstance(content, str):
                msg["content"] = [{"type": "text", "text": content,
                                   "cache_control": {"type": "ephemeral"}}]
            elif isinstance(content, list) and content:
                content[-1] = {**content[-1], "cache_control": {"type": "ephemeral"}}
            break
        return api_messages

    # -- the one method --------------------------------------------------
    def chat(self, system: str, messages: Iterable[Msg], tools: list[ToolSpec]) -> Turn:
        a = self._anthropic
        api_messages = self._to_api(messages)
        if self.cache_last_user:
            api_messages = self._mark_last_user_cacheable(api_messages)
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": [{"type": "text", "text": system,
                        "cache_control": {"type": "ephemeral"}}],
            "messages": api_messages,
            "tools": [t.anthropic() for t in tools],
        }
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature

        last_exc: Exception | None = None
        for attempt in range(self.own_retries + 1):
            try:
                resp = self._client.messages.create(**kwargs)
                break
            except a.RateLimitError as exc:
                last_exc = exc
            except a.APIStatusError as exc:
                if exc.status_code >= 500 or exc.status_code == 429:
                    last_exc = exc
                else:
                    body = str(getattr(exc, "message", "") or exc)
                    from harness.providers.base import looks_like_policy_block
                    if looks_like_policy_block(body):
                        return Turn("", [], "refusal", blank_usage(), None,
                                    {"category": "api_policy_block",
                                     "explanation": body[:500]})
                    return Turn("", [], "error", blank_usage(), None,
                                {"category": "api_error", "explanation": body[:500]})
            except a.APIConnectionError as exc:
                last_exc = exc
            if attempt < self.own_retries:
                time.sleep(min(2.0 * (2 ** attempt) + random.uniform(0, 1), 30.0))
        else:
            return Turn("", [], "error", blank_usage(), None,
                        {"category": "api_error", "explanation": str(last_exc)[:500]})

        text_parts: list[str] = []
        calls: list[ToolCall] = []
        for block in resp.content or []:
            btype = getattr(block, "type", None)
            if btype == "text":
                text_parts.append(block.text)
            elif btype == "tool_use":
                calls.append(ToolCall(id=block.id, name=block.name,
                                      args=dict(block.input or {})))

        stop = _STOP_MAP.get(resp.stop_reason or "", "end_turn")
        if calls and stop == "end_turn":
            stop = "tool_use"

        refusal = None
        if stop == "refusal":
            details = getattr(resp, "stop_details", None)
            refusal = {
                "category": getattr(details, "category", None) or "unspecified",
                "explanation": getattr(details, "explanation", None) or "",
            }

        u = resp.usage
        usage = {
            "input_tokens": int(getattr(u, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(u, "output_tokens", 0) or 0),
            "cache_read_input_tokens": int(getattr(u, "cache_read_input_tokens", 0) or 0),
            "cache_creation_input_tokens": int(getattr(u, "cache_creation_input_tokens", 0) or 0),
        }
        return Turn("\n".join(text_parts).strip(), calls, stop, usage,
                    raw=None, refusal_details=refusal)

    def describe(self) -> dict:
        return {"sdk": "anthropic", "sdk_version": getattr(self._anthropic, "__version__", "?"),
                "max_tokens": self.max_tokens,
                "model_verification": self._model_list_note}
