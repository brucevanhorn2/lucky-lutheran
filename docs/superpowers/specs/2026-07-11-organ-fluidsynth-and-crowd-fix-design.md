# Organ via fluidsynth + crowd drift fix

*2026-07-11*

Two QA issues surfaced from the first crowd + official-readings render
(2026-02-18 Matins):

1. The pure-python organ bumper sounds like a toy — dry additive sines with
   no room and a thin registration.
2. The congregation crowd mix drifts into an echo chamber on long
   congregational passages (short responses sound right).

Both are addressed here. The changes are independent and small.

## Change 1 — Organ bumper via fluidsynth + soundfont

### Decision

Render tunes through **fluidsynth** driving a real pipe-organ **soundfont**,
replacing pure-python additive synthesis as the primary path. The synth stays
as a no-dependency fallback.

Rationale: the ceiling on additive synthesis is "convincing imitation"; a
recorded-pipe soundfont captures formants, chiff, and rank interaction that
synthesis cannot. fluidsynth is a *software* synth — no MIDI hardware, and it
is lighter than the interpreted-Python synth. The bumper renders once per tune
and is cached, so compute is a non-issue; it never touches the GPU.

### Soundfont: FluidR3_GM (MIT)

FluidR3_GM.sf2 is MIT-licensed, explicitly free for personal and commercial
use. General MIDI guarantees a Church Organ preset (program 19). This is the
publish-safe default for a public feed.

Rejected: **Jeux d'orgues** — sounds better but its legal notice prohibits
recording/reproduction without written permission (unsafe for a public feed).
**hedOrgan** — license unverified. Either could be A/B'd later with no code
change, since the soundfont path is a swappable file.

The `.sf2` is a machine-local asset (like the episodes and crowd WAVs) — **not
committed to git** (too large).

### Tune sources: YAML note-lists *and* MIDI files

The renderer accepts either:

- existing `data/tunes/*.yaml` note lists → converted to a Standard MIDI File
  by a **minimal pure-Python SMF writer** (no new Python dependency), or
- a dropped-in `.mid` file placed alongside the tunes.

MIDI-as-a-source is the "more songs" lever: public-domain hymn tunes exist as
free MIDIs (Cyber Hymnal, Hymnary.org) or can be exported from MuseScore, and
dropped straight in. Scope note: we are **not** building optical music
recognition; we only make the renderer consume MIDI. Licensing caveat for the
public feed: the tune is PD, but avoid modern copyrighted *arrangements* —
prefer plain melodies or pre-1929 / explicitly-PD settings.

### Rendering

`tune (YAML→SMF, or .mid) → fluidsynth -F out.wav <soundfont> → WAV`, using GM
program 19 (Church Organ) with fluidsynth's reverb enabled for the church
tail. A light additional reverb via ffmpeg is permitted if the tail is too dry.
Output is cached in `assets/music/rendered/` exactly as today.

### Fallback

When the `fluidsynth` binary or the soundfont is absent (local dev machine,
tests), fall back to the existing pure-python additive synth. This mirrors the
existing pattern where the crowd only engages where its reference WAVs exist,
and keeps offline tests green.

## Change 2 — Crowd drift fix (`audio.py:_mix_crowd`)

### Problem

`_mix_crowd` applies a single global `atempo` to stretch each voice's whole
clip to the median duration. That pins the endpoints but never re-syncs the
interior; over a long chunk the voices phase apart at clause breaks, producing
a round/echo. Short chunks stay locked because there is no room to drift.

### Fix

Split congregation text at phrase/clause boundaries into short units, render
and mix each unit separately, then concatenate the per-phrase mixes. Drift
resets at every phrase boundary instead of accumulating across a whole Creed,
so the "short sequences are perfect" quality holds across long passages. The
existing seeded per-voice delays/gains (resume-friendly raggedness) are
preserved within each phrase.

## Out of scope

- Optical music recognition / automated sheet-music-to-MIDI.
- Adding new seasonal tunes (the pipeline enables it; content comes later).
- A/B'ing a fancier cathedral soundfont (swappable later, no code change).

## Testing

- Offline: with fluidsynth absent, `music.render_tune` still returns a cached
  WAV via the fallback; existing tests stay green.
- The SMF writer is unit-testable in pure Python (bytes of a known tiny tune).
- Crowd: assert a long congregation chunk is split into multiple phrase mixes;
  manual QA listen on wintermute confirms the echo is gone.
