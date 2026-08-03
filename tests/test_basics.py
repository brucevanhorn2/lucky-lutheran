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
    assert evening.reading != a.reading  # morning Gospels, evening Epistles


def test_propers_govern_sundays_and_festivals():
    """Appointed days draw on the historic one-year lectionary; the Gospel is
    read in the morning and the Epistle in the evening."""
    easter = dt.date(2026, 4, 5)
    r = lectionary.readings_for(easter, "matins")
    assert (r.source, r.proper, r.reading) == ("proper", "easter-day", "Mark 16:1-8")
    assert lectionary.readings_for(easter, "vespers").reading == "1 Corinthians 5:6-8"

    # Christmas Day is the one day with two full sets of propers.
    xmas = dt.date(2026, 12, 25)
    assert lectionary.readings_for(xmas, "matins").proper == "christmas-day-early"
    assert lectionary.readings_for(xmas, "vespers").proper == "christmas-day-later"

    # A fixed festival outranks an ordinary day.
    andrew = lectionary.readings_for(dt.date(2026, 11, 30), "matins")
    assert (andrew.proper, andrew.reading) == ("st-andrew", "Matthew 4:18-22")


def test_weekdays_read_in_course():
    r = lectionary.readings_for(dt.date(2026, 7, 15), "matins")
    assert r.source == "course"
    assert r.proper is None
    # Consecutive weekdays advance through the books a chapter at a time.
    nxt = lectionary.readings_for(dt.date(2026, 7, 16), "matins")
    assert nxt.reading != r.reading


def test_every_reading_of_a_year_resolves_in_scripture():
    from luckylutheran import kjv
    unresolved = []
    for i in range(366):
        day = dt.date(2028, 1, 1) + dt.timedelta(days=i)
        if day.year != 2028:
            break
        for office in ("matins", "vespers"):
            r = lectionary.readings_for(day, office)
            for ref in (r.reading, r.psalm):
                if not any(_resolves(kjv, c) for c in
                           (ref, ref.rsplit("-", 1)[0], ref.split(":")[0])):
                    unresolved.append((day, office, ref))
    assert not unresolved, unresolved[:5]


def _resolves(kjv, ref):
    try:
        return bool(kjv.passage(ref))
    except Exception:
        return False


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


def test_catechism_covers_a_month_without_repeating():
    # A 30-day batch must not cycle back to day 1's portion.
    assert len(catechism._portions()) >= 30
    seen = {catechism.portion_for(dt.date(2026, 7, day))["title"]
            for day in range(1, 31)}
    assert len(seen) == 30


def test_assemble_all_offices():
    for office in assemble.OFFICES:
        ep = assemble.build_episode(dt.date(2026, 7, 8), office)
        assert len(ep.segments) > 10
        transcript = ep.transcript()
        assert "Lord's Prayer" in transcript
        speakers = {s.speaker for s in ep.segments}
        assert {"liturgist", "congregation"} <= speakers


def test_kjv_local_index_complete():
    from luckylutheran import kjv
    idx = kjv._index()
    assert sum(len(v) for b in idx.values() for v in b.values()) == 31102
    assert idx["Genesis"][1][1] == \
        "In the beginning God created the heaven and the earth."
    # Regression: the Old/New Testament divider text and a bare "***"
    # section break used to leak into the preceding book's last verse.
    assert idx["Malachi"][4][6] == (
        "And he shall turn the heart of the fathers to the children, and "
        "the heart of the children to their fathers, lest I come and "
        "smite the earth with a curse.")


def test_kjv_passage_ranges():
    from luckylutheran import kjv
    assert kjv.passage("John 3:16") == (
        "For God so loved the world, that he gave his only begotten Son, "
        "that whosoever believeth in him should not perish, but have "
        "everlasting life.")
    assert kjv.passage("Psalm 117") == (
        "O praise the LORD, all ye nations: praise him, all ye people. "
        "For his merciful kindness is great toward us: and the truth of "
        "the LORD endureth for ever. Praise ye the LORD.")
    # Cross-chapter range (the daily lectionary cites these): resolves
    # cleanly, no leaked boilerplate, no truncation.
    cross = kjv.passage("Genesis 16:15-17:22")
    assert cross is not None and len(cross) > 500
    assert "***" not in cross and "Testament" not in cross
    assert kjv.passage("Nonexistent Book 1:1") is None


