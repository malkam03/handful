# handful mappings. Edit and save; the Pico restarts with the new mappings.
#
# Buttons: T thumb, I index, M middle, R ring, P pinky.
# A chord is the buttons joined with "+", like "T+I".
# An action is the keys to press together, like "CMD+SHIFT+4".
#   Modifiers: CMD, OPTION, CTRL, SHIFT, WIN (CMD and WIN are the same key,
#   as are OPTION and ALT).
#   Keys: A-Z, 0-9, F1-F24, ENTER, ESCAPE, BACKSPACE, DELETE, TAB, SPACE,
#   UP, DOWN, LEFT, RIGHT, HOME, END, PAGE_UP, PAGE_DOWN, PRINT_SCREEN and
#   punctuation such as MINUS, COMMA, PERIOD, SLASH.
# A held chord fires its action once. To repeat while held, write
#   ("BACKSPACE", "repeat"). To keep the modifiers down and press the key
#   again and again until you lift, as for switching apps, write
#   ("CMD+TAB", "cycle").
# Chords that aren't listed do nothing.
#
# LED on (RGB LED green): macOS mode. LED off (RGB LED blue): Windows mode.
# Fast blink (RGB LED red): this file has a problem; the serial console says
# what it is.

# How long a chord is held before it counts as a hold, in milliseconds.
HOLD_MS = 400
# After a repeating hold fires, wait this long, then repeat at this interval.
REPEAT_DELAY_MS = 400
REPEAT_INTERVAL_MS = 50
# A cycling hold opens the switcher at the hold, then moves on one step this
# often until you lift.
CYCLE_INTERVAL_MS = 500

# Hold this chord to switch between macOS and Windows. Tapping it does nothing.
MODE_CHORD = "T+I+M+R+P"

# Count how often each chord is tapped and held, to see which chords deserve
# the easiest spots. Only totals are kept, with no order or times. Counts are
# saved to the Pico's flash once a minute while you type, which wears it, so
# turn this on for a week or two of tuning, then off again.
# Read them with: python3 tools/usage.py
COUNT_CHORDS = False

MACOS = {
    "T": "OPTION+SPACE",  # push-to-talk
    "I": "ENTER",  # enter
    "M": "CMD+V",  # paste
    "R": "CMD+C",  # copy
    "P": ("BACKSPACE", "repeat"),  # backspace
    "T+I": "SHIFT+ENTER",  # new line, not sent
    "T+M": "CMD+OPTION+SHIFT+V",  # paste as plain text
    "T+R": "CMD+X",  # cut
    "T+P": ("OPTION+BACKSPACE", "repeat"),  # delete word
    "M+R": "CMD+Z",  # undo
    "T+M+R": "CMD+SHIFT+Z",  # redo
    "R+P": "ESCAPE",  # escape
    "T+I+M": "CMD+SPACE",  # search
    "I+R": "CTRL+UP",  # window overview
    "I+M": "CMD+SHIFT+4",  # region screenshot
    "I+M+R": "CMD+SHIFT+3",  # full screenshot
    "I+M+R+P": "CMD+A",  # select all
}

WINDOWS = {
    "T": "CTRL+SPACE",  # push-to-talk
    "I": "ENTER",  # enter
    "M": "CTRL+V",  # paste
    "R": "CTRL+C",  # copy
    "P": ("BACKSPACE", "repeat"),  # backspace
    "T+I": "SHIFT+ENTER",  # new line, not sent
    "T+M": "CTRL+SHIFT+V",  # paste as plain text
    "T+R": "CTRL+X",  # cut
    "T+P": ("CTRL+BACKSPACE", "repeat"),  # delete word
    "M+R": "CTRL+Z",  # undo
    "T+M+R": "CTRL+Y",  # redo
    "R+P": "ESCAPE",  # escape
    "T+I+M": "WIN+S",  # search
    "I+R": "WIN+TAB",  # window overview
    "I+M": "WIN+SHIFT+S",  # region screenshot
    "I+M+R": "WIN+PRINT_SCREEN",  # full screenshot
    "I+M+R+P": "CTRL+A",  # select all
}
