"""The printed parts of the handful grip shell, built with build123d.

Every function takes a ``Params`` and returns a build123d ``Part`` in place.
The shell, caps, base and wedges are built for the left hand and mirrored
across the YZ plane for the right hand. The key module is the same for both
hands.

Frames: the shell frame has its origin at the centre of the footprint on top
of the base (see ``geometry``). The base sits below z = 0. ``placement`` moves
the shell frame onto a wedge.
"""

import math
from collections import Counter
from dataclasses import replace
from functools import cache

from build123d import (
    Align,
    Axis,
    Box,
    Circle,
    Compound,
    Cylinder,
    Edge,
    Face,
    Location,
    Part,
    Plane,
    Polygon,
    Pos,
    RectangleRounded,
    Rot,
    Solid,
    Vector,
    Wire,
    extrude,
    loft,
    mirror,
)
from OCP.BRepTools import BRepTools

from .geometry import Body, KeyPose, _top_down, key_poses, led_pose, widening
from .params import Params

BIG = 400.0
STL_TOLERANCE = (0.02, 0.1)  # linear (mm) and angular (rad) mesh tolerance of the exported STLs
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)
TOP = (Align.CENTER, Align.CENTER, Align.MAX)
CORNER = (Align.MIN, Align.MIN, Align.MIN)
ORIGIN = Vector(0, 0, 0)


def _above(z: float) -> Part:
    return Pos(0, 0, z) * Box(BIG, BIG, BIG, align=BOTTOM)


def _below(z: float) -> Part:
    return Pos(0, 0, z) * Box(BIG, BIG, BIG, align=TOP)


def _handed(params: Params, part: Part) -> Part:
    return mirror(part, about=Plane.YZ) if params.mirrored else part


def _largest(part: Part) -> Part:
    """Drops the zero-volume slivers that booleans on curved faces can leave behind."""
    return Part(Compound([max(part.solids(), key=lambda s: s.volume)]).wrapped)


def _mirror_vector(v: Vector) -> Vector:
    return Vector(-v.X, v.Y, v.Z)


def poses(params: Params) -> list:
    """Key poses for the chosen hand, thumb first."""
    left = key_poses(params)
    if not params.mirrored:
        return left
    keys = ("surface", "normal", "axis", "along", "module_along")
    return [replace(p, **{k: getattr(p, k) and _mirror_vector(getattr(p, k)) for k in keys}) for p in left]


# Outlines and the body -----------------------------------------------------


def _outline_points(
    thumb: float,
    front: float,
    n: float,
    centre: Vector = ORIGIN,
    count: int = 96,
    back: float | None = None,
    pinky: float | None = None,
    n_rear: float | None = None,
    spread: tuple = (0.0, 0.0),
) -> list:
    """A superellipse round ``centre``, reaching ``thumb`` towards +X,
    ``pinky`` towards -X, ``front`` towards +Y and ``back`` towards -Y, with
    exponent n in front and ``n_rear`` behind. The front half widens by
    ``spread`` towards the front (see ``geometry.widening``)."""
    back = front if back is None else back
    pinky = thumb if pinky is None else pinky
    n_rear = n if n_rear is None else n_rear
    points = []
    for i in range(count):
        t = 2 * math.pi * i / count
        c, s = math.cos(t), math.sin(t)
        e = 2 / (n if s >= 0 else n_rear)
        t = abs(s) ** e if s >= 0 else 0.0
        reach = thumb * widening(spread[0], t) if c >= 0 else pinky * widening(spread[1], t)
        x = reach * math.copysign(abs(c) ** e, c)
        y = (front if s >= 0 else back) * math.copysign(abs(s) ** e, s)
        points.append(Vector(centre.X + x, centre.Y + y, centre.Z))
    return points


def _outline_wire(
    thumb: float,
    front: float,
    n: float,
    centre: Vector,
    back: float | None = None,
    pinky: float | None = None,
    n_rear: float | None = None,
    spread: tuple = (0.0, 0.0),
) -> Wire:
    points = _outline_points(thumb, front, n, centre, back=back, pinky=pinky, n_rear=n_rear, spread=spread)
    # Same parameters on every outline, so lofted sections share one knot
    # vector and the surface stays light for booleans.
    parameters = [i / len(points) for i in range(len(points) + 1)]
    return Wire([Edge.make_spline(points, periodic=True, parameters=parameters)])


def _footprint_points(params: Params, grow: float, z0: float) -> list:
    a, b, _ = params.body_axes
    # A fine polyline rather than a spline: flat facets keep the base's and
    # wedges' booleans reliable, and stay within 0.05 mm of the body's curve.
    return _outline_points(
        a + grow,
        b + grow,
        params.body_squareness,
        Vector(0, 0, z0),
        240,
        params.body_rear_length + grow,
        params.body_pinky_width + grow,
        params.body_rear_squareness,
        params.front_spread,
    )


def footprint_extremes(params: Params) -> tuple:
    """The left-hand body's outline at the desk: its pinky edge (least X) and thumb edge (most X)."""
    xs = [p.X for p in _footprint_points(params, 0, 0)]
    return min(xs), max(xs)


def heel_line(params: Params) -> tuple:
    """The line the wedges tilt about, on the base's bottom face, in the
    left-hand frame: a point on it, its direction and the unit normal
    pointing in towards the thumb. With no heel bevel it is the pinky edge."""
    points = _footprint_points(params, 0, 0)
    edge = min(p.X for p in points)
    z = -params.base_thickness
    if not params.heel_angle:
        return Vector(edge, 0, z), Vector(0, 1, 0), Vector(1, 0, 0)
    inset, frac = params.heel_front
    front = Vector(edge + inset, frac * max(p.Y for p in points), z)
    back = Vector(edge + params.heel_back, min(p.Y for p in points), z)
    u = (back - front).normalized()
    n = Vector(u.Y, -u.X, 0)
    if n.X < 0:
        u, n = -u, -n
    return front, u, n


def _heel_side(params: Params, offset: float) -> Part:
    """Everything more than ``offset`` past the heel line, away from the thumb (left-hand frame)."""
    at, u, n = heel_line(params)
    return Plane(at - n * offset, x_dir=-n, z_dir=u) * Box(BIG, BIG, BIG, align=(Align.MIN, Align.CENTER, Align.CENTER))


def _heel_rise(params: Params, d: float) -> float:
    """How far the rounded heel's underside rises above the base's bottom, ``d`` mm past the heel line."""
    r, b = params.heel_radius, math.radians(params.heel_angle)
    reach = r * math.sin(b)
    if d <= reach:
        return r - math.sqrt(r * r - d * d)
    return r * (1 - math.cos(b)) + (d - reach) * math.tan(b)


def _heel_cut(params: Params) -> Part | None:
    """What the rounded heel removes past the heel line (left-hand frame):
    under an arc of ``heel_radius`` that starts flat on the base's bottom,
    then under its tangent at ``heel_angle``."""
    if not params.heel_angle:
        return None
    at, u, n = heel_line(params)
    r, b = params.heel_radius, math.radians(params.heel_angle)
    up = Vector(0, 0, 1)
    centre = at + up * r
    touch = centre + (-n * math.sin(b) - up * math.cos(b)) * r
    x_dir = -n * math.cos(b) + up * math.sin(b)
    z_dir = x_dir.cross(u)
    if z_dir.Z < 0:
        z_dir = -z_dir
    below = (Align.CENTER, Align.CENTER, Align.MAX)
    straight = Plane(touch, x_dir=x_dir, z_dir=z_dir) * Box(BIG, BIG, BIG, align=below)
    under_arc = Plane(centre, x_dir=-n, z_dir=up) * Box(2 * r * math.sin(b) + 0.02, BIG, BIG, align=below)
    roller = Plane(centre, z_dir=u) * Cylinder(r, BIG)
    return ((straight + under_arc) & _heel_side(params, 0)) - roller


def _heel_reach(params: Params) -> float:
    """How far the footprint reaches past the heel line."""
    at, _, n = heel_line(params)
    return max(0.0, max(-(p - Vector(at.X, at.Y, 0)).dot(n) for p in _footprint_points(params, 0, 0)))


def _footprint(params: Params, grow: float, z0: float, height: float, x_scale: float = 1.0) -> Part:
    """The body's outline, ``grow`` larger all round, extruded up from z0.

    ``x_scale`` shrinks it across X towards the pinky edge, which is the
    wedge's hinge."""
    points = _footprint_points(params, grow, z0)
    edge = min(p.X for p in points)
    points = [Vector(edge + (p.X - edge) * x_scale, p.Y, p.Z) for p in points]
    wire = Wire.make_polygon(points, close=True)
    return Part(Compound([extrude(Face(wire), height)]).wrapped)


