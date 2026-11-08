"""Draws the open grimoire (desk, props, pages) on a tkinter Canvas.

Only decoration lives here; the Sigil Book draws its text and buttons on top. Every
random choice is seeded, so a redraw (resize, selection) never makes the page "jump".
"""

from __future__ import annotations

import math
import random
import tkinter as tk
from dataclasses import dataclass

from .themes import blend

Rect = tuple[float, float, float, float]

RUNES = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"
SYMBOLS = "☉☽☿♀♂♃♄♅♆♇⚶⚷⚸⚹⚺⚻✶✧△▽⊕⊗"


@dataclass
class Layout:
    left: Rect    # writable area of the left page
    right: Rect   # writable area of the right page
    gutter: float
    book: Rect


def draw(c: tk.Canvas, w: int, h: int, t: dict) -> Layout:
    rng = random.Random(7)
    mx, top, bottom = 58, 66, 50
    book = (mx, top, w - mx, h - bottom)
    bx0, by0, bx1, by1 = book
    gx = w / 2
    px0, py0, px1, py1 = bx0 + 12, by0 + 10, bx1 - 12, by1 - 20

    c.create_rectangle(0, 0, w, h, fill=t["desk"], outline="")
    if t["name"] == "parchment":
        _fur(c, w, h, t, rng)
        _sphere(c, bx0 + 26, by0 + 14, 74, "#6b3f8f", "#b48ad6", "#3a1f52")
        _sphere(c, bx1 - 40, by0 - 18, 50, "#d9e1e8", "#ffffff", "#9aa6b2")
        _twigs(c, w, top, rng)
    else:
        _wood(c, w, h, t)
        _scraps(c, w, h, book, rng)
        _candles(c, bx0, by0)
        _coin(c, bx1 - 150, by0 - 18, 30, "✡")
        _coin(c, bx1 - 70, by0 - 6, 30, "☽")

    # book: shadow, cover, stacked page edges, pages
    shadow = blend(t["desk"], "#000000", 0.25)
    c.create_rectangle(bx0 + 10, by0 + 14, bx1 + 10, by1 + 14, fill=shadow, outline="")
    c.create_rectangle(bx0, by0, bx1, by1, fill=t["cover"], outline=blend(t["cover"], "#000000", .4))
    c.create_line(bx0 + 4, by0 + 4, bx1 - 4, by0 + 4, bx1 - 4, by1 - 4, bx0 + 4, by1 - 4,
                  bx0 + 4, by0 + 4, fill=t["gilt"], width=1)
    for i in range(6, 0, -1):
        edge = t["gilt"] if (t["name"] == "parchment" and i <= 2) else t["page_edge"]
        for side in (-1, 1):
            c.create_polygon(*_page_points(px0 - i, py0 + i * 2.2, px1 + i, py1 + i * 2.2, gx, side),
                             fill=edge, outline=t["page_dark"], smooth=True)
    for side in (-1, 1):
        c.create_polygon(*_page_points(px0, py0, px1, py1, gx, side), fill=t["page"],
                         outline=t["page_dark"], smooth=True)

    _stains(c, (px0, py0, gx, py1), t, rng)
    _stains(c, (gx, py0, px1, py1), t, rng)
    _glyph_rows(c, (px0 + 22, py0 + 18, gx - 34, py1 - 14), t, rng)
    _glyph_rows(c, (gx + 34, py0 + 18, px1 - 22, py1 - 14), t, rng)
    _shade_gutter(c, gx, py0, py1, t)
    _shade_edges(c, px0, px1, py0, py1, t)

    # props that lie on top of the pages, tagged "front" so they stay above the writing
    before = set(c.find_all())
    if t["name"] == "parchment":
        _ribbon(c, gx + 26, by0 - 6, by1 + 34, t["accent"])
        _beads(c, w, h, rng)
    else:
        _bone_strand(c, gx, py0 - 4, py1 + 6)
        _quill(c, px1 - 40, py1 - 34)
    for item in c.find_all():
        if item not in before:
            c.addtag_withtag("front", item)

    pad = 46
    return Layout(left=(px0 + pad, py0 + 22, gx - pad, py1 - 22),
                  right=(gx + pad, py0 + 22, px1 - pad, py1 - 22),
                  gutter=gx, book=book)


# ---- pages -----------------------------------------------------------------

def _page_points(x0: float, y0: float, x1: float, y1: float, gx: float, side: int) -> list[float]:
    """A page whose top and bottom rise slightly toward the spine. Doubled points keep
    the corners sharp on a smoothed polygon."""
    outer = x0 if side < 0 else x1
    mid = (outer + gx) / 2
    pts = [(outer, y0 + 8), (outer, y0 + 8), (mid, y0 + 3), (gx, y0 - 3), (gx, y0 - 3),
           (gx, y1 + 3), (gx, y1 + 3), (mid, y1 - 1), (outer, y1), (outer, y1)]
    return [v for p in pts for v in p]


