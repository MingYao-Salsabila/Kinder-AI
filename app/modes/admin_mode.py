from __future__ import annotations

import pandas as pd
import streamlit as st

from app.config import AppSettings
from app.core.database_helpers import preview_text
from app.db.database import get_dashboard_summary, get_recent_conversations


def render_admin_mode(settings: AppSettings) -> None:
    st.header("Admin Mode")
    st.write("Review logs, stub settings, and demo analytics.")

    summary = get_dashboard_summary(settings.sqlite_path)
    c1, c2, c3 = st.columns(3)
    c1.metric("Conversations", summary["conversation_count"])
    c2.metric("Kid prompts", summary["kid_count"])
    c3.metric("Teacher prompts", summary["teacher_count"])

    st.subheader("Recent conversations")
    rows = get_recent_conversations(settings.sqlite_path, limit=10)
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
        df = pd.DataFrame(display_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No conversation logs yet.")

    st.subheader("Configuration snapshot")
    st.code(
        "\n".join(
            [
                f"APP_ENV={settings.app_env}",
                f"DEFAULT_MODE={settings.default_mode}",
                f"SQLITE_PATH={settings.sqlite_path}",
                f"GEMINI_API_KEY={'set' if settings.gemini_api_key else 'missing'}",
                f"GEMINI_USE_STUB={settings.gemini_use_stub}",
            ]
        ),
        language="text",
    )
