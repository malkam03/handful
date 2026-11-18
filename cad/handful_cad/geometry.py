"""The shell's outer surface, and where each key sits on it.

Everything here is for the left hand; ``parts`` mirrors the result for the
right hand. Coordinates: the origin is the centre of the shell's footprint on
top of the base, +Y points away from the user, +Z points up and the thumb is
on the +X side.

The body is a sheared superellipsoid: every horizontal slice is a superellipse,
the side profile is a superellipse (flatter on top than an ellipsoid), and the
slices lean backwards with height so the highest point sits behind the middle,
where the palm rests. The hand lies along the surface: the heel of the palm on
the desk behind the shell, the palm over the top, the fingers down the front.
Each finger key sits under that finger's fingertip pad, found by walking along
the surface from the back edge, and faces straight out of the surface there.
"""

import math
from dataclasses import dataclass, replace
from functools import cache

from build123d import Location, Plane, Vector

from .params import PAD_DEPTH, PAD_HEIGHT, PINKY_PAD_HEIGHT, Params

FINGERS = ("index", "middle", "ring", "pinky")


WIDEN_UNTIL = 0.75  # the outline stops widening this far towards the front edge: just past the fingertip pads


def widening(spread: float, t: float) -> float:
    """How much wider the outline is at ``t``, the fraction of the way to the
    front edge: it grows smoothly from the middle and levels off before the
    front, so the front is only as wide as the outer caps need."""
    u = min(max(t / WIDEN_UNTIL, 0.0), 1.0)
    return 1 + spread * u * u * (3 - 2 * u)


@dataclass(frozen=True)
class Body:
    """The shell's outer surface; ``grow`` offsets it outwards (negative: inwards).

    Each horizontal slice is a superellipse with its own reach in each
    direction. With height the slice centre leans back (``lean``) and towards
    the thumb (``crest``), so the highest point sits under the index
    knuckle. The thumb side falls steeply (``crown``), so the thumb rests on
    a near-vertical face; the pinky side reaches further (``a_pinky``) and
    falls gently (``pinky_crown``), so the hand rolls towards the desk on that
    side; its foot flares out (``pinky_flare``), so that side is a low,
    concave slope rather than a wall. The back reaches further (``b_rear``) and slopes gently down to the
    desk (``rear_crown``).
    """

    a: float
    b: float
    c: float
    crown: float
    square: float  # footprint exponent: 2 is an ellipse, higher is squarer
    lean: float  # slice centre moves this much in -Y per mm of height
    b_rear: float
    rear_crown: float
    a_pinky: float
    pinky_crown: float
    crest: float  # the top's offset towards the thumb
    pinky_flare: float = 0.0  # extra reach at the foot of the pinky side
    flare_height: float = 1.0  # the flare runs out at this height
    square_rear: float = 4.0  # footprint exponent behind the centre
    front_crown: float | None = None  # front profile exponent; lower is a longer, straighter ramp
    spread: tuple = (0.0, 0.0)  # the front half widens by these fractions on the thumb and pinky side

    @classmethod
    def of(cls, params: Params, grow: float = 0.0, spread: tuple | None = None) -> "Body":
        a, b, c = params.body_axes
        return cls(
            a + grow,
            b + grow,
            c + grow,
            params.body_crown,
            params.body_squareness,
            params.body_peak_shift / c,
            params.body_rear_length + grow,
            params.body_rear_crown,
            params.body_pinky_width + grow,
            params.body_pinky_crown,
            params.body_crest_shift,
            params.body_pinky_flare,
            params.body_pinky_flare_height,
            params.body_rear_squareness,
            params.body_front_crown,
            params.front_spread if spread is None else spread,
        )

    def centre_y(self, z: float) -> float:
        return -self.lean * z

    def centre_x(self, z: float) -> float:
        return self.crest * min(max(z / self.c, 0.0), 1.0)

    def _shrink(self, z: float, exponent: float) -> float:
        t = min(max(z / self.c, 0.0), 1.0)
        return (1 - t**exponent) ** (1 / exponent)

    def slice(self, z: float) -> tuple:
        """Reach towards the thumb, the pinky, the front and the back from the slice centre, and the centre."""
        side = self._shrink(z, self.crown)
        front = self._shrink(z, self.crown if self.front_crown is None else self.front_crown)
        cx = self.centre_x(z)
        thumb = (self.a - cx) * side
        # A convex wall that stops short of the outline, plus a concave foot
        # that flares out to it, as the MX Ergo's pinky side does.
        foot = (1 - min(max(z / self.flare_height, 0.0), 1.0)) ** 2
        pinky = (self.a_pinky - self.pinky_flare + cx) * self._shrink(z, self.pinky_crown) + self.pinky_flare * foot
        back = self.b_rear * self._shrink(z, self.rear_crown)
        return thumb, pinky, self.b * front, back, Vector(cx, self.centre_y(z), z)

    def value(self, p: Vector) -> float:
        """Negative inside, zero on the surface, positive outside."""
        if p.Z >= self.c:
            return p.Z - self.c + 1
        thumb, pinky, front, back, centre = self.slice(p.Z)
        if min(thumb, pinky, front, back) < 1e-9:
            return 1.0
        x, y = p.X - centre.X, p.Y - centre.Y
        n = self.square if y >= 0 else self.square_rear
        reach = thumb * widening(self.spread[0], y / front) if x >= 0 else pinky * widening(self.spread[1], y / front)
        return (abs(x / reach) ** n + abs(y / (front if y >= 0 else back)) ** n) ** (1 / n) - 1

    def normal(self, p: Vector) -> Vector:
        h = 1e-4
        grad = Vector(
            self.value(p + Vector(h, 0, 0)) - self.value(p - Vector(h, 0, 0)),
            self.value(p + Vector(0, h, 0)) - self.value(p - Vector(0, h, 0)),
            self.value(p + Vector(0, 0, h)) - self.value(p - Vector(0, 0, h)),
        )
        return grad.normalized()

    def hit(self, origin: Vector, direction: Vector) -> Vector:
        """Where a ray from inside the body leaves it."""
        direction = direction.normalized()
        lo, hi = 0.0, 4 * max(self.a, self.a_pinky, self.b, self.b_rear, self.c)
        for _ in range(60):
            mid = (lo + hi) / 2
            if self.value(origin + direction * mid) < 0:
                lo = mid
            else:
                hi = mid
        return origin + direction * lo


