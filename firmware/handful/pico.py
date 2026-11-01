"""Board layer for a wired Raspberry Pi Pico: buttons, LED, USB keyboard and saved mode."""

import time

import board
import digitalio
import microcontroller
import supervisor
import usb_hid

from handful.config import BUTTONS
from handful.hid import Keyboard

# Each button connects its pin to GND.
PINS = {"T": board.GP2, "I": board.GP3, "M": board.GP4, "R": board.GP5, "P": board.GP6}
ERROR_BLINK_S = 0.1

_MODE_BYTES = {"macos": ord("M"), "windows": ord("W")}


class Pico:
    DEBOUNCE_MS = 5

    def __init__(self):
        self._buttons = []
        for letter in BUTTONS:
            button = digitalio.DigitalInOut(PINS[letter])
            button.switch_to_input(pull=digitalio.Pull.UP)
            self._buttons.append(button)
        self._led = digitalio.DigitalInOut(board.LED)
        self._led.switch_to_output(value=False)
        self._keyboard = None

    def now(self):
        return supervisor.ticks_ms()

    def read(self):
        """Raw button bitmask in config.BUTTONS order; 1 means pressed."""
        mask = 0
        for i, button in enumerate(self._buttons):
            if not button.value:
                mask |= 1 << i
        return mask

    def _hid(self):
        if self._keyboard is None:
            self._keyboard = Keyboard(usb_hid.devices)
        return self._keyboard

    def press(self, keys):
        self._hid().press(*keys)

    def release_all(self):
        self._hid().release_all()

    def load_mode(self):
        byte = microcontroller.nvm[0]
        for mode, value in _MODE_BYTES.items():
            if byte == value:
                return mode
        return "macos"

    def save_mode(self, mode):
        microcontroller.nvm[0] = _MODE_BYTES[mode]

    def show_mode(self, mode):
        """LED on for macOS, off for Windows."""
        self._led.value = mode == "macos"

    def blink_error(self):
        """Blink fast forever. CircuitPython restarts when a file on the drive is saved."""
        while True:
            self._led.value = not self._led.value
            time.sleep(ERROR_BLINK_S)
