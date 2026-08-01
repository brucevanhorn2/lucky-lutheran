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

## Matins

| Source | `luckylutheran/templates/matins.yaml` |
|---|---|
| Primary sources | *Evangelical Lutheran Hymn-Book* (Concordia Publishing House, 1912), via Project Wittenberg (public-domain release, explicitly stated on the source page); *Common Service Book of the Lutheran Church* (General Synod/General Council/United Synod South, 1917/1918), via archive.org, unrestricted scan (`commonserviceboo1917phil` et al.) |
| PD basis | Both are US publications from before 1930 — automatically public domain under the rolling PD cutoff. |
| Status | ✅ Verified: opening versicles, invitatory, Venite, Te Deum, salutation, Lord's Prayer, Benedicamus, Collect for Grace, Benediction (fixed: "the Lord Jesus Christ" not "our Lord Jesus Christ", confirmed via 2 Cor. 13:14 KJV). |
| | ⚠️ Unverified: the Responsory ("But Thou, O Lord, have mercy upon us...") — the Vespers-order and Matins-order predecessor texts disagree with each other. The Kyrie line-count (single vs. doubled) — the Communion order and Vespers order in the 1912 ELHB disagree with each other. Luther's Morning Prayer's exact wording ("every evil" vs. "all evil") — flagged from a paraphrasing web fetch, not confirmed against raw source text. |
| Not consulted | TLH (1941) itself — only a copyright-restricted archive.org lending scan (`bwb_T4-APS-822`, `access-restricted-item: true`) was found; abandoned rather than circumvented. |

## Vespers

| Source | `luckylutheran/templates/vespers.yaml` |
|---|---|
| Primary sources | Same two predecessor editions as Matins (1912 ELHB, 1917/18 Common Service Book). |
| Status | ✅ Verified: opening versicles, Magnificat (fixed: "holpen" not "helped", confirmed via Luke 1:54 KJV + both period sources), Nunc Dimittis, Lord's Prayer, salutation, Benedicamus, Collect for Peace (fixed ending, confirmed against the Common Service Book's own text), Benediction (same fix as Matins). |
| | ⚠️ Unverified: Responsory, Kyrie line-count (same cross-office disagreement as Matins), the incense versicle ("prayer" singular vs. "prayers" plural — kept singular since it matches Psalm 141:2 KJV exactly), Luther's Evening Prayer's exact wording ("that Thou wouldst forgive" vs. "to forgive"). |
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
| Core portions (commandments, Creed, Baptism, Sacrament of the Altar) | 1921 Triglot Concordia translation tradition (concordant with bookofconcord.org's presentation of the Small Catechism). |
| Status | ⚠️ **Unverified** — the file's own header states these were "transcribed from memory," not yet checked against the raw Triglot Concordia text. This predates the current proofreading pass and is still open. |
| Table of Duties (14 entries) + "Christian Questions" Words of Institution | Not hand-transcribed — resolved live via `scripture.get_passage()`, the same local-KJV-first path used for lectionary readings. |
| Status | ✅ Verified by construction — no manual transcription risk, inherits the KJV verification above. |
| Remaining "Christian Questions with Their Answers" (non-Scripture portions) | 1921 Triglot Concordia tradition (bookofconcord.org), hand-transcribed. |
| Status | ⚠️ Unverified — same "transcribed from memory" caveat as the core portions. |
| Still missing | The Lord's Prayer and Confession/Office of the Keys chief parts. |

## Collects (seasonal, `luckylutheran/data/collects.yaml`)

| Status | ⚠️ **Unverified** — the file's own header states these were transcribed from memory of the historic Western collect texts (Common Service tradition, as printed in TLH) and have not yet been proofread against the Triglot Concordia or a period source. Not addressed in this pass; still open. |

## Summary: what's left before "proof of PD" is complete

1. Compline is **substantially closed out**: the Confession is verified against the 1881 Missouri Synod Church Liturgy, and both collects plus the benediction against the 1928 Deposited Book's Order for Compline. Four short lines remain flagged (opening versicle, Nunc Dimittis antiphon opening, absolution, pre-confession bidding) — all are PD in substance; none blocks publication.
2. `small_catechism.yaml`'s hand-transcribed portions (commandments, Creed, Baptism, Sacrament of the Altar, non-Scripture Christian Questions) — never checked against the Triglot Concordia.
3. `collects.yaml`'s seasonal collects — never checked against a period source.
4. Matins/Vespers' four flagged ambiguous items (Responsory, Kyrie line-count, incense versicle, Luther's Morning/Evening Prayer minor wording) — sources disagree; a judgment call or a tie-breaking source is needed, not just more searching.

Everything else — all of scripture, and the bulk of Matins/Vespers liturgy —
is checked word-for-word against confirmed-PD raw source text.
