import unittest

import _path  # noqa: F401
from handful import config
from handful.keypad import SEND, SET_MODE, Keypad
from handful.keys import parse_keys
from handful.usage import Usage
from test_config import shipped_mappings

T, I, M, R, P = 1, 2, 4, 8, 16
ALL = 31


def run(keypad, steps):
    out = []
    for now, pressed in steps:
        out.extend(keypad.update(pressed, now))
    return out


def tap(chord, at=0):
    return [(at, chord), (at + 50, 0)]


def hold(chord, until, at=0):
    return [(t, chord) for t in range(at, at + until, 10)] + [(at + until, 0)]


class KeypadTest(unittest.TestCase):
    def setUp(self):
        self.keypad = Keypad(config.load(shipped_mappings()), "macos")

    def test_tap_sends_mode_specific_keys(self):
        self.assertEqual(run(self.keypad, tap(M)), [(SEND, parse_keys("CMD+V"))])
        self.keypad.mode = "windows"
        self.assertEqual(run(self.keypad, tap(M, 100)), [(SEND, parse_keys("CTRL+V"))])

    def test_unmapped_chord_does_nothing(self):
        self.assertEqual(run(self.keypad, tap(T | I | P)), [])

    def test_adding_fingers_cancels(self):
        steps = [(0, T), (50, T | I), (150, ALL), (250, 0)]
        self.assertEqual(run(self.keypad, steps), [])

    def test_tapping_all_five_does_nothing(self):
        self.assertEqual(run(self.keypad, tap(ALL)), [])
        self.assertEqual(self.keypad.mode, "macos")

    def test_holding_all_five_toggles_mode_once(self):
        self.assertEqual(run(self.keypad, hold(ALL, 2000)), [(SET_MODE, "windows")])
        self.assertEqual(run(self.keypad, hold(ALL, 500, at=3000)), [(SET_MODE, "macos")])

    def test_held_once_action_fires_once(self):
        self.assertEqual(run(self.keypad, hold(M | R, 2000)), [(SEND, parse_keys("CMD+Z"))])

    def test_held_repeat_action_repeats(self):
        sent = run(self.keypad, hold(P, 1000))
        self.assertEqual(len(sent), 1 + 4)
        self.assertTrue(all(s == (SEND, parse_keys("BACKSPACE")) for s in sent))

    def test_counts_taps_and_holds_mapped_or_not(self):
        usage = Usage()
        keypad = Keypad(self.keypad.config, "macos", usage)
        run(keypad, tap(M) + hold(P, 1000, at=100) + tap(T | I | P, at=2000) + hold(ALL, 500, at=3000))
        self.assertEqual(usage.used(), [(M, 1, 0), (P, 0, 1), (T | I | P, 1, 0), (ALL, 0, 1)])

    def test_unknown_saved_mode_falls_back_to_macos(self):
        self.assertEqual(Keypad(self.keypad.config, "linux").mode, "macos")


if __name__ == "__main__":
    unittest.main()
