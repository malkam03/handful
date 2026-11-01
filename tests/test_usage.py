import unittest

import _path  # noqa: F401
from handful.usage import SIZE, Usage

M, ALL = 4, 31


class UsageTest(unittest.TestCase):
    def test_counts_taps_and_holds_apart(self):
        usage = Usage()
        usage.record("tap", M)
        usage.record("tap", M)
        usage.record("hold", ALL)
        self.assertTrue(usage.changed)
        self.assertEqual(usage.used(), [(M, 2, 0), (ALL, 0, 1)])

    def test_round_trips_through_bytes(self):
        usage = Usage()
        usage.record("hold", 1)
        data = usage.to_bytes()
        self.assertEqual(len(data), SIZE)
        loaded = Usage(data)
        self.assertEqual(loaded.used(), [(1, 0, 1)])
        self.assertFalse(loaded.changed)

    def test_ignores_data_of_the_wrong_size(self):
        self.assertEqual(Usage(b"\xff" * 3).used(), [])

    def test_stops_at_the_largest_count(self):
        usage = Usage(b"\xff" * SIZE)
        usage.record("tap", M)
        self.assertFalse(usage.changed)
        self.assertEqual(usage.count("tap", M), 0xFFFFFFFF)

    def test_reset(self):
        usage = Usage(b"\x01" * SIZE)
        usage.reset()
        self.assertEqual(usage.used(), [])
        self.assertTrue(usage.changed)


if __name__ == "__main__":
    unittest.main()
