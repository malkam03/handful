# 0023: Kailh Choc v2 low-profile switches, weighted per finger

Replaces: ADR-0010 (removed; see git history)

## Context

On the 20° wedge the printed grip held the fingers up while the wrist rested
on the desk, which strained the hand. The hand is most relaxed when its outer
edge lies along the desk from the wrist to the pinky knuckle. That means a
lower shell, above all on the pinky side.

What sets the height is each key's stack along its press axis: cap, switch,
hot-swap socket and module floor. The keys slope down the front, and every
stack must stay above the base. An MX switch in a Kailh MX socket needs about
23 mm. The pinky's module is the lowest, so it set the body height at 50 mm.

The keys are long caps resting on the fingers all day, and chords press
several keys at once. Gerard et al. (1999, *Human Factors*) found that a
0.83 N (about 85 gf) keyboard caused the most muscle activity and discomfort,
and most typists preferred a 0.72 N keyboard with a clear click.

## Options considered

- Keep MX switches: the most weights and the lowest cost, but the shell can't
  get any lower.
- Kailh Choc v2 on the pinky only: lowers the pinky side, but needs two switch
  families, two socket types and two module designs.
- Kailh Choc v2 on every key: a stack about 15 mm deep, roughly 8 mm shorter, an MX-style cross
  stem and the same pin pattern as Choc v1. It comes in fewer weights and
  costs more.
- Gateron low-profile: few switches and sockets to choose from.

## Decision

We will use Kailh Choc v2 switches (drawing PG135301D03) in Kailh Choc
hot-swap sockets (CPG135001S30) on all five keys, hand-wired, with no PCB.
Each key module has a 1.3 mm Choc plate. The socket's floor ledge stays open
at the solder-tab side, which keeps the module short.

The body is 46 mm tall above the base. Lowering it further pushes the pinky's
module through the 0.6 mm floor left in the base under its pocket. The heel
rounding (see [0022](0022-rounded-heel-and-slanted-keys.md)) starts 17 mm in
from the pinky edge at the front, as far as it can before reaching the pinky's
module.

Each finger gets its own switch weight. The pinky is the weakest and gets the
lightest. The weights are picked by trying switches on the printed shell, and
anything heavy, about 80 gf or more, is avoided.

## Consequences

- The knuckles sit several millimetres lower on every wedge, most on the
  pinky side.
- Each cap's stop pad lands on the shell after 2.5 mm of stem travel, past
  the 1.3 ± 0.3 mm actuation point and before the switch bottoms out.
- Choc v2 takes MX-style keycaps, but handful uses its own printed caps, so
  only the stem shape matters.
- Fewer weights are on offer, and the switches cost more than MX. Weights can
  still be tried and changed per finger without soldering.
- In the tactile adapter, the 12 × 12 mm test buttons sit partly below the
  plate, so their legs are cut to 1 mm.