def test_scripture_uses_local_kjv_offline():
    """get_passage() must resolve KJV text from the local index without
    ever touching the network — batches render ahead on a machine that's
    about to be powered off, so this can't have a live dependency."""
    from luckylutheran import scripture

    def boom(*a, **k):
        raise AssertionError("network fetch used for a local KJV lookup")

    original = scripture._fetch
    scripture._fetch = boom
    try:
        text = scripture.get_passage("John 3:16")
    finally:
        scripture._fetch = original
    assert text == (
        "For God so loved the world, that he gave his only begotten Son, "
        "that whosoever believeth in him should not perish, but have "
        "everlasting life.")


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


def test_phrase_units_bounds_drift():
    from luckylutheran.audio import _phrase_units
    # A short response stays a single unit.
    assert _phrase_units("Amen.") == ["Amen."]
    # A long, comma-heavy creed line splits into several short units...
    creed = ("I believe in God, the Father Almighty, Maker of heaven and "
             "earth; and in Jesus Christ, His only Son, our Lord.")
    units = _phrase_units(creed)
    assert len(units) >= 3
    assert all(len(u) <= 60 for u in units)
    # ...and no words are lost or reordered.
    assert " ".join(units).split() == creed.split()


def test_proper_for_resolves_the_historic_one_year_lectionary():
    """Every date must name a proper the CSB actually supplies, and every
    proper in the table must be reachable — checked across 41 years so both
    the early- and late-Easter extremes are covered."""
    import datetime as dt
    import pathlib
    import yaml
    from luckylutheran import churchyear as cy

    data = pathlib.Path("docs/lectionary-migration/temporale.yaml")
    known = {p["id"] for p in yaml.safe_load(data.read_text())["propers"]}

    seen = set()
    for year in range(2020, 2061):
        day = dt.date(year, 1, 1)
        while day.year == year:
            for office in ("matins", "vespers"):
                p = cy.proper_for_office(day, office)
                if p is not None:
                    assert p in known, f"{day} {office} -> unknown proper {p!r}"
                    seen.add(p)
            day += dt.timedelta(days=1)
    assert seen == known, f"unreachable propers: {sorted(known - seen)}"


def test_proper_for_anchors():
    import datetime as dt
    from luckylutheran import churchyear as cy

    e = cy.easter(2026)
    assert cy.proper_for(e) == "easter-day"
    assert cy.proper_for(e - dt.timedelta(days=7)) == "palm-sunday"
    assert cy.proper_for(e - dt.timedelta(days=46)) == "ash-wednesday"
    assert cy.proper_for(e + dt.timedelta(days=39)) == "ascension"
    assert cy.proper_for(e + dt.timedelta(days=56)) == "trinity-sunday"
    assert cy.proper_for(cy.advent_start(2026)) == "advent-1"
    # The Trinity season must stop at Advent rather than counting past the
    # 27 propers the lectionary contains.
    assert cy.proper_for(cy.advent_start(2026) - dt.timedelta(days=7)).startswith("trinity-")
    # Christmas Day carries two sets of propers, one per office.
    xmas = dt.date(2026, 12, 25)
    assert cy.proper_for_office(xmas, "matins") == "christmas-day-early"
    assert cy.proper_for_office(xmas, "vespers") == "christmas-day-later"
    # Ordinary weekdays name no proper, but do name a week.
    wed = e + dt.timedelta(days=59)
    assert cy.proper_for(wed) is None
    assert cy.week_for(wed) == ("trinity-sunday", "Wednesday")


