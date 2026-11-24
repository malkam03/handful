import contextlib
import io
import types
import unittest

import _path  # noqa: F401
from handful import app
from handful.keys import parse_keys
from handful.usage import Usage
from test_config import shipped_mappings

M, ALL = 4, 31


class FakeBoard:
    DEBOUNCE_MS = 5

    def __init__(self, mode="macos"):
        self.time = 0
        self.buttons = 0
        self.mode = mode
        self.led = None
        self.dark = None
        self.log = []
        self.fail_press = 0
        self.fail_release = 0
        self.blinking = False
        self.usage = None
        self.usage_saves = 0
        self.lines = []

    def now(self):
        return self.time

    def read(self):
        return self.buttons

    def press(self, keys):
        if self.fail_press:
            self.fail_press -= 1
            raise OSError("USB busy")
        self.log.append(("press", keys))

    def release_all(self):
        if self.fail_release:
            self.fail_release -= 1
            raise OSError("USB busy")
        self.log.append(("release_all",))

    def load_mode(self):
        return self.mode

    def save_mode(self, mode):
        self.mode = mode

    def show_mode(self, mode):
        self.led = mode == "macos"
        self.dark = False

    def lights_off(self):
        self.dark = True

    def blink_error(self):
        self.blinking = True

    def load_usage(self):
        return self.usage

    def save_usage(self, data):
        self.usage = data
        self.usage_saves += 1

    def read_line(self):
        return self.lines.pop(0) if self.lines else None


def shipped_mappings_with(**settings):
    module = shipped_mappings()
    for name, value in settings.items():
        setattr(module, name, value)
    return module


def quiet():
    return contextlib.redirect_stdout(io.StringIO())


class AppTest(unittest.TestCase):
    def setUp(self):
        self.board = FakeBoard()
        with quiet():
            self.app = app.App(self.board, app.load_settings(shipped_mappings))

    def drive(self, buttons, ms):
        """Hold `buttons` for `ms` milliseconds, stepping every millisecond."""
        self.board.buttons = buttons
        with quiet():
            for _ in range(ms):
                self.board.time += 1
                self.app.step()

    def test_shows_the_saved_mode_at_start(self):
        self.assertTrue(self.board.led)

    def test_lights_go_dark_after_the_timeout_and_wake_on_a_press(self):
        self.drive(0, 4999)
        self.assertFalse(self.board.dark)
        self.drive(0, 1)
        self.assertTrue(self.board.dark)
        self.drive(M, 20)
        self.assertFalse(self.board.dark)
        self.assertTrue(self.board.led)

    def test_held_button_keeps_the_lights_on(self):
        self.drive(M, 8000)
        self.assertFalse(self.board.dark)
        self.drive(0, 4990)
        self.assertFalse(self.board.dark)
        self.drive(0, 20)
        self.assertTrue(self.board.dark)

    def test_mode_change_shows_the_new_mode_then_goes_dark(self):
        self.drive(ALL, 450)
        self.drive(0, 4990)
        self.assertEqual((self.board.led, self.board.dark), (False, False))
        self.drive(0, 20)
        self.assertTrue(self.board.dark)

    def test_zero_timeout_keeps_the_lights_on(self):
        board = FakeBoard()
        with quiet():
            self.app = app.App(board, app.load_settings(lambda: shipped_mappings_with(LED_TIMEOUT_MS=0)))
        self.board = board
        self.drive(0, 60000)
        self.assertFalse(board.dark)

    def test_tap_presses_and_releases(self):
        self.drive(M, 20)
        self.drive(0, 20)
        self.assertEqual(self.board.log, [("press", parse_keys("CMD+V")), ("release_all",)])

    def test_held_cycle_keeps_the_modifier_down_until_lifted(self):
        I_R = 2 | 8
        self.drive(I_R, 950)
        self.drive(0, 20)
        cmd_tab, cmd = parse_keys("CMD+TAB"), parse_keys("CMD")
        self.assertEqual(self.board.log, [("press", cmd_tab), ("press", cmd)] * 2 + [("release_all",)])

    def test_holding_all_five_switches_and_saves_the_mode(self):
        self.drive(ALL, 450)
        self.assertEqual(self.board.mode, "windows")
        self.assertFalse(self.board.led)

    def test_usb_error_on_press_skips_the_press_but_still_releases(self):
        self.board.fail_press = 1
        self.drive(M, 20)
        self.drive(0, 20)
        self.assertEqual(self.board.log, [("release_all",)])

    def test_failed_release_is_retried_until_it_works(self):
        self.board.fail_release = 3
        self.drive(M, 20)
        self.drive(0, 20)
        self.assertIsNone(self.app.pending)
        self.assertEqual(self.board.log, [("press", parse_keys("CMD+V")), ("release_all",)])

    def test_failed_tab_up_during_a_cycle_is_retried(self):
        cmd_tab, cmd = parse_keys("CMD+TAB"), parse_keys("CMD")
        fail_cmd_once = self.fail_when(cmd, times=1)
        self.drive(2 | 8, 420)
        self.assertEqual(self.board.log, [("press", cmd_tab), ("press", cmd)])
        self.assertIsNone(self.app.pending)
        self.assertEqual(fail_cmd_once["left"], 0)

    def test_a_stale_release_does_not_close_a_new_cycle(self):
        cmd_tab, cmd = parse_keys("CMD+TAB"), parse_keys("CMD")
        self.board.fail_release = 10 ** 6
        self.drive(M, 20)
        self.drive(0, 20)
        self.drive(2 | 8, 420)
        self.board.fail_release = 0
        self.drive(2 | 8, 20)
        self.assertEqual(self.board.log[-2:], [("press", cmd_tab), ("press", cmd)])

    def fail_when(self, keys, times):
        """Make press(keys) raise OSError `times` times."""
        state = {"left": times}
        press = self.board.press

        def flaky(pressed):
            if pressed == keys and state["left"]:
                state["left"] -= 1
                raise OSError("USB busy")
            press(pressed)
        self.board.press = flaky
        return state


