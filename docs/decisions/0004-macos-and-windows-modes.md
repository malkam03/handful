# 0004: macOS and Windows mapping sets, switched on the device

## Context

handful must work on macOS and on Windows. The same action needs different
shortcuts on each: copy is Cmd+C on macOS and Ctrl+C on Windows, delete word
is Option+Backspace against Ctrl+Backspace, and a region screenshot is
Cmd+Shift+4 against Win+Shift+S. A USB keyboard can't tell which operating
system or app it's typing into.

## Options considered

- One operating system only: simplest, but doesn't cover both.
- A mode chord on the device: no software on the computer; the user switches
  by hand.
- Neutral keys (F13–F24) translated per app by a computer-side tool such as
  Karabiner-Elements: switches automatically, but needs host software and
  moves the mappings off the device.

## Decision

We will keep two mapping sets in the firmware, one for macOS and one for
Windows. A dedicated chord toggles between them. The Pico's onboard LED shows
the active mode, and the mode is remembered when handful is unplugged.

## Consequences

- No software on the computer, and the mappings stay on the device.
- The user has to switch modes when moving between operating systems.
- One chord is reserved for the mode toggle.
- Each action is defined twice, once per operating system.
- Linux isn't supported yet. A third set could be added the same way.
