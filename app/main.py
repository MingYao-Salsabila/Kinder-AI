from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app.config import load_settings
from app.core.rag import get_index
from app.core.router import render_mode
from app.db.database import initialize_database, seed_demo_content

MODES = ("landing", "kid", "teacher", "admin")
_MODE_THEME_CSS = {
    "kid": "kid_theme.css",
    "teacher": "teacher_theme.css",
}


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

    with st.sidebar:
        st.subheader("Mode")
        # Consume any pending navigation set by landing-page buttons *before*
        # the radio widget is instantiated -- Streamlit forbids writing a
        # widget's key in session state after it has been created.
        _pending = st.session_state.pop("_nav_mode", None)
        _default_idx = MODES.index(_pending) if _pending in MODES else MODES.index(settings.default_mode)

        selected_mode = st.radio(
            "Select a mode",
            options=MODES,
            index=_default_idx,
            horizontal=False,
            key="app_mode",
        )

        st.divider()
        st.write(f"Environment: `{settings.app_env}`")
        if settings.is_live:
            st.success(f"Gemini: live (`{settings.gemini_model}`)")
        else:
            st.info("Gemini: offline stub — no live API calls")
            if settings.gemini_use_stub:
                st.caption("Set `GEMINI_USE_STUB=false` and a real `GEMINI_API_KEY` to go live.")
            else:
                st.caption("`GEMINI_API_KEY` looks like a placeholder — add a real key to go live.")

        try:
            index = get_index(settings)
            doc_count = len(index.documents)
        except Exception:
            doc_count = 0
        st.caption(f"📚 Knowledge base: {doc_count} lesson note(s) indexed")

    styles_dir = ROOT / "app" / "styles"
    css = load_css(styles_dir / "shared.css")
    theme_file = _MODE_THEME_CSS.get(selected_mode)
    if theme_file:
        css = f"{css}\n{load_css(styles_dir / theme_file)}"
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    st.title(settings.app_name)
    st.caption("A safe, modular learning assistant for kids, teachers, and admins.")

    render_mode(selected_mode, settings)


if __name__ == "__main__":
    main()
