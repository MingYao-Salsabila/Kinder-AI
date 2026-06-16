from __future__ import annotations

import dataclasses

import pytest

from app.core.providers import get_provider
from app.core.providers.stub import StubProvider


def test_get_provider_returns_stub_when_not_live(settings):
    provider = get_provider(settings)

    assert isinstance(provider, StubProvider)
    assert provider.name == "stub"


def test_get_provider_returns_gemini_when_live(settings):
    pytest.importorskip("google.genai")
    live_settings = dataclasses.replace(settings, gemini_use_stub=False, gemini_api_key="a-real-looking-key")

    provider = get_provider(live_settings)

    assert provider.name == "gemini"


def test_stub_provider_is_deterministic_and_marks_is_stub():
    provider = StubProvider()

    result = provider.generate("system", "How do plants make food?", mode="kid")

    assert result.is_stub is True
    assert result.error is None
    assert "How do plants make food?" in result.text


def test_stub_provider_kid_mode_uses_snippets():
    provider = StubProvider()
    snippets = [
        {"title": "Plants and Photosynthesis", "content": "Plants make food using sunlight.", "source": "plants.md"}
    ]

    result = provider.generate("system", "How do plants make food?", mode="kid", snippets=snippets, learner_name="Ana")

    assert "Ana" in result.text
    assert "Plants and Photosynthesis" in result.text


def test_stub_provider_teacher_mode_structure():
    provider = StubProvider()

    result = provider.generate("system", "Explain fractions", mode="teacher")

    assert "Explanation" in result.text
    assert "Check for understanding" in result.text