@dataclass(frozen=True)
class KeyPose:
    name: str
    surface: Vector  # point on the shell surface under the key centre
    normal: Vector  # outward surface normal there
    axis: Vector  # the switch's press axis, pointing out of the shell
    along: Vector  # across the axis, along the finger towards the palm
    plate_depth: float = 0.0  # surface to switch plate top, along the axis
    # The switch module's along, where the cap turns away from it about the
    # press axis (the thumb's); None: the module lines up with the cap.
    module_along: Vector | None = None

    @property
    def x_dir(self) -> Vector:
        return self.along.cross(self.axis)

    @property
    def module_x_dir(self) -> Vector:
        return (self.module_along or self.along).cross(self.axis)

    @property
    def plane(self) -> Plane:
        """The key frame at the surface: z along the press axis, y along the finger."""
        return Plane(origin=self.surface, x_dir=self.x_dir, z_dir=self.axis)

    @property
    def plate(self) -> Location:
        """The switch plate's top face, recessed below the surface."""
        origin = self.surface - self.axis * self.plate_depth
        return Plane(origin=origin, x_dir=self.module_x_dir, z_dir=self.axis).location


def _squared(along: Vector, axis: Vector) -> Vector:
    return (along - axis * along.dot(axis)).normalized()


def cap_depth(params: Params, pose: KeyPose, samples: int = 11) -> float:
    """How far below the key centre, along the axis, the cap's underside
    reaches over the switch housing, once pressed to its stop: the pusher on
    the housing, ``press_stop`` down at the switch and further towards the
    digit's tip, as the cap turns about its hinge. Where the shell rolls away
    across the cap, the cap stops ``params.cap_roll_for(key)`` under its centre line."""
    surface = Body.of(params)
    under = Body.of(params, grow=-(params.cap_thickness - params.cap_proud))
    deepest = 0.0
    hinge = -1 if pose.name == "thumb" else 1
    lever = params.cap_reach(pose.name)[2] + params.flexure_length / 2
    width = length = params.switch_clip_clearance
    # Over the housing, square to the module, which the cap may turn away from.
    x_dir, along = pose.module_x_dir, pose.module_along or pose.along
    for j in range(samples):
        for i in range(samples):
            u = (i / (samples - 1) - 0.5) * width
            w = (j / (samples - 1) - 0.5) * length
            point = pose.surface + x_dir * u + along * w
            v = (point - pose.surface).dot(pose.along)
            floor = _top_down(surface, pose.surface + pose.along * v, -pose.axis)
            floor += params.cap_thickness + params.cap_roll_for(pose.name)
            drop = params.press_stop * (lever - hinge * v) / lever
            depth = min(floor, _top_down(under, point, -pose.axis))
            deepest = max(deepest, depth + drop)
    return deepest


