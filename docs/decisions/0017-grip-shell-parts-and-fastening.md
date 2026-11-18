# 0017: Grip shell shape, parts and how they join

## Context

The grip shell ([0011](0011-grip-shell.md)) holds five Kailh Choc v2 switches in
Kailh hot-swap sockets, hand-wired to a Pico with no PCB
([0023](0023-choc-v2-low-profile-switches.md)), sits on swappable tilt wedges and lets a
USB cable out ([0012](0012-wired-usb.md)). The hand should rest on it the
whole time, as on a palm-supported mouse, and press keys without lifting.
Studies with the palm supported find 25–30° of tilt relaxes the forearm
(Chen and Leung, 2007), and the Logitech MX Ergo, about 133 × 100 × 51 mm,
tilts 0° or 20°. Parts are printed on a hobby FDM printer (0.4 mm nozzle, PLA
or PETG) and must open again to swap a switch or fix a wire.

## Options considered

- Shape: a dome (simple, but it curls the palm), a symmetric mouse-like body,
  or a lopsided one like the MX Ergo: highest under the index knuckle, sloping
  down to the desk on the pinky side and at the back, so the hand rests half
  on its side, touching the shell and the desk at once.
- Body: a thin hollow shell (light, but its inside roof needs supports that
  are hard to remove), or a solid body with a cavity cut for each part (more
  plastic and print time, but stiff, and every cavity prints unsupported).
- Keys: standard keycaps standing above the shell (the hand lifts to reach
  them), or flush caps that are part of the shell surface, like mouse buttons.
- Switch mounting: cutouts in the curved shell (a flat 1.3 mm plate is hard
  to print on a curve), or a flat **key module** per switch, inside the shell.
- Holding the modules: screws into pillars in the shell (the thumb's would
  point sideways, where no screwdriver fits), or a post on the base that
  presses each module into its seat when the base goes on.
- Shell to base: self-tapping screws into plastic (wear on reopening), snap
  clips (hard to tune), or screws into heat-set inserts.
- Wedges: screws, magnets, or a printed dovetail.

## Decision

- **Shape**: horizontal slices are rounded rectangles at the front, where the
  four finger keys need room, and egg-shaped at the back. The crest sits under
  the index and middle knuckles; the thumb side drops steeply to the thumb
  key, and the pinky side slopes gently down and out over about 60 mm, like
  the MX Ergo, ending in a concave foot, so the palm lies across it and the
  hand's edge reaches the desk. The back slopes gently down too, so the heel
  rests on both. The pinky side is full enough that the pinky's module sits
  inside the base, whose bottom stays closed. The default body is
  102 × 138 × 46 mm above a 4.5 mm base, sized from the hand parameters.
- **Body**: solid, with cavities for the key modules, the Pico, the wires,
  the USB plug and the status LED. Their walls are vertical or 45° roofs, or
  short bridges, so the shell prints rim-down with supports only under the
  rounded heel ([0022](0022-rounded-heel-and-slanted-keys.md)).
- **Keys**: each key is a long cap cut from the shell surface, 0.5 mm
  proud at its edges and dished along its middle, with a 0.4 mm gap, hinged at its back end and resting on the stem of
  a Choc switch under the digit's pad
  ([0021](0021-long-hinged-caps-and-fanned-fingers.md)). The four finger
  keys fan out across the front and press along nearly one shared axis, so
  their modules fit side by side; the thumb key is on the side and presses
  straight sideways.
- **Key modules**: five flat parts, a 1.3 mm Choc plate with a floor
  that holds the hot-swap socket like a PCB. They are identical except the
  pinky's, whose lip has one corner trimmed where its cap's side reaches
  down; that corner sits under the cap's well and seats against nothing. Each slides into its own cavity
  from below until its plate's lip stops on a seat in the shell. When the
  base goes on, a printed post (fingers) or a block (thumb) presses each
  module against its seat; a rib on the thumb block also stops the thumb
  module dropping. No screws hold the modules.
- **Shell to base**: four M3 heat-set inserts in the shell and four
  M3 socket-head screws from below, their heads sunk in counterbores. A rim on the base, just inside the
  outline, fits a groove in the shell and guides it into place.
- **Pico**: at the back, under the palm, with four M2 screws into heat-set
  inserts in standoffs on the base. Its USB port faces the front; the plug
  sits in a channel between the middle and ring fingers' posts, and the
  cable runs on in a groove to the front edge. The cable is plugged in
  before the base goes on and stays captive, like a mouse's.
- **Status LED**: the 5 mm RGB LED of
  [0018](0018-rgb-indicator-led.md) pushes out through a hole just ahead of
  the thumb tip, between the thumb and index switches, so the resting thumb
  leaves it in view. Its tip sits just proud; its four leads run from a bay
  behind it down to the main cavity, where the resistor sits on the common
  wire, and on to the Pico.
- **Wedges** slide onto the base from the back on dovetail rails, without
  tools. They raise the thumb side, so the front cable exit stays level.

## Consequences

- Four M3 screws from below close the shell and hold all five modules at
  once; five M2 screws from above hold the caps.
- Every thread is metal, so the device opens and closes many times.
- Swapping the USB cable means opening the base, because the finger modules
  leave no room for a plug-sized passage to the front.
- Bought hardware: 9 M2 and 4 M3 heat-set inserts, 9 M2 × 4 mm socket-head
  screws (4 for the Pico, 5 for the caps), 4 M3 × 8 mm socket-head
  screws, an LED and its resistor; inserts need a soldering iron.
- The solid shell uses about 260 cm³ of filament before infill savings, and
  each module's fit against its post needs a test print (`post_gap`).
- Caps flush with the surface keep the hand in contact everywhere; each
  stops at 2.5 mm of travel, so light switches suit best.
