"""Text-to-speech layer, built around Qwen3-TTS (the model on wintermute).

Each liturgical speaker maps to a distinct, consistent voice so the office
sounds responsive (liturgist / congregation / lector) rather than like an
audiobook.

Two-step voice workflow (Qwen's recommended pattern):

1. ONE TIME:  `lucky voices` uses the VoiceDesign model to synthesize a
   reference clip per cast member from the text descriptions below, saved to
   assets/voices/<speaker>.wav.  (Or drop in your own recordings — any short
   clean WAV works, just set `ref_text` to its exact transcript.)
2. EVERY BUILD: the CustomVoice model turns each reference clip into a
   reusable clone prompt, then renders all ~40 segments with a stable cast.

Requires on wintermute:  pip install -U qwen-tts soundfile
Models download from Hugging Face on first use.
"""

from __future__ import annotations

import abc
import os
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "voices"

# The voice cast. `design` drives the one-time VoiceDesign generation;
# `ref_text` is spoken in the reference clip and reused as the clone
# prompt's transcript, so keep them in sync if you regenerate.
VOICE_CAST = {
    # Cast chosen by Bruce 2026-07-09 from designed candidates
    # (liturgist-b, congregation-c, lector-a in assets/voices/candidates/).
    "liturgist": {
        "design": (
            "A deep, dignified male voice in his sixties, like an old "
            "cathedral rector. Slow, solemn, deliberate delivery, rich low "
            "timbre, long unhurried phrases."
        ),
        "ref_text": (
            "O Lord, our heavenly Father, almighty and everlasting God, "
            "we give Thee thanks for all Thy goodness and tender mercies."
        ),
    },
    "congregation": {
        "design": (
            "A young adult male voice, quiet and earnest, plain unadorned "
            "delivery, like a parishioner speaking a response from the pew."
        ),
        "ref_text": (
            "Glory be to the Father and to the Son and to the Holy Ghost; "
            "as it was in the beginning, is now, and ever shall be."
        ),
    },
    "lector": {
        "design": (
            "A clear, articulate male narrator in his forties, like a "
            "seasoned audiobook reader of classic literature. Warm but "
            "precise diction, moderate pace."
        ),
        "ref_text": (
            "In the beginning God created the heaven and the earth. And "
            "the earth was without form, and void; and darkness was upon "
            "the face of the deep."
        ),
    },
    # 'All' texts (creeds, canticles, Lord's Prayer) use the congregation
    # voice; a layered multi-voice mix is a v2 experiment.
    "all": {"alias": "congregation"},
}


# --- The congregation crowd -------------------------------------------------
# Individual parishioners, designed once (see `lucky crowd`) and mixed
# slightly out of sync by audio.py so congregation lines sound like an
# actual roomful of people rather than one voice. All speak the same
# reference line; variety comes from the designs.
CROWD_DIR = ASSETS / "crowd"
CROWD_REF_TEXT = (
    "Glory be to the Father and to the Son and to the Holy Ghost; "
    "as it was in the beginning, is now, and ever shall be."
)
CROWD_DESIGNS = {
    "parishioner-01": "An older male voice in his seventies, gravelly and "
                      "devout, praying aloud slowly from long habit.",
    "parishioner-02": "A middle-aged female voice, warm and steady, "
                      "speaking prayers in an even, unhurried unison cadence.",
    "parishioner-03": "A young adult female voice, soft and sincere, "
                      "slightly hushed, praying along attentively.",
    "parishioner-04": "A deep male voice in his forties, plainspoken and "
                      "solid, reciting in a measured, workmanlike way.",
    "parishioner-05": "An elderly female voice, gentle and a little frail, "
                      "but sure of every word of the prayer.",
    "parishioner-06": "A teenage male voice, quiet and slightly flat in "
                      "delivery, dutifully following the liturgy.",
    "parishioner-07": "A male voice in his thirties with a light Texas "
                      "drawl, relaxed but reverent, praying along evenly.",
}


# Which designed parishioners actually sing. Empty = all of them.
#
# This is a roster, not a delete: the WAVs are nondeterministic one-off
# designs and are not in git, so a removed one cannot be got back. Narrowing
# the roster is also the single biggest lever on render time — congregation
# lines are ~97% of all TTS calls, and each phrase unit is synthesized once
# per voice.
#
# Clarity note: the mixer puts the lead (the `congregation` cast voice) at
# gain 1.0 and every crowd voice at 0.55-0.85, then scales the sum by
# 1.6/len(parts). So a shorter roster does not merely thin the room — it
# raises the lead's share of the mix, which is where intelligibility
# actually comes from.
#
# Override per-run without editing this file:
#   LUCKY_CROWD=parishioner-01,parishioner-02,parishioner-04 python3 -m luckylutheran ...
#   LUCKY_CROWD=none    # no crowd at all; congregation lines go solo
CROWD_ROSTER: tuple[str, ...] = ()


