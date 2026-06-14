from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

SCHEMA_SQL_PATH = Path(__file__).with_name("schema.sql")


def _connect(sqlite_path: Path) -> sqlite3.Connection:
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(sqlite_path: Path) -> None:
    schema_sql = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
    with _connect(sqlite_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()


def save_conversation(sqlite_path: Path, mode: str, prompt: str, response: str) -> None:
    with _connect(sqlite_path) as conn:
        conn.execute(
            """
            INSERT INTO conversations (mode, prompt, response)
            VALUES (?, ?, ?)
            """,
            (mode, prompt, response),
        )
        conn.commit()


def seed_demo_content(sqlite_path: Path) -> None:
    initialize_database(sqlite_path)
    with _connect(sqlite_path) as conn:
        count = conn.execute("SELECT COUNT(*) AS count FROM conversations").fetchone()["count"]
        if count == 0:
            conn.executemany(
                "INSERT INTO conversations (mode, prompt, response) VALUES (?, ?, ?)",
                [
                    ("kid", "What is a plant?", "A plant is a living thing that grows and makes its own food."),
                    ("teacher", "Explain fractions", "Fractions show parts of a whole and can be used in lessons with examples."),
                    ("admin", "Show logs", "Admin review response for demo data."),
                ],
            )
            conn.executemany(
                "INSERT OR REPLACE INTO app_settings (setting_key, setting_value) VALUES (?, ?)",
                [
                    ("theme", "shared"),
                    ("language", "en"),
                ],
            )
            conn.commit()


def get_recent_conversations(sqlite_path: Path, limit: int = 10) -> list[dict[str, Any]]:
    with _connect(sqlite_path) as conn:
        rows = conn.execute(
            """
            SELECT id, mode, prompt, response, created_at
            FROM conversations
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_dashboard_summary(sqlite_path: Path) -> dict[str, int]:
    with _connect(sqlite_path) as conn:
        total = conn.execute("SELECT COUNT(*) AS count FROM conversations").fetchone()["count"]
        kid_count = conn.execute(
            "SELECT COUNT(*) AS count FROM conversations WHERE mode = 'kid'"
        ).fetchone()["count"]
        teacher_count = conn.execute(
            "SELECT COUNT(*) AS count FROM conversations WHERE mode = 'teacher'"
        ).fetchone()["count"]
    return {
        "conversation_count": int(total),
        "kid_count": int(kid_count),
        "teacher_count": int(teacher_count),
    }
