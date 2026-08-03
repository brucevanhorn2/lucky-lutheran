# Replace Compline with the Evening Suffrages

**Status: planned, not started.** `compline.yaml` is still the live third
office. Read this before touching it.

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

## Steps

1. **Extract the full order** from the page images. It begins around flat-text
   offset ~found via `grep -o -i "evening suffrages may be said" csbA_flat.txt`;
   locate the printed page, then use the hybrid OCR recipe (full page
   `--psm 1` for blackletter headings, cropped columns `--psm 4` for body) as
   documented in `lectionary-migration/README.md`. Verify every scripture
   citation against the local KJV, as always.
2. **Write `luckylutheran/templates/evening-suffrages.yaml`** in the same shape
   as the existing templates. Keep the `psalm`, `reading` and `hymn` slots —
   the rubric explicitly calls for a Psalm, a brief Lesson and a Hymn, so this
   office *is* variable, unlike Compline.
3. **Retire `compline.yaml`.** Do not delete it — move it to `docs/retired/`
   with a header explaining why, so the work and its citations survive.
4. **Update the code**: `assemble.OFFICES`, `feed.PUBLISH_HOUR`,
   `churchyear`/`lectionary` office checks, and `lectionary.readings_for` —
   note the invariable-Compline special case added 2026-08-02 must go, since
   the Evening Suffrages take a psalm and lesson.
5. **Update the prose**: `feed.PODCAST["description"]`, the artwork subtitle
   ("MATINS · VESPERS · COMPLINE"), `docs/show-description.md`, the README, and
   SOURCES.md.
6. **Decide the name.** "The Evening Suffrages" is what the book calls it.
   Do not call it Compline — that is the borrowing this change exists to
   remove.

## Two things this also settles

**The Kyrie line-count.** SOURCES.md has carried a ⚠️ since the first pass
because the 1912 ELHB's Communion order says each Kyrie line once while its
Vespers order doubles them. The Evening Suffrages **doubles** them — "Lord,
have mercy upon us. Lord, have mercy upon us. Christ, have mercy upon us…" —
which is a third witness and resolves the flag for the evening offices.

**The noon office.** Already declined and recorded in SOURCES.md; this plan
does not revive it.

## What to do about the retired Compline

Its Confession is genuinely Lutheran (1881 Missouri Synod, verified) and could
be carried into the new office if a confession is wanted there. The Anglican
collects should not be.

---

## Extraction progress (2026-08-02) — page located, text not yet complete

**The office is on scan pages n193-n196** (printed ~189-192). Running headers:
n193 "The Morning Suffrages", n194 "General Prayers", n195 "The Bidding
Prayer" — the Morning and Evening Suffrages sit adjacent, with the Evening
rubric beginning on n194.

Column crops of n193 and n194 are saved in `docs/evening-suffrages-extract/`.

### The layout trap on these pages

Unlike the Propers, these pages are **two-column body text with a full-width
rubric block running underneath**. A plain column crop therefore interleaves
the rubric with the body and produces text that looks continuous but is not —
e.g. "Che Hlorning : O Lord, let there be peace... The Morning Suffrages may
be said ai Matins" is two different registers spliced together.

Extract the rubric band and the body columns **separately**, by vertical
position, before OCR. Do not trust a single-pass column crop here.

### Confirmed so far

The Morning Suffrages carry the identical rubric, mutatis mutandis — "may be
said at Matins, or in the Morning Prayer of the Household, or alone as a brief
Morning Office." So the Common Service Book provides a matched household pair,
morning and evening. Worth knowing: if the Evening Suffrages replace Compline,
the **Morning Suffrages** are the natural short-form Matins, should a brief
option ever be wanted.

Both end with the same Benedicamus and Benediction:

> Bless we the Lord. / Thanks be to God.
>
> The Grace of our Lord Jesus Christ, and the Love of God, and the Communion
> of the Holy Ghost, be with you all. Amen.

Note that benediction is 2 Corinthians 13:14 — the same text already used in
Matins and Vespers, and already verified. It reads "our Lord Jesus Christ"
here; the Matins/Vespers files were corrected to "the Lord Jesus Christ" from
the 1912 ELHB and the KJV. Reconcile deliberately rather than silently.

### Next step

Re-OCR n193-n196 with the rubric band and body columns separated, assemble the
full Evening Suffrages order, then proceed with steps 2-6 above.

