"""Render progress display.

The render loop used to print one line per chunk, which on a 30-day batch is
tens of thousands of lines and tells you almost nothing: you cannot see how
far along you are, and you cannot tell a slow crowd render from a hung one.

Two things this fixes.

**Progress is weighted by TTS calls, not segments.** A congregation line is
synthesized once per voice per phrase unit — eight voices over five phrases is
forty calls, against one for a liturgist line of the same length. A bar driven
by segment count therefore lurches: it sits still through the Creed and then
jumps four segments during the versicles. Counting calls makes the bar move at
a constant rate and makes the ETA mean something.

**It adapts to where it is running.** Interactively you get one live line that
rewrites itself. Redirected to a log — which is how overnight batches actually
run — it degrades to periodic plain lines, because a log full of carriage
returns and escape codes is worse than what we had. Nothing here writes an
escape sequence unless stdout is a terminal.

The ETA is computed from *uncached* work only. A resumed build skips thousands
of existing WAVs in the first seconds; billing those to the average would
predict a finish time that is wildly optimistic and then slides backwards for
an hour.
"""

from __future__ import annotations

import shutil
import sys
import time

BAR_WIDTH = 28
MIN_REDRAW = 0.08          # seconds between live redraws
LOG_EVERY = 25.0           # seconds between lines when not a terminal


def _fmt(seconds: float) -> str:
    if seconds < 0 or seconds != seconds:      # negative or NaN
        return "--:--"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


class Render:
    """Progress for one episode's render.

    `total` is the expected number of TTS calls. Call `step()` as each lands,
    with `cached=True` when it cost nothing. `note()` emits a line that
    survives above the live bar. `finish()` closes it out.
    """

    def __init__(self, title: str, total: int, prefix: str = "",
                 stream=None) -> None:
        self.title = title
        self.total = max(total, 1)
        self.prefix = prefix
        self.stream = stream or sys.stdout
        self.live = bool(getattr(self.stream, "isatty", lambda: False)())
        self.done = 0
        self.worked = 0                 # uncached calls, for the rate
        self.cached = 0
        self.label = ""
        self.started = time.monotonic()
        self._work_started: float | None = None
        self._last_draw = 0.0
        self._open = False

    # -- lifecycle ---------------------------------------------------------

    def start(self) -> None:
        head = f"{self.prefix}{self.title}  ({self.total:,} voice renders)"
        self._writeln(head)
        # Draw the empty bar immediately when live, so something is on screen
        # before the first synthesis call returns. In a log that same draw is
        # just a 0.0% line repeating what the header said, so skip it.
        if self.live:
            self._draw(force=True)

    def finish(self, outcome: str = "") -> None:
        self._clear()
        elapsed = time.monotonic() - self.started
        bits = [f"{self.done:,} renders in {_fmt(elapsed)}"]
        if self.cached:
            bits.append(f"{self.cached:,} cached")
        line = f"  {' · '.join(bits)}"
        if outcome:
            line += f" → {outcome}"
        self._writeln(line)
        self._open = False

    # -- updates -----------------------------------------------------------

    def step(self, n: int = 1, label: str | None = None,
             cached: bool = False) -> None:
        if label is not None:
            self.label = label
        self.done += n
        if cached:
            self.cached += n
        else:
            if self._work_started is None:
                self._work_started = time.monotonic()
            self.worked += n
        self._draw()

    def note(self, text: str) -> None:
        """A durable line. Scrolls above the bar rather than being overwritten."""
        self._clear()
        self._writeln(f"  {text}")
        self._draw(force=True)

    # -- rendering ---------------------------------------------------------

    def eta(self) -> float:
        """Seconds remaining, from the rate of *uncached* work only."""
        if self.worked < 3 or self._work_started is None:
            return float("nan")
        rate = self.worked / max(time.monotonic() - self._work_started, 1e-6)
        remaining = self.total - self.done
        # Assume what's left is as cacheable as what's been seen so far.
        hit = self.cached / max(self.done, 1)
        return (remaining * (1 - hit)) / rate if rate else float("nan")

    def _draw(self, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self._last_draw < (
                MIN_REDRAW if self.live else LOG_EVERY):
            return
        self._last_draw = now
        frac = min(self.done / self.total, 1.0)
        pct = f"{frac * 100:5.1f}%"
        elapsed = _fmt(now - self.started)
        remaining = self.eta()
        # Until enough uncached work has been timed there is no honest
        # estimate; say so rather than printing a confident wrong number.
        eta = f"{_fmt(remaining)} left" if remaining == remaining else "estimating"

        if not self.live:
            # Log mode: a plain, greppable line, occasionally.
            self._writeln(f"  {pct}  {self.done:,}/{self.total:,}  "
                          f"elapsed {elapsed}  {eta}  {self.label}")
            return

        filled = int(BAR_WIDTH * frac)
        bar = "█" * filled + "·" * (BAR_WIDTH - filled)
        head = f"  {bar} {pct}  {elapsed} / {eta}  "
        room = max(shutil.get_terminal_size((100, 24)).columns - len(head) - 1, 8)
        label = self.label if len(self.label) <= room else self.label[:room - 1] + "…"
        self.stream.write(f"\r\033[K{head}{label}")
        self.stream.flush()
        self._open = True

    def _clear(self) -> None:
        if self.live and self._open:
            self.stream.write("\r\033[K")
            self.stream.flush()
            self._open = False

    def _writeln(self, text: str) -> None:
        self._clear()
        self.stream.write(text + "\n")
        self.stream.flush()


class Silent(Render):
    """No output at all — for tests and script-only builds."""

    def __init__(self) -> None:
        super().__init__("", 1)
        self.live = False

    def start(self) -> None: ...
    def finish(self, outcome: str = "") -> None: ...
    def note(self, text: str) -> None: ...
    def _draw(self, force: bool = False) -> None: ...
