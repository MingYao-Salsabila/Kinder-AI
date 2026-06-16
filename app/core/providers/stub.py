from __future__ import annotations

import textwrap

from app.core.providers.base import LLMProvider, ProviderResponse


class StubProvider(LLMProvider):
    """Deterministic, fully offline provider.

    Used whenever ``GEMINI_USE_STUB`` is true, no real API key is configured,
    or the live provider returned an error. It never makes network calls, so
    the whole app -- including retrieval, quizzes, and progress tracking --
    can be demoed end-to-end with zero configuration.
    """

    name = "stub"

    def __init__(self, model: str = "stub") -> None:
        self.model = model or "stub"

    def generate(self, system_instruction: str, user_prompt: str, **kwargs: object) -> ProviderResponse:
        mode = str(kwargs.get("mode") or "general")
        learner_name = kwargs.get("learner_name")
        snippets = kwargs.get("snippets") or []

        text = _render(mode=mode, prompt=user_prompt, snippets=snippets, learner_name=learner_name)
        return ProviderResponse(text=text, is_stub=True, model=self.model)


def _render(mode: str, prompt: str, snippets: list[dict], learner_name: object) -> str:
    prompt = (prompt or "").strip() or "your question"
    context = _format_snippets(snippets)

    if mode == "kid":
        greeting = f"Hi {learner_name}! " if learner_name else "Hi there! "
        lines = [f"{greeting}Great question about **{prompt}**."]
        if context:
            lines.append("")
            lines.append("Here is what our lesson notes say:")
            lines.append(context)
        else:
            lines.append("")
            lines.append(
                "Here is a simple way to think about it: break the idea into small "
                "steps, picture it in your head, and try saying it out loud in your "
                "own words."
            )
        lines.append("")
        lines.append("Want to try a quiz about this, or ask me to explain it a different way?")
        return "\n".join(lines)

    if mode == "teacher":
        lines = [f"**Lesson draft: {prompt}**", ""]
        if context:
            lines.append("Grounded in the curated lesson notes below:")
            lines.append(context)
            lines.append("")
        lines.append(
            "**Explanation** — introduce the idea in plain language and connect it "
            "to something students already know."
        )
        lines.append("**Example** — walk through one worked example or a short demonstration.")
        lines.append(
            "**Check for understanding** — ask students to summarize the idea in one "
            "sentence or answer a quick question."
        )
        return "\n".join(lines)

    if mode == "admin":
        lines = [
            "**Admin review (offline stub)**",
            f"- Prompt received: {prompt}",
            "- Status: safe for review.",
            "- Suggested follow-up: inspect logs, confirm routing, and review learner context.",
        ]
        return "\n".join(lines)

    return f"Stub response for {mode}: {prompt}"


def _format_snippets(snippets: list[dict]) -> str:
    if not snippets:
        return ""
    parts = []
    for snippet in snippets[:3]:
        title = snippet.get("title", "Lesson note")
        content = (snippet.get("content") or "").strip()
        excerpt = textwrap.shorten(content, width=220, placeholder="…")
        parts.append(f"> **{title}** — {excerpt}")
    return "\n".join(parts)
