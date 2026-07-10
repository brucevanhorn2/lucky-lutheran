"""Collect of the day, resolved from the church calendar."""

from __future__ import annotations

from importlib import resources

import yaml

from luckylutheran.churchyear import ChurchDay


def _load() -> dict:
    ref = resources.files("luckylutheran") / "data" / "collects.yaml"
    return yaml.safe_load(ref.read_text(encoding="utf-8"))


def collect_of_the_day(day: ChurchDay) -> dict:
    """Return {'title': ..., 'text': ...} for the day's season.

    Per-Sunday propers can later be added to collects.yaml and looked up here
    before falling back to the seasonal collect.
    """
    data = _load()
    seasons = data["seasons"]
    entry = seasons.get(day.season) or seasons["trinity"]
    return {"title": entry["title"], "text": entry["text"].strip()}
