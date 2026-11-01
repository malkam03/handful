# 0005: Chords fire on release, with a hold threshold

## Context

Fingers never land on a chord at exactly the same moment, so the firmware has
to decide which buttons belong together and when to send. handful's actions are
discrete commands (enter, copy, paste, screenshot), so a wrong action costs
more than a few tens of milliseconds. Some actions, such as backspace, are also
useful when held. No direct study compares the strategies for small chord
pads. The best-studied one-handed chorder, the Twiddler, and stenography
machines both fire on release. QMK and KMK combos use a timeout because they
share keys with fast normal typing, which handful doesn't have.

## Options considered

- Fire on release: the chord is every button pressed until all are released;
  tolerant of any stagger, fires when the fingers lift, needs a separate rule
  for holds.
- Fire after a fixed window from the first press: fires sooner and holds come
  naturally, but a finger landing late splits the chord.
- Hybrid, window or first release: faster than release, still splits chords
  with a slow finger, needs tuning.

## Decision

We will treat every button pressed between the first press and the moment all
buttons are released as one chord, and send it on that release. If the chord
is still held after a hold threshold (400 ms by default, configurable), it
counts as a hold instead and fires at that point, with no second action on
release.

## Consequences

- Staggered fingers never split a chord, which suits 3–5 finger chords.
- A tap fires when the fingers lift, typically 100–200 ms after the press.
- Holds have a defined trigger. What each action does when held is set in the
  mappings.
- The hold threshold may need tuning after real use.
