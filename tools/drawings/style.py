"""Colours, fonts and text helpers shared by every drawing. Sizes are in mm unless noted."""

import base64
import functools
import io
import os
import re
from xml.sax.saxutils import unescape

from fontTools import subset
from fontTools.ttLib import TTFont

from handful import config

# Fonts embedded in every drawing, so it looks the same on any computer.
# Both are Apache-2.0 licensed; see fonts/LICENSE.txt.
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
FACES = {
    "handful marker": "PermanentMarker-Regular.ttf",
    "handful hand": "ComingSoon-Regular.ttf",
}
# Width of a symbol such as \u2318 that the font lacks and the viewer draws from a system font, in em.
FALLBACK_EM = 0.85

HAND_FONT = "'handful hand', 'Comic Sans MS', cursive"
MARKER = "'handful marker', 'Comic Sans MS', cursive"
INK = "#2b2b33"
GREY = "#76716a"
PAPER = "#fffaf0"
SKIN = "#9a6440"
CREASE = "#5a3520"
SKIN_LABEL = "#fbe9d7"
SLEEVE = "#8ec5e8"
NOTE = "#fff1a6"
REPEAT = "#0072B2"
PT = 0.3528  # millimetres per point

# Okabe-Ito colours, readable with every common type of colour blindness.
FINGER_STYLE = {
    "T": ("Thumb", "#E69F00"),
    "I": ("Index", "#0072B2"),
    "M": ("Middle", "#009E73"),
    "R": ("Ring", "#CC79A7"),
    "P": ("Pinky", "#D55E00"),
}
# (letter, name, colour) in chord bit order.
FINGERS = [(letter,) + FINGER_STYLE[letter] for letter in config.BUTTONS]
COLOUR = {letter: colour for letter, _, colour in FINGERS}

# Small, repeating tilts so the cards look placed by hand.
TILTS = (-0.6, 0.4, -0.2, 0.7, -0.4, 0.3, -0.7)


def pt(size):
    return round(size * PT, 2)


def text(x, y, content, size, weight=400, fill=INK, anchor="start", family=HAND_FONT, extra=""):
    """`size` is in points; everything else is in mm."""
    return (
        '<text x="{:.2f}" y="{:.2f}" font-family="{}" font-size="{}" font-weight="{}" fill="{}" '
        'text-anchor="{}" {}>{}</text>'.format(x, y, family, pt(size), weight, fill, anchor, extra, content)
    )


@functools.lru_cache(maxsize=None)
def _font(family):
    name = family.split("'")[1]
    return TTFont(os.path.join(FONT_DIR, FACES[name]), recalcTimestamp=False)


def text_width(content, size, family=HAND_FONT):
    """How wide `content` is at `size` points, measured from the font."""
    font = _font(family)
    cmap, metrics, units = font.getBestCmap(), font["hmtx"], font["head"].unitsPerEm
    em = sum(metrics[cmap[ord(c)]][0] / units if ord(c) in cmap else FALLBACK_EM for c in content)
    return em * pt(size)


def embed_fonts(svg):
    """Add both fonts to the SVG, cut down to the characters it uses."""
    used = unescape("".join(re.findall(r">([^<>]+)<", svg)))
    faces = []
    for name, file in FACES.items():
        options = subset.Options()
        options.hinting = False
        subsetter = subset.Subsetter(options)
        subsetter.populate(text=used)
        font = TTFont(os.path.join(FONT_DIR, file), recalcTimestamp=False)
        subsetter.subset(font)
        data = io.BytesIO()
        font.save(data)
        faces.append("@font-face{{font-family:'{}';src:url(data:font/ttf;base64,{})}}".format(
            name, base64.b64encode(data.getvalue()).decode("ascii")))
    start = svg.index(">") + 1
    return svg[:start] + "\n<style>" + "".join(faces) + "</style>" + svg[start:]


def wrap(words, limit):
    lines, line = [], ""
    for word in words.split():
        candidate = (line + " " + word).strip()
        if len(candidate) > limit and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    lines.append(line)
    return lines
