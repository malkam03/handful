# 0025: Cycling hold, search and Mission Control

Replaces: ADR-0019 (removed; see git history)

## Context

The user moves between Spaces and full-screen apps many times a day, more
often than they switch apps with Cmd+Tab. They also open system search often.

On macOS, Ctrl+Right and Ctrl+Left move one Space at a time, and Ctrl+Up
opens Mission Control, which shows every open window and Space
([Apple](https://support.apple.com/guide/mac-help/mh35798/mac),
[Apple](https://support.apple.com/guide/mac-help/mh14112/mac)). Spaces don't
wrap around and macOS has no "previous Space" key, so moving both ways
needs two chords. On Windows, Win+Tab opens Task View, which shows open
windows and virtual desktops. Spotlight is Cmd+Space on macOS, and Win+S
opens search on Windows.

Every action is pressed and then fully released
([0009](0009-default-mappings.md)), and a held chord is frozen
([0005](0005-chords-fire-on-release.md)). An app switcher such as Cmd+Tab only
walks through apps if its modifier stays down while the key repeats.

## Options considered

- Two chords for left and right Spaces, with the thumb reversing direction:
  no firmware work, but it takes two chords.
- One chord that goes right on a tap and left on a hold: a single chord, but
  needs a new held behaviour and going left waits for the hold threshold.
- One chord that alternates direction on every tap: good for two Spaces,
  confusing with more.
- Mission Control on one chord: a single chord with no firmware work, and it
  reaches any Space or window. Picking one usually takes the pointer.

## Decision

We will put Mission Control on I+R, the easy pair that switch app used.
Switch app leaves the default layout.

| Chord | Action | macOS | Windows | Held |
| --- | --- | --- | --- | --- |
| I+R | Mission Control | Ctrl+Up | Win+Tab | once |
| T+I+M | Search | Cmd+Space | Win+S | once |

The firmware keeps the `"cycle"` held behaviour, written as
`("CMD+TAB", "cycle")`, for anyone who maps an app switcher. A tap sends the
keys once. At the hold threshold the firmware presses the keys and lets go
of all but the modifiers, so the computer's switcher opens on the previous
app. Every `CYCLE_INTERVAL_MS` (500 ms by default) it presses the key again
with the modifiers still down. Lifting the fingers lets every key go, which
picks the highlighted item. A cycle action needs at least one modifier and
one other key.

## Consequences

- A quick I+R shows every window and Space; another I+R or a click leaves
  it.
- Switch app, and moving one Space left or right, are one line each in
  `mappings.py`: `("CMD+TAB", "cycle")`, `"CTRL+LEFT"` and `"CTRL+RIGHT"`.
- No default chord cycles, so the cheat sheet and banner show the » mark
  and its legend only when a mapping uses `"cycle"`.
- While a cycle is held, its modifiers stay down on the computer until the
  fingers lift, and overshooting means lifting and cycling again.
