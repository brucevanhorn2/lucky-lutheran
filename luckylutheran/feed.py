"""Podcast RSS feed generation.

Scans the episodes directory for <slug>.json metadata (written by `lucky
build`) and emits a standard RSS 2.0 feed with iTunes podcast tags. Upload
the episodes directory (MP3s + feed.xml) to any static host — S3, Cloudflare
R2, GitHub Pages — and the feed URL is the podcast.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

# Edit these before publishing.
PODCAST = {
    "title": "The Daily Office",
    "description": (
        "A ten-minute daily office after the historic Lutheran liturgy — "
        "Matins in the morning, Vespers at evening, and Compline at the "
        "close of the day — with the "
        "psalm appointed for the day, a lesson, a portion of Luther's Small "
        "Catechism, and the collect of the season. Drawn entirely from "
        "public-domain sources. Read by synthetic voices."
    ),
    # Where episodes are hosted. Enclosure URLs must be absolute and
    # reachable by the podcast app, so this cannot be a relative path or
    # localhost — a phone fetching the feed needs to resolve it too. Override
    # with LUCKY_BASE_URL; for serving off the LAN that is the machine's
    # address, e.g. http://192.168.1.51:8080
    "base_url": os.environ.get("LUCKY_BASE_URL",
                               "https://example.com/daily-office").rstrip("/"),
    "language": "en-us",
    "author": "Bruce Van Horn",
    "category": "Religion & Spirituality",
}


# Episodes appear in the feed at these local times on their appointed day
# (batches are rendered weeks ahead; pubDate must be the office's day, not
# the render day).
PUBLISH_HOUR = {"matins": 5, "vespers": 17, "compline": 20}


def write_feed(episodes_dir: Path, include_future: bool = False) -> Path:
    now = dt.datetime.now()
    items = []
    for meta_path in sorted(episodes_dir.glob("*.json"), reverse=True):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        mp3 = episodes_dir / f"{meta['slug']}.mp3"
        if not mp3.exists():
            continue  # script-only build; no audio to publish yet
        pub = dt.datetime.combine(
            dt.date.fromisoformat(meta["date"]),
            dt.time(hour=PUBLISH_HOUR.get(meta["office"], 5)))
        if pub > now and not include_future:
            continue  # rendered ahead; publishes on its appointed morning
        items.append(f"""
    <item>
      <title>{escape(meta['episode_title'])}</title>
      <description>{escape(meta['summary'])}</description>
      <guid isPermaLink="false">{escape(meta['slug'])}</guid>
      <pubDate>{format_datetime(pub)}</pubDate>
      <enclosure url="{PODCAST['base_url']}/{mp3.name}"
                 length="{mp3.stat().st_size}" type="audio/mpeg"/>
    </item>""")

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{escape(PODCAST['title'])}</title>
    <link>{PODCAST['base_url']}</link>
    <description>{escape(PODCAST['description'])}</description>
    <language>{PODCAST['language']}</language>
    <itunes:author>{escape(PODCAST['author'])}</itunes:author>
    <itunes:category text="{escape(PODCAST['category'])}"/>
    {''.join(items)}
  </channel>
</rss>
"""
    out = episodes_dir / "feed.xml"
    out.write_text(feed, encoding="utf-8")
    return out
