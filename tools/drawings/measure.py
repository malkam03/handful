"""The hand measurement guide: the cartoon left hand, palm up, with every measurement the CAD build takes."""

from drawings.hand import _finger, _finger_points, _smooth
from drawings.sketch import FILTERS, circle_d, sketch, squiggle
from drawings.style import COLOUR, CREASE, GREY, INK, MARKER, PAPER, SKIN, SLEEVE, embed_fonts, text, text_width

WIDTH, HEIGHT = 232, 180
OX, OY, SCALE = 34, 18, 1.55  # where the hand goes and how big
SPAN = 44.0  # mirror line: the cartoon hand is drawn palm down, so mirroring it shows a left palm
WRIST_Y = 77.5  # the wrist crease, just above the sleeve, in hand units
CREASE_ALONG = 3.0  # each finger's base crease, mm along the finger from its base, in hand units
THUMB_CREASE = 11.3  # the thumb's last joint crease, along the thumb: its last segment is about 46% of it

# (letter, colour, what to measure, the name in hand.local.toml)
MEASUREMENTS = (
    ("A", INK, "Hand length: wrist crease to middle fingertip", "hand_length"),
    ("B", INK, "Palm length: wrist crease to middle base crease", "palm_length"),
    ("C", INK, "Hand breadth: across the knuckles, no thumb", "hand_breadth"),
    ("D", COLOUR["I"], "Index finger: base crease to fingertip", "index_length"),
    ("E", COLOUR["M"], "Middle finger: base crease to fingertip", "middle_length"),
    ("F", COLOUR["R"], "Ring finger: base crease to fingertip", "ring_length"),
    ("G", COLOUR["P"], "Pinky: base crease to fingertip", "pinky_length"),
    ("H", COLOUR["I"], "Index base crease: how far behind the middle's", "index_knuckle_back"),
    ("I", COLOUR["R"], "Ring base crease: how far behind the middle's", "ring_knuckle_back"),
    ("J", COLOUR["P"], "Pinky base crease: how far behind the middle's", "pinky_knuckle_back"),
    ("K", COLOUR["T"], "Thumb reach: wrist crease to thumb tip", "thumb_reach"),
    ("L", COLOUR["T"], "Thumb tip: last joint crease to thumb tip", "thumb_tip_length"),
)
STYLE = {letter: colour for letter, colour, _, _ in MEASUREMENTS}

def _page(p):
    """A point in hand units, mirrored into a palm-up left hand, in page mm."""
    return OX + (SPAN - p[0]) * SCALE, OY + p[1] * SCALE

def _along(letter, along):
    b, d, _, _, _, _ = _finger(letter)
    return _page((b[0] + d[0] * along, b[1] + d[1] * along))

def _tip(letter):
    return _along(letter, _finger(letter)[5])

def _crease(letter):
    return _along(letter, CREASE_ALONG)

def _beside(letter, along, side):
    """A point beside a finger, ``side`` hand units off its centre line."""
    b, d, n, _, _, _ = _finger(letter)
    return _page((b[0] + d[0] * along + n[0] * side, b[1] + d[1] * along + n[1] * side))

def _line(a, b, colour, width=0.45, dashed=False):
    """A marker line with a slight bow. A perfectly straight one has a flat
    bounding box, and the wobble filter would hide it."""
    dash = ' stroke-dasharray="1.2 1.4"' if dashed else ""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = max((dx * dx + dy * dy) ** 0.5, 1e-6)
    bow = min(0.5, length * 0.02)
    mid = ((a[0] + b[0]) / 2 - dy / length * bow, (a[1] + b[1]) / 2 + dx / length * bow)
    d = 'd="M{:.2f},{:.2f} Q{:.2f},{:.2f} {:.2f},{:.2f}"{}'.format(a[0], a[1], mid[0], mid[1], b[0], b[1], dash)
    return sketch(d, "none", colour, width)

def _badge(x, y, letter, r=2.6):
    return sketch(circle_d(x, y, r), STYLE[letter], INK, 0.35) + text(
        x, y + r * 0.42, letter, r * 3.1, 700, "#fff", "middle", MARKER)

def _dimension(a, b, letter, badge_at=0.5, shift=(0.0, 0.0)):
    """A measurement from a to b: end bars, a line and the letter on it."""
    colour = STYLE[letter]
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = (dx * dx + dy * dy) ** 0.5
    nx, ny = -dy / length * 1.4, dx / length * 1.4
    out = [_line(a, b, colour, 0.55)]
    for p in (a, b):
        out.append(_line((p[0] - nx, p[1] - ny), (p[0] + nx, p[1] + ny), colour, 0.55))
    mx, my = a[0] + dx * badge_at + shift[0], a[1] + dy * badge_at + shift[1]
    out.append(_badge(mx, my, letter))
    return "".join(out)

