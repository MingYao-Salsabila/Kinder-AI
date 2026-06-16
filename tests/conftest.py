from __future__ import annotations

from pathlib import Path

import pytest

from app.config import AppSettings


@pytest.fixture
def settings(tmp_path: Path) -> AppSettings:
    """An AppSettings pointing at isolated, temporary paths (stub mode)."""
    return AppSettings(
        app_name="KinderAi",
        app_env="test",
        default_mode="landing",
        gemini_api_key="stub-gemini-api-key",
        gemini_model="gemini-2.5-flash",
        gemini_use_stub=True,
        sqlite_path=tmp_path / "db" / "kinderai.sqlite3",
        vector_index_path=tmp_path / "vector_index",
        knowledge_base_path=tmp_path / "knowledge_base",
        max_response_tokens=512,
    )


@pytest.fixture
def populated_settings(settings: AppSettings) -> AppSettings:
    """Settings whose knowledge base has a couple of real lesson notes."""
    kb = settings.knowledge_base_path
    kb.mkdir(parents=True, exist_ok=True)

    (kb / "plants.md").write_text(
        "# Plants and Photosynthesis\n\n"
        "Plants are living things that make their own food. "
        "They use sunlight, water, and carbon dioxide in a process called photosynthesis.\n",
        encoding="utf-8",
    )
    (kb / "water_cycle.md").write_text(
        "# The Water Cycle\n\n"
        "Water evaporates into the air, condenses into clouds, falls as rain, "
        "and collects in rivers and oceans before evaporating again.\n",
        encoding="utf-8",
    )
    return settings
