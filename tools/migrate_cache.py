#!/usr/bin/env python3
"""Fold the old per-episode segment directories into the shared render store.

Before the store was shared, every episode kept its own copy of the liturgy's
audio under `episodes/segments/<slug>/`. The names already carried the content
hash, so the old renders are perfectly good cache entries -- they were just
filed where no other episode could find them.

This hardlinks them into `episodes/cache/`, so the first batch run after the
change starts warm instead of re-synthesizing the ordinary parts of Matins and
Vespers from scratch. Hardlinks, not copies: no new disk, and nothing is moved
or deleted, so a batch running right now is untouched.

    python3 tools/migrate_cache.py [episodes_dir] [--prune]

Safe to run while a batch is working: it only adds links, and it ignores
anything written in the last few minutes, so a WAV still being synthesized is
never adopted half-finished. `--prune` afterwards deletes the old per-episode
directories, reclaiming the duplicate copies -- run that only once no batch
is running.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import time
from pathlib import Path

# A render still being written looks like a complete one: a WAV header plus
# however many frames have landed. Adopting that would put a truncated take
# in the store for good, so leave the recently-touched alone.
SETTLED_SECONDS = 300

# <index>[-<chunk>]-<section>-<speaker>-<key8>.wav
LINE = re.compile(r"^\d{3}(?:-\d{2})?-(?:.+)-([a-z0-9]+)\.wav$")
VOICE = re.compile(r"^[a-f0-9]{8}-[A-Za-z0-9_.-]+\.wav$")


def _speaker(name: str) -> str:
    # ...-<section>-<speaker>-<key>.wav; no speaker contains a hyphen.
    return name[:-4].rsplit("-", 2)[-2]


def _settled(wav: Path, now: float) -> bool:
    st = wav.stat()
    return st.st_size > 44 and now - st.st_mtime > SETTLED_SECONDS


def _adopt(src: Path, dst: Path, stats: dict[str, int]) -> None:
    if dst.exists():
        stats["already"] += 1
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)      # different filesystem, or no link support
    stats["adopted"] += 1


def migrate(out_dir: Path, prune: bool = False) -> None:
    segments = out_dir / "segments"
    if not segments.is_dir():
        sys.exit(f"no {segments} to migrate")
    cache = out_dir / "cache"
    for tier in ("lines", "phrases", "voices"):
        (cache / tier).mkdir(parents=True, exist_ok=True)

    stats = {"adopted": 0, "already": 0}
    now = time.time()
    for slug in sorted(p for p in segments.iterdir() if p.is_dir()):
        # Whole-chunk renders, which short-circuit everything below them.
        for wav in sorted(slug.glob("*.wav")):
            m = LINE.match(wav.name)
            if m and _settled(wav, now):
                _adopt(wav, cache / "lines" / f"{m.group(1)}-{_speaker(wav.name)}.wav",
                       stats)
        # Per-voice TTS renders -- the expensive tier. They lived in two
        # places (beside the chunk, and again under crowd-units/) and were
        # already named exactly as the shared store names them.
        for wav in sorted(slug.rglob("crowd-parts/*.wav")):
            if VOICE.match(wav.name) and _settled(wav, now):
                _adopt(wav, cache / "voices" / wav.name, stats)
        # crowd-units/ is skipped on purpose: the old names key the mix on
        # its position in the chunk, not on the phrase, so they cannot be
        # re-addressed. They are pure ffmpeg mixes of the voices above, and
        # a line-cache hit means they are never asked for anyway.

    print(f"adopted {stats['adopted']} renders "
          f"({stats['already']} already in the store)")

    if prune:
        for slug in sorted(p for p in segments.iterdir() if p.is_dir()):
            shutil.rmtree(slug)
        print(f"pruned {segments} (re-created per episode on the next run)")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    migrate(Path(args[0]) if args else Path("episodes"),
            prune="--prune" in sys.argv[1:])
