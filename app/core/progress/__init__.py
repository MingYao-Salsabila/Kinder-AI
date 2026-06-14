from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ProgressSummary:
    learner_id: str
    completed_lessons: int
    badges: int
    streak_days: int


def compute_progress_score(completed_lessons: int, badges: int, streak_days: int) -> int:
    return max(0, completed_lessons * 10 + badges * 5 + streak_days * 2)