def test_cli_build_writes_metadata_without_audio(tmp_path):
    """Exercise the CLI's build path end to end.

    Regression guard: lectionary.py's rewrite removed DailyReadings.optional
    while cli.py still read it, so a full render succeeded and then crashed
    writing metadata. No unit test touched cli.py, so nothing caught it.
    """
    import json
    from luckylutheran import cli

    engine = cli._get_engine("null")
    mp3 = cli._build_one(dt.date(2026, 8, 2), "matins", tmp_path, engine)
    assert mp3 is None or mp3.exists()

    meta = json.loads((tmp_path / "2026-08-02-matins.json").read_text())
    assert meta["reading_source"] in ("proper", "course")
    assert meta["psalm"].startswith("Psalm ")
    # A Sunday must be governed by a proper and name it.
    assert meta["proper"] == "trinity-9"
    assert meta["proper_title"]
    assert (tmp_path / "2026-08-02-matins.md").exists()


def test_cli_build_on_a_course_day(tmp_path):
    import json
    from luckylutheran import cli

    cli._build_one(dt.date(2026, 7, 15), "vespers", tmp_path,
                   cli._get_engine("null"))
    meta = json.loads((tmp_path / "2026-07-15-vespers.json").read_text())
    assert meta["reading_source"] == "course"
    assert meta["proper"] is None


def test_id3_tags_describe_the_episode():
    """The MP3 must be self-describing when sideloaded rather than played
    through the feed — a car stereo shows these, not the RSS."""
    from luckylutheran import assemble, audio, feed

    ep = assemble.build_episode(dt.date(2026, 8, 2), "matins")   # Trinity 9, a Sunday
    tags = audio.id3_tags(ep)
    assert tags["title"] == ep.episode_title
    assert tags["album"] == feed.PODCAST["title"]
    assert tags["artist"] == feed.PODCAST["author"]
    assert tags["date"] == "2026-08-02"
    # A proper day names the day it is appointed to.
    assert "Trinity 9" in tags["comment"]
    assert tags["TIT3"] == "Trinity Season"

    # A course day says so instead of naming a proper.
    course = audio.id3_tags(assemble.build_episode(dt.date(2026, 7, 15), "vespers"))
    assert "Read in course" in course["comment"]


def test_selah_becomes_a_pause_not_a_spoken_word():
    """Selah is a performance direction, not text. It should leave a silence
    where it stood rather than be read aloud."""
    from luckylutheran import assemble, speech

    assert speech.split_on_selah("A. Selah. B. Selah. C.") == ["A.", "B.", "C."]
    assert speech.split_on_selah("No rubric here.") == ["No rubric here."]

    # Psalm 32 carries three of them.
    ep = assemble.build_episode(dt.date(2026, 8, 2), "matins")
    assert not any("selah" in s.text.lower() for s in ep.segments)
    psalm = [s for s in ep.segments
             if s.section_id == "psalm" and s.speaker == "lector"]
    assert sum(1 for s in psalm if s.pause_after == speech.SELAH_PAUSE) == 3


def test_pronunciation_respelling_is_spoken_only():
    """Respellings go to the synthesizer; transcripts keep the written word."""
    from luckylutheran import assemble, speech

    assert speech.for_speech("Matins") == "Mattins"      # MAT-ins, not MAY-tins
    assert speech.for_speech("Compline") == "Complin"
    transcript = assemble.build_episode(dt.date(2026, 8, 2), "matins").transcript()
    assert "Mattins" not in transcript


def test_evening_suffrages_is_invariable():
    """The Evening Suffrages does not take the day's propers. The same psalms
    are said every night — that is the office's character, not an oversight.
    Its rubric calls for "a Psalm" without appointing one; we appoint the
    historic night psalms of the Rule of St Benedict, ch. 18."""
    from luckylutheran import lectionary

    a = lectionary.readings_for(dt.date(2026, 1, 1), "evening-suffrages")
    b = lectionary.readings_for(dt.date(2026, 7, 4), "evening-suffrages")
    assert (a.psalm, a.reading) == (b.psalm, b.reading)
    assert a.source == "ordinary"
    assert a.proper is None
    assert "Psalm 4" in a.psalm and "Psalm 91" in a.psalm and "Psalm 134" in a.psalm

    # ...and it must differ from Vespers, which does take the propers. This is
    # the whole reason it cannot simply reuse the day's psalm: `_psalm_for` is
    # keyed on the date, so both offices would draw the same one every night.
    vespers = lectionary.readings_for(dt.date(2026, 1, 1), "vespers")
    assert vespers.reading != a.reading
    assert vespers.psalm != a.psalm


