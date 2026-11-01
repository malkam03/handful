"""The wide README banner: the hand, then every chord in a compact grid."""

from xml.sax.saxutils import escape

from drawings.hand import hand
from drawings.labels import mac_label, repeats, win_label
from drawings.layout import Layout
from drawings.sheet import centred, title_width
from drawings.sketch import FILTERS, GLYPH_REACH, glyph, highlight, rect_d, sketch, squiggle
from drawings.style import GREY, INK, MARKER, PAPER, REPEAT, TILTS, embed_fonts, text, text_width


def mini_card(x, y, w, h, chord, name, mac, win, colour, tilt):
    out = ['<g transform="rotate({:.2f} {:.2f} {:.2f})">'.format(tilt, x + w / 2, y + h / 2)]
    out.append(sketch(rect_d(x, y, w, h), "#fff", INK, 0.4))
    title = name[:1].upper() + name[1:]
    right = max(19.5 + title_width(title, 10, repeats(mac) or repeats(win)), 48 + text_width(win_label(win), 8.5))
    x = centred(x, w, 9.5 - GLYPH_REACH * 0.78 - 1.6, right)
    out.append(glyph(x + 9.5, y + h / 2 - 0.8, chord, 0.78, 1.6))
    out.append(highlight(x + 19.5, y + 7, text_width(title, 10), colour, 3.3))
    label = escape(title)
    if repeats(mac) or repeats(win):
        label += '<tspan fill="{}" font-weight="700"> \u21bb</tspan>'.format(REPEAT)
    out.append(text(x + 19.5, y + 7, label, 10, 700))
    out.append(text(x + 19.5, y + 13.6, "mac", 6.5, 400, GREY))
    out.append(text(x + 24.5, y + 13.6, escape(mac_label(mac)), 8.5, 400))
    out.append(text(x + 43, y + 13.6, "win", 6.5, 400, GREY))
    out.append(text(x + 48, y + 13.6, escape(win_label(win)), 8.5, 400))
    out.append("</g>")
    return "".join(out)


def render_banner(mappings_path):
    """A wide banner for the README: the hand, then every chord in a compact grid."""
    layout = Layout(mappings_path)
    width, height = 300, 128
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="{0}mm" height="{1}mm" viewBox="0 0 {0} {1}">'.format(
            width, height),
        FILTERS,
        '<rect width="{}" height="{}" rx="3" fill="{}"/>'.format(width, height, PAPER),
        hand(7, 6, 0.8),
        glyph(14, 98, layout.settings.mode_chord, 0.78, 1.6),
        text(26, 97, "Hold all five", 9.5, 700),
        text(26, 101.5, "to switch OS", 7.5, 400),
        text(6, 113, "Tap: fires when you lift.", 7.5, 400),
        text(6, 117.5, "Hold: fires after {} ms.".format(layout.settings.hold_ms), 7.5, 400),
        text(6, 122, "\u21bb repeats while held.", 7.5, 400, REPEAT),
    ]
    column, gutter, x = 74, 3, 64
    pitch, card_h = 20.4, 17.6
    card = 0
    for title, subtitle, colour, rows in layout.groups:
        out.append(text(x + 1, 11, escape(title), 13, 400, INK, "start", MARKER))
        out.append(squiggle(x + 1, 13, text_width(title, 13, MARKER), colour, 0.8))
        out.append(text(x + column, 11, escape(subtitle), 7.5, 400, GREY, "end"))
        y = 19
        for chord, name, mac, win in rows:
            out.append(mini_card(x, y, column, card_h, chord, name, mac, win, colour, TILTS[card % len(TILTS)] * 0.6))
            card += 1
            y += pitch
        x += column + gutter
    out.append("</svg>\n")
    return embed_fonts("\n".join(out))
