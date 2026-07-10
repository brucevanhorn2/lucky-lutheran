"""TTS server for wintermute.

Loads Qwen3-TTS once, builds the three-voice cast's clone prompts, and
serves synthesis over a minimal JSON/WAV HTTP API (stdlib only, no
FastAPI/gradio). The lucky-lutheran pipeline on any other machine uses it
via `--engine remote` (LUCKY_TTS_URL).

    python3 -m luckylutheran serve [--port 8765] [--ip 0.0.0.0]

Endpoints:
  GET  /health      -> {"status": "ok", "model": ..., "device": ...}
  POST /synthesize  {"text": "...", "speaker": "liturgist|congregation|lector|all"}
                    -> audio/wav bytes

If the reference voice WAVs are missing at startup, the VoiceDesign model is
loaded first to generate the cast (then released) before the CustomVoice
model is loaded — so a fresh install needs no manual steps.

Requests are handled serially, which is what we want: one GPU, one job.
This is a trusted-LAN service; do not expose it to the internet.
"""

from __future__ import annotations

import io
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from luckylutheran import tts


def _ensure_cast() -> None:
    missing = [s for s in ("liturgist", "congregation", "lector")
               if not (tts.ASSETS / f"{s}.wav").exists()]
    if not missing:
        return
    print(f"reference voices missing ({missing}); designing cast first...")
    tts.design_voice_cast()
    # Release the VoiceDesign model before loading CustomVoice.
    import gc
    import torch
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


class _Handler(BaseHTTPRequestHandler):
    engine: tts.Qwen3TTS  # set on the class before serving

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        if self.path != "/health":
            self.send_error(404)
            return
        body = json.dumps({
            "status": "ok",
            "model": os.environ.get("LUCKY_QWEN_MODEL",
                                    "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"),
            "device": os.environ.get("LUCKY_TTS_DEVICE", "cuda:0"),
        }).encode("utf-8")
        self._respond(200, "application/json", body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/synthesize":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            text = payload["text"]
            speaker = payload.get("speaker", "liturgist")
        except (ValueError, KeyError) as exc:
            self.send_error(400, f"bad request: {exc}")
            return

        try:
            import soundfile as sf
            wav, sr = self.engine.synth_array(text, speaker)
            buf = io.BytesIO()
            sf.write(buf, wav, sr, format="WAV")
        except Exception as exc:  # surface synth errors to the client
            self.send_error(500, f"synthesis failed: {exc}")
            return
        self._respond(200, "audio/wav", buf.getvalue())

    def _respond(self, code: int, ctype: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.address_string()}] {fmt % args}")


def run(ip: str = "0.0.0.0", port: int = 8765) -> None:
    _ensure_cast()
    print("loading CustomVoice model and building clone prompts...")
    _Handler.engine = tts.Qwen3TTS()
    server = HTTPServer((ip, port), _Handler)
    print(f"lucky-lutheran TTS server listening on http://{ip}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
