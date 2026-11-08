import math
import os
import random
import tempfile
import unittest

from sigil import share
from sigil.recognizer import compare
from sigil.store import Sigil

from .shapes import circle, triangle

JEM = {"USERPROFILE": r"C:\Users\jem", "LOCALAPPDATA": r"C:\Users\jem\AppData\Local",
       "APPDATA": r"C:\Users\jem\AppData\Roaming", "ProgramFiles": r"C:\Program Files",
       "ProgramFiles(x86)": r"C:\Program Files (x86)", "SystemRoot": r"C:\WINDOWS",
       "ProgramData": r"C:\ProgramData", "TEMP": r"C:\Users\jem\AppData\Local\Temp"}
JUN = {**JEM, "USERPROFILE": r"D:\Home\jun", "LOCALAPPDATA": r"D:\Home\jun\AppData\Local",
       "APPDATA": r"D:\Home\jun\AppData\Roaming"}


def hand_drawn(seed=1, points=220, size=600, wobble=1.0):
    """A wobbly, mouse-like drawing: a loop and a line, a few px between points."""
    rng = random.Random(seed)
    loop = [(size / 2 + size * .4 * math.cos(t / points * 2 * math.pi) + rng.uniform(-wobble, wobble),
             size / 2 + size * .4 * math.sin(t / points * 2 * math.pi) + rng.uniform(-wobble, wobble))
            for t in range(points + 1)]
    cross = [(100 + i * 4 + rng.uniform(-wobble, wobble), 100 + i * 4 + rng.uniform(-wobble, wobble))
             for i in range(100)]
    return [loop, cross]


def sigil(target=r"C:\Users\jem\AppData\Local\Discord\Update.exe", kind="app", templates=None):
    return Sigil("Discord", {"type": kind, "target": target},
                 templates or [hand_drawn(1), hand_drawn(2), hand_drawn(3)],
                 {"pen": "quill", "size": 8, "color": "#a32a1e"})


class PathTest(unittest.TestCase):
    def test_paths_become_portable_and_local_again(self):
        shared = share.portable_target("app", r"C:\Users\jem\AppData\Local\Discord\Update.exe",
                                       JEM)
        self.assertEqual(shared, r"%LOCALAPPDATA%\Discord\Update.exe")
        self.assertEqual(share.local_target("app", shared, JUN),
                         r"D:\Home\jun\AppData\Local\Discord\Update.exe")

    def test_most_specific_place_wins_and_case_is_ignored(self):
        self.assertEqual(share.portable_target("file", r"c:\users\JEM\Documents\a.txt", JEM),
                         r"%USERPROFILE%\Documents\a.txt")
        self.assertEqual(share.portable_target("app", r"C:\Program Files (x86)\Steam\steam.exe",
                                               JEM), r"%ProgramFiles(x86)%\Steam\steam.exe")

    def test_urls_and_bare_names_are_untouched(self):
        self.assertEqual(share.portable_target("url", "https://canvas.uw.edu", JEM),
                         "https://canvas.uw.edu")
        self.assertEqual(share.portable_target("app", "notepad.exe", JEM), "notepad.exe")

    def test_32_and_64_bit_program_files_both_tried(self):
        found = {r"C:\Program Files\Steam\steam.exe"}
        target, ok = share.find_target("app", r"%ProgramFiles(x86)%\Steam\steam.exe", JUN,
                                       exists=found.__contains__)
        self.assertTrue(ok)
        self.assertEqual(target, r"C:\Program Files\Steam\steam.exe")

    def test_unknown_place_is_not_found(self):
        _, ok = share.find_target("app", r"%ONEDRIVE%\x.exe", JUN, exists=lambda p: True)
        self.assertFalse(ok)

    def test_missing_target_is_reported(self):
        target, ok = share.find_target("app", r"%LOCALAPPDATA%\Discord\Update.exe", JUN,
                                       exists=lambda p: False)
        self.assertFalse(ok)
        self.assertTrue(target.startswith(r"D:\Home\jun"))


