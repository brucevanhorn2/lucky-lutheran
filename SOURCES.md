# Sources and Public-Domain Basis

This document tracks exactly where every piece of spoken content in the
podcast comes from, and the evidence that each source is free to use. It
exists because the podcast is public and everything in it must be public
domain — no LSB (© Concordia Publishing House), no ESV (© Crossway), no
1986/1991 CPH catechism translation, no TLH 1941 text taken directly (its
only available scan is copyright-restricted; see below).

Legend: **✅ Verified** = checked word-for-word against a raw copy of the
cited source. **⚠️ Unverified** = sourced/composited but not yet checked
against a raw primary text; carries a `!! VERIFY` comment in the file itself.

## Scripture (Psalms, Lessons, Table of Duties, Words of Institution)

| Source | `luckylutheran/data/kjv.txt`, `kjv_index.json` |
|---|---|
| Title | The Holy Bible, King James Version (Authorized Version), Project Gutenberg eBook #10 |
| PD basis | The KJV text itself is public domain in the US (Crown Copyright applies only in the UK/Commonwealth, not the US). The Project Gutenberg transcription (eBook #10, gutenberg.org/ebooks/10) is explicitly released to the public domain in the US. |
| Status | ✅ Verified — 31,102 verses parsed, matching the canonical KJV verse count exactly; cross-checked against bible-api.com as an independent oracle for boundary correctness (two real parser bugs found and fixed this way: testament-divider text and a stray `***` marker leaking into Malachi 4:6). |
| Notes | `bible-api.com` (also KJV) is retained only as a network fallback for any reference the local parser can't resolve; `test_scripture_uses_local_kjv_offline` proves the local index is used first. |

## Daily Lectionary and Psalms — ✅ RESOLVED

**The LSB dependency is gone.** `daily_lectionary.yaml`, transcribed from the
Lutheran Service Book (CPH 2006) on an untested "facts aren't copyrightable"
argument, has been deleted. It supplied both the readings *and* the psalm
tables; both are now drawn from public-domain sources. No permission was
sought and none is needed. See `docs/lectionary-migration/` for the full
extraction record.

| Part | Source | Status |
|---|---|---|
| Sundays & festivals | The historic one-year lectionary, from the Propers of the *Common Service Book of the Lutheran Church* (1917), archive.org `commonserviceboo00phil` — already this repo's verified source for Matins, Vespers, the collects and the Evening Suffrages. `data/temporale.yaml` (71 propers, Advent 1 – Trinity 27) and `data/sanctorale.yaml` (23 fixed festivals). | ✅ Verified — all 188 citations resolve against the local KJV; alignment confirmed against page scans at four points across the book. |
| Weekdays | Continuous course reading — Gospels in the morning, Acts and the Epistles in the evening, a chapter a day. **No source needed:** this is a *method*, and 17 USC 102(b) excludes methods from copyright outright. It also mirrors Luther's own practice in the *Deutsche Messe* (1526), which assigned books to weekdays and worked through them in course. | ✅ Not a compilation at all — a stronger footing than any "facts aren't copyrightable" claim. |
| Psalms | `data/proper_psalms.yaml`, the CSB's **Table of Proper Psalms for Festivals and Seasons** (printed p.313). 30 seasons and occasions, 267 references. | ✅ Verified — all in range 1–150, cross-read twice (cropped OCR and a direct read of the page). |

**On the psalms specifically:** the CSB gives a *pool per season* rather than a
day-keyed table — it appoints a set and leaves the choice open. `lectionary.py`
therefore chooses from the pool by day-of-year, deterministically, so a given
date always yields the same psalm and episodes stay reproducible.

**Still on the shelf, not wired in:** the CSB also carries a complete daily
weekday lectionary, *"IX. A Table of Lessons for Morning and Evening
Throughout the Year"* (printed pp.303–312). It is extracted and citation-validated
(295 rows, 294 resolving) in `docs/lectionary-migration/table_of_lessons_raw.json`,
but its **week-keying is not yet reliable** — OCR paragraph breaks split weeks
across groups, so mapping rows to church-year weeks would mis-key some of them.
A mis-keyed lectionary serves wrong readings silently, every day, so it was
deliberately left out. Finishing that keying would upgrade weekdays from course
reading to the CSB's own seasonal weekday lessons.

## Why there is no noon office

Considered and **declined**, 2026-08-02. Recorded here because the idea is
likely to recur.

LCMS practice today knows Matins, Vespers and Compline; LSB also prints brief
household orders for Morning, Noon, Early Evening and the Close of Day — but
those are 2006 CPH text and unavailable to this project.

The historic noon hour is **Sext**, one of the monastic little hours. It is
not a Lutheran office in any meaningful sense: the Reformation church orders
kept Matins and Vespers for congregational use and let the little hours lapse,
and Luther criticised the monastic hours directly. No Lutheran service book has
carried Sext.

The 1928 Deposited Book was proposed as a source and turns out **not to contain
the little hours** at all — it added Compline but not Prime, Terce, Sext or
None. The books that do carry them (*The Day Hours of the Church of England*,
the Sarum lesser hours) are Anglican, with an Anglican calendar and Anglican
propers. Importing Sext from them would dress a Lutheran office in another
tradition's vestments.

If a midday devotion is ever wanted, the honest Lutheran material is already to
hand: the Small Catechism's table of daily prayers, whose blessing before meat
("The eyes of all wait upon Thee, O Lord") is a genuine household noon
devotion. That would be a Lutheran table prayer, not a monastic hour, and
should be described as such.

## ✅ Compline was replaced — the third office is now Lutheran

**Done 2026-08-02.** Compline's opening versicle, both collects, benediction
and Nunc Dimittis antiphon came from the 1928 Deposited Book, which is
Anglican. They were taken because no Lutheran book of the period contains a
Compline office at all. The prayers are ancient Western texts predating the
Reformation, so the borrowing was defensible — but this project's whole claim
is that everything is cited, and a borrowed office is the first thing an
informed critic would find.

The replacement was in the book already used for everything else: the Common
Service Book's **Evening Suffrages** (1917, pp. 190-191), whose own rubric
appoints it "at Vespers, or in the Evening Prayer of the Household, or alone
as a brief Evening Office" — this project's premise stated in the source
book's words. It is now `luckylutheran/templates/evening-suffrages.yaml`; the
retired order is kept, with all its citations, at `docs/retired/compline.yaml`.

See the **Evening Suffrages** section below, and
**[docs/replace-compline-with-evening-suffrages.md](docs/replace-compline-with-evening-suffrages.md)**
for the account of the change.

## Matins

| Source | `luckylutheran/templates/matins.yaml` |
|---|---|
| Primary sources | *Evangelical Lutheran Hymn-Book* (Concordia Publishing House, 1912), via Project Wittenberg (public-domain release, explicitly stated on the source page); *Common Service Book of the Lutheran Church* (General Synod/General Council/United Synod South, 1917/1918), via archive.org, unrestricted scan (`commonserviceboo1917phil` et al.) |
| PD basis | Both are US publications from before 1930 — automatically public domain under the rolling PD cutoff. |
| Status | ✅ Verified: opening versicles, invitatory, Venite, Te Deum, salutation, Lord's Prayer, Benedicamus, Collect for Grace, Benediction (fixed: "the Lord Jesus Christ" not "our Lord Jesus Christ", confirmed via 2 Cor. 13:14 KJV). |
| | ✅ **Luther's Morning Prayer — now verified** against the English column of *Concordia Triglotta* (CPH, 1921), Small Catechism Appendix I, archive.org `concordiatriglot00unse`, unrestricted, pre-1930. The earlier flag was correct: fixed to "I pray Thee **to keep me**" (was "that Thou wouldst keep me") and "from sin and **all** evil" (was "every evil"). |
| | ✅ **Responsory — no longer unverified, but a choice.** The disagreement is real and both sides are public domain: the 1912 ELHB's Vespers order has "But Thou, O Lord, have mercy upon us / Thanks be to Thee, O Lord", while the 1917 CSB prints "℣. O Lord, have mercy upon us. ℟. Thanks be to God." — and, checked directly on p. 42 (2026-08-02), the CSB uses that same form in **Vespers** as well as Matins. So the earlier guess that the wording might be office-specific is wrong for the CSB; it is a book-to-book recension difference. Ours follows the ELHB, which is a real PD source. Nothing to fix; the only open question is which book to follow, and that is a taste call, not a rights one. |
| | ⚠️ **Kyrie line-count — evidence now favours doubling, and our files do not.** The 1917 CSB's Evening Suffrages (p. 190) doubles every line, joining the 1912 ELHB's Vespers order against the ELHB's Communion order. That is two witnesses to one for the evening offices. `evening-suffrages.yaml` doubles them accordingly; `matins.yaml` and `vespers.yaml` still say each line once. **This is a live inconsistency awaiting a decision** — not a copyright question, and not changed unilaterally, because it alters two offices already rendered and heard. |
| Not consulted | TLH (1941) itself — only a copyright-restricted archive.org lending scan (`bwb_T4-APS-822`, `access-restricted-item: true`) was found; abandoned rather than circumvented. |

## Vespers

| Source | `luckylutheran/templates/vespers.yaml` |
|---|---|
| Primary sources | Same two predecessor editions as Matins (1912 ELHB, 1917/18 Common Service Book). |
| Status | ✅ Verified: opening versicles, Magnificat (fixed: "holpen" not "helped", confirmed via Luke 1:54 KJV + both period sources), Nunc Dimittis, Lord's Prayer, salutation, Benedicamus, Collect for Peace (fixed ending, confirmed against the Common Service Book's own text), Benediction (same fix as Matins). |
| | ✅ **Luther's Evening Prayer — now verified** against the same Triglotta Appendix I. The earlier flag was correct: fixed to "I pray Thee **to forgive** me all my sins" (was "that Thou wouldst forgive"). |
| | ✅ **The incense versicle — now verified.** Read directly off the 1917 CSB's order of Vespers, p. 42 (2026-08-02): "℣. Let my prayer be set forth before Thee as incense. ℟. And the lifting up of my hands as the evening sacrifice." **Singular**, exactly as this file has it. The 1912 ELHB's plural "prayers" is the variant, not ours. The earlier flag is closed. |
| | Responsory and Kyrie line-count: see the Matins rows above — same two questions, same evidence, and the Kyrie remains the one open decision. |
| Not consulted | TLH (1941) — same restricted-scan issue as Matins. |

