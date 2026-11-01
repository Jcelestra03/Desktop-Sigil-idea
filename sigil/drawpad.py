"""A small canvas to draw sigils on inside a window, and a helper to draw thumbnails."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from .overlay import GLOW, INK
from .recognizer import Stroke


class DrawPad(tk.Canvas):
    def __init__(self, master: tk.Misc, size: int = 320, bg: str = "#0b0a1a",
                 guide: str = "#2a2650", on_change: Callable[[], None] | None = None):
        super().__init__(master, width=size, height=size, bg=bg, highlightthickness=0,
                         cursor="crosshair")
        self.strokes: list[Stroke] = []
        self.on_change = on_change
        pad = size * 0.08
        self.create_oval(pad, pad, size - pad, size - pad, outline=guide, width=2, dash=(4, 6))
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<ButtonRelease-1>", lambda e: self.on_change and self.on_change())

    @property
    def drawing(self) -> list[Stroke]:
        return [s for s in self.strokes if len(s) > 1]

    def clear(self) -> None:
        self.strokes = []
        self.delete("ink")
        if self.on_change:
            self.on_change()

    def _press(self, event: tk.Event) -> None:
        self.strokes.append([(event.x, event.y)])

    def _drag(self, event: tk.Event) -> None:
        if not self.strokes:
            return
        stroke = self.strokes[-1]
        x0, y0 = stroke[-1]
        if abs(event.x - x0) + abs(event.y - y0) < 2:
            return
        stroke.append((event.x, event.y))
        self.create_line(x0, y0, event.x, event.y, fill=GLOW, width=10, capstyle="round", tags="ink")
        self.create_line(x0, y0, event.x, event.y, fill=INK, width=4, capstyle="round", tags="ink")


def draw_strokes(canvas: tk.Canvas, strokes: list[Stroke], x: float, y: float, w: float,
                 h: float, color: str = INK, width: int = 2) -> None:
    """Draw a sigil scaled to fit the box (x, y, w, h), keeping its proportions."""
    points = [p for s in strokes for p in s]
    if not points:
        return
    min_x, max_x = min(p[0] for p in points), max(p[0] for p in points)
    min_y, max_y = min(p[1] for p in points), max(p[1] for p in points)
    scale = min(w / max(max_x - min_x, 1), h / max(max_y - min_y, 1))
    off_x = x + (w - (max_x - min_x) * scale) / 2
    off_y = y + (h - (max_y - min_y) * scale) / 2
    for stroke in strokes:
        if len(stroke) < 2:
            continue
        flat = [c for px, py in stroke
                for c in ((px - min_x) * scale + off_x, (py - min_y) * scale + off_y)]
        canvas.create_line(*flat, fill=color, width=width, capstyle="round", joinstyle="round")
