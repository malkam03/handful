import contextlib
import io
import types
import unittest

import _path  # noqa: F401
from handful import app
from handful.keys import parse_keys
from test_config import shipped_mappings

M, ALL = 4, 31


class FakeBoard:
    DEBOUNCE_MS = 5

    def __init__(self, mode="macos"):
        self.time = 0
        self.buttons = 0
        self.mode = mode
        self.led = None
        self.log = []
        self.fail_press = 0
        self.fail_release = 0
        self.blinking = False

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

    def blink_error(self):
        self.blinking = True


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

    def test_tap_presses_and_releases(self):
        self.drive(M, 20)
        self.drive(0, 20)
        self.assertEqual(self.board.log, [("press", parse_keys("CMD+V")), ("release_all",)])

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
        self.assertFalse(self.app.release_pending)
        self.assertEqual(self.board.log, [("press", parse_keys("CMD+V")), ("release_all",)])


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
