"""Provider-neutral message objects and the one method every provider implements.

``Provider.chat(system, messages, tools) -> Turn``

``messages`` is a list of :class:`Msg`; each provider serialises it into its own wire
format and the harness serialises the same list into the SPEC.md section 3 ``transcript``
shape, so the log is identical across providers.

A refusal is an OUTCOME, never a retry: every provider maps its own refusal signal to
``stop_reason == "refusal"`` with ``refusal_details``, and the agent loop stops the item.
The harness never rewords a prompt after a refusal (plan section 9).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

#: Normalised stop reasons (SPEC.md section 3, ``provider_stop_reason``).
STOP_REASONS = (
    "end_turn", "tool_use", "refusal", "max_tokens", "max_turns", "timeout", "error",
)


class ProviderError(RuntimeError):
    """Configuration or transport failure the harness should surface, not retry blindly."""


class UnknownModelError(ProviderError):
    """The ``--model`` string is not served by this provider. Fails fast, at construction.

    ``--model`` is a pass-through string everywhere else; this is the one place it is
    checked, exactly once per provider instance.
    """

    def __init__(self, provider: str, model: str, available: list[str]) -> None:
        import difflib

        close = difflib.get_close_matches(model, available, n=10, cutoff=0.0)
        listing = "\n  ".join(close) if close else "(the provider returned no model list)"
        super().__init__(
            f"{provider} does not serve model {model!r}. Closest served ids:\n  {listing}"
        )
        self.model = model
        self.closest = close


class MissingKeyError(ProviderError):
    def __init__(self, env_name: str, provider: str) -> None:
        super().__init__(
            f"{provider} provider needs {env_name}, which is not set. "
            f"Put it in the repo-root .env (gitignored) or export it, then rerun. "
            f"No key is required for --provider fake / --dry-run."
        )
        self.env_name = env_name


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict            # JSON Schema object

    def anthropic(self) -> dict:
        return {"name": self.name, "description": self.description,
                "input_schema": self.parameters}

    def openai(self) -> dict:
        return {"type": "function",
                "function": {"name": self.name, "description": self.description,
                             "parameters": self.parameters}}

    # Ollama accepts the OpenAI function shape.
    ollama = openai


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict


@dataclass
class Msg:
    """One provider-neutral conversation entry.

    role: "system" | "user" | "assistant" | "tool"
    """

    role: str
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None
    tool_name: str | None = None

    def transcript_entry(self) -> dict:
        """The SPEC.md section 3 ``transcript`` shape."""
        return {
            "role": self.role,
            "content": self.content,
            "tool_calls": [{"id": tc.id, "name": tc.name, "args": tc.args}
                           for tc in self.tool_calls],
            "tool_call_id": self.tool_call_id,
        }


@dataclass
class Turn:
    text: str
    tool_calls: list[ToolCall]
    stop_reason: str
    usage: dict
    raw: Any = None
    refusal_details: dict | None = None

    def as_msg(self) -> Msg:
        return Msg(role="assistant", content=self.text, tool_calls=list(self.tool_calls))


def blank_usage() -> dict:
    return {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0}


def merge_usage(total: dict, add: dict | None) -> dict:
    if not add:
        return total
    for k, v in add.items():
        if isinstance(v, (int, float)):
            total[k] = total.get(k, 0) + v
    return total


class Provider:
    """Base class. Subclasses implement :meth:`chat` and set ``name``/``model``."""

    name = "base"

    def __init__(self, model: str, **_kwargs: Any) -> None:
        self.model = model

    def chat(self, system: str, messages: Iterable[Msg], tools: list[ToolSpec]) -> Turn:
        raise NotImplementedError

    def describe(self) -> dict:
        """Extra provider/model facts recorded in ``batch.json`` (e.g. `ollama show`)."""
        return {}

    def begin_item(self, item_key: str) -> None:
        """Hook: the scripted fake provider uses it to select its script."""

    def close(self) -> None:
        """Release transport resources."""


_REFUSAL_MARKERS = (
    "content_filter", "content filter", "content_policy", "content policy",
    "policy violation", "safety", "flagged", "refus", "moderation", "prohibited",
)


def looks_like_policy_block(body: str) -> bool:
    """True when an HTTP error body indicates a policy block rather than a transport fault."""
    low = (body or "").lower()
    return any(marker in low for marker in _REFUSAL_MARKERS)
