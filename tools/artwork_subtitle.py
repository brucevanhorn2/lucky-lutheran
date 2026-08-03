#!/usr/bin/env python3
"""Re-letter the subtitle line on the podcast artwork.

The cover art was built once, by hand, from the corner medallion of the
Calendar page of the Common Service Book (1917) — assets/source-calendar-
page-1917.jpg, printed p.1, scan n10. No generator script was kept, so when
the third office changed name from Compline to the Evening Suffrages there
was nothing to rebuild the art with.

Rather than reconstruct the whole composition from memory and risk a
different-looking cover, this repaints only the subtitle band: fills it with
the page's own cream, then re-letters in the same gold, font and metrics as
the line it replaces. The medallion, the title and the gold rules are never
touched.

Colours and metrics below were sampled from the existing 3000px art, so the
patched line matches the original letter for letter in everything but its
words.

    python3 tools/artwork_subtitle.py "MATINS · VESPERS · SUFFRAGES"
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"

CREAM = (238, 231, 214)   # the page ground
GOLD = (150, 116, 48)     # the subtitle ink, and the rules

# Sampled from assets/podcast-art-3000.png. The band is generously taller than
# the glyphs so descenders and any tracking overhang are cleared.
MASTER = 3000
BAND = (150, 2450, 2850, 2585)   # region to repaint, in master pixels
CAP_TOP = 2479                   # cap height top of the line being replaced
CAP_BOTTOM = 2540                # baseline (the line has no descenders)
TRACKING = 6                     # letter-spacing, master pixels

SIZES = (3000, 1400)             # Apple wants >=1400; 3000 is the master


def _letter(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont,
            centre_x: int, cap_top: int) -> None:
    """Draw `text` letter-spaced and centred, with its cap height at cap_top."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + TRACKING * (len(text) - 1)
    x = centre_x - total / 2
    # Anchor on cap height, not the ascender: "M" must land where "M" landed.
    top = font.getbbox("M")[1]
    for ch, w in zip(text, widths):
        draw.text((x, cap_top - top), ch, font=font, fill=GOLD)
        x += w + TRACKING


def _fit_font(draw: ImageDraw.ImageDraw, text: str) -> ImageFont.FreeTypeFont:
    """Largest size whose cap height matches the line being replaced."""
    want = CAP_BOTTOM - CAP_TOP
    size = want
    while True:
        f = ImageFont.truetype(FONT, size)
        top, bottom = f.getbbox("M")[1], f.getbbox("M")[3]
        if bottom - top >= want:
            return f
        size += 1


def relabel(subtitle: str, assets: Path) -> list[Path]:
    master = Image.open(assets / f"podcast-art-{MASTER}.png").convert("RGB")
    draw = ImageDraw.Draw(master)
    draw.rectangle(BAND, fill=CREAM)
    _letter(draw, subtitle, _fit_font(draw, subtitle), MASTER // 2, CAP_TOP)

    written = []
    for size in SIZES:
        img = master if size == MASTER else master.resize(
            (size, size), Image.LANCZOS)
        out = assets / f"podcast-art-{size}.png"
        img.save(out)
        written.append(out)
    return written


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__.strip().splitlines()[-1].strip())
    root = Path(__file__).resolve().parent.parent
    for p in relabel(sys.argv[1], root / "assets"):
        print(f"wrote {p}")
