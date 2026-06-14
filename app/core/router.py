from __future__ import annotations

from app.config import AppSettings
from app.modes.admin_mode import render_admin_mode
from app.modes.kid_mode import render_kid_mode
from app.modes.landing import render_landing_mode
from app.modes.teacher_mode import render_teacher_mode


def render_mode(mode: str, settings: AppSettings) -> None:
    if mode == "landing":
        render_landing_mode(settings)
    elif mode == "kid":
        render_kid_mode(settings)
    elif mode == "teacher":
        render_teacher_mode(settings)
    elif mode == "admin":
        render_admin_mode(settings)
    else:
        render_landing_mode(settings)
