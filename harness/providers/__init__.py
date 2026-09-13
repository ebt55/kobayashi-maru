"""Providers: one ``chat(system, messages, tools) -> Turn`` interface, four backends."""

from __future__ import annotations

from harness.providers.base import (  # noqa: F401
    MissingKeyError,
    Msg,
    Provider,
    ProviderError,
    STOP_REASONS,
    ToolCall,
    ToolSpec,
    Turn,
    blank_usage,
    merge_usage,
)

PROVIDER_NAMES = ("anthropic", "ollama", "openrouter", "openai", "fake")


def build_provider(cfg, scripts: dict | None = None) -> Provider:
    """Construct the provider named by ``cfg.provider`` (a :class:`harness.config.RunConfig`)."""
    provider = cfg.provider
    if cfg.dry_run or provider == "fake":
        from harness.providers.fake_provider import FakeProvider

        return FakeProvider(scripts=scripts, model=cfg.model)
    if provider == "anthropic":
        from harness.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(model=cfg.model, max_tokens=cfg.max_tokens,
                                 temperature=cfg.temperature)
    if provider == "ollama":
        from harness.providers.ollama_provider import OllamaProvider

        return OllamaProvider(model=cfg.model, num_ctx=cfg.num_ctx,
                              temperature=cfg.temperature)
    if provider in ("openrouter", "openai"):
        from harness.providers.openai_compat import make

        return make(provider, model=cfg.model, max_tokens=cfg.max_tokens,
                    temperature=cfg.temperature, reasoning_effort=cfg.reasoning_effort)
    raise ValueError(f"unknown provider {provider!r}; known: {PROVIDER_NAMES}")
