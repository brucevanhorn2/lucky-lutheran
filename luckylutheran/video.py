"""Read-along video: the episode's transcript on screen, in step with the audio.

Built *after* the MP3, from what the audio build left behind, and never calls
the TTS engine. The timing is not estimated or aligned after the fact: the
per-episode directory `segments/<slug>/` holds one numbered link per spoken
chunk, in stitch order, and `_stitch` lays those clips end to end with known
silences between them. Summing the clip lengths and the same silences
reproduces every line's start time exactly. The result is checked against
the MP3's real duration, so a mismatch fails loudly instead of drifting out
of step for twenty minutes.

The page is laid out as the `.md` transcript reads: the title, the italic
summary line, section headings, and paragraphs that open with the speaker's
label. The line being spoken is in full ink with a red rubric label, and the
rest of the page is dimmed. The page scrolls so the current line stays in
the same place on screen. Each line is one still image held for its duration,
so encoding is cheap and needs no GPU.
"""

from __future__ import annotations

import re
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from luckylutheran import audio, music
from luckylutheran.assemble import Episode

W, H = 1920, 1080
FPS = 24

PAPER = (244, 239, 228)
INK = (35, 31, 27)
DIM = (172, 163, 150)
RUBRIC = (150, 32, 24)
RUBRIC_DIM = (205, 160, 150)

FONT_DIR = Path("/usr/share/fonts/opentype/urw-base35")
FONTS = {
    "roman": "P052-Roman.otf",
    "bold": "P052-Bold.otf",
    "italic": "P052-Italic.otf",
}
FALLBACK = {
    "roman": "DejaVuSerif.ttf",
    "bold": "DejaVuSerif-Bold.ttf",
    "italic": "DejaVuSerif-Italic.ttf",
}

BODY_SIZE = 44
HEAD_SIZE = 52
COLUMN_X = 260
COLUMN_W = W - 2 * COLUMN_X
LEADING = 1.42
PARA_GAP = 30
HEAD_GAP_ABOVE = 40
HEAD_GAP_BELOW = 18

# The current line's top edge sits here, so there is always some context
# above it and a good run of what is coming below.
ANCHOR_Y = 330
# Top and bottom bands fade into the paper so lines don't end in a hard cut.
FADE = 150

LABELS = {"liturgist": "L:", "congregation": "C:", "lector": "Lector:",
          "all": "All:"}

LINK_RE = re.compile(r"^(\d{3})(?:-(\d{2}))?-(.+)-([0-9a-f]{8})\.wav$")


def _font(style: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(FONT_DIR / FONTS[style]), size)
    except OSError:
        return ImageFont.truetype(FALLBACK[style], size)


# --- timing -----------------------------------------------------------------

@dataclass
class Cue:
    """One spoken chunk: which segment, which chunk of it, and when."""
    seg: int
    chunk: int
    start: float
    end: float  # includes the silence after it; the line stays up through it


def _duration(path: Path) -> float:
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes() / w.getframerate()
    except (wave.Error, EOFError):
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            check=True, capture_output=True, text=True)
        return float(out.stdout.strip())


def _crowd_roster() -> list[str]:
    """The crowd as the engines name it, for checking crowd-line keys."""
    crowd = Path(__file__).resolve().parent.parent / "assets" / "voices" / "crowd"
    return sorted(f"crowd/{p.stem}" for p in crowd.glob("*.wav"))


def _pick_clip(work: Path, i: int, j: int | None, chunk: str,
               roster: list[str]) -> Path:
    """The link for segment i, chunk j that matches the current words.

    The links are named by content hash and are never pruned, so an earlier
    render of an edited line leaves a stale link at the same position. The
    hash tells them apart: the matching link is the one this text produces."""
    prefix = f"{i:03d}" + (f"-{j:02d}" if j is not None else "") + "-"
    candidates = []
    for p in work.glob(f"{prefix}*.wav"):
        m = LINK_RE.match(p.name)
        if m and m.group(2) == (f"{j:02d}" if j is not None else None):
            candidates.append((p, m.group(4), m.group(3).endswith("-crowd")))
    if not candidates:
        raise FileNotFoundError(
            f"no rendered clip for segment {i}"
            + (f" chunk {j}" if j is not None else "") + f" in {work}")
    want = {audio._key(chunk), audio._key(chunk, *roster)}
    matching = [p for p, key, _ in candidates if key in want]
    if matching:
        return matching[0]
    # Crowd keys depend on the roster the engine had at render time. If it
    # doesn't match today's, take the newest link; the total-duration check
    # below still guards the result.
    return max((p for p, _, _ in candidates), key=lambda p: p.lstat().st_mtime)


