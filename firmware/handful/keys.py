"""Key names used in mappings.py and their USB HID usage IDs."""

MODIFIERS = {
    "CTRL": 0xE0,
    "SHIFT": 0xE1,
    "ALT": 0xE2,
    "GUI": 0xE3,
}

ALIASES = {
    "CONTROL": "CTRL",
    "OPTION": "ALT",
    "OPT": "ALT",
    "CMD": "GUI",
    "COMMAND": "GUI",
    "WIN": "GUI",
    "WINDOWS": "GUI",
    "RETURN": "ENTER",
    "ESC": "ESCAPE",
    "DEL": "DELETE",
    "PRTSCN": "PRINT_SCREEN",
    "PRINTSCREEN": "PRINT_SCREEN",
}

KEYS = {
    "ENTER": 0x28,
    "ESCAPE": 0x29,
    "BACKSPACE": 0x2A,
    "TAB": 0x2B,
    "SPACE": 0x2C,
    "MINUS": 0x2D,
    "EQUALS": 0x2E,
    "LEFT_BRACKET": 0x2F,
    "RIGHT_BRACKET": 0x30,
    "BACKSLASH": 0x31,
    "SEMICOLON": 0x33,
    "QUOTE": 0x34,
    "GRAVE": 0x35,
    "COMMA": 0x36,
    "PERIOD": 0x37,
    "SLASH": 0x38,
    "CAPS_LOCK": 0x39,
    "PRINT_SCREEN": 0x46,
    "SCROLL_LOCK": 0x47,
    "PAUSE": 0x48,
    "INSERT": 0x49,
    "HOME": 0x4A,
    "PAGE_UP": 0x4B,
    "DELETE": 0x4C,
    "END": 0x4D,
    "PAGE_DOWN": 0x4E,
    "RIGHT": 0x4F,
    "LEFT": 0x50,
    "DOWN": 0x51,
    "UP": 0x52,
}
for _i in range(26):
    KEYS[chr(ord("A") + _i)] = 0x04 + _i
for _i in range(1, 10):
    KEYS[str(_i)] = 0x1D + _i
KEYS["0"] = 0x27
for _i in range(1, 13):
    KEYS["F" + str(_i)] = 0x39 + _i
for _i in range(13, 25):
    KEYS["F" + str(_i)] = 0x5B + _i


def parse_keys(text):
    """Turn "CMD+SHIFT+4" into HID usage IDs, modifiers first.

    Raises ValueError with a readable message for unknown or empty names.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("expected keys like \"CMD+V\", got {!r}".format(text))
    modifiers = []
    others = []
    for part in text.split("+"):
        name = part.strip().upper()
        name = ALIASES.get(name, name)
        if name in MODIFIERS:
            code = MODIFIERS[name]
            if code not in modifiers:
                modifiers.append(code)
        elif name in KEYS:
            code = KEYS[name]
            if code not in others:
                others.append(code)
        else:
            raise ValueError("unknown key {!r} in {!r}".format(part.strip(), text))
    return tuple(modifiers + others)
