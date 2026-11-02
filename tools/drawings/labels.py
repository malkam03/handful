"""How a mapping's keys are written on the cards for each OS."""

from handful.keys import ALIASES, MODIFIERS

MAC_MODIFIERS = {"CTRL": "\u2303", "ALT": "\u2325", "SHIFT": "\u21e7", "GUI": "\u2318"}
WIN_MODIFIERS = {"CTRL": "Ctrl", "ALT": "Alt", "SHIFT": "Shift", "GUI": "Win"}
MAC_KEYS = {"ENTER": "Return", "BACKSPACE": "Delete", "ESCAPE": "Esc", "DELETE": "Fwd Del"}
WIN_KEYS = {"ENTER": "Enter", "BACKSPACE": "Backspace", "ESCAPE": "Esc", "PRINT_SCREEN": "PrtScn"}
MODIFIER_ORDER = ["CTRL", "ALT", "SHIFT", "GUI"]
WIN_MODIFIER_ORDER = ["GUI", "CTRL", "ALT", "SHIFT"]
UNMAPPED = "\u2014"


def split_keys(value):
    keys = value[0] if isinstance(value, tuple) else value
    modifiers, others = [], []
    for part in keys.split("+"):
        name = part.strip().upper()
        name = ALIASES.get(name, name)
        (modifiers if name in MODIFIERS else others).append(name)
    modifiers.sort(key=MODIFIER_ORDER.index)
    return modifiers, others


def pretty_key(name, table):
    if name in table:
        return table[name]
    if len(name) == 1:
        return name
    return name.replace("_", " ").title()


def mac_label(value):
    if value is None:
        return UNMAPPED
    modifiers, others = split_keys(value)
    symbols = "".join(MAC_MODIFIERS[m] for m in modifiers)
    keys = " ".join(pretty_key(k, MAC_KEYS) for k in others)
    if symbols and len(keys) > 1:
        return symbols + " " + keys
    return symbols + keys


def win_label(value):
    if value is None:
        return UNMAPPED
    modifiers, others = split_keys(value)
    modifiers.sort(key=WIN_MODIFIER_ORDER.index)
    return "+".join([WIN_MODIFIERS[m] for m in modifiers] + [pretty_key(k, WIN_KEYS) for k in others])


HELD_MARKS = {"repeat": "\u21bb", "cycle": "\u00bb"}


def held_mark(mac, win):
    """The mark after a chord's name when holding it repeats or cycles, else ""."""
    for value in (mac, win):
        if isinstance(value, tuple) and value[1] in HELD_MARKS:
            return HELD_MARKS[value[1]]
    return ""
