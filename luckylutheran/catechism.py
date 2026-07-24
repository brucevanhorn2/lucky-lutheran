"""Rotating daily portion of Luther's Small Catechism."""

from __future__ import annotations

import datetime as dt
from importlib import resources

import yaml

from luckylutheran import scripture


def _portions() -> list[dict]:
    ref = resources.files("luckylutheran") / "data" / "small_catechism.yaml"
    return yaml.safe_load(ref.read_text(encoding="utf-8"))["portions"]


def portion_for(date: dt.date) -> dict:
    """The day's catechism portion, cycling through the list by day of year.

    Most portions carry their own `text`. Table of Duties / Words of
    Institution entries instead carry a `reference` (a Bible citation) and
    are resolved to real KJV text via scripture.get_passage — the same
    fetch-and-cache path the daily lectionary readings use — so no
    scripture is hand-transcribed in the YAML."""
    portions = _portions()
    doy = date.timetuple().tm_yday
    entry = portions[(doy - 1) % len(portions)]
    text = entry.get("text")
    if text is None and "reference" in entry:
        text = scripture.get_passage(entry["reference"])
        if text is None:
            text = (f"[Text of {entry['reference']} unavailable — will be "
                     "fetched at build time from the KJV.]")
    return {
        "title": entry["title"],
        "text": (text or "").strip(),
        "meaning": entry.get("meaning", "").strip(),
        "citation": entry.get("citation", ""),
    }
