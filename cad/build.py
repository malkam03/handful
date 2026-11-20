"""Builds every handful grip part and writes STEP, STL and PNG files.

Usage (from the cad/ directory, with the CAD environment active):
    python build.py                 # left hand, into build/left/
    python build.py --hand both     # left and right
    python build.py --no-renders    # STEP and STL only
    python build.py --params hand.local.toml  # your own measurements
    python build.py --no-cache      # build every part afresh

The slow parts are kept in build/cache/ (handful_cad.store), shared with the
tests, so a part built once for the same source and parameters loads from
its file.

A left-hand build with renders also refreshes the committed previews in
previews/, which the READMEs show. A build with --params never does, so
personal measurements stay in the ignored build/ folder.
"""

import argparse
import os
import shutil
import time
from pathlib import Path

from build123d import Compound, Pos, export_step, export_stl
from OCP.BRepTools import BRepTools

from handful_cad import hand as hand_file
from handful_cad import parts, store
from handful_cad.params import DEFAULT, Params
from handful_cad.render import render

HERE = Path(__file__).resolve().parent
PREVIEWS = ("assembly", "assembly_side", "assembly_20deg", "exploded", "inside", "caps")


def printable_parts(params: Params) -> dict:
    result = {
        "shell": parts.shell(params),
        "base": parts.base(params),
        "key_module": parts.key_module_print(params),
        "tactile_adapter": parts.tactile_adapter_print(params),
    }
    for name in params.own_module_keys:
        result[f"key_module_{name}"] = parts.key_module_print(params, name)
    for pose in parts.poses(params):
        result[f"cap_{pose.name}"] = parts.cap_print(params, pose.name)
    for angle in params.wedge_angles:
        result[f"wedge_{angle:02d}"] = parts.wedge(params, angle)
    result["hinge_test"] = parts.hinge_test(params)
    result["hinge_test_base"] = parts.hinge_test_base(params)
    result["insert_test"] = parts.insert_test(params)
    result["insert_test_plate"] = parts.insert_test_plate(params)
    for thickness in params.hinge_test_flexures:
        cap = parts.cap_print(params.with_(flexure_thickness=thickness), parts.HINGE_TEST_KEY)
        result[f"hinge_test_cap_{thickness:.1f}mm".replace(".", "_")] = cap
    return result


def export(name: str, part, folder: Path) -> None:
    BRepTools.Clean_s(part.wrapped)
    export_step(part, str(folder / f"{name}.step"))
    linear, angular = parts.STL_TOLERANCE
    if not export_stl(part, str(folder / f"{name}.stl"), tolerance=linear, angular_tolerance=angular):
        raise RuntimeError(f"STL export failed for {name}")


def build(hand: str, out: Path, renders: bool, overrides: dict | None = None) -> None:
    params = DEFAULT.with_(hand=hand, **(overrides or {}))
    folder = out / hand
    folder.mkdir(parents=True, exist_ok=True)
    built = printable_parts(params)
    for name, part in built.items():
        export(name, part, folder)
        print(f"  {name}: {part.volume / 1000:.1f} cm3")

    for angle in (0, 20):
        items = parts.assembly(params, angle, extras=False)
        export_step(Compound([p for _, p, _ in items], label=f"handful_{hand}_{angle}"),
                    str(folder / f"assembly_{angle:02d}.step"))

    if not renders:
        return
    pics = folder / "renders"
    module = parts.key_module(params)
    render(parts.assembly(params, 0), pics / "assembly.png", f"{hand} hand, flat", view=(25, 40))
    render(parts.assembly(params, 0), pics / "assembly_front.png", f"{hand} hand, from the front", view=(12, 90))
    side = 0 if hand == "left" else 180
    render(parts.assembly(params, 0), pics / "assembly_side.png", f"{hand} hand, thumb side", view=(10, side))
    render(parts.assembly(params, 20), pics / "assembly_20deg.png", f"{hand} hand on the 20 deg wedge", view=(8, 90))
    render(parts.assembly(params, 0, explode=45), pics / "exploded.png", f"{hand} hand, exploded", view=(20, 40))
    inside = [item for item in parts.assembly(params, 0) if item[0] not in ("wedge", "base")]
    render(inside, pics / "inside.png", "from below, base hidden", view=(-55, 40))
    colours = parts.COLOURS
    render([("shell", built["shell"], colours["shell"])], pics / "shell.png", "shell", view=(30, 40))
    render([("base", built["base"], colours["base"])], pics / "base.png", "base", view=(40, -60))
    render([("base", built["base"], colours["base"])], pics / "base_bottom.png", "base, underside", view=(-40, -60))
    render([("module", module, colours["key_module"])], pics / "key_module.png",
           "key module, plate up", view=(35, -50))
    render([("module", module, colours["key_module"])], pics / "key_module_bottom.png",
           "key module, socket side", view=(-45, -50))
    names = [p.name for p in parts.poses(params)]
    laid = [(n, Pos(i * 30, 0, 0) * built[f"cap_{n}"], colours["cap"]) for i, n in enumerate(names)]
    render(laid, pics / "caps.png", "caps, as printed: " + ", ".join(names), view=(35, -70), size=(11, 6))
    wedges = []
    for i, angle in enumerate(params.wedge_angles):
        wedges.append((f"wedge {angle}", Pos(i * 130, 0, 0) * built[f"wedge_{angle:02d}"], colours["wedge"]))
    render(wedges, pics / "wedges.png", "wedges: " + ", ".join(f"{a} deg" for a in params.wedge_angles),
           view=(20, -75), size=(11, 6))
    if hand == "left" and not overrides:
        (HERE / "previews").mkdir(exist_ok=True)
        for name in PREVIEWS:
            shutil.copy(pics / f"{name}.png", HERE / "previews" / f"{name}.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--hand", choices=("left", "right", "both"), default="left")
    parser.add_argument("--out", type=Path, default=HERE / "build")
    parser.add_argument("--no-renders", action="store_true", help="skip the PNG previews")
    parser.add_argument("--params", type=Path, help="your hand measurements, e.g. hand.local.toml")
    parser.add_argument("--no-cache", action="store_true", help="build every part afresh, ignoring build/cache/")
    args = parser.parse_args()
    if args.no_cache:
        os.environ["HANDFUL_CACHE"] = "0"
    store.prune()
    try:
        overrides = hand_file.load(args.params) if args.params else None
    except (OSError, ValueError) as error:
        raise SystemExit(error) from None
    hands = ("left", "right") if args.hand == "both" else (args.hand,)
    for hand in hands:
        start = time.time()
        print(f"{hand} hand:")
        build(hand, args.out, not args.no_renders, overrides)
        print(f"  written to {args.out / hand} in {time.time() - start:.0f} s")


if __name__ == "__main__":
    main()
