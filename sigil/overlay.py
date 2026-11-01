"""Full-screen translucent window to draw a sigil on.

The overlay only collects strokes. Whoever opens it decides what the strokes mean
through the on_done callback, which may return a short message to flash before closing.
"""

from __future__ import annotations

import ctypes
import tkinter as tk
from typing import Callable

from .recognizer import Stroke

BG = "#0b0a1a"
INK = "#f5c96a"
GLOW = "#6b4f1d"
TEXT = "#e9e3ff"
HINT = "#8c86a8"

IDLE_MS = 800  # pause after the last stroke before the drawing is cast
FLASH_MS = 700


def make_root() -> tk.Tk:
    """Hidden Tk root. Call once, before any overlay."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # crisp lines, real pixel coords
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    root.withdraw()
    return root


class Overlay:
    def __init__(
        self,
        root: tk.Tk,
        prompt: str,
        on_done: Callable[[list[Stroke] | None], str | None],
        hint: str = "Draw your sigil  ·  Enter to cast  ·  Esc to cancel",
    ):
        self.on_done = on_done
        self.strokes: list[Stroke] = []
        self._idle_job: str | None = None
        self._closed = False

        win = self.win = tk.Toplevel(root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-alpha", 0.72)
        width, height = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"{width}x{height}+0+0")

        canvas = self.canvas = tk.Canvas(
            win, bg=BG, highlightthickness=0, cursor="crosshair", width=width, height=height
        )
        canvas.pack(fill="both", expand=True)
        self.prompt_id = canvas.create_text(
            width / 2, height * 0.08, text=prompt, fill=TEXT, font=("Segoe UI", 26)
        )
        canvas.create_text(width / 2, height * 0.94, text=hint, fill=HINT, font=("Segoe UI", 13))

        canvas.bind("<ButtonPress-1>", self._press)
        canvas.bind("<B1-Motion>", self._drag)
        canvas.bind("<ButtonRelease-1>", self._release)
        canvas.bind("<Button-3>", lambda e: self._finish(cancel=True))
        win.bind("<Escape>", lambda e: self._finish(cancel=True))
        win.bind("<Return>", lambda e: self._finish())

        win.lift()
        win.after(30, win.focus_force)

    def _press(self, event: tk.Event) -> None:
        self._cancel_idle()
        self.strokes.append([(event.x, event.y)])

    def _drag(self, event: tk.Event) -> None:
        if not self.strokes:
            return
        stroke = self.strokes[-1]
        x0, y0 = stroke[-1]
        if abs(event.x - x0) + abs(event.y - y0) < 2:
            return
        stroke.append((event.x, event.y))
        self.canvas.create_line(x0, y0, event.x, event.y, fill=GLOW, width=14, capstyle="round")
        self.canvas.create_line(x0, y0, event.x, event.y, fill=INK, width=5, capstyle="round")

    def _release(self, event: tk.Event) -> None:
        self._cancel_idle()
        self._idle_job = self.win.after(IDLE_MS, self._finish)

    def _cancel_idle(self) -> None:
        if self._idle_job is not None:
            self.win.after_cancel(self._idle_job)
            self._idle_job = None

    def _finish(self, cancel: bool = False) -> None:
        if self._closed:
            return
        self._closed = True
        self._cancel_idle()
        strokes = [s for s in self.strokes if len(s) > 1]
        message = self.on_done(None if cancel or not strokes else strokes)
        if message:
            self.canvas.itemconfigure(self.prompt_id, text=message)
            self.win.after(FLASH_MS, self.win.destroy)
        else:
            self.win.destroy()
