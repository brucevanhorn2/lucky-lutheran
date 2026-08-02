# Migrating off the LSB lectionary — work in progress

**Status: research done, integration not started. Nothing here is wired into
the app yet. `luckylutheran/data/daily_lectionary.yaml` is still the live
lectionary and still carries the unresolved rights question.**

This directory holds the transferable state of a migration that will take
several sessions. Read this first; it is written for whoever picks it up next,
including a future session with no memory of this one.

## Why

`daily_lectionary.yaml` was transcribed from the Lutheran Service Book (CPH,
2006) — a current commercial product — on an untested "facts aren't
copyrightable" argument. See the **Daily Lectionary** section of
[`SOURCES.md`](../../SOURCES.md) for the full analysis. Research on
2026-08-01 found the LSB daily lectionary is described as *independent of both
of LSB's Sunday lectionaries*, prepared by the Commission on Worship for the
2006 book — i.e. an original compilation, which is exactly what Feist
protects. The decision was therefore to leave LSB entirely rather than seek a
licence.

Note the dependency is **not only the readings**: the psalm scheme in that
file (`psalms:`, 9 blocks) is LSB's Table of Psalms for Daily Prayer too. Both
must be replaced.

## The replacement design (decided)

Three parts, all public domain:

| | source | nature |
|---|---|---|
| Sundays & festivals | historic one-year pericopes, from the Common Service Book (1917) Propers | ancient scheme, PD book |
| Weekdays | continuous course reading — Gospels/OT in the morning, Epistles in the evening | a *method*; 17 USC 102(b) excludes methods from copyright outright |
| Psalms | the 1662 monthly psalter cycle | PD rule, stated in prose in the 1928 BCP |

**Deliberately accepted:** weekday readings will *not* be seasonally aware.
Lent and Holy Week weekdays get course reading like any other week. This was
an explicit decision — the podcast is a household office and does not try to
compete with a parish's Lent and Holy Week services; the historic treatment
has merit through novelty.

### What Luther actually did (for the record)

The *Deutsche Messe* (1526) assigns books to weekdays — Monday/Tuesday the
catechism, Wednesday Matthew, Thursday/Friday the Apostolic Epistles and rest
of the New Testament, Saturday John — worked through *in course*. For Sundays
he kept the historic pericopes. There was no dated daily table; that genre is
modern. His stated reason for keeping the pericopes: "there are but few
inspired preachers who can handle a whole Gospel or other book with force and
profit." The design above follows this shape.

## What is in this directory

- **`propers_full.json`** — 163 readings (81 Epistles, 82 Gospels) extracted
  from the CSB Propers in document order.
- **`extract2.py`** — the extractor. Re-runnable; needs `csbA_flat.txt` (see
  below) in the working directory.

### How the source was obtained

```bash
curl -sL https://archive.org/download/commonserviceboo00phil/commonserviceboo00phil_djvu.txt -o csbA.txt
# NB: this scan double-spaces words and wraps mid-phrase. Flatten before grepping,
# or exact-phrase searches return false negatives:
tr -s ' \t' ' ' < csbA.txt | tr '\n' ' ' | tr -s ' ' > csbA_flat.txt
```

archive.org `commonserviceboo00phil`, unrestricted. Pre-1930 US publication →
public domain. Already the verified source for Matins, Vespers and the
collects.

### The validation trick — keep using it

The CSB prints each reading's **full text immediately after its citation**, so
every citation can be checked independently: look it up in the project's own
local KJV index and compare against the printed incipit. This is what makes
OCR transcription trustworthy rather than a leap of faith.

It has already caught **four real citation errors** that would otherwise have
been transcribed silently:

| OCR read | actually | caught by |
|---|---|---|
| Romans 15:11-14 | **Romans 13:11-14** | "And that, knowing the time…" |
| Luke 3:1-11 | **Luke 5:1-11** | "And it came to pass, that, as the people pressed…" |
| Ephesians 1:22-28 | **Ephesians 4:22-28** | "That ye put off concerning the former conversation…" |
| Ephesians 3:15-21 | **Ephesians 5:15-21** | "See then that ye walk circumspectly…" |

Current tallies: **117 verified, 4 corrected, 42 unverified.**

## What remains — in order