def test_no_office_is_anglican_by_accident():
    """Every built office must have a template that ships with the package.

    The retired Compline order lives in docs/retired/ and must NOT be
    loadable as an office — that borrowing is the thing this replacement
    removed. See docs/replace-compline-with-evening-suffrages.md."""
    from importlib import resources

    from luckylutheran import assemble

    templates = resources.files("luckylutheran") / "templates"
    shipped = {p.name for p in templates.iterdir() if p.name.endswith(".yaml")}
    assert shipped == {f"{o}.yaml" for o in assemble.OFFICES}
    assert "compline" not in assemble.OFFICES

    try:
        assemble.build_episode(dt.date(2026, 8, 2), "compline")
    except ValueError:
        pass
    else:
        raise AssertionError("compline is still buildable")


def test_offices_all_expands_to_every_office():
    """`--offices all` must pick up a newly added office on its own — the
    third office was renamed once already and the batch default did not
    follow it."""
    from luckylutheran import assemble
    from luckylutheran.cli import _parse_offices

    assert _parse_offices("all") == list(assemble.OFFICES)
    assert _parse_offices("matins,vespers") == ["matins", "vespers"]
    # mixable, order-preserving, and duplicates collapse
    assert _parse_offices("vespers,all") == [
        "vespers", *(o for o in assemble.OFFICES if o != "vespers")]
    assert _parse_offices(" matins , matins ") == ["matins"]
    # unknown names and empty specs are rejected, not silently dropped
    assert _parse_offices("matins,compline") is None
    assert _parse_offices(",") is None


def test_crowd_roster_selects_without_deleting(monkeypatch=None):
    """The crowd roster must narrow the mix by *selection*. The WAVs are
    nondeterministic one-off designs and are not in git, so trimming the
    room must never mean deleting a voice."""
    import os
    from luckylutheran import tts

    def with_env(value):
        prev = os.environ.get("LUCKY_CROWD")
        if value is None:
            os.environ.pop("LUCKY_CROWD", None)
        else:
            os.environ["LUCKY_CROWD"] = value
        try:
            return [w.stem for w in tts.crowd_reference_wavs()]
        finally:
            os.environ.pop("LUCKY_CROWD", None)
            if prev is not None:
                os.environ["LUCKY_CROWD"] = prev

    everyone = with_env(None)
    if not everyone:
        return  # no crowd WAVs on this machine; nothing to select from

    three = with_env(",".join(everyone[:3]))
    assert three == everyone[:3]
    assert with_env("none") == []
    assert with_env("  ") == everyone          # blank falls back to the default
    assert with_env("nobody-here") == []       # unknown names select nothing
    # ...and selecting never removes anything from disk.
    assert with_env(None) == everyone


def test_progress_never_writes_escapes_when_redirected():
    """Overnight batches run with stdout redirected to a log. A log full of
    carriage returns and ANSI escapes is worse than plain lines, so the live
    bar must only ever appear on a real terminal."""
    import io
    from luckylutheran import progress

    buf = io.StringIO()                 # StringIO has no isatty() -> not live
    bar = progress.Render("Vespers", total=10, prefix="[3/90] ", stream=buf)
    bar.start()
    for i in range(10):
        bar.step(1, f"segment {i}")
    bar.note("organ bumper")
    bar.finish("out.mp3")

    out = buf.getvalue()
    assert "\r" not in out and "\x1b" not in out
    assert "[3/90] Vespers" in out and "organ bumper" in out
    assert "out.mp3" in out


def test_progress_counts_voice_renders_not_segments():
    """The bar is driven by TTS calls, because a congregation line costs one
    call per voice per phrase unit and a liturgist line costs one. Counting
    segments makes the bar lurch and the ETA meaningless."""
    import datetime as dt
    from luckylutheran import assemble, audio

    ep = assemble.build_episode(dt.date(2026, 8, 2), "vespers")
    solo = audio.count_voice_renders(ep, crowd=[])
    crowded = audio.count_voice_renders(ep, crowd=["a", "b", "c"])
    assert solo >= len(ep.segments)      # long segments split into chunks
    assert crowded > solo * 2            # the crowd dominates the work
