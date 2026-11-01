# 0013: CircuitPython firmware with built-in modules only

Replaces: ADR-0002 (removed; see git history)

## Context

The firmware reads five buttons, detects chords and sends key presses over USB
HID. Dependencies must be permissively licensed. The user wires the hardware
and wants to change mappings easily. Chords fire on release (see
[0005](0005-chords-fire-on-release.md)), and a press-and-release takes far
longer than the latency of any of the stacks below.

Every library downloaded at install time is code the keypad runs without
review, and a keyboard can type anything on the computer it's plugged into.
handful already has its own key name table (`keys.py`), and a USB boot
keyboard report is a fixed 8-byte format that is short to build.

## Options considered

- CircuitPython (MIT) with only its built-in `usb_hid` module: the Pico
  appears as a USB drive and code or mappings reload on save; nothing to
  download besides CircuitPython itself; handful builds its own HID reports.
- CircuitPython with the `adafruit_hid` library (MIT): the same, with a
  mature keyboard helper, but a download on every fresh install that has to
  be trusted or pinned.
- Pico SDK with TinyUSB (BSD-3, MIT): about 1 ms latency and a fast boot, but
  every change needs a rebuild and reflash with a CMake and arm-gcc toolchain.
- Rust with embassy or rp-hal (MIT, Apache-2.0): same speed as C, safer, but
  rebuild to change anything and the hardest for the user to tweak.
- MicroPython (MIT): similar to CircuitPython, with less mature USB keyboard
  support.

## Decision

We will write handful's firmware in CircuitPython and use only modules built
into CircuitPython. `handful/hid.py` builds the 8-byte keyboard reports and
sends them through the `usb_hid` keyboard device. The chord logic is
handful's own code.

## Consequences

- No toolchain to install: editing a file on the Pico's drive is enough.
- The only third-party code on the keypad is the CircuitPython firmware,
  flashed once from circuitpython.org. Deploying downloads nothing.
- handful maintains its own small HID report code, covered by host tests.
  Media keys or a mouse would need their own report code too.
- Latency is a few ms above C or Rust, which is below what a person notices
  next to the time it takes to press and release a chord.
- The Pico shows up as a USB drive unless `boot.py` hides it.
- An always-running interpreter uses more power, which matters if handful
  later runs on a battery.
