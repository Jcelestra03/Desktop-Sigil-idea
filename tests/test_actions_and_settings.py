import os
import tempfile
import unittest
from pathlib import Path

from sigil import store
from sigil.actions import normalize_target
from sigil.hotkey import MOD_ALT, MOD_CONTROL, MOD_WIN, VK_SPACE, parse, pretty


class NormalizeTargetTest(unittest.TestCase):
    def test_bare_web_address_gets_https(self):
        self.assertEqual(normalize_target("url", " canvas.uw.edu "), "https://canvas.uw.edu")

    def test_full_and_custom_scheme_urls_are_kept(self):
        self.assertEqual(normalize_target("url", "http://x.com"), "http://x.com")
        self.assertEqual(normalize_target("url", "steam://rungameid/570"), "steam://rungameid/570")

    def test_paths_are_cleaned(self):
        self.assertEqual(normalize_target("app", '"C:/Games/thing.exe"'),
                         os.path.normpath("C:/Games/thing.exe"))
        self.assertEqual(normalize_target("app", "notepad.exe"), "notepad.exe")


class HotkeyParseTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse("ctrl+alt+space"), (MOD_CONTROL | MOD_ALT, VK_SPACE))
        self.assertEqual(parse("Win + Alt + S"), (MOD_WIN | MOD_ALT, ord("S")))
        self.assertEqual(parse("ctrl+f2")[1], 0x71)

    def test_bad_hotkeys(self):
        for bad in ("ctrl+banana+x", "s", "ctrl+enter"):
            with self.assertRaises(ValueError, msg=bad):
                parse(bad)

    def test_pretty(self):
        self.assertEqual(pretty("ctrl+alt+s"), "Ctrl+Alt+S")
        self.assertEqual(pretty("win+f12"), "Win+F12")


class SettingsTest(unittest.TestCase):
    def test_defaults_and_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "settings.json"
            settings = store.load_settings(path)
            self.assertEqual(settings["hotkey"], "ctrl+alt+s")
            settings["orb_pos"] = [10, 20]
            store.save_settings(settings, path)
            self.assertEqual(store.load_settings(path)["orb_pos"], [10, 20])


if __name__ == "__main__":
    unittest.main()
