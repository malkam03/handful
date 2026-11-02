"""The printable A4 cheat sheet."""

from xml.sax.saxutils import escape

from drawings.hand import hand
from drawings.labels import HELD_MARKS, held_mark, mac_label, win_label
from drawings.layout import Layout
from drawings.sketch import FILTERS, GLYPH_REACH, circle_d, glyph, highlight, rect_d, sketch, squiggle
from drawings.style import COLOUR, GREY, INK, MARKER, NOTE, PAPER, REPEAT, TILTS, embed_fonts, text, text_width, wrap


def heading(x, y, title, subtitle, colour):
    return (
        text(x, y, escape(title), 16, 400, INK, "start", MARKER)
        + squiggle(x, y + 2.2, text_width(title, 16, MARKER), colour, 0.9)
        + text(x, y + 7.2, escape(subtitle), 8, 400, GREY)
    )


def centred(x, w, left, right):
    """Shift for content spanning left..right (relative to x) so it sits in the middle of a card."""
    return x + (w - (right - left)) / 2 - left


def title_width(title, size, mark):
    return text_width(title, size) + (text_width(" " + mark, size) if mark else 0)


def chord_card(x, y, w, h, chord, name, mac, win, colour, tilt):
    out = ['<g transform="rotate({:.2f} {:.2f} {:.2f})">'.format(tilt, x + w / 2, y + h / 2)]
    out.append(sketch(rect_d(x, y, w, h), "#fff", INK, 0.45))
    title = name[:1].upper() + name[1:]
    keys_w = max(text_width(mac_label(mac), 9.5), text_width(win_label(win), 9.5))
    mark = held_mark(mac, win)
    right = 23 + max(title_width(title, 11, mark), 7 + keys_w)
    x = centred(x, w, 11.5 - GLYPH_REACH * 0.95 - 1.95, right)
    out.append(glyph(x + 11.5, y + h / 2 - 1.2, chord, 0.95, 1.95))
    out.append(highlight(x + 23, y + 8.4, text_width(title, 11), colour))
    label = escape(title)
    if mark:
        label += '<tspan fill="{}" font-weight="700"> {}</tspan>'.format(REPEAT, mark)
    out.append(text(x + 23, y + 8.4, label, 11, 700))
    for i, (tag, keys) in enumerate((("mac", mac_label(mac)), ("win", win_label(win)))):
        ly = y + 15.2 + i * 5.4
        out.append(text(x + 23, ly, tag, 7, 400, GREY))
        out.append(text(x + 30, ly, escape(keys), 9.5, 400, INK))
    out.append("</g>")
    return "".join(out)


def sticky_note(x, y, w, h, settings):
    hold = settings.hold_ms
    rows = [
        ("Tap", "press, then lift every finger. It fires as you lift."),
        ("Hold", "keep it down {} ms and it fires right away, once.".format(hold)),
        (HELD_MARKS["repeat"], "repeats for as long as you hold."),
        (HELD_MARKS["cycle"], "keeps the switcher open and steps on until you lift."),
        ("Cancel", "squeeze in the other fingers before lifting."),
    ]
    out = ['<g transform="rotate(-1.5 {:.2f} {:.2f})">'.format(x + w / 2, y + h / 2)]
    out.append(sketch(rect_d(x, y, w, h), NOTE, "#d8c25a", 0.4))
    out.append('<rect x="{:.2f}" y="{:.2f}" width="16" height="5" fill="#e9e4d8" fill-opacity="0.85" '
               'transform="rotate(4 {:.2f} {:.2f})" filter="url(#rough)"/>'.format(
                   x + w / 2 - 8, y - 2.5, x + w / 2, y))
    out.append(text(x + 4, y + 9, "How it works", 13, 400, INK, "start", MARKER))
    cy = y + 15.5
    for label, body in rows:
        repeat = label in HELD_MARKS.values()
        out.append(text(x + 4, cy, label, 11 if repeat else 8.5, 700, REPEAT if repeat else INK))
        lines = wrap(body, 33)
        for j, line in enumerate(lines):
            out.append(text(x + 15.5, cy + j * 3.8, escape(line), 8.2, 400))
        cy += 3.8 * len(lines) + 1.5
    out.append("</g>")
    return "".join(out)


def mode_box(x, y, all_five):
    return "".join([
        glyph(x + 10, y + 5, all_five, 0.95, 1.95),
        text(x + 21, y + 3, "Hold all five", 11.5, 700),
        text(x + 21, y + 7.6, "to switch macOS / Windows.", 8.5, 400),
        sketch(circle_d(x + 22.2, y + 11.7, 1.2), "#F0C419", INK, 0.3),
        text(x + 25, y + 12.7, "LED on: macOS", 8, 400),
        sketch(circle_d(x + 48.5, y + 11.7, 1.2), "#fff", INK, 0.3),
        text(x + 51.2, y + 12.7, "off: Windows", 8, 400),
    ])


def render(mappings_path):
    """The printable A4 sheet."""
    layout = Layout(mappings_path)
    settings = layout.settings
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">',
        FILTERS,
        '<rect width="297" height="210" fill="{}"/>'.format(PAPER),
        text(12, 21, "handful", 34, 400, INK, "start", MARKER),
        squiggle(12, 24.5, 44, COLOUR["P"], 1.1),
        text(12, 32, "chord cheat sheet for your left hand", 9.5, 400, GREY),
        hand(15, 37, 0.88),
        sticky_note(10, 124, 68, 54, settings),
        mode_box(10, 186, settings.mode_chord),
    ]

    column, gutter, x = 63, 5, 86
    pitch, card_h = 27, 24.6
    card = 0
    for title, subtitle, colour, rows in layout.groups:
        out.append(heading(x + 1, 22, title, subtitle, colour))
        y = 37
        for chord, name, mac, win in rows:
            out.append(chord_card(x, y, column, card_h, chord, name, mac, win, colour, TILTS[card % len(TILTS)]))
            card += 1
            y += pitch
        x += column + gutter

    out.append(text(285, 204, "Chords not listed do nothing. Change them in mappings.py on the CIRCUITPY drive; "
                    "a fast LED blink means it needs a fix.", 7.5, 400, GREY, "end"))
    out.append("</svg>\n")
    return embed_fonts("\n".join(out))
