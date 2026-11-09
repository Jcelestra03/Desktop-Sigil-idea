import unittest

from sigil import themes


class ThemesTest(unittest.TestCase):
    def test_blend(self):
        self.assertEqual(themes.blend("#000000", "#ffffff", 0), "#000000")
        self.assertEqual(themes.blend("#000000", "#ffffff", 1), "#ffffff")
        self.assertEqual(themes.blend("#000000", "#ffffff", 0.5), "#808080")

    def test_themes_define_the_same_keys(self):
        # Adding a color to one theme but not the others would crash the window
        for theme in themes.THEMES.values():
            self.assertEqual(set(theme), set(themes.PARCHMENT), theme["name"])

    def test_unknown_theme_falls_back_to_candlelight(self):
        self.assertIs(themes.get("nope"), themes.CANDLELIGHT)
        self.assertIs(themes.get(None), themes.CANDLELIGHT)
        self.assertIs(themes.get("obsidian"), themes.OBSIDIAN)
        self.assertIs(themes.get("parchment"), themes.PARCHMENT)

    def test_painted_looks_have_their_art(self):
        from sigil import artbook
        for theme in themes.THEMES.values():
            if theme["art"]:
                for scale in artbook.info()["scales"]:
                    self.assertTrue(artbook.picture(theme["art"], scale).exists(),
                                    (theme["name"], scale))


if __name__ == "__main__":
    unittest.main()
