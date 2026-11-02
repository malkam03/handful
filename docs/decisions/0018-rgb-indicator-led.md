# 0018: RGB indicator LED on GP26–GP28

## Context

The Pico's onboard LED shows the mode and blinks when `mappings.py` has a
problem (see [0004](0004-macos-and-windows-modes.md) and
[0006](0006-mappings-py.md)). Inside the 3D-printed grip shell (see
[0011](0011-grip-shell.md)) the onboard LED is hidden. Its pin, GP25, is
wired only to that LED and isn't on the Pico's edge pins, so an LED on the
shell needs GPIOs of its own. A GPIO pin drives 4 mA by default at 3.3 V.

## Options considered

- A single-colour LED on one GPIO, copying the onboard LED: one pin, but
  Windows mode is "off", which looks the same as unplugged.
- A plain 4-leg common-cathode RGB LED on three GPIOs: a colour per state,
  always lit while powered, and room for more colours later.
- A WS2812B addressable LED: any colour from one pin, but it needs 5 V or
  level care and a timing-critical protocol.

## Decision

We will fit a common-cathode RGB LED on the shell. It shows green in macOS
mode, blue in Windows mode, and blinks red, together with the onboard LED,
when `mappings.py` has a problem. The onboard LED keeps working: on for
macOS, off for Windows. The wiring is:

| From | Part | To |
| --- | --- | --- |
| GP26 (physical pin 31) | | blue leg |
| GP27 (physical pin 32) | | green leg |
| GP28 (physical pin 34) | | red leg |
| common leg (the longest) | 330 Ω resistor | GND (physical pin 38) |

Physical pin 33 between them is the analog ground; the common leg uses pin
38. The firmware lights one colour at a time, so the single resistor sets
each colour's current: about 4 mA for red (about 2 V) and about 1 mA for
green and blue (about 3 V), all within the default drive. The pins are fixed
in the board layer, like the button pins.

## Consequences

- The mode is visible from outside the shell, and every state has its own
  colour.
- The LED takes three GPIOs, one resistor and no other parts.
- Mixed colours such as yellow or white would need a resistor per colour
  leg: with one shared resistor, red takes most of the current.
- New states, such as a chord-preview colour, need only a firmware change.
- The firmware drives the pins whether or not the LED is fitted, so a Pico
  without it works the same.
