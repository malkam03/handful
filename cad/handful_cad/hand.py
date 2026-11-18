"""Turns a user's own hand measurements into shell parameters.

Every measurement is optional: leave one out and the default in
``params.py`` stands. Lengths are in millimetres, with the hand flat and
palm up.
"""

from dataclasses import dataclass, fields
from pathlib import Path

import tomllib

from handful_cad.params import DEFAULT, Params

MIDDLE_SLACK = 3.0  # mm the hand, palm and middle-finger lengths may disagree by
OFFSETS = {"index_knuckle_back", "ring_knuckle_back", "pinky_knuckle_back"}  # may be zero or negative


@dataclass(frozen=True)
class Hand:
    hand_length: float | None = None  # wrist crease to the middle fingertip
    palm_length: float | None = None  # wrist crease to the middle finger's base crease
    hand_breadth: float | None = None  # across the four knuckles, without the thumb
    # Base crease to fingertip.
    index_length: float | None = None
    middle_length: float | None = None
    ring_length: float | None = None
    pinky_length: float | None = None
    # How far the base crease sits behind the middle finger's (mm, positive back).
    index_knuckle_back: float | None = None
    ring_knuckle_back: float | None = None
    pinky_knuckle_back: float | None = None
    # Thumb laid alongside the index finger.
    thumb_reach: float | None = None  # wrist crease to the thumb tip
    thumb_tip_length: float | None = None  # thumb tip to the crease of its last joint
    def overrides(self) -> dict:
        """The ``Params`` values these measurements imply."""
        result = {}
        hand, palm, middle = self.hand_length, self.palm_length, self.middle_length
        if hand is not None and palm is None and middle is not None:
            palm = hand - middle
        if hand is None and middle is not None:
            hand = (palm if palm is not None else DEFAULT.palm_length) + middle
        if None not in (hand, palm, middle) and abs(hand - palm - middle) > MIDDLE_SLACK:
            raise ValueError(
                f"hand_length ({hand}) minus palm_length ({palm}) should equal middle_length ({middle});"
                " measure again or leave one out"
            )
        for name, value in (("hand_length", hand), ("palm_length", palm), ("hand_breadth", self.hand_breadth)):
            if value is not None:
                result[name] = value
        if middle is None:
            middle = result.get("hand_length", DEFAULT.hand_length) - result.get("palm_length", DEFAULT.palm_length)
        lengths = (self.index_length, None, self.ring_length, self.pinky_length)
        if any(v is not None for v in lengths):
            result["finger_ratios"] = tuple(
                1.0 if i == 1 else (v / middle if v is not None else DEFAULT.finger_ratios[i])
                for i, v in enumerate(lengths)
            )
        backs = (self.index_knuckle_back, None, self.ring_knuckle_back, self.pinky_knuckle_back)
        if any(v is not None for v in backs):
            result["knuckle_offsets"] = tuple(
                0.0 if i == 1 else (-v if v is not None else DEFAULT.knuckle_offsets[i])
                for i, v in enumerate(backs)
            )
        if self.thumb_reach is not None:
            result["thumb_reach"] = self.thumb_reach
        if self.thumb_tip_length is not None:
            result["thumb_tip_length"] = self.thumb_tip_length
        return result


def load(path: Path) -> dict:
    """``Params`` overrides from a TOML file with optional [hand] and [params] tables.

    [hand] holds measurements (see ``Hand``); [params] sets any ``Params``
    field directly and wins over [hand].
    """
    with Path(path).open("rb") as file:
        data = tomllib.load(file)
    unknown_tables = sorted(set(data) - {"hand", "params"})
    if unknown_tables:
        raise ValueError(f"{path}: unknown tables {', '.join(unknown_tables)}; use [hand] and [params]")
    measured = data.get("hand", {})
    _check(path, "hand", measured, {f.name for f in fields(Hand)})
    direct = data.get("params", {})
    _check(path, "params", direct, set(Params.__dataclass_fields__) - {"hand"})
    for name, value in measured.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{path}: [hand] {name} must be a number of millimetres")
        if value <= 0 and name not in OFFSETS:
            raise ValueError(f"{path}: [hand] {name} must be a positive number of millimetres")
    result = Hand(**{k: float(v) for k, v in measured.items()}).overrides()
    result.update({k: _frozen(v) for k, v in direct.items()})
    if result.get("palm_length", DEFAULT.palm_length) >= result.get("hand_length", DEFAULT.hand_length):
        raise ValueError(f"{path}: the palm must be shorter than the whole hand")
    return result


def _frozen(value):
    """TOML arrays as tuples, nested ones too, so Params stays hashable."""
    return tuple(_frozen(v) for v in value) if isinstance(value, list) else value


def _check(path, table: str, values: dict, known: set) -> None:
    unknown = sorted(set(values) - known)
    if unknown:
        raise ValueError(f"{path}: unknown [{table}] entries {', '.join(unknown)}")
