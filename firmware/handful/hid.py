"""USB boot keyboard reports, sent through CircuitPython's built-in usb_hid devices.

A report is 8 bytes: a modifier bitmask (usage codes 0xE0-0xE7), a reserved
byte, then up to six other usage codes.
"""

KEYBOARD_USAGE_PAGE = 0x01
KEYBOARD_USAGE = 0x06
MODIFIER_FIRST = 0xE0
MODIFIER_LAST = 0xE7
MAX_KEYS = 6


def report(keys):
    """Build the 8-byte report for the given usage codes held together."""
    data = bytearray(8)
    slot = 2
    for code in keys:
        if MODIFIER_FIRST <= code <= MODIFIER_LAST:
            data[0] |= 1 << (code - MODIFIER_FIRST)
        elif slot < 2 + MAX_KEYS:
            data[slot] = code
            slot += 1
        else:
            raise ValueError("a keyboard report holds at most {} keys".format(MAX_KEYS))
    return data


class Keyboard:
    def __init__(self, devices):
        for device in devices:
            if device.usage_page == KEYBOARD_USAGE_PAGE and device.usage == KEYBOARD_USAGE:
                self._device = device
                return
        raise ValueError("no USB keyboard device is enabled")

    def press(self, *keys):
        self._device.send_report(report(keys))

    def release_all(self):
        self._device.send_report(bytes(8))
