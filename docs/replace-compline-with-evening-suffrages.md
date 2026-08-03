# Replace Compline with the Evening Suffrages

**Status: DONE, 2026-08-02.** The third office is now
`luckylutheran/templates/evening-suffrages.yaml`. The retired Compline order
is at `docs/retired/compline.yaml`. This file is kept as the record of why the
change was made and how the text was obtained — see "How it was actually
extracted" at the end, which supersedes the earlier progress notes.

## Why

Compline as built is roughly half Anglican. No Lutheran book of the period
contains a Compline office at all — confirmed absent from the 1868/1893 Church
Book, the 1917/18 Common Service Book, and the 1881 Missouri Synod Church
Liturgy — so during the Compline pass its missing pieces were taken from *The
Book of Common Prayer with the Additions and Deviations Proposed in 1928* (the
English "Deposited Book").

| element | current source | Lutheran? |
|---|---|---|
| Confession | 1881 Missouri Synod Church Liturgy | ✅ |
| Nunc Dimittis, Lord's Prayer, Kyrie | shared with Vespers | ✅ |
| Opening versicle | 1928 Deposited Book | ❌ Anglican |
| Both collects (*Visita quaesumus*, *Adesto*) | 1928 Deposited Book | ❌ Anglican |
| Benediction | 1928 Deposited Book | ❌ Anglican |
| Nunc Dimittis antiphon | 1928 recension | ❌ Anglican |

The original justification — that these are ancient Western prayers predating
the Reformation, and that no Lutheran alternative existed — is defensible but
beside the point. **This is a Lutheran podcast whose entire claim is that
everything is cited.** A borrowed office is the first thing an informed critic
would find, and SOURCES.md hands it to them.

## The replacement

The Common Service Book (1917) — already this project's source for Matins,
Vespers, the collects, the lectionary and the psalms — contains **The Evening
Suffrages**, with this rubric:

> ¶ The Evening Suffrages may be said at Vespers, or in the Evening Prayer of
> the Household, or alone as **a brief Evening Office**.
>
> ¶ When used as a special Evening Office, the Evening Suffrages shall begin:
> ℣. In the Name of the Father, and of the Son, and of the Holy Ghost.
> ℟. Amen. After the Creed shall follow a Psalm, a brief Lesson with the
> Response, and a Hymn; and after the Benedicamus shall be said this
> Benediction: The Blessing of Almighty God, the Father, the Son, and the Holy
> Ghost, be with you all. ℟. Amen.

A complete, self-contained Lutheran brief evening office, whose own rubric
authorises household use. That *is* this project's premise, in the source
book's words.

### Order, as the rubric gives it

1. ℣. In the Name of the Father, and of the Son, and of the Holy Ghost. ℟. Amen.
2. The Apostles' Creed
3. The Kyrie — **doubled** (see below)
4. The Lord's Prayer
5. A Psalm
6. A brief Lesson, with the Response
7. A Hymn
8. The Suffrages proper — "Blessed art Thou, O Lord God of our fathers: And
   greatly to be praised and glorified, forever. / Bless we the Father, and the
   Son, and the Holy Ghost: We praise and magnify Him forever. / Blessed art
   Thou, O Lord, in the firmament of heaven: …"
9. The Benedicamus
10. The Benediction: "The Blessing of Almighty God, the Father, the Son, and
    the Holy Ghost, be with you all. ℟. Amen."

## What was done

All six steps below are complete. Two of them turned out differently than
planned, and the differences are the interesting part.

1. ✅ **Extracted the full order** from scan pages n193-n196 — but *not* with
   the OCR recipe this plan called for. See the next section: OCR is the wrong
   tool for this page layout, and the recipe here was the thing that stalled
   the first attempt.
2. ✅ **Wrote `luckylutheran/templates/evening-suffrages.yaml`.** The `psalm`,
   `reading` and `hymn` slots are kept, but the guess in the original step —
   "so this office *is* variable, unlike Compline" — was **wrong**. The rubric
   calls for a Psalm and a brief Lesson without appointing either, so the
   choice falls to us, and making it variable would have had Vespers and this
   office drawing the identical psalm every single night (`_psalm_for` is
   keyed on the date). The office is invariable, and now has a citation for
   the set it says.
3. ✅ **Retired `compline.yaml`** to `docs/retired/`, with a header explaining
   why and what in it is worth keeping.
4. ✅ **Updated the code**: `assemble.OFFICES`, `assemble._greeting`,
   `feed.PUBLISH_HOUR`, `feed.PODCAST`, `lectionary.readings_for` and its
   `NIGHT_PSALMS`/`NIGHT_LESSON` (the old invariable-Compline special case
   was renamed and given a source, not removed — see step 2), plus a
   `Suffrages` respelling in `speech.PRONUNCIATION`. Two transcript fixes fell
   out of it: `source == "ordinary"` was printing "Read in course", and three
   psalms read as "A and B and C".
