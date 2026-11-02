# 0019: Cycling hold for app switching, and search

## Context

The user switches apps and opens system search many times a day. Switching
to the previous app is Cmd+Tab on macOS
([Apple](https://support.apple.com/en-us/102650)) and Alt+Tab on Windows,
where Microsoft says to "continue to hold the Alt key and press Tab multiple
times" to go further back
([Microsoft](https://support.microsoft.com/en-us/windows/keyboard-shortcuts-in-windows-dcc61a57-8ff0-cffe-9796-cb9706c75eec)).
Ctrl+Tab switches tabs inside an app. Spotlight is Cmd+Space on macOS; on
Windows, Win+S opens search. Every action is pressed and then fully released
([0009](0009-default-mappings.md)), so a repeating Cmd+Tab lets go of Cmd each
time and only flips between the same two apps. A held chord is frozen
([0005](0005-chords-fire-on-release.md)), so other fingers can't add Tabs.

## Options considered

- A general "cycle" held behaviour: any mapping with a modifier and a key can
  use it; adds one word and one timing to `mappings.py`.
- A built-in app-switch action: same feel, but only for Cmd/Alt+Tab.
- Keep the modifier down without stepping: the switcher stays open, but
  moving in it needs another input.

## Decision

We will add a third held behaviour, `"cycle"`, written as
`("CMD+TAB", "cycle")`. A tap sends the keys once. At the hold threshold the
firmware presses the keys and lets go of all but the modifiers, so the
computer's switcher opens on the previous app. Every `CYCLE_INTERVAL_MS`
(500 ms by default) it presses the key again with the modifiers still down.
Lifting the fingers lets every key go, which picks the highlighted app. A
cycle action needs at least one modifier and one other key.

The default layout gains two chords on free, easy spots:

| Chord | Action | macOS | Windows | Held |
| --- | --- | --- | --- | --- |
| I+R | Switch app | Cmd+Tab | Alt+Tab | cycle |
| T+I+M | Search | Cmd+Space | Win+S | once |

## Consequences

- A quick I+R returns to the previous app; holding it walks through the
  open apps, one every 500 ms, until the fingers lift.
- Backwards switching (Cmd/Alt+Shift+Tab) and Ctrl+Tab for tabs aren't
  mapped; each is one line in `mappings.py` with `"cycle"`.
- Overshooting means lifting and cycling again, as there is no step back.
- While a cycle is held, its modifiers stay down on the computer until the
  fingers lift.
- The cheat sheet and banner fit six chords per group, and mark cycling
  actions with ».
