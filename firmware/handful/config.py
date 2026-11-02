"""Read and check the settings and mapping sets in mappings.py."""

from handful.keys import parse_keys

# Thumb, index, middle, ring, pinky: bit 0 to bit 4 of every chord bitmask.
BUTTONS = "TIMRP"
MODES = ("macos", "windows")
HELD_BEHAVIOURS = ("once", "repeat", "cycle")
MODIFIER_CODES = range(0xE0, 0xE8)


class MappingError(Exception):
    pass


class Action:
    def __init__(self, keys, held="once"):
        self.keys = keys
        self.held = held
        self.repeat = held == "repeat"
        self.modifiers = tuple(k for k in keys if k in MODIFIER_CODES)


class Config:
    def __init__(self, hold_ms, repeat_delay_ms, repeat_interval_ms, mode_chord, sets, count_chords=False,
                 cycle_interval_ms=500):
        self.hold_ms = hold_ms
        self.repeat_delay_ms = repeat_delay_ms
        self.repeat_interval_ms = repeat_interval_ms
        self.cycle_interval_ms = cycle_interval_ms
        self.mode_chord = mode_chord
        self.sets = sets
        self.count_chords = count_chords


def parse_chord(text):
    """Turn "T+I" into a button bitmask (bit 0 thumb ... bit 4 pinky)."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("expected a chord like \"T+I\", got {!r}".format(text))
    mask = 0
    for part in text.split("+"):
        name = part.strip().upper()
        if len(name) != 1 or name not in BUTTONS:
            raise ValueError(
                "unknown button {!r} in chord {!r} (use T, I, M, R, P)".format(part.strip(), text)
            )
        bit = 1 << BUTTONS.index(name)
        if mask & bit:
            raise ValueError("button {} appears twice in chord {!r}".format(name, text))
        mask |= bit
    return mask


def chord_name(mask):
    return "+".join(b for i, b in enumerate(BUTTONS) if mask & (1 << i))


def _parse_action(value):
    if isinstance(value, tuple):
        if len(value) != 2:
            raise ValueError("expected (\"KEYS\", \"once\", \"repeat\" or \"cycle\"), got {!r}".format(value))
        keys, held = value
        if held not in HELD_BEHAVIOURS:
            raise ValueError("held behaviour must be \"once\", \"repeat\" or \"cycle\", got {!r}".format(held))
        action = Action(parse_keys(keys), held)
        if held == "cycle" and (not action.modifiers or len(action.modifiers) == len(action.keys)):
            raise ValueError("\"cycle\" needs a modifier and a key, like \"CMD+TAB\", got {!r}".format(keys))
        return action
    return Action(parse_keys(value))


def _setting(module, name, default, errors):
    value = getattr(module, name, default)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        errors.append("{} must be a whole number of milliseconds above 0, got {!r}".format(name, value))
        return default
    return value


def load(module):
    """Build a Config from a mappings module. Raises MappingError listing every problem."""
    errors = []
    hold_ms = _setting(module, "HOLD_MS", 400, errors)
    repeat_delay_ms = _setting(module, "REPEAT_DELAY_MS", 400, errors)
    repeat_interval_ms = _setting(module, "REPEAT_INTERVAL_MS", 50, errors)
    cycle_interval_ms = _setting(module, "CYCLE_INTERVAL_MS", 500, errors)

    count_chords = getattr(module, "COUNT_CHORDS", False)
    if not isinstance(count_chords, bool):
        errors.append("COUNT_CHORDS must be True or False, got {!r}".format(count_chords))
        count_chords = False

    mode_chord = 0
    try:
        mode_chord = parse_chord(getattr(module, "MODE_CHORD", "T+I+M+R+P"))
    except ValueError as e:
        errors.append("MODE_CHORD: {}".format(e))

    sets = {}
    for mode in MODES:
        name = mode.upper()
        table = getattr(module, name, None)
        if not isinstance(table, dict):
            errors.append("{} must be a dict of chord: action".format(name))
            continue
        actions = {}
        for chord_text, value in table.items():
            where = "{}[{!r}]".format(name, chord_text)
            try:
                chord = parse_chord(chord_text)
            except ValueError as e:
                errors.append("{}: {}".format(where, e))
                continue
            if chord == mode_chord:
                errors.append("{}: {} is the MODE_CHORD".format(where, chord_name(chord)))
                continue
            if chord in actions:
                errors.append("{}: {} is mapped twice".format(where, chord_name(chord)))
                continue
            try:
                actions[chord] = _parse_action(value)
            except ValueError as e:
                errors.append("{}: {}".format(where, e))
        sets[mode] = actions

    if errors:
        raise MappingError("\n".join(errors))
    return Config(hold_ms, repeat_delay_ms, repeat_interval_ms, mode_chord, sets, count_chords, cycle_interval_ms)
