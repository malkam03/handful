"""Draw the handful chords from mappings.py.

Usage: python3 tools/cheatsheet.py [--mappings firmware/mappings.py] [--docs docs]

Writes two drawings in the same hand-drawn style:
- cheatsheet.svg, a printable A4 landscape sheet that also fits on Letter;
- chords.svg, a wide banner for the README.

Each chord is drawn as five dots laid out like the fingertips of a left hand
seen from above, filled in the finger's colour when that button is part of
the chord. Action names come from the comment at the end of each line in
mappings.py. The drawing code lives in tools/drawings/.
"""

import argparse
import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path[:0] = [TOOLS, os.path.join(ROOT, "firmware")]

from drawings.banner import render_banner  # noqa: E402
from drawings.sheet import render  # noqa: E402

DRAWINGS = (("cheatsheet.svg", render), ("chords.svg", render_banner))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mappings", default=os.path.join(ROOT, "firmware", "mappings.py"))
    parser.add_argument("--docs", default=os.path.join(ROOT, "docs"))
    args = parser.parse_args(argv)
    for name, draw in DRAWINGS:
        path = os.path.join(args.docs, name)
        with open(path, "w") as f:
            f.write(draw(args.mappings))
        print("Wrote " + os.path.relpath(path))


if __name__ == "__main__":
    main()
