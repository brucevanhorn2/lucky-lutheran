"""Sanity tests: computus, seasons, lectionary determinism, and full script
assembly for every office (offline-safe)."""

import datetime as dt

from luckylutheran import assemble, catechism, lectionary
from luckylutheran.churchyear import church_day, easter


def test_easter_known_dates():
    assert easter(2024) == dt.date(2024, 3, 31)
    assert easter(2025) == dt.date(2025, 4, 20)
    assert easter(2026) == dt.date(2026, 4, 5)
    assert easter(2027) == dt.date(2027, 3, 28)


def test_seasons():
    assert church_day(dt.date(2026, 7, 8)).season == "trinity"
    assert church_day(dt.date(2026, 12, 25)).season == "christmas"
    assert church_day(dt.date(2026, 11, 29)).season == "advent"  # Advent 1
    assert church_day(dt.date(2026, 2, 18)).season == "lent"  # Ash Wednesday
    assert church_day(dt.date(2026, 4, 5)).season == "easter"
    assert church_day(dt.date(2026, 1, 20)).season == "epiphany"


def test_lectionary_deterministic():
    d = dt.date(2026, 7, 8)
    a = lectionary.readings_for(d, "matins")
    b = lectionary.readings_for(d, "matins")
    assert a == b
    evening = lectionary.readings_for(d, "vespers")
    assert evening.psalm != a.psalm  # morning/evening get different psalms


def test_catechism_rotates():
    seen = {catechism.portion_for(dt.date(2026, 7, day))["title"]
            for day in range(1, 9)}
    assert len(seen) == 8


def test_assemble_all_offices():
    for office in assemble.OFFICES:
        ep = assemble.build_episode(dt.date(2026, 7, 8), office)
        assert len(ep.segments) > 10
        transcript = ep.transcript()
        assert "Lord's Prayer" in transcript
        speakers = {s.speaker for s in ep.segments}
        assert {"liturgist", "congregation"} <= speakers
