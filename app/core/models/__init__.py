from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

Role = Literal["user", "assistant", "system"]
Mode = Literal["landing", "kid", "teacher", "admin"]


@dataclass(slots=True)
class Message:
    role: Role
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class ConversationRecord:
    mode: Mode
    prompt: str
    response: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class SafetyResult:
    allowed: bool
    reason: str = ""
    redacted_prompt: str = ""


@dataclass(slots=True)
class LearnerProfile:
    learner_id: str
    display_name: str
    grade_level: str = "Unknown"
