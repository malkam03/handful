import unittest

import _path  # noqa: F401
import fakes
from handful import hid


class ReportTest(unittest.TestCase):
    def test_modifiers_set_bits_and_keys_fill_slots(self):
        # Left Ctrl (0xE0) and right GUI (0xE7) with A (0x04) and B (0x05).
        self.assertEqual(hid.report((0xE0, 0x04, 0xE7, 0x05)), bytes([0x81, 0, 0x04, 0x05, 0, 0, 0, 0]))

    def test_empty_report_releases_everything(self):
        self.assertEqual(hid.report(()), bytes(8))

    def test_more_than_six_keys_is_an_error(self):
        with self.assertRaises(ValueError):
            hid.report(range(0x04, 0x0B))


class KeyboardTest(unittest.TestCase):
    def test_uses_the_keyboard_device(self):
        mouse, keyboard = fakes.HIDDevice(0x01, 0x02), fakes.HIDDevice(0x01, 0x06)
        hid.Keyboard([mouse, keyboard]).press(0x04)
        self.assertEqual(keyboard.reports, [bytes([0, 0, 0x04, 0, 0, 0, 0, 0])])
        self.assertEqual(mouse.reports, [])

    def test_missing_keyboard_device_is_an_error(self):
        with self.assertRaises(ValueError):
            hid.Keyboard([fakes.HIDDevice(0x01, 0x02)])


if __name__ == "__main__":
    unittest.main()
