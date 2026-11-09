"""Paint the Candlelight and Midnight grimoires into PNG pictures for the Sigil Book.

tkinter can't do soft light, glow or paper grain, so these two looks are painted ahead of
time: this script writes each one as an SVG (stone desk, glowing rune circle, the open
book, a candle and its light) and has Microsoft Edge (headless) save it as a PNG. The
app shows the picture and draws its text and buttons on top (see sigil/artbook.py), so
users don't need Edge, only the PNGs in assets/grimoire/.

    python tools/render_art.py

Everything is drawn in a 1160×760 "design" space (the default window) and scaled; each
scale gets a picture with extra desk around the book so it fills windows of other
shapes. art.json records the scales and where the pages are, for the app's layout.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "grimoire"
EDGE = [Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")]

DESIGN = (1160, 760)
SCALES = [0.86, 1.0, 1.2, 1.45]
EXTRA = (1.3, 1.22)          # picture size = design × scale × this
BOOK = (100, 90, 1060, 700)
PAGE_L = (116, 106, 575, 684)
PAGE_R = (586, 106, 1048, 684)
GUTTER = 580
CANDLE = (78, 64)            # the flame, in design space

LOOKS = {
    "candlelight": {
        "stone": "#24201b", "stone_light": "#6a6258", "edge": "#0b0a09",
        "cover": "#4a1f12", "cover_light": "#7a3f22", "page_under": "#c8a670",
        "page": ("#efdcae", "#ddc089", "#a97d45"), "gutter": "#5a3a17",
        "grain": "0 0 0 0 0.35  0 0 0 0 0.22  0 0 0 0 0.1  0 0 0 0.16 0",
        "fox": "0 0 0 0 0.5  0 0 0 0 0.32  0 0 0 0 0.12  0 0 0 1.6 -0.62", "fox_opacity": 0.45,
        "spine": "#3a220e", "ribbon": "#7d1a14",
        "candle": "#efe2c4", "candle_top": "#d8c7a0", "candle_rim": "#f6ead0", "wick": "#2a1a10",
        "dark": 0.72, "warm": 0.6, "page_dim": 0.16, "page_warm": 0.22,
    },
    "midnight": {
        "stone": "#1a1816", "stone_light": "#4c4842", "edge": "#080808",
        "cover": "#141110", "cover_light": "#3a3430", "page_under": "#3a332c",
        "page": ("#262120", "#1b1717", "#0c0a0a"), "gutter": "#000000",
        "grain": "0 0 0 0 0.85  0 0 0 0 0.75  0 0 0 0 0.55  0 0 0 0.06 0",
        "fox": "0 0 0 0 0.3  0 0 0 0 0.26  0 0 0 0 0.2  0 0 0 1.4 -0.6", "fox_opacity": 0.22,
        "spine": "#5a4a30", "ribbon": "#6e1712",
        "candle": "#1d1a19", "candle_top": "#2a2524", "candle_rim": "#3a3331", "wick": "#c9b48a",
        "dark": 0.65, "warm": 0.5, "page_dim": 0.08, "page_warm": 0.1,
    },
}

RUNE_RING = [("ᚠ", 0, -360), ("ᚱ", 255, -250), ("ᚲ", 364, 6), ("ᚷ", 255, 262), ("ᚹ", 0, 372),
             ("ᚺ", -255, 262), ("ᚾ", -364, 6), ("ᛁ", -255, -250), ("ᛃ", 140, -334),
             ("ᛇ", 334, -132), ("ᛈ", 334, 146), ("ᛉ", 140, 346), ("ᛊ", -140, 346),
             ("ᛏ", -334, 146), ("ᛒ", -334, -132), ("ᛖ", -140, -334)]


def page_path(x0, y0, x1, y1, side) -> str:
    """A page whose top and bottom dip toward the spine, like the mockups."""
    if side < 0:
        return (f"M{x0} {y0} Q{(x0 + x1) / 2} {y0 - 20} {x1} {y0 + 6} L{x1} {y1} "
                f"Q{(x0 + x1) / 2} {y1 - 22} {x0} {y1} Z")
    return (f"M{x0} {y0 + 6} Q{(x0 + x1) / 2} {y0 - 20} {x1} {y0} L{x1} {y1} "
            f"Q{(x0 + x1) / 2} {y1 - 22} {x0} {y1} Z")


def svg(look: dict, w: int, h: int, s: float) -> str:
    L = look
    ox, oy = (w - DESIGN[0] * s) / 2, (h - DESIGN[1] * s) / 2
    cx, cy = (ox + CANDLE[0] * s) / w, (oy + CANDLE[1] * s) / h   # candle, as a fraction
    gx = GUTTER
    p0, p1 = PAGE_L, PAGE_R
    runes = "".join(f'<text x="{x}" y="{y}">{ch}</text>' for ch, x, y in RUNE_RING)
    pl = page_path(p0[0], p0[1], p0[2], p0[3], -1)
    pr = page_path(p1[0], p1[1], p1[2], p1[3], 1)
    edge_w, edge_h = w * 0.06, h * 0.08
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs>
<filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="2.6" result="b"/>
<feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="bigglow" filterUnits="userSpaceOnUse" x="-400" y="-400" width="2000" height="1600"><feGaussianBlur stdDeviation="22"/></filter>
<filter id="shadow" filterUnits="userSpaceOnUse" x="-200" y="-200" width="1600" height="1200"><feGaussianBlur stdDeviation="14"/></filter>
<filter id="stone" x="0" y="0" width="100%" height="100%">
<feTurbulence type="fractalNoise" baseFrequency="{0.02 / s:.4f}" numOctaves="5" seed="40" result="n"/>
<feDiffuseLighting in="n" surfaceScale="3" lighting-color="{L['stone_light']}" result="l"><feDistantLight azimuth="225" elevation="50"/></feDiffuseLighting>
<feComposite in="l" in2="SourceGraphic" operator="in"/></filter>
<filter id="grain" x="0" y="0" width="100%" height="100%">
<feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="2" seed="7" result="n"/>
<feColorMatrix in="n" type="matrix" values="{L['grain']}"/><feComposite in2="SourceGraphic" operator="in"/></filter>
<filter id="fox" x="0" y="0" width="100%" height="100%">
<feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="5" seed="12" result="n"/>
<feColorMatrix in="n" type="matrix" values="{L['fox']}"/><feComposite in2="SourceGraphic" operator="in"/></filter>
<filter id="leather" x="0" y="0" width="100%" height="100%">
<feTurbulence type="fractalNoise" baseFrequency="0.35" numOctaves="3" seed="3" result="n"/>
<feDiffuseLighting in="n" surfaceScale="1.6" lighting-color="{L['cover_light']}" result="l"><feDistantLight azimuth="225" elevation="48"/></feDiffuseLighting>
<feComposite in="l" in2="SourceGraphic" operator="in"/></filter>
<radialGradient id="pool" gradientUnits="userSpaceOnUse" cx="{ox + 580 * s}" cy="{oy + 400 * s}" r="{560 * s}">
<stop offset="0" stop-color="#3fe0a8" stop-opacity="0.32"/><stop offset="0.6" stop-color="#1c7a62" stop-opacity="0.11"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
<radialGradient id="page" cx="0.5" cy="0.45" r="0.75"><stop offset="0" stop-color="{L['page'][0]}"/><stop offset="0.7" stop-color="{L['page'][1]}"/><stop offset="1" stop-color="{L['page'][2]}"/></radialGradient>
<linearGradient id="gutL" x1="0" y1="0" x2="1" y2="0"><stop offset="0.72" stop-color="{L['gutter']}" stop-opacity="0"/><stop offset="1" stop-color="{L['gutter']}" stop-opacity="0.55"/></linearGradient>
<linearGradient id="gutR" x1="1" y1="0" x2="0" y2="0"><stop offset="0.72" stop-color="{L['gutter']}" stop-opacity="0"/><stop offset="1" stop-color="{L['gutter']}" stop-opacity="0.55"/></linearGradient>
<linearGradient id="gold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f7dc8f"/><stop offset="0.45" stop-color="#c79a3e"/><stop offset="1" stop-color="#7a5418"/></linearGradient>
<radialGradient id="wax" cx="0.4" cy="0.35" r="0.7"><stop offset="0" stop-color="#d8473a"/><stop offset="0.7" stop-color="#8f1d16"/><stop offset="1" stop-color="#5e100c"/></radialGradient>
<radialGradient id="dark" gradientUnits="userSpaceOnUse" cx="{cx * w}" cy="{cy * h}" r="{1.15 * 1200 * s}">
<stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="0.45" stop-color="#000" stop-opacity="0.16"/><stop offset="1" stop-color="#000" stop-opacity="{L['dark']}"/></radialGradient>
<radialGradient id="warm" gradientUnits="userSpaceOnUse" cx="{cx * w}" cy="{cy * h}" r="{0.85 * 1200 * s}">
<stop offset="0" stop-color="#ffb35c" stop-opacity="{L['warm']}"/><stop offset="0.4" stop-color="#d9772b" stop-opacity="0.16"/><stop offset="1" stop-color="#d9772b" stop-opacity="0"/></radialGradient>
<radialGradient id="emerald" gradientUnits="userSpaceOnUse" cx="{ox + 580 * s}" cy="{oy + 400 * s}" r="{580 * s}">
<stop offset="0" stop-color="#3fe0a8" stop-opacity="0.14"/><stop offset="1" stop-color="#3fe0a8" stop-opacity="0"/></radialGradient>
<radialGradient id="pagedim" gradientUnits="userSpaceOnUse" cx="{CANDLE[0]}" cy="{CANDLE[1]}" r="1150">
<stop offset="0.35" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="{L['page_dim']}"/></radialGradient>
<radialGradient id="pagewarm" gradientUnits="userSpaceOnUse" cx="{CANDLE[0]}" cy="{CANDLE[1]}" r="700">
<stop offset="0" stop-color="#ffb35c" stop-opacity="{L['page_warm']}"/><stop offset="1" stop-color="#ffb35c" stop-opacity="0"/></radialGradient>
<linearGradient id="fadeL" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{L['edge']}"/><stop offset="1" stop-color="{L['edge']}" stop-opacity="0"/></linearGradient>
<linearGradient id="fadeR" x1="1" y1="0" x2="0" y2="0"><stop offset="0" stop-color="{L['edge']}"/><stop offset="1" stop-color="{L['edge']}" stop-opacity="0"/></linearGradient>
<linearGradient id="fadeT" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{L['edge']}"/><stop offset="1" stop-color="{L['edge']}" stop-opacity="0"/></linearGradient>
<linearGradient id="fadeB" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{L['edge']}"/><stop offset="1" stop-color="{L['edge']}" stop-opacity="0"/></linearGradient>
</defs>
<rect width="{w}" height="{h}" fill="{L['stone']}"/>
<rect width="{w}" height="{h}" fill="#000" filter="url(#stone)"/>
<rect width="{w}" height="{h}" fill="url(#pool)"/>
<g transform="translate({ox:.2f} {oy:.2f}) scale({s})">
<g transform="translate(580 400)" fill="none" filter="url(#glow)">
<circle r="372" stroke="#46e0ac" stroke-width="2" opacity="0.8"/>
<circle r="356" stroke="#46e0ac" stroke-width="0.8" opacity="0.6"/>
<circle r="340" stroke="#e8c26a" stroke-width="0.8" stroke-dasharray="3 9" opacity="0.7"/>
<path d="M0 -356 L308 178 L-308 178 Z" stroke="#46e0ac" stroke-width="0.8" opacity="0.4"/>
<path d="M0 356 L308 -178 L-308 -178 Z" stroke="#46e0ac" stroke-width="0.8" opacity="0.4"/>
<g fill="#7cf5c9" stroke="none" font-size="18" font-family="Segoe UI Historic, serif" text-anchor="middle" opacity="0.9">{runes}</g>
</g>
</g>
<rect width="{w}" height="{h}" fill="url(#dark)"/>
<rect width="{w}" height="{h}" fill="url(#warm)" style="mix-blend-mode: screen"/>
<rect width="{w}" height="{h}" fill="url(#emerald)" style="mix-blend-mode: screen"/>
<g transform="translate({ox:.2f} {oy:.2f}) scale({s})">
<path d="M{BOOK[0] - 4} {BOOK[1] + 14} Q580 {BOOK[1] - 6} {BOOK[2] + 4} {BOOK[1] + 14} L{BOOK[2] + 14} {BOOK[3] + 16} Q580 {BOOK[3] - 4} {BOOK[0] - 14} {BOOK[3] + 16} Z" fill="#000" opacity="0.75" filter="url(#shadow)"/>
<path d="M{BOOK[0]} {BOOK[1]} Q580 {BOOK[1] - 20} {BOOK[2]} {BOOK[1]} L{BOOK[2] + 6} {BOOK[3]} Q580 {BOOK[3] - 20} {BOOK[0] - 6} {BOOK[3]} Z" fill="{L['cover']}"/>
<path d="M{BOOK[0]} {BOOK[1]} Q580 {BOOK[1] - 20} {BOOK[2]} {BOOK[1]} L{BOOK[2] + 6} {BOOK[3]} Q580 {BOOK[3] - 20} {BOOK[0] - 6} {BOOK[3]} Z" fill="#000" filter="url(#leather)" opacity="0.9"/>
<path d="M{BOOK[0] + 6} {BOOK[1] + 6} Q580 {BOOK[1] - 14} {BOOK[2] - 6} {BOOK[1] + 6} L{BOOK[2]} {BOOK[3] - 6} Q580 {BOOK[3] - 26} {BOOK[0]} {BOOK[3] - 6} Z" fill="none" stroke="url(#gold)" stroke-width="1.6"/>
<path d="{page_path(p0[0] - 6, p0[1] - 4, gx - 5, p0[3] + 6, -1)}" fill="{L['page_under']}"/>
<path d="{page_path(gx + 6, p1[1] - 4, p1[2] + 4, p1[3] + 6, 1)}" fill="{L['page_under']}"/>
<path d="{pl}" fill="url(#page)"/>
<path d="{pr}" fill="url(#page)"/>
<clipPath id="pages"><path d="{pl}"/><path d="{pr}"/></clipPath>
<g clip-path="url(#pages)">
<rect x="{p0[0]}" y="{p0[1] - 20}" width="{p1[2] - p0[0]}" height="{p0[3] - p0[1] + 30}" fill="#000" filter="url(#fox)" opacity="{L['fox_opacity']}"/>
<rect x="{p0[0]}" y="{p0[1] - 20}" width="{p1[2] - p0[0]}" height="{p0[3] - p0[1] + 30}" fill="#000" filter="url(#grain)"/>
<rect x="{gx - 160}" y="{p0[1] - 20}" width="160" height="{p0[3] - p0[1] + 30}" fill="url(#gutL)"/>
<rect x="{gx}" y="{p0[1] - 20}" width="160" height="{p0[3] - p0[1] + 30}" fill="url(#gutR)"/>
</g>
<line x1="{gx}" y1="{p0[1] + 4}" x2="{gx}" y2="{p0[3] - 2}" stroke="{L['spine']}" stroke-width="2"/>
<path d="M{p0[0]} {p0[1]} l40 0 l-40 34z M{p1[2]} {p1[1]} l-40 0 l40 34z M{p0[0]} {p0[3]} l40 0 l-40 -34z M{p1[2]} {p1[3]} l-40 0 l40 -34z" fill="url(#gold)"/>
<path d="M{gx + 8} {BOOK[1] - 30} l14 0 l0 {BOOK[3] - BOOK[1] + 70} l-7 -12 l-7 12z" fill="{L['ribbon']}"/>
<circle cx="{BOOK[2] + 2}" cy="{BOOK[3] + 4}" r="28" fill="url(#wax)"/>
<path d="M{BOOK[2] - 24} {BOOK[3] - 12} q-8 18 6 38 M{BOOK[2] + 26} {BOOK[3] - 6} q6 20 -10 32" stroke="#5e100c" stroke-width="5" fill="none"/>
<path d="M{BOOK[2] + 2} {BOOK[3] - 14} l4 13 l13 5 l-13 5 l-4 13 l-4 -13 l-13 -5 l13 -5z" fill="#5e100c"/>
<!-- the pages stay readable: only a gentle warmth near the candle and a little dimming
     far from it (the deep shadow falls on the desk, drawn before the book) -->
<rect x="{BOOK[0] - 10}" y="{BOOK[1] - 30}" width="{BOOK[2] - BOOK[0] + 20}" height="{BOOK[3] - BOOK[1] + 60}" fill="url(#pagedim)"/>
<rect x="{BOOK[0] - 10}" y="{BOOK[1] - 30}" width="{BOOK[2] - BOOK[0] + 20}" height="{BOOK[3] - BOOK[1] + 60}" fill="url(#pagewarm)" style="mix-blend-mode: screen"/>
</g>
<g transform="translate({ox:.2f} {oy:.2f}) scale({s})">
<ellipse cx="78" cy="96" rx="120" ry="120" fill="#ffb35c" opacity="0.26" filter="url(#bigglow)"/>
<ellipse cx="78" cy="214" rx="56" ry="12" fill="#000" opacity="0.5" filter="url(#shadow)"/>
<path d="M54 92 h48 v108 q-24 10 -48 0z" fill="{L['candle']}"/>
<path d="M54 100 q24 12 48 0 v14 q-6 2 -6 12 q-4 -8 -8 -2 q-10 4 -20 -2 q-6 6 -8 0 q-2 -8 -6 -8z" fill="{L['candle_top']}"/>
<ellipse cx="78" cy="94" rx="24" ry="6" fill="{L['candle_rim']}"/>
<path d="M78 92 v-12" stroke="{L['wick']}" stroke-width="2"/>
<path d="M78 40 q14 20 0 42 q-14 -22 0 -42z" fill="#ffcf73"/>
<path d="M78 54 q6 12 0 24 q-6 -12 0 -24z" fill="#fff6d6"/>
<circle cx="78" cy="64" r="40" fill="#ffd58a" opacity="0.34" filter="url(#bigglow)"/>
</g>
<rect width="{edge_w:.0f}" height="{h}" fill="url(#fadeL)"/>
<rect x="{w - edge_w:.0f}" width="{edge_w:.0f}" height="{h}" fill="url(#fadeR)"/>
<rect width="{w}" height="{edge_h:.0f}" fill="url(#fadeT)"/>
<rect y="{h - edge_h:.0f}" width="{w}" height="{edge_h:.0f}" fill="url(#fadeB)"/>
</svg>"""


