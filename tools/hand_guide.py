"""Draw the hand measurement guide for the CAD build.

Usage: python3 tools/hand_guide.py [--docs docs]

Writes hand-measurements.svg in the same hand-drawn style as the chord
drawings: the cartoon left hand, palm up, with a letter on each measurement
that cad/hand.example.toml asks for. The drawing code lives in
tools/drawings/measure.py.
"""

import argparse
import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path[:0] = [TOOLS, os.path.join(ROOT, "firmware")]

from drawings.measure import render_measurements  # noqa: E402

NAME = "hand-measurements.svg"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--docs", default=os.path.join(ROOT, "docs"))
    args = parser.parse_args(argv)
    path = os.path.join(args.docs, NAME)
    with open(path, "w") as f:
        f.write(render_measurements())
    print("Wrote " + os.path.relpath(path))


if __name__ == "__main__":
    main()
