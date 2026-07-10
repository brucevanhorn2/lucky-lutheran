"""Church year calculations for the historic (one-year) Western calendar.

Computes the date of Easter (Gregorian computus) and derives the liturgical
season for any civil date, following the historic Lutheran calendar as used
in The Lutheran Hymnal (1941): Advent, Christmas, Epiphany, Pre-Lent
(Gesima Sundays), Lent, Holy Week, Easter, Ascension, Pentecost/Whitsun,
and the Trinity season.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

# Season identifiers (keys into collects.yaml and template overrides)
ADVENT = "advent"
CHRISTMAS = "christmas"
EPIPHANY = "epiphany"
PRE_LENT = "pre_lent"
LENT = "lent"
HOLY_WEEK = "holy_week"
EASTER = "easter"
ASCENSION = "ascension"
PENTECOST = "pentecost"
TRINITY = "trinity"


def easter(year: int) -> dt.date:
    """Date of Easter Sunday (Gregorian calendar, Anonymous/Meeus algorithm)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return dt.date(year, month, day + 1)


def advent_start(year: int) -> dt.date:
    """First Sunday of Advent: the fourth Sunday before Christmas Day."""
    christmas_day = dt.date(year, 12, 25)
    # Sunday strictly before Christmas (if Christmas is a Sunday, use Dec 24's week)
    days_back = christmas_day.isoweekday() % 7  # Sunday -> 0
    if days_back == 0:
        days_back = 7
    fourth_sunday_before = christmas_day - dt.timedelta(days=days_back + 21)
    return fourth_sunday_before


@dataclass(frozen=True)
class ChurchDay:
    date: dt.date
    season: str
    easter: dt.date
    # Days since the most recent First Sunday in Advent (start of church year)
    day_of_church_year: int

    @property
    def season_name(self) -> str:
        return {
            ADVENT: "Advent",
            CHRISTMAS: "Christmastide",
            EPIPHANY: "Epiphany",
            PRE_LENT: "Pre-Lent",
            LENT: "Lent",
            HOLY_WEEK: "Holy Week",
            EASTER: "Eastertide",
            ASCENSION: "Ascensiontide",
            PENTECOST: "Whitsuntide",
            TRINITY: "Trinity Season",
        }[self.season]


def church_day(date: dt.date) -> ChurchDay:
    """Classify a civil date into its liturgical season."""
    year = date.year
    e = easter(year)

    # Fixed-date seasons first.
    if dt.date(year, 12, 25) <= date <= dt.date(year, 12, 31):
        season = CHRISTMAS
    elif date >= advent_start(year):
        season = ADVENT
    elif date <= dt.date(year, 1, 5):
        season = CHRISTMAS
    else:
        septuagesima = e - dt.timedelta(days=63)
        ash_wednesday = e - dt.timedelta(days=46)
        palm_sunday = e - dt.timedelta(days=7)
        ascension_day = e + dt.timedelta(days=39)
        pentecost_day = e + dt.timedelta(days=49)
        trinity_sunday = e + dt.timedelta(days=56)

        if date < septuagesima:
            season = EPIPHANY
        elif date < ash_wednesday:
            season = PRE_LENT
        elif date < palm_sunday:
            season = LENT
        elif date < e:
            season = HOLY_WEEK
        elif date < ascension_day:
            season = EASTER
        elif date < pentecost_day:
            season = ASCENSION
        elif date < trinity_sunday:
            season = PENTECOST
        else:
            season = TRINITY

    start = advent_start(year if date >= advent_start(year) else year - 1)
    return ChurchDay(
        date=date,
        season=season,
        easter=e,
        day_of_church_year=(date - start).days + 1,
    )