class ReviewTest(unittest.TestCase):
    def test_normal_things_have_no_notes(self):
        self.assertEqual(share.review("url", "https://canvas.uw.edu", JUN), [])
        self.assertEqual(share.review("app", r"C:\Program Files (x86)\Steam\steam.exe", JUN), [])
        self.assertEqual(share.review("app", r"D:\Home\jun\AppData\Local\Discord\Update.exe",
                                      JUN), [])
        self.assertEqual(share.review("app", "notepad.exe", JUN), [])
        self.assertEqual(share.review("folder", r"D:\Home\jun\Documents", JUN), [])

    def test_scripts_and_odd_places_are_flagged(self):
        self.assertTrue(share.review("app", r"C:\Program Files\x\run.bat", JUN))
        self.assertTrue(share.review("file", r"D:\Home\jun\Downloads\cute.ps1", JUN))
        self.assertTrue(share.review("file", r"D:\Home\jun\Downloads\photo.exe", JUN))
        self.assertTrue(share.review("app", r"D:\Home\jun\Downloads\game.exe", JUN))
        self.assertTrue(share.review("app", r"C:\Users\jem\AppData\Local\Temp\x.exe", JEM))
        self.assertTrue(share.review("url", "file:///C:/x.exe", JUN))


class CodeTest(unittest.TestCase):
    def test_round_trip_through_a_code(self):
        original = sigil()
        code = share.to_code(original, JEM)
        self.assertTrue(code.startswith(share.CODE_PREFIX))
        self.assertLessEqual(len(code), share.MAX_CODE_CHARS)
        got = share.from_code(code)
        self.assertEqual(got.name, "Discord")
        self.assertEqual(got.shared_target, r"%LOCALAPPDATA%\Discord\Update.exe")
        self.assertEqual(got.style, {"pen": "quill", "size": 8, "color": "#a32a1e"})
        self.assertEqual(len(got.templates), 3)
        # still recognized as the same drawing
        for a, b in zip(original.templates, got.templates):
            self.assertGreater(compare(a, b), 0.9)

    def test_code_found_inside_a_chat_message_with_line_breaks(self):
        code = share.to_code(sigil(), JEM)
        message = f"here's my discord sigil!!\n{code[:40]}\n{code[40:90]} {code[90:]}\nenjoy"
        self.assertEqual(share.from_code(message).name, "Discord")

    def test_very_detailed_drawings_still_fit_one_message(self):
        busy = [hand_drawn(i, points=900) for i in range(6)]
        code = share.to_code(sigil(templates=busy), JEM)
        self.assertLessEqual(len(code), share.MAX_CODE_CHARS)
        got = share.from_code(code)
        # the simplified drawing still matches the shape, and not a different one
        clean = hand_drawn(0, wobble=0)
        for t in got.templates:
            self.assertGreater(compare(clean, t), 0.85)
            self.assertGreater(compare(clean, t), compare(triangle(), t) + 0.2)

    def test_damaged_codes_are_refused(self):
        code = share.to_code(sigil(), JEM)
        for bad in ("hello", code[:-30], code[:50] + "AAAA" + code[54:], share.CODE_PREFIX):
            with self.assertRaises(share.ShareError):
                share.from_code(bad)


class FileTest(unittest.TestCase):
    def test_round_trip_through_a_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "Canvas.sigil")
            share.save_file(Sigil("Canvas", {"type": "url", "target": "https://canvas.uw.edu"},
                                  [circle(), triangle()]), path, JEM)
            got = share.load_file(path)
        self.assertEqual(got.name, "Canvas")
        self.assertEqual(got.target, "https://canvas.uw.edu")
        self.assertEqual(len(got.templates), 2)

    def test_not_a_sigil(self):
        for text in ("{}", "[1,2]", "not json", '{"format": "desktop-sigil", "name": "x"}'):
            with self.assertRaises(share.ShareError):
                share.from_file_text(text)

    def test_bad_fields_are_refused_or_cleaned(self):
        base = {"format": "desktop-sigil", "version": 1, "name": "  Odd \n name ",
                "action": {"type": "app", "target": "x.exe"},
                "style": {"pen": "laser", "size": 999, "color": "red; drop"},
                "templates": [[[[0, 0], [5, 5]]]]}
        import json
        got = share.from_file_text(json.dumps(base))
        self.assertEqual(got.name, "Odd name")
        self.assertEqual(got.style, {})
        for change in ({"action": {"type": "shell", "target": "x"}},
                       {"templates": []}, {"templates": [[[["a", "b"]]]]},
                       {"templates": [[[[0, 0], [1e9, 0]]]]}, {"version": 99}):
            with self.assertRaises(share.ShareError):
                share.from_file_text(json.dumps({**base, **change}))


class NameTest(unittest.TestCase):
    def test_free_name(self):
        self.assertEqual(share.free_name("Canvas", ["Steam"]), "Canvas")
        self.assertEqual(share.free_name("Canvas", ["canvas", "Canvas (2)"]), "Canvas (3)")


if __name__ == "__main__":
    unittest.main()
