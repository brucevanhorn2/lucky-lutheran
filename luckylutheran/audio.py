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
from luckylutheran import progress, speech
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


def render_episode(episode: Episode, engine: TTSEngine, out_dir: Path,
                   prog: progress.Render | None = None) -> Path | None:
    """Render all segments and stitch them. Returns the MP3 path, or None in
    script-only mode (engine produced no audio).

    Resumable: chunks whose WAV already exists are skipped, so a failed or
    interrupted build only re-renders what's missing."""
    work = out_dir / "segments" / episode.slug
    work.mkdir(parents=True, exist_ok=True)

    from luckylutheran.tts import resolve_speaker

    # Crowd: when parishioner voices exist (and ffmpeg can mix them),
    # congregation lines are rendered once per voice and layered.
    crowd = engine.crowd_voices() if ffmpeg_available() else []

    total = len(episode.segments)
    voices = len(crowd) + 1
    bar = prog or progress.Render(
        title=episode.slug,
        total=count_voice_renders(episode, crowd),
        prefix="")
    if crowd:
        bar.title += f"  ·  crowd of {voices} on congregation lines"
    bar.start()

    rendered: list[tuple[Path, float]] = []
    for i, seg in enumerate(episode.segments):
        chunks = _chunk_text(seg.text)
        in_crowd = crowd and resolve_speaker(seg.speaker) == "congregation"
        for j, chunk in enumerate(chunks):
            suffix = "" if len(chunks) == 1 else f"-{j:02d}"
            name = (f"{i:03d}{suffix}-{seg.section_id}-crowd.wav" if in_crowd
                    else f"{i:03d}{suffix}-{seg.section_id}-{seg.speaker}.wav")
            wav = work / name
            label = f"{seg.section_title[:22]:<22} {seg.speaker}"
            if len(chunks) > 1:
                label += f" ({j + 1}/{len(chunks)})"
            cost = (len(_phrase_units(chunk)) * voices) if in_crowd else 1

            if wav.exists() and wav.stat().st_size > 44:
                bar.step(cost, f"{label}  (cached)", cached=True)
                result: Path | None = wav
            elif in_crowd:
                result = _render_crowd_chunk(engine, chunk, crowd, wav,
                                             bar=bar, label=label)
            else:
                bar.step(0, label)
                result = engine.synthesize(speech.for_speech(chunk),
                                           seg.speaker, wav)
                bar.step(1, label)

            if result is not None:
                last = j == len(chunks) - 1
                rendered.append((result, seg.pause_after if last else CHUNK_PAUSE))

    if not rendered:
        bar.finish("no audio (script-only)")
        return None
    if not ffmpeg_available():
        bar.note("ffmpeg not found — stitching to WAV with the pure-python "
                 "fallback (install ffmpeg for MP3 + loudness normalization; "
                 "bumper music requires ffmpeg and is skipped)")
        out = _stitch_wave(rendered, out_dir / f"{episode.slug}.wav")
        bar.finish(out.name)
        return out

    from luckylutheran import music
    tune = music.tune_for(episode.day.season)
    bar.note(f"organ bumper ({tune})")
    bumper = music.render_tune(tune)
    out_path = out_dir / f"{episode.slug}.mp3"
    bar.note(f"stitching {len(rendered)} clips, normalizing loudness")
    result = _stitch(rendered, out_path, bumper=bumper, tags=id3_tags(episode))
    bar.finish(result.name)
    return result


def count_voice_renders(episode: Episode, crowd: list[str]) -> int:
    """How many TTS calls this episode costs — the honest unit of progress.

    A congregation line is synthesized once per voice per phrase unit, so an
    eight-voice crowd over five phrases is forty calls against one for a
    liturgist line of the same length. Counting segments instead makes the
    bar lurch and the ETA meaningless."""
    from luckylutheran.tts import resolve_speaker

    voices = len(crowd) + 1
    calls = 0
    for seg in episode.segments:
        in_crowd = bool(crowd) and resolve_speaker(seg.speaker) == "congregation"
        for chunk in _chunk_text(seg.text):
            calls += len(_phrase_units(chunk)) * voices if in_crowd else 1
    return calls


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


