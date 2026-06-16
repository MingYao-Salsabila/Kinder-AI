from __future__ import annotations

import streamlit as st

from app.config import AppSettings
from app.core.conversation import get_conversation_service
from app.core.models import LearnerProfile
from app.core.progress import next_level_target
from app.core.quiz import generate_quiz
from app.core.rag import get_index, retrieve_approved_snippets
from app.core.speech import text_to_speech_html
from app.db.database import (
    get_learner_progress_summary,
    record_lesson_progress,
    record_quiz_attempt,
    save_conversation,
)

_GRADE_BANDS = ("K-2", "3-5", "6-8", "Not sure")


def render_kid_mode(settings: AppSettings) -> None:
    st.header("Kid Mode")
    st.write("Ask a school-friendly question. Answers are kept short, simple, and safe.")

    name_col, grade_col = st.columns([2, 1])
    with name_col:
        learner_name = st.text_input("Your name", value="Guest", key="kid_learner_name")
    with grade_col:
        grade_level = st.selectbox("Grade band", _GRADE_BANDS, key="kid_grade_band")

    learner_id = (learner_name or "Guest").strip() or "Guest"
    learner = LearnerProfile(learner_id=learner_id, display_name=learner_id, grade_level=grade_level)

    _render_progress(settings, learner)
    st.divider()

    _render_suggestions(settings)

    prompt = st.text_area(
        "Your question",
        placeholder="Ask about science, reading, math, or nature.",
        key="kid_question_input",
    )

    if st.button("Ask KinderAi", type="primary"):
        if not (prompt or "").strip():
            st.warning("Type a question first!")
        else:
            service = get_conversation_service(settings)
            response = service.respond(prompt, mode="kid", audience="kid", learner=learner)
            save_conversation(settings.sqlite_path, mode="kid", prompt=prompt, response=response.text)

            st.session_state["kid_last_response"] = response
            st.session_state["kid_last_topic"] = prompt.strip()
            # A new question retires any quiz tied to the previous topic.
            st.session_state.pop("kid_quiz_questions", None)
            st.session_state.pop("kid_quiz_topic", None)

    _render_last_response(settings)
    _render_quiz(settings, learner)

    st.caption("Tip: keep questions about learning and school topics.")


def _render_progress(settings: AppSettings, learner: LearnerProfile) -> None:
    summary = get_learner_progress_summary(settings.sqlite_path, learner.learner_id)

    cols = st.columns(4)
    cols[0].metric("Lessons done", summary.completed_lessons)
    cols[1].metric("Badges", summary.badges)
    cols[2].metric("Active days", summary.streak_days)
    cols[3].metric("Level", summary.level)

    target = next_level_target(summary.score)
    if target:
        next_label, threshold = target
        remaining = max(0, threshold - summary.score)
        st.caption(f"🌟 {summary.score} points — {remaining} more to reach **{next_label}**!")
    else:
        st.caption(f"🌟 {summary.score} points — you've reached the top level!")


def _render_suggestions(settings: AppSettings) -> None:
    try:
        index = get_index(settings)
    except Exception:
        return

    if not index.documents:
        return

    st.caption("Need an idea? Try one of these:")
    docs = index.documents[:4]
    cols = st.columns(len(docs))
    for col, doc in zip(cols, docs):
        with col:
            if st.button(doc.title, key=f"kid_suggest_{doc.source}", width="stretch"):
                st.session_state["kid_question_input"] = f"Can you tell me about {doc.title.lower()}?"


def _render_last_response(settings: AppSettings) -> None:
    response = st.session_state.get("kid_last_response")
    if response is None:
        return

    st.success(response.text)
    if response.notice:
        st.caption(f"ℹ️ {response.notice}")
    if response.sources:
        with st.expander("📚 Where this came from"):
            for title in response.sources:
                st.write(f"- {title}")

    st.iframe(text_to_speech_html(response.text, label="Read it to me"), height=70)

    if st.button("🎯 Quiz me on this!", key="kid_quiz_button"):
        topic = st.session_state.get("kid_last_topic", "this topic")
        snippets = retrieve_approved_snippets(topic, settings, top_k=2)
        st.session_state["kid_quiz_questions"] = generate_quiz(topic, settings, snippets=snippets, num_questions=3)
        st.session_state["kid_quiz_topic"] = topic


def _render_quiz(settings: AppSettings, learner: LearnerProfile) -> None:
    quiz = st.session_state.get("kid_quiz_questions")
    if not quiz:
        return

    topic = st.session_state.get("kid_quiz_topic", "this topic")
    st.divider()
    st.subheader(f"🎯 Quick quiz: {topic}")

    answers: list[str | None] = []
    for i, question in enumerate(quiz):
        st.markdown(f"**{i + 1}. {question.prompt}**")
        if question.is_multiple_choice:
            answer = st.radio(
                f"Answer for question {i + 1}",
                question.choices,
                key=f"kid_quiz_choice_{i}",
                index=None,
                label_visibility="collapsed",
            )
        else:
            answer = st.text_input(
                f"Answer for question {i + 1}",
                key=f"kid_quiz_text_{i}",
                label_visibility="collapsed",
            )
        answers.append(answer)
        if question.hint:
            with st.expander("Need a hint?"):
                st.write(question.hint)

    if st.button("Check my answers", key="kid_quiz_check", type="primary"):
        graded = [(q, a) for q, a in zip(quiz, answers) if q.is_multiple_choice]
        correct = sum(1 for q, a in graded if q.is_correct(a or ""))
        total = len(graded)

        for i, (question, answer) in enumerate(zip(quiz, answers), start=1):
            if question.is_multiple_choice:
                if question.is_correct(answer or ""):
                    st.success(f"{i}. Correct! 🎉")
                else:
                    st.error(f"{i}. Not quite -- the answer is: **{question.answer}**")
            else:
                st.info(f"{i}. Here's one way to put it: {question.answer}")

        if total:
            st.write(f"**Score: {correct} / {total}**")
            badges_earned = 1 if correct == total else 0
            record_quiz_attempt(settings.sqlite_path, learner.learner_id, topic, total, correct)
            record_lesson_progress(
                settings.sqlite_path, learner.learner_id, topic,
                completed=True, badges_earned=badges_earned,
            )
            if badges_earned:
                st.balloons()
        else:
            record_lesson_progress(settings.sqlite_path, learner.learner_id, topic, completed=True, badges_earned=0)
