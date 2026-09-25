"""Small presentation and time-formatting helpers."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


def today_iso() -> str:
    return date.today().isoformat()


def now_time() -> str:
    return datetime.now().strftime("%H:%M")


def display_date(value: Any) -> str:
    text = str(value or "")
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").strftime("%b %d, %Y")
    except ValueError:
        return text or "—"


def display_time(value: Any) -> str:
    text = str(value or "")
    try:
        return datetime.strptime(text[:5], "%H:%M").strftime("%I:%M %p").lstrip("0")
    except ValueError:
        return text or "—"


def as_text(value: Any, fallback: str = "—") -> str:
    text = str(value or "").strip()
    return text if text else fallback