def crowd_roster() -> tuple[str, ...]:
    env = os.environ.get("LUCKY_CROWD", "").strip()
    if not env:
        return CROWD_ROSTER
    if env.lower() == "none":
        return ("",)          # a roster that matches nothing
    return tuple(s.strip() for s in env.split(",") if s.strip())


def crowd_reference_wavs() -> list[Path]:
    if not CROWD_DIR.exists():
        return []
    wavs = sorted(CROWD_DIR.glob("*.wav"))
    roster = crowd_roster()
    if not roster:
        return wavs
    chosen = [w for w in wavs if w.stem in roster]
    missing = [n for n in roster if n and n not in {w.stem for w in wavs}]
    if missing:
        print(f"warning: crowd roster names no such voice: {', '.join(missing)}",
              file=sys.stderr)
    return chosen


def resolve_speaker(speaker: str) -> str:
    entry = VOICE_CAST.get(speaker, {})
    return entry.get("alias", speaker if speaker in VOICE_CAST else "liturgist")


def reference_wav(speaker: str) -> Path:
    return ASSETS / f"{resolve_speaker(speaker)}.wav"


class TTSEngine(abc.ABC):
    """Renders one segment of text in one speaker's voice to a WAV file."""

    name: str = "base"

    @abc.abstractmethod
    def synthesize(self, text: str, speaker: str, out_path: Path) -> Path | None:
        """Write audio for `text` to `out_path`; return the path, or None if
        this engine produces no audio (script-only mode). `speaker` may be a
        cast role (liturgist/congregation/lector/all) or an extra voice key
        from crowd_voices()."""

    def crowd_voices(self) -> list[str]:
        """Extra voice keys usable as `speaker` for crowd mixing (empty when
        this engine has no crowd support or no crowd WAVs exist)."""
        return []


class NullTTS(TTSEngine):
    """Script-only engine: produces no audio. Lets the whole pipeline run on
    machines without a speech model (transcript, metadata, feed)."""

    name = "null"

    def synthesize(self, text: str, speaker: str, out_path: Path) -> Path | None:
        return None


class Qwen3TTS(TTSEngine):
    """Qwen3-TTS CustomVoice engine with a cloned three-voice cast.

    Env overrides:
      LUCKY_QWEN_MODEL   (default Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice)
      LUCKY_TTS_DEVICE   (default cuda:0)
    """

    name = "qwen3"

    def __init__(self) -> None:
        import torch  # deferred: only needed on the TTS machine
        from qwen_tts import Qwen3TTSModel

        missing = [s for s in ("liturgist", "congregation", "lector")
                   if not (ASSETS / f"{s}.wav").exists()]
        if missing:
            raise FileNotFoundError(
                f"Missing reference voices {missing} in {ASSETS}. "
                "Run `lucky voices` once to design the cast, or drop in "
                "your own WAVs (and update ref_text in tts.py)."
            )

        self.model = Qwen3TTSModel.from_pretrained(
            os.environ.get("LUCKY_QWEN_MODEL",
                           "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"),
            device_map=os.environ.get("LUCKY_TTS_DEVICE", "cuda:0"),
            dtype=torch.bfloat16,
        )
        # Build each speaker's clone prompt once; reused across all segments.
        self._prompts = {
            speaker: self.model.create_voice_clone_prompt(
                ref_audio=str(ASSETS / f"{speaker}.wav"),
                ref_text=VOICE_CAST[speaker]["ref_text"],
            )
            for speaker in ("liturgist", "congregation", "lector")
        }
        for wav in crowd_reference_wavs():
            self._prompts[f"crowd/{wav.stem}"] = \
                self.model.create_voice_clone_prompt(
                    ref_audio=str(wav), ref_text=CROWD_REF_TEXT)

    def crowd_voices(self) -> list[str]:
        return sorted(k for k in self._prompts if k.startswith("crowd/"))

    def synth_array(self, text: str, speaker: str):
        """Render to (numpy_audio, sample_rate) — used by both the local
        engine path and the wintermute HTTP server."""
        key = speaker if speaker in self._prompts else resolve_speaker(speaker)
        wavs, sr = self.model.generate_voice_clone(
            text=text,
            language="English",
            voice_clone_prompt=self._prompts[key],
        )
        return wavs[0], sr

    def synthesize(self, text: str, speaker: str, out_path: Path) -> Path | None:
        import soundfile as sf

        wav, sr = self.synth_array(text, speaker)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(out_path), wav, sr)
        return out_path


