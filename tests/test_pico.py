import importlib
import os
import runpy
import unittest
from unittest import mock

import _path  # noqa: F401
import fakes
from handful.usage import SIZE

FIRMWARE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "firmware")


class PicoTest(unittest.TestCase):
    def setUp(self):
        self.hw = fakes.install()
        import handful.pico as pico

        pico = importlib.reload(pico)

        self.pico_module = pico
        self.pico = pico.Pico()
        self.buttons = fakes.DigitalInOut.instances[:5]
        self.leds = fakes.DigitalInOut.instances[5:]

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

    def test_usage_is_saved_after_the_mode_byte(self):
        self.assertIsNone(self.pico.load_usage())
        self.pico.save_mode("windows")
        data = bytes(i % 256 for i in range(SIZE))
        self.pico.save_usage(data)
        self.assertEqual(self.pico.load_usage(), data)
        self.assertEqual(self.pico.load_mode(), "windows")

    def test_read_line_collects_serial_input_without_waiting(self):
        runtime = self.hw.supervisor.runtime
        pending = list("usa")

        def read(n):
            char = pending.pop(0)
            runtime.serial_bytes_available = len(pending)
            return char

        runtime.serial_bytes_available = len(pending)
        with mock.patch.object(self.pico_module.sys, "stdin", mock.Mock(read=read)):
            self.assertIsNone(self.pico.read_line())
            pending[:] = list("ge\r\n" + "x" * 100 + "\n")
            runtime.serial_bytes_available = len(pending)
            self.assertEqual(self.pico.read_line(), "usage")
            self.assertEqual(self.pico.read_line(), "x" * self.pico_module.MAX_LINE)
            self.assertIsNone(self.pico.read_line())

    def lit(self):
        """(onboard, red, green, blue)"""
        return tuple(led.value for led in self.leds)

    def test_leds_start_off(self):
        self.assertEqual([led.pin.name for led in self.leds], ["LED", "GP28", "GP27", "GP26"])
        self.assertEqual(self.lit(), (False, False, False, False))

    def test_leds_show_the_mode(self):
        self.pico.show_mode("macos")
        self.assertEqual(self.lit(), (True, False, True, False))
        self.pico.show_mode("windows")
        self.assertEqual(self.lit(), (False, False, False, True))

    def test_never_two_colours_at_once_while_switching(self):
        rgb = self.leds[1:]
        seen = []

        class Watched(type(rgb[0])):
            def __setattr__(led, name, value):
                object.__setattr__(led, name, value)
                if name == "value":
                    seen.append(sum(1 for pin in rgb if pin.value))

        for led in rgb:
            led.__class__ = Watched
        self.pico.show_mode("windows")
        self.pico.show_mode("macos")
        self.pico.show_mode("windows")
        with mock.patch.object(self.pico_module.time, "sleep", side_effect=StopIteration):
            with self.assertRaises(StopIteration):
                self.pico.blink_error()
        self.assertTrue(seen)
        self.assertLessEqual(max(seen), 1)

    def test_blink_error_blinks_onboard_and_red_together(self):
        self.pico.show_mode("macos")
        seen = []

        def sleep(seconds):
            seen.append(self.lit())
            if len(seen) == 3:
                raise StopIteration

        with mock.patch.object(self.pico_module.time, "sleep", side_effect=sleep):
            with self.assertRaises(StopIteration):
                self.pico.blink_error()
        on, off = (True, True, False, False), (False, False, False, False)
        self.assertEqual(seen, [on, off, on])

    def test_code_py_runs_the_app_on_the_pico(self):
        with mock.patch("handful.app.run") as run:
            runpy.run_path(os.path.join(FIRMWARE, "code.py"))
        board, load = run.call_args[0]
        self.assertIsInstance(board, self.pico_module.Pico)
        with mock.patch.dict("sys.modules", {"mappings": "loaded"}):
            self.assertEqual(load(), "loaded")


if __name__ == "__main__":
    unittest.main()
