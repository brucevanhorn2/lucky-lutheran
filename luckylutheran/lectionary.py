"""Daily readings: the LSB daily lectionary, with a deterministic fallback.

The official table (data/daily_lectionary.yaml, transcribed from the
Lutheran Service Book's Daily Lectionary, pp. 299-304) keys days two ways,
per the lectionary's own design:

  movable: "ash+N" — N days after Ash Wednesday; covers Ash Wednesday
           through the Saturday after Pentecost (N = 0..101), so the
           Lent/Easter readings follow the movable church year.
  days:    "MM-DD" — the civil calendar; covers Nov 27 (the earliest
           possible eve of Advent) until the beginning of Lent. When both
           schemes could apply (Lent reaching into the civil range), the
           movable table wins, as in the book.

Each day appoints a first (Old Testament) and second (New Testament)
reading, plus an occasional optional third covering material otherwise
passed over. Matins reads the first lesson; Vespers/Compline the second.

Psalms come from the Table of Psalms for Daily Prayer (LSB p. 304):
weekday tables for Lent, Easter, and Advent; date-keyed Christmastide;
and four "general" weeks repeating through Epiphany and the Time of the
Church. Evening rows appoint two psalms ("42; 32").

Dates missing from the reading tables (the summer Time-of-the-Church
stretch is not yet transcribed) fall back to a deterministic plan —
mornings sequentially through the Gospels, evenings through Acts and the
Epistles — labeled "fallback", never "official".
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from functools import cache
from importlib import resources

import yaml

from luckylutheran.churchyear import advent_start, easter

GOSPEL_CHAPTERS = [("Matthew", 28), ("Mark", 16), ("Luke", 24), ("John", 21)]
EPISTLE_CHAPTERS = [
    ("Acts", 28), ("Romans", 16), ("1 Corinthians", 16), ("2 Corinthians", 13),
    ("Galatians", 6), ("Ephesians", 6), ("Philippians", 4), ("Colossians", 4),
    ("1 Thessalonians", 5), ("2 Thessalonians", 3), ("1 Timothy", 6),
    ("2 Timothy", 4), ("Titus", 3), ("Philemon", 1), ("Hebrews", 13),
    ("James", 5), ("1 Peter", 5), ("2 Peter", 3), ("1 John", 5),
    ("2 John", 1), ("3 John", 1), ("Jude", 1), ("Revelation", 22),
]

# Indexed by date.weekday() (Monday = 0), matching the psalm-table keys.
WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


@dataclass(frozen=True)
class DailyReadings:
    psalm: str
    reading: str
    source: str  # "official" or "fallback"
    optional: str | None = None  # the italic third reading (show notes)


@cache
def _tables() -> dict:
    ref = resources.files("luckylutheran") / "data" / "daily_lectionary.yaml"
    return yaml.safe_load(ref.read_text(encoding="utf-8")) or {}


def _days_since_ash_wednesday(date: dt.date) -> int:
    return (date - (easter(date.year) - dt.timedelta(days=46))).days


def _official_entry(date: dt.date) -> dict | None:
    tables = _tables()
    n = _days_since_ash_wednesday(date)
    if 0 <= n <= 101:
        return (tables.get("movable") or {}).get(f"ash+{n}")
    return (tables.get("days") or {}).get(date.strftime("%m-%d"))


def _psalm_row(date: dt.date) -> dict:
    """The day's row {morning, evening} from the Table of Psalms."""
    psalms = _tables()["psalms"]
    row = psalms["christmas"].get(date.strftime("%m-%d"))
    if row:
        return row
    weekday = WEEKDAYS[date.weekday()]
    n = _days_since_ash_wednesday(date)
    if 0 <= n <= 45:  # Ash Wednesday through Holy Saturday
        return psalms["lent"][weekday]
    if 46 <= n <= 101:  # Easter through the Saturday after Pentecost
        return psalms["easter"][weekday]
    if date >= advent_start(date.year):
        return psalms["advent"][weekday]
    # Epiphany and the Time of the Church: the four General weeks repeat,
    # Sunday-aligned so the row changes at the start of the liturgical week.
    week = (date.toordinal() - date.isoweekday() % 7) // 7 % 4 + 1
    return psalms[f"general-{week}"][weekday]


def _format_psalms(spec: str) -> str:
    """Table entry to citation(s): "42; 32" -> "Psalm 42; Psalm 32"."""
    return "; ".join(f"Psalm {part.strip()}" for part in str(spec).split(";"))


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
    psalm = _format_psalms(_psalm_row(date)["morning" if morning else "evening"])

    entry = _official_entry(date)
    if entry:
        return DailyReadings(
            psalm=psalm,
            reading=entry["first"] if morning else entry["second"],
            source="official",
            optional=entry.get("optional"),
        )

    doy = date.timetuple().tm_yday
    books = GOSPEL_CHAPTERS if morning else EPISTLE_CHAPTERS
    return DailyReadings(psalm=psalm, reading=_nth_chapter(books, doy - 1),
                         source="fallback")
