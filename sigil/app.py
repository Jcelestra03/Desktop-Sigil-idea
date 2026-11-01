"""Main run loop: hotkey -> overlay -> recognizer -> action."""

from __future__ import annotations

import queue

from . import actions, store
from .hotkey import DEFAULT_HOTKEY, HotkeyListener
from .overlay import Overlay, make_root
from .recognizer import Stroke, recognize

POLL_MS = 50


class SigilApp:
    def __init__(self, hotkey: str = DEFAULT_HOTKEY) -> None:
        self.events: queue.Queue[str] = queue.Queue()
        self.hotkey = HotkeyListener(lambda: self.events.put("summon"), hotkey)
        self.root = make_root()
        self.overlay_open = False

    def run(self) -> None:
        self.hotkey.start()
        print(f"Desktop Sigil is listening. Press {self.hotkey.hotkey.title()} to draw. "
              "Ctrl+C here to quit.")
        self.root.after(POLL_MS, self._poll)
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.hotkey.stop()

    def _poll(self) -> None:
        # Runs on the main thread, so it is safe to touch tkinter here.
        try:
            while True:
                if self.events.get_nowait() == "summon":
                    self.summon()
        except queue.Empty:
            pass
        self.root.after(POLL_MS, self._poll)

    def summon(self) -> None:
        if self.overlay_open:
            return
        sigils = store.load()  # reload so sigils added while running are picked up
        if not sigils:
            print('No sigils yet. Add one with: python -m sigil add "Name" --url https://...')
        self.overlay_open = True
        Overlay(self.root, "✦", lambda strokes: self._cast(strokes, sigils))

    def _cast(self, strokes: list[Stroke] | None, sigils: list[store.Sigil]) -> str | None:
        self.overlay_open = False
        if strokes is None:
            return None
        match = recognize(strokes, sigils)
        if match is None:
            print("No sigil recognized.")
            return "No sigil recognized"
        sigil = match.sigil
        print(f"Cast {sigil.name} (score {match.score:.2f}) -> {actions.describe(sigil.action)}")
        try:
            actions.run(sigil.action)
        except OSError as e:
            print(f"  Couldn't open it: {e}")
            return f"Couldn't open {sigil.name}"
        return f"✦ {sigil.name}"


def run(hotkey: str = DEFAULT_HOTKEY) -> None:
    SigilApp(hotkey).run()


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
