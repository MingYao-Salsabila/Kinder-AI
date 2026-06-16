from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Mode = Literal["landing", "kid", "teacher", "admin"]


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
