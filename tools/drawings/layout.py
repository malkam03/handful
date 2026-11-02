"""Read mappings.py and group its chords the way the drawings show them."""

import io
import tokenize
import types

from handful import config

THUMB = 1 << config.BUTTONS.index("T")


def fingers(chord):
    return bin(chord).count("1")


GROUPS = [
    ("One finger", "The everyday moves", lambda chord: fingers(chord) == 1),
    ("Thumb +", "A twist on that finger", lambda chord: chord & THUMB and fingers(chord) > 1),
    ("Combos", "More fingers, bigger action", lambda chord: not chord & THUMB and fingers(chord) > 1),
]

# Chords per group that fit in each drawing's column.
ROWS = 6

# Highlighter colour behind each group's chord names.
HIGHLIGHT = ["#ffe45c", "#a9dcff", "#a6efb4"]


def load_mappings(path):
    module = types.ModuleType("mappings")
    with open(path) as f:
        source = f.read()
    exec(compile(source, path, "exec"), module.__dict__)
    comments = {}
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT:
            comments[token.start[0]] = token.string.lstrip("#").strip()
    return module, source, comments


def action_names(source, comments, set_name):
    """Map each chord in MACOS or WINDOWS to the comment on its line."""
    names = {}
    inside = False
    for number, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith(set_name + " = {"):
            inside = True
            continue
        if inside and stripped.startswith("}"):
            break
        if inside and stripped.startswith('"') and number in comments:
            chord_text = stripped.split('"')[1]
            names[config.parse_chord(chord_text)] = comments[number]
    return names


class Layout:
    """Everything the drawings need from mappings.py."""

    def __init__(self, mappings_path):
        module, source, comments = load_mappings(mappings_path)
        self.settings = config.load(module)
        names = action_names(source, comments, "MACOS")
        names.update({k: v for k, v in action_names(source, comments, "WINDOWS").items() if k not in names})
        mac_raw = {config.parse_chord(k): v for k, v in module.MACOS.items()}
        win_raw = {config.parse_chord(k): v for k, v in module.WINDOWS.items()}
        chords = list(mac_raw) + [c for c in win_raw if c not in mac_raw]
        self.groups = []
        for (title, subtitle, belongs), colour in zip(GROUPS, HIGHLIGHT):
            group = sorted((c for c in chords if belongs(c)), key=lambda c: (bin(c).count("1"), c))
            if len(group) > ROWS:
                raise SystemExit("{} has {} chords; the drawings fit {}. Give the layout more rows.".format(
                    title, len(group), ROWS))
            rows = []
            for chord in group:
                # A chord missing from one set does nothing in that mode, so it's drawn as a dash there.
                mac, win = mac_raw.get(chord), win_raw.get(chord)
                rows.append((chord, names.get(chord, config.chord_name(chord)), mac, win))
            if rows:
                self.groups.append((title, subtitle, colour, rows))
