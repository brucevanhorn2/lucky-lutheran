# Organ via fluidsynth + Crowd Drift Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render the organ bumper through fluidsynth + a real pipe-organ soundfont (falling back to the pure-python synth), and stop the congregation crowd from drifting into an echo chamber on long passages.

**Architecture:** `music.py` gains a fluidsynth path: tune YAML → a pure-Python Standard MIDI File → `fluidsynth` + soundfont → WAV; a dropped-in `.mid` bypasses the YAML step (the "more songs" lever). When fluidsynth or the soundfont is absent, the existing additive synth renders instead, so the local box and offline tests are unaffected. `audio.py` splits congregation text into short phrase units, mixes each unit, and concatenates — so crowd drift resets every few words instead of accumulating.

**Tech Stack:** Python 3.14 stdlib (`struct`, `subprocess`, `shutil`, `wave`), PyYAML, the `fluidsynth` binary + `FluidR3_GM.sf2` (wintermute only), ffmpeg (already required for mixing).

## Global Constraints

- Python 3.14, stdlib-first; the only Python dependency is PyYAML. Do **not** add a Python MIDI library — write the SMF bytes by hand.
- New runtime requirements (`fluidsynth` binary, `.sf2` soundfont) live only on wintermute and must be **optional**: absence triggers the pure-python fallback, never an error.
- The soundfont is a machine-local asset — never committed to git.
- Soundfont default path: `/usr/share/sounds/sf2/FluidR3_GM.sf2` (the `fluid-soundfont-gm` apt package), overridable via the `LUCKY_SOUNDFONT` environment variable.
- GM "Church Organ" is program `19` (0-indexed) — MIDI program-change byte `0xC0 0x13`.
- This repo has **no pytest**. Tests are plain functions in `tests/test_basics.py`, run by importing and calling them (see each task's run command).
- Preserve the existing resume-friendly caching and the seeded (text-hashed) crowd raggedness.

---

### Task 1: Pure-Python Standard MIDI File writer

Adds MIDI-note conversion and a minimal SMF writer to `music.py`. Pure Python, fully testable offline — no fluidsynth needed.

**Files:**
- Modify: `luckylutheran/music.py` (add helpers near the existing `_frequency`, `_NOTE_INDEX`)
- Test: `tests/test_basics.py` (append two test functions)

**Interfaces:**
- Consumes: the existing `_NOTE_INDEX` dict and tune dicts of shape `{"tempo_qpm": int, "notes": [[pitch_str, beats_number], ...]}`.
- Produces:
  - `_midi_note(pitch: str) -> int` — e.g. `_midi_note("A4") == 69`
  - `_write_midi(tune: dict, path: Path) -> Path` — writes a valid format-0 SMF, returns `path`
  - module constants `TICKS_PER_QUARTER = 480`, `CHURCH_ORGAN_PROGRAM = 19`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_basics.py`:

```python
def test_midi_note_numbers():
    from luckylutheran.music import _midi_note
    assert _midi_note("A4") == 69   # concert A
    assert _midi_note("C4") == 60   # middle C
    assert _midi_note("G4") == 67
    assert _midi_note("F#4") == 66
    assert _midi_note("Bb3") == 58


def test_write_midi_bytes(tmp_path=None):
    import tempfile
    from pathlib import Path
    from luckylutheran.music import _write_midi
    tune = {"tempo_qpm": 120, "notes": [["C4", 1], ["E4", 1], ["G4", 2]]}
    out = Path(tempfile.mkdtemp()) / "t.mid"
    _write_midi(tune, out)
    data = out.read_bytes()
    assert data[:4] == b"MThd"                      # header chunk
    assert data[8:10] == b"\x00\x00"                # format 0
    assert data[10:12] == b"\x00\x01"               # one track
    assert b"MTrk" in data                          # track chunk present
    assert bytes([0xC0, 0x13]) in data              # program change: church organ
    assert data.endswith(bytes([0xFF, 0x2F, 0x00])) # end-of-track meta
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -c "import tests.test_basics as t; t.test_midi_note_numbers()"`
Expected: FAIL — `ImportError: cannot import name '_midi_note'`

- [ ] **Step 3: Implement the helpers**

In `luckylutheran/music.py`, after the `_NOTE_INDEX` line (currently line 31), add:

```python
TICKS_PER_QUARTER = 480
CHURCH_ORGAN_PROGRAM = 19   # General MIDI program (0-indexed): "Church Organ"


def _midi_note(pitch: str) -> int:
    """'F#4' / 'Bb3' / 'G4' -> MIDI note number (A4 = 69)."""
    name, octave = pitch[:-1], int(pitch[-1])
    semitone = _NOTE_INDEX[name[0].upper()]
    semitone += name.count("#") - name.count("b")
    return 12 * (octave + 1) + semitone


def _vlq(value: int) -> bytes:
    """MIDI variable-length quantity (big-endian, 7 bits per byte)."""
    out = bytearray([value & 0x7F])
    value >>= 7
    while value:
        out.insert(0, (value & 0x7F) | 0x80)
        value >>= 7
    return bytes(out)


def _write_midi(tune: dict, path: Path) -> Path:
    """Render a tune's note list to a format-0 Standard MIDI File on one
    channel set to Church Organ. Notes are legato (each release meets the
    next attack), which suits a sustaining pipe organ."""
    tempo = round(60_000_000 / tune["tempo_qpm"])  # microseconds per quarter
    track = bytearray()
    track += _vlq(0) + bytes([0xFF, 0x51, 0x03]) + tempo.to_bytes(3, "big")
    track += _vlq(0) + bytes([0xC0, CHURCH_ORGAN_PROGRAM])
    for pitch, beats in tune["notes"]:
        note = _midi_note(pitch)
        ticks = round(beats * TICKS_PER_QUARTER)
        track += _vlq(0) + bytes([0x90, note, 80])      # note on
        track += _vlq(ticks) + bytes([0x80, note, 0])   # note off after duration
    track += _vlq(0) + bytes([0xFF, 0x2F, 0x00])        # end of track

    header = (b"MThd" + (6).to_bytes(4, "big") + (0).to_bytes(2, "big")
              + (1).to_bytes(2, "big") + TICKS_PER_QUARTER.to_bytes(2, "big"))
    chunk = b"MTrk" + len(track).to_bytes(4, "big") + bytes(track)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + chunk)
    return path
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -c "import tests.test_basics as t; t.test_midi_note_numbers(); t.test_write_midi_bytes(); print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add luckylutheran/music.py tests/test_basics.py
git commit -m "music: pure-python Standard MIDI File writer"
```

---

### Task 2: fluidsynth render path with additive fallback

Routes `render_tune` through fluidsynth + soundfont when both are present, generating (or reusing a dropped-in) MIDI; otherwise falls back to the existing additive synth. Testable offline because this machine has no fluidsynth — the fallback path runs, and MIDI generation is exercised directly.

**Files:**
- Modify: `luckylutheran/music.py` (add imports; add `TUNES_DIR`, `_soundfont`, `_tune_midi`, `_render_fluidsynth`; refactor `render_tune`; rename current synth body to `_render_additive`; extend `available_tunes`)
- Test: `tests/test_basics.py` (append one test function)

**Interfaces:**
- Consumes: `_write_midi`, `TICKS_PER_QUARTER`, `RENDER_DIR`, `SAMPLE_RATE`, and the existing additive-synth code (`_note`, `_frequency`, `PARTIALS`, etc.).
- Produces:
  - `render_tune(name: str, force: bool = False) -> Path` — unchanged signature, now fluidsynth-first
  - `_soundfont() -> Path | None`
  - `_tune_midi(name: str) -> Path` — dropped-in `data/tunes/{name}.mid` if present, else generated to `RENDER_DIR/{name}.mid`
  - `_render_additive(name: str, out: Path) -> Path`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_basics.py`:

