import tempfile
import tkinter as tk
import unittest
from pathlib import Path

from sigil import store
from sigil.drawpad import PENS, DrawPad, draw_strokes, render_stroke

ZIGZAG = [(10, 10), (40, 60), (70, 10), (100, 60)]


class PensTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def test_every_pen_draws_something(self):
        for pen in PENS:
            c = tk.Canvas(self.root)
            render_stroke(c, ZIGZAG, pen, 6, "#a32a1e", "#efdfbd")
            self.assertGreater(len(c.find_all()), 0, pen)
            c.destroy()

    def test_thumbnail_with_style(self):
        c = tk.Canvas(self.root)
        draw_strokes(c, [ZIGZAG], 0, 0, 40, 40, "#000000", 2,
                     style={"pen": "calligraphy", "size": 9, "color": None}, bg="#ffffff")
        self.assertGreater(len(c.find_all()), 0)
        c.destroy()

    def test_pad_undo_and_restyle_keep_points(self):
        pad = DrawPad(self.root, size=200)
        pad.strokes = [list(ZIGZAG), [(5, 5), (50, 50)]]
        pad.set_style({"pen": "spray", "size": 10, "color": "#123456"})
        self.assertEqual(pad.drawing[0], ZIGZAG)  # pens never change the points
        pad.undo()
        self.assertEqual(len(pad.strokes), 1)
        pad.destroy()


class StyleStorageTest(unittest.TestCase):
    def test_style_round_trip_and_old_files(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sigils.json"
            style = {"pen": "quill", "size": 8, "color": None}
            store.save([store.Sigil("A", {"type": "url", "target": "x"}, [[ZIGZAG]], style),
                        store.Sigil("B", {"type": "url", "target": "y"}, [[ZIGZAG]])], path)
            a, b = store.load(path)
            self.assertEqual(a.style, style)
            self.assertEqual(b.style, {})  # sigils saved before pens existed still load


if __name__ == "__main__":
    unittest.main()
