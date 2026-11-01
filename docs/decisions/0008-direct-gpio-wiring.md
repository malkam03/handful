# 0008: Direct wiring to GPIO with internal pull-ups

## Context

handful has five buttons. The Pico has 26 GPIO pins with built-in pull-up
resistors. The user wires the hardware and needs exact pins. Mechanical
contacts bounce for a few milliseconds when pressed or released.

## Options considered

- One GPIO per button, internal pull-ups, active low: no extra parts, simplest
  wiring and firmware.
- A key matrix with diodes: saves pins, which only matters with many more
  buttons.
- External pull-up resistors: more parts with no benefit at this size.

## Decision

We will wire each button between its own GPIO pin and GND, with the Pico's
internal pull-ups enabled, so a pressed button reads low. The pins are:

| Finger | GPIO | Physical pin |
| --- | --- | --- |
| Thumb | GP2 | 4 |
| Index | GP3 | 5 |
| Middle | GP4 | 6 |
| Ring | GP5 | 7 |
| Pinky | GP6 | 9 |

Any GND pin can be the common ground; pins 3 and 8 are next to the buttons.
The prototype's 12 × 12 mm tactile buttons have four legs joined in two pairs
inside. Each button is wired through two legs that a multimeter's continuity
mode shows as connected only while the button is pressed.
The firmware debounces each button for 5 ms.

## Consequences

- No resistors or diodes are needed.
- The five button pins sit together on one edge of the Pico.
- A sixth button would need one more GPIO and a firmware change.
- The debounce time adds up to 5 ms of latency, small next to the chord
  release.