def timeline(episode: Episode, out_dir: Path) -> tuple[list[Cue], float]:
    """Cues for every spoken chunk, plus the intro length (bumper + breath).

    Mirrors `audio.render_episode` and `audio._stitch` exactly: the same
    chunking, the same pauses, and the bumper both before and after."""
    work = out_dir / "segments" / episode.slug
    if not work.is_dir():
        raise FileNotFoundError(f"{work} not found; build the audio first")
    roster = _crowd_roster()

    bumper = music.render_tune(music.tune_for(episode.day.season))
    bumper_len = _duration(bumper)
    t = bumper_len + 2.0
    intro = t

    cues: list[Cue] = []
    for i, seg in enumerate(episode.segments):
        chunks = audio._chunk_text(seg.text)
        for j, chunk in enumerate(chunks):
            clip = _pick_clip(work, i, j if len(chunks) > 1 else None,
                              chunk, roster)
            last = j == len(chunks) - 1
            span = _duration(clip) + (seg.pause_after if last
                                      else audio.CHUNK_PAUSE)
            cues.append(Cue(i, j, t, t + span))
            t += span
    expected = t + bumper_len

    mp3 = out_dir / f"{episode.slug}.mp3"
    actual = _duration(mp3)
    if abs(actual - expected) > 1.5:
        raise RuntimeError(
            f"{mp3.name} runs {actual:.1f}s but its clips add up to "
            f"{expected:.1f}s; the transcript has changed since the audio was "
            "built. Rebuild the audio, then the video.")
    return cues, intro


# --- page layout ------------------------------------------------------------

@dataclass
class Word:
    text: str
    x: int
    y: int  # relative to the document top
    chunk: int | None  # None = the speaker label
    seg: int


@dataclass
class Block:
    kind: str  # "heading" or "line"
    top: int
    bottom: int
    seg: int  # for headings, the first segment of the section
    words: list[Word]
    section: str


def layout(episode: Episode) -> list[Block]:
    body = _font("roman", BODY_SIZE)
    bold = _font("bold", BODY_SIZE)
    line_h = int(BODY_SIZE * LEADING)
    space = body.getlength(" ")

    blocks: list[Block] = []
    y = 0
    current = None
    for i, seg in enumerate(episode.segments):
        if seg.section_title != current:
            current = seg.section_title
            y += HEAD_GAP_ABOVE if blocks else 0
            blocks.append(Block("heading", y, y + HEAD_SIZE, i,
                                [Word(current, COLUMN_X, y, None, i)], current))
            y += HEAD_SIZE + HEAD_GAP_BELOW

        tokens: list[tuple[str, int | None]] = [(LABELS[seg.speaker], None)]
        for j, chunk in enumerate(audio._chunk_text(seg.text)):
            tokens += [(w, j) for w in chunk.split()]

        words: list[Word] = []
        top = y
        x = COLUMN_X
        for text, chunk in tokens:
            font = bold if chunk is None else body
            width = font.getlength(text)
            if x > COLUMN_X and x + width > COLUMN_X + COLUMN_W:
                x = COLUMN_X
                y += line_h
            words.append(Word(text, int(x), y, chunk, i))
            x += width + space
        y += line_h
        blocks.append(Block("line", top, y, i, words, current))
        y += PARA_GAP
    return blocks


def _fade_mask() -> Image.Image:
    """Opacity of the paper laid over the text: solid above and below the
    viewport, ramping to clear across the fade bands."""
    mask = Image.new("L", (1, H), 0)
    top, bottom = 150, H - 40
    for yy in range(H):
        if yy < top:
            a = 255
        elif yy < top + FADE:
            a = int(255 * (1 - (yy - top) / FADE))
        elif yy > bottom:
            a = 255
        elif yy > bottom - FADE:
            a = int(255 * (1 - (bottom - yy) / FADE))
        else:
            a = 0
        mask.putpixel((0, yy), a)
    return mask.resize((W, H))


