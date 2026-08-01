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

## Daily Lectionary — ⚠️ THE ONE UNRESOLVED RIGHTS QUESTION

**Read this section before publishing publicly.** It is the only part of the
project sourced from a live commercial product, and the only sourcing claim
here that has not been tested. Everything else in this document is either
verified against a public-domain scan or explicitly flagged as unverified
text we control. This is different in kind: it is a question about someone
else's property, and it is unresolved.

| Source | `luckylutheran/data/daily_lectionary.yaml` |
|---|---|
| Origin | Transcribed from the **Lutheran Service Book** (Concordia Publishing House, 2006; pew edition, Kindle), Daily Lectionary, pp. 299–304. A current, in-print, commercially sold product. |
| Scale | 215 entries — 102 movable (keyed `ash+N`), 104 civil-date (`MM-DD`), 9 psalm blocks. This is the complete LSB daily reading table, not an excerpt. |
| Justification as written | The file header asserts, in one line: *"A lectionary is a list of citations (facts, not copyrightable text)."* No source or analysis is given. |

### Why that justification is not sufficient on its own

It is a real argument, and it may well win. It is not a settled one, and
three things cut against it:

1. **Feist protects selection and arrangement.** *Feist v. Rural Telephone*
   (499 U.S. 340, 1991) holds that facts are not copyrightable but that a
   compilation is protected where facts are "selected, coordinated, or
   arranged" with minimal originality. A lectionary is nothing *but* a
   selection and arrangement — which pericopes, paired how, on which days.
   Individual citations ("Genesis 1:1–19") are certainly facts. The *table*
   is the part at issue, and it is exactly the kind of thing Feist
   contemplates protecting.
2. **The industry treats lectionary selections as licensable property.** The
   Revised Common Lectionary's daily readings are copyrighted by the
   Consultation on Common Texts and Augsburg Fortress and are reproduced
   under permission notices. Whatever the theory, the practice is that
   these tables are licensed, not treated as free facts.
3. **CPH grants no allowance covering this.** CPH's Copyrights &
   Permissions page explicitly permits free noncommercial reproduction of
   *Luther's Small Catechism* (© 1986, with credit) and quotation of up to
   200 sentences from *Concordia: The Lutheran Confessions*. It says
   **nothing** about lectionary tables, reading schedules, or scripture
   reference lists. LSB's own notice is a blanket reservation — "no part of
   this publication may be reproduced… without prior written permission" —
   and CPH directs everything not specifically excepted to
   copyrights@cph.org. Liturgical material from LSB requires a paid license
   (LSBHymnLicense.Net or the CPH Liturgy License).

The counter-arguments are genuine and worth preserving: courts have refused
compilation protection to selections that are *systematic or functional*
rather than creative, and a continuous-reading plan that walks through
books of the Bible in canonical order is arguably a method rather than an
expression — and methods are excluded from copyright outright. Much of any
daily lectionary is also inherited from far older schemes. None of this has
been researched against the LSB table specifically.

### Why this matters more than it looks

It is structural, not cosmetic. The lectionary decides what scripture is
read **every single day**, so a defect here is not one bad line in one
office — it is present in every episode ever generated.

It is also inconsistent with the standard applied everywhere else in this
project. TLH 1941 was abandoned rather than use a copyright-restricted
scan. A Compline confession was rejected for being merely uncitable. The
Christian Questions are held back over a *register* mismatch suggesting a
modern source. Against that, "facts, not copyrightable text" is a much
lower bar, applied to the one artifact taken directly from a book that is
on sale today.

### Options, in order of increasing cost

1. **Ask CPH.** copyrights@cph.org, 1-800-325-3040. A written yes ends the
   question permanently and costs one email. A written no is also valuable
   — it is far better to know before publishing than after.
2. **Research the specific claim.** Determine whether the LSB daily
   lectionary's selection is substantially inherited from an older public
   scheme. If it is, the originality argument weakens considerably in our
   favor.
3. **Substitute a public-domain lectionary.** Two candidates, both already
   trusted sources in this project: the **historic one-year lectionary**
   (the classic Western pericope set, in use for centuries and unambiguously
   PD), and the **1917/18 Common Service Book's own tables** — already the
   verified source for Matins and Vespers. This costs a re-transcription and
   changes what gets read, but removes the question entirely.

### Status

🚨 **OPEN.** No decision has been made and no permission has been sought.
The podcast has not published publicly, so nothing has been distributed
under the current arrangement. Recorded here — 2026-08-01 — so that this
does not quietly persist as a settled matter simply because it was written
down once in a file header.

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
| **"Christian Questions with Their Answers" (8 hand-transcribed portions)** | 🚨 **COPYRIGHT RISK — do not publish as they stand.** Two separate problems. First, the Triglotta **does not contain the Christian Questions at all**: it discusses them in its historical introduction (p. 88 — first published 1549, attributed to Luther in a 1551 edition) but prints no text, running straight from the Sacrament of the Altar into Appendix I. The file's former claim that this section followed the Triglotta was simply wrong. Second, the wording here is modern second person ("Do you believe that you are a sinner?"), which is the register of the **current CPH translation** — the very text this project refuses to use. Any pre-1930 English printing would read "Dost thou believe…", matching the Thou register used everywhere else in the repo; that mismatch is the tell that this was recalled from a modern copyrighted source. Searched without success: the Triglotta, the 1881 Missouri Synod Church Liturgy, the 1912 ELHB (and its 1905/1909 printings), Crull's 1879/1884 hymn books, and five pre-1930 English Small Catechism editions on archive.org. **Fix:** drop these eight from the rotation, or retranslate from the German the Triglotta does print. |
| Still missing | The Lord's Prayer and Confession/Office of the Keys chief parts. |

## Collects (seasonal, `luckylutheran/data/collects.yaml`)

| Status | ⚠️ **Unverified** — the file's own header states these were transcribed from memory of the historic Western collect texts (Common Service tradition, as printed in TLH) and have not yet been proofread against the Triglot Concordia or a period source. Not addressed in this pass; still open. |

## Summary: what's left before "proof of PD" is complete

0. 🚨 **The daily lectionary** — the only unresolved *rights* question in the project, and the only text taken from a live commercial product. Everything below is about text we control; this one is about someone else's property. See the Daily Lectionary section above. **Do not publish publicly without addressing it.** Cheapest resolution is one email to copyrights@cph.org.
1. Compline is **substantially closed out**: the Confession is verified against the 1881 Missouri Synod Church Liturgy, and both collects plus the benediction against the 1928 Deposited Book's Order for Compline. Four short lines remain flagged (opening versicle, Nunc Dimittis antiphon opening, absolution, pre-confession bidding) — all are PD in substance; none blocks publication.
2. `small_catechism.yaml`'s 16 chief-part portions are **verified** against the 1921 Concordia Triglotta (six corrected). The **8 Christian Questions portions are a live copyright risk** and are the single highest-priority item on this list — see the Catechism section above. Everything else in the file is safe.
3. `collects.yaml`'s seasonal collects — never checked against a period source. Now the largest wholly unverified body of text in the project.
4. Matins/Vespers: Luther's Morning and Evening Prayers are **verified** against the Triglotta (both earlier flags were correct and are fixed). Two ambiguous items remain (Responsory, Kyrie line-count) plus the incense versicle — sources disagree with each other; these need a judgment call or a tie-breaking source, not more searching.

Everything else — all of scripture, and the bulk of Matins/Vespers liturgy —
is checked word-for-word against confirmed-PD raw source text.
