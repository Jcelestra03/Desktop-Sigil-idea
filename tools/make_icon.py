"""Draw the app icon (a red seal with a ✦ on parchment) and save it as assets/sigil.ico.

Standard library only: the shapes are drawn by sampling each pixel, and every size is
stored as a PNG inside the .ico (supported since Windows Vista).

    python tools/make_icon.py
"""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "sigil.ico"
SIZES = [16, 24, 32, 48, 64, 128, 256]

PAGE = (239, 223, 189)
RED = (163, 42, 30)
EDGE = (122, 90, 44)


def _star(n_points=4, outer=0.30, inner=0.085):
    pts = []
    for i in range(n_points * 2):
        a = i * math.pi / n_points - math.pi / 2
        r = outer if i % 2 == 0 else inner
        pts.append((math.cos(a) * r, math.sin(a) * r))
    return pts


STAR = _star()


def _in_poly(x, y, poly) -> bool:
    inside = False
    j = len(poly) - 1
    for i, (xi, yi) in enumerate(poly):
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _color_at(x: float, y: float, size: int):
    """Color of a point; x, y from -0.5 to 0.5. None is transparent."""
    r = math.hypot(x, y)
    px = 1 / size                       # one pixel, so thin lines stay visible when small
    if r > 0.48:
        return None
    if r > 0.48 - max(0.025, px):
        return EDGE
    if r > 0.41 - max(0.0, px * 0.3) and r <= 0.465 - max(0.0, px * 0.3):
        return RED
    if 0.355 < r <= 0.355 + max(0.012, px * 0.9) and size >= 32:
        return RED
    if _in_poly(x, y, STAR if size >= 32 else _star(outer=0.33, inner=0.11)):
        return RED
    return PAGE


def render(size: int, ss: int = 4) -> bytes:
    """RGBA rows with a filter byte each (ready for PNG)."""
    rows = bytearray()
    for py in range(size):
        rows.append(0)
        for px in range(size):
            acc = [0, 0, 0, 0]
            for sy in range(ss):
                for sx in range(ss):
                    x = (px + (sx + 0.5) / ss) / size - 0.5
                    y = (py + (sy + 0.5) / ss) / size - 0.5
                    c = _color_at(x, y, size)
                    if c:
                        acc[0] += c[0]
                        acc[1] += c[1]
                        acc[2] += c[2]
                        acc[3] += 1
            n = acc[3]
            if n:
                rows += bytes((acc[0] // n, acc[1] // n, acc[2] // n, round(255 * n / ss / ss)))
            else:
                rows += b"\0\0\0\0"
    return bytes(rows)


def png(size: int) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    head = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", head)
            + chunk(b"IDAT", zlib.compress(render(size), 9)) + chunk(b"IEND", b""))


def ico(sizes=SIZES) -> bytes:
    images = [png(s) for s in sizes]
    out = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    for s, data in zip(sizes, images):
        out += struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    return out + b"".join(images)


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(ico())
    (OUT.with_suffix(".png")).write_bytes(png(256))
    print(f"wrote {OUT}")