def _render_crowd_chunk(engine, chunk: str, crowd: list[str],
                        out_path: Path, bar=None, label: str = "") -> Path | None:
    """Render a congregation chunk as several short phrase units, mixing each
    unit's voices independently and concatenating them. Mixing per phrase
    keeps the crowd tight: onset drift resets at every phrase boundary instead
    of accumulating across a long passage into an echo chamber.

    Per-unit mixes are cached beside the output, so retries are cheap."""
    units = _phrase_units(chunk)
    voices = len(crowd) + 1
    if len(units) <= 1:
        return _render_crowd_unit(engine, chunk, crowd, out_path,
                                  bar=bar, label=label)

    unit_dir = out_path.parent / "crowd-units"
    unit_dir.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []
    for k, unit in enumerate(units):
        part = unit_dir / f"{out_path.stem}-u{k:02d}.wav"
        phrase = f"{label}  phrase {k + 1}/{len(units)}"
        if part.exists() and part.stat().st_size > 44:
            if bar:
                bar.step(voices, f"{phrase}  (cached)", cached=True)
        elif _render_crowd_unit(engine, unit, crowd, part,
                                bar=bar, label=phrase) is None:
            return None
        parts.append(part)
    return _concat_wavs(parts, out_path)


def _render_crowd_unit(engine, chunk: str, crowd: list[str],
                       out_path: Path, bar=None, label: str = "") -> Path | None:
    """Render one congregation phrase with every voice (the chosen
    congregation cast member leads, parishioners join) and layer them
    slightly out of sync, like a real roomful of people praying.

    Per-voice renders are cached beside the mix, so retries are cheap. When
    `label` is given, prints one dot per voice as it lands, so a slow crowd
    render visibly progresses instead of looking hung."""
    voices = ["congregation", *crowd]
    part_dir = out_path.parent / "crowd-parts"
    parts: list[Path] = []
    for n, voice in enumerate(voices, 1):
        part = part_dir / f"{out_path.stem}-{voice.replace('/', '_')}.wav"
        hit = part.exists() and part.stat().st_size > 44
        if not hit:
            if engine.synthesize(speech.for_speech(chunk), voice,
                                 part) is None:
                if bar:
                    bar.note(f"FAILED {label} — {voice}")
                return None
        # One tick per voice, so a slow crowd visibly advances rather than
        # looking hung for the length of eight synthesis calls.
        if bar:
            bar.step(1, f"{label}  voice {n}/{len(voices)}", cached=hit)
        parts.append(part)
    return _mix_crowd(parts, chunk, out_path)


