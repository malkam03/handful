"""Copy the handful firmware to a CIRCUITPY drive.

Usage: python3 tools/deploy.py [--drive /Volumes/CIRCUITPY] [--mappings]

Copies code.py and handful/, removes files on the drive that the firmware no
longer has, and copies mappings.py only when the drive has none (or with
--mappings, which replaces it). Nothing is downloaded: the firmware uses only
modules built into CircuitPython.
"""

import argparse
import os
import shutil
import sys

FIRMWARE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "firmware")
# Libraries earlier firmware versions installed, which the current one doesn't use.
UNUSED_LIBS = ("adafruit_hid",)


def copy_package(drive):
    source = os.path.join(FIRMWARE, "handful")
    target = os.path.join(drive, "handful")
    os.makedirs(target, exist_ok=True)
    wanted = sorted(name for name in os.listdir(source) if name.endswith(".py"))
    for name in sorted(os.listdir(target)):
        path = os.path.join(target, name)
        stale = name not in wanted and not name.startswith("._") and name.endswith((".py", ".mpy"))
        if stale and os.path.isfile(path):
            os.remove(path)
            print("Removed handful/" + name)
    for name in wanted:
        shutil.copyfile(os.path.join(source, name), os.path.join(target, name))
        print("Copied handful/" + name)


def _ignore_missing(function, path, exc_info):
    # macOS "._name" files on the FAT drive vanish together with "name".
    if not issubclass(exc_info[0], FileNotFoundError):
        raise exc_info[1]


def remove_unused_libs(drive):
    for name in UNUSED_LIBS:
        path = os.path.join(drive, "lib", name)
        if os.path.isdir(path):
            shutil.rmtree(path, onerror=_ignore_missing)
            print("Removed lib/" + name)


def deploy(drive, replace_mappings=False):
    if not os.path.isfile(os.path.join(drive, "boot_out.txt")):
        sys.exit("No CircuitPython drive at {}".format(drive))
    remove_unused_libs(drive)
    copy_package(drive)

    mappings = os.path.join(drive, "mappings.py")
    if replace_mappings or not os.path.exists(mappings):
        shutil.copyfile(os.path.join(FIRMWARE, "mappings.py"), mappings)
        print("Copied mappings.py")
    else:
        print("Kept the existing mappings.py (use --mappings to replace it)")

    # code.py goes last, so the Pico restarts once everything else is in place.
    shutil.copyfile(os.path.join(FIRMWARE, "code.py"), os.path.join(drive, "code.py"))
    print("Copied code.py")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--drive", default="/Volumes/CIRCUITPY")
    parser.add_argument("--mappings", action="store_true", help="replace mappings.py on the drive")
    args = parser.parse_args(argv)
    deploy(args.drive, args.mappings)


if __name__ == "__main__":
    main()
