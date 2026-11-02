import contextlib
import io
import os
import sys
import tempfile
import unittest

import _path  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import cheatsheet  # noqa: E402
from drawings.labels import UNMAPPED  # noqa: E402


class CheatsheetTest(unittest.TestCase):
    def test_draws_every_shipped_chord(self):
        svg = cheatsheet.render(os.path.join(ROOT, "firmware", "mappings.py"))
        for name in ("Push-to-talk", "Paste", "Delete word", "Select all", "Hold all five"):
            self.assertIn(name, svg)
        self.assertIn("Win+Shift+S", svg)
        self.assertIn("\u2318V", svg)

    def test_banner_draws_every_shipped_chord(self):
        svg = cheatsheet.render_banner(os.path.join(ROOT, "firmware", "mappings.py"))
        for name in ("Push-to-talk", "Paste", "Delete word", "Select all", "Hold all five"):
            self.assertIn(name, svg)

    def test_chord_in_one_mode_only_is_a_dash_in_the_other(self):
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write('MACOS = {"I": "ENTER",  # enter\n}\nWINDOWS = {}\n')
        try:
            for draw in (cheatsheet.render, cheatsheet.render_banner):
                svg = draw(f.name)
                self.assertIn("Return", svg)
                self.assertNotIn(">Enter<", svg)
                self.assertIn(UNMAPPED, svg)
        finally:
            os.remove(f.name)

    def test_cli_writes_both_drawings(self):
        with tempfile.TemporaryDirectory() as docs, contextlib.redirect_stdout(io.StringIO()):
            cheatsheet.main(["--docs", docs])
            self.assertEqual(sorted(os.listdir(docs)), ["cheatsheet.svg", "chords.svg"])

    def test_too_many_chords_in_a_group_is_explained(self):
        combos = ["I+M", "I+R", "I+P", "M+R", "M+P", "R+P", "I+M+R"]
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write("MACOS = {}\nWINDOWS = {}\n".format({c: "A" for c in combos}, {}))
        try:
            with self.assertRaises(SystemExit):
                cheatsheet.render(f.name)
        finally:
            os.remove(f.name)

    def test_committed_drawings_match_mappings(self):
        mappings = os.path.join(ROOT, "firmware", "mappings.py")
        for name, draw in (("cheatsheet.svg", cheatsheet.render), ("chords.svg", cheatsheet.render_banner)):
            with open(os.path.join(ROOT, "docs", name)) as f:
                committed = f.read()
            self.assertEqual(committed, draw(mappings), "run python3 tools/cheatsheet.py to redraw docs/" + name)


if __name__ == "__main__":
    unittest.main()
