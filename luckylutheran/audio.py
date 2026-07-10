"""Audio assembly: stitch per-segment WAVs into one podcast-ready MP3.

Requires ffmpeg on PATH. Renders each segment via the TTS engine, inserts
the template's deliberate silences between sections, loudness-normalizes to
the podcast standard (-16 LUFS), and writes <slug>.mp3.

Music beds (organ hymn instrumentals in assets/music/) are a planned v2:
they will be mixed under the greeting/benediction and fill the hymn slots.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from luckylutheran.assemble import Episode
from luckylutheran.tts import TTSEngine


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


# TTS models slow down and degrade on very long inputs; render long texts
# (full psalms, chapter readings) as sentence-boundary chunks of at most
# this many characters, with a short breath between chunks.
MAX_CHUNK_CHARS = 400
CHUNK_PAUSE = 0.65


def _chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    import re
    sentences = re.split(r"(?<=[.!?;])\s+", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def render_episode(episode: Episode, engine: TTSEngine, out_dir: Path) -> Path | None:
    """Render all segments and stitch them. Returns the MP3 path, or None in
    script-only mode (engine produced no audio).

    Resumable: chunks whose WAV already exists are skipped, so a failed or
    interrupted build only re-renders what's missing."""
    work = out_dir / "segments" / episode.slug
    work.mkdir(parents=True, exist_ok=True)

    rendered: list[tuple[Path, float]] = []
    for i, seg in enumerate(episode.segments):
        chunks = _chunk_text(seg.text)
        for j, chunk in enumerate(chunks):
            suffix = "" if len(chunks) == 1 else f"-{j:02d}"
            wav = work / f"{i:03d}{suffix}-{seg.section_id}-{seg.speaker}.wav"
            if wav.exists() and wav.stat().st_size > 44:
                result: Path | None = wav  # resume: already rendered
            else:
                result = engine.synthesize(chunk, seg.speaker, wav)
            if result is not None:
                last = j == len(chunks) - 1
                rendered.append((result, seg.pause_after if last else CHUNK_PAUSE))

    if not rendered:
        return None
    if not ffmpeg_available():
        print("ffmpeg not found — stitching to WAV with the pure-python "
              "fallback (install ffmpeg for MP3 + loudness normalization)")
        return _stitch_wave(rendered, out_dir / f"{episode.slug}.wav")

    return _stitch(rendered, out_dir / f"{episode.slug}.mp3")


def _stitch(rendered: list[tuple[Path, float]], out_path: Path) -> Path:
    """Concatenate WAVs with per-segment trailing silence, normalize, encode."""
    inputs: list[str] = []
    filters: list[str] = []
    for i, (wav, pause) in enumerate(rendered):
        inputs += ["-i", str(wav)]
        # Per clip: resample to a common rate, fade the head (30 ms) and
        # tail (80 ms, via the areverse trick) so joins never click or cut
        # off abruptly, then pad with the segment's trailing silence.
        filters.append(
            f"[{i}:a]aresample=44100,aformat=channel_layouts=mono,"
            f"afade=t=in:d=0.03,areverse,afade=t=in:d=0.08,areverse,"
            f"apad=pad_dur={pause}[s{i}]"
        )
    concat = "".join(f"[s{i}]" for i in range(len(rendered)))
    filters.append(
        f"{concat}concat=n={len(rendered)}:v=0:a=1,"
        f"loudnorm=I=-16:TP=-1.5:LRA=11[out]"
    )

    cmd = ["ffmpeg", "-y", *inputs,
           "-filter_complex", ";".join(filters),
           "-map", "[out]", "-ar", "44100",
           "-codec:a", "libmp3lame", "-b:a", "96k",
           str(out_path)]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


def _stitch_wave(rendered: list[tuple[Path, float]], out_path: Path) -> Path:
    """ffmpeg-less fallback: concatenate PCM WAVs of identical format with
    trailing silences, using only the stdlib wave module. No normalization
    or MP3 — good enough to listen; install ffmpeg for the real thing."""
    import wave

    with wave.open(str(rendered[0][0]), "rb") as first:
        params = first.getparams()

    with wave.open(str(out_path), "wb") as out:
        out.setparams(params)
        bytes_per_sec = params.framerate * params.sampwidth * params.nchannels
        for wav, pause in rendered:
            with wave.open(str(wav), "rb") as w:
                if (w.getframerate(), w.getsampwidth(), w.getnchannels()) != (
                        params.framerate, params.sampwidth, params.nchannels):
                    raise RuntimeError(
                        f"{wav} has different audio format; install ffmpeg "
                        "to stitch mixed formats")
                out.writeframes(w.readframes(w.getnframes()))
            out.writeframes(b"\x00" * int(bytes_per_sec * pause))
    return out_path