def _mix_crowd(parts: list[Path], chunk: str, out_path: Path) -> Path:
    """Time-align the renders to a common phrase length, then mix with
    small per-voice onset delays and gain differences.

    Different voices take different time over the same words; a few percent
    of atempo keeps them together phrase-level while staying humanly ragged
    syllable-level. Randomness is seeded from the text, so re-renders of the
    same chunk mix identically (resume-friendly)."""
    import hashlib
    import random
    import wave as wave_mod

    def duration(p: Path) -> float:
        with wave_mod.open(str(p), "rb") as w:
            return w.getnframes() / w.getframerate()

    durations = sorted(duration(p) for p in parts)
    target = durations[len(durations) // 2]  # median

    rng = random.Random(hashlib.sha256(chunk.encode()).digest())
    inputs: list[str] = []
    filters: list[str] = []
    for i, part in enumerate(parts):
        inputs += ["-i", str(part)]
        tempo = min(max(duration(part) / target, 0.5), 2.0)
        delay_ms = 0 if i == 0 else rng.randint(15, 70)   # lead voice on time
        gain = 1.0 if i == 0 else rng.uniform(0.55, 0.85)
        filters.append(
            f"[{i}:a]atempo={tempo:.4f},adelay={delay_ms},"
            f"volume={gain:.2f}[v{i}]")
    mix = "".join(f"[v{i}]" for i in range(len(parts)))
    filters.append(
        f"{mix}amix=inputs={len(parts)}:duration=longest:normalize=0,"
        f"volume={1.6 / len(parts):.3f}[out]")

    cmd = ["ffmpeg", "-y", *inputs,
           "-filter_complex", ";".join(filters),
           "-map", "[out]", str(out_path)]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


def id3_tags(episode: Episode) -> dict[str, str]:
    """ID3 tags for the episode, so the MP3 is self-describing off the feed.

    Podcast apps read these when a file is sideloaded or downloaded rather
    than played through the RSS feed, and they are what a car stereo or a
    plain music player shows. Kept consistent with feed.py's PODCAST block.
    """
    from luckylutheran import feed

    day = episode.day
    readings = episode.readings
    appointed = (readings.title or readings.proper) if readings.source == "proper" else None
    comment = (f"{episode.title} for {day.date.strftime('%B %-d, %Y')}. "
               f"{readings.psalm}; {readings.reading}"
               + (f". Appointed for {appointed}." if appointed else ". Read in course."))
    return {
        "title": episode.episode_title,
        "artist": feed.PODCAST["author"],
        "album_artist": feed.PODCAST["author"],
        "album": feed.PODCAST["title"],
        "date": day.date.isoformat(),
        "year": str(day.date.year),
        "genre": "Religion & Spirituality",
        "comment": comment,
        "TIT3": day.season_name,          # subtitle
        "language": "eng",
    }


def _stitch(rendered: list[tuple[Path, float]], out_path: Path,
            bumper: Path | None = None,
            tags: dict[str, str] | None = None) -> Path:
    """Concatenate WAVs with per-segment trailing silence, normalize, encode.
    A bumper tune, when given, opens the episode (fading down into the
    greeting) and closes it after the benediction (fading up, then out)."""
    clips = list(rendered)
    if bumper is not None:
        # Intro: full tune, gentle entrance, 2s breath before the greeting.
        # Outro: same tune returning after the final silence.
        clips = [(bumper, 2.0), *clips, (bumper, 0.0)]

    inputs: list[str] = []
    filters: list[str] = []
    for i, (wav, pause) in enumerate(clips):
        inputs += ["-i", str(wav)]
        # Per clip: resample to a common rate, fade the head (30 ms) and
        # tail (80 ms, via the areverse trick) so joins never click or cut
        # off abruptly, then pad with the segment's trailing silence.
        is_bumper = bumper is not None and wav == bumper
        fade_in, fade_out = (1.5, 3.0) if is_bumper else (0.03, 0.08)
        gain = ",volume=0.65" if is_bumper else ""
        filters.append(
            f"[{i}:a]aresample=44100,aformat=channel_layouts=mono,"
            f"afade=t=in:d={fade_in},areverse,afade=t=in:d={fade_out},"
            f"areverse{gain},apad=pad_dur={pause}[s{i}]"
        )
    concat = "".join(f"[s{i}]" for i in range(len(clips)))
    filters.append(
        f"{concat}concat=n={len(clips)}:v=0:a=1,"
        f"loudnorm=I=-16:TP=-1.5:LRA=11[out]"
    )

    meta: list[str] = []
    for key, value in (tags or {}).items():
        meta += ["-metadata", f"{key}={value}"]

    cmd = ["ffmpeg", "-y", *inputs,
           "-filter_complex", ";".join(filters),
           "-map", "[out]", "-ar", "44100",
           "-codec:a", "libmp3lame", "-b:a", "96k",
           *meta, "-id3v2_version", "3", "-write_id3v1", "1",
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
