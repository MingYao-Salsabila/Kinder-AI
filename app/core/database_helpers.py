from __future__ import annotations


def preview_text(text: str, limit: int = 120) -> str:
    clean = " ".join((text or "").split())
    if len(clean) <= limit:
        return clean
    return clean[: max(0, limit - 1)].rstrip() + "…"


def normalize_mode(mode: str) -> str:
    value = (mode or "").strip().lower()
    if value in {"kid", "teacher", "admin", "landing"}:
        return value
    return "landing"
