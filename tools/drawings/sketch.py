"""Hand-drawn marker strokes and the five-dot chord glyph."""

from drawings.style import COLOUR, FINGERS, GREY, INK, MARKER, text

# Wobbly marker lines. Two seeds so a doubled stroke looks sketched.
FILTERS = (
    '<defs>'
    '<filter id="rough" x="-5%" y="-5%" width="110%" height="110%">'
    '<feTurbulence type="fractalNoise" baseFrequency="0.09" numOctaves="2" seed="4"/>'
    '<feDisplacementMap in="SourceGraphic" scale="0.9" xChannelSelector="R" yChannelSelector="G"/></filter>'
    '<filter id="rough2" x="-5%" y="-5%" width="110%" height="110%">'
    '<feTurbulence type="fractalNoise" baseFrequency="0.13" numOctaves="2" seed="11"/>'
    '<feDisplacementMap in="SourceGraphic" scale="1.1" xChannelSelector="R" yChannelSelector="G"/></filter>'
    '</defs>'
)

# Chord glyph: fingertip positions relative to the middle finger, in mm.
GLYPH = {"P": (-8.4, 2.6), "R": (-4.3, -0.9), "M": (0.0, -2.0), "I": (4.4, -0.6), "T": (8.0, 6.2)}
# How far the glyph reaches left of its centre, in mm at scale 1.
GLYPH_REACH = -min(dx for dx, _ in GLYPH.values())


def sketch(shape, fill="none", stroke=INK, width=0.5):
    """Draw an SVG shape element twice through the wobble filters, like a marker going over it."""
    attrs = '{} fill="{}" stroke="{}" stroke-linecap="round" stroke-linejoin="round"'.format(shape, fill, stroke)
    return (
        '<path {} stroke-width="{:.2f}" filter="url(#rough)"/>'.format(attrs, width)
        + '<path {} fill-opacity="0" stroke-width="{:.2f}" stroke-opacity="0.55" filter="url(#rough2)"/>'.format(
            attrs, width * 0.5)
    )


def circle_d(x, y, r):
    return 'd="M{:.2f},{:.2f} a{r:.2f},{r:.2f} 0 1,0 {d:.2f},0 a{r:.2f},{r:.2f} 0 1,0 {m:.2f},0"'.format(
        x - r, y, r=r, d=2 * r, m=-2 * r)


def rect_d(x, y, w, h):
    return 'd="M{:.2f},{:.2f} h{:.2f} v{:.2f} h{:.2f} Z"'.format(x, y, w, h, -w)


def highlight(x, y, w, colour, h=3.6):
    """A highlighter swipe ending at baseline y."""
    return (
        '<path d="M{:.2f},{:.2f} l{:.2f},-0.5 l0.3,{:.2f} l{:.2f},0.4 Z" '
        'fill="{}" fill-opacity="0.75" filter="url(#rough)"/>'
    ).format(
        x - 1, y + 0.9, w + 2, -h, -(w + 2.3), colour)


def squiggle(x, y, w, colour, width=0.8):
    d = "M{:.2f},{:.2f}".format(x, y)
    steps = max(2, int(w / 4))
    for i in range(steps):
        d += " q{:.2f},{:.2f} {:.2f},0".format(w / steps / 2, -1.2 if i % 2 else 1.2, w / steps)
    return (
        '<path d="{}" fill="none" stroke="{}" stroke-width="{}" stroke-linecap="round" filter="url(#rough)"/>'
    ).format(
        d, colour, width)


def dot(x, y, r, letter):
    return sketch(circle_d(x, y, r), COLOUR[letter], INK, 0.35) + text(
        x, y + r * 0.42, letter, r * 3.1, 700, "#fff", "middle", MARKER)


def glyph(cx, cy, chord, scale=1.0, radius=2.0):
    parts = []
    for i, (letter, _, _) in enumerate(FINGERS):
        dx, dy = GLYPH[letter]
        x, y = cx + dx * scale, cy + dy * scale
        if chord & (1 << i):
            parts.append(dot(x, y, radius, letter))
        else:
            parts.append(sketch(circle_d(x, y, radius - 0.2), "none", GREY, 0.35))
    return "".join(parts)
