# 0025: LEDs go dark when idle

## Context

The onboard LED and the RGB indicator LED (see
[0018](0018-rgb-indicator-led.md)) show the mode. The RGB LED sits just
ahead of the thumb tip, in view, so a light that stays on all day is a
distraction. The mode matters when typing a chord, not while the hand rests.

## Options considered

- Always on: the mode is visible at a glance, but the light never rests.
- Dark after a fixed idle time, lit again at the next press: calm when idle,
  and the mode shows the moment a button goes down.
- Lit only while a button is held: darkest, but a tap is too short to read
  the colour.

## Decision

We will turn both LEDs off `LED_TIMEOUT_MS` after the last button is
released, 5000 ms by default, and light them again with the mode colour at
the next press. A held button keeps them lit, and a mode change shows the new
colour for the same time. `LED_TIMEOUT_MS = 0` in `mappings.py` keeps them on.
The error blink for a broken `mappings.py` keeps going forever.

## Consequences

- The LEDs rest when the keypad does, and draw no current while dark.
- Dark looks the same as unplugged; a press shows the keypad is alive.
- The first press after a rest still sends its chord as normal; the light is
  only a display.
- The board layer gains a `lights_off()` call; the timing lives in the
  tested main loop.
