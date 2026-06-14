from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app.config import load_settings
from app.core.router import render_mode
from app.db.database import initialize_database, seed_demo_content


def load_css(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def main() -> None:
    settings = load_settings()
    initialize_database(settings.sqlite_path)
    seed_demo_content(settings.sqlite_path)

    st.set_page_config(
        page_title=settings.app_name,
        page_icon="✨",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    styles = ROOT / "app" / "styles" / "shared.css"
    st.markdown(f"<style>{load_css(styles)}</style>", unsafe_allow_html=True)

    st.title(settings.app_name)
    st.caption("A safe, modular learning assistant for kids, teachers, and admins.")

    with st.sidebar:
        st.subheader("Mode")
        selected_mode = st.radio(
            "Select a mode",
            options=("landing", "kid", "teacher", "admin"),
            index=("landing", "kid", "teacher", "admin").index(settings.default_mode),
            horizontal=False,
        )
        st.divider()
        st.write(f"Environment: `{settings.app_env}`")
        st.write(f"Gemini stub: `{str(settings.gemini_use_stub).lower()}`")
        st.write(f"Model: `{settings.gemini_model}`")

    render_mode(selected_mode, settings)


if __name__ == "__main__":
    main()
