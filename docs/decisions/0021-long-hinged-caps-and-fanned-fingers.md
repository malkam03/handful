# 0021: Long hinged caps and fanned fingers

## Context

A printed test shell with fingertip-sized flush caps on a 19.05 mm pitch
showed five problems: the fingers sat too close together, the fingertip had
to find a small cap, the front dropped too steeply, the short thumb cap left
the thumb poorly placed, and the resting thumb covered the status LED.

What we found:

- A relaxed finger bends most at its middle joint (PIP), so a hand resting on
  a mouse lies along the whole finger, not only the tip
  ([0020](0020-hand-fitted-grip.md)). Mouse buttons reach from near the
  knuckle to the tip.
- Others make long buttons that bend: the Ploopy Nano 2's printed top has a
  "flexible moving button mechanism" over its switch, and Logitech's main
  buttons are cantilevers of the top shell (iFixit teardowns of the MX
  Master 3S and MX Ergo). Keyboards keep long keys level with wire
  stabilisers instead.
- Fingertips are about 16–20 mm wide. Neighbouring fingers spread at most
  about 17° (index–middle), 14–18° (middle–ring) and 28–32° (ring–pinky)
  (KoreaMed 2024; Medicine Science 2023). Ring–pinky opens widest. No survey
  reports a relaxed spacing.
- The MX Ergo holds four or five fingers in about 100 mm, and the test shell
  had unused room on the pinky side.

## Options considered

- Caps: fingertip caps (small targets); long caps on a steel-pin hinge
  (durable, but a pin and bearing per key); long caps resting only on the
  stem (they rock); or long caps with a printed flexure, as Ploopy does (one
  part each, but the strip's life must be tested).
- Spacing: a fixed 19.05 mm pitch (cramped); the measured spacings with the
  body growing to fit (about 150 mm across); or the fingers fanned into the
  body's own width.
- LED: behind the thumb (covered), top front between thumb and index, or
  just ahead of the thumb tip.

## Decision

We will give every key a long cap cut from the shell surface: from the
finger's middle joint to its tip (59.4 % of the finger), and for the thumb
its last segment plus half its first. The switch sits under the pad; the
cap's back end bends on a 0.8 mm flexure strip and a tab behind it screws to
an M2 insert in the shell. A pusher under the pad rests on the stem. A
stop pad under the fingertip end lands on the shell after 2.5 mm of stem
travel, past the 1.3 ± 0.3 mm actuation point and before the switch
bottoms out, so the cap swings less and keeps its full width over more of
its length. Caps
print on their side in PETG, so the strip's layers run along it.

The fingers fan out from their knuckles to `fingertip_spacing`, centre to
centre (31, 37 and 30 mm by default). Index to middle comes from the spread
angles above; on a printed grip the ring finger rests more comfortably nearer
the pinky, so ring to pinky is a little under index to middle, and middle to
ring takes the rest of the spread's total. The spacings are centred in the room the body has at the keys; where they add up
to more, they shrink in proportion and the body keeps its size. The front
follows a straighter ramp (`body_front_crown`). The body is 46 mm tall with low-profile switches
([0023](0023-choc-v2-low-profile-switches.md)), so each module stays above
the base under its sloped key.

The status LED sits 4.5 mm ahead of the thumb tip, between the thumb and
index switches, where the resting thumb leaves it in view.

A slice of the real shell round the middle key, its base slice and the middle
cap in 0.6, 0.8 and 1.0 mm strips print first, to tune the flexure.

## Consequences

- The whole finger rests on its key and presses anywhere along it.
- Each cap needs an M2 insert and screw: 9 of each in all, with the Pico's.
- The flexure's fatigue life in printed PETG is unknown; the hinge test
  answers it before the full shell prints. A steel-pin hinge is the fallback.
- Measured spacings wider than the body are scaled down; a hand that needs
  more must widen the body (`body_front_margin`, `hand_breadth`).
- The LED shares a narrow gap with the thumb and index modules; the tests
  check it clears both.
