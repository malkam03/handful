# 0002: CircuitPython firmware

## Context

The firmware reads 4–5 buttons, detects chords and sends key presses over USB
HID. Dependencies must be permissively licensed. The user wires the hardware
and wants to change mappings easily. Chords fire on release (see
[0005](0005-chords-fire-on-release.md)), and a press-and-release takes far
longer than the latency of any of the stacks below.

## Options considered

- CircuitPython (MIT) with `adafruit_hid` (MIT): the Pico appears as a USB
  drive and code or mappings reload on save; mature HID support; a few ms of
  extra latency and a 1–2 s boot.
- Pico SDK with TinyUSB (BSD-3, MIT): about 1 ms latency and a fast boot, but
  every change needs a rebuild and reflash with a CMake and arm-gcc toolchain.
- Rust with embassy or rp-hal (MIT, Apache-2.0): same speed as C, safer, but
  rebuild to change anything and the hardest for the user to tweak.
- MicroPython (MIT): similar to CircuitPython, with less mature USB keyboard
  support.

## Decision

We will write handful's firmware in CircuitPython, using its built-in
`usb_hid` module and the `adafruit_hid` library to send key presses. The chord
logic is handful's own code.

## Consequences

- No toolchain to install: editing a file on the Pico's drive is enough.
- Latency is a few ms above C or Rust, which is below what a person notices
  next to the time it takes to press and release a chord.
- The Pico shows up as a USB drive unless `boot.py` hides it.
- An always-running interpreter uses more power, which matters if handful
  later runs on a battery.
