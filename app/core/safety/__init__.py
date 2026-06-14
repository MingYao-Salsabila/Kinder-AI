from __future__ import annotations

import re

from app.core.models import SafetyResult


_BLOCKLIST_PATTERNS = [
    r"\bself[- ]?harm\b",
    r"\bsuicide\b",
    r"\bkill myself\b",
    r"\bviolent\b",
    r"\bweapon\b",
    r"\bporn\b",
    r"\bsexual\b",
]


def check_prompt_safety(prompt: str, audience: str = "kid") -> SafetyResult:
    text = (prompt or "").strip()
    if not text:
        return SafetyResult(allowed=False, reason="Prompt is empty.", redacted_prompt="")

    lowered = text.lower()
    if audience == "kid":
        for pattern in _BLOCKLIST_PATTERNS:
            if re.search(pattern, lowered):
                return SafetyResult(
                    allowed=False,
                    reason="The prompt is not suitable for the kid-facing mode.",
                    redacted_prompt="[blocked for kid mode]",
                )

    return SafetyResult(allowed=True, reason="OK", redacted_prompt=text)
