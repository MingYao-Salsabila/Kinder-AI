from __future__ import annotations

from app.core.database_helpers import normalize_mode, preview_text


def test_preview_text_collapses_whitespace_and_truncates():
    text = "Line one\n\n  Line two   with   extra spaces"

    result = preview_text(text, limit=20)

    assert result.endswith("…")
    assert len(result) <= 20
    assert "\n" not in result


def test_preview_text_returns_short_text_unchanged():
    assert preview_text("short", limit=20) == "short"


def test_preview_text_handles_empty_input():
    assert preview_text("", limit=20) == ""
    assert preview_text(None, limit=20) == ""  # type: ignore[arg-type]


def test_normalize_mode_valid_values_pass_through():
    for mode in ("landing", "kid", "teacher", "admin"):
        assert normalize_mode(mode) == mode


def test_normalize_mode_is_case_and_whitespace_insensitive():
    assert normalize_mode("  KID  ") == "kid"


def test_normalize_mode_unknown_falls_back_to_landing():
    assert normalize_mode("not-a-mode") == "landing"
    assert normalize_mode("") == "landing"
    assert normalize_mode(None) == "landing"  # type: ignore[arg-type]