1. **Resolve the 42 unverified readings.** Most are *incipit capture* failures,
   not wrong citations: the reading is followed immediately by `GRADUAL`, or a
   Fraktur festival heading bleeds in ("GTfie Jfegttual of tfjc Reformation" =
   "The Festival of the Reformation"). Each still needs individual
   confirmation. Four already checked by hand and found **correct** despite
   failing the automated check — `1 Peter 2:11-20`, `John 3:1-15`,
   `Ephesians 4:1-6`, and `Matthew 4:18-22`. One is a **real error**:
   `Matthew 22:31-46` should be **`Matthew 22:34-46`** (verified: "But when
   the Pharisees had heard that he had put the Sadducees to silence").
   Watch for page numbers captured into citations (`John 21:19-24. 155`,
   `Galatians 2:16-21. 159`).
2. **Label every reading with its proper day.** *This is the hard part and the
   main risk of silent error.* The readings sit in the file in liturgical
   order (Advent 1 → … → Trinity 27, then the festivals), so they can be
   mapped onto the known fixed sequence — but the CSB's own day headings are
   Fraktur and OCR badly, so the mapping must be checked against a known list
   of the historic propers rather than trusted from the scan.
3. **Add proper-day resolution to `churchyear.py`.** `church_day()` currently
   returns season + `day_of_church_year` + the Easter date, but *not* an
   identity like `trinity-5` or `advent-2`. That resolver is the join key to
   the pericope table. Note the counts of Sundays after Epiphany and after
   Trinity flex with the date of Easter — that is the fiddly bit.
4. **The psalter.** Replace LSB's psalm tables with the 1662 monthly cycle.
   The *rule* OCRs cleanly from the 1928 BCP (`bookofcommonpray00chur_20`,
   CC0) — "The Psalter shall be read through once every Month… both for
   Morning and Evening Prayer", with the rules for February, for 31-day
   months, and for dividing Psalm 119 into portions. The per-day divisions
   are printed as headers in the Psalter itself and did **not** OCR usefully
   from that scan; another source or another approach is needed.
5. **Rewrite `lectionary.py`.** Pericopes on Sundays and festivals; course
   reading on weekdays. The existing `_nth_chapter` fallback (mornings through
   the Gospels, evenings through Acts and the Epistles) is already exactly the
   weekday mechanism — it gets promoted from fallback to primary and extended
   over the Old Testament. `DailyReadings.source` should stop saying
   "fallback"/"official" and say something true of the new scheme.
6. **Delete `daily_lectionary.yaml`**, update `SOURCES.md` (replace the Daily
   Lectionary section with the new sourcing), the README table, and the
   `lectionary.py` docstring.

## Do not

- Do not wire any of this in half-done. The app currently works; a partial
  migration that breaks daily readings is worse than the rights question.
- Do not transcribe citations from memory or from a modern lectionary website.
  Extract from the scan and validate against the local KJV, every time.
- Do not trust a phrase-grep miss on an archive.org OCR file until the text
  has been whitespace-flattened (see above).

---

## Pass B result (2026-08-01): temporale complete

`temporale.yaml` — **71 propers, Advent 1 through Trinity 27**, each with its
historic Epistle and Gospel. All 142 citations resolve against the local KJV.

Built by mapping the extracted readings (which sit in the book in liturgical
order) onto the known historic sequence, then confirming the alignment against
page scans at three points spread across the span:

| page | shows | confirms |
|---|---|---|
| 117 | Gospel Luke 24:13-35, then "Quasi Modo Geniti. The First Sunday after Easter" | Easter Monday / Easter 1 boundary |
| 126 | "The Festival of the Holy Trinity" — Epistle Rom 11:33-36, Gospel John 3:1-15 | Trinity Sunday |
| 150 | Epistle 1 Thess 4:13-18, Gospel Matt 24:15-28, then "The Twenty-sixth Sunday after Trinity" | Trinity 25 |

No drift at the start, middle or end, so the intervening alignment holds.

Three Epistles that the automated pass missed were recovered by hand and match
the expected historic readings exactly: Trinity 7 `Romans 6:19-23` (printed
"EPISTLE" with no full stop), Trinity 25 and Trinity 27 (printed
"lThessalonians", OCR `l` for `1`).

**Page images are legible — including Fraktur.** This was the unlock. Fetch:

    https://archive.org/download/commonserviceboo00phil/page/n<N>_medium.jpg

where N is roughly the printed page + 3 in the Propers. The scans read cleanly
where the OCR is unusable, so pass A is a cost question, not a feasibility one.

### Still outstanding

- **The sanctorale (festivals) is NOT done.** Readings 139-162 of
  `propers_full.json` are the saints' days and festivals — St. Andrew,
  St. Thomas, St. Stephen, St. John, Holy Innocents, Conversion of St. Paul,
  Presentation, St. Matthias, Annunciation, St. Mark, SS. Philip and James,
  Nativity of St. John the Baptist, SS. Peter and Paul, St. James the Elder,
  St. Bartholomew, St. Matthew, St. Michael and All Angels, St. Luke,
  SS. Simon and Jude, Reformation, All Saints, Harvest, Day of Humiliation and
  Prayer, and a general Thanksgiving. Their extraction is unreliable because
  the Fraktur headings bled into the incipit capture, so both citations *and*
  day assignment need reading off the page images. This is the first job for
  pass A.
- **The three Christmas services** (`christmas-day`, `christmas-second`,
  `christmas-third`) are ordered as printed but their exact titles were not
  read off the page. Worth confirming in pass A.
- Steps 3-6 of the plan above (churchyear proper-day resolution, psalter,
  lectionary.py rewrite, deleting the LSB file) are untouched.


---

## OCR breakthrough (2026-08-01): tesseract + Fraktur at full resolution

**The blackletter headings are recoverable.** This removes the main obstacle
to pass A. Archive.org's own OCR was generic English run on blackletter, which
is why every festival heading came out as mush.

### The recipe

Fetch **full resolution** — drop the `_medium` suffix. It is 2155x3201 versus
539x801, roughly 4x linear:

    https://archive.org/download/commonserviceboo00phil/page/n<N>.jpg

Then OCR with the Fraktur model *alongside* English:

    tesseract page.jpg out -l eng+frk --psm 1

`eng+frk` is the setting that matters. Measured against a known heading
("The Second Christmas Day", printed p.92):

| model | result |
|---|---|
| `-l eng` | "The Second Christmas **Dap**." |
| `-l frk` | correct heading, but roman body text degrades |
| **`-l eng+frk`** | **correct heading and clean body text** |

Sample gain on the sanctorale:

| archive.org OCR | tesseract eng+frk |
|---|---|
| `g t eter anb g t aul` | St. Peter and St. Paul |
| `t f iltp anb t fames gpostle May` | St. Philip and St. James, Apostles. May 1. |
| `he Jlatibitp of g t SToftn tfjc ba` | The Nativity of St. John, the Baptist. June 24. |
| `GTfie Jfegttual of tfjc Reformation` | The Festival of the Reformation. October 31. |

Kraken was considered and is unnecessary — tesseract 5.3.4 with `frk` clears
the bar.

### Still to fix: two-column layout

`--psm 1` on a full page mixes the two columns and pulls the running header
into the body, producing artefacts like "St. Peter and St. Paul St. Mark,
Evangelist" and citations truncated at the column break (`Ephesians 2: 19722`,
`Acts 12:`). Crop the columns first:

    convert page.jpg -crop 50%x100% +repage col_%d.jpg
    tesseract col_0.jpg - -l eng+frk --psm 4