def _header(draw: ImageDraw.ImageDraw, episode: Episode) -> None:
    md = episode.transcript().splitlines()
    title = md[0].lstrip("# ")
    summary = md[2].strip("*")
    draw.text((COLUMN_X, 38), title, font=_font("bold", 40), fill=INK)
    draw.text((COLUMN_X, 92), summary, font=_font("italic", 28), fill=DIM)
    draw.line((COLUMN_X, 140, COLUMN_X + COLUMN_W, 140), fill=DIM, width=2)


def render_page(blocks: list[Block], episode: Episode, cue: Cue,
                fade: Image.Image) -> Image.Image:
    body = _font("roman", BODY_SIZE)
    bold = _font("bold", BODY_SIZE)
    head = _font("bold", HEAD_SIZE)

    active = next(b for b in blocks if b.kind == "line" and b.seg == cue.seg)
    # Keep the current chunk's first line at the anchor, not the block's top,
    # so a long psalm scrolls through as it is read.
    first = next(w for w in active.words if w.chunk == cue.chunk)
    shift = ANCHOR_Y - first.y

    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    for b in blocks:
        if b.bottom + shift < 0 or b.top + shift > H:
            continue
        if b.kind == "heading":
            on = b.section == active.section
            w = b.words[0]
            draw.text((w.x, w.y + shift), w.text, font=head,
                      fill=RUBRIC if on else RUBRIC_DIM)
            continue
        for w in b.words:
            if w.chunk is None:
                on = b is active
                draw.text((w.x, w.y + shift), w.text, font=bold,
                          fill=RUBRIC if on else RUBRIC_DIM)
            else:
                on = b is active and w.chunk == cue.chunk
                draw.text((w.x, w.y + shift), w.text, font=body,
                          fill=INK if on else DIM)

    img.paste(Image.new("RGB", (W, H), PAPER), (0, 0), fade)
    _header(ImageDraw.Draw(img), episode)
    return img


def render_card(episode: Episode) -> Image.Image:
    """Shown under the organ bumper at the start and the end."""
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    md = episode.transcript().splitlines()
    lines = [
        (episode.title, _font("bold", 110), RUBRIC),
        (episode.date.strftime("%A, %B %-d, %Y"), _font("roman", 56), INK),
        (md[2].strip("*"), _font("italic", 36), DIM),
    ]
    y = 340
    for text, font, fill in lines:
        width = draw.textlength(text, font=font)
        draw.text(((W - width) / 2, y), text, font=font, fill=fill)
        y += int(font.size * 1.6)
    return img


# --- encoding ---------------------------------------------------------------

def build_video(episode: Episode, out_dir: Path,
                say=print) -> Path:
    cues, intro = timeline(episode, out_dir)
    blocks = layout(episode)
    fade = _fade_mask()

    frames = out_dir / "video" / episode.slug
    frames.mkdir(parents=True, exist_ok=True)
    for old in frames.glob("*.png"):
        old.unlink()

    card = frames / "card.png"
    render_card(episode).save(card)

    # The concat demuxer shows each image for its `duration`. The intro card
    # holds until the first line starts; the outro card covers the closing
    # bumper. The last entry is repeated because the demuxer ignores the
    # final duration otherwise.
    entries: list[tuple[Path, float]] = [(card, intro)]
    say(f"  drawing {len(cues)} pages")
    for n, cue in enumerate(cues):
        page = frames / f"{n:04d}.png"
        render_page(blocks, episode, cue, fade).save(page)
        entries.append((page, cue.end - cue.start))
    mp3 = out_dir / f"{episode.slug}.mp3"
    entries.append((card, _duration(mp3) - cues[-1].end))

    listfile = frames / "frames.txt"
    with listfile.open("w") as f:
        for path, dur in entries:
            f.write(f"file '{path.resolve()}'\nduration {dur:.4f}\n")
        f.write(f"file '{entries[-1][0].resolve()}'\n")

    out = out_dir / f"{episode.slug}.mp4"
    say(f"  encoding {out.name}")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
         "-i", str(mp3),
         "-map", "0:v", "-map", "1:a",
         "-vf", f"fps={FPS},format=yuv420p",
         "-c:v", "libx264", "-preset", "medium", "-tune", "stillimage",
         "-crf", "20",
         "-c:a", "aac", "-b:a", "160k",
         "-shortest", "-movflags", "+faststart",
         str(out)],
        check=True, capture_output=True)
    return out
