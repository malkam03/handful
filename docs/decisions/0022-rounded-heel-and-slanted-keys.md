# 0022: Rounded heel and slanted keys

## Context

On the 20° wedge, the printed shell held the hand in the air: the wedge
lifted the whole base, so the wrist and the pinky side of the palm floated
above the desk and the arm held them up. On an MX Ergo the same corner of the
hand rests on the desk. Its underside starts well in from the pinky edge and
the shell curves down to meet the desk.

The four finger keys use the whole front, so moving the fingertips towards
the pinky makes the key modules collide. The hand can still turn about its
fingertips: the tips stay on their keys and the rest of the hand swings
towards the pinky, onto the desk.

## Options considered

- Widen the pinky side into a lip or step: more surface, but tilting it lifts
  the hand higher.
- Lower the whole shell: less room for the key modules and the Pico.
- Round off the pinky-and-wrist corner so it rolls onto the desk at the chosen
  tilt, with the base and wedges starting further in.
- Move the fingertips towards the pinky: the modules collide.
- Turn each key about its fingertip, so the palm end swings towards the pinky.

## Decision

We will round the corner under the wrist and the pinky side of the palm. Seen
from the front, the underside leaves the desk along a curve of
`heel_radius` (25 mm) that rises to `heel_angle` (20°), the steepest wedge,
then runs straight. The curve runs from `heel_back` (40 mm in from the pinky
edge at the back) to `heel_front` (17 mm in at the front, as far as it goes
before it reaches the pinky's module). The base and the
wedges stop where the curve begins. On every wedge up to `heel_angle` the curve
rests on the desk, so the wrist does too.

We will turn each finger key and its switch 10° about its fingertip
(`cap_slant`), so the palm end swings towards the pinky. The thumb follows the
turning hand: its tip moves 8 mm back (`thumb_back`) and its cap turns 10°
about the tip, palm end up (`thumb_cap_tilt`). The thumb module stays level. Its
tab sits where the side curves over into the top, so its M2 screw and
insert move 3 mm down the side and 1.5 mm towards the hinge
(`thumb_screw_shift`) and stay in full-thickness tab.

The default wedges are 0°, 10° and 20°.

## Consequences

- The wrist and the pinky side of the hand rest on the desk on every default
  wedge.
- On a wedge steeper than `heel_angle`, the heel stays 0.5 mm above the desk
  instead (`heel_clearance`). A steeper tilt needs a larger `heel_angle`,
  which narrows the base.
- The curved underside of the shell and the base needs supports from the
  build plate.
- A rigid hand would turn the thumb cap about 18°. Past 12°, the screw tab
  behind the thumb's hinge reaches the thin top of the shell, so the tilt
  stops at 10° until a print shows whether more is needed.
- The finger switches move 2–3 mm as they turn; the tests check the modules
  still clear each other, the base and the cavities.
