"""Board layer for a wired Raspberry Pi Pico: buttons, LED, USB keyboard, serial console and nvm."""

import sys
import time

import board
import digitalio
import microcontroller
import supervisor
import usb_hid

from handful.config import BUTTONS
from handful.hid import Keyboard
from handful.usage import SIZE as USAGE_SIZE

# Each button connects its pin to GND.
PINS = {"T": board.GP2, "I": board.GP3, "M": board.GP4, "R": board.GP5, "P": board.GP6}
# Common-cathode RGB LED: each pin drives a colour leg; the common leg goes through one resistor to GND,
# so only one colour is lit at a time.
RGB_PINS = (board.GP28, board.GP27, board.GP26)  # red, green, blue
OFF = (False, False, False)
RED = (True, False, False)
MODE_COLOURS = {"macos": (False, True, False), "windows": (False, False, True)}
ERROR_BLINK_S = 0.1

# nvm layout: byte 0 is the mode, then a marker and the chord usage counts.
_MODE_BYTES = {"macos": ord("M"), "windows": ord("W")}
_USAGE_MARK = b"HU\x01"
_USAGE_START = 1
_USAGE_END = _USAGE_START + len(_USAGE_MARK) + USAGE_SIZE
MAX_LINE = 64


class Pico:
    DEBOUNCE_MS = 5

    def __init__(self):
        self._buttons = []
        for letter in BUTTONS:
            button = digitalio.DigitalInOut(PINS[letter])
            button.switch_to_input(pull=digitalio.Pull.UP)
            self._buttons.append(button)
        self._led = self._output(board.LED)
        self._rgb = [self._output(pin) for pin in RGB_PINS]
        self._keyboard = None
        self._line = ""

    @staticmethod
    def _output(pin):
        led = digitalio.DigitalInOut(pin)
        led.switch_to_output(value=False)
        return led

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

    def load_usage(self):
        """The saved usage counts, or None when nvm holds none."""
        data = bytes(microcontroller.nvm[_USAGE_START:_USAGE_END])
        if data[:len(_USAGE_MARK)] != _USAGE_MARK:
            return None
        return data[len(_USAGE_MARK):]

    def save_usage(self, data):
        # One slice write, so the flash is erased once per save.
        microcontroller.nvm[_USAGE_START:_USAGE_END] = _USAGE_MARK + data

    def read_line(self):
        """A line typed on the serial console, or None. Never waits."""
        while supervisor.runtime.serial_bytes_available:
            char = sys.stdin.read(1)
            if char in "\r\n":
                line, self._line = self._line.strip(), ""
                if line:
                    return line
            elif len(self._line) < MAX_LINE:
                self._line += char
        return None

    def show_mode(self, mode):
        """Onboard LED on for macOS and off for Windows; RGB LED green for macOS and blue for Windows."""
        self._light(mode == "macos", MODE_COLOURS[mode])

    def blink_error(self):
        """Blink the onboard LED and the RGB LED in red, fast, forever.

        CircuitPython restarts when a file on the drive is saved.
        """
        on = False
        while True:
            on = not on
            self._light(on, RED if on else OFF)
            time.sleep(ERROR_BLINK_S)

    def _light(self, onboard, colour):
        self._led.value = onboard
        # Off before on, so two colours never share the one resistor, even briefly.
        for lit in (False, True):
            for led, value in zip(self._rgb, colour):
                if value == lit:
                    led.value = value
