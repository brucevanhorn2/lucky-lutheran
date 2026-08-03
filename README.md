# lucky-lutheran

An automated daily-office podcast generator. Twice a day it builds a short
(~10 minute) personal worship service — **Matins** in the morning, **Vespers**
at evening, and **the Evening Suffrages** at the close of the day — after the
historic Lutheran liturgy, with the
day's psalm, scripture reading, a rotating portion of Luther's Small
Catechism, and the collect of the day resolved from the church calendar.

## What this is: a household office, not a service

This is daily prayer as a layman leads it in his own house — a father with
his family — not a recording of a church service and not a substitute for
one. That isn't a compromise forced by circumstance. It is what the Small
Catechism was written to enable, and the source text says so on every
chief part:

> **I. THE TEN COMMANDMENTS, as the Head of the Family Should Teach Them in
> a Simple Way to His Household.**

Not *as the pastor should teach*. The Commandments, the Creed, the Lord's
Prayer, Baptism, the Sacrament — every one carries that rubric, and the
Daily Prayers appendix is headed *"How the Head of the Family Should Teach
His Household to Bless Themselves Morning and Evening."* The modern church
tends to convene on Sunday; the catechism assumes the office continues at
home the rest of the week, led by whoever is there to lead it.

**What that changes in the text.** The boundary is Augsburg Confession XIV
(*rite vocatus*): the preaching office, administering the sacraments, and
absolving in the stead of Christ require a call from the church. A father
has a genuine vocation — Luther's three estates make the household a
divine station — but it is not the *Predigtamt*, and the language marks the
difference. Concretely:

- **No declarative absolution.** Where the older books print the minister's
  declaration, this project keeps the ancient prayer form instead — *"The
  almighty and merciful Lord grant us pardon, forgiveness, and remission of
  all our sins."* The 1881 Missouri Synod liturgy's own absolution — *"I,
  by virtue of my office, as a called and ordained servant of the Word...
  I forgive you all your sins"* — was deliberately **not** adopted, though
  it was right there in a verified public-domain source. A layman cannot
  say it, and neither can a recording.
- **The salutation and benediction stay.** *"The Lord be with you / And
  with thy spirit"* is a dialogue, not a reserved formula, and *"the
  communion of the Holy Ghost be with you all"* is 2 Corinthians 13:14
  spoken to four people who are actually in the room. Neither claims the
  office.
- **Nothing in the repo claims ordination.** Audited: no "called and
  ordained," no "by virtue of my office," no "in the stead and by the
  command," no "I forgive you."

**Why everything sounds old.** The Thou register began as a consequence of
using only public-domain sources — the pre-1930 books are what is free to
publish. It stayed because it turned out to be the right voice for this.
It is now a deliberate choice, not a workaround, and it is permanent. See
[SOURCES.md](SOURCES.md) for where every line comes from.

## Copyright strategy (this is a public podcast — it matters)

Everything is built from **public-domain sources** so the podcast can be
published freely, with no licenses. See **[SOURCES.md](SOURCES.md)** for the
full citation list (title/year/URL/PD basis) and current verification status
of every piece of content — summary:

| Content | Source | Status |
|---|---|---|
| Liturgy (Matins, Vespers) | 1912 Evangelical Lutheran Hymn-Book + 1917/18 Common Service Book (verified PD predecessors of TLH 1941, which was not directly consulted) | mostly verified, a few items flagged `!! VERIFY` |
| The Evening Suffrages | *Common Service Book* (1917), pp. 190-191 — a complete Lutheran brief evening office whose own rubric appoints it for the household. Night psalms cited to the Rule of St Benedict, ch. 18 | verified word-for-word; **replaced Compline**, which was half Anglican (retired to `docs/retired/`) |
| Scripture | King James Version, local index built from Project Gutenberg eBook #10 (bible-api.com kept only as network fallback) | verified |
| Daily lectionary & psalms | historic one-year lectionary + Table of Proper Psalms, Common Service Book (1917); weekdays read in course | verified — LSB dependency removed entirely |
| Catechism core (commandments, Creed, sacraments) | Concordia Triglotta (CPH, 1921), English column — archive.org `concordiatriglot00unse` | verified word-for-word; 6 of 16 portions corrected |
| Catechism — Lord's Prayer, Confession | Concordia Triglotta (CPH, 1921), English column | verified; four of six chief parts complete |
| Catechism Table of Duties / Words of Institution | resolved live from the local KJV, not hand-transcribed | verified |
| Collects | Propers of the Common Service Book (1917) — archive.org `commonserviceboo00phil` | verified word-for-word; 7 of 10 corrected |

