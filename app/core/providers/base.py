from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class ProviderResponse:
    """Normalized result returned by any LLM provider."""

    text: str
    is_stub: bool
    model: str
    error: str | None = None


class LLMProvider(ABC):
    """Common interface every model provider must implement.

    Keeping this interface tiny makes it easy to add new providers
    (Anthropic, OpenAI, local models, ...) later without touching the
    conversation service or any of the Streamlit screens.
    """

    name: str = "base"

    @abstractmethod
    def generate(self, system_instruction: str, user_prompt: str, **kwargs: object) -> ProviderResponse:
        """Generate a response for ``user_prompt`` guided by ``system_instruction``.

        Implementations must never raise for "expected" failure modes
        (missing key, network error, etc.) -- they should return a
        ``ProviderResponse`` with ``error`` set so the caller can decide
        how to degrade gracefully.
        """
        raise NotImplementedError
