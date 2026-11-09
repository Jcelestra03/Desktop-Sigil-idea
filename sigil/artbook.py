"""The painted grimoires (Candlelight, Midnight): show the right-size picture and say where
its pages are, so the Sigil Book can write on them.

The pictures are made ahead of time by tools/render_art.py in a few scales of a 1160×760
design, each with extra desk around the book. Here the biggest scale that fits the window
is centered on the canvas; the canvas background is the color the picture fades to at
its edges, so a window wider than the picture shows no seam.
"""

from __future__ import annotations

import json
import os
import tkinter as tk
from functools import lru_cache
from pathlib import Path

from .grimoire import Layout

ART = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "assets" / "grimoire"
PAD = 40    # text inset from the page edges, in design pixels


@lru_cache(maxsize=1)
def info() -> dict:
    return json.loads((ART / "art.json").read_text(encoding="utf-8"))


def picture(art: str, scale: float) -> Path:
    return ART / f"{art}@{scale}.png"


def scale_for(w: int, h: int) -> float:
    """The biggest painted scale whose book fits a w×h canvas."""
    dw, dh = info()["design"]
    fit = min(w / dw, h / dh)
    scales = sorted(info()["scales"])
    return max([s for s in scales if s <= fit + 1e-6], default=scales[0])


def _image(c: tk.Canvas, art: str, scale: float) -> tk.PhotoImage:
    cache = c.__dict__.setdefault("_art_images", {})  # kept with the canvas, reused
    key = (art, scale)
    if key not in cache:
        cache[key] = tk.PhotoImage(master=c, file=str(picture(art, scale)))
    return cache[key]


def draw(c: tk.Canvas, w: int, h: int, t: dict) -> Layout:
    a = info()
    s = scale_for(w, h)
    dw, dh = a["design"]
    c.create_rectangle(0, 0, w, h, fill=t["desk"], outline="")
    c.create_image(w / 2, h / 2, image=_image(c, t["art"], s))

    ox, oy = w / 2 - dw * s / 2, h / 2 - dh * s / 2

    def at(x: float, y: float) -> tuple[float, float]:
        return ox + x * s, oy + y * s

    gx = at(a["gutter"], 0)[0]
    lx0, ly0 = at(*a["page_left"][:2])
    _, ly1 = at(*a["page_left"][2:])
    rx1, _ = at(*a["page_right"][2:])
    pad, top, bottom = PAD * s, 22 * s, 20 * s
    return Layout(left=(lx0 + pad, ly0 + top, gx - pad, ly1 - bottom),
                  right=(gx + pad, ly0 + top, rx1 - pad, ly1 - bottom),
                  gutter=gx, book=(*at(*a["book"][:2]), *at(*a["book"][2:])))
