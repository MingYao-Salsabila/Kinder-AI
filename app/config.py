from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

APP_NAME = "KinderAi"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return default if value is None or value.strip() == "" else value.strip()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


_STUB_KEY_VALUES = {"", "stub-gemini-api-key", "your-gemini-api-key", "changeme"}


@dataclass(frozen=True)
class AppSettings:
    app_name: str
    app_env: str
    default_mode: str
    gemini_api_key: str
    gemini_model: str
    gemini_use_stub: bool
    sqlite_path: Path
    vector_index_path: Path
    knowledge_base_path: Path
    max_response_tokens: int

    @property
    def project_root(self) -> Path:
        return PROJECT_ROOT

    @property
    def has_real_gemini_key(self) -> bool:
        """Whether a non-placeholder Gemini API key has been configured."""
        return self.gemini_api_key.strip().lower() not in _STUB_KEY_VALUES

    @property
    def is_live(self) -> bool:
        """Whether the app will call the real Gemini API instead of the stub."""
        return (not self.gemini_use_stub) and self.has_real_gemini_key


def _resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_settings() -> AppSettings:
    load_dotenv(override=False)

    app_name = _env("APP_NAME", APP_NAME)
    app_env = _env("APP_ENV", "development")
    default_mode = _env("DEFAULT_MODE", "landing").lower()
    if default_mode not in {"landing", "kid", "teacher", "admin"}:
        default_mode = "landing"

    gemini_api_key = _env("GEMINI_API_KEY", "stub-gemini-api-key")
    gemini_model = _env("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_use_stub = _env_bool("GEMINI_USE_STUB", True)

    sqlite_path = _resolve_path(_env("SQLITE_PATH", "app/db/kinderai.sqlite3"))
    vector_index_path = _resolve_path(_env("VECTOR_INDEX_PATH", "app/data/vector_index"))
    knowledge_base_path = _resolve_path(_env("KNOWLEDGE_BASE_PATH", "app/data/knowledge_base"))

    max_response_tokens = 1024
    raw_tokens = os.getenv("GEMINI_MAX_OUTPUT_TOKENS")
    if raw_tokens and raw_tokens.strip().isdigit():
        max_response_tokens = max(128, int(raw_tokens.strip()))

    return AppSettings(
        app_name=app_name,
        app_env=app_env,
        default_mode=default_mode,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
        gemini_use_stub=gemini_use_stub,
        sqlite_path=sqlite_path,
        vector_index_path=vector_index_path,
        knowledge_base_path=knowledge_base_path,
        max_response_tokens=max_response_tokens,
    )
