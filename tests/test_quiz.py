from __future__ import annotations

from app.core.quiz import QuizQuestion, generate_quiz
from app.core.rag import retrieve_approved_snippets


def test_quiz_question_is_correct_is_case_insensitive():
    question = QuizQuestion(prompt="2 + 2?", answer="Four", choices=["Four", "Five"])

    assert question.is_correct("four") is True
    assert question.is_correct(" FOUR ") is True
    assert question.is_correct("five") is False
    assert question.is_correct(None) is False


def test_quiz_question_is_multiple_choice():
    mcq = QuizQuestion(prompt="?", answer="A", choices=["A", "B"])
    open_ended = QuizQuestion(prompt="?", answer="A")

    assert mcq.is_multiple_choice is True
    assert open_ended.is_multiple_choice is False


def test_generate_quiz_stub_mode_uses_fallback_and_grounds_in_snippets(populated_settings):
    snippets = retrieve_approved_snippets("Tell me about plants", populated_settings, top_k=1)
    assert snippets  # sanity check the fixture KB is searchable

    questions = generate_quiz("plants", populated_settings, snippets=snippets, num_questions=3)

    assert len(questions) == 3
    assert all(isinstance(q, QuizQuestion) for q in questions)
    # The true/false question should be answerable and grounded in the snippet.
    tf_question = questions[0]
    assert tf_question.is_multiple_choice
    assert tf_question.answer == "True"
    assert "Plants and Photosynthesis" in tf_question.hint


def test_generate_quiz_without_snippets_still_returns_questions(settings):
    questions = generate_quiz("space", settings, snippets=[], num_questions=2)

    assert len(questions) == 2
    assert all(q.prompt for q in questions)


def test_generate_quiz_clamps_question_count(settings):
    questions = generate_quiz("space", settings, snippets=[], num_questions=20)

    assert len(questions) <= 6
