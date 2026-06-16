from __future__ import annotations

import re

from app.core.models import SafetyResult

# Topics that are never appropriate for the kid-facing persona. Patterns are
# intentionally broad and matched case-insensitively -- in a kids' product, a
# false positive (an over-cautious refusal) is far less costly than a false
# negative.
_BLOCKED_PATTERNS: dict[str, list[str]] = {
    "self-harm or suicide": [
        r"\bself[- ]?harm\b",
        r"\bsuicid\w*\b",
        r"\bkill (myself|yourself)\b",
        r"\bcut(ting)? myself\b",
    ],
    "violence or weapons": [
        r"\bweapons?\b",
        r"\bguns?\b",
        r"\bbombs?\b",
        r"\bhow to (fight|hurt|kill)\b",
    ],
    "sexual content": [
        r"\bporn\w*\b",
        r"\bsex(ual|y)?\b",
        r"\bnude\w*\b",
    ],
    "drugs and alcohol": [
        r"\balcohol\b",
        r"\bdrugs?\b",
        r"\bcigarettes?\b",
        r"\bvap(e|ing)\b",
    ],
    "personal information": [
        r"\bhome address\b",
        r"\bphone number\b",
        r"\bcredit card\b",
        r"\bpassword\b",
        r"\bwhere do you live\b",
    ],
}

_MAX_PROMPT_LENGTH = 4000


def check_prompt_safety(prompt: str, audience: str = "kid") -> SafetyResult:
    """Run a lightweight, dependency-free keyword screen over ``prompt``.

    This is a fast first line of defense that runs before any model call --
    it is not a substitute for the underlying model's own safety behaviour,
    which still applies whenever the live Gemini provider is used.
    """

    text = (prompt or "").strip()
    if not text:
        return SafetyResult(allowed=False, reason="Please type a question first.", redacted_prompt="")

    if len(text) > _MAX_PROMPT_LENGTH:
        text = text[:_MAX_PROMPT_LENGTH]

    if audience == "kid":
        lowered = text.lower()
        for category, patterns in _BLOCKED_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, lowered):
                    return SafetyResult(
                        allowed=False,
                        reason=(
                            f"That question touches on {category}, which isn't covered in Kid Mode. "
                            "Try asking about a school topic like science, reading, math, or nature instead."
                        ),
                        redacted_prompt="[blocked for kid mode]",
                    )

    return SafetyResult(allowed=True, reason="OK", redacted_prompt=text)
