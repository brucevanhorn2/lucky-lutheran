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


# --------------------------------------------------------------------------
# Proper-day resolution
#
# The historic one-year lectionary is keyed by *proper*, not by date: the
# Sunday and festival propers in docs/lectionary-migration/temporale.yaml
# carry ids like "advent-1" and "trinity-5", and the daily Table of Lessons
# is keyed by the week those propers name. Both counts flex with Easter — the
# Sundays after Epiphany run 1..6 and those after Trinity 22..27, because the
# Gesima Sundays are reckoned back from Easter while Epiphany is fixed.
# --------------------------------------------------------------------------

# Holy Saturday is deliberately absent: the Common Service Book appoints no
# proper for it (its Propers run Good Friday straight into Easter Day), so
# emitting one would name a proper the lectionary cannot supply.
_HOLY_WEEK_IDS = {
    -6: "holy-monday", -5: "holy-tuesday", -4: "holy-wednesday",
    -3: "maundy-thursday", -2: "good-friday",
}

# Festivals of the temporale that fall on fixed dates rather than Sundays.
_FIXED = {
    (12, 25): "christmas-day",   # two services; see christmas_service()
    (12, 26): "christmas-day-second",
    (1, 1): "new-year",
    (1, 6): "epiphany",
}


def _sundays_between(a: dt.date, b: dt.date) -> int:
    """Number of Sundays strictly after `a` and on or before `b`."""
    if b < a:
        return 0
    first = a + dt.timedelta(days=(7 - a.isoweekday()) % 7 or 7)
    return 0 if first > b else (b - first).days // 7 + 1


def proper_for(date: dt.date) -> str | None:
    """The temporale proper governing `date`, or None if it names no proper.

    Returns the id used in temporale.yaml. Every day gets an answer for the
    *week* it belongs to (see `week_for`); this returns a proper only for the
    days the historic lectionary actually appoints one to — Sundays, the
    festivals of the temporale, and Holy Week.
    """
    year = date.year
    e = easter(year)
    delta = (date - e).days

    # Easter cycle — checked first, since these are movable and outrank the
    # fixed-date reckoning below.
    if delta == 0:
        return "easter-day"
    if delta == 1:
        return "easter-monday"
    if delta in _HOLY_WEEK_IDS:
        return _HOLY_WEEK_IDS[delta]
    if delta == -7:
        return "palm-sunday"
    if delta == 39:
        return "ascension"
    if delta == 49:
        return "pentecost"
    if delta == 50:
        return "pentecost-monday"
    if delta == 56:
        return "trinity-sunday"

    ash = e - dt.timedelta(days=46)
    if date == ash:
        return "ash-wednesday"

    fixed = _FIXED.get((date.month, date.day))
    if fixed:
        return fixed

    if date.weekday() != 6:          # only Sundays name a proper from here on
        return None

    # The Trinity season runs until Advent, so Advent must be known before it
    # can be bounded — otherwise late-November Sundays keep counting upward
    # and yield propers ("trinity-29") the lectionary does not contain.
    adv = advent_start(year if date >= advent_start(year) else year - 1)
    advent_next = advent_start(year)

    # Sundays inside the Easter cycle.
    if 0 < delta < 39:
        return f"easter-{delta // 7}"
    if 39 < delta < 49:
        return "ascension-sunday"    # Exaudi
    if delta > 56 and date < advent_next:
        return f"trinity-{(delta - 56) // 7}"

    # Pre-Lent and Lent, reckoned back from Easter.
    if -63 <= delta <= -50:
        return {-63: "septuagesima", -56: "sexagesima", -49: "quinquagesima"}.get(
            delta, {-63: "septuagesima"}.get(delta))
    if delta == -49:
        return "quinquagesima"
    if -42 <= delta <= -14:
        return f"lent-{(delta + 49) // 7}"

    # Advent and Christmastide.
    if 0 <= (date - adv).days < 28:
        return f"advent-{(date - adv).days // 7 + 1}"

    christmas = dt.date(adv.year, 12, 25)
    if christmas < date <= christmas + dt.timedelta(days=6):
        return "christmas-sunday"
    new_year = dt.date(adv.year + 1, 1, 1)
    if new_year < date < dt.date(adv.year + 1, 1, 6):
        return "new-year-sunday"

    # Sundays after Epiphany, however many the year affords.
    epiph = dt.date(year, 1, 6)
    if date > epiph and delta < -63:
        n = _sundays_between(epiph, date)
        if n >= 1:
            return f"epiphany-{n}"
    return None


def proper_for_office(date: dt.date, office: str) -> str | None:
    """`proper_for`, resolved to a single proper for a given office.

    Christmas Day is the one day the Common Service Book appoints two complete
    sets of propers — "I. For the Early Service" and "II. For the Later
    Service" — which map onto the morning and evening offices exactly.
    """
    p = proper_for(date)
    if p == "christmas-day":
        return "christmas-day-early" if office == "matins" else "christmas-day-later"
    return p


def week_for(date: dt.date) -> tuple[str, str]:
    """(week id, weekday name) — the key into the daily Table of Lessons.

    The table appoints readings by the week a day falls in, named for the
    Sunday that begins it, so a Tuesday in the week after Trinity 5 is
    ("trinity-5", "Tuesday").
    """
    sunday = date - dt.timedelta(days=(date.weekday() + 1) % 7)
    return proper_for(sunday) or "", date.strftime("%A")