```python
def test_render_tune_offline_and_midi_generation():
    from luckylutheran import music
    # No fluidsynth on the dev box -> additive fallback still yields a WAV.
    out = music.render_tune("old-hundredth", force=True)
    assert out.exists() and out.suffix == ".wav"
    # MIDI generation from the YAML works with no fluidsynth present.
    midi = music._tune_midi("old-hundredth")
    assert midi.suffix == ".mid"
    assert midi.read_bytes()[:4] == b"MThd"
    # Soundfont discovery honors the env override and missing files.
    import os
    os.environ["LUCKY_SOUNDFONT"] = "/nonexistent/x.sf2"
    assert music._soundfont() is None
    os.environ.pop("LUCKY_SOUNDFONT")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -c "import tests.test_basics as t; t.test_render_tune_offline_and_midi_generation()"`
Expected: FAIL — `AttributeError: module 'luckylutheran.music' has no attribute '_tune_midi'`

- [ ] **Step 3: Add imports and the tunes-dir constant**

In `luckylutheran/music.py`, change the import block (currently lines 12-18) to add `os`, `shutil`, `subprocess`:

```python
import math
import os
import shutil
import struct
import subprocess
import wave
from importlib import resources
from pathlib import Path
```

Immediately after the `RENDER_DIR = ...` / `SAMPLE_RATE = 44100` lines, add:

