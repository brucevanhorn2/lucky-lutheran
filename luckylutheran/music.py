"""Bumper music: public-domain hymn tunes on a pure-python pipe organ.

Tunes are note lists in data/tunes/*.yaml. Synthesis is additive — an organ
pipe's tone really is a stack of near-pure harmonics, so summed sines with a
gentle attack/release and a slightly detuned chorus layer land surprisingly
close to a small principal registration. No soundfonts, no external synth;
rendered WAVs are cached in assets/music/rendered/.
"""

from __future__ import annotations

import math
import struct
import wave
from importlib import resources
from pathlib import Path

import yaml

RENDER_DIR = Path(__file__).resolve().parent.parent / "assets" / "music" / "rendered"
SAMPLE_RATE = 44100

# Principal-chorus registration: (harmonic multiple, amplitude).
# 8' fundamental, 4' octave, 2 2/3' twelfth, 2' fifteenth, faint mixture.
PARTIALS = [(1, 1.00), (2, 0.42), (3, 0.20), (4, 0.11), (6, 0.045)]
DETUNE = 1.0035          # second rank, slightly sharp — the organ's shimmer
DETUNE_LEVEL = 0.35
ATTACK, RELEASE = 0.030, 0.10   # pipe speech, seconds
ARTICULATION_GAP = 0.02          # silence between repeated notes

_NOTE_INDEX = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

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


def _frequency(pitch: str) -> float:
    """'F#4' / 'Bb3' / 'G4' -> Hz (equal temperament, A4 = 440)."""
    name, octave = pitch[:-1], int(pitch[-1])
    semitone = _NOTE_INDEX[name[0].upper()]
    semitone += name.count("#") - name.count("b")
    midi = 12 * (octave + 1) + semitone
    return 440.0 * 2 ** ((midi - 69) / 12)


def available_tunes() -> list[str]:
    ref = resources.files("luckylutheran") / "data" / "tunes"
    return sorted(p.name[:-5] for p in ref.iterdir() if p.name.endswith(".yaml"))


def tune_for(season: str) -> str:
    """Season -> tune name. One tune for now; grow this map as tunes are
    added (e.g. Advent -> wachet-auf, Christmas -> vom-himmel-hoch)."""
    return "old-hundredth"


def render_tune(name: str, force: bool = False) -> Path:
    """Synthesize a tune to a cached WAV; return the path."""
    out = RENDER_DIR / f"{name}.wav"
    if out.exists() and not force:
        return out

    ref = resources.files("luckylutheran") / "data" / "tunes" / f"{name}.yaml"
    tune = yaml.safe_load(ref.read_text(encoding="utf-8"))
    spb = 60.0 / tune["tempo_qpm"]  # seconds per quarter beat

    samples: list[float] = []
    for pitch, beats in tune["notes"]:
        samples.extend(_note(_frequency(pitch), beats * spb))
    samples.extend(_note(None, RELEASE * 2))  # let the last release ring out

    peak = max(abs(s) for s in samples)
    scale = 0.55 / peak if peak else 0.0
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(b"".join(
            struct.pack("<h", int(s * scale * 32767)) for s in samples))
    return out


def _note(freq: float | None, duration: float) -> list[float]:
    """One note (or rest if freq is None) as float samples in [-1, 1]."""
    n = int(duration * SAMPLE_RATE)
    if freq is None:
        return [0.0] * n

    sounding = max(n - int(ARTICULATION_GAP * SAMPLE_RATE), 1)
    attack_n = min(int(ATTACK * SAMPLE_RATE), sounding)
    release_n = min(int(RELEASE * SAMPLE_RATE), sounding)
    two_pi_t = 2 * math.pi / SAMPLE_RATE

    out = [0.0] * n
    for i in range(sounding):
        t = i * two_pi_t
        v = sum(a * math.sin(h * freq * t) for h, a in PARTIALS)
        v += DETUNE_LEVEL * math.sin(freq * DETUNE * t)
        if i < attack_n:
            v *= i / attack_n
        remaining = sounding - i
        if remaining < release_n:
            v *= remaining / release_n
        out[i] = v
    return out