## The Evening Suffrages

*Replaced the former Compline order on 2026-08-02. The retired file, with all
of its own citations and the reasoning behind them, is at
`docs/retired/compline.yaml`; the account of the change is in
[docs/replace-compline-with-evening-suffrages.md](docs/replace-compline-with-evening-suffrages.md).*

| Source | `luckylutheran/templates/evening-suffrages.yaml` |
|---|---|
| Primary source | *Common Service Book of the Lutheran Church* (Philadelphia, 1917/18), **The Evening Suffrages**, pp. 190-191. archive.org `commonserviceboo00phil`, unrestricted scan. Pre-1930 US publication, so automatically public domain. This is the same book that already supplies Matins, Vespers, the collects, the one-year lectionary and the psalm table. |
| Why this office | Its own rubric authorises exactly this use: "¶ The Evening Suffrages may be said at Vespers, or in the Evening Prayer of the Household, **or alone as a brief Evening Office**." A second rubric gives the complete order for that standalone form — the trinitarian opening, the Psalm/Lesson/Hymn after the Creed, and the closing Benediction — so nothing had to be assembled or inferred. The office is used in that third form here. |
| Status | ✅ **Verified — the whole order**, read directly off the page images rather than OCR'd (the page carries two-column body text with a full-width rubric band beneath it, which defeats column-crop OCR by splicing the two registers together; see the migration doc). Opening versicle, doubled Kyrie, Lord's Prayer, Apostles' Creed, the Suffrages proper, salutation, the Evening Prayer, Benedicamus and Benediction are all transcribed from pp. 190-191 word for word, including the book's own capitalization. |
| | ✅ **Verified — the Response** the rubric names but does not print. It is in the CSB's own order of Vespers, p. 42, under The Lesson: "¶ The Scripture Lessons shall then be read. After each Lesson shall be sung or said the Response. ℣. O Lord, have mercy upon us. ℟. Thanks be to God." |
| | ✅ **Verified — the Psalm and the Lesson.** The rubric calls for "a Psalm, a brief Lesson with the Response, and a Hymn" but appoints none of them, the same open hand the CSB's psalm table shows — so the choice is ours and had to be made on a principle. It could not be the day's psalm: `_psalm_for` is keyed on the date, so Vespers and this office would draw the identical psalm every night. It takes the historic night psalms instead, which is what an office at the close of day is for. The set is appointed in the **Rule of St Benedict (c. 530), ch. 18** — *"Ad Completorium vero quotidie iidem Psalmi repetantur; id est quartus, nonagesimus, et centesimus trigesimus tertius"* — Vulgate numbering, which is KJV 4, 91 and 134. Checked against three independent PD English editions on archive.org, all agreeing word for word: `TheRuleOfStBenedict` (1907, prints the Latin alongside), `TheRuleOfOurMostHolyFather` (1875), `rulestbenedictf00benegoog` (1875, from the English edition of 1638). The brief Lesson is 1 Peter 5:8-9, the traditional short chapter of the night office, read from the KJV. |
| | This is pre-Reformation Western patrimony, **not** an Anglican borrowing — the distinction that retired the old order. The Lutheran confessions claim it explicitly (Ap. XV; cf. AC XXIV, "we keep the ancient rites"). No 1928 Deposited Book text survives anywhere in the office. |
| Ours, not the book's | Two insertions, both marked in the file: the spoken **welcome** (no printed office has one; every office in this project carries one) and the **daily catechism portion**, placed after the Hymn where Vespers puts it. Nothing else is added, moved or reworded. |
| Note — the benediction | The book prints 2 Corinthians 13:14 ("The Grace of **our** Lord Jesus Christ…") as the benediction of the Suffrages said *after Vespers*, but the rubric appoints a different blessing when the office is said *alone*: "The Blessing of Almighty God, the Father, the Son, and the Holy Ghost, be with you all." That is the form used here, so the "our Lord" / "the Lord" discrepancy against Matins and Vespers never arises in this office. |
| Note — the Evening Prayer | The prayer the book prints after the collect is Luther's Evening Prayer from the Small Catechism **in the plural** ("we", "us", "our bodies and souls"), as a household says it together. Vespers carries the same prayer in Luther's own singular, from the 1921 Concordia Triglotta. These are not a duplication to be resolved — they are the prayer as the catechism teaches it privately and as the office says it corporately, and each file follows its own source. |
| Note — the Morning Suffrages | The CSB prints the matching **Morning Suffrages** on p. 189 with the identical rubric, mutatis mutandis: "may be said at Matins, or in the Morning Prayer of the Household, or alone as a brief Morning Office." So the book supplies a matched household pair. If a brief morning office is ever wanted, it is already sourced. |

