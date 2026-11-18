# 0016: build123d for the grip shell CAD

## Context

The grip shell ([0011](0011-grip-shell.md)) needs a CAD model that mirrors
for the right hand, scales to the user's hand and makes a new tilt wedge from
one number. It should live in this repository as reviewable text, build the
same way on any computer and in CI, and be easy for agents to change. The
repository only takes permissively licensed dependencies.

## Options considered

- **OpenSCAD**: text-based and widely used, but GPL-2.0, which the repository
  does not take, and its mesh kernel makes fillets and STEP export hard.
- **CadQuery**: Python on the OpenCASCADE kernel, Apache-2.0; a fluent
  chained API that is harder to read once a part grows.
- **build123d**: Python on the same kernel, Apache-2.0; plain Python objects
  and operators (`+`, `-`, `&`, `mirror`), STEP and STL export built in.
- **FreeCAD**: a full GUI, LGPL-2.1; models are binary files that are hard to
  review and to build headless.
- **Onshape or Fusion**: capable, but proprietary and cloud-hosted, so the
  model would not live in the repository.

## Decision

We will model the shell in build123d 0.13.0, in the `cad/` directory, as
parametric Python scripts that export STEP and STL for every part. The
licences were checked on PyPI and in the OpenCASCADE repository:

- build123d 0.13.0 and cadquery-ocp (its OpenCASCADE bindings) are Apache-2.0;
- OpenCASCADE Technology itself is LGPL-2.1 with the Open CASCADE exception
  version 1.0 (`LICENSE_LGPL_21.txt` and `OCCT_LGPL_EXCEPTION.txt` in the
  OCCT repository).

OpenCASCADE is a design-time tool here: pip installs it into a separate
environment, this repository does not redistribute it, our MIT scripts only
call it, and the STL and STEP files it writes are ours. Nothing from it ships
in the firmware or on the Pico. AGENTS.md allows exactly this case.

## Consequences

- Every dimension is a named parameter in `cad/handful_cad/params.py`, with
  its source; a right-hand shell or a new wedge angle is one setting.
- Tests build each part and check that it is a closed solid and that the
  parts fit together, so a change that breaks the fit fails CI.
- The CAD tools need their own environment (`cad/requirements.txt`, about
  750 MB) and do not touch the firmware tooling.
- Generated STL and STEP files are rebuilt from the scripts and not
  committed, so they never drift from the source. A few preview PNGs in
  `cad/previews/` are committed so the design shows on GitHub; a left-hand
  build refreshes them.
