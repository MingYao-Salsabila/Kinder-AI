from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

try:
    from pydantic import Field
except Exception:  # pragma: no cover
    Field = None  # type: ignore


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

    @property
    def project_root(self) -> Path:
        return PROJECT_ROOT


def load_settings() -> AppSettings:
    load_dotenv(override=False)

    app_name = _env("APP_NAME", APP_NAME)
    app_env = _env("APP_ENV", "development")
    default_mode = _env("DEFAULT_MODE", "landing").lower()
    if default_mode not in {"landing", "kid", "teacher", "admin"}:
        default_mode = "landing"

    gemini_api_key = _env("GEMINI_API_KEY", "stub-gemini-api-key")
    gemini_model = _env("GEMINI_MODEL", "gemini-stub")
    gemini_use_stub = _env_bool("GEMINI_USE_STUB", True)

    sqlite_path = Path(_env("SQLITE_PATH", "app/db/kinderai.sqlite3"))
    vector_index_path = Path(_env("VECTOR_INDEX_PATH", "app/data/vector_index"))

    return AppSettings(
        app_name=app_name,
        app_env=app_env,
        default_mode=default_mode,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
        gemini_use_stub=gemini_use_stub,
        sqlite_path=sqlite_path,
        vector_index_path=vector_index_path,
    )
