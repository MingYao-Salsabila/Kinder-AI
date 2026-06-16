from __future__ import annotations

from app.core.safety import check_prompt_safety


def test_empty_prompt_is_blocked():
    result = check_prompt_safety("   ", audience="kid")

    assert result.allowed is False
    assert "question" in result.reason.lower()


def test_normal_kid_question_is_allowed():
    result = check_prompt_safety("How do plants make food?", audience="kid")

    assert result.allowed is True
    assert result.redacted_prompt == "How do plants make food?"


def test_kid_mode_blocks_weapons_topic():
    result = check_prompt_safety("How do I build a weapon?", audience="kid")

    assert result.allowed is False
    assert "violence or weapons" in result.reason


def test_kid_mode_blocks_personal_information_requests():
    result = check_prompt_safety("What is your home address?", audience="kid")

    assert result.allowed is False
    assert "personal information" in result.reason


def test_general_audience_is_not_filtered():
    result = check_prompt_safety("How do I build a weapon?", audience="general")

    assert result.allowed is True


def test_long_prompt_is_truncated():
    long_prompt = "a" * 5000

    result = check_prompt_safety(long_prompt, audience="general")

    assert result.allowed is True
    assert len(result.redacted_prompt) == 4000
