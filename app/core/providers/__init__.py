from __future__ import annotations

from app.config import AppSettings
from app.core.providers.base import LLMProvider, ProviderResponse
from app.core.providers.stub import StubProvider

__all__ = ["LLMProvider", "ProviderResponse", "StubProvider", "get_provider"]


def get_provider(settings: AppSettings) -> LLMProvider:
    """Return the LLM provider to use for ``settings``.

    Falls back to :class:`StubProvider` whenever the real provider cannot be
    used -- ``GEMINI_USE_STUB=true``, a missing/placeholder API key, or the
    optional ``google-genai`` package not being installed. This keeps the
    rest of the app (and any demo) working with zero configuration.

    To add another provider (Anthropic, OpenAI, a local model, ...), create
    a module under ``app/core/providers/`` that implements
    :class:`LLMProvider`, then branch on a new setting here.
    """

    if not settings.is_live:
        return StubProvider(model="stub")

    try:
        from app.core.providers.gemini import GeminiProvider

        return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
    except Exception:
        # Missing dependency, bad key format, etc. -- degrade to the stub
        # rather than crashing the whole app.
        return StubProvider(model="stub")
