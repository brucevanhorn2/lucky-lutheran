"""Scripture text provider.

Fetches passages in public-domain translations (KJV by default) from
bible-api.com, with a local file cache so each passage is fetched once ever.
Fully offline-safe: if the network is unavailable and the passage is not
cached, returns None and the assembler inserts a readable placeholder.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_TRANSLATION = "kjv"  # public domain; "web" (World English Bible) also PD
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "scripture"
API = "https://bible-api.com/{ref}?translation={translation}"


def _cache_path(reference: str, translation: str) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", reference.lower()).strip("-")
    return CACHE_DIR / translation / f"{slug}.json"


def get_passage(reference: str, translation: str = DEFAULT_TRANSLATION) -> str | None:
    """Return passage text for e.g. 'Psalm 95' or 'John 1:1-14', or None."""
    cache = _cache_path(reference, translation)
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))["text"]

    url = API.format(ref=urllib.parse.quote(reference), translation=translation)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None

    verses = payload.get("verses")
    if verses:
        raw = " ".join(v.get("text", "").strip() for v in verses)
    else:
        raw = payload.get("text", "")
    text = _clean(raw)
    if not text:
        return None

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps({"reference": reference, "translation": translation, "text": text},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    return text


def _clean(text: str) -> str:
    """Normalize whitespace and strip verse-number artifacts for smooth TTS."""
    text = text.replace("¶", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()