```python
TUNES_DIR = Path(__file__).resolve().parent / "data" / "tunes"
DEFAULT_SOUNDFONT = Path("/usr/share/sounds/sf2/FluidR3_GM.sf2")
```

- [ ] **Step 4: Add soundfont discovery, MIDI resolution, and the fluidsynth renderer**

Add these functions to `luckylutheran/music.py` (place them just above the existing `render_tune`):

```python
def _soundfont() -> Path | None:
    """The organ soundfont to use, or None if none is available.

    Honors $LUCKY_SOUNDFONT, else the apt package's standard path. Returns
    None when the file is missing so callers fall back to the synth."""
    override = os.environ.get("LUCKY_SOUNDFONT")
    candidate = Path(override) if override else DEFAULT_SOUNDFONT
    return candidate if candidate.is_file() else None


def _tune_midi(name: str) -> Path:
    """A MIDI file for the tune: a hand-dropped data/tunes/{name}.mid if one
    exists (any public-domain hymn MIDI works), else one generated from the
    YAML note list into the render cache."""
    dropped = TUNES_DIR / f"{name}.mid"
    if dropped.is_file():
        return dropped
    tune = yaml.safe_load((TUNES_DIR / f"{name}.yaml").read_text(encoding="utf-8"))
    return _write_midi(tune, RENDER_DIR / f"{name}.mid")


def _render_fluidsynth(name: str, out: Path, soundfont: Path) -> Path:
    """Render the tune to a WAV with fluidsynth, with a churchy reverb tail."""
    midi = _tune_midi(name)
    subprocess.run(
        ["fluidsynth", "-ni", "-g", "0.8", "-r", str(SAMPLE_RATE),
         "-o", "synth.reverb.room-size=0.9",
         "-o", "synth.reverb.level=0.9",
         "-o", "synth.reverb.width=0.8",
         "-F", str(out), str(soundfont), str(midi)],
        check=True, capture_output=True)
    return out
```

- [ ] **Step 5: Refactor `render_tune` and rename the synth body to `_render_additive`**

Replace the current `render_tune` function body (currently lines 54-78) with a dispatcher, and move the additive synthesis into `_render_additive`:

```python
def render_tune(name: str, force: bool = False) -> Path:
    """Render a tune to a cached WAV; return the path.

    Uses fluidsynth + a pipe-organ soundfont when both are present (a real
    recorded organ), and falls back to the pure-python additive synth
    otherwise (e.g. the dev box), so builds never hard-depend on fluidsynth."""
    out = RENDER_DIR / f"{name}.wav"
    if out.exists() and not force:
        return out
    RENDER_DIR.mkdir(parents=True, exist_ok=True)

    soundfont = _soundfont()
    if shutil.which("fluidsynth") and soundfont:
        return _render_fluidsynth(name, out, soundfont)
    return _render_additive(name, out)


def _render_additive(name: str, out: Path) -> Path:
    """The pure-python pipe-organ synth (no external tools)."""
    ref = resources.files("luckylutheran") / "data" / "tunes" / f"{name}.yaml"
    tune = yaml.safe_load(ref.read_text(encoding="utf-8"))
    spb = 60.0 / tune["tempo_qpm"]  # seconds per quarter beat

    samples: list[float] = []
    for pitch, beats in tune["notes"]:
        samples.extend(_note(_frequency(pitch), beats * spb))
    samples.extend(_note(None, RELEASE * 2))  # let the last release ring out

    peak = max(abs(s) for s in samples)
    scale = 0.55 / peak if peak else 0.0
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(b"".join(
            struct.pack("<h", int(s * scale * 32767)) for s in samples))
    return out
```

