"""Turning written text into text meant to be *said*.

Two jobs the printed page leaves to the reader:

1. **Rubrics that are not text.** "Selah" appears 71 times in the Psalms and
   three times in Habakkuk 3, and nobody is certain what it means — the
   Septuagint renders it *diapsalma*, "through the psalm", an instrumental
   interlude; others tie it to a root meaning "lift up" (the voices, the
   instruments) or read it as a cue for the congregation. What is not in
   doubt is that it was a direction to those performing the psalm, not a word
   to be spoken aloud. The KJV prints it because the KJV prints what is on
   the page. Reading it out is like a singer singing "repeat chorus".

   So we do what it says instead of saying it: the word is removed and a
   silence is left in its place.

2. **Words the synthesizer says wrongly.** Qwen3-TTS has no pronunciation
   lexicon we can address, so the only lever is respelling the input. Kept
   deliberately small — every entry is a word this office actually uses that
   a general-purpose English voice gets wrong.
"""

from __future__ import annotations

import re

# Silence left where a "Selah" stood, in seconds. Long enough to register as
# a deliberate breath rather than a glitch in the read.
SELAH_PAUSE = 1.6

_SELAH = re.compile(r"\s*\bSelah\b\s*[.;,]?\s*", re.IGNORECASE)

# Respellings fed to the TTS. The written form is preserved in transcripts and
# show notes — only what is *spoken* changes.
PRONUNCIATION = {
    # "MAT-ins", rhyming with "flattens", from Latin matutinus. "MAY-tins" is
    # a spelling pronunciation and is not how the office is named by anyone
    # who prays it.
    r"\bMatins\b": "Mattins",
    # "KOM-plin", not "com-PLINE". The Compline office was retired in favour
    # of the Evening Suffrages (see docs/retired/compline.yaml), but the word
    # still occurs in show notes and prose, so the respelling stays.
    r"\bCompline\b": "Complin",
    # "SUFF-ra-jez" — not "suff-RAY-ges", and not the voting sense.
    r"\bSuffrages\b": "SUFF-ra-jez",
    # "BEN-eh-dih-site" / "beh-NED-ih-kah-mus" — Latin-derived office names a
    # general English voice reliably mangles.
    r"\bBenedicamus\b": "Beneh-DEE-kah-mus",
    r"\bMagnificat\b": "Mag-NIF-ih-cat",
    r"\bNunc Dimittis\b": "Noonk Dee-MIT-tis",
    r"\bVenite\b": "Ven-EE-tay",
    r"\bKyrie\b": "KEER-ee-ay",
}


def split_on_selah(text: str) -> list[str]:
    """Split a passage where "Selah" stood, dropping the word itself.

    Returns one or more chunks; the caller renders each as its own segment so
    a real silence falls between them. A passage with no Selah comes back as
    a single chunk, so callers need no special case.
    """
    parts = [p.strip() for p in _SELAH.split(text)]
    return [p for p in parts if p] or [text.strip()]


def for_speech(text: str) -> str:
    """Apply pronunciation respellings. Written text is left untouched
    elsewhere — this is only what goes to the synthesizer."""
    for pattern, said in PRONUNCIATION.items():
        text = re.sub(pattern, said, text)
    return text
