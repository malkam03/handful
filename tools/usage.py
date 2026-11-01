"""Show how often each handful chord is used, to see which ones deserve the easiest spots.

Usage: python3 tools/usage.py [--port /dev/cu.usbmodem...] [--mappings PATH] [--reset]

Asks the Pico over its serial console for the chord counts and prints them
ranked, with the mapped chords that were never used and the unmapped chords
that were pressed anyway. --reset prints the counts, then clears them.

The Pico counts only while COUNT_CHORDS = True in its mappings.py. Close any
other serial console first; only one program can hold the port.
"""

import argparse
import os
import sys
import time

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path[:0] = [TOOLS, os.path.join(ROOT, "firmware")]

from drawings.layout import action_names, load_mappings  # noqa: E402
from handful import config  # noqa: E402

DRIVE_MAPPINGS = "/Volumes/CIRCUITPY/mappings.py"
CIRCUITPYTHON_VID = 0x239A
TIMEOUT_S = 3.0


class UsageError(Exception):
    pass


def find_port(comports):
    """The serial port of the one CircuitPython board plugged in."""
    ports = sorted(p.device for p in comports if p.vid == CIRCUITPYTHON_VID)
    if len(ports) == 1:
        return ports[0]
    if not ports:
        raise UsageError("No CircuitPython board found. Plug in handful, or pass --port.")
    raise UsageError("Several CircuitPython boards found ({}); pick one with --port.".format(", ".join(ports)))


def ask(port, command, clock=time.monotonic):
    """Send a command to the Pico and return its "usage" reply lines, up to "usage end"."""
    port.reset_input_buffer()
    port.write(("\r\n" + command + "\r\n").encode())
    lines = []
    deadline = clock() + TIMEOUT_S
    while clock() < deadline:
        line = port.readline().decode("utf-8", "replace").strip()
        if line.startswith("usage "):
            lines.append(line)
            if line == "usage end":
                return lines
    raise UsageError(
        "No answer from handful. Check that its firmware is running (Ctrl-D in a serial console "
        "restarts it) and that no other program has the port open.")


def parse(lines):
    """Turn reply lines into (counting, {chord: (taps, holds)})."""
    counting = False
    counts = {}
    for line in lines:
        words = line.split()
        if words[1] == "counting":
            counting = words[2] == "on"
        elif len(words) == 4:
            counts[config.parse_chord(words[1])] = (int(words[2]), int(words[3]))
    return counting, counts


def chord_names(mappings_path):
    """{chord: action name} for every mapped chord, the mode chord included."""
    module, source, comments = load_mappings(mappings_path)
    settings = config.load(module)
    names = {}
    for set_name in ("WINDOWS", "MACOS"):
        for chord in settings.sets[set_name.lower()]:
            names[chord] = config.chord_name(chord)
        names.update(action_names(source, comments, set_name))
    names[settings.mode_chord] = "switch mode"
    return names


def report(counting, counts, names):
    out = []
    total = sum(taps + holds for taps, holds in counts.values())
    out.append("Chord counts: {} presses, counting is {}.".format(total, "on" if counting else "off"))
    if not counting:
        out.append("Set COUNT_CHORDS = True in mappings.py on the CIRCUITPY drive to count.")

    used = sorted(counts.items(), key=lambda item: (-sum(item[1]), item[0]))
    mapped = [(chord, c) for chord, c in used if chord in names]
    if mapped:
        out.append("")
        out.append("{:>3}  {:<10} {:>7}  {:<26} {:>6} {:>6} {:>6} {:>6}".format(
            "#", "chord", "fingers", "action", "taps", "holds", "total", "share"))
        for rank, (chord, (taps, holds)) in enumerate(mapped, start=1):
            out.append("{:>3}  {:<10} {:>7}  {:<26} {:>6} {:>6} {:>6} {:>5.1f}%".format(
                rank, config.chord_name(chord), bin(chord).count("1"), names[chord][:26],
                taps, holds, taps + holds, 100.0 * (taps + holds) / total))

    never = sorted((c for c in names if c not in counts), key=lambda c: (bin(c).count("1"), c))
    if never and total:
        out.append("")
        out.append("Mapped, not used yet:")
        for chord in never:
            out.append("     {:<10} {}".format(config.chord_name(chord), names[chord]))

    unmapped = [(chord, c) for chord, c in used if chord not in names]
    if unmapped:
        out.append("")
        out.append("Not mapped, pressed anyway (cancels or slips):")
        for chord, (taps, holds) in unmapped:
            out.append("     {:<10} {} taps, {} holds".format(config.chord_name(chord), taps, holds))
    return "\n".join(out)


def open_port(device):
    import serial

    return serial.Serial(device, 115200, timeout=0.2)


def list_ports():
    from serial.tools import list_ports

    return list_ports.comports()


def main(argv=None, open_port=open_port, list_ports=list_ports):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", help="serial port; found automatically when one CircuitPython board is plugged in")
    default_mappings = DRIVE_MAPPINGS if os.path.isfile(DRIVE_MAPPINGS) else os.path.join(
        ROOT, "firmware", "mappings.py")
    parser.add_argument("--mappings", default=default_mappings, help="mappings.py used for action names")
    parser.add_argument("--reset", action="store_true", help="clear the counts after printing them")
    args = parser.parse_args(argv)
    try:
        port = open_port(args.port or find_port(list_ports()))
        try:
            counting, counts = parse(ask(port, "usage"))
            print(report(counting, counts, chord_names(args.mappings)))
            if args.reset:
                ask(port, "usage reset")
                print("")
                print("Counts cleared. A fresh round starts now.")
        finally:
            port.close()
    except UsageError as error:
        sys.exit(str(error))


if __name__ == "__main__":
    main()
