"""A friendly cartoon left hand, palm down, with each fingertip in its finger's colour."""

import math

from drawings.sketch import dot, sketch
from drawings.style import CREASE, FINGERS, HAND_FONT, INK, SKIN, SKIN_LABEL, SLEEVE, pt

# Cartoon left hand seen from above, palm down. Per finger: base centre,
# length, half width and angle from vertical in degrees (positive leans
# towards the thumb). Units are mm before scaling.
HAND = {
    "P": ((8.0, 41.0), 19.0, 4.5, -9),
    "R": ((17.0, 35.5), 25.0, 4.8, -3),
    "M": ((26.4, 34.0), 27.5, 4.9, 1),
    "I": ((35.6, 36.5), 24.5, 4.8, 6),
    "T": ((38.0, 58.5), 21.0, 5.6, 54),
}


def _finger(letter):
    (bx, by), length, h, deg = HAND[letter]
    a = math.radians(deg)
    d = (math.sin(a), -math.cos(a))
    n = (d[1], -d[0])
    c = (bx + d[0] * (length - h), by + d[1] * (length - h))
    return (bx, by), d, n, h, c, length


def _at(p, d, along, n, side):
    return (p[0] + d[0] * along + n[0] * side, p[1] + d[1] * along + n[1] * side)


def _finger_points(letter, start=0.0):
    b, d, n, h, c, length = _finger(letter)
    pts = [_at(b, d, start, n, h), _at(c, d, 0, n, h)]
    for k in range(1, 6):
        phi = math.pi * k / 6
        pts.append(_at(c, d, h * math.sin(phi), n, h * math.cos(phi)))
    pts += [_at(c, d, 0, n, -h), _at(b, d, start, n, -h)]
    return pts


def _smooth(points):
    """An open Catmull-Rom curve through the points, as SVG path data."""
    p = [points[0]] + points + [points[-1]]
    out = ["M{:.2f},{:.2f}".format(*points[0])]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out.append("C{:.2f},{:.2f} {:.2f},{:.2f} {:.2f},{:.2f}".format(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1]))
    return " ".join(out)


def hand(ox, oy, scale):
    """A friendly cartoon left hand, palm down, with each fingertip in its finger's colour."""
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
    path = 'd="{}"'.format(_smooth(outline))
    parts = [
        '<g transform="translate({:.2f} {:.2f}) scale({})">'.format(ox, oy, scale),
        sketch(path, SKIN, INK, 0.9),
        # Knuckle creases and the thumb fold.
        sketch('d="M14.5,47.5 q2.5,1.2 5,0 M24,46 q2.5,1.2 5,0 M33,47.5 q2.2,1.1 4.4,0"', "none", CREASE, 0.45),
        sketch('d="M38.6,52 C36.2,56 35,60 35,65"', "none", CREASE, 0.5),
        # Sleeve cuff.
        sketch('d="M6.5,80 C16,82.5 30,82.5 39.5,80 L41,93 C30,95.5 16,95.5 5,93 Z"', SLEEVE, INK, 0.9),
        sketch('d="M8,86.5 C17,88.5 29,88.5 39,86.5"', "none", "#5b9ac4", 0.4),
    ]
    for letter, finger, _ in FINGERS:
        b, d, n, h, c, length = _finger(letter)
        parts.append(dot(c[0] - d[0] * 0.6, c[1] - d[1] * 0.6, h * 0.7, letter))
        mid = _at(b, d, length * {"T": 0.18, "P": 0.28}.get(letter, 0.4), n, 0)
        angle = HAND[letter][3] - 90
        parts.append(
            '<text x="0" y="0" transform="translate({:.2f} {:.2f}) rotate({:.1f})" font-family="{}" font-size="{}" '
            'font-weight="700" fill="{}" text-anchor="middle" dy="0.9">{}</text>'.format(
                mid[0], mid[1], angle, HAND_FONT, pt(7.5), SKIN_LABEL, finger.lower()))
    parts.append("</g>")
    return "".join(parts)
