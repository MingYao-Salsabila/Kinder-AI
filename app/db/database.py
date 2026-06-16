from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.core.progress import ProgressSummary

SCHEMA_SQL_PATH = Path(__file__).with_name("schema.sql")

DEFAULT_LEARNER_ID = "guest"
DEFAULT_LESSON_NAME = "General"


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


# ---------------------------------------------------------------------------
# Conversation log
# ---------------------------------------------------------------------------

def save_conversation(sqlite_path: Path, mode: str, prompt: str, response: str) -> None:
    with _connect(sqlite_path) as conn:
        conn.execute(
            "INSERT INTO conversations (mode, prompt, response) VALUES (?, ?, ?)",
            (mode, prompt, response),
        )
        conn.commit()


def get_recent_conversations(sqlite_path: Path, limit: int = 10, mode: str | None = None) -> list[dict[str, Any]]:
    query = "SELECT id, mode, prompt, response, created_at FROM conversations"
    params: tuple[Any, ...]
    if mode:
        query += " WHERE mode = ?"
        params = (mode, limit)
    else:
        params = (limit,)
    query += " ORDER BY id DESC LIMIT ?"

    with _connect(sqlite_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def clear_conversations(sqlite_path: Path) -> int:
    """Delete all conversation log entries. Returns the number of rows removed."""
    with _connect(sqlite_path) as conn:
        before = conn.execute("SELECT COUNT(*) AS count FROM conversations").fetchone()["count"]
        conn.execute("DELETE FROM conversations")
        conn.commit()
    return int(before)


# ---------------------------------------------------------------------------
# Dashboard summary
# ---------------------------------------------------------------------------

def get_dashboard_summary(sqlite_path: Path) -> dict[str, int]:
    with _connect(sqlite_path) as conn:
        total = conn.execute("SELECT COUNT(*) AS count FROM conversations").fetchone()["count"]
        kid_count = conn.execute("SELECT COUNT(*) AS count FROM conversations WHERE mode = 'kid'").fetchone()["count"]
        teacher_count = conn.execute(
            "SELECT COUNT(*) AS count FROM conversations WHERE mode = 'teacher'"
        ).fetchone()["count"]
        quiz_count = conn.execute("SELECT COUNT(*) AS count FROM quiz_attempts").fetchone()["count"]
        learner_count = conn.execute(
            "SELECT COUNT(DISTINCT learner_id) AS count FROM learner_progress"
        ).fetchone()["count"]
    return {
        "conversation_count": int(total),
        "kid_count": int(kid_count),
        "teacher_count": int(teacher_count),
        "quiz_attempt_count": int(quiz_count),
        "learner_count": int(learner_count),
    }


# ---------------------------------------------------------------------------
# Learner progress
# ---------------------------------------------------------------------------

def record_lesson_progress(
    sqlite_path: Path,
    learner_id: str,
    lesson_name: str,
    completed: bool = True,
    badges_earned: int = 0,
) -> None:
    """Record (or update) progress on a lesson for a learner.

    Existing rows for the same ``(learner_id, lesson_name)`` pair are
    updated in place (``completed`` is OR-ed in, ``badges`` accumulate);
    otherwise a new row is inserted. ``updated_at`` is refreshed either way,
    which is also what drives the "active days" count used for streaks.
    """

    learner_id = (learner_id or DEFAULT_LEARNER_ID).strip() or DEFAULT_LEARNER_ID
    lesson_name = (lesson_name or DEFAULT_LESSON_NAME).strip() or DEFAULT_LESSON_NAME
    badges_earned = max(0, int(badges_earned))

    with _connect(sqlite_path) as conn:
        row = conn.execute(
            "SELECT id, completed, badges FROM learner_progress WHERE learner_id = ? AND lesson_name = ?",
            (learner_id, lesson_name),
        ).fetchone()

        if row is None:
            conn.execute(
                """
                INSERT INTO learner_progress (learner_id, lesson_name, completed, badges, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (learner_id, lesson_name, int(bool(completed)), badges_earned),
            )
        else:
            new_completed = max(int(row["completed"]), int(bool(completed)))
            new_badges = int(row["badges"]) + badges_earned
            conn.execute(
                "UPDATE learner_progress SET completed = ?, badges = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_completed, new_badges, row["id"]),
            )
        conn.commit()


def get_learner_progress_summary(sqlite_path: Path, learner_id: str) -> ProgressSummary:
    learner_id = (learner_id or DEFAULT_LEARNER_ID).strip() or DEFAULT_LEARNER_ID
    with _connect(sqlite_path) as conn:
        row = conn.execute(
            """
            SELECT
                COALESCE(SUM(completed), 0) AS completed_lessons,
                COALESCE(SUM(badges), 0) AS badges,
                COUNT(DISTINCT DATE(updated_at)) AS streak_days
            FROM learner_progress
            WHERE learner_id = ?
            """,
            (learner_id,),
        ).fetchone()

    return ProgressSummary(
        learner_id=learner_id,
        completed_lessons=int(row["completed_lessons"] or 0),
        badges=int(row["badges"] or 0),
        streak_days=int(row["streak_days"] or 0),
    )


def list_learner_progress(sqlite_path: Path) -> list[dict[str, Any]]:
    """Per-learner progress totals, most recently active first. Used by Admin Mode."""
    with _connect(sqlite_path) as conn:
        rows = conn.execute(
            """
            SELECT
                learner_id,
                COUNT(*) AS lessons_tracked,
                COALESCE(SUM(completed), 0) AS completed_lessons,
                COALESCE(SUM(badges), 0) AS badges,
                COUNT(DISTINCT DATE(updated_at)) AS active_days,
                MAX(updated_at) AS last_activity
            FROM learner_progress
            GROUP BY learner_id
            ORDER BY last_activity DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Quiz attempts
# ---------------------------------------------------------------------------

def record_quiz_attempt(
    sqlite_path: Path, learner_id: str, topic: str, total_questions: int, correct_answers: int
) -> None:
    learner_id = (learner_id or DEFAULT_LEARNER_ID).strip() or DEFAULT_LEARNER_ID
    topic = (topic or DEFAULT_LESSON_NAME).strip() or DEFAULT_LESSON_NAME
    total_questions = max(0, int(total_questions))
    correct_answers = max(0, min(int(correct_answers), total_questions))

    with _connect(sqlite_path) as conn:
        conn.execute(
            """
            INSERT INTO quiz_attempts (learner_id, topic, total_questions, correct_answers)
            VALUES (?, ?, ?, ?)
            """,
            (learner_id, topic, total_questions, correct_answers),
        )
        conn.commit()


def list_recent_quiz_attempts(
    sqlite_path: Path, limit: int = 10, learner_id: str | None = None
) -> list[dict[str, Any]]:
    query = "SELECT id, learner_id, topic, total_questions, correct_answers, created_at FROM quiz_attempts"
    params: tuple[Any, ...]
    if learner_id:
        query += " WHERE learner_id = ?"
        params = (learner_id, limit)
    else:
        params = (limit,)
    query += " ORDER BY id DESC LIMIT ?"

    with _connect(sqlite_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# App settings
# ---------------------------------------------------------------------------

def get_app_settings(sqlite_path: Path) -> dict[str, str]:
    with _connect(sqlite_path) as conn:
        rows = conn.execute("SELECT setting_key, setting_value FROM app_settings ORDER BY setting_key").fetchall()
    return {row["setting_key"]: row["setting_value"] for row in rows}


def set_app_setting(sqlite_path: Path, key: str, value: str) -> None:
    with _connect(sqlite_path) as conn:
        conn.execute(
            "INSERT INTO app_settings (setting_key, setting_value) VALUES (?, ?) "
            "ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value",
            (key, value),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Demo seed data
# ---------------------------------------------------------------------------

_SEED_FLAG_KEY = "demo_seeded"


def seed_demo_content(sqlite_path: Path) -> None:
    """Insert a small set of demo rows the first time the app runs.

    Uses an ``app_settings`` flag (rather than checking table counts) so
    that an admin clearing the conversation log later doesn't trigger
    re-seeding and duplicate demo rows.
    """

    initialize_database(sqlite_path)
    with _connect(sqlite_path) as conn:
        already_seeded = conn.execute(
            "SELECT 1 FROM app_settings WHERE setting_key = ?", (_SEED_FLAG_KEY,)
        ).fetchone()
        if already_seeded:
            return

        conn.executemany(
            "INSERT INTO conversations (mode, prompt, response) VALUES (?, ?, ?)",
            [
                ("kid", "What is a plant?",
                 "A plant is a living thing that grows and makes its own food from sunlight."),
                ("teacher", "Explain fractions",
                 "Fractions show parts of a whole and can be taught with pizza or pie examples."),
                ("admin", "Show logs", "Admin review response for demo data."),
            ],
        )
        conn.executemany(
            "INSERT INTO learner_progress (learner_id, lesson_name, completed, badges) VALUES (?, ?, ?, ?)",
            [
                ("Demo Learner", "What is a plant?", 1, 1),
                ("Demo Learner", "Fractions basics", 1, 0),
            ],
        )
        conn.executemany(
            "INSERT INTO quiz_attempts (learner_id, topic, total_questions, correct_answers) VALUES (?, ?, ?, ?)",
            [("Demo Learner", "plants", 3, 2)],
        )
        conn.executemany(
            "INSERT OR REPLACE INTO app_settings (setting_key, setting_value) VALUES (?, ?)",
            [
                ("theme", "shared"),
                ("language", "en"),
                (_SEED_FLAG_KEY, "true"),
            ],
        )
        conn.commit()