def design_voice_cast(overwrite: bool = False) -> list[Path]:
    """One-time cast generation with the Qwen3-TTS VoiceDesign model."""
    import torch
    import soundfile as sf
    from qwen_tts import Qwen3TTSModel

    model = Qwen3TTSModel.from_pretrained(
        "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
        device_map=os.environ.get("LUCKY_TTS_DEVICE", "cuda:0"),
        dtype=torch.bfloat16,
    )
    ASSETS.mkdir(parents=True, exist_ok=True)
    written = []
    for speaker, cast in VOICE_CAST.items():
        if "alias" in cast:
            continue
        out = ASSETS / f"{speaker}.wav"
        if out.exists() and not overwrite:
            print(f"keep existing {out}")
            continue
        wavs, sr = model.generate_voice_design(
            text=cast["ref_text"],
            language="English",
            instruct=cast["design"],
        )
        sf.write(str(out), wavs[0], sr)
        written.append(out)
        print(f"designed {speaker}: {out}")
    return written


def design_crowd_via_gradio(url: str | None = None,
                            overwrite: bool = False) -> list[Path]:
    """Generate the parishioner reference WAVs through a running
    qwen-tts-demo serving the VoiceDesign model. One-time (per crowd)."""
    import json
    import urllib.request

    url = (url or os.environ.get("LUCKY_TTS_URL",
                                 "http://192.168.1.51:8000")).rstrip("/")
    try:
        with urllib.request.urlopen(f"{url}/config", timeout=10) as r:
            config = json.loads(r.read().decode("utf-8"))
    except OSError as exc:
        raise ConnectionError(
            f"Gradio demo not reachable at {url} ({exc}). On wintermute: "
            "qwen-tts-demo Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign "
            "--ip 0.0.0.0 --port 8000") from exc
    banner = next((c["props"].get("value", "") for c in config["components"]
                   if c["type"] == "markdown"), "")
    if "voice_design" not in banner:
        raise RuntimeError(
            "The demo at {} is not serving the VoiceDesign model (banner: "
            "{!r}). Restart it with Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign, "
            "design the crowd, then switch back to Base.".format(
                url, " ".join(banner.split())))

    CROWD_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for name, design in CROWD_DESIGNS.items():
        out = CROWD_DIR / f"{name}.wav"
        if out.exists() and not overwrite:
            print(f"keep existing {out.name}")
            continue
        result = _gradio_call(url, "/run_voice_design",
                              [CROWD_REF_TEXT, "English", design])
        with urllib.request.urlopen(result[0]["url"], timeout=120) as resp:
            out.write_bytes(resp.read())
        written.append(out)
        print(f"designed {name}: {out}")
    return written


