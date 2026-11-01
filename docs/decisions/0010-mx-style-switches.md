# 0010: MX-style switches, weighted per finger

## Context

The finished keypad is a grip shell shaped like the Logitech MX Ergo: about
51 mm deep, with the palm resting on it, the thumb on the side and the fingers
over the front. Each switch sits in its own hot-swap socket, hand-wired and
angled inside the 3D-printed shell (see [0007](0007-switches.md)). In a shell
that deep, switch height barely matters. What matters:

- the fingers rest on the keys all day;
- chords press several keys at once;
- each key needs a clear feel so you know it registered.

On weight, Gerard et al. (1999, *Human Factors*) found that a 0.83 N
(about 85 gf) keyboard caused the most muscle activity and discomfort. Most of
the typists preferred a 0.72 N keyboard with a clear click. No study we found
measures fingers resting on a grip.

## Options considered

- MX-style: the widest range of weights and feels, a standard cutout, many
  printable single-key mounts, common hot-swap sockets, the widest keycap
  choice and the lowest cost.
- Kailh Choc: low profile, which a deep shell doesn't need; fewer weights and
  pricier.
- Gateron low-profile: few switches and keycaps.

## Decision

We will use MX-style switches in Kailh MX hot-swap sockets, with a weight
chosen for each finger. The pinky is weaker and sits more upright on the
shell, so it gets a lighter switch than the index or middle. Weights are
picked by trying switches on the printed shell, avoiding heavy switches of
about 80 gf or more.

## Consequences

- The shell uses the standard MX cutout for each key.
- Weights can be tried and changed per finger without soldering.
- Switch testers or sampler packs are needed before buying a full set.
- Keycaps can be off-the-shelf MX or printed to fit each finger.
