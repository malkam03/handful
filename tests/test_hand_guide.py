import contextlib
import io
import os
import re
import sys
import tempfile
import unittest

import _path  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import hand_guide  # noqa: E402
from drawings.measure import MEASUREMENTS  # noqa: E402


class HandGuideTest(unittest.TestCase):
    def test_names_every_measurement_the_cad_build_reads(self):
        with open(os.path.join(ROOT, "cad", "hand.example.toml")) as f:
            example = set(re.findall(r"^# (\w+) = ", f.read().split("[params]")[0], re.M))
        self.assertEqual({key for _, _, _, key in MEASUREMENTS}, example)

    def test_letters_match_the_example_file(self):
        with open(os.path.join(ROOT, "cad", "hand.example.toml")) as f:
            text = f.read()
        for letter, _, _, key in MEASUREMENTS:
            self.assertRegex(text, r"# {} = [\d.]+ +# {}\b".format(key, letter))

    def test_cli_writes_the_drawing(self):
        with tempfile.TemporaryDirectory() as docs, contextlib.redirect_stdout(io.StringIO()):
            hand_guide.main(["--docs", docs])
            self.assertEqual(os.listdir(docs), [hand_guide.NAME])

    def test_committed_drawing_is_current(self):
        with open(os.path.join(ROOT, "docs", hand_guide.NAME)) as f:
            committed = f.read()
        self.assertEqual(committed, hand_guide.render_measurements(),
                         "run python3 tools/hand_guide.py to redraw docs/" + hand_guide.NAME)


if __name__ == "__main__":
    unittest.main()
