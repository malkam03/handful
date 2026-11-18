"""The parts the tests check, built once and kept on disk as BREP files.

Each part is filed under a hash of the CAD source and the parameters, so a
change to either builds it again. ``prebuild`` builds the missing parts on
every core at once; pytest calls it before its workers start (conftest.py),
and they then load the files instead of each building its own copies.
"""

import hashlib
import os
import shutil
from collections.abc import Mapping
from concurrent.futures import ProcessPoolExecutor
from functools import cache
from pathlib import Path

from build123d import export_brep, import_brep

from handful_cad import parts
from handful_cad.geometry import key_poses
from handful_cad.hand import load
from handful_cad.params import DEFAULT, Params

HANDS = ("left", "right")
BASE = DEFAULT.with_(**load(os.environ["HANDFUL_PARAMS"])) if os.environ.get("HANDFUL_PARAMS") else DEFAULT
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "build" / "test-cache"
SLOW_FIRST = ("hinge_test", "shell", "hinge_test_base", "base")  # start the longest builds first


def _source_digest() -> str:
    digest = hashlib.sha256()
    for path in sorted((ROOT / "handful_cad").glob("*.py")):
        digest.update(path.name.encode() + path.read_bytes())
    return digest.hexdigest()[:16]


SOURCE = _source_digest()


def _builders(params: Params) -> dict:
    """Every cached part by name: the printable parts, then each cap in place and its moving paddle."""
    names = [pose.name for pose in key_poses(params)]
    result = {
        "shell": lambda: parts.shell(params),
        "base": lambda: parts.base(params),
        "key_module": lambda: parts.key_module(params),
        "tactile_adapter": lambda: parts.tactile_adapter(params),
    }
    for name in params.own_module_keys:
        result[f"key_module_{name}"] = lambda name=name: parts.module_for(params, name)
    for name in names:
        result[f"cap_{name}"] = lambda name=name: parts.cap_print(params, name)
    for angle in params.wedge_angles:
        result[f"wedge_{angle:02d}"] = lambda angle=angle: parts.wedge(params, angle)
    result["hinge_test"] = lambda: parts.hinge_test(params)
    result["hinge_test_base"] = lambda: parts.hinge_test_base(params)
    result["insert_test"] = lambda: parts.insert_test(params)
    result["insert_test_plate"] = lambda: parts.insert_test_plate(params)
    for name in names:
        result[f"placed_{name}"] = lambda name=name: parts.cap(params, name)
        result[f"moving_{name}"] = lambda name=name: parts.cap(params, name, moving=True)
    return result


def _path(hand: str, name: str) -> Path:
    params = hashlib.sha256(repr(BASE.with_(hand=hand)).encode()).hexdigest()[:16]
    return CACHE / SOURCE / params / hand / f"{name}.brep"


def _build(hand: str, name: str) -> None:
    path = _path(hand, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    part = _builders(BASE.with_(hand=hand))[name]()
    partial = path.with_suffix(f".{os.getpid()}.tmp")
    export_brep(part, partial)
    partial.replace(path)  # a reader never sees half a file


@cache
def part(hand: str, name: str):
    """The named part for ``hand``, built if no run has built it yet."""
    path = _path(hand, name)
    if not path.exists():
        _build(hand, name)
    return import_brep(path)


class Built(Mapping):
    """The printable parts for one hand by name, loaded as the tests ask for them."""

    def __init__(self, hand: str):
        self.hand = hand
        self.names = [n for n in _builders(BASE) if not n.startswith(("placed_", "moving_"))]

    def __getitem__(self, name: str):
        if name not in self.names:
            raise KeyError(name)
        return part(self.hand, name)

    def __iter__(self):
        return iter(self.names)

    def __len__(self) -> int:
        return len(self.names)


@cache
def built(hand: str) -> Built:
    return Built(hand)


@cache
def caps(hand: str, moving: bool = False) -> dict:
    """The five caps in place by key name; ``moving``: their paddles and pushers only."""
    kind = "moving" if moving else "placed"
    return {pose.name: part(hand, f"{kind}_{pose.name}") for pose in key_poses(BASE)}


def prebuild() -> None:
    """Build every missing part for both hands, one per core, and drop caches of other source versions."""
    if CACHE.exists():
        for stale in CACHE.iterdir():
            if stale.name != SOURCE:
                shutil.rmtree(stale, ignore_errors=True)
    names = sorted(_builders(BASE), key=lambda n: SLOW_FIRST.index(n) if n in SLOW_FIRST else len(SLOW_FIRST))
    todo = [(hand, name) for name in names for hand in HANDS if not _path(hand, name).exists()]
    if not todo:
        return
    with ProcessPoolExecutor(max_workers=min(len(todo), os.cpu_count() or 1)) as pool:
        for future in [pool.submit(_build, hand, name) for hand, name in todo]:
            future.result()
