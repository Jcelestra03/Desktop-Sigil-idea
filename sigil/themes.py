"""The grimoire looks for the Sigil Book window.

candlelight: vellum pages by candlelight, over a glowing emerald rune circle (painted art).
midnight:    the same scene with black pages and gold ink (painted art).
parchment:   aged pages, black ink, red-ink seals, on white fur with crystals and twigs.
obsidian:    black pages, gold ink, a bone-bead strand down the spine, on teal wood.

"art" names a painted background in assets/grimoire (drawn by sigil/artbook.py, made by
tools/render_art.py); None means the book is drawn with canvas shapes (sigil/grimoire.py).
"glow" gives seals a soft halo. "danger" colors Erase.
"""

from __future__ import annotations


def blend(a: str, b: str, t: float) -> str:
    """Mix two #rrggbb colors; t=0 gives a, t=1 gives b."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


_FONTS = {
    "title": ("Gabriola", 34),
    "head": ("Gabriola", 26),
    "name": ("Gabriola", 22),
    "body": ("Palatino Linotype", 12),
    "small": ("Palatino Linotype", 10),
    "italic": ("Palatino Linotype", 10, "italic"),
    "button": ("Palatino Linotype", 12),
    "glyph": ("Segoe UI Historic", 13),
}

PARCHMENT = {
    "name": "parchment",
    "label": "Parchment",
    "desk": "#ece8e1",
    "desk_detail": "#dcd5ca",
    "desk_text": "#5e4b38",
    "cover": "#7a5a2c",
    "gilt": "#c9a24a",
    "page": "#efdfbd",
    "page_dark": "#c9ac78",
    "page_edge": "#e4cf9f",
    "stain": "#d8bd8a",
    "ink": "#2b1d14",
    "ink_soft": "#6e5843",
    "glyph": "#dcc59c",
    "accent": "#a32a1e",
    "field": "#f6ebd0",
    "field_line": "#c9ac78",
    "on_accent": "#f6ebd0",
    "danger": "#a32a1e",
    "art": None,
    "glow": False,
    **{f"font_{k}": v for k, v in _FONTS.items()},
}

OBSIDIAN = {
    "name": "obsidian",
    "label": "Obsidian",
    "desk": "#5f8286",
    "desk_detail": "#4f7074",
    "desk_text": "#f1e6cf",
    "cover": "#140f0f",
    "gilt": "#a8884a",
    "page": "#1f1c1d",
    "page_dark": "#0b0a0b",
    "page_edge": "#2c2829",
    "stain": "#262223",
    "ink": "#e0c27a",
    "ink_soft": "#a48c58",
    "glyph": "#352f25",
    "accent": "#f0d48a",
    "field": "#2a2627",
    "field_line": "#5a4c30",
    "on_accent": "#1f1c1d",
    "danger": "#f0d48a",
    "art": None,
    "glow": False,
    **{f"font_{k}": v for k, v in _FONTS.items()},
}

# the painted pages have texture and candle shading, so their small print is a size up
_PAINTED_FONTS = {
    "font_small": ("Palatino Linotype", 11),
    "font_italic": ("Palatino Linotype", 11, "italic"),
}

CANDLELIGHT = {
    "name": "candlelight",
    "label": "Candlelight",
    "desk": "#0b0a09",          # the painted art fades to this at its edges
    "desk_detail": "#24201b",
    "desk_text": "#d9b981",
    "cover": "#4a1f12",
    "gilt": "#c79a3e",
    "page": "#e2c995",
    "page_dark": "#a97d45",
    "page_edge": "#cdb07a",
    "stain": "#d8bd8a",
    "ink": "#2a1d10",
    "ink_soft": "#47331f",
    "glyph": "#d8bd8a",
    "accent": "#0f7d5e",
    "field": "#f0e0b8",
    "field_line": "#bf9f68",
    "on_accent": "#f0e0b8",
    "danger": "#8f1d16",
    "art": "candlelight",
    "glow": True,
    **{f"font_{k}": v for k, v in _FONTS.items()},
    **_PAINTED_FONTS,
}

MIDNIGHT = {
    "name": "midnight",
    "label": "Midnight",
    "desk": "#080808",
    "desk_detail": "#1a1816",
    "desk_text": "#c4ae84",
    "cover": "#141110",
    "gilt": "#c79a3e",
    "page": "#1f1b1a",
    "page_dark": "#0c0a0a",
    "page_edge": "#3a332c",
    "stain": "#262120",
    "ink": "#e6c77a",
    "ink_soft": "#bba06a",
    "glyph": "#352f25",
    "accent": "#46e0ac",
    "field": "#2a2523",
    "field_line": "#5a4a30",
    "on_accent": "#141110",
    "danger": "#ef8a76",
    "art": "midnight",
    "glow": True,
    **{f"font_{k}": v for k, v in _FONTS.items()},
    **_PAINTED_FONTS,
}

THEMES = {t["name"]: t for t in (CANDLELIGHT, MIDNIGHT, PARCHMENT, OBSIDIAN)}
DEFAULT_THEME = "candlelight"


def get(name: str | None) -> dict:
    return THEMES.get(name or DEFAULT_THEME, CANDLELIGHT)