**Do not** substitute LSB (Lutheran Service Book, © CPH), the ESV
(© Crossway), or the 1986/1991 CPH catechism translation without obtaining
licenses. The KJV/TLH "Thou" register is a feature, not a bug.

> **⚠️ VERIFY BEFORE PUBLISHING:** several files still carry a `!! VERIFY`
> comment marking text not yet checked against a raw primary source. See
> [SOURCES.md](SOURCES.md) for exactly which lines and what's needed to close
> each one out.

## Quick start

```bash
# What day is it in the church year?
python3 -m luckylutheran calendar

# Print today's Matins transcript
python3 -m luckylutheran script --office matins

# Build an episode (transcript + metadata; audio once a TTS engine is wired)
python3 -m luckylutheran build --office matins
python3 -m luckylutheran build --office evening-suffrages --date 2026-12-24

# Regenerate the podcast RSS feed from built episodes
python3 -m luckylutheran feed
```

Requires Python ≥ 3.10 and PyYAML. `ffmpeg` is required only for audio
stitching. Scripture is fetched once per passage and cached in
`.cache/scripture/`, so builds are offline-safe after warmup.

## How it works

```
date ──> churchyear.py   (Easter computus → season)
     ──> lectionary.py   (psalm + reading for the date/office)
     ──> collects.py     (collect of the day, by season)
     ──> catechism.py    (rotating Small Catechism portion)
              │
              ▼
     assemble.py         office template (templates/*.yaml) + slots
              │              → Episode: ordered Segments, each with a
              ▼                speaker (liturgist/congregation/lector/all)
     tts.py              one consistent voice per speaker (VOICE_CAST)
              │
              ▼
     audio.py            ffmpeg: stitch + deliberate silences + -16 LUFS → MP3
              │
              ▼
     feed.py             RSS 2.0 + iTunes tags → episodes/feed.xml
```