def counting_mappings():
    m = shipped_mappings()
    m.COUNT_CHORDS = True
    return m


class UsageTest(unittest.TestCase):
    def start(self, mappings, board=None):
        self.board = board or FakeBoard()
        with quiet():
            self.app = app.App(self.board, app.load_settings(mappings))

    def drive(self, buttons, ms):
        self.board.buttons = buttons
        for _ in range(ms):
            self.board.time += 1
            self.app.step()

    def command(self, line):
        self.board.lines.append(line)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.app.step()
        return out.getvalue().splitlines()

    def test_off_by_default_counts_nothing_and_never_saves(self):
        self.start(shipped_mappings)
        with quiet():
            self.drive(M, 20)
            self.drive(0, app.USAGE_SAVE_MS + 10)
        self.assertEqual(self.command("usage"), ["usage counting off", "usage end"])
        self.assertEqual(self.board.usage_saves, 0)

    def test_counts_and_saves_a_minute_after_the_first_new_count(self):
        self.start(counting_mappings)
        self.drive(0, 5000)
        self.drive(M, 20)
        self.drive(0, app.USAGE_SAVE_MS - 30)
        self.assertEqual(self.board.usage_saves, 0)
        self.drive(0, 40)
        self.assertEqual(self.board.usage_saves, 1)
        self.drive(0, app.USAGE_SAVE_MS * 2)
        self.assertEqual(self.board.usage_saves, 1)
        self.assertEqual(Usage(self.board.usage).used(), [(M, 1, 0)])

    def test_reports_counts_including_unsaved_ones(self):
        self.start(counting_mappings)
        with quiet():
            self.drive(ALL, 450)
        self.drive(0, 20)
        self.drive(M, 20)
        self.drive(0, 20)
        self.assertEqual(
            self.command("usage"), ["usage counting on", "usage M 1 0", "usage T+I+M+R+P 0 1", "usage end"])

    def test_continues_from_saved_counts(self):
        saved = Usage()
        saved.record("tap", M)
        board = FakeBoard()
        board.usage = saved.to_bytes()
        self.start(counting_mappings, board)
        self.assertEqual(self.command("usage")[1], "usage M 1 0")

    def test_reset_clears_and_saves_right_away(self):
        self.start(counting_mappings)
        self.drive(M, 20)
        self.drive(0, 20)
        self.assertEqual(self.command("usage reset"), ["usage reset", "usage counting on", "usage end"])
        self.assertEqual(Usage(self.board.usage).used(), [])

    def test_unknown_command_gets_a_hint(self):
        self.start(shipped_mappings)
        self.assertIn("unknown command", self.command("hello")[0])


class LoadSettingsTest(unittest.TestCase):
    def test_reports_mapping_errors(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            settings = app.load_settings(lambda: types.SimpleNamespace(MACOS={"X": "V"}, WINDOWS={}))
        self.assertIsNone(settings)
        self.assertIn("please fix mappings.py", out.getvalue())

    def test_reports_other_errors_with_a_traceback(self):
        def broken():
            raise SyntaxError("invalid syntax")

        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertIsNone(app.load_settings(broken))
        self.assertIn("could not be loaded", out.getvalue())
        self.assertIn("SyntaxError", err.getvalue())


class RunTest(unittest.TestCase):
    def test_blinks_when_mappings_need_a_fix(self):
        board = FakeBoard()
        with quiet():
            app.run(board, lambda: types.SimpleNamespace(MACOS=None, WINDOWS=None))
        self.assertTrue(board.blinking)

    def test_runs_the_loop(self):
        board = FakeBoard()
        board.buttons = M
        with quiet():
            app.run(board, shipped_mappings, steps=3)
        self.assertFalse(board.blinking)


if __name__ == "__main__":
    unittest.main()
