"""Turns chord events into key presses for the active mode."""

from handful.chords import HOLD, REPEAT, TAP, ChordDetector
from handful.config import MODES

SEND = "send"
SET_MODE = "set_mode"


class Keypad:
    def __init__(self, config, mode):
        self.config = config
        self.mode = mode if mode in MODES else MODES[0]
        self.detector = ChordDetector(
            config.hold_ms, config.repeat_delay_ms, config.repeat_interval_ms
        )

    def update(self, pressed, now):
        """Feed the debounced button bitmask; returns a list of (SEND, keys) or (SET_MODE, mode)."""
        out = []
        for event, chord in self.detector.update(pressed, now):
            if chord == self.config.mode_chord:
                if event == HOLD:
                    self.mode = MODES[(MODES.index(self.mode) + 1) % len(MODES)]
                    out.append((SET_MODE, self.mode))
                continue
            action = self.config.sets[self.mode].get(chord)
            if action is None:
                continue
            if event in (TAP, HOLD) or (event == REPEAT and action.repeat):
                out.append((SEND, action.keys))
        return out
