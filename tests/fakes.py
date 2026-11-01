"""Stand-ins for the CircuitPython modules pico.py imports, so it runs on the computer."""

import sys
import types


class Pin:
    def __init__(self, name):
        self.name = name


class DigitalInOut:
    instances = []

    def __init__(self, pin):
        self.pin = pin
        self.value = True
        self.pull = None
        DigitalInOut.instances.append(self)

    def switch_to_input(self, pull=None):
        self.pull = pull

    def switch_to_output(self, value=False):
        self.value = value


class HIDDevice:
    def __init__(self, usage_page, usage):
        self.usage_page = usage_page
        self.usage = usage
        self.reports = []

    def send_report(self, report):
        self.reports.append(bytes(report))


def install():
    """Put fake board, digitalio, microcontroller, supervisor and usb_hid modules in sys.modules."""
    board = types.ModuleType("board")
    for name in ("GP2", "GP3", "GP4", "GP5", "GP6", "LED"):
        setattr(board, name, Pin(name))
    digitalio = types.ModuleType("digitalio")
    digitalio.DigitalInOut = DigitalInOut
    digitalio.Pull = types.SimpleNamespace(UP="up")
    microcontroller = types.ModuleType("microcontroller")
    microcontroller.nvm = bytearray(8)
    supervisor = types.ModuleType("supervisor")
    supervisor.ticks_ms = lambda: 1234
    usb_hid = types.ModuleType("usb_hid")
    keyboard = HIDDevice(0x01, 0x06)
    usb_hid.devices = [HIDDevice(0x01, 0x02), keyboard]
    for module in (board, digitalio, microcontroller, supervisor, usb_hid):
        sys.modules[module.__name__] = module
    DigitalInOut.instances = []
    return types.SimpleNamespace(board=board, microcontroller=microcontroller, keyboard=keyboard)
