"""The two grimoire looks for the Sigil Book window.

parchment: aged pages, black ink, red-ink seals, on white fur with crystals and twigs.
obsidian:  black pages, gold ink, a bone-bead strand down the spine, on teal wood.
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
    **{f"font_{k}": v for k, v in _FONTS.items()},
}

THEMES = {t["name"]: t for t in (PARCHMENT, OBSIDIAN)}
DEFAULT_THEME = "parchment"


def get(name: str | None) -> dict:
    return THEMES.get(name or DEFAULT_THEME, PARCHMENT)
