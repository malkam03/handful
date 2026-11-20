"""The parts the tests check, built once and kept on disk by ``handful_cad.store``.

The slow parts are ``@stored``, so they're filed under a digest of the CAD
source and their parameters, and shared with ``build.py``. ``prebuild`` builds
the missing ones on every core at once; pytest calls it before its workers
start (conftest.py), and they then load the files instead of each building
its own copies.
"""

import os
from collections.abc import Mapping
from concurrent.futures import ProcessPoolExecutor
from functools import cache

from handful_cad import parts, store
from handful_cad.geometry import key_poses
from handful_cad.hand import load
from handful_cad.params import DEFAULT, Params

HANDS = ("left", "right")
BASE = DEFAULT.with_(**load(os.environ["HANDFUL_PARAMS"])) if os.environ.get("HANDFUL_PARAMS") else DEFAULT
SLOW_FIRST = ("hinge_test", "shell", "hinge_test_base", "base")  # start the longest builds first


def _builders(params: Params) -> dict:
    """Every part the tests use by name, as (function, arguments): the printable
    parts, then each cap in place and its moving paddle."""
    names = [pose.name for pose in key_poses(params)]
    result = {
        "shell": (parts.shell, (params,)),
        "base": (parts.base, (params,)),
        "key_module": (parts.key_module, (params,)),
        "tactile_adapter": (parts.tactile_adapter, (params,)),
    }
    for name in params.own_module_keys:
        result[f"key_module_{name}"] = (parts.module_for, (params, name))
    for name in names:
        result[f"cap_{name}"] = (parts.cap_print, (params, name))
    for angle in params.wedge_angles:
        result[f"wedge_{angle:02d}"] = (parts.wedge, (params, angle))
    result["hinge_test"] = (parts.hinge_test, (params,))
    result["hinge_test_base"] = (parts.hinge_test_base, (params,))
    result["insert_test"] = (parts.insert_test, (params,))
    result["insert_test_plate"] = (parts.insert_test_plate, (params,))
    for name in names:
        result[f"placed_{name}"] = (parts.cap, (params, name, False))
        result[f"moving_{name}"] = (parts.cap, (params, name, True))
    return result


def _build(hand: str, name: str) -> None:
    func, args = _builders(BASE.with_(hand=hand))[name]
    func(*args)


def _missing(hand: str, name: str) -> bool:
    func, args = _builders(BASE.with_(hand=hand))[name]
    return hasattr(func, "is_stored") and not func.is_stored(*args)


@cache
def part(hand: str, name: str):
    """The named part for ``hand``, loaded from the store or built."""
    func, args = _builders(BASE.with_(hand=hand))[name]
    return func(*args)


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
    """Build every missing stored part for both hands, one per core, and drop files of other source versions."""
    store.prune()
    names = sorted(_builders(BASE), key=lambda n: SLOW_FIRST.index(n) if n in SLOW_FIRST else len(SLOW_FIRST))
    todo = [(hand, name) for name in names for hand in HANDS if _missing(hand, name)]
    if not todo or not store.enabled():
        return
    with ProcessPoolExecutor(max_workers=min(len(todo), os.cpu_count() or 1)) as pool:
        for future in [pool.submit(_build, hand, name) for hand, name in todo]:
            future.result()
