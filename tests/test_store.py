import tempfile
import unittest
from pathlib import Path

from sigil import store


class StoreTest(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sigils.json"
            sigils = [store.Sigil("Canvas", {"type": "url", "target": "https://canvas.uw.edu"},
                                  [[[(1.0, 2.0), (3.25, 4.0)]], [[(0, 0), (9, 9)], [(1, 1), (2, 2)]]])]
            store.save(sigils, path)
            loaded = store.load(path)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].name, "Canvas")
            self.assertEqual(loaded[0].action["target"], "https://canvas.uw.edu")
            self.assertEqual(loaded[0].templates[0], [[(1.0, 2.0), (3.2, 4.0)]])
            self.assertEqual(len(loaded[0].templates[1]), 2)

    def test_missing_file_is_empty(self):
        self.assertEqual(store.load(Path(tempfile.gettempdir()) / "no-such-sigils.json"), [])

    def test_find_ignores_case(self):
        sigils = [store.Sigil("Steam", {"type": "app", "target": "steam.exe"})]
        self.assertIs(store.find(sigils, "steam"), sigils[0])
        self.assertIsNone(store.find(sigils, "discord"))


if __name__ == "__main__":
    unittest.main()
