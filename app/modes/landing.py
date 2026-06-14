from __future__ import annotations

import streamlit as st

from app.config import AppSettings


def render_landing_mode(settings: AppSettings) -> None:
    st.header("Welcome to KinderAi")
    st.write(
        "KinderAi is a shared learning assistant built for kids, teachers, and admins. "
        "Use the sidebar to switch modes."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("Kid Mode")
        st.write("Guided, simple, and safety-filtered responses.")
    with col2:
        st.info("Teacher Mode")
        st.write("Lesson planning, explanations, and classroom support.")
    with col3:
        st.warning("Admin Mode")
        st.write("Review logs, settings, and progress summaries.")

    st.divider()
    st.subheader("Current settings")
    st.code(
        "\n".join(
            [
                f"APP_NAME={settings.app_name}",
                f"APP_ENV={settings.app_env}",
                f"DEFAULT_MODE={settings.default_mode}",
                f"GEMINI_MODEL={settings.gemini_model}",
                f"GEMINI_USE_STUB={settings.gemini_use_stub}",
            ]
        ),
        language="text",
    )
