# 0006: Mappings in a separate mappings.py

## Context

The user changes mappings by editing a file on the Pico's CIRCUITPY drive,
and CircuitPython reloads on save. Each mapping set, macOS and Windows, maps
chords to actions, including how an action behaves when held. Firmware updates
must not overwrite the user's mappings.

## Options considered

- `mappings.py`: comments and readable key names, can share entries between
  sets; a mistake can stop the firmware from starting.
- `mappings.json`: pure data that a future tool could generate; no comments,
  strict syntax and more repetition.
- Inside `code.py`: fewest files, but mappings mix with firmware logic and are
  overwritten by updates.

## Decision

We will keep the mappings in `mappings.py` on the CIRCUITPY drive, separate
from the firmware code. It defines one set for macOS and one for Windows. The
firmware checks the file at startup and reports problems by blinking the
onboard LED and printing the error on the serial console.

## Consequences

- Editing mappings needs only a text editor, and comments can explain each
  chord.
- Firmware updates replace the firmware files and leave `mappings.py` alone.
- Mappings are Python, so a mistake can stop startup until it is fixed. The
  LED and serial console make the cause visible.
- The CIRCUITPY drive has to be visible to edit mappings.
