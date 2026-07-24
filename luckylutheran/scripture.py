"""Scripture text provider.

Fetches passages in public-domain translations (KJV by default) from
bible-api.com, with a local file cache so each passage is fetched once ever.
Fully offline-safe: if the network is unavailable and the passage is not
cached, returns None and the assembler inserts a readable placeholder.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from luckylutheran import kjv

DEFAULT_TRANSLATION = "kjv"  # public domain; "web" (World English Bible) also PD
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "scripture"
API = "https://bible-api.com/{ref}?translation={translation}"


def _cache_path(reference: str, translation: str) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", reference.lower()).strip("-")
    return CACHE_DIR / translation / f"{slug}.json"


# Books of a single chapter: the lectionary cites them verse-only
# ("Jude 1-25"), which the API reads as chapters 1-25 unless the chapter
# is spelled out ("Jude 1:1-25").
SINGLE_CHAPTER_BOOKS = {"Obadiah", "Philemon", "2 John", "3 John", "Jude"}


def _expand_reference(reference: str) -> list[str]:
    """Break a lectionary citation into simple references the API accepts.

    The LSB writes compound citations — "Exodus 12:29-32; 13:1-16",
    "Genesis 16:1-9, 15-17:22", "Isaiah 10:12-27a, 33-34" — that
    bible-api.com cannot parse whole. Semicolons separate chapter-level
    items (inheriting the book), commas separate verse-level items
    (inheriting book and chapter), and letter halves ("27a") widen to
    the full verse.
    """
    reference = re.sub(r"(\d)[ab]\b", r"\1", reference)
    refs: list[str] = []
    book, chapter = "", ""
    for part in re.split(r";\s*", reference.strip()):
        m = re.match(r"^((?:[123]\s+)?[A-Za-z][A-Za-z. ]*?)\s+(\d.*)$", part)
        if m:
            book, rest = m.group(1), m.group(2)
        else:
            rest = part  # bare "13:1-16" after a semicolon keeps the book
        for i, item in enumerate(re.split(r",\s*", rest)):
            if i == 0:
                if ":" not in item and book in SINGLE_CHAPTER_BOOKS:
                    item = f"1:{item}"
                ref = f"{book} {item}"
            else:
                ref = f"{book} {chapter}:{item}"
            refs.append(ref)
            chapters = re.findall(r"(\d+):", ref)
            chapter = chapters[-1] if chapters else item
    return refs


def get_passage(reference: str, translation: str = DEFAULT_TRANSLATION) -> str | None:
    """Return passage text for e.g. 'Psalm 95' or 'John 1:1-14', or None.

    Compound lectionary citations are fetched piecewise (_expand_reference)
    and joined; the whole citation is cached under one entry. If any piece
    is unavailable, returns None rather than a silently shortened passage.

    For the default "kjv" translation, resolved first from the local,
    offline King James text (kjv.py) — no network, no cache file needed.
    Falls back to the bible-api.com path below only for whatever the local
    index can't resolve (e.g. a different translation).
    """
    if translation == "kjv":
        local = _local_passage(reference)
        if local is not None:
            return local

    cache = _cache_path(reference, translation)
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))["text"]

    parts = []
    for ref in _expand_reference(reference):
        text = _fetch(ref, translation)
        if text is None:
            return None
        parts.append(text)
    text = " ".join(parts)

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps({"reference": reference, "translation": translation, "text": text},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    return text


def _local_passage(reference: str) -> str | None:
    """Resolve a whole (possibly compound) reference from the local KJV
    index; None if any piece of it isn't found there."""
    parts = []
    for ref in _expand_reference(reference):
        text = kjv.passage(ref)
        if text is None:
            return None
        parts.append(text)
    return " ".join(parts)


def _fetch(reference: str, translation: str) -> str | None:
    """One API call for one simple reference."""
    url = API.format(ref=urllib.parse.quote(reference), translation=translation)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None

    verses = payload.get("verses")
    if verses:
        raw = " ".join(v.get("text", "").strip() for v in verses)
    else:
        raw = payload.get("text", "")
    return _clean(raw) or None


def _clean(text: str) -> str:
    """Normalize whitespace and strip verse-number artifacts for smooth TTS."""
    text = text.replace("¶", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()
