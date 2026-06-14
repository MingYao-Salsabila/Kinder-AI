from __future__ import annotations

import streamlit as st

from app.config import AppSettings
from app.core.conversation import GeminiStubClient
from app.db.database import save_conversation


def render_teacher_mode(settings: AppSettings) -> None:
    st.header("Teacher Mode")
    st.write("Use this mode for lesson planning, explanations, and classroom support.")

    topic = st.text_input("Topic", placeholder="For example: photosynthesis")
    request = st.text_area("Request", placeholder="Explain this topic for grade 5 and give one quiz question.")

    if st.button("Generate teacher response", type="primary"):
        prompt = f"Topic: {topic}\nRequest: {request}".strip()
        client = GeminiStubClient(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            use_stub=settings.gemini_use_stub,
        )
        response = client.generate(prompt=prompt, mode="teacher", audience="general")
        st.markdown("### Draft")
        st.write(response.text)
        save_conversation(settings.sqlite_path, mode="teacher", prompt=prompt, response=response.text)

    st.caption("This screen is intentionally broad, but still starts from educational prompts.")
