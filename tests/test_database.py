from __future__ import annotations

from app.db.database import (
    clear_conversations,
    get_app_settings,
    get_dashboard_summary,
    get_learner_progress_summary,
    get_recent_conversations,
    initialize_database,
    list_learner_progress,
    list_recent_quiz_attempts,
    record_lesson_progress,
    record_quiz_attempt,
    save_conversation,
    seed_demo_content,
    set_app_setting,
)


def test_initialize_database_creates_all_tables(tmp_path):
    db_path = tmp_path / "kinderai.sqlite3"

    initialize_database(db_path)

    assert db_path.exists()
    # Each call below queries a different table -- none should raise.
    assert get_recent_conversations(db_path) == []
    assert list_learner_progress(db_path) == []
    assert list_recent_quiz_attempts(db_path) == []
    assert get_app_settings(db_path) == {}


def test_save_and_filter_conversations(tmp_path):
    db_path = tmp_path / "kinderai.sqlite3"
    initialize_database(db_path)

    save_conversation(db_path, "kid", "What is a plant?", "A plant is...")
    save_conversation(db_path, "teacher", "Explain fractions", "Fractions are...")

    assert len(get_recent_conversations(db_path, limit=10)) == 2

    kid_rows = get_recent_conversations(db_path, limit=10, mode="kid")
    assert len(kid_rows) == 1
    assert kid_rows[0]["prompt"] == "What is a plant?"


def test_clear_conversations_removes_all_rows(tmp_path):
    db_path = tmp_path / "kinderai.sqlite3"
    initialize_database(db_path)
    save_conversation(db_path, "kid", "Q1", "A1")
    save_conversation(db_path, "kid", "Q2", "A2")

    removed = clear_conversations(db_path)

    assert removed == 2
    assert get_recent_conversations(db_path) == []


def test_dashboard_summary_counts(tmp_path):
    db_path = tmp_path / "kinderai.sqlite3"
    initialize_database(db_path)
    save_conversation(db_path, "kid", "Q", "A")
    save_conversation(db_path, "teacher", "Q", "A")
    record_quiz_attempt(db_path, "Ana", "plants", 3, 2)
    record_lesson_progress(db_path, "Ana", "plants", completed=True, badges_earned=1)

    summary = get_dashboard_summary(db_path)

    assert summary["conversation_count"] == 2
    assert summary["kid_count"] == 1
    assert summary["teacher_count"] == 1
    assert summary["quiz_attempt_count"] == 1
    assert summary["learner_count"] == 1


def test_record_lesson_progress_accumulates_within_a_lesson(tmp_path):
    db_path = tmp_path / "kinderai.sqlite3"
    initialize_database(db_path)

    record_lesson_progress(db_path, "Ana", "Plants", completed=True, badges_earned=1)
    record_lesson_progress(db_path, "Ana", "Plants", completed=True, badges_earned=1)
    record_lesson_progress(db_path, "Ana", "Water cycle", completed=True, badges_earned=0)

    summary = get_learner_progress_summary(db_path, "Ana")

    assert summary.completed_lessons == 2  # one completed row per distinct lesson
    assert summary.badges == 2  # badges accumulate within the same lesson


def test_record_lesson_progress_defaults_blank_learner_to_guest(tmp_path):
    db_path = tmp_path / "kinderai.sqlite3"
    initialize_database(db_path)

    record_lesson_progress(db_path, "   ", "Plants", completed=True)

    summary = get_learner_progress_summary(db_path, "guest")
    assert summary.completed_lessons == 1


def test_list_learner_progress_groups_by_learner(tmp_path):
    db_path = tmp_path / "kinderai.sqlite3"
    initialize_database(db_path)
    record_lesson_progress(db_path, "Ana", "Plants", completed=True, badges_earned=1)
    record_lesson_progress(db_path, "Ben", "Fractions", completed=False)

    rows = list_learner_progress(db_path)

    assert {row["learner_id"] for row in rows} == {"Ana", "Ben"}


def test_record_and_list_quiz_attempts_most_recent_first(tmp_path):
    db_path = tmp_path / "kinderai.sqlite3"
    initialize_database(db_path)

    record_quiz_attempt(db_path, "Ana", "plants", 3, 2)
    record_quiz_attempt(db_path, "Ana", "fractions", 2, 2)

    rows = list_recent_quiz_attempts(db_path, learner_id="Ana")

    assert [row["topic"] for row in rows] == ["fractions", "plants"]


def test_quiz_attempt_correct_answers_are_clamped_to_total(tmp_path):
    db_path = tmp_path / "kinderai.sqlite3"
    initialize_database(db_path)

    record_quiz_attempt(db_path, "Ana", "plants", 2, 99)

    rows = list_recent_quiz_attempts(db_path)
    assert rows[0]["correct_answers"] == 2


def test_app_settings_round_trip_and_overwrite(tmp_path):
    db_path = tmp_path / "kinderai.sqlite3"
    initialize_database(db_path)

    set_app_setting(db_path, "theme", "kid")
    set_app_setting(db_path, "theme", "teacher")

    assert get_app_settings(db_path)["theme"] == "teacher"


def test_seed_demo_content_is_idempotent(tmp_path):
    db_path = tmp_path / "kinderai.sqlite3"

    seed_demo_content(db_path)
    first_count = get_dashboard_summary(db_path)["conversation_count"]

    seed_demo_content(db_path)
    second_count = get_dashboard_summary(db_path)["conversation_count"]

    assert first_count == second_count > 0


def test_seed_demo_content_does_not_return_after_clearing_logs(tmp_path):
    db_path = tmp_path / "kinderai.sqlite3"
    seed_demo_content(db_path)

    clear_conversations(db_path)
    seed_demo_content(db_path)

    assert get_dashboard_summary(db_path)["conversation_count"] == 0
