import unittest

from sigil import themes


class ThemesTest(unittest.TestCase):
    def test_blend(self):
        self.assertEqual(themes.blend("#000000", "#ffffff", 0), "#000000")
        self.assertEqual(themes.blend("#000000", "#ffffff", 1), "#ffffff")
        self.assertEqual(themes.blend("#000000", "#ffffff", 0.5), "#808080")

    def test_themes_define_the_same_keys(self):
        # Adding a color to one theme but not the other would crash the window
        parchment, obsidian = themes.PARCHMENT, themes.OBSIDIAN
        self.assertEqual(set(parchment), set(obsidian))

    def test_unknown_theme_falls_back_to_parchment(self):
        self.assertIs(themes.get("nope"), themes.PARCHMENT)
        self.assertIs(themes.get(None), themes.PARCHMENT)
        self.assertIs(themes.get("obsidian"), themes.OBSIDIAN)


if __name__ == "__main__":
    unittest.main()
