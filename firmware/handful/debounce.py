"""Per-button debouncing on a bitmask of raw button states."""

from handful.ticks import ticks_diff


class Debouncer:
    """A button's state changes only after its raw reading has held for `ms`."""

    def __init__(self, count, ms):
        self._count = count
        self._ms = ms
        self.state = 0
        self._raw = 0
        self._since = [0] * count

    def update(self, raw, now):
        changed = raw ^ self._raw
        for i in range(self._count):
            if changed & (1 << i):
                self._since[i] = now
        self._raw = raw
        for i in range(self._count):
            bit = 1 << i
            if (raw ^ self.state) & bit and ticks_diff(now, self._since[i]) >= self._ms:
                self.state ^= bit
        return self.state
