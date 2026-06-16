from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache

from app.config import AppSettings
from app.core.models import LearnerProfile, Mode
from app.core.providers import LLMProvider, get_provider
from app.core.providers.stub import StubProvider
from app.core.rag import RetrievedSnippet, retrieve_approved_snippets
from app.core.safety import check_prompt_safety

_REFUSAL_TEXT = (
    "I can't help with that question here. Let's pick something about learning -- "
    "try asking about science, reading, math, or nature instead!"
)

_BASE_RULES = (
    "You are KinderAi, a friendly learning assistant built for the MajuBarengAi "
    "programme (Hacktiv8 with Google). Always be encouraging, honest, and "
    "age-appropriate. If you are unsure about something, say so plainly instead "
    "of guessing, and keep responses focused on learning."
)

_MODE_INSTRUCTIONS: dict[str, str] = {
    "kid": (
        "Audience: a child, roughly 6-12 years old.\n"
        "- Use short sentences and simple, everyday words.\n"
        "- Keep the whole answer under about 120 words unless asked for more detail.\n"
        "- Be warm and encouraging, like a patient tutor.\n"
        "- Never discuss violence, weapons, self-harm, drugs, or adult topics; "
        "gently steer the conversation back to a school subject instead.\n"
        "- End with a short follow-up question or a suggestion for what to try next."
    ),
    "teacher": (
        "Audience: a teacher or instructional staff member.\n"
        "- Produce classroom-ready material.\n"
        "- Structure the answer with a short Explanation, one concrete Example, "
        "and a brief \"Check for understanding\" question.\n"
        "- If lesson notes are provided below, ground your answer in them and "
        "mention which note you drew from."
    ),
    "admin": (
        "Audience: a programme administrator reviewing the assistant.\n"
        "- Be concise and operational.\n"
        "- Summarize the request, note anything that needs follow-up, and "
        "suggest a next action."
    ),
}


@dataclass(slots=True)
class ConversationResponse:
    text: str
    mode: str
    is_stub: bool = True
    sources: list[str] = field(default_factory=list)
    provider_name: str = "stub"
    notice: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationService:
    """Coordinates safety checks, retrieval, and the LLM provider for one turn.

    A single instance is cheap to create (provider construction makes no
    network calls), but :func:`get_conversation_service` caches one instance
    per :class:`AppSettings` so Streamlit reruns reuse the same provider.
    """

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.provider: LLMProvider = get_provider(settings)
        self._fallback = StubProvider(model="stub")

    def respond(
        self,
        prompt: str,
        mode: Mode | str,
        audience: str = "general",
        learner: LearnerProfile | None = None,
        use_retrieval: bool | None = None,
    ) -> ConversationResponse:
        """Generate a response for ``prompt`` in the given ``mode``.

        Always returns a usable :class:`ConversationResponse`, even when the
        live provider fails -- in that case ``notice`` explains the
        degradation and ``is_stub`` is ``True``.
        """

        safety = check_prompt_safety(prompt, audience=audience)
        if not safety.allowed:
            return ConversationResponse(text=_REFUSAL_TEXT, mode=str(mode), is_stub=True, provider_name="safety")

        cleaned = safety.redacted_prompt
        if use_retrieval is None:
            use_retrieval = mode in {"kid", "teacher"}

        snippets: list[RetrievedSnippet] = []
        if use_retrieval:
            snippets = retrieve_approved_snippets(cleaned, self.settings, top_k=3)

        system_instruction = build_system_instruction(mode, snippets, learner)
        call_kwargs: dict[str, object] = {
            "mode": str(mode),
            "learner_name": learner.display_name if learner else None,
            "snippets": [
                {"title": s.title, "content": _snippet_body(s), "source": s.source} for s in snippets
            ],
            "temperature": 0.4,
            "max_output_tokens": self.settings.max_response_tokens,
        }

        result = self.provider.generate(system_instruction, cleaned, **call_kwargs)

        notice = ""
        if result.error:
            notice = "The live Gemini API was unavailable, so here is an offline preview answer instead."
            result = self._fallback.generate(system_instruction, cleaned, **call_kwargs)

        provider_name = "stub" if result.is_stub else self.provider.name
        return ConversationResponse(
            text=result.text,
            mode=str(mode),
            is_stub=result.is_stub,
            sources=[snippet.title for snippet in snippets],
            provider_name=provider_name,
            notice=notice,
        )


@lru_cache(maxsize=4)
def get_conversation_service(settings: AppSettings) -> ConversationService:
    """Return a cached :class:`ConversationService` for ``settings``."""
    return ConversationService(settings)


def _snippet_body(snippet: RetrievedSnippet) -> str:
    """Return a snippet's content with its leading Markdown heading removed and whitespace collapsed."""
    lines = snippet.content.splitlines()
    if lines and lines[0].strip().startswith("#"):
        lines = lines[1:]
    return " ".join(" ".join(lines).split())


def build_system_instruction(mode: Mode | str, snippets: list[RetrievedSnippet], learner: LearnerProfile | None) -> str:
    """Compose the system prompt sent to the LLM provider for this turn."""

    parts = [_BASE_RULES, _MODE_INSTRUCTIONS.get(str(mode), _MODE_INSTRUCTIONS["teacher"])]

    if learner and learner.display_name:
        learner_line = f"The learner's name is {learner.display_name}."
        if learner.grade_level and learner.grade_level != "Unknown":
            learner_line += f" They are in grade band {learner.grade_level}."
        learner_line += " You may use their name warmly."
        parts.append(learner_line)

    if snippets:
        context_lines = ["Curated lesson notes you can use as grounding (mention the title if you use one):"]
        for snippet in snippets:
            excerpt = textwrap.shorten(_snippet_body(snippet), width=600, placeholder="…")
            context_lines.append(f"### {snippet.title}\n{excerpt}")
        parts.append("\n\n".join(context_lines))

    return "\n\n".join(parts)
