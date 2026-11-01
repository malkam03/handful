import os
import types
import unittest

import _path  # noqa: F401
from handful import config
from handful.keys import parse_keys

MAPPINGS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "firmware", "mappings.py")


def module(**attrs):
    m = types.SimpleNamespace(MACOS={}, WINDOWS={})
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


def shipped_mappings():
    m = types.ModuleType("mappings")
    with open(MAPPINGS) as f:
        exec(f.read(), m.__dict__)
    return m


class ParseChordTest(unittest.TestCase):
    def test_bits_and_order(self):
        self.assertEqual(config.parse_chord("T"), 1)
        self.assertEqual(config.parse_chord("P"), 16)
        self.assertEqual(config.parse_chord("i+t"), config.parse_chord("T+I"))
        self.assertEqual(config.parse_chord("T+I+M+R+P"), 31)

    def test_rejects_bad_chords(self):
        for bad in ("X", "T+T", "", "TI", None):
            with self.assertRaises(ValueError):
                config.parse_chord(bad)

    def test_chord_name(self):
        self.assertEqual(config.chord_name(config.parse_chord("P+T+M")), "T+M+P")


class LoadTest(unittest.TestCase):
    def test_shipped_mappings_load(self):
        c = config.load(shipped_mappings())
        self.assertEqual((c.hold_ms, c.repeat_delay_ms, c.repeat_interval_ms), (400, 400, 50))
        self.assertEqual(c.mode_chord, 31)
        for mode in ("macos", "windows"):
            self.assertEqual(len(c.sets[mode]), 15)
        p = config.parse_chord("P")
        self.assertTrue(c.sets["macos"][p].repeat)
        self.assertFalse(c.sets["macos"][config.parse_chord("M+R")].repeat)
        self.assertEqual(c.sets["windows"][config.parse_chord("M")].keys, parse_keys("CTRL+V"))
        self.assertFalse(c.count_chords)

    def test_count_chords_can_be_turned_on(self):
        self.assertTrue(config.load(module(COUNT_CHORDS=True)).count_chords)

    def test_defaults_when_settings_missing(self):
        c = config.load(module())
        self.assertEqual((c.hold_ms, c.repeat_delay_ms, c.repeat_interval_ms, c.mode_chord), (400, 400, 50, 31))

    def test_reports_every_problem(self):
        m = module(
            HOLD_MS="slow",
            COUNT_CHORDS="yes",
            MACOS={"X": "ENTER", "I": "NOPE", "M": ("V", "twice"), "T+I+M+R+P": "A"},
            WINDOWS={"I": "ENTER", "i": "ENTER"},
        )
        with self.assertRaises(config.MappingError) as ctx:
            config.load(m)
        message = str(ctx.exception)
        for fragment in ("HOLD_MS", "COUNT_CHORDS", "'X'", "NOPE", "twice", "MODE_CHORD", "mapped twice"):
            self.assertIn(fragment, message)

    def test_missing_set(self):
        m = types.SimpleNamespace(MACOS={})
        with self.assertRaises(config.MappingError) as ctx:
            config.load(m)
        self.assertIn("WINDOWS", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
