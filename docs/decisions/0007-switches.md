# 0007: Tactile buttons for the prototype, hand-wired hot-swap for the build

## Context

handful's five buttons are pressed all day, often resting under the fingers,
in a shape like an ergonomic mouse. The user already has 12 × 12 mm tactile
push buttons with a square yellow actuator and wants a working prototype
before choosing final parts. The firmware treats every switch the same way.
Mechanical switches can be made swappable without soldering by using hot-swap
sockets, and each socket type fits one switch family.

## Options considered

- 12 × 12 mm tactile push buttons: cheap, already on hand and fit a
  breadboard, but stiff with short travel, so they tire fingers over a day.
- Mechanical switches in hot-swap sockets, mounted on:
  - one custom PCB: neat, but a flat, fixed layout;
  - per-key PCBs: free angles, extra parts;
  - a 3D-printed plate, hand-wired: no PCB, free placement, fiddly
    soldering.

## Decision

We will build the prototype with the 12 × 12 mm tactile push buttons on a
breadboard. The finished keypad will use mechanical switches in hot-swap
sockets that sit in a 3D-printed plate and are hand-wired to the Pico, with no
PCB.

## Consequences

- The prototype can be built now with parts on hand.
- Moving to mechanical switches changes the hardware only, not the firmware.
- Switches can be swapped without soldering; the sockets are soldered to
  wires once.
- Each key can be placed and angled freely in the plate.
- The plate's holes depend on the switch family; see
  [0023](0023-choc-v2-low-profile-switches.md).