def _top_down(body: Body, point: Vector, down: Vector, step: float = 0.5, reach: float = 40.0) -> float:
    """How far from ``point`` along ``down`` the line first enters ``body``, coming from outside."""
    start = point - down * 10
    s = 0.0
    while body.value(start + down * s) >= 0:
        s += step
        if s > reach:
            return reach - 10
    lo, hi = s - step, s
    for _ in range(30):
        mid = (lo + hi) / 2
        if body.value(start + down * mid) >= 0:
            lo = mid
        else:
            hi = mid
    return hi - 10


def _recessed(params: Params, pose: KeyPose) -> KeyPose:
    """Sets the plate depth so the cap's pusher rests on the switch stem and
    the pressed cap clears the switch housing."""
    on_stem = params.cap_thickness - params.cap_proud + params.switch_stem_height
    clear = cap_depth(params, pose) + params.switch_housing_height + params.cap_travel_margin
    return replace(pose, plate_depth=max(on_stem, clear))


@cache
def _meridian(body: Body, x: float, y: float = 0.0, heading: float = 0.0, samples: int = 600) -> tuple:
    """The surface in the vertical plane through (x, y) at ``heading`` degrees
    from +Y towards -X, from the back edge over the top to the front edge.

    Returns the points and the distance walked along the surface to each one.
    """
    h = Vector(-math.sin(math.radians(heading)), math.cos(math.radians(heading)), 0)
    cy = body.centre_y(body.c * 0.3)
    centre = Vector(x, y, 0) + h * ((cy - y) / h.Y)
    points, walked = [], [0.0]
    for i in range(samples + 1):
        angle = math.pi * (1 - i / samples)  # pi: straight back, 0: straight forward
        points.append(body.hit(centre, h * math.cos(angle) + Vector(0, 0, math.sin(angle))))
        if i:
            walked.append(walked[-1] + (points[-1] - points[-2]).length)
    return points, walked


def walk(body: Body, x: float, distance: float, y: float = 0.0, heading: float = 0.0) -> tuple:
    """Point and forward tangent after walking ``distance`` from the back edge, in the plane of ``_meridian``."""
    points, walked = _meridian(body, x, y, heading)
    for i in range(1, len(points)):
        if walked[i] >= distance:
            t = (distance - walked[i - 1]) / (walked[i] - walked[i - 1])
            point = points[i - 1] + (points[i] - points[i - 1]) * t
            return point, (points[i] - points[i - 1]).normalized()
    raise ValueError(f"the shell is too short for a {distance:.0f} mm walk at x = {x:.0f} mm")


def _distance_to(body: Body, x: float, y: float, heading: float, target: Vector) -> float:
    """How far from the back edge the meridian passes closest to ``target``."""
    points, walked = _meridian(body, x, y, heading)
    i = min(range(len(points)), key=lambda k: (points[k] - target).length)
    return walked[i]


def knuckle_xs(params: Params) -> list:
    """Across the hand, where each finger's knuckle lies, index to pinky: evenly over the hand breadth."""
    pitch = params.hand_breadth / 4
    return [params.finger_offset_x + (1.5 - i) * pitch for i in range(4)]


def fingertip_room(params: Params) -> tuple:
    """Across the hand, the least and most X a fingertip pad may take: the
    pinky's and the index's caps keep ``body_front_margin`` inside the body's
    outline where the pads lie, ``PAD_DEPTH`` of the way to the front edge
    and ``PAD_HEIGHT`` of the way up; the pinky's lower down the broad,
    gently sloping pinky side, at ``PINKY_PAD_HEIGHT``."""
    body = Body.of(params)
    n = params.body_squareness
    fit = (1 - PAD_DEPTH**n) ** (1 / n)
    margin = params.body_front_margin
    thumb, _, _, _, centre = body.slice(PAD_HEIGHT * params.body_height)
    high = centre.X + thumb * fit - margin - params.cap_widths[1] / 2
    _, pinky, _, _, centre = body.slice(PINKY_PAD_HEIGHT * params.body_height)
    low = centre.X - pinky * fit + margin + params.cap_widths[4] / 2
    return low, high


def fingertip_xs(params: Params) -> list:
    """Across the hand, where each fingertip pad lies, index to pinky.

    The pads sit ``fingertip_spacing`` apart, centred in the room the body
    has for them (see ``fingertip_room``), so the fan uses the broad, gently
    sloping pinky side. Where the spacings add up to more than the room,
    they shrink in proportion and the body keeps its size."""
    offsets = [0.0]
    for gap in params.fingertip_spacing:
        offsets.append(offsets[-1] - gap)
    low, high = fingertip_room(params)
    scale = min(1.0, (high - low) / -offsets[-1])
    middle = (low + high) / 2 - offsets[-1] * scale / 2
    return [middle + o * scale for o in offsets]


