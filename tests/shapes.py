"""Synthetic hand-drawn-ish shapes for recognizer tests."""

from __future__ import annotations

import math
import random

from sigil.recognizer import Stroke


def _line(a, b, steps=20) -> Stroke:
    return [(a[0] + (b[0] - a[0]) * t / steps, a[1] + (b[1] - a[1]) * t / steps)
            for t in range(steps + 1)]


def _polyline(points) -> Stroke:
    out: Stroke = []
    for a, b in zip(points, points[1:]):
        out.extend(_line(a, b)[:-1])
    out.append(points[-1])
    return out


def circle() -> list[Stroke]:
    return [[(100 + 80 * math.cos(t / 40 * 2 * math.pi), 100 + 80 * math.sin(t / 40 * 2 * math.pi))
             for t in range(41)]]


def triangle() -> list[Stroke]:
    return [_polyline([(100, 20), (180, 170), (20, 170), (100, 20)])]


def star() -> list[Stroke]:
    pts = [(100 + 90 * math.sin(k * 4 * math.pi / 5), 100 - 90 * math.cos(k * 4 * math.pi / 5))
           for k in range(6)]
    return [_polyline(pts)]


def x_mark() -> list[Stroke]:
    return [_line((20, 20), (180, 180)), _line((180, 20), (20, 180))]


def zigzag() -> list[Stroke]:
    return [_polyline([(20, 100), (60, 40), (100, 160), (140, 40), (180, 100)])]


def circle_with_cross() -> list[Stroke]:
    return circle() + [_line((100, 10), (100, 190)), _line((10, 100), (190, 100))]


SHAPES = {
    "circle": circle,
    "triangle": triangle,
    "star": star,
    "x": x_mark,
    "zigzag": zigzag,
    "circle_cross": circle_with_cross,
}


def wobble(strokes: list[Stroke], rng: random.Random, jitter=4.0, scale=None,
           offset=None) -> list[Stroke]:
    """Imitate another attempt: jitter, a different size, a different spot on screen."""
    s = scale if scale is not None else rng.uniform(0.6, 1.8)
    dx, dy = offset if offset is not None else (rng.uniform(0, 800), rng.uniform(0, 500))
    return [[(x * s + dx + rng.gauss(0, jitter), y * s + dy + rng.gauss(0, jitter))
             for x, y in stroke] for stroke in strokes]