def edge() -> Path:
    for path in EDGE:
        if path.exists():
            return path
    sys.exit("Microsoft Edge wasn't found; it's needed to render the art (not to run the app).")


def render(look: str, s: float, browser: Path, tmp: Path) -> tuple[int, int]:
    w, h = round(DESIGN[0] * s * EXTRA[0]), round(DESIGN[1] * s * EXTRA[1])
    page = tmp / f"{look}-{s}.html"
    page.write_text("<!doctype html><meta charset='utf-8'><style>html,body{margin:0;"
                    f"overflow:hidden;background:{LOOKS[look]['edge']}}}</style>"
                    + svg(LOOKS[look], w, h, s), encoding="utf-8")
    out = OUT / f"{look}@{s}.png"
    subprocess.run([str(browser), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", f"--window-size={w},{h}",
                    f"--user-data-dir={tmp / 'profile'}", f"--screenshot={out}",
                    page.as_uri()], check=True, capture_output=True, timeout=120)
    print(f"{out.name}: {w}×{h}, {out.stat().st_size / 1e6:.1f} MB")
    return w, h


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    browser = edge()
    sizes = {}
    with tempfile.TemporaryDirectory() as tmp:
        for look in LOOKS:
            for s in SCALES:
                sizes[str(s)] = render(look, s, browser, Path(tmp))
    (OUT / "art.json").write_text(json.dumps({
        "design": DESIGN, "scales": SCALES, "sizes": sizes, "book": BOOK,
        "page_left": PAGE_L, "page_right": PAGE_R, "gutter": GUTTER,
        "edge": {k: v["edge"] for k, v in LOOKS.items()},
    }, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