- [ ] **Step 6: Let `available_tunes` see dropped-in MIDI files**

Replace the body of `available_tunes` (currently lines 43-45) with:

```python
def available_tunes() -> list[str]:
    """Tune names renderable today: YAML note-lists and any dropped-in
    .mid files in data/tunes/."""
    names = {p.stem for p in TUNES_DIR.glob("*.yaml")}
    names |= {p.stem for p in TUNES_DIR.glob("*.mid")}
    return sorted(names)
```

- [ ] **Step 7: Run the new test and the full suite**

Run: `python3 -c "import tests.test_basics as t; t.test_render_tune_offline_and_midi_generation(); print('ok')"`
Expected: `ok`

Run the whole suite to confirm nothing regressed:
```bash
python3 -c "import tests.test_basics as t; [getattr(t,n)() for n in dir(t) if n.startswith('test_')]; print('all pass')"
```
Expected: `all pass`

- [ ] **Step 8: Commit**

```bash
git add luckylutheran/music.py tests/test_basics.py
git commit -m "music: fluidsynth+soundfont organ path with additive fallback and MIDI tune source"
```

---

### Task 3: Fix crowd drift by mixing phrase-level units

Splits a congregation chunk into short phrase units, mixes each unit with the existing crowd algorithm, and concatenates them — so drift resets per phrase. The current whole-chunk mixer becomes the per-unit mixer.

**Files:**
- Modify: `luckylutheran/audio.py` (add `_phrase_units`, `_concat_wavs`; rename `_render_crowd_chunk` → `_render_crowd_unit`; add a new `_render_crowd_chunk` splitter wrapper)
- Test: `tests/test_basics.py` (append one test function)

**Interfaces:**
- Consumes: the existing `_mix_crowd(parts, chunk, out_path)` and `_render_crowd_unit` (the renamed old body). The caller in `render_episode` (line 76) still calls `_render_crowd_chunk(engine, chunk, crowd, wav)` unchanged.
- Produces:
  - `_phrase_units(text: str, max_chars: int = 60) -> list[str]`
  - `_concat_wavs(parts: list[Path], out_path: Path) -> Path`
  - `_render_crowd_chunk(engine, chunk, crowd, out_path) -> Path | None` (new splitter wrapper)
  - `_render_crowd_unit(engine, chunk, crowd, out_path) -> Path | None` (renamed old body)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_basics.py`:

```python
def test_phrase_units_bounds_drift():
    from luckylutheran.audio import _phrase_units
    # A short response stays a single unit.
    assert _phrase_units("Amen.") == ["Amen."]
    # A long, comma-heavy creed line splits into several short units...
    creed = ("I believe in God, the Father Almighty, Maker of heaven and "
             "earth; and in Jesus Christ, His only Son, our Lord.")
    units = _phrase_units(creed)
    assert len(units) >= 3
    assert all(len(u) <= 60 for u in units)
    # ...and no words are lost or reordered.
    assert " ".join(units).split() == creed.split()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -c "import tests.test_basics as t; t.test_phrase_units_bounds_drift()"`
Expected: FAIL — `ImportError: cannot import name '_phrase_units'`

- [ ] **Step 3: Add `_phrase_units` and `_concat_wavs`**

In `luckylutheran/audio.py`, add these two functions just above `_render_crowd_chunk` (currently line 100):

```python
def _phrase_units(text: str, max_chars: int = 60) -> list[str]:
    """Break congregation text into short phrase units so the crowd mix
    re-syncs frequently. Splits at clause/sentence punctuation, then breaks
    any still-long piece on word boundaries. Every word is preserved in
    order."""
    import re
    units: list[str] = []
    for piece in re.split(r"(?<=[,.;:!?])\s+", text.strip()):
        if len(piece) <= max_chars:
            if piece:
                units.append(piece)
            continue
        current = ""
        for word in piece.split():
            if current and len(current) + 1 + len(word) > max_chars:
                units.append(current)
                current = word
            else:
                current = f"{current} {word}".strip()
        if current:
            units.append(current)
    return units


