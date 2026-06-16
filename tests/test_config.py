from __future__ import annotations

from app.config import load_settings

_ENV_KEYS = (
    "APP_NAME",
    "APP_ENV",
    "DEFAULT_MODE",
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
    "GEMINI_USE_STUB",
    "SQLITE_PATH",
    "VECTOR_INDEX_PATH",
    "KNOWLEDGE_BASE_PATH",
    "GEMINI_MAX_OUTPUT_TOKENS",
)


def _clear_env(monkeypatch) -> None:
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_defaults_are_safe_and_offline(monkeypatch):
    _clear_env(monkeypatch)

    settings = load_settings()

    assert settings.default_mode == "landing"
    assert settings.gemini_use_stub is True
    assert settings.has_real_gemini_key is False
    assert settings.is_live is False
    assert settings.max_response_tokens == 1024


def test_invalid_default_mode_falls_back_to_landing(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("DEFAULT_MODE", "not-a-real-mode")

    settings = load_settings()

    assert settings.default_mode == "landing"


def test_relative_paths_resolve_against_project_root(monkeypatch):
    _clear_env(monkeypatch)

    settings = load_settings()

    assert settings.sqlite_path.is_absolute()
    assert settings.sqlite_path == settings.project_root / "app" / "db" / "kinderai.sqlite3"


def test_is_live_requires_both_a_real_key_and_stub_disabled(monkeypatch):
    _clear_env(monkeypatch)

    # Real-looking key, but stub still enabled -> not live.
    monkeypatch.setenv("GEMINI_API_KEY", "a-real-looking-key-123")
    monkeypatch.setenv("GEMINI_USE_STUB", "true")
    settings = load_settings()
    assert settings.has_real_gemini_key is True
    assert settings.is_live is False

    # Stub disabled with a real key -> live.
    monkeypatch.setenv("GEMINI_USE_STUB", "false")
    settings = load_settings()
    assert settings.is_live is True

    # Stub disabled but placeholder key -> still not live.
    monkeypatch.setenv("GEMINI_API_KEY", "stub-gemini-api-key")
    settings = load_settings()
    assert settings.has_real_gemini_key is False
    assert settings.is_live is False


def test_max_response_tokens_env_override(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("GEMINI_MAX_OUTPUT_TOKENS", "256")

    settings = load_settings()

    assert settings.max_response_tokens == 256


def test_max_response_tokens_has_a_floor(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("GEMINI_MAX_OUTPUT_TOKENS", "10")

    settings = load_settings()

    assert settings.max_response_tokens == 128
