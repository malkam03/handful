import importlib
import os
import runpy
import unittest
from unittest import mock

import _path  # noqa: F401
import fakes

FIRMWARE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "firmware")


class PicoTest(unittest.TestCase):
    def setUp(self):
        self.hw = fakes.install()
        import handful.pico as pico

        pico = importlib.reload(pico)

        self.pico_module = pico
        self.pico = pico.Pico()
        self.buttons = fakes.DigitalInOut.instances[:5]
        self.led = fakes.DigitalInOut.instances[5]

    def test_buttons_follow_the_config_order_with_pull_ups(self):
        self.assertEqual([b.pin.name for b in self.buttons], ["GP2", "GP3", "GP4", "GP5", "GP6"])
        self.assertTrue(all(b.pull == "up" for b in self.buttons))

    def test_read_is_active_low(self):
        self.assertEqual(self.pico.read(), 0)
        self.buttons[0].value = False
        self.buttons[4].value = False
        self.assertEqual(self.pico.read(), 0b10001)

    def test_now_uses_supervisor_ticks(self):
        self.assertEqual(self.pico.now(), 1234)

    def test_press_and_release_send_keyboard_reports(self):
        self.pico.press((0xE3, 0x19))
        self.pico.release_all()
        self.assertEqual(self.hw.keyboard.reports, [bytes([0x08, 0, 0x19, 0, 0, 0, 0, 0]), bytes(8)])

    def test_mode_is_saved_in_nvm(self):
        self.assertEqual(self.pico.load_mode(), "macos")
        self.pico.save_mode("windows")
        self.assertEqual(self.hw.microcontroller.nvm[0], ord("W"))
        self.assertEqual(self.pico.load_mode(), "windows")

    def test_led_shows_the_mode(self):
        self.pico.show_mode("macos")
        self.assertTrue(self.led.value)
        self.pico.show_mode("windows")
        self.assertFalse(self.led.value)

    def test_blink_error_toggles_the_led(self):
        with mock.patch.object(self.pico_module.time, "sleep", side_effect=StopIteration):
            with self.assertRaises(StopIteration):
                self.pico.blink_error()
        self.assertTrue(self.led.value)

    def test_code_py_runs_the_app_on_the_pico(self):
        with mock.patch("handful.app.run") as run:
            runpy.run_path(os.path.join(FIRMWARE, "code.py"))
        board, load = run.call_args[0]
        self.assertIsInstance(board, self.pico_module.Pico)
        with mock.patch.dict("sys.modules", {"mappings": "loaded"}):
            self.assertEqual(load(), "loaded")


if __name__ == "__main__":
    unittest.main()
