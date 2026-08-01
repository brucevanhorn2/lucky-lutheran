# lucky-lutheran

An automated daily-office podcast generator. Twice a day it builds a short
(~10 minute) personal worship service — **Matins** in the morning, **Vespers**
or **Compline** in the evening — after the historic Lutheran liturgy, with the
day's psalm, scripture reading, a rotating portion of Luther's Small
Catechism, and the collect of the day resolved from the church calendar.

## Copyright strategy (this is a public podcast — it matters)

Everything is built from **public-domain sources** so the podcast can be
published freely, with no licenses. See **[SOURCES.md](SOURCES.md)** for the
full citation list (title/year/URL/PD basis) and current verification status
of every piece of content — summary:

| Content | Source | Status |
|---|---|---|
| Liturgy (Matins, Vespers) | 1912 Evangelical Lutheran Hymn-Book + 1917/18 Common Service Book (verified PD predecessors of TLH 1941, which was not directly consulted) | mostly verified, a few items flagged `!! VERIFY` |
| Compline | ancient office components; no PD Lutheran predecessor office found. Confession verified from the 1881 Missouri Synod Church Liturgy | partly verified — versicle, collects, benediction still flagged; see SOURCES.md |
| Scripture | King James Version, local index built from Project Gutenberg eBook #10 (bible-api.com kept only as network fallback) | verified |
| Catechism core (commandments, Creed, sacraments) | Concordia Triglotta (CPH, 1921), English column — archive.org `concordiatriglot00unse` | verified word-for-word; 6 of 16 portions corrected |
| Catechism "Christian Questions" (8 portions) | none — not in the Triglotta; present wording matches the modern CPH translation | 🚨 **copyright risk — do not publish; see SOURCES.md** |
| Catechism Table of Duties / Words of Institution | resolved live from the local KJV, not hand-transcribed | verified |
| Collects | historic Common Service texts | unverified — transcribed from memory, not yet proofread |

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
python3 -m luckylutheran build --office compline --date 2026-12-24

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
currently hold *placeholder* voices bootstrapped from a sample clip (all
three sound alike). To mint the real cast, either record your own short
clips (update each speaker's `ref_text` in `tts.py` to the exact
transcript), or briefly run the VoiceDesign demo —
`qwen-tts-demo Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign --ip 0.0.0.0 --port
8000` — and regenerate from the `VOICE_CAST` descriptions, then switch back
to Base.

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
python3 -m luckylutheran feed --future              # QA feed (everything)

# Anywhere/anytime (needs no GPU): republish the public feed, which only
# includes episodes whose day has arrived (matins 05:00, vespers 17:00,
# compline 20:00 local):
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
