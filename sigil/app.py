"""Main run loop: hotkey -> overlay -> recognizer -> action."""

from __future__ import annotations

import queue
import tkinter as tk
from typing import Callable

from . import actions, store
from .hotkey import DEFAULT_HOTKEY, HotkeyListener, pretty
from .overlay import Overlay, make_root
from .recognizer import Stroke, recognize

POLL_MS = 50


class SigilApp:
    """Hotkey + overlay + recognizer. Used headless by `run` and by the Sigil Book window."""

    def __init__(self, root: tk.Tk | None = None,
                 on_status: Callable[[str], None] | None = None) -> None:
        self.events: queue.Queue[str] = queue.Queue()
        self.hotkey: HotkeyListener | None = None
        self.root = root or make_root()
        self.on_status = on_status or print
        self.overlay_open = False
        self.root.after(POLL_MS, self._poll)

    def set_hotkey(self, hotkey: str) -> None:
        """Listen for a new hotkey. Raises ValueError (bad name) or OSError (already in use);
        on failure the previous hotkey keeps working."""
        listener = HotkeyListener(lambda: self.events.put("summon"), hotkey)
        old = self.hotkey
        if old:
            old.stop()
        try:
            listener.start()
        except OSError:
            if old:
                self.hotkey = HotkeyListener(old.callback, old.hotkey)
                self.hotkey.start()
            raise
        self.hotkey = listener

    def stop(self) -> None:
        if self.hotkey:
            self.hotkey.stop()

    def run(self, hotkey: str = DEFAULT_HOTKEY) -> None:
        self.set_hotkey(hotkey)
        print(f"Desktop Sigil is listening. Press {pretty(hotkey)} to draw. Ctrl+C here to quit.")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def _poll(self) -> None:
        # Runs on the main thread, so it is safe to touch tkinter here.
        try:
            while True:
                if self.events.get_nowait() == "summon":
                    self.summon()
        except queue.Empty:
            pass
        self.root.after(POLL_MS, self._poll)

    def _can_open(self) -> bool:
        if self.overlay_open:
            return False
        if self.root.grab_current() is not None:
            # A dialog (e.g. the sigil editor) holds the mouse; an overlay would get no input
            self.on_status("Finish or close the open dialog first.")
            return False
        return True

    def practice(self, prompt: str,
                 on_done: Callable[[list[Stroke] | None], str | None]) -> bool:
        """Open the overlay for a practice drawing (the tutorial). on_done gets the strokes
        (None if cancelled) and may return a message to flash. Nothing is cast."""
        if not self._can_open():
            return False
        self.overlay_open = True

        def done(strokes: list[Stroke] | None) -> str | None:
            self.overlay_open = False
            return on_done(strokes)

        Overlay(self.root, prompt, done,
                hint="Practice: nothing will open  ·  Enter to cast  ·  Esc to cancel")
        return True

    def summon(self, dry_run: bool = False) -> None:
        """Open the overlay. With dry_run, report what would open instead of opening it."""
        if not self._can_open():
            return
        sigils = store.load()  # reload so sigils added while running are picked up
        if not sigils:
            self.on_status("No sigils yet. Add one first.")
        self.overlay_open = True
        prompt = "Test a sigil (nothing will open)" if dry_run else "✦"
        Overlay(self.root, prompt, lambda strokes: self._cast(strokes, sigils, dry_run))

    def _cast(self, strokes: list[Stroke] | None, sigils: list[store.Sigil],
              dry_run: bool) -> str | None:
        self.overlay_open = False
        if strokes is None:
            return None
        match = recognize(strokes, sigils)
        if match is None:
            self.on_status("No sigil recognized.")
            return "No sigil recognized"
        sigil = match.sigil
        if dry_run:
            self.on_status(f"That's {sigil.name} ({match.score:.0%} match). Nothing was opened.")
            return f"{sigil.name}  ·  {match.score:.0%} match"
        self.on_status(f"Cast {sigil.name} ({match.score:.0%} match).")
        try:
            actions.run(sigil.action)
        except OSError as e:
            self.on_status(f"Couldn't open {sigil.name}: {e.strerror or e}")
            return f"Couldn't open {sigil.name}"
        return f"✦ {sigil.name}"


def run(hotkey: str = DEFAULT_HOTKEY) -> None:
    SigilApp().run(hotkey)


def draw_once(prompt: str, hint: str | None = None) -> list[Stroke] | None:
    """Open one overlay, block until it closes, and return the strokes (None if cancelled)."""
    root = make_root()
    result: list[list[Stroke] | None] = [None]

    def done(strokes: list[Stroke] | None) -> str | None:
        result[0] = strokes
        root.after(10, root.quit)
        return None

    kwargs = {"hint": hint} if hint else {}
    Overlay(root, prompt, done, **kwargs)
    root.mainloop()
    root.destroy()
    return result[0]


def draw_many(prompts: list[str], hint: str | None = None) -> list[list[Stroke]] | None:
    """Draw several times in a row (e.g. samples for a new sigil). None if any is cancelled."""
    root = make_root()
    drawings: list[list[Stroke]] = []
    cancelled = [False]

    def open_next() -> None:
        if len(drawings) == len(prompts) or cancelled[0]:
            root.quit()
            return
        kwargs = {"hint": hint} if hint else {}
        Overlay(root, prompts[len(drawings)], done, **kwargs)

    def done(strokes: list[Stroke] | None) -> str | None:
        if strokes is None:
            cancelled[0] = True
            root.after(10, open_next)
            return None
        drawings.append(strokes)
        root.after(800, open_next)  # after the "Got it" flash
        return "Got it"

    root.after(0, open_next)
    root.mainloop()
    root.destroy()
    return None if cancelled[0] else drawings
