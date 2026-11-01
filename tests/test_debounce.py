import unittest

import _path  # noqa: F401
from handful.debounce import Debouncer


class DebouncerTest(unittest.TestCase):
    def test_press_registers_after_stable_period(self):
        d = Debouncer(5, 5)
        self.assertEqual(d.update(0b1, 0), 0)
        self.assertEqual(d.update(0b1, 4), 0)
        self.assertEqual(d.update(0b1, 5), 0b1)

    def test_bounce_restarts_the_timer(self):
        d = Debouncer(5, 5)
        d.update(0b1, 0)
        d.update(0b0, 2)
        d.update(0b1, 3)
        self.assertEqual(d.update(0b1, 7), 0)
        self.assertEqual(d.update(0b1, 8), 0b1)

    def test_release_is_debounced_too(self):
        d = Debouncer(5, 5)
        d.update(0b1, 0)
        d.update(0b1, 5)
        d.update(0b0, 10)
        self.assertEqual(d.update(0b0, 14), 0b1)
        self.assertEqual(d.update(0b0, 15), 0)

    def test_buttons_are_independent(self):
        d = Debouncer(5, 5)
        d.update(0b01, 0)
        d.update(0b11, 3)
        self.assertEqual(d.update(0b11, 5), 0b01)
        self.assertEqual(d.update(0b11, 8), 0b11)


if __name__ == "__main__":
    unittest.main()