## Catechism

| Source | `luckylutheran/data/small_catechism.yaml` |
|---|---|
| Primary source | *Concordia Triglotta: Die symbolischen Bücher der evangelisch-lutherischen Kirche* (Concordia Publishing House, St. Louis, 1921), English column, Small Catechism pp. 539–557 + Appendix I. archive.org `concordiatriglot00unse`, unrestricted scan. Pre-1930 US publication → public domain. |
| Core portions — 10 Commandments, their Close, 3 Creed articles, Baptism, Sacrament of the Altar (16 portions) | ✅ **Verified** word for word against the Triglotta's English column. Ten were already correct. Six had drifted toward the familiar TLH (1943) English and were corrected to the 1921 source: cmdt 4 ("serve, obey, and hold them"), cmdt 9 ("seek to get"), cmdt 10 ("anything that is his"), the Close ("contrary to these commandments"), Creed 2 ("in order that I may be His own"), and Creed 3 ("**one** holy Christian Church", "He forgives daily and richly", "at the last day will raise up", "everlasting life"). Creed 1 was reworded substantially — "limbs" for "members", "in addition thereto" for "also", "house and homestead", "provides me richly and daily", "protects me from all danger, and guards me and preserves me from all evil", "out of pure, fatherly", "for all which I owe it to Him to thank, praise, serve, and obey Him". |
| Table of Duties (14 entries) + "Christian Questions" Words of Institution | Not hand-transcribed — resolved live via `scripture.get_passage()`, the same local-KJV-first path used for lectionary readings. |
| Status | ✅ Verified by construction — no manual transcription risk, inherits the KJV verification above. |
| ~~"Christian Questions with Their Answers" (8 portions)~~ | ✅ **REMOVED 2026-08-01 — no longer a risk.** Deleted from the rotation rather than repaired. Retained here for the record: Two separate problems. First, the Triglotta **does not contain the Christian Questions at all**: it discusses them in its historical introduction (p. 88 — first published 1549, attributed to Luther in a 1551 edition) but prints no text, running straight from the Sacrament of the Altar into Appendix I. The file's former claim that this section followed the Triglotta was simply wrong. Second, the wording here is modern second person ("Do you believe that you are a sinner?"), which is the register of the **current CPH translation** — the very text this project refuses to use. Any pre-1930 English printing would read "Dost thou believe…", matching the Thou register used everywhere else in the repo; that mismatch is the tell that this was recalled from a modern copyrighted source. Searched without success: the Triglotta, the 1881 Missouri Synod Church Liturgy, the 1912 ELHB (and its 1905/1909 printings), Crull's 1879/1884 hymn books, and five pre-1930 English Small Catechism editions on archive.org. They were in any case an appendix rather than a chief part — first printed 1549, three years after Luther’s death, attributed to him only from a 1551 edition, and the Triglotta does not print them at all — and their content largely restated Creed and Sacrament portions already in the rotation. The effort went into the missing **Confession** chief part instead. A public-domain German text exists (1894 BSB scan `11581004bsb`, corroborated by 1878 `drmartinluthersk0000mart`) should a fresh translation ever be wanted. |
| Confession — the Fifth Chief Part (3 portions) | ✅ **Verified**, added 2026-08-01 from the same Triglotta English column, "V. How the Unlearned Should Be Taught to Confess" (pp. 551-553). Only the catechetical questions are included: what Confession is, what sins to confess, and considering one’s station by the Ten Commandments. Luther’s chief part continues into a Brief Form of Confession ending *"And by the command of our Lord Jesus Christ I forgive thee thy sins"* — the declarative absolution reserved to a called and ordained minister (AC XIV) — **deliberately omitted**, on the same principle that governs Compline’s absolution. |
| Coverage | **All six chief parts are complete**: the Ten Commandments with their Close, the Creed, the whole Lord’s Prayer, Holy Baptism (4 portions), Confession (3), and the Sacrament of the Altar (4) — plus the Table of Duties and the Words of Institution. 49 portions in all, in the catechism's own order. Scripture quoted *inside* a chief part is transcribed as the Triglotta prints it, since Luther's proof texts are part of the catechetical text and his wording is sometimes his own; standalone scripture still resolves from the KJV index. |

