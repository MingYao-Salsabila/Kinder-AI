from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class QuizQuestion:
    prompt: str
    answer: str
    hint: str = ""


def build_quiz(topic: str) -> list[QuizQuestion]:
    topic = topic.strip() or "the topic"
    return [
        QuizQuestion(
            prompt=f"What is one important fact about {topic}?",
            answer="Answers will vary.",
            hint="Look for a main idea.",
        ),
        QuizQuestion(
            prompt=f"Can you explain {topic} in your own words?",
            answer="Answers will vary.",
            hint="Use simple words.",
        ),
    ]
