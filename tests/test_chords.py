import unittest

import _path  # noqa: F401
from handful.chords import HOLD, RELEASE, REPEAT, TAP, ChordDetector
from handful.ticks import ticks_add

T, I, M, R, P = 1, 2, 4, 8, 16


def run(detector, steps):
    events = []
    for now, pressed in steps:
        events.extend((now, e, c) for e, c in detector.update(pressed, now))
    return events


class ChordDetectorTest(unittest.TestCase):
    def setUp(self):
        self.d = ChordDetector(hold_ms=400, repeat_delay_ms=400, repeat_interval_ms=50)

    def test_single_tap_fires_on_release(self):
        self.assertEqual(run(self.d, [(0, I), (100, I), (150, 0)]), [(150, TAP, I)])

    def test_staggered_chord_is_one_union(self):
        steps = [(0, T), (60, T | I), (120, I), (180, 0)]
        self.assertEqual(run(self.d, steps), [(180, TAP, T | I)])

    def test_nothing_while_idle(self):
        self.assertEqual(run(self.d, [(0, 0), (10, 0)]), [])

    def test_hold_fires_once_at_threshold_then_reports_the_release(self):
        steps = [(0, M), (399, M), (400, M), (500, M), (700, 0)]
        self.assertEqual(run(self.d, steps), [(400, HOLD, M), (700, RELEASE, M)])

    def test_repeats_after_delay_at_interval(self):
        steps = [(t, P) for t in range(0, 1000, 10)] + [(1000, 0)]
        events = run(self.d, steps)
        self.assertEqual(events[0], (400, HOLD, P))
        self.assertEqual([t for t, e, _ in events[1:-1]], [800, 850, 900, 950])
        self.assertTrue(all(e == REPEAT for _, e, _ in events[1:-1]))
        self.assertEqual(events[-1], (1000, RELEASE, P))

    def test_chord_frozen_after_hold(self):
        steps = [(0, I), (400, I), (450, I | M), (500, 0)]
        self.assertEqual(run(self.d, steps), [(400, HOLD, I), (500, RELEASE, I)])

    def test_next_chord_starts_fresh(self):
        steps = [(0, I), (50, 0), (100, M), (150, 0)]
        self.assertEqual(run(self.d, steps), [(50, TAP, I), (150, TAP, M)])

    def test_survives_tick_wrap(self):
        start = (1 << 29) - 100
        steps = [(start, R), (ticks_add(start, 399), R), (ticks_add(start, 400), R)]
        self.assertEqual(run(self.d, steps), [(ticks_add(start, 400), HOLD, R)])


if __name__ == "__main__":
    unittest.main()
