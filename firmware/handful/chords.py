"""Chord detection: a chord is every button pressed until all are released.

Fires a tap on release, or a hold once the chord has been down for the hold
threshold. After a hold, repeat ticks follow until every button is released.
"""

from handful.ticks import ticks_add, ticks_diff

TAP = "tap"
HOLD = "hold"
REPEAT = "repeat"


class ChordDetector:
    def __init__(self, hold_ms, repeat_delay_ms, repeat_interval_ms):
        self.hold_ms = hold_ms
        self.repeat_delay_ms = repeat_delay_ms
        self.repeat_interval_ms = repeat_interval_ms
        self.chord = 0
        self._start = 0
        self._held = False
        self._next_repeat = 0

    def update(self, pressed, now):
        """Feed the debounced button bitmask; returns a list of (event, chord)."""
        if not self.chord:
            if not pressed:
                return []
            self.chord = pressed
            self._start = now
            self._held = False
        elif not self._held:
            self.chord |= pressed

        if not pressed:
            chord, held = self.chord, self._held
            self.chord = 0
            self._held = False
            return [] if held else [(TAP, chord)]

        if not self._held:
            if ticks_diff(now, self._start) >= self.hold_ms:
                self._held = True
                self._next_repeat = ticks_add(now, self.repeat_delay_ms)
                return [(HOLD, self.chord)]
            return []

        if ticks_diff(now, self._next_repeat) >= 0:
            self._next_repeat = ticks_add(now, self.repeat_interval_ms)
            return [(REPEAT, self.chord)]
        return []
