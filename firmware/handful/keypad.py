"""Turns chord events into key presses for the active mode."""

from handful.chords import HOLD, RELEASE, REPEAT, TAP, ChordDetector
from handful.config import MODES
from handful.ticks import ticks_add, ticks_diff

# Press the keys, then let them all go.
SEND = "send"
# Press the keys and leave them down until the next PRESS or RELEASE.
PRESS = "press"
# RELEASE, from chords, lets every key go.
SET_MODE = "set_mode"


class Keypad:
    def __init__(self, config, mode, usage=None):
        """`usage`, when given, counts every tap and hold, mapped or not."""
        self.config = config
        self.usage = usage
        self.mode = mode if mode in MODES else MODES[0]
        self.detector = ChordDetector(
            config.hold_ms, config.repeat_delay_ms, config.repeat_interval_ms
        )
        self._cycling = None
        self._next_cycle = 0

    def update(self, pressed, now):
        """Feed the debounced button bitmask; returns a list of (SEND, keys), (PRESS, keys),
        (RELEASE, None) or (SET_MODE, mode)."""
        out = []
        for event, chord in self.detector.update(pressed, now):
            if self.usage is not None and event in (TAP, HOLD):
                self.usage.record(event, chord)
            if event == RELEASE:
                if self._cycling is not None:
                    self._cycling = None
                    out.append((RELEASE, None))
                continue
            if chord == self.config.mode_chord:
                if event == HOLD:
                    self.mode = MODES[(MODES.index(self.mode) + 1) % len(MODES)]
                    out.append((SET_MODE, self.mode))
                continue
            action = self.config.sets[self.mode].get(chord)
            if action is None:
                continue
            if event == HOLD and action.held == "cycle":
                # The modifiers stay down so the computer's switcher stays open until the fingers lift.
                self._cycling = action
                self._next_cycle = ticks_add(now, self.config.cycle_interval_ms)
                out.extend(self._cycle_step(action))
            elif event in (TAP, HOLD) or (event == REPEAT and action.repeat):
                out.append((SEND, action.keys))
        if self._cycling is not None and ticks_diff(now, self._next_cycle) >= 0:
            self._next_cycle = ticks_add(now, self.config.cycle_interval_ms)
            out.extend(self._cycle_step(self._cycling))
        return out

    @staticmethod
    def _cycle_step(action):
        return [(PRESS, action.keys), (PRESS, action.modifiers)]
