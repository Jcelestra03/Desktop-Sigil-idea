import math
import os
import re
import tempfile
import unittest
from pathlib import Path

from sigil import tutorial

ROOT = Path(__file__).resolve().parent.parent


def ellipse(cx, cy, rx, ry, wobble=0.0):
    return [[(cx + rx * math.cos(a / 48 * 2 * math.pi) + wobble * math.sin(a * 1.7),
              cy + ry * math.sin(a / 48 * 2 * math.pi) + wobble * math.cos(a * 2.3))
             for a in range(50)]]


class HelpTextTest(unittest.TestCase):
    def test_every_help_key_used_exists(self):
        source = (ROOT / "sigil" / "manager.py").read_text(encoding="utf-8")
        used = set(re.findall(r'help_mark\([^,]+, "(\w+)"', source))
        used |= set(re.findall(r'_help\([^,]+, "(\w+)"', source))
        used |= set(re.findall(r'_titled\([^,]+, "[^"]*", "(\w+)"\)', source))
        used |= set(re.findall(r'"(\w+)"\)(?:,|\])', source)) & set(tutorial.HELP)
        self.assertGreater(len(used), 15)
        self.assertLessEqual(used, set(tutorial.HELP))

    def test_help_texts_are_short(self):
        for key, (title, text) in tutorial.HELP.items():
            self.assertTrue(title and text, key)
            self.assertLess(len(text), 200, key)


class PracticeTest(unittest.TestCase):
    def test_a_hand_drawn_circle_is_a_circle(self):
        name, score = tutorial.check_practice(ellipse(400, 300, 160, 120, wobble=6))
        self.assertEqual(name, tutorial.PRACTICE_TARGET)
        self.assertGreater(score, 0.5)

    def test_other_shapes_are_not_circles(self):
        triangle = [[(100 + 80 * t, 20 + 150 * t) for t in (i / 20 for i in range(21))]
                    + [(180 - 160 * t, 170) for t in (i / 20 for i in range(1, 21))]
                    + [(20 + 80 * t, 170 - 150 * t) for t in (i / 20 for i in range(1, 21))]]
        self.assertNotEqual(tutorial.check_practice(triangle)[0], tutorial.PRACTICE_TARGET)
        line = [[(10 + i * 10, 200) for i in range(30)]]
        self.assertNotEqual(tutorial.check_practice(line)[0], tutorial.PRACTICE_TARGET)


class TourTest(unittest.TestCase):
    """Opens a real Sigil Book with empty, temporary sigils and settings."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.environ.get("SIGIL_FILE")
        os.environ["SIGIL_FILE"] = str(Path(self.tmp.name) / "sigils.json")
        from sigil import store
        store.save_settings({"hotkey": "ctrl+alt+shift+f10", "orb": False})
        from sigil.manager import SigilBook
        self.book = SigilBook()
        self.book.root.geometry("1160x760")
        self.book.root.update()
        self.book.redraw()

    def tearDown(self):
        root = self.book.root
        for job in root.tk.splitlist(root.tk.call("after", "info")):
            root.after_cancel(job)
        self.book.quit()
        if self.old is None:
            os.environ.pop("SIGIL_FILE", None)
        else:
            os.environ["SIGIL_FILE"] = self.old
        self.tmp.cleanup()

    def test_first_launch_shows_the_tour_once(self):
        from sigil import store
        self.book.root.after(600, self.book.root.quit)
        self.book.root.mainloop()
        self.assertIsNotNone(self.book.tour)
        self.assertTrue(store.load_settings()["tutorial_seen"])

    def test_every_step_outlines_its_part_and_has_buttons(self):
        book = self.book
        book.start_tour()
        for i, step in enumerate(tutorial.STEPS):
            book.tour.go(i)
            if step.region:
                self.assertIn(step.region, book.regions)
            self.assertTrue(book.canvas.find_withtag("tour"), i)
            left, right = book.tour._buttons()
            self.assertTrue(right, i)
        book.tour.end()
        self.assertIsNone(book.tour)
        self.assertFalse(book.canvas.find_withtag("tour"))

    def test_book_buttons_have_help(self):
        tips = {h.tip for h in self.book.hits if h.tip}
        self.assertTrue({"theme", "index", "inscribe", "cast", "test", "receive", "hotkey",
                         "orb"} <= tips)


if __name__ == "__main__":
    unittest.main()