def _hand():
    outline = [(10.5, 84.0), (5.0, 70.0), (3.6, 54.0)]
    fingers = [_finger_points(letter, start=2.0) for letter in "PRMI"]
    for i, pts in enumerate(fingers):
        if i:
            a, b = fingers[i - 1][-1], pts[0]
            outline.append(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 0.6))
        outline += pts
    outline += [(40.6, 45.0)]
    outline += _finger_points("T", start=7.0)[:-1]
    outline += [(39.0, 66.0), (36.5, 73.0), (35.0, 84.0)]
    creases = []
    for letter in "PRMI":
        b, d, n, h, _, _ = _finger(letter)
        c = (b[0] + d[0] * CREASE_ALONG, b[1] + d[1] * CREASE_ALONG)
        creases.append("M{:.2f},{:.2f} L{:.2f},{:.2f}".format(
            c[0] - n[0] * h * 0.8, c[1] - n[1] * h * 0.8, c[0] + n[0] * h * 0.8, c[1] + n[1] * h * 0.8))
    b, d, n, h, _, _ = _finger("T")
    c = (b[0] + d[0] * THUMB_CREASE, b[1] + d[1] * THUMB_CREASE)
    creases.append("M{:.2f},{:.2f} L{:.2f},{:.2f}".format(
        c[0] - n[0] * h * 0.75, c[1] - n[1] * h * 0.75, c[0] + n[0] * h * 0.75, c[1] + n[1] * h * 0.75))
    return "".join([
        '<g transform="translate({:.2f} {:.2f}) scale({} {})">'.format(OX + SPAN * SCALE, OY, -SCALE, SCALE),
        sketch('d="{}"'.format(_smooth(outline)), SKIN, INK, 0.9),
        sketch('d="{}"'.format(" ".join(creases)), "none", CREASE, 0.45),
        # The thumb's palm crease and the wrist crease.
        sketch('d="M37.5,50 C33.5,56 31.5,64 32,72"', "none", CREASE, 0.5),
        sketch('d="M9,{0:.1f} C18,{1:.1f} 28,{1:.1f} 37,{0:.1f}"'.format(WRIST_Y, WRIST_Y + 1.2), "none", CREASE, 0.5),
        sketch('d="M6.5,80 C16,82.5 30,82.5 39.5,80 L41,93 C30,95.5 16,95.5 5,93 Z"', SLEEVE, INK, 0.9),
        sketch('d="M8,86.5 C17,88.5 29,88.5 39,86.5"', "none", "#5b9ac4", 0.4),
        "</g>",
    ])

def _measurements():
    out = []
    wrist = _page((26.4, WRIST_Y + 0.9))
    tip, crease = _tip("M"), _crease("M")
    a_x, b_x = _page((-13.0, 0))[0], _page((-5.5, 0))[0]
    for y, x in ((tip[1], a_x), (crease[1], b_x), (wrist[1], a_x)):
        out.append(_line((_page((26.4, 0))[0] if y != crease[1] else crease[0], y), (x + 2, y), GREY, 0.3, True))
    out.append(_dimension((a_x, wrist[1]), (a_x, tip[1]), "A", 0.45))
    out.append(_dimension((b_x, wrist[1]), (b_x, crease[1]), "B", 0.5))
    out.append(_dimension(_page((4.0, 48.5)), _page((40.4, 48.5)), "C", 0.62))
    for letter, finger in zip("DEFG", "IMRP"):
        out.append(_dimension(_crease(finger), _tip(finger), letter, 0.55))
    # The base crease steps, measured from a line through the middle finger's crease.
    left, right = _page((44.0, 0))[0], _page((1.0, 0))[0]
    out.append(_line((left, crease[1]), (right, crease[1]), INK, 0.35, True))
    for letter, finger, side in (("H", "I", -1), ("I", "R", 1), ("J", "P", 1)):
        b, d, n, h, _, _ = _finger(finger)
        edge = _page((b[0] + d[0] * CREASE_ALONG - side * h * 1.05, b[1] + d[1] * CREASE_ALONG))
        step = (edge[0], crease[1])
        out.append(_line(step, edge, STYLE[letter], 0.55))
        out.append(_badge(edge[0] + side * 4.2, (edge[1] + crease[1]) / 2 + 2.6, letter, 2.2))
    # The thumb: its reach from the wrist crease, and its last segment.
    thumb = _finger("T")
    out.append(_dimension(_page((37.0, WRIST_Y + 0.9)), _tip("T"), "K", 0.4))
    out.append(_dimension(_beside("T", THUMB_CREASE, -(thumb[3] + 3.0)),
                          _beside("T", thumb[5], -(thumb[3] + 3.0)), "L", 0.5))
    return "".join(out)

def _legend(x, y):
    out = [
        text(x, y, "Measure your hand", 17, 400, INK, "start", MARKER),
        squiggle(x, y + 2.4, text_width("Measure your hand", 17, MARKER), COLOUR["M"], 0.9),
        text(x, y + 10, "Left hand, palm up, fingers together and straight.", 8.5),
        text(x, y + 14.5, "Millimetres. Skip any you like: the defaults fill in.", 8.5),
    ]
    row = y + 25
    for letter, _, what, key in MEASUREMENTS:
        out.append(_badge(x + 2.6, row - 1.3, letter, 2.4))
        out.append(text(x + 7.5, row, what, 8.5))
        out.append(text(x + 7.5, row + 4.2, key, 7.5, 400, GREY))
        row += 10
    out.append(text(x, row + 1, "Write them in cad/hand.local.toml, a copy of hand.example.toml.", 8))
    out.append(text(x, row + 5.5, "Git ignores it, so your numbers stay on your computer.", 8, 400, GREY))
    return "".join(out)

def render_measurements(_=None):
    """The measurement guide as an SVG string."""
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="{0}mm" height="{1}mm" viewBox="0 0 {0} {1}">'.format(
            WIDTH, HEIGHT),
        FILTERS,
        '<rect width="{}" height="{}" rx="3" fill="{}"/>'.format(WIDTH, HEIGHT, PAPER),
        _hand(),
        _measurements(),
        _legend(136, 16),
        "</svg>\n",
    ]
    return embed_fonts("\n".join(out))
