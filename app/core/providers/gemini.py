from __future__ import annotations

from app.core.providers.base import LLMProvider, ProviderResponse


class GeminiProvider(LLMProvider):
    """Thin wrapper around the Google GenAI SDK (``google-genai``).

    Construction is cheap and does not make a network call -- the
    ``genai.Client`` is created lazily and lazily authenticated on first use.
    Any failure during a call (missing package, bad key, network error,
    safety block, etc.) is captured in :class:`ProviderResponse.error`
    instead of raising, so the caller can fall back to the stub provider.
    """

    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        from google import genai  # imported lazily so the dependency stays optional

        self._client = genai.Client(api_key=api_key)
        self.model = model or "gemini-2.5-flash"

    def generate(self, system_instruction: str, user_prompt: str, **kwargs: object) -> ProviderResponse:
        try:
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - guarded again at construction time
            return ProviderResponse(text="", is_stub=False, model=self.model, error=str(exc))

        temperature = float(kwargs.get("temperature", 0.4))  # type: ignore[arg-type]
        max_output_tokens = int(kwargs.get("max_output_tokens", 1024))  # type: ignore[arg-type]

        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
        except Exception as exc:  # noqa: BLE001 - any SDK/network error degrades gracefully
            return ProviderResponse(text="", is_stub=False, model=self.model, error=str(exc))

        text = (getattr(response, "text", None) or "").strip()
        if not text:
            return ProviderResponse(
                text="",
                is_stub=False,
                model=self.model,
                error="Gemini returned an empty response (it may have been blocked by safety filters).",
            )
        return ProviderResponse(text=text, is_stub=False, model=self.model)
