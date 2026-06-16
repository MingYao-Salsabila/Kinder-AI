from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ProgressSummary:
    learner_id: str
    completed_lessons: int
    badges: int
    streak_days: int

    @property
    def score(self) -> int:
        return compute_progress_score(self.completed_lessons, self.badges, self.streak_days)

    @property
    def level(self) -> str:
        return level_for_score(self.score)


def compute_progress_score(completed_lessons: int, badges: int, streak_days: int) -> int:
    return max(0, completed_lessons * 10 + badges * 5 + streak_days * 2)


# (minimum score, label) pairs, ordered ascending. The label for a score is
# the highest threshold it meets or exceeds.
_LEVELS: list[tuple[int, str]] = [
    (0, "Curious Seedling"),
    (20, "Growing Learner"),
    (50, "Steady Explorer"),
    (100, "Bright Star"),
    (200, "KinderAi Champion"),
]


def level_for_score(score: int) -> str:
    """Return a friendly level label for a progress score."""
    label = _LEVELS[0][1]
    for threshold, name in _LEVELS:
        if score >= threshold:
            label = name
        else:
            break
    return label


def next_level_target(score: int) -> tuple[str, int] | None:
    """Return ``(label, score_needed)`` for the next level, or ``None`` if maxed out."""
    for threshold, name in _LEVELS:
        if score < threshold:
            return name, threshold
    return None
