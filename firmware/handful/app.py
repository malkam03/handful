"""The keypad main loop. Plain Python: the board is passed in, so tests can use a fake one.

A board provides: DEBOUNCE_MS, now(), read(), press(keys), release_all(),
load_mode(), save_mode(mode), show_mode(mode), blink_error(), load_usage(),
save_usage(data) and read_line(). press() and release_all() raise OSError when
USB isn't ready. read_line() returns a line typed on the serial console, or None.

Typing "usage" on the serial console prints the chord counts; "usage reset"
clears them. tools/usage.py does both from the computer.
"""

import time
import traceback

from handful import config
from handful.debounce import Debouncer
from handful.keypad import SEND, Keypad
from handful.ticks import ticks_diff
from handful.usage import Usage

POLL_S = 0.001
# Counts are saved at most this often, to spare the flash.
USAGE_SAVE_MS = 60000


def load_settings(load_mappings):
    """Return the Config from mappings.py, or None after printing what needs fixing."""
    try:
        return config.load(load_mappings())
    except config.MappingError as error:
        print("handful: please fix mappings.py:")
        print(error)
    except Exception as error:
        print("handful: mappings.py could not be loaded:")
        traceback.print_exception(type(error), error, error.__traceback__)
    return None


class App:
    def __init__(self, board, settings):
        self.board = board
        self.counting = settings.count_chords
        self.usage = Usage(board.load_usage())
        self.saved_at = board.now()
        self.keypad = Keypad(settings, board.load_mode(), self.usage if self.counting else None)
        self.debouncer = Debouncer(len(config.BUTTONS), board.DEBOUNCE_MS)
        self.release_pending = False
        board.show_mode(self.keypad.mode)
        print("handful ready, mode:", self.keypad.mode)
        if self.counting:
            print("handful: counting chords (COUNT_CHORDS in mappings.py)")

    def step(self):
        """Read the buttons once and act on any chord events."""
        if self.release_pending:
            self._release()
        line = self.board.read_line()
        if line is not None:
            self._command(line)
        now = self.board.now()
        pressed = self.debouncer.update(self.board.read(), now)
        for kind, value in self.keypad.update(pressed, now):
            if kind == SEND:
                self._send(value)
            else:
                self.board.save_mode(value)
                self.board.show_mode(value)
                print("handful mode:", value)
        # Saves a minute after the first new count, and keeps the timer clear of the tick wrap.
        if not self.usage.changed:
            self.saved_at = now
        elif ticks_diff(now, self.saved_at) >= USAGE_SAVE_MS:
            self._save_usage(now)

    def _save_usage(self, now):
        self.board.save_usage(self.usage.to_bytes())
        self.usage.changed = False
        self.saved_at = now

    def _command(self, line):
        words = line.split()
        if words == ["usage", "reset"]:
            self.usage.reset()
            self._save_usage(self.board.now())
            print("usage reset")
        elif words != ["usage"]:
            print("handful: unknown command {!r}; try \"usage\" or \"usage reset\"".format(line))
            return
        print("usage counting", "on" if self.counting else "off")
        for chord, taps, holds in self.usage.used():
            print("usage", config.chord_name(chord), taps, holds)
        print("usage end")

    def _send(self, keys):
        # If USB isn't ready, skip this press but keep the keypad running.
        try:
            self.board.press(keys)
        except OSError as error:
            print("handful: USB not ready:", error)
        self._release()

    def _release(self):
        # A failed release is retried on every step, so no key stays down on the computer.
        try:
            self.board.release_all()
            self.release_pending = False
        except OSError:
            self.release_pending = True


def run(board, load_mappings, steps=None):
    """Run the keypad forever (or for `steps` steps). Blinks the LED when mappings.py needs a fix."""
    settings = load_settings(load_mappings)
    if settings is None:
        board.blink_error()
        return
    app = App(board, settings)
    while steps is None or steps > 0:
        app.step()
        time.sleep(POLL_S)
        if steps is not None:
            steps -= 1
