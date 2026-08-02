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
| Sundays & festivals | The historic one-year lectionary, from the Propers of the *Common Service Book of the Lutheran Church* (1917), archive.org `commonserviceboo00phil` — already this repo's verified source for Matins, Vespers, the collects and the Compline confession. `data/temporale.yaml` (71 propers, Advent 1 – Trinity 27) and `data/sanctorale.yaml` (23 fixed festivals). | ✅ Verified — all 188 citations resolve against the local KJV; alignment confirmed against page scans at four points across the book. |
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

## Matins

| Source | `luckylutheran/templates/matins.yaml` |
|---|---|
| Primary sources | *Evangelical Lutheran Hymn-Book* (Concordia Publishing House, 1912), via Project Wittenberg (public-domain release, explicitly stated on the source page); *Common Service Book of the Lutheran Church* (General Synod/General Council/United Synod South, 1917/1918), via archive.org, unrestricted scan (`commonserviceboo1917phil` et al.) |
| PD basis | Both are US publications from before 1930 — automatically public domain under the rolling PD cutoff. |
| Status | ✅ Verified: opening versicles, invitatory, Venite, Te Deum, salutation, Lord's Prayer, Benedicamus, Collect for Grace, Benediction (fixed: "the Lord Jesus Christ" not "our Lord Jesus Christ", confirmed via 2 Cor. 13:14 KJV). |
| | ✅ **Luther's Morning Prayer — now verified** against the English column of *Concordia Triglotta* (CPH, 1921), Small Catechism Appendix I, archive.org `concordiatriglot00unse`, unrestricted, pre-1930. The earlier flag was correct: fixed to "I pray Thee **to keep me**" (was "that Thou wouldst keep me") and "from sin and **all** evil" (was "every evil"). |
| | ⚠️ Unverified: the Responsory ("But Thou, O Lord, have mercy upon us...") — the Vespers-order and Matins-order predecessor texts disagree with each other. The Kyrie line-count (single vs. doubled) — the Communion order and Vespers order in the 1912 ELHB disagree with each other. |
| Not consulted | TLH (1941) itself — only a copyright-restricted archive.org lending scan (`bwb_T4-APS-822`, `access-restricted-item: true`) was found; abandoned rather than circumvented. |

## Vespers

| Source | `luckylutheran/templates/vespers.yaml` |
|---|---|
| Primary sources | Same two predecessor editions as Matins (1912 ELHB, 1917/18 Common Service Book). |
| Status | ✅ Verified: opening versicles, Magnificat (fixed: "holpen" not "helped", confirmed via Luke 1:54 KJV + both period sources), Nunc Dimittis, Lord's Prayer, salutation, Benedicamus, Collect for Peace (fixed ending, confirmed against the Common Service Book's own text), Benediction (same fix as Matins). |
| | ✅ **Luther's Evening Prayer — now verified** against the same Triglotta Appendix I. The earlier flag was correct: fixed to "I pray Thee **to forgive** me all my sins" (was "that Thou wouldst forgive"). |
| | ⚠️ Unverified: Responsory, Kyrie line-count (same cross-office disagreement as Matins), the incense versicle ("prayer" singular vs. "prayers" plural — kept singular since it matches Psalm 141:2 KJV exactly). |
| Not consulted | TLH (1941) — same restricted-scan issue as Matins. |

## Compline

