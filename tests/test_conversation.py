from __future__ import annotations

from app.core.conversation import ConversationService, get_conversation_service
from app.core.models import LearnerProfile


def test_blocked_kid_prompt_returns_safe_refusal(settings):
    service = ConversationService(settings)

    response = service.respond("Tell me about weapons", mode="kid", audience="kid")

    assert response.is_stub is True
    assert response.provider_name == "safety"
    assert "science" in response.text or "reading" in response.text


def test_kid_mode_grounds_response_in_knowledge_base(populated_settings):
    service = ConversationService(populated_settings)
    learner = LearnerProfile(learner_id="ana", display_name="Ana", grade_level="3-5")

    response = service.respond("How do plants make food?", mode="kid", audience="kid", learner=learner)

    assert response.is_stub is True  # stub mode in tests
    assert response.provider_name == "stub"
    assert "Plants and Photosynthesis" in response.sources
    assert "Ana" in response.text


def test_teacher_mode_without_matching_lesson_has_no_sources(settings):
    service = ConversationService(settings)

    response = service.respond("Explain long division", mode="teacher", audience="general")

    assert response.sources == []
    assert "Explanation" in response.text


def test_admin_mode_does_not_use_retrieval_by_default(populated_settings):
    service = ConversationService(populated_settings)

    response = service.respond("How do plants make food?", mode="admin", audience="general")

    assert response.sources == []


def test_get_conversation_service_is_cached(settings):
    first = get_conversation_service(settings)
    second = get_conversation_service(settings)

    assert first is second
