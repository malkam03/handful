# 0024: The Pico hangs in the shell, under two bridges

## Context

The grip shell ([0017](0017-grip-shell-parts-and-fastening.md)) holds the
five key modules and the status LED, and every one of their wires runs to
the Pico. With the Pico on the base, each wire must be long enough to
reach across while the base is open, and the spare length must be tucked
in as the base closes, which makes assembly fiddly.
The shell prints rim-down, so anything that holds the Pico from the
shell's side must print without supports inside a closed cavity. The
Pico's four 2.1 mm holes sit 2 mm in from its short ends, 11.4 mm apart
across the board (Raspberry Pi Pico datasheet), and the board's back face is flat.

## Options considered

- Keep the Pico on the base: simple to print, but the wires stay long and
  the base can only close with everything already soldered.
- Pads in the shell with the board right side up: the pads hang from the
  bay's roof, so they need supports inside a closed cavity, which are hard
  to remove.
- A printed snap cradle in the shell: no screws, but the clips need tuning
  and loosen as the board goes in and out.
- Two bridges across the Pico's bay with the board upside down under them,
  screwed up from below into heat-set inserts in the bridges: the bridges
  print as bridges, and the board's flat back face rests on them.

## Decision

We will hang the Pico upside down under two bridges across its bay, one at
each short end of the board. Each bridge holds two M2 heat-set inserts,
pressed in from below, and four M2 × 4 mm screws go up through the board's
holes into them. A 45° chamfer at each wall shortens the bridged span to
the board's width and centres the board. The board's component face sits
6.9 mm above the base, so the USB socket lines up with the same plug
channel and cable groove, and the screw heads clear the base. The base is
a lid with the module posts, the thumb block and the dovetail.

## Consequences

- The switches, LED and Pico are all in the shell, so the wires are short
  and every joint can be soldered and tested with the base off.
- The USB cable plugs in before the base goes on and stays captive.
- The bridges cover pins 1, 2, 19, 20, 21, 22, 39 and 40. The firmware uses
  none of them; keep their holes free of solder on the board's back face so
  it seats flat. Each bridge ends 5 mm in from the board's end, so the GND
  pins next to it (3, 18, 23 and 38) stay free to solder.
- The board's components, its LED and the BOOTSEL button face the base,
  so they are hidden once the base is on and reachable with it off.
- The bridges add a little plastic and print as 21 mm bridges, within what
  PLA and PETG bridge cleanly.
