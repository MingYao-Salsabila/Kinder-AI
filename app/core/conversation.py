from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.core.models import ConversationRecord, SafetyResult
from app.core.safety import check_prompt_safety


@dataclass(slots=True)
class ConversationResponse:
    text: str
    mode: str
    is_stub: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


class GeminiStubClient:
    def __init__(self, api_key: str, model: str = "gemini-stub", use_stub: bool = True) -> None:
        self.api_key = api_key.strip()
        self.model = model.strip() or "gemini-stub"
        self.use_stub = use_stub

    def generate(self, prompt: str, mode: str = "teacher", audience: str = "general") -> ConversationResponse:
        safety = check_prompt_safety(prompt, audience=audience)
        if not safety.allowed:
            return ConversationResponse(
                text=(
                    "I cannot help with that request in this mode. "
                    "Please try a school-friendly question about learning, writing, science, math, or reading."
                ),
                mode=mode,
                is_stub=True,
            )

        cleaned = safety.redacted_prompt
        if mode == "kid":
            body = (
                "Here is a simple answer:\n\n"
                f"{cleaned}\n\n"
                "Try to think about the idea step by step. "
                "If you want, ask for a smaller hint or an example."
            )
        elif mode == "admin":
            body = (
                "Admin review response:\n\n"
                f"Prompt received: {cleaned}\n"
                "Status: safe for review.\n"
                "Suggested follow-up: inspect logs, confirm routing, and review learner context."
            )
        elif mode == "teacher":
            body = (
                "Teacher-ready response:\n\n"
                f"{cleaned}\n\n"
                "You can turn this into a classroom explanation, an example, and a short check-for-understanding question."
            )
        else:
            body = f"Stub response for {mode}: {cleaned}"

        return ConversationResponse(text=body, mode=mode, is_stub=True)


def build_conversation_record(mode: str, prompt: str, response: str) -> ConversationRecord:
    return ConversationRecord(mode=mode, prompt=prompt, response=response)
