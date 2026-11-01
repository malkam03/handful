"""Millisecond tick arithmetic that survives the 2**29 wrap of supervisor.ticks_ms()."""

_PERIOD = 1 << 29
_HALF = _PERIOD // 2


def ticks_add(ticks, delta):
    return (ticks + delta) % _PERIOD


def ticks_diff(later, earlier):
    return ((later - earlier + _HALF) % _PERIOD) - _HALF