5. ✅ **Updated the prose**: `feed.PODCAST["description"]`, the artwork
   subtitle (now "MATINS · VESPERS · SUFFRAGES"), `docs/show-description.md`,
   the README and SOURCES.md. The artwork had **no generator script** — it was
   built once by hand and nothing could rebuild it — so `tools/artwork_subtitle.py`
   was written to re-letter the subtitle band in place, matching the sampled
   colours, font and metrics rather than reconstructing the composition.
6. ✅ **Named it "The Evening Suffrages"**, which is what the book calls it.

## How it was actually extracted — and the lesson

**OCR was the wrong tool and was abandoned.** These pages are two-column body
text with a *full-width rubric band running underneath*, so every column crop
spliced the two registers together and produced text that looked continuous
but was not — e.g. "Che Hlorning : O Lord, let there be peace... The Morning
Suffrages may be said ai Matins" is two different registers joined mid-
sentence. The first attempt at this migration stalled there, trying to fix the
crop geometry.

The fix was to stop cropping. The page images were downscaled 2:1 from the
JP2s and **read directly** — at 1077×1600 the CSB's body type is comfortably
legible, blackletter headings included, and a page read has no splice failure
mode at all because nothing is being reassembled. The whole office came off
four pages in two reads, with the rubrics, the italic responses and the
paragraph marks all correctly attached to what they govern.

    unzip -o -j csb_jp2.zip "commonserviceboo00phil_jp2/commonserviceboo00phil_0194.jp2"
    python3 -c "from PIL import Image; im=Image.open('...0194.jp2'); \
        im.resize((im.width//2, im.height//2), Image.LANCZOS).save('p194.png')"
    # then read p194.png directly

**Use this for any page whose layout is not a plain single column.** OCR earns
its keep on long uniform tables — the Table of Lessons, the psalm table, the
propers — where there is far too much text to read and the shape is regular.
It is a liability on a page with mixed registers. The known-bad column crops
from the first attempt were deleted rather than kept, so nobody trusts them
later.

### Pages

| scan | printed | contents |
|---|---|---|
| n193 | 189 | end of the Morning Prayers; **The Morning Suffrages** begin |
| n194 | 190 | Morning Suffrages continue; **The Evening Suffrages** begin — rubric, Kyrie, Lord's Prayer, Creed |
| n195 | 191 | Creed concludes; **the Suffrages proper**, salutation, collect rubric, the Evening Prayer, Benedicamus, Benediction |
| n196 | 192 | General Prayers — past the end of the office |

The Response the rubric names but does not print was taken from the CSB's own
order of **Vespers, printed p. 42 (scan n47)**.

## What the extraction settled

**The Kyrie line-count.** The Evening Suffrages **doubles** every line. That is
a third witness, joining the 1912 ELHB's Vespers order against the ELHB's
Communion order. `evening-suffrages.yaml` doubles accordingly. Matins and
Vespers still say each line once and were **not** changed — that alters two
offices already rendered and heard, so it is recorded in SOURCES.md as the one
open decision rather than made silently.

**The benediction.** No reconciliation was needed after all. The book prints
2 Corinthians 13:14 ("The Grace of **our** Lord Jesus Christ…") for the
Suffrages said *after Vespers*, but the rubric appoints a different blessing
when the office is said *alone* — "The Blessing of Almighty God, the Father,
the Son, and the Holy Ghost, be with you all." That is the form used, so the
"our Lord" / "the Lord" question against Matins and Vespers never arises here.

**Two unrelated flags closed.** Reading CSB p. 42 for the Response also settled
both remaining ⚠️ items in SOURCES.md: the **incense versicle** is printed
**singular** there, exactly as `vespers.yaml` has it, and the **Responsory**
turns out to be a book-to-book recension difference (CSB vs. 1912 ELHB) with
both forms PD-attested, not an office-specific one as earlier guessed.

**The Psalm and Lesson.** The rubric calls for "a Psalm, a brief Lesson with
the Response, and a Hymn" and appoints none of them. It could not be the day's
psalm — `_psalm_for` is keyed on the date, so Vespers and this office would
draw the identical psalm every night. It takes the historic night psalms
instead, cited to the **Rule of St Benedict, ch. 18** (verified against three
independent PD English editions), which is pre-Reformation Western patrimony
rather than an Anglican borrowing — the whole distinction this change exists
to draw.

## What was decided and not done

**The Morning Suffrages** (p. 189) carry the identical rubric, mutatis
mutandis — "may be said at Matins, or in the Morning Prayer of the Household,
or alone as a brief Morning Office." The CSB therefore supplies a matched
household pair. If a brief morning office is ever wanted, it is already
sourced and the extraction method above applies unchanged.

**The retired Compline's Confession** is genuinely Lutheran (1881 Missouri
Synod, verified) and could be carried into the Evening Suffrages if a
confession is ever wanted there. The Anglican collects should not be.

**The noon office** was already declined and recorded in SOURCES.md; this
change did not revive it.
