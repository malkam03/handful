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
#   ("BACKSPACE", "repeat").
# Chords that aren't listed do nothing.
#
# LED on: macOS mode. LED off: Windows mode. Fast blink: this file has a
# problem; the serial console says what it is.

# How long a chord is held before it counts as a hold, in milliseconds.
HOLD_MS = 400
# After a repeating hold fires, wait this long, then repeat at this interval.
REPEAT_DELAY_MS = 400
REPEAT_INTERVAL_MS = 50

# Hold this chord to switch between macOS and Windows. Tapping it does nothing.
MODE_CHORD = "T+I+M+R+P"

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
    "I+M": "WIN+SHIFT+S",  # region screenshot
    "I+M+R": "WIN+PRINT_SCREEN",  # full screenshot
    "I+M+R+P": "CTRL+A",  # select all
}
