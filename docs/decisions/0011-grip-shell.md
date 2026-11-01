# 0011: MX Ergo-style grip shell with swappable tilt wedges

## Context

handful is held in one hand while the other stays on a Logitech MX Ergo
trackball. The user wants the same feel: the palm resting on a shell, the
thumb on the side and the fingers over the front, more like grabbing a
joystick than typing on a keyboard. The MX Ergo tilts 0° or 20° on a hinge,
and the Plus versions add a 10° wedge for up to 30° (Logitech). The user holds
handful in the left hand. A shell is handed: the thumb key, finger angles and
cable exit all sit on one side.

## Options considered

- Shape:
  - a flat keypad: simple, but the wrist lies flat and the fingers stretch;
  - a grip shell inspired by the MX Ergo: a relaxed, tilted hand with the keys
    under resting fingers.
- Handedness: left only, or left first and mirrorable for the right.
- Tilt:
  - a fixed angle: simple, but changing it means reprinting the shell;
  - a hinge plus a wedge, like the MX Ergo Plus: close to the original, but
    more moving parts to design;
  - swappable printed wedges: simple, any angle.

## Decision

We will build a 3D-printed grip shell inspired by the MX Ergo's posture and
designed from scratch for handful. It is shaped for the left hand first and
designed so that it can be mirrored for the right. The tilt comes from
swappable printed wedges under the shell, from 0° to 30° and beyond.

## Consequences

- The five MX-style switches sit in the shell at their own angles (see
  [0010](0010-mx-style-switches.md)).
- New tilt angles mean printing a new wedge, not a new shell.
- The CAD model needs a way to mirror the shell, which affects the choice of
  CAD tool.
- The shell must leave room for the Pico, the wiring and a USB cable exit.
