"""Assemble a complete episode script for a given date and office.

Loads the office template, resolves the church calendar, fills the dynamic
slots (psalm, reading, hymn, catechism, collect of the day), and returns an
Episode: an ordered list of Segments, each tagged with a speaker so the TTS
layer can render distinct voices.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from importlib import resources

import yaml

from luckylutheran import catechism, collects, lectionary, scripture, speech
from luckylutheran.churchyear import ChurchDay, church_day

OFFICES = ("matins", "vespers", "evening-suffrages")

# Default pause between lines within a section, seconds. Versicle and
# response need room to breathe or the office sounds hard-edited.
LINE_PAUSE = 1.0


@dataclass
class Segment:
    section_id: str
    section_title: str
    speaker: str  # liturgist | congregation | lector | all
    text: str
    pause_after: float = LINE_PAUSE


@dataclass
class Episode:
    office: str
    title: str
    date: dt.date
    day: ChurchDay
    readings: lectionary.DailyReadings
    segments: list[Segment] = field(default_factory=list)

    @property
    def episode_title(self) -> str:
        return f"{self.title} for {self.date.strftime('%A, %B %-d, %Y')}"

    @property
    def slug(self) -> str:
        return f"{self.date.isoformat()}-{self.office}"

    def transcript(self) -> str:
        """Human-readable transcript (also the podcast show notes)."""
        # "proper" days name the appointed day; "course" days are read in
        # course through the books and have no proper to name. "ordinary" is
        # the invariable office, which is neither — it says the same thing
        # every night on purpose.
        if self.readings.source == "proper":
            appointed = self.readings.title or self.readings.proper
            provenance = f"Appointed for {appointed}"
        elif self.readings.source == "ordinary":
            provenance = "Said every night"
        else:
            provenance = "Read in course"
        lines = [f"# {self.episode_title}", "",
                 f"*Season: {self.day.season_name}. "
                 f"Psalm: {self.readings.psalm}. "
                 f"Reading: {self.readings.reading}"
                 f" ({provenance}).*", ""]
        current = None
        for seg in self.segments:
            if seg.section_title != current:
                current = seg.section_title
                lines += [f"## {current}", ""]
            label = {"liturgist": "L", "congregation": "C",
                     "lector": "Lector", "all": "All"}[seg.speaker]
            lines += [f"**{label}:** {seg.text}", ""]
        return "\n".join(lines)


def _load_template(office: str) -> dict:
    ref = resources.files("luckylutheran") / "templates" / f"{office}.yaml"
    return yaml.safe_load(ref.read_text(encoding="utf-8"))


def _spoken_date(date: dt.date) -> str:
    return date.strftime("%A, %B %-d")


def _greeting(office: str) -> str:
    return ("Good evening." if office in ("vespers", "evening-suffrages")
            else "Good morning.")


def _passage_segments(section: dict, reference: str, kind: str) -> list[Segment]:
    """Render a scripture passage (psalm or lesson) as lector segments.

    The LSB psalm table appoints two psalms most evenings ("Psalm 42;
    Psalm 32"): each is read as its own segment, with one Gloria Patri
    closing the set."""
    sid, title = section["id"], section["title"]
    if kind == "psalm":
        refs = [r.strip() for r in reference.split(";")]
        # "A and B" for two, "A, B, and C" for three — the night office says
        # three psalms every time, and "A and B and C" reads as a stammer.
        names = (" and ".join(refs) if len(refs) < 3
                 else f"{', '.join(refs[:-1])}, and {refs[-1]}")
        plural = "psalms appointed for this day are" if len(refs) > 1 \
            else "psalm appointed for this day is"
        intro, outro = f"The {plural} {names}.", None
    else:
        refs = [reference]
        intro, outro = f"The reading is from {reference}.", "Here ends the reading."

    segs = [Segment(sid, title, "lector", intro, 1.0)]
    any_text = False
    for ref in refs:
        text = scripture.get_passage(ref)
        if text is None:
            segs.append(Segment(
                sid, title, "lector",
                f"[Text of {ref} unavailable — will be fetched at build "
                f"time from the KJV.]", 1.0))
        else:
            # "Selah" is a performance direction, not text to be read. Split
            # the passage where it stood so a real silence falls there
            # instead — doing what the rubric says rather than saying it.
            chunks = speech.split_on_selah(text)
            for i, chunk in enumerate(chunks):
                last = i == len(chunks) - 1
                segs.append(Segment(sid, title, "lector", chunk,
                                    1.5 if last else speech.SELAH_PAUSE))
            any_text = True
    if kind == "psalm" and any_text:
        segs.append(Segment(
            sid, title, "all",
            "Glory be to the Father and to the Son and to the Holy "
            "Ghost; as it was in the beginning, is now, and ever shall "
            "be, world without end. Amen.", 1.0))
    if outro:
        segs.append(Segment(sid, title, "lector", outro, 1.0))
    return segs


def _fill_slot(section: dict, episode: Episode) -> list[Segment]:
    slot = section["slot"]
    sid, title = section["id"], section["title"]

    if slot == "psalm":
        return _passage_segments(section, episode.readings.psalm, "psalm")

    if slot == "reading":
        return _passage_segments(section, episode.readings.reading, "reading")

    if slot == "collect_of_day":
        c = collects.collect_of_the_day(episode.day)
        return [
            Segment(sid, title, "liturgist", c["text"], 0.4),
            Segment(sid, title, "congregation", "Amen.", 1.0),
        ]

    if slot == "catechism":
        p = catechism.portion_for(episode.date)
        segs = [Segment(sid, title, "liturgist",
                        f"From Luther's Small Catechism: {p['title']}.", 1.0)]
        if p["citation"]:
            segs.append(Segment(sid, title, "liturgist", p["citation"], 0.6))
        segs.append(Segment(sid, title, "liturgist", p["text"], 1.0))
        if p["meaning"]:
            segs.append(Segment(sid, title, "liturgist", p["meaning"], 1.0))
        return segs

    if slot == "hymn":
        # v1: no singing. Music beds / organ hymns are wired in audio.py
        # later; for now the hymn slot is silently omitted from the script.
        return []

    raise ValueError(f"Unknown slot type: {slot!r}")


def build_episode(date: dt.date, office: str) -> Episode:
    if office not in OFFICES:
        raise ValueError(f"office must be one of {OFFICES}, got {office!r}")

    template = _load_template(office)
    day = church_day(date)
    readings = lectionary.readings_for(date, office)
    episode = Episode(office=office, title=template["title"], date=date,
                      day=day, readings=readings)

    season_phrase = ("in the Trinity season" if day.season == "trinity"
                     else f"in the season of {day.season_name}")
    variables = {
        "greeting": _greeting(office),
        "date_spoken": _spoken_date(date),
        "season_name": day.season_name,
        "season_phrase": season_phrase,
    }

    for section in template["sections"]:
        if "slot" in section:
            segs = _fill_slot(section, episode)
        else:
            segs = [
                Segment(section["id"], section["title"], line["speaker"],
                        " ".join(line["text"].split()).format(**variables))
                for line in section["lines"]
            ]
        if segs:
            segs[-1].pause_after = float(section.get("pause_after", 1.0))
            episode.segments.extend(segs)

    return episode