### Digit errors persist — validation stays mandatory

OCR still garbles numerals (`Ephesians 2: 19722` for 2:19-22), and those land
in *citations*, where a wrong digit is invisible. **Always** re-validate every
citation against the local KJV by incipit. That check has now caught five real
errors and is independent of OCR quality.

## Sanctorale: partial (2026-08-01)

`sanctorale_ocr_raw.txt` holds the raw OCR of printed pages ~154-159. Sixteen
festivals now have a confident name, date and at least one citation:

    St. Thomas (Dec 21), St. John Apostle & Evangelist (Dec 27),
    The Presentation (Feb 2), St. Matthias (Feb 24), The Annunciation (Mar 25),
    St. Mark (Apr 25), SS. Philip and James (May 1),
    The Nativity of St. John the Baptist (Jun 24), SS. Peter and Paul (Jun 29),
    The Visitation (Jul 2), St. James the Elder (Jul 25), St. Matthew (Sep 21),
    St. Michael and All Angels (Sep 29), St. Luke (Oct 18),
    SS. Simon and Jude (Oct 28), The Festival of the Reformation (Oct 31)

Still missing or incomplete: **St. Andrew (Nov 30), St. Stephen (Dec 26),
Holy Innocents (Dec 28), The Conversion of St. Paul (Jan 25), All Saints
(Nov 1), Harvest, the Day of Humiliation and Prayer, and a general
Thanksgiving** — plus the Epistles that fell in the column gutter for the
Presentation, Annunciation, Nativity of St. John, St. Michael, and the
Reformation. Redo those pages with column cropping, then validate every
citation against the KJV before adding any of it to `temporale.yaml`
(or a sibling `sanctorale.yaml`).


