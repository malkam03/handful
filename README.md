# handful

Your whole workflow, in a handful of keys.

These days I do a lot of my work by voice: tap a shortcut, speak, tap it
again. The rest is a few familiar moves, like copy, paste, undo a word or grab
a screenshot. handful puts those moves under one hand, so I can lean back with
the other on the mouse. Each button sends a key on its own, and pressing
several together (a chord) sends more: 4 buttons give 15 actions, 5 give 31.
It shows up as a normal USB keyboard, so the computer needs no drivers.

## What it is

- A small one-handed keypad with five buttons, one per finger and one for the
  thumb.
- A chording keyboard: any combination of buttons pressed together is its own
  action.
- Built for a voice-first workflow: push-to-talk, enter, copy, paste,
  backspace and screenshots are the moves that matter most.
- Runs on a Raspberry Pi Pico, which acts as a standard USB keyboard.
- Buttons and mappings are configurable.

## Status

The project is in its requirements step. There is no firmware yet. The current
design is in [`docs/architecture.md`](docs/architecture.md), and each accepted
decision is in [`docs/decisions/`](docs/decisions/).

## Inspiration

handful borrows ideas, not code, from
[ARTSEY](https://artsey.io/), GKOS, the Twiddler,
[tobychui/4xMacropad](https://github.com/tobychui/4xMacropad) and the combo
features of [QMK](https://qmk.fm/) and [KMK](https://github.com/KMKfw/kmk_firmware).

## Licence

[MIT](LICENSE)
