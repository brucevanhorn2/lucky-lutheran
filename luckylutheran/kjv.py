"""Local, offline King James Bible.

Parsed once from a public-domain plain-text transcription
(luckylutheran/data/kjv.txt — Project Gutenberg eBook #10, "The King
James Version of the Bible", https://www.gutenberg.org/ebooks/10,
Gutenberg boilerplate stripped) into an in-memory index, so scripture
lookups don't depend on any network service or a warm cache. Verified
2026-07-23: parses to exactly 31,102 verses, the well-known KJV total,
and spot-checked against bible-api.com for verse-boundary accuracy.

scripture.py tries this first for the default "kjv" translation and
falls back to the network (bible-api.com) only for anything this
module can't resolve.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib import resources

# Each book's full heading as printed in the Gutenberg text, in Bible
# order — both in its table of contents (first occurrence) and again at
# the head of its actual text (last occurrence, which is what we want).
_GUTENBERG_HEADERS = [
    "The First Book of Moses: Called Genesis",
    "The Second Book of Moses: Called Exodus",
    "The Third Book of Moses: Called Leviticus",
    "The Fourth Book of Moses: Called Numbers",
    "The Fifth Book of Moses: Called Deuteronomy",
    "The Book of Joshua",
    "The Book of Judges",
    "The Book of Ruth",
    "The First Book of Samuel",
    "The Second Book of Samuel",
    "The First Book of the Kings",
    "The Second Book of the Kings",
    "The First Book of the Chronicles",
    "The Second Book of the Chronicles",
    "Ezra",
    "The Book of Nehemiah",
    "The Book of Esther",
    "The Book of Job",
    "The Book of Psalms",
    "The Proverbs",
    "Ecclesiastes",
    "The Song of Solomon",
    "The Book of the Prophet Isaiah",
    "The Book of the Prophet Jeremiah",
    "The Lamentations of Jeremiah",
    "The Book of the Prophet Ezekiel",
    "The Book of Daniel",
    "Hosea",
    "Joel",
    "Amos",
    "Obadiah",
    "Jonah",
    "Micah",
    "Nahum",
    "Habakkuk",
    "Zephaniah",
    "Haggai",
    "Zechariah",
    "Malachi",
    "The Gospel According to Saint Matthew",
    "The Gospel According to Saint Mark",
    "The Gospel According to Saint Luke",
    "The Gospel According to Saint John",
    "The Acts of the Apostles",
    "The Epistle of Paul the Apostle to the Romans",
    "The First Epistle of Paul the Apostle to the Corinthians",
    "The Second Epistle of Paul the Apostle to the Corinthians",
    "The Epistle of Paul the Apostle to the Galatians",
    "The Epistle of Paul the Apostle to the Ephesians",
    "The Epistle of Paul the Apostle to the Philippians",
    "The Epistle of Paul the Apostle to the Colossians",
    "The First Epistle of Paul the Apostle to the Thessalonians",
    "The Second Epistle of Paul the Apostle to the Thessalonians",
    "The First Epistle of Paul the Apostle to Timothy",
    "The Second Epistle of Paul the Apostle to Timothy",
    "The Epistle of Paul the Apostle to Titus",
    "The Epistle of Paul the Apostle to Philemon",
    "The Epistle of Paul the Apostle to the Hebrews",
    "The General Epistle of James",
    "The First Epistle General of Peter",
    "The Second General Epistle of Peter",
    "The First Epistle General of John",
    "The Second Epistle General of John",
    "The Third Epistle General of John",
    "The General Epistle of Jude",
    "The Revelation of Saint John the Divine",
]

# Canonical short names, in the same order, matching how references are
# written throughout this project's data files (daily_lectionary.yaml,
# collects.yaml, small_catechism.yaml) and what scripture.py/bible-api.com
# already expect.
CANONICAL_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua",
    "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
    "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job",
    "Psalm", "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah",
    "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel",
    "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah",
    "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians",
    "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians",
    "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy",
    "Titus", "Philemon", "Hebrews", "James", "1 Peter", "2 Peter",
    "1 John", "2 John", "3 John", "Jude", "Revelation",
]

assert len(_GUTENBERG_HEADERS) == len(CANONICAL_BOOKS) == 66

# Testament-divider lines (not book headers) sit between a book's last
# verse and the next book's header — e.g. between Malachi and Matthew.
# Left in place they'd get swept into the preceding book's last verse (no
# new verse token follows them, so the tokenizer would otherwise capture
# them as trailing text). Stripped before indexing.
_TESTAMENT_DIVIDERS = {
    "The Old Testament of the King James Version of the Bible",
    "The New Testament of the King James Bible",
}

_VERSE_TOKEN = re.compile(r"(?:^|(?<=\s))(\d+):(\d+)\s")
_REF = re.compile(
    r"^(?P<book>.+?)\s+(?P<chap>\d+)"
    r"(?::(?P<verse>\d+)(?:-(?:(?P<echap>\d+):)?(?P<everse>\d+))?)?$"
)


_DATA_DIR = "data"
_INDEX_JSON = "kjv_index.json"  # prebuilt from kjv.txt; regenerate with
                                 # `python3 -m luckylutheran.kjv` if kjv.txt
                                 # ever changes (it won't — static PD text).


@lru_cache(maxsize=1)
def _index() -> dict[str, dict[int, dict[int, str]]]:
    """{book: {chapter: {verse: text}}}, loaded once per process.

    The KJV text is static, so the expensive regex parse of kjv.txt
    (_parse_from_source) happens exactly once, ever, at build time — see
    `python3 -m luckylutheran.kjv`. Normal runs just load the resulting
    JSON, which is materially faster and needs no regex/tokenizing at
    all. Falls back to parsing from source if the JSON is ever missing.
    """
    json_path = resources.files("luckylutheran") / _DATA_DIR / _INDEX_JSON
    if json_path.is_file():
        raw = json.loads(json_path.read_text(encoding="utf-8"))
        return {book: {int(c): {int(v): t for v, t in verses.items()}
                        for c, verses in chapters.items()}
                for book, chapters in raw.items()}
    return _parse_from_source()


def _parse_from_source() -> dict[str, dict[int, dict[int, str]]]:
    """Parse data/kjv.txt into {book: {chapter: {verse: text}}}. Only run
    at build time (see __main__ below) — normal runs load the prebuilt
    JSON via _index() instead."""
    raw = (resources.files("luckylutheran") / "data" / "kjv.txt").read_text(
        encoding="utf-8")
    lines = [l for l in raw.split("\n") if l.strip() not in _TESTAMENT_DIVIDERS
             and not re.fullmatch(r"\*+", l.strip())]

    # Each heading appears twice: once in the table of contents, once at
    # the actual head of the book's text. The last occurrence is real.
    last_seen: dict[str, int] = {}
    for i, line in enumerate(lines):
        s = line.strip()
        if s in _GUTENBERG_HEADERS:
            last_seen[s] = i
    starts = [last_seen[h] for h in _GUTENBERG_HEADERS]

    index: dict[str, dict[int, dict[int, str]]] = {}
    for bi, canon in enumerate(CANONICAL_BOOKS):
        start = starts[bi] + 1
        end = starts[bi + 1] if bi + 1 < len(starts) else len(lines)
        body = "\n".join(lines[start:end])
        tokens = list(_VERSE_TOKEN.finditer(body))
        book: dict[int, dict[int, str]] = {}
        for k, m in enumerate(tokens):
            chap, vs = int(m.group(1)), int(m.group(2))
            text_start = m.end()
            text_end = tokens[k + 1].start() if k + 1 < len(tokens) else len(body)
            book.setdefault(chap, {})[vs] = " ".join(
                body[text_start:text_end].split())
        index[canon] = book
    return index


def passage(simple_ref: str) -> str | None:
    """Resolve one simple reference ('Genesis 1:1-19', 'Psalm 95',
    'John 3:16', or a cross-chapter 'Genesis 16:15-17:22') to KJV text,
    or None if the book/verse isn't found in the local index."""
    m = _REF.match(simple_ref.strip())
    if not m:
        return None
    idx = _index()
    book = m.group("book")
    if book not in idx:
        return None
    chapters = idx[book]
    chap = int(m.group("chap"))

    if m.group("verse") is None:
        verses = chapters.get(chap)
        if not verses:
            return None
        return " ".join(verses[v] for v in sorted(verses))

    start_v = int(m.group("verse"))
    end_chap = int(m.group("echap")) if m.group("echap") else chap
    end_v = int(m.group("everse")) if m.group("everse") else start_v

    out: list[str] = []
    c = chap
    while c <= end_chap:
        verses = chapters.get(c)
        if not verses:
            return None
        lo = start_v if c == chap else 1
        hi = end_v if c == end_chap else max(verses)
        for v in range(lo, hi + 1):
            if v not in verses:
                return None
            out.append(verses[v])
        c += 1
    return " ".join(out)


if __name__ == "__main__":
    # One-time build step (rerun only if data/kjv.txt itself ever changes):
    #   python3 -m luckylutheran.kjv
    from pathlib import Path

    parsed = _parse_from_source()
    out_path = Path(__file__).resolve().parent / _DATA_DIR / _INDEX_JSON
    out_path.write_text(json.dumps(parsed, ensure_ascii=False), encoding="utf-8")
    verse_count = sum(len(v) for b in parsed.values() for v in b.values())
    print(f"wrote {out_path} ({len(parsed)} books, {verse_count} verses)")
