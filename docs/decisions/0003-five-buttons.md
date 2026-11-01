# 0003: Five buttons, one per finger and thumb

## Context

handful needs roughly 10–12 actions: push-to-talk, enter, copy, paste, cut,
backspace, delete word, undo, select all, escape and screenshots. Four buttons
give 15 combinations and five give 31, so both cover the list. The user wants
the keypad to rest the hand the way a Logitech Ergo-style mouse does, with the
thumb in use.

## Options considered

- Four buttons, fingers only: 15 actions, simplest build, thumb idle.
- Five buttons, fingers and thumb: 31 actions, a natural resting shape, and the
  thumb is free for a frequent single press.
- Firmware for five, four wired: avoids a rewrite but leaves the shape
  unsettled.

## Decision

We will build handful with five buttons: one for each finger and one for the
thumb. The firmware and mappings handle all 31 combinations, and mappings only
need to fill the ones in use.

## Consequences

- The most frequent actions can have single presses, with chords for the rest.
- Many combinations stay unused, which leaves room for new actions.
- The Pico needs five GPIO inputs.
- The enclosure has to place the thumb button comfortably, which shapes its
  design.
