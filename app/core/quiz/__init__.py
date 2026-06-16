from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field

from app.config import AppSettings
from app.core.providers import get_provider
from app.core.rag import RetrievedSnippet

_QUIZ_SYSTEM_INSTRUCTION = (
    "You write short, age-appropriate quiz questions for children aged "
    "roughly 6-12. Respond with ONLY a JSON array -- no markdown fences, no "
    "commentary, no surrounding text. Each item must be an object with keys: "
    '"prompt" (string), "choices" (array of 3-4 short strings, or an empty '
    'array for an open-ended question), "answer" (string -- for multiple '
    "choice it must exactly match one of the choices), and \"hint\" (a short, "
    "gentle hint string)."
)


@dataclass(slots=True)
class QuizQuestion:
    prompt: str
    answer: str
    choices: list[str] = field(default_factory=list)
    hint: str = ""

    @property
    def is_multiple_choice(self) -> bool:
        return len(self.choices) >= 2

    def is_correct(self, given_answer: str) -> bool:
        return (given_answer or "").strip().casefold() == self.answer.strip().casefold()


def generate_quiz(
    topic: str,
    settings: AppSettings,
    snippets: list[RetrievedSnippet] | None = None,
    num_questions: int = 3,
) -> list[QuizQuestion]:
    """Build a short quiz about ``topic``.

    When ``settings.is_live`` is true, this asks the configured Gemini model
    for JSON-formatted questions (optionally grounded in ``snippets``). If
    the live call fails, returns malformed JSON, or the app is running in
    stub mode, falls back to :func:`_fallback_quiz`, which is deterministic
    and works fully offline using whatever lesson notes are available.
    """

    topic = (topic or "").strip() or "this topic"
    snippets = list(snippets or [])
    num_questions = max(1, min(num_questions, 6))

    if settings.is_live:
        try:
            questions = _generate_with_provider(settings, topic, snippets, num_questions)
        except Exception:
            questions = []
        if questions:
            return questions[:num_questions]

    return _fallback_quiz(topic, snippets, num_questions)


def _generate_with_provider(
    settings: AppSettings, topic: str, snippets: list[RetrievedSnippet], num_questions: int
) -> list[QuizQuestion]:
    provider = get_provider(settings)

    context = ""
    if snippets:
        lines = [f"- {s.title}: {' '.join(s.content.split())[:300]}" for s in snippets[:3]]
        context = "Curated lesson notes:\n" + "\n".join(lines) + "\n\n"

    user_prompt = (
        f"{context}Topic: {topic}\n"
        f"Write exactly {num_questions} quiz questions about this topic for the "
        "lesson notes above (or general knowledge if none are given)."
    )

    result = provider.generate(
        system_instruction=_QUIZ_SYSTEM_INSTRUCTION,
        user_prompt=user_prompt,
        mode="quiz",
        temperature=0.6,
        max_output_tokens=settings.max_response_tokens,
    )
    if result.error or result.is_stub:
        return []

    items = _parse_quiz_json(result.text)
    return _items_to_questions(items)


def _parse_quiz_json(text: str) -> list[dict]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()

    # Some models wrap the array in a single top-level key despite instructions.
    data = json.loads(cleaned)
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                data = value
                break
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array of quiz questions.")
    return data


def _items_to_questions(items: list[dict]) -> list[QuizQuestion]:
    questions: list[QuizQuestion] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        prompt = str(item.get("prompt", "")).strip()
        answer = str(item.get("answer", "")).strip()
        if not prompt or not answer:
            continue

        raw_choices = item.get("choices") or []
        choices = [str(choice).strip() for choice in raw_choices if str(choice).strip()]
        if choices and answer not in choices:
            choices.append(answer)

        hint = str(item.get("hint", "")).strip()
        questions.append(QuizQuestion(prompt=prompt, answer=answer, choices=choices, hint=hint))
    return questions


def _fallback_quiz(topic: str, snippets: list[RetrievedSnippet], num_questions: int) -> list[QuizQuestion]:
    """A small, deterministic quiz generator that needs no network access.

    Uses whatever lesson notes were retrieved to build a true/false question
    and a "which lesson is this?" multiple-choice question, then always adds
    an open-ended reflection prompt.
    """

    questions: list[QuizQuestion] = []
    rng = random.Random(topic)

    if snippets:
        fact = _first_sentence(snippets[0].content)
        if fact:
            questions.append(
                QuizQuestion(
                    prompt=f'True or False: "{fact}"',
                    answer="True",
                    choices=["True", "False"],
                    hint=f'This comes from the lesson note "{snippets[0].title}".',
                )
            )

        correct_title = snippets[0].title
        choices = [correct_title] + [s.title for s in snippets[1:3]]
        while len(choices) < 3:
            choices.append("None of these lesson notes")
        choices = list(dict.fromkeys(choices))  # de-duplicate, preserve order
        rng.shuffle(choices)
        questions.append(
            QuizQuestion(
                prompt=f'Which lesson note best matches "{topic}"?',
                answer=correct_title,
                choices=choices,
                hint="Think about which title is closest to your question.",
            )
        )

    model_answer = _first_sentence(snippets[0].content) if snippets else (
        f"Answers will vary -- look for a clear, simple explanation about {topic}."
    )
    questions.append(
        QuizQuestion(
            prompt=f"In your own words, explain one thing you learned about {topic}.",
            answer=model_answer,
            choices=[],
            hint="There's no single right answer here -- focus on using your own words.",
        )
    )

    # Always offer a couple of topic-agnostic prompts so a quiz can still be
    # assembled even when nothing in the knowledge base matched the topic.
    questions.append(
        QuizQuestion(
            prompt=f"What is one important fact about {topic}?",
            answer=f"Answers will vary -- look for a clear, simple fact about {topic}.",
            choices=[],
            hint="There's no single right answer -- any true, relevant fact works.",
        )
    )
    questions.append(
        QuizQuestion(
            prompt=f"Why might {topic} be useful or interesting to know about?",
            answer="Answers will vary -- any thoughtful reason works.",
            choices=[],
            hint="Think about how this connects to everyday life.",
        )
    )

    return questions[: max(1, num_questions)]


def _first_sentence(text: str) -> str:
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        sentence = re.split(r"(?<=[.!?])\s+", line)[0].strip()
        if len(sentence) > 15:
            return sentence
    return ""
