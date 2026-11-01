"""Chord usage counts: how often each chord fired as a tap and as a hold.

Only totals are kept, with no order and no times, so typed text can't be
rebuilt from them.
"""

from handful.chords import HOLD, TAP

CHORDS = 31
KINDS = (TAP, HOLD)
_WIDTH = 4
_MAX = (1 << (8 * _WIDTH)) - 1
SIZE = CHORDS * len(KINDS) * _WIDTH


class Usage:
    def __init__(self, data=None):
        self.counts = [0] * (CHORDS * len(KINDS))
        self.changed = False
        if data is not None and len(data) == SIZE:
            for i in range(len(self.counts)):
                self.counts[i] = int.from_bytes(bytes(data[i * _WIDTH:(i + 1) * _WIDTH]), "little")

    def _index(self, kind, chord):
        return (chord - 1) * len(KINDS) + KINDS.index(kind)

    def record(self, kind, chord):
        """Count one tap or hold of a chord bitmask (1 to 31)."""
        i = self._index(kind, chord)
        if self.counts[i] < _MAX:
            self.counts[i] += 1
            self.changed = True

    def count(self, kind, chord):
        return self.counts[self._index(kind, chord)]

    def reset(self):
        self.counts = [0] * len(self.counts)
        self.changed = True

    def to_bytes(self):
        out = bytearray()
        for value in self.counts:
            out += value.to_bytes(_WIDTH, "little")
        return bytes(out)

    def used(self):
        """(chord, taps, holds) for every chord fired at least once."""
        rows = []
        for chord in range(1, CHORDS + 1):
            taps, holds = self.count(TAP, chord), self.count(HOLD, chord)
            if taps or holds:
                rows.append((chord, taps, holds))
        return rows
