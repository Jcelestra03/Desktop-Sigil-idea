"""$P point-cloud gesture recognizer.

Vatavu, Anthony & Wobbrock, "Gestures as Point Clouds: A $P Recognizer for User
Interface Prototypes" (ICMI 2012). A drawing is resampled to a fixed number of points,
scaled and centered, then compared to each saved sample by greedily matching points.
Stroke order and direction do not matter, which suits multi-stroke sigils.

Pure Python, no tkinter: the overlay passes in strokes, this module returns a Match.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol, Sequence

Point = tuple[float, float]
Stroke = list[Point]

NUM_POINTS = 32
# $P scores are max((2 - distance) / 2, 0). Below this, we say "no sigil recognized".
# Synthetic tests: same shape >= ~0.53, different shapes <= ~0.40. Tune with real drawings.
DEFAULT_MIN_SCORE = 0.45


class HasTemplates(Protocol):
    name: str
    templates: list[list[Stroke]]


@dataclass
class Match:
    sigil: HasTemplates
    score: float


# Internal point: (x, y, stroke_index)
_P = tuple[float, float, int]


def recognize(
    strokes: Sequence[Stroke],
    sigils: Sequence[HasTemplates],
    min_score: float = DEFAULT_MIN_SCORE,
) -> Match | None:
    """Return the best-matching sigil, or None if nothing scores at least min_score."""
    candidate = normalize(strokes)
    if candidate is None:
        return None

    best: Match | None = None
    for sigil in sigils:
        for template in sigil.templates:
            points = normalize(template)
            if points is None:
                continue
            score = _score(_greedy_cloud_match(candidate, points))
            if best is None or score > best.score:
                best = Match(sigil, score)

    if best is None or best.score < min_score:
        return None
    return best


def compare(a: Sequence[Stroke], b: Sequence[Stroke]) -> float:
    """Similarity score (0..1) between two drawings. Handy for tests and tuning."""
    pa, pb = normalize(a), normalize(b)
    if pa is None or pb is None:
        return 0.0
    return _score(_greedy_cloud_match(pa, pb))


def normalize(strokes: Sequence[Stroke], n: int = NUM_POINTS) -> list[_P] | None:
    """Resample, scale and center a drawing. None if it is too small to recognize."""
    points = [(x, y, i) for i, stroke in enumerate(strokes) for x, y in stroke]
    if len(points) < 2 or _path_length(points) < 1e-6:
        return None
    points = _resample(points, n)
    points = _scale(points)
    return _translate_to_origin(points)


def _score(distance: float) -> float:
    return max((2.0 - distance) / 2.0, 0.0)


def _greedy_cloud_match(points: list[_P], template: list[_P]) -> float:
    n = len(points)
    step = max(1, int(n ** 0.5))  # epsilon = 0.5 in the paper
    best = math.inf
    for start in range(0, n, step):
        best = min(
            best,
            _cloud_distance(points, template, start),
            _cloud_distance(template, points, start),
        )
    return best


def _cloud_distance(points: list[_P], template: list[_P], start: int) -> float:
    n = len(points)
    matched = [False] * n
    total = 0.0
    i = start
    while True:
        nearest, nearest_d = -1, math.inf
        for j, t in enumerate(template):
            if not matched[j]:
                d = math.dist(points[i][:2], t[:2])
                if d < nearest_d:
                    nearest, nearest_d = j, d
        matched[nearest] = True
        weight = 1 - ((i - start + n) % n) / n
        total += weight * nearest_d
        i = (i + 1) % n
        if i == start:
            return total


def _path_length(points: list[_P]) -> float:
    return sum(
        math.dist(a[:2], b[:2])
        for a, b in zip(points, points[1:])
        if a[2] == b[2]
    )


def _resample(points: list[_P], n: int) -> list[_P]:
    interval = _path_length(points) / (n - 1)
    gap = 0.0
    out = [points[0]]
    pts = list(points)
    i = 1
    while i < len(pts):
        prev, cur = pts[i - 1], pts[i]
        if prev[2] == cur[2]:
            d = math.dist(prev[:2], cur[:2])
            if gap + d >= interval and d > 0:
                t = (interval - gap) / d
                q = (prev[0] + t * (cur[0] - prev[0]), prev[1] + t * (cur[1] - prev[1]), cur[2])
                out.append(q)
                pts.insert(i, q)  # q becomes the next "prev"
                gap = 0.0
            else:
                gap += d
        i += 1
    # Rounding can leave us one short
    while len(out) < n:
        out.append(pts[-1])
    return out[:n]


def _scale(points: list[_P]) -> list[_P]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    size = max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0
    min_x, min_y = min(xs), min(ys)
    return [((x - min_x) / size, (y - min_y) / size, s) for x, y, s in points]


def _translate_to_origin(points: list[_P]) -> list[_P]:
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    return [(x - cx, y - cy, s) for x, y, s in points]
