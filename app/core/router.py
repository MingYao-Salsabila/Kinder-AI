from __future__ import annotations

from app.config import AppSettings
from app.core.database_helpers import normalize_mode
from app.modes.admin_mode import render_admin_mode
from app.modes.kid_mode import render_kid_mode
from app.modes.landing import render_landing_mode
from app.modes.teacher_mode import render_teacher_mode

_RENDERERS = {
    "landing": render_landing_mode,
    "kid": render_kid_mode,
    "teacher": render_teacher_mode,
    "admin": render_admin_mode,
}


def render_mode(mode: str, settings: AppSettings) -> None:
    renderer = _RENDERERS.get(normalize_mode(mode), render_landing_mode)
    renderer(settings)
