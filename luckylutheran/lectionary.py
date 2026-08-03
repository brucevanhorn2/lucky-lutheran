"""Daily readings and psalms, entirely from public-domain sources.

Everything here derives from the *Common Service Book of the Lutheran Church*
(1917) — the same edition already used for Matins, Vespers, the collects and
the Evening Suffrages — plus, for weekdays, a reading *method* rather than
any table at all. See SOURCES.md.

Three parts:

  Sundays and festivals
      The historic one-year lectionary: an Epistle and a Gospel appointed to
      each proper. data/temporale.yaml carries the 71 propers of the church
      year (Advent 1 through Trinity 27), data/sanctorale.yaml the 23 fixed
      festivals. churchyear.proper_for_office() resolves a date to a proper.
      The Gospel is read in the morning and the Epistle in the evening,
      matching the weekday arrangement below.

  Weekdays
      Continuous course reading — the Gospels in the morning, Acts and the
      Epistles in the evening, advancing a chapter a day. This is a *method*,
      not a compilation, and 17 USC 102(b) excludes methods from copyright
      outright, so it needs no source at all. It is also close to Luther's own
      practice in the Deutsche Messe (1526), which assigned books to weekdays
      and worked through them in course.

  Psalms
      data/proper_psalms.yaml, the CSB's Table of Proper Psalms for Festivals
      and Seasons. Note this is a *pool per season*, not a day-keyed table:
      the book appoints a set and leaves the choice open. We choose from the
      pool deterministically by day-of-year, so a given date always yields the
      same psalm and episodes stay reproducible.

The LSB daily lectionary this replaced was transcribed from a current
commercial product on an untested "facts aren't copyrightable" argument, and
supplied the psalm tables as well as the readings. Both are now gone.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from functools import cache
from importlib import resources

import yaml

from luckylutheran.churchyear import church_day, proper_for_office

GOSPEL_CHAPTERS = [("Matthew", 28), ("Mark", 16), ("Luke", 24), ("John", 21)]
EPISTLE_CHAPTERS = [
    ("Acts", 28), ("Romans", 16), ("1 Corinthians", 16), ("2 Corinthians", 13),
    ("Galatians", 6), ("Ephesians", 6), ("Philippians", 4), ("Colossians", 4),
    ("1 Thessalonians", 5), ("2 Thessalonians", 3), ("1 Timothy", 6),
    ("2 Timothy", 4), ("Titus", 3), ("Philemon", 1), ("Hebrews", 13),
    ("James", 5), ("1 Peter", 5), ("2 Peter", 3), ("1 John", 5),
    ("2 John", 1), ("3 John", 1), ("Jude", 1), ("Revelation", 22),
]

# Season -> key in proper_psalms.yaml. The psalm table is organised by
# festival and season rather than by the season names churchyear.py uses.
_PSALM_SEASON = {
    "advent": "advent", "christmas": "christmas", "epiphany": "epiphany",
    "pre_lent": "pre-lent", "lent": "lent", "holy_week": "holy-week",
    "easter": "eastertide", "ascension": "ascension",
    "pentecost": "whitsunday", "trinity": "christian-life",
}

# Propers with a psalm pool of their own, overriding the season.
_PSALM_PROPER = {
    "ash-wednesday": "ash-wednesday", "palm-sunday": "palm-sunday",
    "good-friday": "good-friday", "easter-day": "easter-day",
    "ascension": "ascension", "pentecost": "whitsunday",
    "trinity-sunday": "trinity-sunday", "reformation": "reformation",
    "new-year": "new-year", "epiphany": "epiphany",
    "christmas-day-early": "christmas", "christmas-day-later": "christmas",
    "christmas-day-second": "christmas", "all-saints": "apostles-evangelists-martyrs",
    "st-michael-all-angels": "st-michael", "thanksgiving": "thanksgiving",
    "harvest": "harvest", "humiliation-prayer": "humiliation-and-prayer",
}


@dataclass(frozen=True)
class DailyReadings:
    psalm: str
    reading: str
    source: str            # "proper" (appointed) or "course" (read in course)
    proper: str | None = None   # the proper's id, when one governs the day
    title: str | None = None    # its human-readable name, for show notes


def _load(name: str) -> dict:
    ref = resources.files("luckylutheran") / "data" / name
    return yaml.safe_load(ref.read_text(encoding="utf-8")) or {}


@cache
def _propers() -> dict[str, dict]:
    out = {}
    for f in ("temporale.yaml", "sanctorale.yaml"):
        for p in _load(f).get("propers", []):
            out[p["id"]] = p
    return out


@cache
def _psalm_pools() -> dict[str, list[int]]:
    return {k: v["psalms"] for k, v in _load("proper_psalms.yaml")["seasons"].items()}


def _festival_for(date: dt.date) -> str | None:
    """A fixed-date festival falling on `date`, if the sanctorale has one."""
    stamp = date.strftime("%B %-d")
    for pid, p in _propers().items():
        if p.get("date") == stamp:
            return pid
    return None


def _psalm_for(date: dt.date, proper: str | None) -> str:
    """Choose deterministically from the pool the CSB appoints.

    The table gives a set per season and leaves the choice open, so the
    choice is ours; keying it to the day of the year keeps a given date
    always yielding the same psalm.
    """
    pools = _psalm_pools()
    key = _PSALM_PROPER.get(proper or "")
    if key is None:
        season = church_day(date).season
        key = _PSALM_SEASON.get(season, "christian-life")
        if proper and proper.startswith(("st-", "all-", "conversion", "annunciation",
                                         "presentation", "visitation", "nativity-")):
            key = "apostles-evangelists-martyrs"
    pool = pools.get(key) or pools["christian-life"]
    return f"Psalm {pool[date.timetuple().tm_yday % len(pool)]}"


def _nth_chapter(books: list[tuple[str, int]], n: int) -> str:
    total = sum(ch for _, ch in books)
    n = n % total
    for book, chapters in books:
        if n < chapters:
            return f"{book} {n + 1}"
        n -= chapters
    raise AssertionError("unreachable")


# The Evening Suffrages is deliberately *invariable*. Its rubric calls for "a
# Psalm, a brief Lesson with the Response, and a Hymn" but appoints none of
# them — the same open hand the CSB's psalm table shows, so the choice is ours
# and has to be made on some principle.
#
# It cannot be the day's psalm. `_psalm_for` is keyed on the date, so Vespers
# and this office would draw the identical psalm every single night, and the
# feed would carry it twice in three hours.
#
# So it takes the historic night psalms instead, which is what an office at
# the close of the day is *for*: it is meant to be known by heart and said in
# the dark without a book, and that only works if it does not change. The set
# is appointed in the Rule of St Benedict (c. 530), ch. 18 — "Ad Completorium
# vero quotidie iidem Psalmi repetantur; id est quartus, nonagesimus, et
# centesimus trigesimus tertius", Vulgate numbering, which is KJV 4, 91 and
# 134. Verified against three independent public-domain English editions on
# archive.org (`TheRuleOfStBenedict` 1907, which prints the Latin alongside;
# `TheRuleOfOurMostHolyFather` 1875; `rulestbenedictf00benegoog` 1875, from
# the English edition of 1638), all agreeing word for word.
#
# This is pre-Reformation Western patrimony, not an Anglican borrowing — the
# distinction that retired the old Compline order. The Lutheran confessions
# claim it explicitly: "we keep the ancient rites" (Ap. XV; cf. AC XXIV).
#
# The brief Lesson is 1 Peter 5:8-9, the "be sober, be vigilant" warning that
# is the traditional short chapter of the night office. It is Scripture read
# from the KJV, so no permission question arises about the text itself; only
# the choice is ours, and the rubric leaves the choice open.
NIGHT_PSALMS = "Psalm 4; Psalm 91; Psalm 134"
NIGHT_LESSON = "1 Peter 5:8-9"


def readings_for(date: dt.date, office: str) -> DailyReadings:
    """Readings for a date and office.

    Matins takes the morning reading and Vespers the evening; the Evening
    Suffrages takes neither, being invariable (see NIGHT_PSALMS).
    """
    if office == "evening-suffrages":
        return DailyReadings(psalm=NIGHT_PSALMS, reading=NIGHT_LESSON,
                             source="ordinary", proper=None,
                             title="The Evening Suffrages (invariable)")

    morning = office == "matins"

    # A fixed festival outranks an ordinary Sunday, but yields to the Sundays
    # of Advent, Lent and Eastertide, which keep their own propers.
    proper = proper_for_office(date, office)
    festival = _festival_for(date)
    if festival and (proper is None
                     or not proper.startswith(("advent-", "lent-", "easter-"))):
        proper = festival

    entry = _propers().get(proper or "")
    psalm = _psalm_for(date, proper)

    if entry:
        return DailyReadings(
            psalm=psalm,
            reading=entry["gospel"] if morning else entry["epistle"],
            source="proper",
            proper=proper,
            title=entry.get("title"),
        )

    doy = date.timetuple().tm_yday
    books = GOSPEL_CHAPTERS if morning else EPISTLE_CHAPTERS
    return DailyReadings(psalm=psalm, reading=_nth_chapter(books, doy - 1),
                         source="course")