@cache
def body_solid(params: Params, grow: float = 0.0) -> Part:
    """The body surface as a solid, ``grow`` larger all round, extended 10 mm below z = 0."""
    body = Body.of(params, grow)
    p = min(body.crown, body.rear_crown, body.pinky_crown)
    wires = []
    sections = 28
    for k in range(sections + 1):
        phi = math.radians(86.0) * k / sections  # stops short of the pole: a small flat top, no sliver
        z = body.c * math.sin(phi) ** (2 / p)
        thumb, pinky, front, back, centre = body.slice(z)
        wires.append(_outline_wire(thumb, front, body.square, centre, back, pinky, body.square_rear, body.spread))
    dome = Solid.make_loft(wires, ruled=False)
    skirt = extrude(Face(wires[0]), -10)
    return Part(Compound([dome]).wrapped) + skirt


@cache
def _boss_points(params: Params) -> list:
    """The shell's screw bosses, set in from the body's outline at the
    insert's top, so a flared side keeps a roof over each insert. Each starts
    at its angle in ``boss_angles`` and slides round the outline, a step at a
    time either way, to the nearest spot where its wall clears every cavity."""
    keepout = cavities(params) + _led_cut(params)
    wall = Cylinder(params.insert_hole / 2 + params.insert_wall, params.insert_depth, align=BOTTOM)
    points = []
    for angle in params.boss_angles:
        for step in range(0, params.boss_search + 1, 2):
            free = [
                p for p in (_boss_point(params, angle + step), _boss_point(params, angle - step))
                if (Pos(p) * wall & keepout).volume < 1e-3
            ]
            if free:
                points.append(min(free, key=lambda p: (p.X, p.Y)))
                break
        else:
            raise ValueError(f"no room for the screw boss near {angle} deg; change boss_angles")
    return points


def _boss_point(params: Params, angle: float) -> Vector:
    thumb, pinky, front, back, centre = Body.of(params).slice(params.insert_depth + params.boss_roof)
    r = params.wall + params.boss_inset
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    n = params.body_squareness if s >= 0 else params.body_rear_squareness
    t = abs(s) ** (2 / n) if s >= 0 else 0.0
    reach = thumb * widening(params.front_spread[0], t) if c >= 0 else pinky * widening(params.front_spread[1], t)
    x = (reach - r) * math.copysign(abs(c) ** (2 / n), c)
    y = ((front if s >= 0 else back) - r) * math.copysign(abs(s) ** (2 / n), s)
    point = Vector(centre.X + x, centre.Y + y, 0)
    if params.heel_angle:
        # A screw near the heel line moves in, so its head stays in the full-thickness base.
        at, _, n = heel_line(params)
        at = Vector(at.X, at.Y, 0)
        point += n * max(0.0, params.heel_boss_gap - (point - at).dot(n))
    return point


def _pico_centre(params: Params) -> Vector:
    return Vector(params.pico_x, params.pico_rear_y + params.pico_size[1] / 2, params.pico_standoff)


def _usb_axis_z(params: Params) -> float:
    return params.pico_standoff + params.pico_size[2] + params.pico_usb_height / 2


def _usb_front_y(params: Params) -> float:
    return params.pico_rear_y + params.pico_size[1] + params.pico_usb_overhang


# Key module -----------------------------------------------------------------


def key_module(params: Params) -> Part:
    """One switch mount: a Choc plate, walls, and a floor holding the socket.

    Local frame: plate top at z = 0, +Y along the finger towards the palm. The
    plate's lip runs on along Y past the walls and seats against the shell; a
    post on the base pushes the floor up, so the module needs no screws.
    Prints leaning on its -Y end with no supports.
    """
    width, outer, plate = params.module_width, params.module_outer, params.switch_plate
    floor_top, depth = -params.switch_plate_to_pcb, params.module_depth
    lip = Box(width, params.module_lip_length, plate, align=TOP)
    walls = Pos(0, 0, -plate) * Box(width, outer, params.switch_plate_to_pcb - plate, align=TOP)
    walls -= Box(params.switch_bottom_clearance, params.switch_clip_clearance, BIG)
    floor = Pos(0, 0, floor_top) * Box(width, outer, depth - params.switch_plate_to_pcb, align=TOP)
    pocket_top = floor_top - params.pcb_thickness
    module = lip + walls + floor + _socket_floor(params, depth)

    cutout = params.switch_cutout + params.hole_clearance
    module -= Box(cutout, cutout, 2 * plate + 0.2)
    module -= Cylinder((params.switch_post_diameter + 2 * params.clearance) / 2, BIG)
    for x, y in params.switch_pins:
        module -= Pos(x, y, 1) * Cylinder(params.socket_hole / 2, 1 - pocket_top + 0.1, align=TOP)
        module -= Pos(x, y) * Cylinder(params.switch_pin_relief / 2, BIG)  # the pin's tip pokes through
    for x, y in params.switch_pegs:
        module -= Pos(x, y) * Cylinder(params.switch_peg_diameter / 2 + params.clearance, BIG)

    # Socket channel: the socket, with its wires soldered on, slides in from
    # the +Y side and rests on a thin skin, which takes the push of the switch.
    (x0, y0), (x1, y1) = params.switch_pins
    mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
    c = params.clearance
    _, bh = params.socket_body
    half_tabs = params.socket_tabs_width / 2 + c
    y_start = mid_y - bh / 2 - c
    # Where the tabs reach past the walls the channel runs out through the side,
    # leaving a ledge under them; the switch's pins hold the socket in place.
    x0, x1 = mid_x - half_tabs, mid_x + half_tabs
    lo, hi = params.module_socket_x
    x0, x1 = (x0 - 1 if x0 <= lo + 1e-6 else x0), (x1 + 1 if x1 >= hi - 1e-6 else x1)
    channel = Box(x1 - x0, outer, params.socket_thickness + 0.1, align=(Align.MIN, Align.MIN, Align.MAX))
    module -= Pos(x0, y_start, pocket_top) * channel
    return module


def _socket_floor(params: Params, depth: float, grow: float = 0.0, x_range: tuple | None = None,
                  y_range: tuple | None = None) -> Part:
    """The floor at the socket's level, reaching out under its solder tabs,
    ``grow`` larger. Under the tabs it tapers in at 45 degrees, clear of a
    neighbouring module and printable leaning on the module's end."""
    lo, hi = x_range or params.module_socket_x
    half = params.module_width / 2 + grow
    top = params.switch_plate_to_pcb + params.pcb_thickness - grow
    under = params.switch_plate_to_pcb + params.pcb_thickness + params.socket_thickness + 0.1 + grow
    floor = Box(2 * half, params.module_outer + 2 * grow, depth - top + grow, align=TOP)
    floor = Pos(0, 0, -top) * floor
    y0, y1 = y_range or (-params.module_outer / 2, params.module_outer / 2)  # along the finger
    y0, y1 = y0 - grow, y1 + grow
    sweep = depth - params.module_depth  # a pocket runs the module's outline on down
    for side, edge in ((1, hi + grow), (-1, -lo + grow)):
        if edge <= half:
            continue
        foot = max(half, edge - (params.module_depth + grow - under))
        bottom = -(under + edge - foot) - sweep
        points = [(half, -top), (edge, -top), (edge, -under - sweep), (foot, bottom), (half, bottom)]
        floor += _xz_prism([(side * x, z) for x, z in points], y0, y1)
    return floor


def tactile_seat(params: Params) -> float:
    """Height of a tactile button's underside above the plate's top, so its
    actuator sits ``tactile_gap`` under the cap's pusher (the switch stem's top)."""
    return params.switch_stem_height - params.tactile_gap - params.tactile_height