class Qwen3RemoteTTS(TTSEngine):
    """Client for the lucky-lutheran TTS server running on wintermute
    (see server.py). Keeps the model and GPU over there; this machine only
    sends text and receives WAV bytes. (No crowd support — the crowd is
    rendered via the gradio or qwen3 engines.)

    Env: LUCKY_TTS_URL (default http://192.168.1.51:8765)
    """

    name = "remote"

    def __init__(self) -> None:
        import json
        import urllib.request

        self.url = os.environ.get("LUCKY_TTS_URL",
                                  "http://192.168.1.51:8765").rstrip("/")
        try:
            with urllib.request.urlopen(f"{self.url}/health", timeout=10) as r:
                health = json.loads(r.read().decode("utf-8"))
        except OSError as exc:
            raise ConnectionError(
                f"TTS server not reachable at {self.url} ({exc}). On "
                "wintermute: python3 -m luckylutheran serve"
            ) from exc
        print(f"TTS server ok: {health.get('model', '?')} on "
              f"{health.get('device', '?')}")

    def synthesize(self, text: str, speaker: str, out_path: Path) -> Path | None:
        import json
        import urllib.request

        req = urllib.request.Request(
            f"{self.url}/synthesize",
            data=json.dumps({"text": text, "speaker": speaker}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        # Long segments (a full psalm) can take a while on the GPU.
        with urllib.request.urlopen(req, timeout=600) as resp:
            wav_bytes = resp.read()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(wav_bytes)
        return out_path


class GradioDemoTTS(TTSEngine):
    """Client for the official `qwen-tts-demo` Gradio server (Base model)
    running on wintermute:

        qwen-tts-demo Qwen/Qwen3-TTS-12Hz-1.7B-Base --ip 0.0.0.0 --port 8000

    On startup, each cast member's reference WAV in assets/voices/ is
    uploaded once and turned into a server-side voice prompt via
    /save_prompt; each segment is then rendered with /load_prompt_and_gen.
    Stdlib only (multipart upload + Gradio's SSE call protocol).

    Env: LUCKY_TTS_URL (default http://192.168.1.51:8000)
    """

    name = "gradio"

    def __init__(self) -> None:
        import json
        import urllib.request

        self.url = os.environ.get("LUCKY_TTS_URL",
                                  "http://192.168.1.51:8000").rstrip("/")
        try:
            with urllib.request.urlopen(f"{self.url}/config", timeout=10) as r:
                json.loads(r.read().decode("utf-8"))
        except OSError as exc:
            raise ConnectionError(
                f"Gradio demo not reachable at {self.url} ({exc}). On "
                "wintermute: qwen-tts-demo Qwen/Qwen3-TTS-12Hz-1.7B-Base "
                "--ip 0.0.0.0 --port 8000"
            ) from exc

        missing = [s for s in ("liturgist", "congregation", "lector")
                   if not (ASSETS / f"{s}.wav").exists()]
        if missing:
            raise FileNotFoundError(
                f"Missing reference voices {missing} in {ASSETS}. Generate "
                "them once via the VoiceDesign demo (see README) or record "
                "your own."
            )

        self._voice_files: dict[str, str] = {}
        for speaker in ("liturgist", "congregation", "lector"):
            self._save_prompt(speaker, ASSETS / f"{speaker}.wav",
                              VOICE_CAST[speaker]["ref_text"])
        for wav in crowd_reference_wavs():
            self._save_prompt(f"crowd/{wav.stem}", wav, CROWD_REF_TEXT)

    def _save_prompt(self, key: str, wav: Path, ref_text: str) -> None:
        uploaded = self._upload(wav)
        result = self._call("/save_prompt", [
            {"path": uploaded, "meta": {"_type": "gradio.FileData"}},
            ref_text,
            False,
        ])
        self._voice_files[key] = result[0]["path"]
        print(f"voice prompt ready: {key}")

    def crowd_voices(self) -> list[str]:
        return sorted(k for k in self._voice_files if k.startswith("crowd/"))

    def synthesize(self, text: str, speaker: str, out_path: Path) -> Path | None:
        import urllib.request

        key = speaker if speaker in self._voice_files else resolve_speaker(speaker)
        result = self._call("/load_prompt_and_gen", [
            {"path": self._voice_files[key],
             "meta": {"_type": "gradio.FileData"}},
            text,
            "English",
        ])
        audio_url = result[0]["url"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(audio_url, timeout=120) as resp:
            out_path.write_bytes(resp.read())
        return out_path

    def _upload(self, path: Path) -> str:
        return _gradio_upload(self.url, path)

    def _call(self, endpoint: str, data: list) -> list:
        return _gradio_call(self.url, endpoint, data)


# -- Gradio protocol helpers (stdlib) -----------------------------------------

def _gradio_upload(url: str, path: Path) -> str:
    """Multipart-upload a file; return its server-side path."""
    import json
    import urllib.request
    import uuid

    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="files"; '
        f'filename="{path.name}"\r\n'
        f"Content-Type: audio/wav\r\n\r\n"
    ).encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{url}/gradio_api/upload", data=body,
        headers={"Content-Type":
                 f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))[0]


def _gradio_call(url: str, endpoint: str, data: list) -> list:
    """POST a Gradio call, follow its SSE stream, return the result."""
    import json
    import urllib.request

    req = urllib.request.Request(
        f"{url}/gradio_api/call{endpoint}",
        data=json.dumps({"data": data}).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        event_id = json.loads(resp.read().decode("utf-8"))["event_id"]

    event = None
    with urllib.request.urlopen(
            f"{url}/gradio_api/call{endpoint}/{event_id}",
            timeout=600) as stream:
        for raw in stream:
            line = raw.decode("utf-8").strip()
            if line.startswith("event:"):
                event = line.split(":", 1)[1].strip()
            elif line.startswith("data:") and event == "complete":
                return json.loads(line.split(":", 1)[1])
            elif line.startswith("data:") and event == "error":
                raise RuntimeError(
                    f"Gradio {endpoint} failed: {line[5:].strip()}")
    raise RuntimeError(f"Gradio {endpoint}: stream ended without result")


ENGINES = {"null": NullTTS, "qwen3": Qwen3TTS, "remote": Qwen3RemoteTTS,
           "gradio": GradioDemoTTS}


def get_engine(name: str) -> TTSEngine:
    try:
        return ENGINES[name]()
    except KeyError:
        raise ValueError(f"Unknown TTS engine {name!r}; known: {list(ENGINES)}")
