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


def test_official_lectionary_movable():
    ash_wednesday = dt.date(2026, 2, 18)
    r = lectionary.readings_for(ash_wednesday, "matins")
    assert (r.reading, r.source) == ("Genesis 1:1-19", "official")
    assert r.psalm == "Psalm 5"  # Lent table, Wednesday morning
    ev = lectionary.readings_for(ash_wednesday, "vespers")
    assert ev.reading == "Mark 1:1-13"
    assert ev.psalm == "Psalm 27; Psalm 51"

    easter_sunday = dt.date(2026, 4, 5)  # ash+46
    r = lectionary.readings_for(easter_sunday, "matins")
    assert r.reading == "Exodus 14:10-31"
    assert r.psalm == "Psalm 93"  # Easter table, Sunday morning


def test_official_lectionary_civil():
    r = lectionary.readings_for(dt.date(2026, 12, 25), "matins")
    assert (r.reading, r.source) == ("Isaiah 49:1-18", "official")
    assert r.psalm == "Psalm 2"  # Christmastide is date-keyed
    # The day before Ash Wednesday still resolves via the civil table.
    r = lectionary.readings_for(dt.date(2026, 2, 17), "matins")
    assert (r.reading, r.source) == ("Job 13:1-12", "official")


def test_summer_gap_falls_back():
    r = lectionary.readings_for(dt.date(2026, 7, 11), "matins")
    assert r.source == "fallback"
    assert r.psalm.startswith("Psalm ")  # psalms are official year-round


def test_expand_reference():
    from luckylutheran.scripture import _expand_reference
    assert _expand_reference("Genesis 16:1-9, 15-17:22") == [
        "Genesis 16:1-9", "Genesis 16:15-17:22"]
    assert _expand_reference("Exodus 12:29-32; 13:1-16") == [
        "Exodus 12:29-32", "Exodus 13:1-16"]
    assert _expand_reference("Isaiah 10:12-27a, 33-34") == [
        "Isaiah 10:12-27", "Isaiah 10:33-34"]
    assert _expand_reference("Isaiah 44:21-45:13, 20-25") == [
        "Isaiah 44:21-45:13", "Isaiah 45:20-25"]
    assert _expand_reference("Lamentations 5:1-22; Psalm 22") == [
        "Lamentations 5:1-22", "Psalm 22"]
    assert _expand_reference("Jude 1-25") == ["Jude 1:1-25"]
    assert _expand_reference("John 3:16") == ["John 3:16"]


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


def test_midi_note_numbers():
    from luckylutheran.music import _midi_note
    assert _midi_note("A4") == 69   # concert A
    assert _midi_note("C4") == 60   # middle C
    assert _midi_note("G4") == 67
    assert _midi_note("F#4") == 66
    assert _midi_note("Bb3") == 58


def test_write_midi_bytes(tmp_path=None):
    import tempfile
    from pathlib import Path
    from luckylutheran.music import _write_midi
    tune = {"tempo_qpm": 120, "notes": [["C4", 1], ["E4", 1], ["G4", 2]]}
    out = Path(tempfile.mkdtemp()) / "t.mid"
    _write_midi(tune, out)
    data = out.read_bytes()
    assert data[:4] == b"MThd"                      # header chunk
    assert data[8:10] == b"\x00\x00"                # format 0
    assert data[10:12] == b"\x00\x01"               # one track
    assert b"MTrk" in data                          # track chunk present
    assert bytes([0xC0, 0x13]) in data              # program change: church organ
    assert data.endswith(bytes([0xFF, 0x2F, 0x00])) # end-of-track meta


def test_render_tune_offline_and_midi_generation():
    from luckylutheran import music
    # No fluidsynth on the dev box -> additive fallback still yields a WAV.
    out = music.render_tune("old-hundredth", force=True)
    assert out.exists() and out.suffix == ".wav"
    # MIDI generation from the YAML works with no fluidsynth present.
    midi = music._tune_midi("old-hundredth")
    assert midi.suffix == ".mid"
    assert midi.read_bytes()[:4] == b"MThd"
    # Soundfont discovery honors the env override and missing files.
    import os
    os.environ["LUCKY_SOUNDFONT"] = "/nonexistent/x.sf2"
    assert music._soundfont() is None
    os.environ.pop("LUCKY_SOUNDFONT")