def tactile_adapter(params: Params) -> Part:
    """Holds a 12 x 12 mm tactile button in a key module instead of a Choc switch.

    Local frame as the key module's: plate top at z = 0. A square plug pushes
    into the switch hole; a block on the plate lifts the button to
    ``tactile_seat`` and a cup round its body holds it. The legs, cut short, run down open
    slots into the module, where wires soldered to them leave through the
    socket holes and channel. Prints plug-down with no supports.
    """
    c = params.clearance
    seat = tactile_seat(params)
    pocket = params.tactile_size + 2 * c
    outer = pocket + 2 * params.tactile_wall
    plug = params.switch_cutout - params.tactile_plug_fit
    adapter = Box(plug, plug, params.tactile_plug_depth, align=TOP)
    adapter += Box(outer, outer, seat + params.tactile_body_height - 0.5, align=BOTTOM)
    adapter -= Pos(0, 0, seat) * Box(pocket, pocket, BIG, align=BOTTOM)
    # Leg slots along Y, open below the cup, wide enough for 12.5 to 13 mm legs.
    near, far, across = params.tactile_legs
    w = params.tactile_leg_slot
    y_from, y_to = near / 2 - w / 2, max(far / 2 + w / 2, outer / 2 + 1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            slot = Box(w, y_to - y_from, BIG, align=(Align.CENTER, Align.MIN, Align.CENTER))
            adapter -= Pos(sx * across / 2, 0, 0) * Rot(0, 0, 0 if sy > 0 else 180) * Pos(0, y_from, 0) * slot
    # A thumb hole under the button, to push it out from below.
    adapter -= Cylinder(params.tactile_size / 4, BIG)
    return adapter


def tactile_adapter_print(params: Params) -> Part:
    """The adapter plug-down on z = 0."""
    return Pos(0, 0, params.tactile_plug_depth) * tactile_adapter(params)


# Shell and caps ---------------------------------------------------------------


def _hinge_sign(pose: KeyPose) -> int:
    """+1 where the key frame's +Y runs from the switch towards the cap's
    hinge: the fingers' palm side. The thumb's is -Y."""
    return -1 if pose.name == "thumb" else 1


CAP_PARTS = ("paddle", "flexure", "anchor")
SWEEP_STEPS = (0.25, 0.5, 0.75, 1.0, 1.15)  # fractions of the stop angle the well is sized for
PUSHER_SWING = 1.0  # sideways room round the pusher: it swings on an arc about the hinge


def _cap_span(params: Params, pose: KeyPose, part: str) -> tuple:
    """From and to, measured from the switch centre towards the hinge, of one part of a cap."""
    _, _, back = params.cap_reach(pose.name)
    hinge = back + params.flexure_length
    return {"paddle": (-BIG, back), "flexure": (back, hinge), "anchor": (hinge, BIG)}[part]


def _cap_region(
    params: Params, pose: KeyPose, part: str, grow: float = 0.0, depth: float = 40.0, tip_extra: float = 0.0
) -> Part:
    """One part of a cap's outline, ``grow`` larger and ``tip_extra`` longer
    at the fingertip end, as a prism along the press axis."""
    width, tip, back = params.cap_reach(pose.name)
    tip += tip_extra
    end = back + params.flexure_length + params.anchor_length
    h = _hinge_sign(pose)
    outline = RectangleRounded(width + 2 * grow, tip + end + 2 * grow, params.cap_corner + grow)
    prism = Pos(0, h * (end - tip) / 2, -depth) * extrude(outline, depth + 20)
    b0, b1 = _cap_span(params, pose, part)
    window = Pos(0, h * (b0 + b1) / 2, -depth) * Box(BIG, b1 - b0, depth + 20, align=BOTTOM)
    return pose.plane * (prism & window)


@cache
def _cap_floor(params: Params, pose: KeyPose, below: float) -> Part:
    """Everything above a floor ``below`` the shell surface along the cap's
    centre line. Caps and wells stop at it, so where the shell rolls away
    across a cap, the cap narrows rather than wrapping down the side wall."""
    _, tip, back = params.cap_reach(pose.name)
    end = back + params.flexure_length + params.anchor_length
    h = _hinge_sign(pose)
    body = Body.of(params)
    steps = 16
    points = []
    for k in range(steps + 1):
        v = -tip - 3 + (tip + end + 6) * k / steps
        drop = _top_down(body, pose.surface + pose.along * (h * v), -pose.axis)
        points.append((h * v, -drop - below))
    points += [(points[-1][0], 40.0), (points[0][0], 40.0)]
    profile = Polygon(*points, align=None)
    return pose.plane * extrude(Plane.YZ * profile, BIG, both=True)


def _surface_at(params: Params, pose: KeyPose, b: float, grow: float = 0.0) -> Vector:
    """The point on the shell surface, ``grow`` out, ``b`` from the switch centre towards the hinge."""
    at = pose.plane.from_local_coords((0, _hinge_sign(pose) * b, 0))
    return Body.of(params, grow).hit(Vector(*at) - pose.axis * 30, pose.axis)


def _near(params: Params, pose: KeyPose, part_name: str, piece: Part) -> Part:
    """The solid of ``piece`` on the shell surface under one part of a cap,
    not where its prism also catches the shell's far side."""
    _, tip, back = params.cap_reach(pose.name)
    middle = {
        "paddle": (back - tip) / 2,
        "flexure": back + params.flexure_length / 2,
        "anchor": back + params.flexure_length + params.anchor_length / 2,
    }[part_name]
    point = _surface_at(params, pose, middle)
    return Part(Compound([min(piece.solids(), key=lambda solid: solid.distance_to(point))]).wrapped)


def _lever(params: Params, pose: KeyPose) -> float:
    """From the switch centre to the hinge, the middle of the flexure."""
    return params.cap_reach(pose.name)[2] + params.flexure_length / 2


@cache
def well_depth(params: Params, pose: KeyPose) -> float:
    """How deep below the surface, along the press axis, the cap's well
    reaches: room for the paddle's underside turned about the hinge to the
    stop, sampled over the paddle, as the shell curves under it."""
    width, tip, back = params.cap_reach(pose.name)
    body = Body.of(params)
    point, direction = _press_axis(params, pose)
    angle = math.asin(min(1.0, params.press_stop / _lever(params, pose)))
    below = params.cap_thickness - params.cap_proud
    h = _hinge_sign(pose)
    deepest = 0.0
    for i in range(5):
        u = (i / 4 - 0.5) * (width - 2 * params.cap_corner)
        for j in range(9):
            v = -tip + (tip + back) * j / 8
            top = pose.surface + pose.x_dir * u + pose.along * (h * v)
            rest = top - pose.axis * (_top_down(body, top, -pose.axis) + below)
            turned = _turn(rest, point, direction, angle)
            deepest = max(deepest, -_top_down(body, turned, -pose.axis))
    return deepest + params.cap_travel_margin


@cache
def tip_swing(params: Params, pose: KeyPose) -> float:
    """How far the paddle's fingertip end moves out past its rest position,
    along the surface, as the cap turns about the hinge to just past the
    stop. On a curved front the tip swings along the slope, so the well is
    that much longer there."""
    width, tip, _ = params.cap_reach(pose.name)
    body = Body.of(params)
    point, direction = _press_axis(params, pose)
    stop = math.asin(min(1.0, params.press_stop / _lever(params, pose)))
    h = _hinge_sign(pose)
    out = -pose.along * h
    furthest = 0.0
    for i in range(5):
        u = (i / 4 - 0.5) * (width - 2 * params.cap_corner)
        top = pose.surface + pose.x_dir * u + pose.along * (-h * tip)
        surface = top - pose.axis * _top_down(body, top, -pose.axis)
        for depth in (-params.cap_proud, params.cap_thickness - params.cap_proud):
            p = surface - pose.axis * depth
            for f in SWEEP_STEPS:
                furthest = max(furthest, (_turn(p, point, direction, stop * f) - p).dot(out))
    return furthest


def _turn(p: Vector, origin: Vector, axis: Vector, angle: float) -> Vector:
    """``p`` turned by ``angle`` radians about the line through ``origin`` along unit ``axis``."""
    r = p - origin
    k = axis.normalized()
    c, s = math.cos(angle), math.sin(angle)
    return origin + r * c + k.cross(r) * s + k * (k.dot(r) * (1 - c))


@cache
def _anchor_depth(params: Params, pose: KeyPose) -> float:
    """How far in, as a body offset, the anchor's underside sits, so the tab
    is ``anchor_thickness`` thick at its screw. An offset body shrinks its
    axes, so where the shell curves tightly it comes out thinner than the
    offset; this offsets that much further."""
    depth = params.anchor_thickness
    top = Body.of(params, params.cap_proud)
    for _ in range(4):
        frame = _anchor_frame(params, pose, depth)
        normal = frame.z_axis.direction
        thick = (top.hit(frame.position, normal) - frame.position).length
        depth += params.anchor_thickness - thick
    return depth


def _anchor_frame(params: Params, pose: KeyPose, depth: float | None = None) -> Location:
    """On the anchor's underside, z out of the surface: where the screw goes
    in. It is at the anchor's middle, but for the thumb's ``thumb_screw_shift``."""
    depth = _anchor_depth(params, pose) if depth is None else depth
    _, _, back = params.cap_reach(pose.name)
    b = back + params.flexure_length + params.anchor_length / 2
    down, towards_hinge = params.thumb_screw_shift if pose.name == "thumb" else (0.0, 0.0)
    across = -down if pose.x_dir.Z > 0 else down
    at = pose.plane.from_local_coords((across, _hinge_sign(pose) * (b - towards_hinge), 0))
    under = Body.of(params, params.cap_proud - depth)
    point = under.hit(Vector(*at) - pose.axis * 30, pose.axis)
    return Plane(origin=point, x_dir=pose.x_dir, z_dir=under.normal(point)).location


def _union(a: Part, b: Part, slack: float = 0.01) -> Part:
    """``a`` and ``b`` fused. Where their faces graze, OpenCASCADE can drop
    most of the result; a fuzzy fuse keeps it. ``slack``: how much volume
    the fuse may lose to rounding."""
    least = max(a.volume, b.volume) - slack
    result = a + b
    if result.is_valid and result.volume >= least:
        return result
    for tol in (1e-4, 1e-3, 1e-2):
        result = a.fuse(b, tol=tol).clean()
        if result.is_valid and result.volume >= least:
            return Part(result.wrapped) if not isinstance(result, Part) else result
    raise ValueError("two cuts don't fuse cleanly; nudge a key's position or cap size")


def _counterbore(params: Params, clear: float, head: float, head_height: float) -> Part:
    """A screw's clearance hole down -z with a pocket for its socket head,
    sunk a clearance below z = 0, the face the head goes in from. The pocket
    runs on out past that face, so where the face curves away (the thumb
    cap's tab) no skin is left over the head."""
    c = params.clearance
    top = (Align.CENTER, Align.CENTER, Align.MAX)
    hole = Cylinder(clear / 2, 20, align=top)
    out = 5.0
    return hole + Pos(0, 0, out) * Cylinder(head / 2 + c, head_height + c + out, align=top)


def _key_well(params: Params, pose: KeyPose, grow: float = 0.0, pocket_grow: float = 0.0) -> Part:
    """Above the plate: a pocket for the switch housing; then the cap's well,
    deep under the paddle, shallow under the flexure, and a seat for the anchor."""
    c = params.clearance
    pocket = params.switch_clip_clearance + 2 * (c + pocket_grow)
    housing = params.switch_housing_height
    cut = pose.plate * Pos(0, 0, -0.1) * Box(pocket, pocket, housing + 0.2, align=BOTTOM)
    g = params.cap_gap + grow
    for name in CAP_PARTS:
        floor = _cap_wrap(params, pose, name, well=True)
        if name == "paddle":
            # Longer at the fingertip end by the tip's swing.
            region = _cap_region(params, pose, name, g, tip_extra=tip_swing(params, pose)) & floor
        else:
            region = _cap_region(params, pose, name, g) & floor
        region -= _below_well(params, pose, name)
        cut = _union(cut, _near(params, pose, name, region))
    # A bore for the pusher from the switch pocket up to the well, wide
    # enough for the pusher's small sideways swing as the cap turns.
    bore = params.pusher_diameter / 2 + g + PUSHER_SWING
    cut = _union(cut, pose.plate * Pos(0, 0, housing) * Cylinder(bore, pose.plate_depth, align=BOTTOM))
    insert = Cylinder(params.m2_insert_hole / 2, params.m2_insert_depth + 0.1, align=TOP)
    return cut + _anchor_frame(params, pose) * Pos(0, 0, 0.1) * insert


def _below_well(params: Params, pose: KeyPose, name: str, lift: float = 0.0) -> Part:
    """The body below the floor of a cap part's well, its top ``lift`` above
    that floor. The paddle's well is as deep as well_depth measures: down the
    press axis, not square to the surface."""
    if name == "paddle":
        return Pos(*(-pose.axis * (well_depth(params, pose) - lift))) * body_solid(params)
    seat = {
        "flexure": params.cap_thickness - params.cap_proud + params.flexure_room,
        "anchor": _anchor_depth(params, pose) - params.cap_proud,
    }[name]
    return body_solid(params, lift - seat)


def _module_box(params: Params, pose: KeyPose, grow: float = 0.0, length: float | None = None) -> Part:
    """The module's lip outline, ``grow`` larger, as a prism down the press axis from the plate."""
    length = params.module_depth if length is None else length
    w = params.module_width + 2 * grow
    lip = params.module_lip_length + 2 * grow
    # The pocket runs the socket side on to the lip's end, room for the wires.
    ys = (-params.module_outer / 2, params.module_lip_length / 2)
    floor = _socket_floor(params, length, grow, _left_socket_x(params), ys)
    return pose.plate * (Box(w, lip, length + grow, align=TOP) + floor)


def _module_seat(params: Params, pose: KeyPose, grow: float = 0.0) -> Part:
    """The seated module's own outline, ``grow`` larger: the lip, plate thick,
    and the body under it. The base round a module needs no more room than
    this, as the modules go in before the base."""
    w, outer, depth = params.module_width + 2 * grow, params.module_outer + 2 * grow, params.module_depth
    lip = Box(w, params.module_lip_length + 2 * grow, params.switch_plate + grow, align=TOP)
    body = Box(w, outer, depth + grow, align=TOP) + _socket_floor(params, depth, grow, _left_socket_x(params))
    return pose.plate * (lip + body)


def _left_socket_x(params: Params) -> tuple:
    """The module's reach across the finger in a left-hand key frame. A
    right-hand shell is built left-handed and mirrored, but its modules are
    the same part turned round, so their off-centre socket side swaps over."""
    lo, hi = params.module_socket_x
    return (-hi, -lo) if params.mirrored else (lo, hi)


def _module_x_extent(params: Params, pose: KeyPose) -> tuple:
    """How far below and above the plate's centre the module reaches, across the finger, in world Z."""
    lo, hi = _left_socket_x(params)
    dz = pose.module_x_dir.Z
    return min(lo * dz, hi * dz), max(lo * dz, hi * dz)


def _insertion_length(params: Params, pose: KeyPose) -> float:
    """How far a finger module travels down its axis from its seat until all of it is below the shell."""
    c = params.clearance
    along = pose.module_along or pose.along
    high = (params.module_lip_length / 2 + c) * abs(along.Z)
    high += _module_x_extent(params, pose)[1] + c * abs(pose.module_x_dir.Z)
    return (pose.plate.position.Z + high) / pose.axis.Z + 1


def _floor(params: Params, pose: KeyPose, offset: float = 0.0) -> Location:
    """The module floor's underside, ``offset`` further down the press axis."""
    return pose.plate * Pos(0, 0, -params.module_depth - offset)


def _post(params: Params, pose: KeyPose, grow: float = 0.0) -> Part:
    """A vertical post on the base, its top on the module's floor."""
    centre = _floor(params, pose).position
    size = params.post_size + 2 * grow
    post = Pos(centre.X, centre.Y, -1) * Box(size, size, centre.Z + 20, align=BOTTOM)
    return post & (_floor(params, pose, params.post_gap - grow) * _below(0))


def _thumb_bay(params: Params, pose: KeyPose, grow: float = 0.0) -> tuple:
    """The thumb module's bay and the block on the base that holds the module, as (x0, x_floor, x_plate, top, half)."""
    plate = pose.plate.position
    x_floor = plate.X - params.module_depth
    x0 = x_floor - params.thumb_block - params.clearance
    top = plate.Z + _module_x_extent(params, pose)[1] + params.clearance
    half = params.module_lip_length / 2 + params.clearance
    return x0, x_floor, plate.X, top, half


def _xz_prism(points: list, y0: float, y1: float) -> Part:
    """A prism along Y from y0 to y1 with the given (x, z) outline."""
    face = Plane.XZ * Polygon(*points, align=None)
    return Pos(0, y1, 0) * extrude(face, y1 - y0, dir=(0, -1, 0))  # either winding


def _thumb_cavity(params: Params, pose: KeyPose) -> Part:
    """Room to lift the thumb module, its switch fitted, in from below. The roof over the block slopes at 45 degrees."""
    x0, x_floor, x_plate, top, half = _thumb_bay(params, pose)
    y = pose.plate.position.Y
    points = [(x0, -1), (x_plate, -1), (x_plate, top), (x_floor, top), (x0, top - (x_floor - x0))]
    cavity = _xz_prism(points, y - half, y + half)
    # The switch, clipped in, rises with the module: a slot past the plate
    # for its housing, and a narrower one for its stem.
    c, z = params.clearance, pose.plate.position.Z
    housing, stem = params.switch_housing_height + c, params.switch_stem_height + c
    for depth, width in ((housing, params.switch_clip_clearance + 2 * c), (stem, params.pusher_diameter + 2 * c)):
        cavity += Pos(x_plate - 0.1, y, -1) * Box(depth + 0.1, width, z + 1, align=(Align.MIN, Align.CENTER, Align.MIN))
    return cavity


def thumb_block(params: Params) -> Part:
    """The block on the base that holds the thumb module against its seat, in the left-hand frame."""
    pose = key_poses(params)[0]
    x0, x_floor, x_plate, top, _ = _thumb_bay(params, pose)
    c, g = params.clearance, params.post_gap
    x1 = x_floor - g
    roof = lambda x: top - (x_floor - x) - 2 * c  # noqa: E731
    lead = 1.0
    points = [
        (x0 + c, -1), (x1, -1), (x1, roof(x1 - lead) - lead), (x1 - lead, roof(x1 - lead)), (x0 + c, roof(x0 + c))
    ]
    # Narrower than the module's floor, so the socket wires pass at the +Y end.
    y = pose.plate.position.Y
    half = params.module_outer / 2 - params.module_wall
    block = _xz_prism(points, y - half - 2, y + half - 2)
    # A rib under the module's plate end stops it dropping; the wires run
    # beside it, under the rest of the module.
    under = pose.plate.position.Z + _module_x_extent(params, pose)[0] - g
    r0, r1 = x_plate - params.thumb_rib - c, x_plate - c
    rib = [(r0, -1), (r1, -1), (r1, under), (r0, under)]
    block += _xz_prism(rib, y - params.module_outer / 2, y + half - 2)
    return block & _above(-1)


def _core(params: Params, grow: float = 0.0) -> Part:
    """The Pico's bay: vertical walls, then 45 degree roofs on all four sides."""
    w = params.core_half_width + grow
    wall = params.core_wall_height
    x = params.pico_x
    y0, y1 = params.core_rear_y - grow, _usb_front_y(params) + 1 + grow
    top = wall + w
    gable = _xz_prism([(x - w, -1), (x + w, -1), (x + w, wall), (x, top), (x - w, wall)], y0 - top, y1 + top)
    ends = Plane.YZ * Polygon((y0, -1), (y1, -1), (y1, wall), (y1 - w, top), (y0 + w, top), (y0, wall), align=None)
    hip = Pos(x - w - 1, 0, 0) * extrude(ends, 2 * w + 2)
    return gable & hip


def _troughs(params: Params) -> Part:
    """Wire channels along the bottom face: the finger tunnels to the thumb bay, and the thumb bay to the Pico's bay."""
    thumb, *fingers = key_poses(params)
    x0, _, x_plate, _, half = _thumb_bay(params, thumb)
    h, w = params.trough_height, params.trough_width
    ty = thumb.plate.position.Y
    ends = [_floor(params, f).position for f in fingers]
    y = ty + half - 2
    across = Pos(min(e.X for e in ends) - 4, y, -1) * Box(x_plate - min(e.X for e in ends) + 4, w, h + 1, align=CORNER)
    out = across
    for e in ends:
        out += Pos(e.X, y, -1) * Box(w, max(e.Y - y, w), h + 1, align=(Align.CENTER, Align.MIN, Align.MIN))
    xc = params.pico_x + params.core_half_width
    out += Pos(xc - w, ty - half - 4, -1) * Box(x0 - xc + 2 * w, w + 4, h + 1, align=CORNER)
    return out


def _cable_channel(params: Params) -> Part:
    """The USB plug's channel, then a groove for the cable out through the front."""
    _, b, _ = params.body_axes
    c = params.clearance
    w, h = params.usb_plug_size
    y = _usb_front_y(params) - 2
    top = _usb_axis_z(params) + h / 2
    rear_up = (Align.CENTER, Align.MIN, Align.MIN)
    plug = Pos(params.pico_x, y, -1) * Box(w, params.usb_plug_length + 4, top + 1, align=rear_up)
    d = params.usb_cable_diameter + 2 * c
    cable = Pos(params.pico_x, y, -1) * Box(d, 2 * b, _usb_axis_z(params) + d / 2 + 1, align=rear_up)
    return plug + cable


def _led_seat(params: Params) -> float:
    """Depth below the shell surface where the LED's flange stops."""
    _, _, length = params.led
    return max(length - params.led_flange_thickness - params.led_proud, params.wall + 1.0)


def _led_cut(params: Params) -> Part:
    """The status LED's hole, the bay behind it for its leads, and a way down to the bottom face for the wires."""
    pose = led_pose(params)
    at = pose.plane.location
    c = params.clearance
    diameter, room = params.led_wiring_room
    r = diameter / 2
    body, _, _ = params.led
    front = _led_seat(params)
    hole = at * Pos(0, 0, 5) * Cylinder(body / 2 + c, front + 5, align=TOP)
    room += params.led_flange_thickness  # the room starts behind the flange
    bay = Cylinder(r, room, align=TOP)
    # A teardrop roof: the local -X is up, so the bay prints without supports.
    bay += Rot(0, 0, 45) * Box(2 * r, 2 * r, room, align=TOP)
    cut = hole + at * Pos(0, 0, -front) * bay
    centre = pose.surface - pose.axis * front
    x_core = params.pico_x + params.core_half_width
    drop = Pos(x_core - 2, centre.Y - r, -1) * Box(centre.X - x_core + 2, 2 * r, centre.Z + 1, align=CORNER)
    return cut + drop


def cavities(params: Params) -> Part:
    """Everything cut out of the solid shell from inside, in the left-hand frame."""
    thumb, *fingers = key_poses(params)
    c = params.clearance
    out = _core(params) + _troughs(params) + _cable_channel(params) + _thumb_cavity(params, thumb)
    for pose in fingers:
        out += _module_box(params, pose, c, length=_insertion_length(params, pose)) + _post(params, pose, c)
    return out


def shell(params: Params) -> Part:
    """The solid grip the hand rests on, with an opening for each flush cap. Prints rim-down."""
    # Where a switch pocket crosses the curved front at a shallow angle, the
    # STL mesher can leave a crack; a pocket a hundredth of a millimetre wider avoids it.
    for pocket_grow in (0.0, 0.01, -0.01, 0.02):
        part = _shell(params, pocket_grow)
        if mesh_closed(part):
            return part
    raise ValueError("the shell's mesh doesn't close; nudge a key's position or the clearance")


def mesh_closed(part: Part) -> bool:
    """Whether the mesh the STL export writes is closed: every edge shared by two triangles."""
    BRepTools.Clean_s(part.wrapped)  # drop meshes left over from earlier booleans
    vertices, triangles = part.tessellate(*STL_TOLERANCE)
    key = [tuple(round(c, 6) for c in v) for v in vertices]  # 4 places merges distinct vertices near the apex
    edges = Counter()
    for tri in triangles:
        ids = [key[i] for i in tri]
        if len(set(ids)) < 3:
            continue  # zero-area triangles at the poles of the curved surfaces
        for i in range(3):
            edges[frozenset((ids[i], ids[(i + 1) % 3]))] += 1
    return bool(edges) and all(n == 2 for n in edges.values())


def _shell(params: Params, pocket_grow: float) -> Part:
    left = key_poses(params)
    part = body_solid(params) & _above(0)
    part -= cavities(params)
    for pose in left:
        # As in _cap_left: where the well grazes a seam of the lofted body,
        # OpenCASCADE can return an invalid or empty solid; a well a
        # hundredth of a millimetre narrower or wider avoids it. Where faces
        # just touch it can leave an empty sliver, which _largest drops.
        for grow in (0.0, -0.01, 0.02, -0.02, 0.05):
            cut = part - _key_well(params, pose, grow, pocket_grow)
            pieces = [s for s in cut.solids() if s.volume > 0.1]
            if cut.is_valid and len(pieces) == 1 and cut.volume > part.volume / 2:
                cut = _largest(cut)
                break
        else:
            raise ValueError(f"the {pose.name} key's well doesn't cut cleanly; nudge its position or cap size")
        part = cut
    for point in _boss_points(params):
        part -= Pos(point) * Pos(0, 0, -1) * Cylinder(params.insert_hole / 2, params.insert_depth + 1, align=BOTTOM)
    part -= _led_cut(params)
    if params.heel_angle:
        part -= _heel_cut(params)
    part -= _rim(params, params.clearance)
    return _handed(params, _largest(part))


@cache
def _cap_wrap(params: Params, pose: KeyPose, name: str, well: bool = False) -> Part:
    """How far one part of a cap wraps round where the shell rolls away
    across it, or with ``well`` its well's floor. The well's floor runs
    ``well_depth`` and the roll under the centre line. A cap wraps down to
    ``clearance`` above that floor, less what the floor would meet as the
    paddle and flexure turn about the hinge to the stop, so a cap gives up
    width only where its press needs the room. The paddle also gives up what
    would meet its switch at the stop (``_switch_keep_out``)."""
    depth = well_depth(params, pose)
    if name == "anchor":
        tab = _anchor_depth(params, pose)
        below = max(depth, tab) + params.anchor_roll
        return _cap_floor(params, pose, below if well else below - params.clearance)
    below = depth + params.cap_roll_for(pose.name)
    if well:
        return _cap_floor(params, pose, below)
    floor = _cap_floor(params, pose, below - params.clearance)
    point, direction = _press_axis(params, pose)
    stop = _stop_angle(params, pose)
    wrap = floor
    for step in range(1, PRESS_STEPS + 1):
        wrap &= floor.rotate(Axis(point, direction), -stop * step / PRESS_STEPS)
    return wrap - _switch_keep_out(params, pose) if name == "paddle" else wrap


PRESS_STEPS = 4  # positions between rest and the stop that a wrapping cap keeps clear of its well's floor


STOP_PAD_LIFT = 0.5  # mm the stop pad keeps above its switch's pocket
STOP_PAD_STEPS = 8  # press positions the stop pad keeps clear of its well's floor


def _stop_angle(params: Params, pose: KeyPose, travel: float | None = None) -> float:
    """How far, in degrees, a cap turns about its hinge before its stop pad lands."""
    travel = params.cap_stop if travel is None else travel
    return math.degrees(math.asin(min(1.0, travel / _lever(params, pose))))


@cache
def _stop_pad(params: Params, pose: KeyPose) -> Part:
    """A pad under the paddle's fingertip end, from the cap down to its
    well's floor turned back up about the hinge by the stop angle. It lands
    on that floor once the stem has moved ``cap_stop``, so the cap never
    swings as far as the room the shell leaves for it."""
    width, tip, _ = params.cap_reach(pose.name)
    h = _hinge_sign(pose)
    length = params.stop_pad_length
    span = width - 2 * params.cap_corner
    footprint = Pos(0, -h * (tip - params.cap_corner - length / 2), -40) * Box(span, length, 60, align=BOTTOM)
    footprint = pose.plane * footprint
    near = pose.plane * Pos(0, -h * tip / 2, -40) * Box(width + 10, tip + 10, 60, align=BOTTOM)
    floor = (near & body_solid(params)) - _key_well(params, pose)
    # The well's floor meets the switch pocket's top in a sharp corner that
    # the pad could slip past between press positions, so the pad treats the
    # pocket as solid up to a little above its top and lands beside it.
    pocket = params.switch_clip_clearance + 2 * params.clearance
    floor += pose.plate * Box(pocket, pocket, params.switch_housing_height + STOP_PAD_LIFT, align=BOTTOM)
    point, direction = _press_axis(params, pose)
    under = body_solid(params, params.cap_proud - params.cap_thickness / 2)
    pad = footprint & under & _cap_wrap(params, pose, "paddle")
    for step in range(1, STOP_PAD_STEPS + 1):
        angle = _stop_angle(params, pose, params.cap_stop * step / STOP_PAD_STEPS)
        pad -= floor.rotate(Axis(point, direction), -angle)
    return _largest(pad)


@cache
def _switch_keep_out(params: Params, pose: KeyPose, bore: bool = True) -> Part:
    """Where a resting paddle would meet its switch at the stop: the module's
    lip and the switch housing, less the pusher's bore (with ``bore``), turned back up about
    the hinge. Where the shell rolls away steeply the paddle's sides give up
    only this corner and keep the rest of their width. Keys in
    ``own_module_keys`` trim their module's lip instead (``module_for``)."""
    c = params.clearance
    side = params.switch_clip_clearance
    housing = Box(side, side, params.switch_housing_height, align=BOTTOM)
    hole = Cylinder(params.pusher_diameter / 2 + PUSHER_SWING + c, 2 * params.switch_housing_height)
    block = housing - hole if bore else housing
    if pose.name not in params.own_module_keys:
        lip = Box(params.module_width + 2 * c, params.module_lip_length + 2 * c, params.module_depth, align=TOP)
        block += Pos(0, 0, c) * lip
    block = pose.plate * block
    point, direction = _press_axis(params, pose)
    return block.rotate(Axis(point, direction), -_stop_angle(params, pose))


def _cap_left(params: Params, pose: KeyPose, moving: bool = False) -> Part:
    """One cap in the left-hand frame: the paddle with its pusher, the
    flexure strip and the anchor tab. ``moving``: the paddle and pusher only."""
    proud, t = params.cap_proud, params.cap_thickness
    layers = {
        "paddle": body_solid(params, proud) - body_solid(params, proud - t),
        "flexure": body_solid(params, proud) - body_solid(params, proud - params.flexure_thickness),
        "anchor": body_solid(params, proud) - body_solid(params, proud - _anchor_depth(params, pose)),
    }
    if params.cap_dish:
        layers["paddle"] -= _dish(params, pose)
    cap = None
    for name in ("paddle",) if moving else CAP_PARTS:
        floor = _cap_wrap(params, pose, name)
        # Where the prism grazes a seam of the lofted body, OpenCASCADE can
        # return an invalid solid; an outline a hundredth of a millimetre
        # smaller avoids it.
        for shrink in (0.0, 0.01, 0.02, 0.05):
            region = _cap_region(params, pose, name, -shrink)
            try:
                piece = layers[name] & region & floor
                if name == "paddle":
                    piece = _union(piece, _stop_pad(params, pose) & region, slack=1.0)
            except ValueError:
                continue
            if not piece.is_valid:
                piece = piece.fix()
            if piece.is_valid and piece.solids():
                piece = _near(params, pose, name, piece)
                break
        else:
            raise ValueError(f"the {pose.name} cap's {name} doesn't cut cleanly; nudge its position or size")
        cap = piece if cap is None else cap + piece
    # The pusher, cut off inside the cap. Where the cylinder's seam lines up
    # with one of the lofted body's, OpenCASCADE can return an empty
    # intersection; turning the cylinder about its axis moves the seam.
    for turn in (0, 7, 13, 29):
        pusher = pose.plate * Pos(0, 0, params.switch_stem_height) * Rot(0, 0, turn)
        pusher *= Cylinder(params.pusher_diameter / 2, pose.plate_depth, align=BOTTOM)
        pusher &= body_solid(params, proud - t / 2)
        if pusher.solids() and pusher.volume > 0:
            break
    else:
        raise ValueError(f"the {pose.name} cap's pusher doesn't cut cleanly; nudge its position or size")
    cap += pusher
    if not moving:
        bore = _counterbore(params, params.m2_clearance, params.m2_head, params.m2_head_height)
        cap -= _anchor_frame(params, pose) * Pos(0, 0, params.anchor_thickness) * bore
    return _largest(cap)


@cache
def _dish(params: Params, pose: KeyPose) -> Part:
    """A long cylinder lying along the paddle's top, ``cap_dish`` into it at
    the centre line and meeting the top at the cap's edges, so the digit
    settles into a shallow channel. It follows the shell's curve along the
    cap and fades out before the flexure, so the top runs on level there."""
    width, tip, back = params.cap_reach(pose.name)
    depth, fade = params.cap_dish, params.cap_dish_fade
    radius = ((width / 2) ** 2 + depth**2) / (2 * depth)
    h = _hinge_sign(pose)
    body = Body.of(params)
    steps = 24
    centres = []
    for k in range(steps + 1):
        v = -tip - 3 + (tip + 3 + back) * k / steps
        at = pose.surface + pose.along * (h * v)
        point = at - pose.axis * _top_down(body, at, -pose.axis)
        # Square to the surface itself, which can lean across the press axis.
        sink = depth * min(1.0, max(0.0, (back - v) / fade))
        centres.append(point + body.normal(point) * (params.cap_proud + radius - sink))
    # A smooth loft through circles square to the run of the centres.
    sections = []
    for k, centre in enumerate(centres):
        run = centres[min(k + 1, steps)] - centres[max(k - 1, 0)]
        across = pose.x_dir - run.normalized() * pose.x_dir.dot(run.normalized())
        sections.append(Plane(origin=centre, x_dir=across, z_dir=run) * Circle(radius))
    tube = loft(sections)
    return tube if tube.volume > 0 else Part(tube.wrapped.Reversed())


def _press_axis(params: Params, pose: KeyPose) -> tuple:
    """The hinge line, in the left-hand frame: a point on it and its direction,
    turning the cap's switch end down for a positive angle."""
    _, _, back = params.cap_reach(pose.name)
    b = back + params.flexure_length / 2
    at = pose.plane.from_local_coords((0, _hinge_sign(pose) * b, 0))
    top = Body.of(params, params.cap_proud - params.flexure_thickness / 2)
    point = top.hit(Vector(*at) - pose.axis * 30, pose.axis)
    direction = pose.x_dir * _hinge_sign(pose)
    return point, direction


def pressed(params: Params, name: str, part: Part, travel: float) -> Part:
    """``part`` turned about the cap's hinge until its pusher has moved ``travel`` down the switch."""
    pose = next(p for p in key_poses(params) if p.name == name)
    point, direction = _press_axis(params, pose)
    angle = math.degrees(math.asin(min(1.0, travel / _lever(params, pose))))
    if params.mirrored:
        point, direction, angle = _mirror_vector(point), _mirror_vector(direction), -angle
    return part.rotate(Axis(point, direction), angle)


HINGE_TEST_KEY = "middle"
HINGE_TEST_MARGIN = 4.0  # solid kept round the key's cap, module and post in the test slices


def _hinge_test_box(params: Params) -> Part:
    """A tall box round the test key's cap, module and post, from above."""
    pose = next(p for p in key_poses(params) if p.name == HINGE_TEST_KEY)
    c = params.clearance
    reach = _cap_left(params, pose) + _module_box(params, pose, c) + _post(params, pose)
    box = _handed(params, reach).bounding_box()
    m = HINGE_TEST_MARGIN
    size = Vector(box.size.X + 2 * m, box.size.Y + 2 * m, BIG)
    return Pos(box.center().X, box.center().Y, 0) * Box(size.X, size.Y, size.Z)


def hinge_test(params: Params) -> Part:
    """A slice of the real shell round the middle finger's key: its cap well,
    switch pocket, module tunnel and anchor insert, at the shell's own curve
    and slope. With ``hinge_test_base`` under it, a key module and a real
    middle cap, it tries the flexure before the whole shell prints. Prints
    rim-down, like the shell."""
    return _largest(shell(params) & _hinge_test_box(params))


def hinge_test_base(params: Params) -> Part:
    """The matching slice of the base, with the module's post and the locating
    rim. The shell slice sits on it; a press loads both parts against the
    desk, so they need no screws. Prints flat, like the base."""
    return _largest(base(params) & _hinge_test_box(params))


INSERT_TEST_STEPS = (-0.1, 0.0, 0.1)  # hole sizes tried round each insert hole, from the notched end
INSERT_TEST_SIZE = (30.0, 22.0)
INSERT_TEST_PITCH = 9.0


def _insert_test_outline(height: float) -> Part:
    """The coupon's footprint, with a corner notch at the end of the smallest holes."""
    x, y = INSERT_TEST_SIZE
    block = Box(x, y, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return block - Pos(-x / 2, -y / 2, 0) * Rot(0, 0, 45) * Box(4, 4, 3 * height)


def _insert_test_spots() -> list:
    """(x, y, row) of each hole: M2 at the front row, M3 at the back."""
    _, y = INSERT_TEST_SIZE
    return [((i - 1) * INSERT_TEST_PITCH, sign * y / 4, row, step)
            for row, sign in (("m2", -1), ("m3", 1)) for i, step in enumerate(INSERT_TEST_STEPS)]


def insert_test(params: Params) -> Part:
    """A block with the M2 and M3 heat-set insert holes, each a little under,
    at and over its size, to try the inserts before a large print. Prints
    holes up."""
    height = params.insert_depth + 1.5
    part = _insert_test_outline(height)
    for x, y, row, step in _insert_test_spots():
        hole, depth = (params.m2_insert_hole, params.m2_insert_depth) if row == "m2" else (
            params.insert_hole, params.insert_depth)
        part -= Pos(x, y, height - depth) * Cylinder((hole + step) / 2, depth + 1, align=BOTTOM)
    return part


def insert_test_plate(params: Params) -> Part:
    """The plate the screws pass through into ``insert_test``: as thick as a
    cap's tab over the M2 holes and as the base over the M3 holes, with the
    same counterbores, so the real screws show whether their length suits.
    Prints flat, counterbores up."""
    x, y = INSERT_TEST_SIZE
    part = _insert_test_outline(params.base_thickness)
    m2_half = Box(x + 1, y / 2 + 0.01, BIG, align=(Align.CENTER, Align.CENTER, Align.MIN))
    part -= Pos(0, -y / 4, params.anchor_thickness) * m2_half
    m2 = (params.anchor_thickness, (params.m2_clearance, params.m2_head, params.m2_head_height))
    m3 = (params.base_thickness, (params.m3_clearance, params.m3_head, params.m3_head_height))
    for sx, sy, row, _ in _insert_test_spots():
        top, screw = m2 if row == "m2" else m3
        part -= Pos(sx, sy, top) * _counterbore(params, *screw)
    return part


def cap(params: Params, name: str, moving: bool = False) -> Part:
    """One long cap in place. ``moving``: the paddle and pusher only."""
    pose = next(p for p in key_poses(params) if p.name == name)
    return _handed(params, _cap_left(params, pose, moving))


def caps(params: Params, moving: bool = False) -> dict:
    """The five long caps in place, by key name. ``moving``: the paddles and pushers only."""
    return {pose.name: cap(params, pose.name, moving) for pose in key_poses(params)}


def cap_print(params: Params, name: str) -> Part:
    """One cap stood on its side for printing, so the flexure's layers run along the strip."""
    pose = next(p for p in key_poses(params) if p.name == name)
    local = pose.plane.location.inverse() * _cap_left(params, pose)
    flat = Rot(0, -90, 0) * local
    box = flat.bounding_box()
    placed = Pos(-box.center().X, -box.center().Y, -box.min.Z) * flat
    return _handed(params, placed)


@cache
def module_for(params: Params, name: str) -> Part:
    """The key module for one key, in its local frame. A key in
    ``own_module_keys`` gets its own: the lip's corner where the shell rolls
    away under the cap's side is trimmed clear of the cap all along its press.
    That corner sits under the cap's well, so it seats against nothing, and
    the trim stays outside the plate round the switch's clips."""
    module = key_module(params)
    if name not in params.own_module_keys:
        return module
    pose = next(p for p in poses(params) if p.name == name)
    c, paddle = params.clearance, cap(params, name, moving=True)
    to_module = Pos(0, 0, -c) * pose.plate.inverse()
    for step in range(5):
        travel = (params.cap_stop + c) * step / 4
        module -= to_module * pressed(params, name, paddle, travel)
    return module


def key_module_print(params: Params, name: str | None = None) -> Part:
    """The key module leaning on its -Y end, resting on z = 0, ready to slice.
    It stands on two edges, the lip's and the floor's, with the plate at about
    58 degrees to the bed. The layers then run across the press of the switch
    rather than along it. The flattest overhangs slope about 32 degrees, steep
    enough to print without supports, so the plate's faces come out smooth."""
    lean = math.degrees(math.atan2(params.module_depth - params.switch_plate, params.module_seat))
    leaning = Rot(lean, 0, 0) * (key_module(params) if name is None else module_for(params, name))
    box = leaning.bounding_box()
    return Pos(-box.center().X, -box.center().Y, -box.min.Z) * leaning


# Base -----------------------------------------------------------------------


def _dovetail(params: Params, grow: float, y_from: float, y_to: float) -> Part:
    """A dovetail prism along Y, narrow at the base's bottom face, ``grow`` wider all round."""
    flank = math.tan(math.radians(params.rail_flank))
    h = params.rail_height + grow
    half = params.rail_width / 2 + grow
    pts = [(-half, 0), (half, 0), (half + h * flank, h), (-half - h * flank, h)]
    if grow > 0:  # a cutter: reach below the base, so no faces coincide
        pts = [(-half, -1), (half, -1), *pts[1:], pts[0]]
    profile = Plane.XZ * Polygon(*pts, align=None)
    prism = Pos(0, y_to, -params.base_thickness) * extrude(profile, y_to - y_from)
    return Pos(-params.rail_x, 0, 0) * prism + Pos(params.rail_x, 0, 0) * prism


def _rim_outline(params: Params, inset: float, z0: float, height: float) -> Part:
    """The body's outline at the top of the rim's groove, ``inset`` smaller,
    extruded up from z0. Taken that high, a flared side keeps a roof over the groove."""
    body = Body.of(params, -inset)
    z = params.locating_lip_height + params.clearance + params.locating_lip_roof
    thumb, pinky, front, back, centre = body.slice(z)
    at = Vector(centre.X, centre.Y, z0)
    points = _outline_points(thumb, front, body.square, at, 240, back, pinky, body.square_rear, body.spread)
    return Part(Compound([extrude(Face(Wire.make_polygon(points, close=True)), height)]).wrapped)


def _rim(params: Params, grow: float = 0.0) -> Part:
    """The base's locating rim, a wall that follows the outline just inside the
    shell's edge and guides the shell into place. ``grow`` > 0 gives the shell's
    groove for it. The rim is notched round each screw boss, so the groove keeps
    clear of the inserts."""
    inset, width = params.locating_lip_inset, params.locating_lip_width
    z0 = -1 if grow > 0 else 0  # a cutter reaches below the shell, so no faces coincide
    height = params.locating_lip_height + grow - z0
    outline = _rim_outline(params, inset - grow, z0, height)
    ring = outline - _rim_outline(params, inset + width + grow, z0 - 1, height + 2)
    if params.heel_angle:
        # Where the base ends at the rounded heel, the rim runs straight along
        # its edge, the same distance in, and joins the curved rim at each end.
        edge = _heel_base_end(params) - inset
        ring -= _heel_side(params, edge + grow)
        ring += (_heel_side(params, edge - width - grow) - _heel_side(params, edge + grow)) & outline
    gap = params.insert_hole / 2 + params.locating_lip_boss_gap - grow
    for point in _boss_points(params):
        ring -= Pos(point.X, point.Y, z0 - 1) * Cylinder(gap, height + 2, align=BOTTOM)
    return ring


def base(params: Params) -> Part:
    """The bottom plate: holds the Pico and the key modules, screws to the shell, takes a wedge. Prints flat."""
    c = params.clearance
    thumb, *fingers = key_poses(params)
    part = _footprint(params, 0, -params.base_thickness, params.base_thickness)
    # A module that reaches below the shell sits in a pocket with a floor.
    floor = _above(params.base_floor - params.base_thickness)
    for pose in fingers:
        part -= _module_seat(params, pose, c) & floor
    rim = _rim(params) - cavities(params) - _led_cut(params)
    for pose in fingers:
        rim -= _module_seat(params, pose, c)
    part += rim

    centre = _pico_centre(params)
    hx, hy = params.pico_holes[0] / 2, params.pico_holes[1] / 2
    for dx in (-hx, hx):
        for dy in (-hy, hy):
            at = Pos(centre.X + dx, centre.Y + dy, 0)
            part += at * Cylinder(params.pico_standoff_diameter / 2, params.pico_standoff, align=BOTTOM)
            depth = params.m2_insert_depth
            insert = Cylinder(params.m2_insert_hole / 2, depth, align=BOTTOM)
            part -= at * Pos(0, 0, params.pico_standoff - depth) * insert

    # A post that stands over the USB plug's channel is notched round it.
    for pose in fingers:
        part += _post(params, pose) - _cable_channel(params)
    part += thumb_block(params)

    bore = _counterbore(params, params.m3_clearance, params.m3_head, params.m3_head_height)
    for point in _boss_points(params):
        part -= Pos(point.X, point.Y, -params.base_thickness) * Rot(180, 0, 0) * bore

    part -= _dovetail(params, c, -params.body_rear_length - 5, params.rail_front_stop)
    if params.heel_angle:
        part -= _heel_cut(params)
        part -= _heel_side(params, _heel_base_end(params))
    return _handed(params, part)


def _heel_base_end(params: Params) -> float:
    """How far past the heel line the base reaches before the heel's curve leaves it too thin."""
    rise = params.base_thickness - params.heel_base_tip
    lo, hi = 0.0, BIG
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if _heel_rise(params, mid) < rise else (lo, mid)
    return lo


# Wedges ---------------------------------------------------------------------


def wedge_edge(params: Params, angle: float) -> float:
    """How high a wedge holds the heel line above the desk: just enough that
    the rounded heel touches the desk. Past ``heel_angle`` the heel's far
    edge would touch first, so it is kept ``heel_clearance`` above it."""
    if not angle or not params.heel_angle:
        return params.wedge_min_thickness
    a = math.radians(angle)
    if angle <= params.heel_angle:
        return params.heel_radius * (1 - math.cos(a))
    reach = _heel_reach(params)
    return reach * math.sin(a) - _heel_rise(params, reach) * math.cos(a) + params.heel_clearance


def placement(params: Params, angle: float) -> Location:
    """Moves the shell frame onto a wedge tilted by ``angle`` about the heel line, thumb side up."""
    at, u, _ = heel_line(params.with_(hand="left"))
    turn = math.degrees(math.atan2(-u.X, u.Y))  # from +Y to the line
    tilt = -angle
    if params.mirrored:
        at, turn, tilt = _mirror_vector(at), -turn, -tilt
    lift = Pos(at.X, at.Y, wedge_edge(params, angle))
    return lift * Rot(0, 0, turn) * Rot(0, tilt, 0) * Rot(0, 0, -turn) * Pos(-at)


def wedge(params: Params, angle: float) -> Part:
    """A tilt wedge with dovetail rails on top. Prints flat on its bottom."""
    left = params.with_(hand="left")
    loc = placement(left, angle)
    at, u, n = heel_line(left)
    # Vertical sides: the base's outline, up to the heel line, seen from above.
    outline = [p for p in _footprint_points(params, 0, -params.base_thickness)]
    keep = [(p - at).dot(n) >= 0 for p in outline]
    points = []
    for i, p in enumerate(outline):
        q = outline[(i + 1) % len(outline)]
        if keep[i]:
            points.append(p)
        if keep[i] != keep[(i + 1) % len(outline)]:
            dp, dq = (p - at).dot(n), (q - at).dot(n)
            points.append(p + (q - p) * (dp / (dp - dq)))
    flat = [loc * Pos(p) for p in points]
    flat = [Vector(f.position.X, f.position.Y, 0) for f in flat]
    height = wedge_edge(params, angle) + BIG / 4
    body = Part(Compound([extrude(Face(Wire.make_polygon(flat, close=True)), height)]).wrapped)
    body &= loc * _below(-params.base_thickness)
    rails = _dovetail(params, 0, -params.body_rear_length - 5, params.rail_front_stop - params.clearance)
    rails &= _footprint(params, 0, -BIG / 2, BIG)
    part = body + loc * rails
    if params.heel_angle or angle:
        # The thin end near the heel line is trimmed to a printable edge, rails too.
        thin = (params.wedge_tip - wedge_edge(params, angle)) / math.sin(math.radians(angle)) if angle else 0.0
        part -= loc * _heel_side(left, -max(0.0, thin))
    part &= _above(0)
    return _handed(params, part)


# Envelopes of bought parts, for clearance checks and renders -----------------


def pico_envelope(params: Params) -> Part:
    w, length, t = params.pico_size
    centre = _pico_centre(params)
    board = Pos(centre) * Box(w, length, t + params.pico_top_clearance, align=BOTTOM)
    usb = Pos(centre.X, _usb_front_y(params), centre.Z + t) * Box(
        params.pico_usb_width, params.pico_usb_overhang + 1, params.pico_usb_height,
        align=(Align.CENTER, Align.MAX, Align.MIN),
    )
    return _handed(params, board + usb)


def usb_plug_envelope(params: Params) -> Part:
    w, h = params.usb_plug_size
    w, h = w - 2 * params.clearance, h - 2 * params.clearance
    at = Pos(params.pico_x, _usb_front_y(params) + 0.5, _usb_axis_z(params))
    plug = at * Box(w, params.usb_plug_length, h, align=(Align.CENTER, Align.MIN, Align.CENTER))
    return _handed(params, plug)


def switch_envelopes(params: Params) -> list:
    """Each switch's top housing, above the plate."""
    size = params.switch_clip_clearance
    return [p.plate * Box(size, size, params.switch_housing_height, align=BOTTOM) for p in poses(params)]


def wiring_envelopes(params: Params) -> list:
    """Room at each socket channel's mouth, where the wires leave the module."""
    depth = params.module_depth - params.switch_plate
    lo, hi = params.module_socket_x
    room = Box(hi - lo, params.wire_clearance, depth, align=(Align.CENTER, Align.MIN, Align.MAX))
    return [p.plate * Pos((lo + hi) / 2, params.module_outer / 2, -params.switch_plate) * room for p in poses(params)]


def led_envelope(params: Params, wiring: bool = True) -> Part:
    """The status LED and, with ``wiring``, room for its leads behind it."""
    at = led_pose(params).plane.location
    body, flange, length = params.led
    diameter, room = params.led_wiring_room
    seat = _led_seat(params)
    tip = length - params.led_flange_thickness - seat  # the flange stops on the seat
    led = Pos(0, 0, tip) * Cylinder(body / 2, length - params.led_flange_thickness, align=TOP)
    led += Pos(0, 0, -seat) * Cylinder(flange / 2, params.led_flange_thickness, align=TOP)
    if wiring:
        led += Pos(0, 0, -seat - params.led_flange_thickness) * Cylinder(diameter / 2, room, align=TOP)
    return _handed(params, at * led)


def placed_modules(params: Params, module: Part = None) -> list:
    """Each key's module in place; ``module`` stands in for the shared one."""
    module = module if module is not None else key_module(params)
    own = params.own_module_keys
    return [p.plate * (module_for(params, p.name) if p.name in own else module) for p in poses(params)]


# Assembly -------------------------------------------------------------------

COLOURS = {
    "shell": (0.30, 0.55, 0.85),
    "base": (0.55, 0.55, 0.60),
    "wedge": (0.95, 0.65, 0.25),
    "key_module": (0.35, 0.75, 0.45),
    "cap": (0.92, 0.92, 0.88),
    "pico": (0.20, 0.50, 0.25),
    "usb_plug": (0.25, 0.25, 0.25),
    "led": (0.90, 0.25, 0.20),
}


def assembly(params: Params, angle: float = 0, explode: float = 0.0, extras: bool = True) -> list:
    """The parts in place on a wedge, as (name, part, colour) tuples.

    ``explode`` lifts the shell, caps and modules away from the base, in mm, to
    show how the parts go together. ``extras`` adds the bought parts as envelopes.
    """
    at = placement(params, angle)
    up = Pos(0, 0, explode)
    module = key_module(params)
    items = [
        ("wedge", wedge(params, angle), COLOURS["wedge"]),
        ("base", at * Pos(0, 0, explode * 0.3) * base(params), COLOURS["base"]),
        ("shell", at * up * shell(params), COLOURS["shell"]),
    ]
    the_caps = caps(params)
    for pose, placed in zip(poses(params), placed_modules(params, module)):
        down = Pos(*(pose.axis * -explode * 0.4))
        items.append((f"key_module_{pose.name}", at * up * down * placed, COLOURS["key_module"]))
        out = Pos(*(pose.axis * explode * 0.6))
        items.append((f"cap_{pose.name}", at * up * out * the_caps[pose.name], COLOURS["cap"]))
    if extras:
        items.append(("pico", at * Pos(0, 0, explode * 0.3) * pico_envelope(params), COLOURS["pico"]))
        plug = at * Pos(0, explode * 0.5, explode * 0.3) * usb_plug_envelope(params)
        items.append(("usb_plug", plug, COLOURS["usb_plug"]))
        items.append(("led", at * up * led_envelope(params, wiring=False), COLOURS["led"]))
    return items
