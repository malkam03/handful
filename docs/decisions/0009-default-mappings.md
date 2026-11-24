# 0009: Default mappings, hold behaviour and cancel

## Context

handful needs a default layout for its macOS and Windows sets. Office
telemetry shows Paste is the most-used command, more than twice the next, with
Save, Copy and Undo following
([Jensen Harris](https://jensenharris.com/blog/no-distaste-for-paste-why-the-ui-part-7)).
Seibel's five-finger chord study (1962) found chords using the thumb, index and
middle fingers easiest, and an isolated ring finger or ring plus pinky
hardest. The user's most-used actions are push-to-talk (a toggle), enter,
paste, copy, backspace and screenshots. Chords fire on release
([0005](0005-chords-fire-on-release.md)), so a chord isn't sent until every
finger lifts.

## Options considered

- Ordering purely by frequency: puts Paste on the ring finger, which is hard.
- Moving chords so a missed finger can never produce Enter: safer, but loses
  the mnemonics. Fire-on-release makes a missed finger visible before lifting,
  and a cancel gesture covers it.
- Mnemonic layout weighted by frequency and finger effort (chosen).

## Decision

We will ship this layout. T is thumb, I index, M middle, R ring, P pinky.

| Chord | Action | macOS | Windows | Held |
| --- | --- | --- | --- | --- |
| T | Push-to-talk toggle | Option+Space | Ctrl+Space | once |
| I | Enter | Return | Enter | once |
| M | Paste | Cmd+V | Ctrl+V | once |
| R | Copy | Cmd+C | Ctrl+C | once |
| P | Backspace | Backspace | Backspace | repeat |
| T+I | New line, not sent | Shift+Return | Shift+Enter | once |
| T+M | Paste as plain text | Cmd+Option+Shift+V | Ctrl+Shift+V | once |
| T+R | Cut | Cmd+X | Ctrl+X | once |
| T+P | Delete word | Option+Backspace | Ctrl+Backspace | repeat |
| M+R | Undo | Cmd+Z | Ctrl+Z | once |
| T+M+R | Redo | Cmd+Shift+Z | Ctrl+Y | once |
| T+I+M | Search | Cmd+Space | Win+S | once |
| I+R | Window overview | Ctrl+Up (Mission Control) | Win+Tab (Task View) | once |
| R+P | Escape | Esc | Esc | once |
| I+M | Region screenshot | Cmd+Shift+4 | Win+Shift+S | once |
| I+M+R | Full screenshot | Cmd+Shift+3 | Win+PrtScn | once |
| I+M+R+P | Select all | Cmd+A | Ctrl+A | once |
| T+I+M+R+P | Toggle macOS / Windows | — | — | toggle |

The mnemonics: the most-used actions are single presses on the easiest
fingers; the thumb plus a finger is a variant of that finger's action; more
fingers means more (bigger screenshot, select all, whole device); rare actions
take the hardest pair.

When held, most actions fire once. Backspace and delete word repeat. No
default chord cycles; the `"cycle"` behaviour is there for mappings that need
it ([0025](0025-cycling-hold-search-and-mission-control.md)). Undo and redo never
repeat. The mode toggle fires only when all five are held; tapping
all five does nothing. Chords with no mapping do nothing, so adding the
remaining fingers before lifting cancels a chord, as long as this happens
before the hold threshold. Once a hold has fired, it can't be cancelled.

## Consequences

- Paste, the most-used command, is on the easiest single finger.
- A missed thumb on T+I sends Enter, and a missed middle on I+M sends Enter;
  the user can cancel by squeezing all five before lifting, within the hold
  threshold.
- The mode can't change by accident on a quick all-finger tap.
- Paste as plain text and Windows redo vary by app; `mappings.py` can change
  them.
- Several easy chords are free for new actions.