| Source | `luckylutheran/templates/compline.yaml` |
|---|---|
| Primary sources | No *Lutheran* Compline office found — confirmed absent from the 1868/1893 Church Book (General Council), the 1917/1918 Common Service Book, and the 1881 Missouri Synod Church Liturgy (all three checked directly). No American Lutheran hymnal had a Compline order until well into the 20th century (LBW 1978, LW 1982, ELW 2006 — all copyrighted; not used). A complete public-domain Compline office does exist outside the Lutheran books, and is now the source for the collects and benediction: the Order for Compline in *The Book of Common Prayer with the Additions and Deviations Proposed in 1928* (the English "Deposited Book"), archive.org `bookofcommonpray00chur_20`, unrestricted scan released **CC0**. |
| PD basis | The underlying prayers are the ancient Western monastic Compline (pre-1200s Latin origin), commonly rendered into English by many hands since the 19th century — the *tradition* is unambiguously PD, but for most pieces no single citable pre-1930 scan of this exact English wording has been located. |
| Status | ✅ Verified (shared with Vespers): Nunc Dimittis, Lord's Prayer, "Our help is in the name of the Lord / Who made heaven and earth" (matches the Common Service Book's own Confession-of-Sins preface verbatim). Fixed: "apple of the eye" not "apple of Thine eye" (confirmed via the Common Service Book's Trinity-season Gradual and KJV Psalm 17:8, both read "the eye"). |
| | ✅ **Verified — the Confession.** Transcribed word-for-word from *Church Liturgy for Evangelical Lutheran Congregations of the Unaltered Augsburg Confession* (Evangelical Lutheran Synod of Missouri, Concordia Publishing House, 1881), archive.org `churchliturgyfor00evan`, unrestricted scan; pre-1930 US publication, automatically PD. The text appears twice in that book, identically: as the general confession after the sermon in the Morning Service, and in the Communion of the Sick. This is the Saxon confession recorded in 16th-century Dresden practice (Sehling I:557) and the direct ancestor of TLH's p.15 wording — so the singular "I, a poor, miserable sinner" form is retained and now cited from the PD original rather than the copyrighted 1941 reprint. Fixes applied: restored two dropped clauses ("and justly deserved Thy punishment in time and eternity" / "but I am heartily sorry for them and greatly repent of them"), "by Thy boundless mercy" not "of Thy boundless mercy", "suffering" singular. The corporate CSB confession ("we poor sinners") was considered and **rejected** — it is from the Order of Public Confession before the chief service, not a Compline text, and its plural voice clashes with the office's singular register. |
| | ✅ **Verified — both collects and the closing benediction.** Transcribed word-for-word from the 1928 Deposited Book's Order for Compline (CC0 scan, above). Published 1928 → public domain in the US under the pre-1930 rule; the CC0 dedication on the scan also disposes of any residual UK Crown-copyright question, the same reasoning already applied to the KJV. The benediction was an **exact match** with no change needed. The collects took four small corrections: collect 1 now reads "this place" (was "this habitation"), "drive from it all the snares", "may Thy blessing"; collect 2 restores "silent hours", "this fleeting world" (was "of life"), and "repose upon" (was "rest in"). "Habitation" is itself PD-attested (St Dominic's Hymn-Book, 1885, `StDominicsHymnBook`) but its neighbouring clauses differ, so adopting the word alone would rebuild a hybrid; the 1928 recension was taken whole instead. Pronoun capitalization normalized to house style; no words changed. |
| | ⚠️ Unverified, minor and all flagged inline: the **opening versicle** — not a rights problem, but a conflation: the 1928 Compline reads "a quiet night and **a perfect end**", while "peace at the last" comes from Newman's evening prayer elsewhere in the same book. Both halves are PD; the join quotes neither. Changing four words would make it citable. The **Nunc Dimittis antiphon's opening** — 1928 reads "Preserve us, O Lord, while waking", ours "Guide us waking"; the second half matches verbatim. The **absolution** (the precatory *Indulgentiam*; the 1881 book's own absolution is the declarative ministerial form, deliberately not adopted — a recorded voice must not purport to absolve). The **bidding** before the confession (the 1881 bidding is sermon-specific and does not fit Compline's order). |
| **Recommendation** | No longer the blocker it was. Every substantial text in the office — confession, both collects, benediction, canticle — is now cited to a public-domain source. What remains is four short lines, none of which carries a copyright risk: each is either a conflation of PD texts or a recension variant. Compline can be published; the open items are polish, and two of them (versicle, antiphon) close with a handful of word changes if exact quotation is wanted. |

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
1. Compline is **substantially closed out**: the Confession is verified against the 1881 Missouri Synod Church Liturgy, and both collects plus the benediction against the 1928 Deposited Book's Order for Compline. Four short lines remain flagged (opening versicle, Nunc Dimittis antiphon opening, absolution, pre-confession bidding) — all are PD in substance; none blocks publication.
2. `small_catechism.yaml`'s 16 chief-part portions are **verified** against the 1921 Concordia Triglotta (six corrected). The **8 Christian Questions portions are a live copyright risk** and are the single highest-priority item on this list — see the Catechism section above. Everything else in the file is safe.
3. `collects.yaml`'s ten seasonal collects are **verified** against the 1917 Common Service Book's Propers (seven corrected, two of them materially — restored trinitarian conclusions). Remaining work here is additive, not corrective: per-Sunday collects, which the same source supplies.
4. Matins/Vespers: Luther's Morning and Evening Prayers are **verified** against the Triglotta (both earlier flags were correct and are fixed). Two ambiguous items remain (Responsory, Kyrie line-count) plus the incense versicle — sources disagree with each other; these need a judgment call or a tie-breaking source, not more searching.

Everything else — all of scripture, and the bulk of Matins/Vespers liturgy —
is checked word-for-word against confirmed-PD raw source text.
