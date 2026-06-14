from __future__ import annotations

import streamlit as st

from app.config import AppSettings
from app.core.conversation import GeminiStubClient
from app.core.safety import check_prompt_safety
from app.db.database import save_conversation


def render_kid_mode(settings: AppSettings) -> None:
    st.header("Kid Mode")
    st.write("Ask a school-friendly question. Answers are kept short and simple.")

    prompt = st.text_area("Your question", placeholder="Ask about science, reading, math, or nature.")
    if st.button("Ask KinderAi", type="primary"):
        safety = check_prompt_safety(prompt, audience="kid")
        if not safety.allowed:
            st.error(safety.reason)
            st.stop()

        client = GeminiStubClient(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            use_stub=settings.gemini_use_stub,
        )
        response = client.generate(prompt=prompt, mode="kid", audience="kid")
        st.success("Answer")
        st.write(response.text)
        save_conversation(settings.sqlite_path, mode="kid", prompt=prompt, response=response.text)

    st.caption("Tip: keep questions about learning and school topics.")
