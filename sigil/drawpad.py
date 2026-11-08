"""Drawing canvas used in the sigil editor, Paint-style pens, and thumbnail drawing.

A pen only changes how a stroke looks. The recognizer only ever sees the points, so
switching pens, sizes or colors never changes which sigil a drawing matches.
"""

from __future__ import annotations

import math
import random
import tkinter as tk
from typing import Callable

from .overlay import INK
from .recognizer import Point, Stroke
from .themes import blend

PENS = {
    "pen": "Pen",
    "brush": "Brush",
    "calligraphy": "Calligraphy",
    "quill": "Quill",
    "marker": "Marker",
    "spray": "Spray",
    "glow": "Glow",
}
DEFAULT_STYLE = {"pen": "pen", "size": 6, "color": None}  # color None = the theme's ink
MIN_SIZE, MAX_SIZE = 1, 30


def render_stroke(c: tk.Canvas, pts: list[Point], pen: str, size: float, color: str, bg: str,
                  tags: tuple[str, ...] = (), taper: bool = True) -> None:
    """Draw one stroke with a pen. taper=False is used while the stroke is still being drawn
    (the brush can't know where it will end); the finished stroke is redrawn with taper."""
    if len(pts) < 2:
        return
    size = max(1.0, size)
    flat = [v for p in pts for v in p]
    n = len(pts)

    if pen == "marker":
        c.create_line(*flat, fill=blend(color, bg, .22), width=size * 2.2, capstyle="projecting",
                      joinstyle="miter", tags=tags)
    elif pen == "glow":
        c.create_line(*flat, fill=blend(color, bg, .78), width=size * 3.2, capstyle="round",
                      joinstyle="round", smooth=True, tags=tags)
        c.create_line(*flat, fill=blend(color, bg, .45), width=size * 1.8, capstyle="round",
                      joinstyle="round", smooth=True, tags=tags)
        c.create_line(*flat, fill=blend(color, "#ffffff", .35), width=max(1, size * .7),
                      capstyle="round", joinstyle="round", smooth=True, tags=tags)
    elif pen == "brush":
        for i in range(n - 1):
            t = (i + .5) / (n - 1)
            k = .25 + .75 * math.sin(math.pi * t) if taper else .85
            c.create_line(*pts[i], *pts[i + 1], fill=color, width=max(1, size * 1.7 * k),
                          capstyle="round", tags=tags)
    elif pen == "calligraphy":
        # a flat nib held at 45 degrees: thick one way, thin the other
        nx, ny = size * .55, -size * .55
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            c.create_polygon(x0 + nx, y0 + ny, x1 + nx, y1 + ny, x1 - nx, y1 - ny, x0 - nx, y0 - ny,
                             fill=color, outline=color, tags=tags)
    elif pen == "quill":
        # ink thins out when you move fast, and pools where the nib touches down and lifts
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            d = math.hypot(x1 - x0, y1 - y0)
            c.create_line(x0, y0, x1, y1, fill=color, width=max(1, size * 1.4 / (1 + d / 10)),
                          capstyle="round", tags=tags)
        ends = (pts[0], pts[-1]) if taper else (pts[0],)
        for x, y in ends:
            r = size * .55
            c.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="", tags=tags)
    elif pen == "spray":
        rng = random.Random(int(pts[0][0] * 7 + pts[0][1] * 13))
        dot = max(.6, size * .12)
        for x, y in pts:
            for _ in range(6):
                dx, dy = rng.gauss(0, size * .9), rng.gauss(0, size * .9)
                c.create_oval(x + dx - dot, y + dy - dot, x + dx + dot, y + dy + dot,
                              fill=color, outline="", tags=tags)
    else:  # "pen"
        c.create_line(*flat, fill=color, width=size, capstyle="round", joinstyle="round",
                      smooth=True, tags=tags)


class DrawPad(tk.Canvas):
    def __init__(self, master: tk.Misc, size: int = 320, bg: str = "#0b0a1a",
                 guide: str = "#2a2650", on_change: Callable[[], None] | None = None,
                 ink: str = INK, style: dict | None = None):
        super().__init__(master, width=size, height=size, bg=bg, highlightthickness=0,
                         cursor="crosshair")
        self.strokes: list[Stroke] = []
        self.on_change = on_change
        self.bg, self.ink = bg, ink
        self.style = dict(style or DEFAULT_STYLE)
        pad = size * 0.06
        self.create_oval(pad, pad, size - pad, size - pad, outline=guide, width=2, dash=(4, 6))
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<ButtonRelease-1>", self._release)

    @property
    def drawing(self) -> list[Stroke]:
        return [s for s in self.strokes if len(s) > 1]

    @property
    def color(self) -> str:
        return self.style.get("color") or self.ink

    def set_style(self, style: dict) -> None:
        """Change the pen; the whole drawing on the pad is redrawn with it."""
        self.style = dict(style)
        for i in range(len(self.strokes)):
            self._render(i)

    def clear(self) -> None:
        self.strokes = []
        self.delete("ink")
        self._changed()

    def undo(self) -> None:
        if self.strokes:
            self.delete(f"s{len(self.strokes) - 1}")
            self.strokes.pop()
            self._changed()

    def _changed(self) -> None:
        if self.on_change:
            self.on_change()

    def _render(self, i: int, taper: bool = True) -> None:
        self.delete(f"s{i}")
        render_stroke(self, self.strokes[i], self.style["pen"], self.style["size"], self.color,
                      self.bg, ("ink", f"s{i}"), taper)

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
        i = len(self.strokes) - 1
        render_stroke(self, [(x0, y0), (event.x, event.y)], self.style["pen"], self.style["size"],
                      self.color, self.bg, ("ink", f"s{i}"), taper=False)

    def _release(self, event: tk.Event) -> None:
        if self.strokes and len(self.strokes[-1]) > 1:
            self._render(len(self.strokes) - 1)  # redraw the finished stroke properly
        self._changed()


def draw_strokes(canvas: tk.Canvas, strokes: list[Stroke], x: float, y: float, w: float,
                 h: float, color: str = INK, width: int = 2, style: dict | None = None,
                 bg: str = "#000000") -> None:
    """Draw a sigil scaled to fit the box (x, y, w, h), keeping its proportions. With a
    style, it's drawn with that pen (sizes scaled down, but never thinner than width)."""
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
        pts = [((px - min_x) * scale + off_x, (py - min_y) * scale + off_y) for px, py in stroke]
        if style:
            size = max(width * .7, style.get("size", 6) * scale * .8)
            render_stroke(canvas, pts, style.get("pen", "pen"), size,
                          style.get("color") or color, bg)
        else:
            canvas.create_line(*[v for p in pts for v in p], fill=color, width=width,
                               capstyle="round", joinstyle="round")
