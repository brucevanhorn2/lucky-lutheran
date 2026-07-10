"""Daily readings.

Two layers:

1. The official table (data/daily_lectionary.yaml), keyed by "MM-DD". This
   ships nearly empty — the LCMS daily lectionary should be typed in from
   lcms.org or the hymnal (it is a list of citations, i.e. uncopyrightable
   facts, but it still has to be entered once).

2. A deterministic FALLBACK plan used for any date not in the table, so the
   pipeline always produces a real episode: mornings read sequentially
   through the Gospels, evenings through Acts and the Epistles, one chapter
   per day. Clearly labeled as the fallback, not the official lectionary.

Psalms follow a simple continuous cycle (Psalm 119 excluded for length):
one psalm each morning and each evening, walking through the Psalter.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from importlib import resources

import yaml

GOSPEL_CHAPTERS = [("Matthew", 28), ("Mark", 16), ("Luke", 24), ("John", 21)]
EPISTLE_CHAPTERS = [
    ("Acts", 28), ("Romans", 16), ("1 Corinthians", 16), ("2 Corinthians", 13),
    ("Galatians", 6), ("Ephesians", 6), ("Philippians", 4), ("Colossians", 4),
    ("1 Thessalonians", 5), ("2 Thessalonians", 3), ("1 Timothy", 6),
    ("2 Timothy", 4), ("Titus", 3), ("Philemon", 1), ("Hebrews", 13),
    ("James", 5), ("1 Peter", 5), ("2 Peter", 3), ("1 John", 5),
    ("2 John", 1), ("3 John", 1), ("Jude", 1), ("Revelation", 22),
]

# Psalter cycle, skipping 119 (176 verses is too long for a 10-minute office).
PSALM_CYCLE = [n for n in range(1, 151) if n != 119]


@dataclass(frozen=True)
class DailyReadings:
    psalm: str
    reading: str
    source: str  # "official" or "fallback"


def _official_table() -> dict:
    ref = resources.files("luckylutheran") / "data" / "daily_lectionary.yaml"
    data = yaml.safe_load(ref.read_text(encoding="utf-8")) or {}
    return data.get("days") or {}


def _nth_chapter(books: list[tuple[str, int]], n: int) -> str:
    total = sum(ch for _, ch in books)
    n = n % total
    for book, chapters in books:
        if n < chapters:
            return f"{book} {n + 1}"
        n -= chapters
    raise AssertionError("unreachable")


def readings_for(date: dt.date, office: str) -> DailyReadings:
    """Readings for a date and office ('matins' morning, else evening)."""
    morning = office == "matins"
    doy = date.timetuple().tm_yday

    psalm_index = (doy - 1) * 2 + (0 if morning else 1)
    psalm = f"Psalm {PSALM_CYCLE[psalm_index % len(PSALM_CYCLE)]}"

    key = date.strftime("%m-%d")
    entry = _official_table().get(key)
    if entry:
        reading = entry["morning"] if morning else entry["evening"]
        return DailyReadings(psalm=entry.get("psalm", psalm),
                             reading=reading, source="official")

    if morning:
        reading = _nth_chapter(GOSPEL_CHAPTERS, doy - 1)
    else:
        reading = _nth_chapter(EPISTLE_CHAPTERS, doy - 1)
    return DailyReadings(psalm=psalm, reading=reading, source="fallback")
