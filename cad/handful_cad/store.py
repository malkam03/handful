"""Keeps the slow parts on disk, so each is built once per source and parameters.

``@stored`` wraps a part function. Each result is kept in memory for the run
and written to ``build/cache/`` as a BREP file, filed under a digest of the
CAD source and the build123d version, then under the function and its
arguments. A run with the same source and arguments loads the file instead of
building the part again, so the tests, ``build.py`` and the renders share
every part any of them has built. Any edit to ``handful_cad`` starts a fresh
folder, since a part may depend on any of its code.

Set ``HANDFUL_CACHE=0`` to build everything afresh without the files.
"""

import functools
import hashlib
import inspect
import os
import shutil
from pathlib import Path

import build123d
from build123d import Part, export_brep, import_brep

ROOT = Path(__file__).resolve().parents[1] / "build" / "cache"


def _source_digest() -> str:
    digest = hashlib.sha256(build123d.__version__.encode())
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode() + path.read_bytes())
    return digest.hexdigest()[:16]


SOURCE = _source_digest()


def enabled() -> bool:
    return os.environ.get("HANDFUL_CACHE", "1") != "0"


def path_for(name: str, args: tuple) -> Path:
    key = hashlib.sha256(repr(args).encode()).hexdigest()[:20]
    return ROOT / SOURCE / name / f"{key}.brep"


# Another run's prune() may remove this run's folder at any moment, so a
# missing or unreadable file only means "build it again".
def _load(path: Path) -> Part | None:
    try:
        return Part(import_brep(path).wrapped) if path.exists() else None
    except (OSError, ValueError):
        return None


def _save(part: Part, path: Path) -> None:
    partial = path.with_suffix(f".{os.getpid()}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        export_brep(part, partial)
        partial.replace(path)  # a reader never sees half a file
    except OSError:
        partial.unlink(missing_ok=True)


def stored(func):
    """Keep ``func``'s part in memory and on disk, by its arguments' ``repr``.
    The arguments must be plain values (``Params``, names, numbers, flags)
    whose ``repr`` says everything about them."""
    memory = {}
    signature = inspect.signature(func)

    def key(args: tuple, kwargs: dict) -> tuple:
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        return tuple(bound.arguments.values())

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        args = key(args, kwargs)
        if args in memory:
            return memory[args]
        path = path_for(func.__name__, args)
        part = _load(path) if enabled() else None
        if part is None:
            part = func(*args)
            if enabled():
                _save(part, path)
        memory[args] = part
        return part

    def is_stored(*args, **kwargs) -> bool:
        args = key(args, kwargs)
        return args in memory or (enabled() and path_for(func.__name__, args).exists())

    wrapper.is_stored = is_stored
    return wrapper


def prune() -> None:
    """Drop the files kept for other versions of the source."""
    if ROOT.exists():
        for stale in ROOT.iterdir():
            if stale.name != SOURCE:
                shutil.rmtree(stale, ignore_errors=True)
