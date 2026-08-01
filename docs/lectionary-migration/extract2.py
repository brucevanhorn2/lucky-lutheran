"""Full extraction of the historic one-year pericopes from the Common Service
Book (1917) Propers, with every citation validated against the local KJV.

Handles the OCR damage observed in this scan: 'Johnl'/'Uohn' for 1 John,
'Mark?' for Mark 7, 'Lake' for Luke, 'PhiliPPians', cross-chapter ranges
('1 Corinthians 9:24-10:5'), and Fraktur headings bleeding into the text.
Validation is by incipit: the CSB prints the reading's text after its
citation, so each citation is checked against our own KJV index.
"""
import json
import re
import sys
import unicodedata

sys.path.insert(0, "/home/daddy/Projects/lucky-lutheran")
from luckylutheran import kjv

SRC = "csbA_flat.txt"

# OCR repairs applied to the whole text before parsing.
REPAIRS = [
    (r"\bUohn\s*(\d)", r"1 John \1"),
    (r"\bJohnl\s*:", "John 1:"),
    (r"\bLake\s+(\d)", r"Luke \1"),
    (r"\bMark\?\s*:", "Mark 7:"),
    (r"\bPhiliPPians\s*(\d)", r"Philippians \1"),
    (r"\bGalatians(\d)", r"Galatians \1"),
    (r"\bEphesians(\d)", r"Ephesians \1"),
    (r"\bColossians(\d)", r"Colossians \1"),
    (r"\bRomans(\d)", r"Romans \1"),
    (r"\bMatthew(\d)", r"Matthew \1"),
    (r"\bLuke(\d)", r"Luke \1"),
    (r"\bJohn(\d)", r"John \1"),
    (r"\bTitus(\d)", r"Titus \1"),
    (r"\bHebrews(\d)", r"Hebrews \1"),
]

BOOKS = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Joshua","Judges",
    "Ruth","Samuel","Kings","Chronicles","Ezra","Nehemiah","Esther","Job","Psalms",
    "Psalm","Proverbs","Ecclesiastes","Isaiah","Jeremiah","Lamentations","Ezekiel",
    "Daniel","Hosea","Joel","Amos","Obadiah","Jonah","Micah","Nahum","Habakkuk",
    "Zephaniah","Haggai","Zechariah","Malachi","Matthew","Mark","Luke","John","Acts",
    "Romans","Corinthians","Galatians","Ephesians","Philippians","Colossians",
    "Thessalonians","Timothy","Titus","Philemon","Hebrews","James","Peter","Jude",
    "Revelation"]
BOOK_RE = "|".join(sorted(BOOKS, key=len, reverse=True))

MARKER = re.compile(
    r"\b(EPISTLE|GOSPEL)\.\s*"
    r"((?:[123]\s+)?(?:St\.?\s*)?(?:%s))\s*"
    r"(\d{1,3})\s*[:.]\s*"
    r"(\d{1,3}(?:\s*[-–—]\s*(?:\d{1,3}\s*[:.]\s*)?\d{1,3})?)"
    r"(.{0,140})" % BOOK_RE,
    re.S,
)


def norm(s):
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", s).lower())


def lookup(ref):
    try:
        return kjv.passage(ref)
    except Exception:
        return None


def candidates(book, ch, verses):
    """Reference strings to try, most specific first."""
    v = re.sub(r"\s+", "", verses).replace("–", "-").replace("—", "-")
    out = []
    m = re.match(r"^(\d+)-(\d+):(\d+)$", v)          # 9-10:5  (cross-chapter)
    if m:
        out.append(f"{book} {ch}:{m.group(1)}")
    out += [f"{book} {ch}:{v}", f"{book} {ch}"]
    m2 = re.match(r"^(\d+)", v)
    if m2:
        out.append(f"{book} {ch}:{m2.group(1)}")
    return out


def main():
    t = open(SRC, encoding="utf-8", errors="replace").read()
    for pat, rep in REPAIRS:
        t = re.sub(pat, rep, t)

    rows, seen = [], set()
    for m in MARKER.finditer(t):
        if m.start() in seen:
            continue
        seen.add(m.start())
        kind, book, ch, verses, tail = m.groups()
        book = re.sub(r"^St\.?\s*", "", book.strip(), flags=re.I)
        # incipit: first run of ordinary prose in the tail
        tail = re.sub(r"\b(GRADUAL|HALLELUJAH|INTROIT|COLLECT)\b.*", " ", tail, flags=re.S)
        tail = re.sub(r"or The History of the Passion", " ", tail)
        words = re.findall(r"[A-Za-z][A-Za-z'’-]*", tail)
        incipit = " ".join(words[:12])
        rows.append(dict(pos=m.start(), kind=kind.upper(), book=book, ch=int(ch),
                         verses=verses.strip(), incipit=incipit))

    ok = fixed = unver = 0
    for r in rows:
        want = norm(r["incipit"])[:20]
        hit = None
        for ref in candidates(r["book"], r["ch"], r["verses"]):
            txt = lookup(ref)
            if txt and want and want in norm(txt)[:600]:
                hit = ref
                break
        if hit:
            ok += 1
            r["status"], r["verified_ref"] = "verified", hit
            continue
        # try neighbouring chapters (OCR digit slips)
        for d in list(range(-9, 10)):
            if d == 0:
                continue
            alt = r["ch"] + d
            if alt < 1:
                continue
            for ref in candidates(r["book"], alt, r["verses"]):
                txt = lookup(ref)
                if txt and want and want in norm(txt)[:600]:
                    hit = ref
                    break
            if hit:
                break
        if hit:
            fixed += 1
            r["status"], r["verified_ref"], r["ocr_chapter"] = "corrected", hit, r["ch"]
            r["ch"] = int(re.search(r"\s(\d+):", hit).group(1))
        else:
            unver += 1
            r["status"] = "unverified"
            r["verified_ref"] = f"{r['book']} {r['ch']}:{r['verses']}"

    print(f"parsed {len(rows)}  verified {ok}  corrected {fixed}  unverified {unver}")
    print()
    print("--- corrected (OCR citation errors) ---")
    for r in rows:
        if r["status"] == "corrected":
            print(f"  {r['book']} {r['ocr_chapter']} -> {r['ch']}:{r['verses']}   \"{r['incipit'][:40]}\"")
    print()
    print("--- unverified ---")
    for r in rows:
        if r["status"] == "unverified":
            print(f"  {r['kind']:8s} {r['verified_ref']:28s} \"{r['incipit'][:46]}\"")

    json.dump(rows, open("propers_full.json", "w"), indent=1)
    print(f"\nwrote propers_full.json ({len(rows)})")


main()