## Collects (seasonal, `luckylutheran/data/collects.yaml`)

| Primary source | Propers of the *Common Service Book of the Lutheran Church* (1917), archive.org `commonserviceboo00phil`, unrestricted scan. Pre-1930 US publication → public domain. The same edition already used for Matins and Vespers. TLH (1941) is **not** the source and was not consulted; the Common Service Book prints the same Common Service propers and is free to quote. |
| Status | ✅ **Verified** — all ten seasonal collects checked word for word. Advent, Christmas, and Trinity were already correct. Seven were corrected. |
| Material corrections | Two were substantively wrong rather than cosmetic: the **Lent** and **Holy Week** collects had lost their entire trinitarian conclusion, ending at "through Jesus Christ, our Lord" where the source continues "…Thy Son, our Lord, Who liveth and reigneth with Thee and the Holy Ghost, ever One God, world without end." The **Whitsuntide** collect ended "with Thee and *the same Spirit*" where the source reads "with Thee and the Holy Ghost." |
| Minor corrections | Epiphany and Ascension: "Thy only-begotten" (was "Thine"); Ascension: "so may we also" (was "so we may also"); Easter: "through Jesus Christ, Thy Son, our Lord" (was "through the same Jesus Christ, our Lord"); Lent: "all those who are penitent" (was "all them that are penitent"); Pre-Lent: "offences"; Holy Week: "Saviour". Source spellings retained even where they differ from modern US usage. |
| Still to come | One collect per *season* only. The historic propers assign one per *Sunday*, and the Common Service Book prints all of them — addable under a `sundays:` key with no code change. |

