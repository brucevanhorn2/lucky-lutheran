"""Rotating daily portion of Luther's Small Catechism."""

from __future__ import annotations

import datetime as dt
from importlib import resources

import yaml


def _portions() -> list[dict]:
    ref = resources.files("luckylutheran") / "data" / "small_catechism.yaml"
    return yaml.safe_load(ref.read_text(encoding="utf-8"))["portions"]


def portion_for(date: dt.date) -> dict:
    """The day's catechism portion, cycling through the list by day of year."""
    portions = _portions()
    doy = date.timetuple().tm_yday
    entry = portions[(doy - 1) % len(portions)]
    return {
        "title": entry["title"],
        "text": entry["text"].strip(),
        "meaning": entry.get("meaning", "").strip(),
    }
