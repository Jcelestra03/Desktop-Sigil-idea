import random
import unittest
from dataclasses import dataclass, field

from sigil.recognizer import DEFAULT_MIN_SCORE, compare, normalize, recognize
from tests.shapes import SHAPES, wobble


@dataclass
class FakeSigil:
    name: str
    templates: list = field(default_factory=list)


def library(rng: random.Random, samples: int = 3) -> list[FakeSigil]:
    return [FakeSigil(name, [wobble(make(), rng) for _ in range(samples)])
            for name, make in SHAPES.items()]


class RecognizeTest(unittest.TestCase):
    def test_recognizes_each_shape(self):
        rng = random.Random(42)
        sigils = library(rng)
        for name, make in SHAPES.items():
            for _ in range(10):
                match = recognize(wobble(make(), rng), sigils)
                self.assertIsNotNone(match, name)
                self.assertEqual(match.sigil.name, name)

    def test_stroke_order_and_direction_do_not_matter(self):
        drawing = SHAPES["circle_cross"]()
        reordered = [list(reversed(s)) for s in reversed(drawing)]
        self.assertGreater(compare(drawing, reordered), 0.95)

    def test_size_and_position_do_not_matter(self):
        rng = random.Random(0)
        small = wobble(SHAPES["star"](), rng, jitter=0, scale=0.5, offset=(0, 0))
        big = wobble(SHAPES["star"](), rng, jitter=0, scale=3, offset=(900, 400))
        self.assertGreater(compare(small, big), 0.95)

    def test_unknown_shape_is_rejected(self):
        rng = random.Random(7)
        sigils = [s for s in library(rng) if s.name != "circle"]
        self.assertIsNone(recognize(wobble(SHAPES["circle"](), rng, jitter=1), sigils))

    def test_different_shapes_score_below_threshold(self):
        rng = random.Random(3)
        names = list(SHAPES)
        for a in names:
            for b in names:
                if a != b:
                    score = compare(wobble(SHAPES[a](), rng), wobble(SHAPES[b](), rng))
                    self.assertLess(score, DEFAULT_MIN_SCORE, f"{a} vs {b}")

    def test_empty_and_dot_drawings(self):
        sigils = library(random.Random(1))
        self.assertIsNone(recognize([], sigils))
        self.assertIsNone(recognize([[(5, 5), (5, 5)]], sigils))
        self.assertIsNone(normalize([[(5, 5)]]))

    def test_straight_line_does_not_crash(self):
        line = [[(0, 0), (0, 100)]]
        self.assertEqual(len(normalize(line)), 32)
        self.assertGreater(compare(line, [[(300, 0), (300, 50)]]), 0.95)


if __name__ == "__main__":
    unittest.main()