def _concat_wavs(parts: list[Path], out_path: Path) -> Path:
    """Concatenate WAV parts in order into one WAV via ffmpeg's concat
    demuxer (re-encoding to a common PCM format to be safe)."""
    listfile = out_path.parent / f"{out_path.stem}-concat.txt"
    listfile.write_text(
        "".join(f"file '{p.resolve()}'\n" for p in parts), encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
         "-c:a", "pcm_s16le", str(out_path)],
        check=True, capture_output=True)
    return out_path
```

- [ ] **Step 4: Rename the old mixer body and add the splitter wrapper**

Rename the existing `_render_crowd_chunk` (currently line 100) to `_render_crowd_unit` — change only its `def` line:

```python
def _render_crowd_unit(engine, chunk: str, crowd: list[str],
                       out_path: Path) -> Path | None:
```

Then add the new splitter wrapper directly above it:

```python
def _render_crowd_chunk(engine, chunk: str, crowd: list[str],
                        out_path: Path) -> Path | None:
    """Render a congregation chunk as several short phrase units, mixing each
    unit's voices independently and concatenating them. Mixing per phrase
    keeps the crowd tight: onset drift resets at every phrase boundary instead
    of accumulating across a long passage into an echo chamber.

    Per-unit mixes are cached beside the output, so retries are cheap."""
    units = _phrase_units(chunk)
    if len(units) <= 1:
        return _render_crowd_unit(engine, chunk, crowd, out_path)

    unit_dir = out_path.parent / "crowd-units"
    unit_dir.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []
    for k, unit in enumerate(units):
        part = unit_dir / f"{out_path.stem}-u{k:02d}.wav"
        if not (part.exists() and part.stat().st_size > 44):
            if _render_crowd_unit(engine, unit, crowd, part) is None:
                return None
        parts.append(part)
    return _concat_wavs(parts, out_path)
```

- [ ] **Step 5: Run the test and the full suite**

Run: `python3 -c "import tests.test_basics as t; t.test_phrase_units_bounds_drift(); print('ok')"`
Expected: `ok`

Run the whole suite:
```bash
python3 -c "import tests.test_basics as t; [getattr(t,n)() for n in dir(t) if n.startswith('test_')]; print('all pass')"
```
Expected: `all pass`

- [ ] **Step 6: Commit**

```bash
git add luckylutheran/audio.py tests/test_basics.py
git commit -m "audio: mix crowd per phrase unit to stop long-passage drift"
```

---

## Post-implementation QA (on wintermute, manual)

These need the GPU box + fluidsynth and are not automated:

1. **Organ:** `python3 -m luckylutheran music --tune old-hundredth --force` — listen to `assets/music/rendered/old-hundredth.wav`. Should sound like a church organ in a room, not a toy. (Re-render is forced because the cached toy WAV would otherwise be returned.)
2. **Full episode:** rebuild `2026-02-18` matins and confirm the bumper and the crowd on long congregational passages (the Creed) both sound right — the echo chamber should be gone.
3. If the organ tail is too dry or too wet, adjust the three `synth.reverb.*` values in `_render_fluidsynth`.

## Self-review notes

- **Spec coverage:** fluidsynth path (Task 2) ✓; FluidR3_GM default + env override (Task 2, `_soundfont`) ✓; YAML→SMF writer, no Python MIDI dep (Task 1) ✓; MIDI-file tune source (Task 2, `_tune_midi`) ✓; additive fallback (Task 2) ✓; soundfont not committed (asset path, nothing added to git) ✓; crowd phrase-split + concat (Task 3) ✓; seeded raggedness preserved (untouched `_mix_crowd`) ✓.
- **Out of scope, honored:** no OMR, no new tunes, no soundfont A/B — all swappable later without code change.