The **responsive structure is preserved**: versicles are tagged `liturgist`,
responses `congregation`, readings `lector`, and common texts (canticles,
Lord's Prayer) `all`. Each maps to a distinct TTS voice, which is what makes
it sound like a service instead of an audiobook.

## TTS: Qwen3-TTS served from wintermute

The engine uses [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)
(open-sourced January 2026). The intended split: **wintermute runs the GPU
server, any machine runs the pipeline** and talks to it over the LAN.

Four engines are available with `build --engine ...`:

| engine | what it talks to |
|---|---|
| `gradio` | the official `qwen-tts-demo` Gradio server on wintermute (**current setup**) |
| `remote` | this project's own `lucky serve` HTTP server on wintermute |
| `qwen3`  | Qwen3-TTS loaded locally (run the pipeline on wintermute itself) |
| `null`   | no audio; transcript/metadata only |

### Current setup: the official demo (`--engine gradio`)

On wintermute (192.168.1.51):

```bash
qwen-tts-demo Qwen/Qwen3-TTS-12Hz-1.7B-Base --ip 0.0.0.0 --port 8000
```

On this machine:

```bash
python3 -m luckylutheran build --office matins --engine gradio
# LUCKY_TTS_URL overrides the default http://192.168.1.51:8000
```

At startup the engine uploads each cast reference WAV from `assets/voices/`
once, makes a server-side voice prompt per cast member (`/save_prompt`), and
renders every segment with `/load_prompt_and_gen` — so voices stay identical
across episodes.

**Cast references:** `assets/voices/{liturgist,congregation,lector}.wav`
hold the **chosen cast**, designed and selected 2026-07-09 from the
candidates in `assets/voices/candidates/` (liturgist-b, congregation-c,
lector-a — recorded in `VOICE_CAST` in `tts.py`). These three WAVs are
committed deliberately: voice design is nondeterministic, so losing them
would permanently change how the podcast sounds. Do not regenerate them
casually.

`assets/voices/crowd/` holds seven designed parishioner voices, layered
slightly out of sync so congregational responses sound like a room rather
than one person. They are currently untracked.

To mint a *different* cast, run the VoiceDesign demo —
`qwen-tts-demo Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign --ip 0.0.0.0 --port
8000` — regenerate from the `VOICE_CAST` descriptions, audition the
candidates, then switch back to Base. If you record real human clips
instead, set each speaker's `ref_text` in `tts.py` to the exact transcript.

### Alternative: this project's own server (`--engine remote`)

```bash
# on wintermute
pip install -U qwen-tts soundfile
python3 -m luckylutheran serve          # http://0.0.0.0:8765
```

On first start it auto-designs the cast with the VoiceDesign model, then
loads CustomVoice with the cloned cast held in memory. Trusted-LAN only.

Without ffmpeg on the pipeline machine, episodes are stitched to WAV by a
pure-python fallback (no MP3/loudness normalization) — install ffmpeg for
podcast-ready output.

Prefer real human reference voices? Drop your own short clean WAVs into
`assets/voices/` and set each speaker's `ref_text` in `tts.py` to the exact
transcript. Env knobs: `LUCKY_QWEN_MODEL` (default
`Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`; the 0.6B variant is faster) and
`LUCKY_TTS_DEVICE` (default `cuda:0`).

## Batch-ahead workflow (the plan)

wintermute is only powered on occasionally (it heats the house), so episodes
are rendered in monthly sittings, QA-listened, and published on their
appointed days:

```bash
# On wintermute, once a month while it's on:
python3 -m luckylutheran batch --days 30            # matins+vespers per day
python3 -m luckylutheran batch --days 30 --offices all   # all three offices

# The congregation crowd is ~97% of all TTS calls — each phrase unit is
# synthesized once per voice. Narrow the roster to trade room-size for
# render time and intelligibility (the lead voice's share of the mix rises
# as the roster shrinks):
LUCKY_CROWD=parishioner-01,parishioner-02,parishioner-04 \
  python3 -m luckylutheran build --office vespers --engine gradio
LUCKY_CROWD=none python3 -m luckylutheran build ...   # congregation solo
python3 -m luckylutheran feed --future              # QA feed (everything)

# Anywhere/anytime (needs no GPU): republish the public feed, which only
# includes episodes whose day has arrived (matins 05:00, vespers 17:00,
# evening-suffrages 20:00 local):
python3 -m luckylutheran feed
```

`batch` is resumable: episodes that already exist are skipped, and one
failed episode doesn't stop the run. Publish by syncing `episodes/` (MP3s +
`feed.xml`) to any static host — S3, Cloudflare R2, GitHub Pages — with a
tiny daily `lucky feed` + upload job on any always-on machine. Set
`PODCAST["base_url"]` in `feed.py` first.

## Roadmap

- [ ] Proofread all `!! VERIFY` texts against printed TLH / Triglot
- [ ] On wintermute: `pip install qwen-tts`, run `lucky voices`, listen to the
      cast, tweak the `VOICE_CAST` descriptions until it sounds right
- [ ] Enter the official LCMS daily lectionary into
      `data/daily_lectionary.yaml` (currently a sequential fallback plan:
      Gospels in the morning, Acts/Epistles in the evening)
- [ ] Complete the Small Catechism portions (all commandments, Table of Duties)
- [ ] Per-Sunday collects (full historic propers) in `data/collects.yaml`
- [ ] **Music**: render public-domain hymn tunes (MusicXML/MIDI from
      hymnary.org / Open Hymnal) through a pipe-organ soundfont (FluidSynth)
      for the hymn slots and intro/outro beds; the `hymn` slot in the
      templates is already plumbed and currently skipped
- [ ] TTS text normalization (e.g., KJV's all-caps "LORD", psalm verse pacing)
- [ ] Long-psalm handling (truncate or split psalms > ~2 minutes)
- [ ] Publish pipeline: host episodes, submit feed to podcast directories
- [ ] v2 experiment: AI-sung hymns (local singing-voice synthesis)