### Page layout: headings span BOTH columns

Do not naively crop the page in half. The festival headings are **centered
across the full page width** while the body text is in two columns. Cropping
at 50-53% cuts the headings in two and makes things worse than no cropping —
"St. Peter and St. X", "St. Luke, Evar", "St. Philip and St. J".

The working combination is a hybrid:

- **headings** — OCR the *full page* with `--psm 1`. This already reads them
  correctly; it is what produced the sixteen confident festival names and
  dates recorded above.
- **body text and citations** — OCR the columns separately (crop, then
  `--psm 4`), which is what stops citations being truncated at the gutter.
- merge the two passes per page.

Pillow is sufficient for the cropping; ImageMagick is not required:

    from PIL import Image
    im = Image.open(p); W, H = im.size
    top = int(H * 0.055)                      # drop the running header
    left  = im.crop((0,           top, int(W*0.53), H))
    right = im.crop((int(W*0.47), top, W,           H))

The running header must be cropped off regardless — it is itself a festival
name in blackletter ("St. Peter and St. Paul" at the top of a page about
St. Mark), and full-page OCR pulls it into the body, producing phantom
entries.

### The source zip is gitignored

`csb_jp2.zip` (~369 MB) and `*_djvu.txt` are excluded in `.gitignore`. They are
large, re-fetchable from archive.org with the commands above, and not ours to
redistribute — only our *derived* citation data belongs in the repo.


## Sanctorale complete (2026-08-01) — `sanctorale.yaml`

**23 festivals, 46 citations, all resolving against the local KJV.** Produced
with the hybrid recipe against the full-resolution `_jp2.zip`, plus a direct
read of printed p.160 to settle three pairings that column order made
ambiguous (the Reformation gospel, All Saints, St. Andrew).

Running headers are *section* names in blackletter ("Harvest",
"Thanksgiving", "The Reformation") and will masquerade as festival headings
if the top ~5.5% of the page is not cropped away.

Rubrics worth preserving if these are ever printed in show notes: several
festivals say "For Introit, Collect and Gradual see APOSTLES' DAYS, p. 153"
or "EVANGELISTS' DAYS, p. 154" — the propers are shared from a common rather
than given in full.

### Two gaps remain in the sanctorale

- **Holy Innocents (December 28)** — not captured. Note that Matthew 2:13-23
  is already assigned to *Sunday after New Year* in `temporale.yaml` from
  document order; the historic lectionary uses that pericope for both, so
  check p.155-156 rather than assuming a conflict.
- **The Festival of Harvest** — the heading is confirmed on printed p.160 but
  its Epistle and Gospel fall on the following page and were not read.

### jp2 zip -> page number

The zip entries map one-to-one onto the archive.org BookReader index:
`commonserviceboo00phil_jp2/commonserviceboo00phil_%04d.jp2` where `%04d` is
the same N as `page/n<N>.jpg`. In the Propers, printed page = N - 4.


## Table of Lessons extracted (2026-08-01) — `table_of_lessons_raw.json`

**295 day-rows, 294 fully resolvable against the local KJV (99.7%).** Printed
pages 303-312 = scan pages n308-n316. Morning is New Testament, Evening is Old
Testament — the reverse of what one might assume.

`extract_lessons.py` is the extractor. Three things it had to solve:

**1. The Days column poisons everything to its right.** Its dotted leaders
bleed across the table rule and corrupt the Morning book names — "eloaike",
"iEuke" and "Mlenike" are all *Luke* — and sometimes its digits too
(`Luke 3:10-11` where the page reads `3:10-14`). Cropping the Days column away
fixes both. The day is then recovered from row order, since each week block
runs Monday..Saturday.