## Summary: what's left before "proof of PD" is complete

0. ✅ **The daily lectionary — resolved.** The LSB file is deleted; readings and psalms now come from the 1917 Common Service Book and from course reading, which is a method rather than a compilation. There is no longer any rights question outstanding in this project. Optional future work: finish keying the CSB's own weekday Table of Lessons (extracted, validated, not yet wired in).
1. ✅ **The third office is resolved.** Compline — which was roughly half Anglican, its versicle, collects, benediction and antiphon all from the 1928 Deposited Book — has been **replaced** by the Common Service Book's Evening Suffrages, whose own rubric appoints it for household use. Every line of the new office is transcribed from the 1917 CSB; the night psalms are cited to the Rule of St Benedict, ch. 18. No Anglican text remains anywhere in the project. The retired order is preserved at `docs/retired/compline.yaml`.
2. `small_catechism.yaml`'s 16 chief-part portions are **verified** against the 1921 Concordia Triglotta (six corrected). The **8 Christian Questions portions are a live copyright risk** and are the single highest-priority item on this list — see the Catechism section above. Everything else in the file is safe.
3. `collects.yaml`'s ten seasonal collects are **verified** against the 1917 Common Service Book's Propers (seven corrected, two of them materially — restored trinitarian conclusions). Remaining work here is additive, not corrective: per-Sunday collects, which the same source supplies.
4. Matins/Vespers: Luther's Morning and Evening Prayers are **verified** against the Triglotta (both earlier flags were correct and are fixed). Of the three items that were ambiguous, two are now closed by direct page reads of the 1917 CSB (2026-08-02): the **incense versicle** is verified singular, as we have it, and the **Responsory** turns out to be a book-to-book recension difference with both forms PD-attested, ours following the 1912 ELHB. The **Kyrie line-count** is the one item left, and it is now a decision rather than a search: two witnesses to one favour doubling, `evening-suffrages.yaml` doubles, and Matins/Vespers do not.

Everything else — all of scripture, and the bulk of Matins/Vespers liturgy —
is checked word-for-word against confirmed-PD raw source text.
