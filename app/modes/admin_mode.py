from __future__ import annotations

import streamlit as st

from app.config import AppSettings
from app.core.database_helpers import preview_text
from app.core.progress import compute_progress_score, level_for_score
from app.core.rag import get_index, rebuild_index
from app.db.database import (
    clear_conversations,
    get_app_settings,
    get_dashboard_summary,
    get_recent_conversations,
    list_learner_progress,
    list_recent_quiz_attempts,
)


def render_admin_mode(settings: AppSettings) -> None:
    st.header("Admin Mode")
    st.write("Review logs, configuration, the knowledge base, and learner progress.")

    summary = get_dashboard_summary(settings.sqlite_path)
    cols = st.columns(5)
    cols[0].metric("Conversations", summary["conversation_count"])
    cols[1].metric("Kid prompts", summary["kid_count"])
    cols[2].metric("Teacher prompts", summary["teacher_count"])
    cols[3].metric("Quiz attempts", summary["quiz_attempt_count"])
    cols[4].metric("Learners tracked", summary["learner_count"])

    st.divider()
    _render_configuration(settings)

    st.divider()
    _render_knowledge_base(settings)

    st.divider()
    _render_conversations(settings)

    st.divider()
    _render_learner_progress(settings)

    st.divider()
    _render_quiz_attempts(settings)

    st.divider()
    _render_app_settings(settings)


def _render_configuration(settings: AppSettings) -> None:
    st.subheader("Configuration snapshot")

    if settings.is_live:
        st.success(f"Live Gemini mode is enabled -- model `{settings.gemini_model}`.")
    elif settings.gemini_use_stub:
        st.info("Running in offline stub mode (`GEMINI_USE_STUB=true`). No live API calls are made.")
    else:
        st.warning(
            "`GEMINI_USE_STUB=false`, but `GEMINI_API_KEY` looks like a placeholder, "
            "so the app is falling back to the offline stub provider."
        )

    st.code(
        "\n".join(
            [
                f"APP_NAME={settings.app_name}",
                f"APP_ENV={settings.app_env}",
                f"DEFAULT_MODE={settings.default_mode}",
                f"SQLITE_PATH={settings.sqlite_path}",
                f"GEMINI_MODEL={settings.gemini_model}",
                f"GEMINI_USE_STUB={settings.gemini_use_stub}",
                f"GEMINI_API_KEY={'configured' if settings.has_real_gemini_key else 'not set (placeholder)'}",
                f"KNOWLEDGE_BASE_PATH={settings.knowledge_base_path}",
                f"VECTOR_INDEX_PATH={settings.vector_index_path}",
                f"GEMINI_MAX_OUTPUT_TOKENS={settings.max_response_tokens}",
            ]
        ),
        language="text",
    )


def _render_knowledge_base(settings: AppSettings) -> None:
    st.subheader("Knowledge base & retrieval")

    try:
        index = get_index(settings)
    except Exception as exc:  # pragma: no cover - defensive UI guard
        st.error(f"Could not load the knowledge base index: {exc}")
        return

    st.write(f"**{len(index.documents)}** lesson note(s) currently indexed from `{settings.knowledge_base_path}`.")
    if index.documents:
        for doc in index.documents:
            st.write(f"- {doc.title} (`{doc.source}`)")
    else:
        st.info("No lesson notes found. Add `.md` or `.txt` files to the knowledge base folder.")

    if st.button("🔄 Rebuild & save index"):
        try:
            new_index = rebuild_index(settings, persist=True)
        except Exception as exc:  # pragma: no cover - defensive UI guard
            st.error(f"Rebuild failed: {exc}")
        else:
            index_file = settings.vector_index_path / "index.json"
            if index_file.exists():
                st.success(f"Rebuilt and saved index with {len(new_index.documents)} document(s) to `{index_file}`.")
            else:
                st.warning(
                    f"Rebuilt index with {len(new_index.documents)} document(s) in memory, "
                    "but could not write it to disk (read-only filesystem?)."
                )


def _render_conversations(settings: AppSettings) -> None:
    st.subheader("Recent conversations")

    mode_filter = st.selectbox("Filter by mode", ("all", "kid", "teacher", "admin"), key="admin_mode_filter")
    rows = get_recent_conversations(
        settings.sqlite_path,
        limit=10,
        mode=None if mode_filter == "all" else mode_filter,
    )

    if rows:
        display_rows = [
            {
                "id": row["id"],
                "mode": row["mode"],
                "prompt": preview_text(row["prompt"], 60),
                "response": preview_text(row["response"], 80),
                "created_at": row["created_at"],
            }
            for row in rows
        ]
        st.dataframe(display_rows, width="stretch", hide_index=True)
    else:
        st.info("No conversation logs yet.")

    with st.expander("⚠️ Danger zone"):
        confirm = st.checkbox("I understand this permanently deletes all conversation logs.", key="admin_confirm_clear")
        if st.button("Clear conversation logs", disabled=not confirm):
            removed = clear_conversations(settings.sqlite_path)
            st.success(f"Cleared {removed} conversation log entr{'y' if removed == 1 else 'ies'}.")
            st.rerun()


def _render_learner_progress(settings: AppSettings) -> None:
    st.subheader("Learner progress")

    rows = list_learner_progress(settings.sqlite_path)
    if not rows:
        st.info("No learner progress recorded yet. It appears here once a learner completes a quiz in Kid Mode.")
        return

    display_rows = []
    for row in rows:
        completed = int(row["completed_lessons"] or 0)
        badges = int(row["badges"] or 0)
        active_days = int(row["active_days"] or 0)
        score = compute_progress_score(completed, badges, active_days)
        display_rows.append(
            {
                "learner_id": row["learner_id"],
                "lessons_tracked": row["lessons_tracked"],
                "completed_lessons": completed,
                "badges": badges,
                "active_days": active_days,
                "score": score,
                "level": level_for_score(score),
                "last_activity": row["last_activity"],
            }
        )
    st.dataframe(display_rows, width="stretch", hide_index=True)


def _render_quiz_attempts(settings: AppSettings) -> None:
    st.subheader("Recent quiz attempts")

    rows = list_recent_quiz_attempts(settings.sqlite_path, limit=10)
    if not rows:
        st.info("No quiz attempts recorded yet.")
        return

    display_rows = []
    for row in rows:
        total = int(row["total_questions"] or 0)
        correct = int(row["correct_answers"] or 0)
        display_rows.append(
            {
                "learner_id": row["learner_id"],
                "topic": preview_text(row["topic"], 40),
                "score": f"{correct}/{total}" if total else "—",
                "created_at": row["created_at"],
            }
        )
    st.dataframe(display_rows, width="stretch", hide_index=True)


def _render_app_settings(settings: AppSettings) -> None:
    st.subheader("Stored app settings")

    rows = get_app_settings(settings.sqlite_path)
    if not rows:
        st.info("No app settings stored yet.")
        return

    display_rows = [{"setting": key, "value": value} for key, value in sorted(rows.items())]
    st.dataframe(display_rows, width="stretch", hide_index=True)