def _shade_gutter(c, gx, y0, y1, t) -> None:
    n = 34
    for i in range(n, 0, -1):
        k = (i / n) ** 1.8
        color = blend(t["page"], t["page_dark"], 0.85 * (1 - k))
        for x in (gx - i, gx + i):
            c.create_line(x, y0 + 1, x, y1 - 1, fill=color)
    c.create_line(gx, y0 - 2, gx, y1 + 2, fill=blend(t["page_dark"], "#000000", .3), width=2)


def _shade_edges(c, x0, x1, y0, y1, t) -> None:
    for i in range(10):
        color = blend(t["page_dark"], t["page"], i / 10)
        c.create_line(x0 + i, y0 + 9, x0 + i, y1, fill=color)
        c.create_line(x1 - i, y0 + 9, x1 - i, y1, fill=color)


def _stains(c, area: Rect, t, rng) -> None:
    x0, y0, x1, y1 = area
    for _ in range(4 if t["name"] == "parchment" else 3):
        r = rng.uniform(30, 80)
        cx = rng.uniform(x0 + r + 12, x1 - r - 12)
        cy = rng.uniform(y0 + r + 12, y1 - r - 12)
        ry = r * rng.uniform(0.7, 1.0)
        for k, amount in ((0, .55), (3, .32), (8, .18)):
            c.create_oval(cx - r + k, cy - ry + k, cx + r - k, cy + ry - k,
                          fill=blend(t["page"], t["stain"], amount), outline="")


def _glyph_rows(c, area: Rect, t, rng) -> None:
    """Faint lines of 'writing' in runes and alchemical signs, like the pictures."""
    x0, y0, x1, y1 = area
    y = y0
    while y < y1:
        x = x0 + rng.uniform(0, 10)
        while x < x1:
            word = rng.randint(2, 6)
            for _ in range(word):
                if x > x1:
                    break
                if rng.random() < .75:
                    ch, font = rng.choice(RUNES), ("Segoe UI Historic", rng.choice((12, 13, 14)))
                else:
                    ch, font = rng.choice(SYMBOLS), ("Segoe UI Symbol", rng.choice((11, 12)))
                c.create_text(x, y, text=ch, fill=t["glyph"], font=font, anchor="w")
                x += rng.uniform(12, 16)
            x += rng.uniform(10, 18)
        y += 24


# ---- desk and props --------------------------------------------------------

def _fur(c, w, h, t, rng) -> None:
    for _ in range(900):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a = rng.uniform(0.6, 1.2)
        length = rng.uniform(6, 18)
        color = rng.choice((t["desk_detail"], "#f7f4ef", "#e2dcd2"))
        c.create_line(x, y, x + math.cos(a) * length, y + math.sin(a) * length, fill=color)


def _sphere(c, cx, cy, r, base, light, dark) -> None:
    steps = 14
    for i in range(steps):
        k = i / steps
        rr = r * (1 - k * 0.9)
        ox, oy = -r * 0.28 * k, -r * 0.3 * k
        color = blend(dark, base, min(1, k * 1.6)) if k < .6 else blend(base, light, (k - .6) / .4)
        c.create_oval(cx + ox - rr, cy + oy - rr, cx + ox + rr, cy + oy + rr, fill=color, outline="")
    c.create_oval(cx - r * .5, cy - r * .6, cx - r * .25, cy - r * .38, fill="#ffffff", outline="")


def _twigs(c, w, top, rng) -> None:
    def branch(x, y, angle, length, width, depth):
        if depth == 0 or length < 8:
            return
        pts = [x, y]
        for _ in range(4):
            angle += rng.uniform(-.25, .25)
            x += math.cos(angle) * length / 4
            y += math.sin(angle) * length / 4
            pts += [x, y]
        c.create_line(*pts, fill=rng.choice(("#5d4634", "#6e5440", "#4b3829")), width=width,
                      capstyle="round", smooth=True)
        for _ in range(2):
            branch(x, y, angle + rng.uniform(-.7, .7), length * .6, max(1, width - 1), depth - 1)

    # kept away from the top-center, where the Grimoire switch is
    branch(-10, top - 34, 0.05, 170, 5, 3)
    branch(w * 0.72, -14, 0.5, 150, 4, 3)
    branch(w + 10, top - 26, math.pi - 0.1, 170, 5, 3)


def _beads(c, w, h, rng) -> None:
    y0 = h - 22
    x = 120
    i = 0
    while x < w - 120:
        y = y0 + math.sin(x / 70) * 6
        if i % 3 == 0:
            c.create_oval(x - 9, y - 8, x + 9, y + 8, fill="#efe8da", outline="#b5aa94")
            c.create_oval(x - 4, y - 3, x - 1, y, fill="#8d8270", outline="")
            c.create_oval(x + 1, y - 3, x + 4, y, fill="#8d8270", outline="")
            x += 20
        else:
            c.create_oval(x - 6, y - 6, x + 6, y + 6, fill=rng.choice(("#6e4a38", "#8a5a3e", "#5a3d30")),
                          outline="#3e2a20")
            x += 14
        i += 1


