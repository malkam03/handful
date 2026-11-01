# 0012: Wired USB, with portable firmware

## Context

handful sits on the desk next to the computer, and the Pico has native USB
but no radio. A wireless keypad needs a different board (such as a Pico W or
an ESP32-S3), a battery, charging and power management, all of which add
size and weight to the shell. Wireless is still appealing for later.

## Options considered

- Wired USB only, with no thought for wireless.
- Wired USB now, with the firmware split so that a wireless board can be
  added later.
- Wireless now, on a Pico W or an ESP32-S3.

## Decision

We will connect handful over a USB cable. The firmware keeps the chord engine
and the mappings apart from a small board layer that owns the pins, the LED
and the HID sender, so that a wireless board only needs a new board layer.

## Consequences

- No battery or charging circuit; the Pico is powered over USB.
- The shell needs a cable exit (see [0011](0011-grip-shell.md)).
- The chord engine is plain Python with no hardware imports, so it can be
  tested on the computer.
- Adding wireless later means a new board layer and a new decision.