def knuckle_points(params: Params) -> list:
    """Each finger's knuckle on the shell's top, index to pinky."""
    body = Body.of(params)
    knuckles = params.palm_length - params.heel_overhang
    return [walk(body, x, knuckles + params.knuckle_offsets[i])[0] for i, x in enumerate(knuckle_xs(params))]


def finger_path(params: Params, i: int) -> tuple:
    """The plane finger ``i`` lies in, as (x, y, heading), and how far along it from the back edge the knuckle is.

    The finger runs over the surface from its knuckle, fanned out so its
    pad lands at its fingertip spacing across the hand.
    """
    body = Body.of(params)
    knuckle = knuckle_points(params)[i]
    reach = params.key_reach * params.middle_finger * params.finger_ratios[i]
    target = fingertip_xs(params)[i]
    heading = 0.0
    for _ in range(6):
        start = _distance_to(body, knuckle.X, knuckle.Y, heading, knuckle)
        point, _ = walk(body, knuckle.X, start + reach, knuckle.Y, heading)
        flat = math.hypot(point.X - knuckle.X, point.Y - knuckle.Y)
        error = math.degrees(math.asin(max(-1.0, min(1.0, (target - point.X) / flat))))
        if abs(error) < 0.01:
            break
        heading -= error
    return (knuckle.X, knuckle.Y, heading), start


def _finger_key(params: Params, body: Body, i: int) -> tuple:
    (x, y, heading), start = finger_path(params, i)
    reach = params.key_reach * params.middle_finger * params.finger_ratios[i]
    return walk(body, x, start + reach, y, heading)


@cache
def finger_poses(params: Params) -> list:
    """The finger keys, index to pinky, each under its fingertip pad.

    The fingers fan out from the knuckles, as a relaxed hand does, so the
    pads sit ``fingertip_spacing`` apart across the hand and each cap runs
    along its own finger.
    """
    body = Body.of(params)
    points = [_finger_key(params, body, i) for i in range(4)]
    normals = [body.normal(point) for point, _ in points]
    # The finger switches lean towards one shared press axis, so their
    # modules sit side by side under the curved front without running into each other.
    mean = sum(normals[1:], normals[0]).normalized()
    poses = []
    for name, (point, forward), normal, slant in zip(FINGERS, points, normals, params.cap_slant):
        axis = (normal * (1 - params.finger_axis_blend) + mean * params.finger_axis_blend).normalized()
        along = _squared(-forward, axis)
        if slant:
            # The cap turns about its fingertip: the tip stays, the switch
            # under the pad and the palm end swing towards the pinky.
            tip = params.cap_reach(name)[1]
            turn = math.radians(slant)
            turned = along * math.cos(turn) + along.cross(axis) * math.sin(turn)
            point = body.hit(point + (turned - along) * tip - axis * 30, axis)
            normal = body.normal(point)
            axis = (normal * (1 - params.finger_axis_blend) + mean * params.finger_axis_blend).normalized()
            along = _squared(turned, axis)
        poses.append(_recessed(params, KeyPose(name, point, normal, axis, along)))
    return poses


def side_pose(params: Params, name: str, y: float, z: float) -> KeyPose:
    """A key on the thumb side, at height ``z`` and ``y`` in front of the centre."""
    body = Body.of(params)
    point = body.hit(Vector(0, y, z), Vector(1, 0, 0))
    normal = body.normal(point)
    return KeyPose(name, point, normal, normal, _squared(Vector(0, 1, 0), normal))


def thumb_pose(params: Params) -> KeyPose:
    """The thumb presses straight sideways, along X, so its bay and the
    base's block are simple prisms however the side curves. Its cap turns
    ``thumb_cap_tilt`` about the thumb tip, the palm end up; the module
    stays level under the switch."""
    tilt = math.radians(params.thumb_cap_tilt)
    half = params.thumb_tip_length / 2
    y = params.thumb_y + half - half * math.cos(tilt)
    z = params.thumb_z + half * math.sin(tilt)
    pose = side_pose(params, "thumb", y, z)
    level = Vector(math.copysign(1.0, pose.normal.X), 0, 0)
    module = _squared(Vector(0, 1, 0), level)
    along = Vector(0, math.cos(tilt), -math.sin(tilt))
    return _recessed(params, replace(pose, axis=level, along=along, module_along=module))


def key_poses(params: Params) -> list:
    """All five keys, thumb first, in the firmware's button order."""
    return [thumb_pose(params), *finger_poses(params)]


def led_pose(params: Params) -> KeyPose:
    """The status LED on the thumb side."""
    return side_pose(params, "led", params.led_y, params.led_z)