def _ribbon(c, x, y0, y1, color) -> None:
    c.create_polygon(x, y0, x + 9, y0, x + 11, y1, x + 5, y1 - 8, x, y1,
                     fill=color, outline=blend(color, "#000000", .35))
    c.create_line(x + 3, y0, x + 4, y1 - 6, fill=blend(color, "#ffffff", .18))


def _wood(c, w, h, t) -> None:
    slope = 0.32
    step = 120
    for x in range(-int(h * slope) - step, w + step, step):
        c.create_line(x, 0, x + h * slope, h, fill=blend(t["desk"], "#000000", .35), width=2)
        for k in (18, 41, 63, 87, 104):
            c.create_line(x + k, 0, x + k + h * slope, h,
                          fill=blend(t["desk"], "#ffffff" if k % 2 else "#000000", .07))


def _scraps(c, w, h, book, rng) -> None:
    bx0, by0, bx1, by1 = book
    for cx, cy, sw, sh, ang in ((bx0 + 40, by1 - 10, 320, 160, -.08), (bx1 - 80, by1 + 4, 300, 140, .06),
                                (bx0 + 120, by0 + 4, 280, 120, .1), (bx1 - 220, by0 - 6, 300, 110, -.05)):
        pts = _rotated_rect(cx, cy, sw, sh, ang)
        c.create_polygon(*pts, fill=rng.choice(("#d8b98b", "#cfae7c", "#dcc196")), outline="#a98a5a")
        for _ in range(16):
            gx = cx + rng.uniform(-sw / 2 + 12, sw / 2 - 12)
            gy = cy + rng.uniform(-sh / 2 + 10, sh / 2 - 10)
            if gy < by0 and abs(gx - w / 2) < 170:
                continue  # keep the Grimoire switch above the book readable
            c.create_text(gx, gy, text=rng.choice(RUNES + SYMBOLS), fill="#8a6136",
                          font=("Segoe UI Historic", 12))


def _rotated_rect(cx, cy, w, h, a) -> list[float]:
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        out += [cx + dx * ca - dy * sa, cy + dx * sa + dy * ca]
    return out


def _candles(c, bx0, by0) -> None:
    for i, (cx, cy) in enumerate(((bx0 + 20, by0 - 22), (bx0 + 54, by0 - 30), (bx0 + 88, by0 - 18))):
        pts = _rotated_rect(cx, cy, 26, 150, 0.12 + i * 0.05)
        c.create_polygon(*pts, fill="#1b1b20", outline="#0c0c0f")
        for k in range(-60, 70, 10):
            c.create_line(cx - 10, cy + k, cx + 10, cy + k + 4, fill="#2a2a31")


def _coin(c, cx, cy, r, symbol) -> None:
    c.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#17171a", outline="#6a6a70", width=2)
    c.create_oval(cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6, outline="#3a3a40")
    c.create_text(cx, cy, text=symbol, fill="#c9c2b0", font=("Segoe UI Symbol", int(r * .9)))


def _bone_strand(c, gx, y0, y1) -> None:
    y = y0
    while y < y1:
        x = gx + math.sin(y / 38) * 5
        c.create_oval(x - 8, y - 7, x + 8, y + 7, fill="#ece4d3", outline="#a99e88")
        c.create_oval(x - 4, y - 2, x - 1, y + 1, fill="#7d7262", outline="")
        c.create_oval(x + 1, y - 2, x + 4, y + 1, fill="#7d7262", outline="")
        y += 15


def _quill(c, x, y) -> None:
    a = -0.75
    ca, sa = math.cos(a), math.sin(a)

    def p(u, v):
        return x + u * ca - v * sa, y + u * sa + v * ca

    vane = [p(-10, 0), p(30, -16), p(110, -22), p(170, -8), p(178, 0), p(170, 8), p(110, 20),
            p(30, 14)]
    c.create_polygon(*[v for q in vane for v in q], fill="#24232a", outline="#3a3942", smooth=True)
    for u in range(20, 170, 9):
        a1, b1 = p(u, 0), p(u + 14, -18 + abs(u - 100) / 10)
        a2, b2 = p(u, 0), p(u + 14, 17 - abs(u - 100) / 10)
        c.create_line(*a1, *b1, fill="#3d3c46")
        c.create_line(*a2, *b2, fill="#3d3c46")
    c.create_line(*p(-40, 0), *p(178, 0), fill="#8e8a80", width=2)
    c.create_line(*p(-58, 0), *p(-38, 0), fill="#c9a24a", width=3)
