from __future__ import annotations

import streamlit as st

from app.config import AppSettings
from app.core.rag import get_index
from app.db.database import get_dashboard_summary


def render_landing_mode(settings: AppSettings) -> None:
    st.header("Welcome to KinderAi")
    st.write(
        "KinderAi is a shared learning assistant for the MajuBarengAi programme, built for kids, "
        "teachers, and admins. Use the sidebar -- or the buttons below -- to switch modes."
    )

    _render_status(settings)

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("Kid Mode")
        st.write(
            "Short, friendly, safety-checked answers grounded in curated lesson notes, "
            "plus a quick quiz and a progress tracker."
        )
        if st.button("Try Kid Mode", width="stretch"):
            _go_to("kid")
    with col2:
        st.info("Teacher Mode")
        st.write(
            "Classroom-ready explanations with examples and check-for-understanding "
            "prompts, plus a downloadable quiz generator."
        )
        if st.button("Open Teacher Mode", width="stretch"):
            _go_to("teacher")
    with col3:
        st.warning("Admin Mode")
        st.write(
            "Review conversation logs, learner progress, quiz attempts, configuration, "
            "and the retrieval knowledge base."
        )
        if st.button("Open Admin Mode", width="stretch"):
            _go_to("admin")

    st.divider()
    st.subheader("How it works")
    st.markdown(
        "1. Every prompt is screened by a lightweight, kid-safety keyword filter.\n"
        "2. Kid and Teacher Mode retrieve relevant lesson notes from the local knowledge "
        "base using a small TF-IDF search index.\n"
        "3. The prompt, retrieved notes, and a mode-specific persona are sent to Gemini "
        "(or an offline stub if no API key is configured).\n"
        "4. Conversations, quiz attempts, and learner progress are saved to a local "
        "SQLite database for Admin Mode to review."
    )


def _render_status(settings: AppSettings) -> None:
    summary = get_dashboard_summary(settings.sqlite_path)
    try:
        doc_count = len(get_index(settings).documents)
    except Exception:
        doc_count = 0

    cols = st.columns(3)
    if settings.is_live:
        cols[0].success(f"Gemini: live (`{settings.gemini_model}`)")
    else:
        cols[0].info("Gemini: offline stub")
    cols[1].metric("Lesson notes indexed", doc_count)
    cols[2].metric("Conversations logged", summary["conversation_count"])


def _go_to(mode: str) -> None:
    st.session_state["app_mode"] = mode
    st.rerun()
