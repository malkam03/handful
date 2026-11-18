"""PNG previews of parts and assemblies, drawn with matplotlib.

These are quick shaded previews for reviewing the design, not photo renders.
Matplotlib sorts faces per triangle, so a few faces can draw in the wrong
order where parts nest closely.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402
from OCP.BRepTools import BRepTools  # noqa: E402

LIGHT = np.array([0.4, -0.5, 0.75])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def _triangles(part, tolerance: float):
    BRepTools.Clean_s(part.wrapped)
    vertices, triangles = part.tessellate(tolerance, 0.12)
    if not triangles:
        return np.empty((0, 3, 3))
    points = np.array([(v.X, v.Y, v.Z) for v in vertices])
    return points[np.array(triangles)]


def _shade(tris: np.ndarray, colour) -> np.ndarray:
    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    length = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = np.divide(normals, length, out=np.zeros_like(normals), where=length > 0)
    light = 0.35 + 0.65 * np.abs(normals @ LIGHT)
    rgb = np.clip(np.outer(light, colour), 0, 1)
    return np.hstack([rgb, np.ones((len(rgb), 1))])


def render(items, path: Path, title: str = "", view=(25, 40), tolerance: float = 0.1, size=(8, 7)) -> Path:
    """Draws (name, part, colour) items to a PNG file and returns its path."""
    fig = plt.figure(figsize=size, dpi=110)
    ax = fig.add_subplot(projection="3d")
    lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
    for _, part, colour in items:
        tris = _triangles(part, tolerance)
        if not len(tris):
            continue
        ax.add_collection3d(Poly3DCollection(tris, facecolors=_shade(tris, colour), linewidths=0))
        flat = tris.reshape(-1, 3)
        lo, hi = np.minimum(lo, flat.min(axis=0)), np.maximum(hi, flat.max(axis=0))
    pad = 0.05 * (hi - lo).max()
    lo, hi = lo - pad, hi + pad
    ax.set_xlim(lo[0], hi[0])
    ax.set_ylim(lo[1], hi[1])
    ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(hi - lo)  # true proportions
    ax.locator_params(axis="z", nbins=4)
    ax.view_init(elev=view[0], azim=view[1])
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_zlabel("z (mm)")
    if title:
        ax.set_title(title)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path
