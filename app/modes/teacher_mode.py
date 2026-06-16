from __future__ import annotations

import re

import streamlit as st

from app.config import AppSettings
from app.core.conversation import get_conversation_service
from app.core.quiz import QuizQuestion, generate_quiz
from app.core.rag import retrieve_approved_snippets
from app.db.database import save_conversation

_GRADE_LEVELS = ("K-2", "3-5", "6-8", "9-12", "Mixed / not specified")


def render_teacher_mode(settings: AppSettings) -> None:
    st.header("Teacher Mode")
    st.write("Use this mode for lesson planning, explanations, and classroom support.")

    topic_col, grade_col = st.columns([3, 1])
    with topic_col:
        topic = st.text_input("Topic", placeholder="For example: photosynthesis", key="teacher_topic")
    with grade_col:
        grade_level = st.selectbox("Grade level", _GRADE_LEVELS, key="teacher_grade")

    request = st.text_area(
        "Request",
        placeholder="Explain this topic and give one quiz question.",
        key="teacher_request",
    )

    if st.button("Generate teacher response", type="primary"):
        if not (topic.strip() or request.strip()):
            st.warning("Add a topic or a request first.")
        else:
            prompt = f"Topic: {topic}\nGrade level: {grade_level}\nRequest: {request}".strip()
            service = get_conversation_service(settings)
            response = service.respond(prompt, mode="teacher", audience="general")
            save_conversation(settings.sqlite_path, mode="teacher", prompt=prompt, response=response.text)

            st.session_state["teacher_last_response"] = response
            st.session_state["teacher_last_topic"] = topic.strip() or request.strip()
            st.session_state.pop("teacher_quiz", None)

    response = st.session_state.get("teacher_last_response")
    if response is not None:
        st.markdown("### Draft")
        st.write(response.text)
        if response.notice:
            st.caption(f"ℹ️ {response.notice}")
        if response.sources:
            with st.expander("📚 Grounded in these lesson notes"):
                for title in response.sources:
                    st.write(f"- {title}")

    st.divider()
    _render_quiz_generator(settings, topic)

    st.caption("This screen is intentionally broad, but still starts from educational prompts.")


def _render_quiz_generator(settings: AppSettings, topic_field: str) -> None:
    st.subheader("Quiz generator")

    default_topic = st.session_state.get("teacher_last_topic") or topic_field
    num_questions = st.slider("Number of questions", min_value=2, max_value=6, value=4, key="teacher_quiz_count")

    if st.button("📝 Generate a quiz for this topic"):
        quiz_topic = (default_topic or "").strip()
        if not quiz_topic:
            st.warning("Add a topic above first.")
        else:
            snippets = retrieve_approved_snippets(quiz_topic, settings, top_k=3)
            questions = generate_quiz(quiz_topic, settings, snippets=snippets, num_questions=num_questions)
            st.session_state["teacher_quiz"] = questions
            st.session_state["teacher_quiz_topic"] = quiz_topic

    quiz = st.session_state.get("teacher_quiz")
    if not quiz:
        return

    quiz_topic = st.session_state.get("teacher_quiz_topic", default_topic)
    st.markdown(f"**Quiz: {quiz_topic}**")

    for i, question in enumerate(quiz, start=1):
        st.markdown(f"{i}. {question.prompt}")
        if question.is_multiple_choice:
            for j, choice in enumerate(question.choices):
                letter = chr(ord("a") + j)
                marker = "✅" if choice == question.answer else "◦"
                st.write(f"&nbsp;&nbsp;{marker} {letter}) {choice}", unsafe_allow_html=True)
        if question.hint:
            st.caption(f"Hint: {question.hint}")

    with st.expander("Answer key"):
        for i, question in enumerate(quiz, start=1):
            st.write(f"{i}. {question.answer}")

    markdown_quiz = _format_quiz_markdown(quiz_topic, quiz)
    st.download_button(
        "⬇️ Download quiz (Markdown)",
        data=markdown_quiz,
        file_name=f"kinderai_quiz_{_slugify(quiz_topic)}.md",
        mime="text/markdown",
    )


def _format_quiz_markdown(topic: str, questions: list[QuizQuestion]) -> str:
    lines = [f"# Quiz: {topic}", ""]
    for i, question in enumerate(questions, start=1):
        lines.append(f"**{i}. {question.prompt}**")
        lines.append("")
        if question.is_multiple_choice:
            for j, choice in enumerate(question.choices):
                letter = chr(ord("a") + j)
                lines.append(f"- {letter}) {choice}")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Answer key")
    for i, question in enumerate(questions, start=1):
        line = f"{i}. {question.answer}"
        if question.hint:
            line += f"  (Hint: {question.hint})"
        lines.append(line)

    return "\n".join(lines)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "topic").lower()).strip("-")
    return slug or "topic"
