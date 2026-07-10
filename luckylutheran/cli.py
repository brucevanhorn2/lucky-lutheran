"""Command-line interface.

  lucky script  [--office matins] [--date 2026-07-08]   print the transcript
  lucky build   [--office matins] [--date ...] [--engine null]
                                                         build episode + metadata (+ audio)
  lucky feed    [--episodes episodes]                    regenerate feed.xml
  lucky calendar [--date ...]                            show church-year info
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from luckylutheran import assemble, audio, feed, tts
from luckylutheran.churchyear import church_day


def _parse_date(value: str | None) -> dt.date:
    return dt.date.fromisoformat(value) if value else dt.date.today()


def cmd_script(args: argparse.Namespace) -> int:
    episode = assemble.build_episode(_parse_date(args.date), args.office)
    print(episode.transcript())
    return 0


def _get_engine(name: str) -> tts.TTSEngine | None:
    """Engine or None (with a message) when unavailable on this machine."""
    try:
        return tts.get_engine(name)
    except ImportError as exc:
        print(f"TTS engine {name!r} unavailable here ({exc.name}). "
              "On wintermute: pip install -U qwen-tts soundfile",
              file=sys.stderr)
    except (ConnectionError, FileNotFoundError) as exc:
        print(exc, file=sys.stderr)
    return None


def _build_one(date: dt.date, office: str, out_dir: Path,
               engine: tts.TTSEngine) -> Path | None:
    """Build one episode (transcript + metadata + audio); return audio path."""
    episode = assemble.build_episode(date, office)
    out_dir.mkdir(parents=True, exist_ok=True)

    transcript_path = out_dir / f"{episode.slug}.md"
    transcript_path.write_text(episode.transcript(), encoding="utf-8")

    mp3 = audio.render_episode(episode, engine, out_dir)

    meta = {
        "slug": episode.slug,
        "office": episode.office,
        "date": date.isoformat(),
        "episode_title": episode.episode_title,
        "season": episode.day.season_name,
        "psalm": episode.readings.psalm,
        "reading": episode.readings.reading,
        "reading_source": episode.readings.source,
        "summary": (f"{episode.title} for {date.strftime('%B %d, %Y')} — "
                    f"{episode.readings.psalm}; {episode.readings.reading}."),
        "built_at": dt.datetime.now().isoformat(timespec="seconds"),
        "audio": mp3.name if mp3 else None,
        "segments": len(episode.segments),
    }
    (out_dir / f"{episode.slug}.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8")
    return mp3


def cmd_build(args: argparse.Namespace) -> int:
    date = _parse_date(args.date)
    engine = _get_engine(args.engine)
    if engine is None:
        return 1
    mp3 = _build_one(date, args.office, Path(args.episodes), engine)
    print(f"transcript: {Path(args.episodes)}/{date.isoformat()}-{args.office}.md")
    print(f"audio:      {mp3 if mp3 else '(script-only: engine produced no audio)'}")
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    """Render a run of daily episodes ahead of time (wintermute is only
    powered on occasionally, so a month is rendered in one sitting)."""
    start = _parse_date(args.start)
    offices = [o.strip() for o in args.offices.split(",")]
    for office in offices:
        if office not in assemble.OFFICES:
            print(f"unknown office {office!r}", file=sys.stderr)
            return 2

    engine = _get_engine(args.engine)
    if engine is None:
        return 1

    out_dir = Path(args.episodes)
    built, skipped, failed = 0, 0, []
    for day_offset in range(args.days):
        date = start + dt.timedelta(days=day_offset)
        for office in offices:
            slug = f"{date.isoformat()}-{office}"
            if not args.force and ((out_dir / f"{slug}.mp3").exists()
                                   or (out_dir / f"{slug}.wav").exists()):
                skipped += 1
                continue
            print(f"=== building {slug}")
            try:
                _build_one(date, office, out_dir, engine)
                built += 1
            except Exception as exc:  # keep the batch going overnight
                failed.append(slug)
                print(f"FAILED {slug}: {exc}", file=sys.stderr)

    feed.write_feed(out_dir, include_future=args.future)
    print(f"\nbatch done: {built} built, {skipped} already existed, "
          f"{len(failed)} failed{': ' + ', '.join(failed) if failed else ''}")
    return 1 if failed else 0


def cmd_feed(args: argparse.Namespace) -> int:
    out = feed.write_feed(Path(args.episodes), include_future=args.future)
    print(f"feed: {out}")
    return 0


def cmd_voices(args: argparse.Namespace) -> int:
    try:
        written = tts.design_voice_cast(overwrite=args.overwrite)
    except ImportError as exc:
        print(f"Qwen3-TTS not available here ({exc.name}). On wintermute: "
              "pip install -U qwen-tts soundfile", file=sys.stderr)
        return 1
    if not written:
        print("all reference voices already exist (use --overwrite to redo)")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    try:
        from luckylutheran import server
        server.run(ip=args.ip, port=args.port)
    except ImportError as exc:
        print(f"Qwen3-TTS not available here ({exc.name}). On the GPU "
              "machine: pip install -U qwen-tts soundfile", file=sys.stderr)
        return 1
    return 0


def cmd_calendar(args: argparse.Namespace) -> int:
    day = church_day(_parse_date(args.date))
    print(f"date:    {day.date.strftime('%A, %B %d, %Y')}")
    print(f"season:  {day.season_name}")
    print(f"easter:  {day.easter.isoformat()} (that year)")
    print(f"day of church year: {day.day_of_church_year}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lucky", description="Daily-office podcast generator")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser, office: bool = True) -> None:
        p.add_argument("--date", help="ISO date (default: today)")
        if office:
            p.add_argument("--office", choices=assemble.OFFICES,
                           default="matins", help="which office to build")

    p = sub.add_parser("script", help="print the episode transcript")
    common(p)
    p.set_defaults(func=cmd_script)

    p = sub.add_parser("build", help="build transcript, metadata, and audio")
    common(p)
    p.add_argument("--episodes", default="episodes", help="output directory")
    p.add_argument("--engine", default="null", choices=list(tts.ENGINES),
                   help="TTS engine (null = script only)")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser(
        "batch", help="render a run of future episodes in one sitting")
    p.add_argument("--start", help="first date, ISO (default: today)")
    p.add_argument("--days", type=int, default=30, help="how many days ahead")
    p.add_argument("--offices", default="matins,vespers",
                   help="comma-separated offices per day")
    p.add_argument("--episodes", default="episodes", help="output directory")
    p.add_argument("--engine", default="gradio", choices=list(tts.ENGINES))
    p.add_argument("--force", action="store_true",
                   help="rebuild episodes that already exist")
    p.add_argument("--future", action="store_true",
                   help="include future-dated episodes in the feed (QA)")
    p.set_defaults(func=cmd_batch)

    p = sub.add_parser("feed", help="regenerate the podcast RSS feed")
    p.add_argument("--episodes", default="episodes", help="episodes directory")
    p.add_argument("--future", action="store_true",
                   help="include future-dated episodes (QA feed)")
    p.set_defaults(func=cmd_feed)

    p = sub.add_parser(
        "voices",
        help="one-time: design the three-voice cast with Qwen3-TTS VoiceDesign")
    p.add_argument("--overwrite", action="store_true",
                   help="regenerate voices that already exist")
    p.set_defaults(func=cmd_voices)

    p = sub.add_parser(
        "serve", help="run the TTS server (on the GPU machine, e.g. wintermute)")
    p.add_argument("--ip", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8765)
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("calendar", help="show church-year info for a date")
    common(p, office=False)
    p.set_defaults(func=cmd_calendar)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