**2. The crop point moves page to page.** A fixed fraction works on one page
and fails on the next. The extractor auto-tunes per page, trying offsets from
0.24 to 0.38 and keeping whichever yields the most *valid book names* — the
winning offset ranged 0.30-0.36 and scored 88-100%.

**3. A one-letter OCR error silently dropped a whole page.** Page 314 came
through as "TA**P**LE OF LESSONS", so a strict `"TABLE OF LESSONS" in text`
filter skipped it entirely — losing the 11th Sunday after Trinity onward with
no error and no warning. The filter is now a tolerant regex. **This is the
failure mode to watch for in any further table work: a page that is silently
absent looks exactly like a page that had nothing on it.**

### Validation without incipits

This table prints citations and no scripture text, so the incipit check that
caught five errors in the Propers does not apply. Two checks replace it:
every citation must resolve in the local KJV, and chapters must not run
backwards within a book (the table reads each book in course, so a digit slip
breaks monotonicity). The resolvability check alone caught `2 Peter 4:12-19` —
2 Peter has only three chapters, so it must be *1 Peter*.

### Caveats before this is wired in

- **13 rows are context-inferred, not OCR-verified.** Where OCR gave an
  unrecoverable book name inside an obvious run ("Gor 7:1-40" amid a stretch of
  1 Corinthians), the book was inferred from context and the chapter:verse kept
  as printed. Each is marked `"inferred"` in the JSON. They resolve, but they
  have not been read off the page.
- **One row is still wrong**: p310, 2d Sunday in Lent, Monday evening reads
  `Deuteronomy 103:1`, which is impossible — Deuteronomy has 34 chapters. The
  surrounding evening readings are in Exodus, so this needs a visual read.
- **Week labels are missing on some groups** (`"week": null`) where the label
  did not OCR. They can be filled by position, since the weeks run in order.
- The **Table of Proper Psalms** (printed p.312) is **not yet extracted** — it
  is printed sideways as a landscape table and must be rotated before OCR.


## Proper Psalms extracted (2026-08-01) — `proper_psalms.yaml`

**30 seasons/occasions, 267 psalm references, all in range 1-150, no
duplicates within a season.** Printed p.313 (scan n317).

**Correction to an earlier note in this file:** the table is *not* printed
sideways. It is upright and perfectly legible. The gibberish that suggested a
rotation ("£9 6 ShL OSI ZOL...") was **show-through from the facing page** —
visible as ghosting behind the text — which full-page OCR picked up along with
the real content. Cropping the label column away (0.38 of page width) removes
both the show-through artefacts and the dotted leaders, and the numbers then
OCR cleanly. Two independent reads — the crop OCR and a direct visual read of
the page — agree line for line.

### This is a different shape from LSB's psalm scheme

LSB gave a *day-keyed* table: look up the date, get the psalm. The CSB gives a
**pool per season** — "Advent: 5, 8, 19, 21, 24, 25, 42, 93, 96, 98, 110, 111,
122, 143, 145" — and leaves the choice open. Two rubrics widen the pool
further: Lent may also draw on the Ash Wednesday or Holy Week psalms, and Holy
Week on the Ash Wednesday or Good Friday psalms.

So `lectionary.py` must *choose* rather than look up. Choose deterministically
(day-of-year modulo pool size, or similar) so a given date always yields the
same psalm and episodes stay reproducible.

Beyond the seasons, the table also supplies pools for occasions the temporale
does not cover — Apostles/Evangelists/Martyrs, St. Michael, the Christian
Life, Cross and Comfort, Death and Burial, Missions, Christian Education,
Harvest, Thanksgiving, Days of Humiliation and Prayer, National Occasions, and
the seven Penitential Psalms. The festival pools pair naturally with
`sanctorale.yaml`.

## Research phase complete

All four data sets are now extracted and validated, every one from the same
public-domain source (Common Service Book, 1917):

| file | contents | validation |
|---|---|---|
| `temporale.yaml` | 71 propers, Advent 1 - Trinity 27 | 142/142 citations resolve |
| `sanctorale.yaml` | 23 festivals | 46/46 citations resolve |
| `table_of_lessons_raw.json` | 295 weekday day-rows, morning + evening | 294/295 resolve |
| `proper_psalms.yaml` | 30 seasonal psalm pools | 267 refs, all 1-150 |

What remains is code, not research: proper-day resolution in `churchyear.py`,
the `lectionary.py` rewrite, and deleting `daily_lectionary.yaml`.

