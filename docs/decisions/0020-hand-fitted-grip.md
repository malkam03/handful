# 0020: A grip fitted to the user's own hand

## Context

The grip shell ([0011](0011-grip-shell.md)) places every key from hand
dimensions. A hand on a mouse-like shell rests best when each digit lies
along its cap and only presses, without reaching or curling. Hands differ:
in ANSUR II (Gordon et al. 2014, 6,068 adults) hand length runs from about
165 mm to over 205 mm, and finger and thumb lengths vary on top of that.
Measurements of someone's hand are personal and shouldn't be published.

We checked the shell against hand anatomy and relaxed-posture studies:

- Joint positions along a finger come from Buryanov & Kotiuk (2010, Int. J.
  Morphol. 28(3), tables I and III, X-rays of 66 adults): tip to the last
  joint is about 26 % of finger length, and the thumb's last segment,
  including the soft tissue of its tip, is about 27.3 mm.
- A relaxed finger bends most at its middle joint (about 27–31°) and only
  slightly at its last one (about 10–14°) (Lee, Mo, Hwang, Wang & Jung,
  "Relaxed hand postures", Ajou University, 2014; Garrett 1971, Human
  Factors 13(2)). Placing a medium middle finger on the shell's
  front in the CAD gives 17° and 28°: the fingertip curls down the front.
- Mouse buttons that the hand simply rests on (Logitech MX Ergo, Evoluent
  VerticalMouse, Ploopy) are long, reaching from near the knuckle to the tip.
- A light make force, at most about 0.47 N, lowers fingertip force and
  flexor activity (Rempel et al. 1997, Ergonomics 40(8)).

## Options considered

- One medium hand for everyone: simplest, but fits only hands near the
  average. Hands more than about 6 % from it don't build.
- Small, medium and large presets: still a guess for any one hand.
- The user's own measurements, with medium-hand defaults for anything left
  out: fits each hand and needs only a tape measure.

## Decision

We will build the shell from the user's own measurements when they give
them. `cad/hand.example.toml` lists twelve measurements, A to L, drawn in
`docs/hand-measurements.svg`: hand length, palm length, hand breadth, each
finger's length, how far each knuckle crease sits behind the middle finger's,
the thumb's reach from the wrist crease and the length of its last segment.
Each is optional; the defaults are a medium adult hand, the midpoint of the
ANSUR II male and female means. The user copies the file to
`hand.local.toml`, which git ignores, so their numbers stay on their
computer.

The thumb gets the same treatment as the fingers: its cap runs the length
of its last segment and ends under its tip, and the thumb's reach places it.

## Consequences

- Each person prints a shell that fits their hand, and the tests can run
  against it with `HANDFUL_PARAMS`.
- The committed previews and tests use the medium hand only; a fitted hand
  is checked on the user's computer.
- Hands far from the medium one need the fixed-size parts (key modules,
  base, Pico bay) to be checked; the tests report any collision.
- The finger angle analysis leads to the straighter front and the long
  caps of [0021](0021-long-hinged-caps-and-fanned-fingers.md).
