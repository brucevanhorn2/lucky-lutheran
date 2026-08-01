"""Extract the CSB Table of Lessons, cropping the Days column away first.

The dotted leaders in the Days column bleed rightward across the table rule and
corrupt the Morning book names ("eloaike" for Luke) and sometimes its digits.
Cropping at 29% of page width removes them entirely; the day is then recovered
from row order (each week block runs Monday..Saturday) and the week label from
a separate full-page pass.
"""
import json
import os
import re
import subprocess
import sys
import zipfile
from collections import Counter

from PIL import Image

sys.path.insert(0, "/home/daddy/Projects/lucky-lutheran")
from luckylutheran import kjv

ZIP = "/home/daddy/Projects/lucky-lutheran/csb_jp2.zip"
ENT = "commonserviceboo00phil_jp2/commonserviceboo00phil_%04d.jp2"
VALID = {"Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Joshua","Judges",
 "Ruth","Samuel","Kings","Chronicles","Ezra","Nehemiah","Esther","Job","Psalms",
 "Proverbs","Ecclesiastes","Isaiah","Jeremiah","Lamentations","Ezekiel","Daniel",
 "Hosea","Joel","Amos","Obadiah","Jonah","Micah","Nahum","Habakkuk","Zephaniah",
 "Haggai","Zechariah","Malachi","Matthew","Mark","Luke","John","Acts","Romans",
 "Corinthians","Galatians","Ephesians","Philippians","Colossians","Thessalonians",
 "Timothy","Titus","Philemon","Hebrews","James","Peter","Jude","Revelation"}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

CITE = re.compile(r"([1-3]?\s?[A-Za-z][A-Za-z\.]{2,14})\s+(\d{1,3})\s*[:;]\s*"
                  r"(\d{1,3}(?:\s*[-—–]\s*(?:\d{1,3}\s*[:;]\s*)?\d{1,3})?)")
WEEK = re.compile(r"((?:\d{1,2}(?:st|nd|rd|d|th)\s+Sunday[A-Za-z ]{0,24}|Epiphany|"
                  r"Christmas|Advent|Easter\w*|Whitsun\w*|Trinity|Ash Wednesday|"
                  r"Holy Week|Palm Sunday))\.")


def png(z, n):
    dst = f"tbl/n{n}.png"
    if not os.path.exists(dst):
        tmp = f"tbl/{n}.jp2"
        open(tmp, "wb").write(z.open(ENT % n).read())
        Image.open(tmp).save(dst)
        os.remove(tmp)
    return dst


def ocr(path, psm=6, lang="eng"):
    return subprocess.run(["tesseract", path, "-", "-l", lang, "--psm", str(psm)],
                          capture_output=True, text=True).stdout


def clean(b):
    return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9 ]", "", b).strip())


def resolves(ref):
    for cand in (ref, ref.rsplit("-", 1)[0], ref.split(":")[0]):
        try:
            if kjv.passage(cand):
                return True
        except Exception:
            pass
    return False


def main():
    lo, hi = int(sys.argv[1]), int(sys.argv[2])
    z = zipfile.ZipFile(ZIP)
    rows = []
    for n in range(lo, hi + 1):
        p = png(z, n)
        full = ocr(p)
        # NB: OCR renders "TABLE" as "TAPLE"/"TARLE" on some pages; a strict
        # match silently dropped an entire page of the lectionary.
        if not re.search(r"T[A-Z]{1,2}LE\s+OF\s+LESSONS|LESSONS\s+FOR\s+MORNING",
                         full.upper()):
            continue
        weeks = [m.group(1).strip() for m in WEEK.finditer(re.sub(r"\s+", " ", full))]
        im = Image.open(p)
        W, H = im.size
        cp = f"tbl/n{n}_cit.png"
        # auto-tune the crop: the Days column width varies page to page, and a
        # crop that leaves any of it in poisons the Morning book names
        best = None
        for frac in (0.24, 0.26, 0.28, 0.30, 0.32, 0.34, 0.36, 0.38):
            im.crop((int(W * frac), 0, W, H)).save(cp)
            txt = ocr(cp)
            toks = re.findall(r"([A-Za-z][A-Za-z]{2,14})\s+\d{1,3}\s*[:;]\s*\d", txt)
            good = sum(1 for b in toks if b in VALID)
            if best is None or good > best[0]:
                best = (good, frac, txt)
        crop_frac, page_txt = best[1], best[2]
        print("   p%d crop=%.2f  %d/%d book names valid"
              % (n, crop_frac, best[0],
                 len(re.findall(r"[A-Za-z]{3,14}\s+\d{1,3}\s*[:;]\s*\d", page_txt))))

        groups, cur = [], []
        for line in page_txt.splitlines():
            c = CITE.findall(line)
            if len(c) >= 2:
                cur.append((f"{clean(c[0][0])} {c[0][1]}:{c[0][2].replace(' ', '')}",
                            f"{clean(c[1][0])} {c[1][1]}:{c[1][2].replace(' ', '')}"))
            elif cur:
                groups.append(cur)
                cur = []
        if cur:
            groups.append(cur)

        for gi, g in enumerate(groups):
            wk = weeks[gi] if gi < len(weeks) else None
            for di, (mo, ev) in enumerate(g):
                rows.append(dict(page=n, week=wk, group=gi, size=len(g),
                                 day=DAYS[di] if di < 6 else "row%d" % di,
                                 morning=mo, evening=ev))

    print("parsed %d rows from pages %d-%d" % (len(rows), lo, hi))
    print("group sizes:", dict(Counter(r["size"] for r in rows)))
    bad = [r for r in rows if not resolves(r["morning"]) or not resolves(r["evening"])]
    print("unresolvable rows: %d of %d\n" % (len(bad), len(rows)))
    for r in bad[:25]:
        print("   p%s g%s %-24s %-9s %-22s %s"
              % (r["page"], r["group"], str(r["week"])[:24], r["day"],
                 r["morning"], r["evening"]))
    json.dump(rows, open("lessons2.json", "w"), indent=1)
    print("\nwrote lessons2.json")


main()
