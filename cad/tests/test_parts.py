"""Checks that every part builds, prints as a closed solid and fits together.

Run from cad/ with ``.venv/bin/pytest``, which spreads the tests over every
core (pytest.ini), or one at a time with
``.venv/bin/python -m unittest discover -s tests -t .``. Set HANDFUL_PARAMS
to a hand file (see cad/hand.example.toml) to check the parts built for that hand instead of the defaults.
"""

import itertools
import math
import unittest

from build123d import Align, Box, Cylinder, GeomType, Pos, Vector

from handful_cad import parts
from handful_cad.geometry import Body, fingertip_room, fingertip_xs, key_poses, led_pose
from tests.partcache import BASE, HANDS, built, caps

EPS = 1e-3  # mm^3; touching faces count as no overlap
POCKETED = {"shell", "base", "hinge_test", "hinge_test_base"}  # parts holding key module pockets
PART_NAMES = tuple(built("left"))


def cases(**axes):
    """Run a test once for every combination of values, as separate tests
    named after them, so pytest can run them on different cores."""

    def mark(test):
        test.cases = axes
        return test

    return mark


class Case(unittest.TestCase):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for name, test in list(vars(cls).items()):
            axes = getattr(test, "cases", None)
            if axes is None:
                continue
            delattr(cls, name)
            for values in itertools.product(*axes.values()):
                kwargs = dict(zip(axes, values))

                def run(self, test=test, kwargs=kwargs):
                    test(self, **kwargs)

                label = "_".join(str(v) for v in values)
                run.__name__ = run.__qualname__ = f"{name}_{label}"
                run.__doc__ = test.__doc__
                setattr(cls, run.__name__, run)


def overlap(a, b) -> float:
    common = a & b
    return 0.0 if common is None else sum(s.volume for s in common.solids())


def is_watertight(part) -> bool:
    return parts.mesh_closed(part)


class PartsTest(Case):
    @cases(hand=HANDS, part=PART_NAMES)
    def test_every_part_is_one_valid_closed_solid(self, hand, part):
        solid = built(hand)[part]
        self.assertTrue(solid.is_valid)
        self.assertEqual(len(solid.solids()), 1)
        self.assertGreater(solid.volume, 0)
        self.assertTrue(is_watertight(solid))

    @cases(part=PART_NAMES)
    def test_right_hand_mirrors_left(self, part):
        left, right = built("left")[part], built("right")[part]
        if part in POCKETED:
            # the Choc socket sits off the switch centre, so its pockets turn
            # the same way in both hands instead of mirroring
            self.assertAlmostEqual(left.volume / right.volume, 1.0, delta=0.03)
        else:  # booleans on the mirrored, lofted body round off a few hundredths of a mm³
            self.assertAlmostEqual(left.volume / right.volume, 1.0, places=4)
        lb, rb = left.bounding_box(), right.bounding_box()
        if not part.startswith("key_module"):  # modules are turned round, not mirrored
            self.assertAlmostEqual(lb.min.X, -rb.max.X, places=3)
            self.assertAlmostEqual(lb.max.Y, rb.max.Y, places=3)

    def test_every_part_is_exported_resting_flat_on_the_bed(self):
        # The key module leans on two edges instead: see test_key_module_prints_leaning_on_its_end.
        printable = {name: part for name, part in built("left").items() if not name.startswith("key_module")}
        for name, part in printable.items():
            with self.subTest(part=name):
                low = part.bounding_box().min.Z  # slicers drop each part onto the bed
                bed = [f for f in part.faces().filter_by(GeomType.PLANE)
                       if abs(f.center().Z - low) < 1e-3 and f.normal_at().Z < -0.999]
                self.assertGreater(sum(f.area for f in bed), 20.0)

    def test_key_module_prints_leaning_on_its_end(self):
        printed = parts.key_module_print(BASE)
        self.assertAlmostEqual(printed.bounding_box().min.Z, 0.0, places=3)
        # It stands on two edges across the module, the lip's and the floor's.
        bed = {round(v.Y, 2) for v in printed.vertices() if v.Z < 1e-3}
        self.assertEqual(len(bed), 2)
        self.assertGreater(max(bed) - min(bed), 5.0)
        # The plate leans: its faces are neither flat nor upright.
        lean = math.atan2(BASE.module_depth - BASE.switch_plate, BASE.module_seat)
        normal = Vector(0, -math.sin(lean), math.cos(lean))  # the plate's top, turned
        self.assertTrue(any(f.normal_at().dot(normal) > 0.999 for f in printed.faces().filter_by(GeomType.PLANE)))
        # Nothing hangs flatter than 30 degrees, so no supports.
        for face in printed.faces().filter_by(GeomType.PLANE):
            if face.center().Z > 1e-3:
                self.assertGreater(face.normal_at().Z, -math.cos(math.radians(30)), face.center())


class KeyModuleTest(Case):
    def setUp(self):
        self.module = built("left")["key_module"]

    def test_own_modules_trim_only_the_lip_clear_of_the_clips(self):
        # The clips sit on the switch's +-Y faces, across its middle.
        clips = Box(BASE.switch_cutout - 1, BASE.module_outer, 2 * BASE.module_depth)
        for hand in HANDS:
            for name in BASE.own_module_keys:
                trimmed = built(hand)[f"key_module_{name}"]
                with self.subTest(hand=hand, key=name):
                    cut = self.module - trimmed
                    self.assertGreater(cut.volume, 1.0)
                    self.assertLess(overlap(cut, clips), EPS)
                    # Only the lip's top corner: the walls and floor stay whole.
                    self.assertGreater(cut.bounding_box().min.Z, -BASE.switch_plate - 0.5)

    def test_switch_cutout_takes_a_14_mm_switch(self):
        plate = BASE.switch_plate
        self.assertLess(overlap(self.module, Pos(0, 0, -plate / 2) * Box(14.0, 14.0, plate)), EPS)
        self.assertGreater(overlap(self.module, Pos(0, 0, -plate / 2) * Box(14.4, 14.4, plate)), EPS)

    def test_plate_is_choc_thickness_around_the_cutout(self):
        column = Pos(0, 7.4, 0) * Box(0.2, 0.2, 40)  # between the cutout and the clip room
        top = max((self.module & column).solids(), key=lambda s: s.bounding_box().max.Z)
        self.assertAlmostEqual(top.bounding_box().size.Z, BASE.switch_plate, places=3)

    def test_floor_sits_where_a_pcb_would(self):
        column = Pos(0, -7.0, 0) * Box(0.2, 0.2, 40)  # clear of every hole
        common = self.module & column
        tops = sorted(round(s.bounding_box().max.Z, 3) for s in common.solids())
        self.assertIn(-BASE.switch_plate_to_pcb, tops)

    def test_switch_pins_and_post_have_holes(self):
        for x, y in BASE.switch_pins:
            down_to_socket = BASE.switch_plate_to_pcb + BASE.pcb_thickness
            pin = Pos(x, y, 0) * Cylinder(1.4, down_to_socket, align=(Align.CENTER, Align.CENTER, Align.MAX))
            self.assertLess(overlap(self.module, pin), EPS)
        self.assertLess(overlap(self.module, Cylinder(BASE.switch_post_diameter / 2, 40)), EPS)

    def _socket(self, dy: float = 0.0, dz: float = 0.0):
        """The socket body and solder tabs where they sit under the switch."""
        (x0, y0), (x1, y1) = BASE.switch_pins
        mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
        top = -BASE.switch_plate_to_pcb - BASE.pcb_thickness
        t, half = BASE.socket_thickness, BASE.socket_tabs_width / 2
        body = Pos(mid_x, mid_y, top) * Box(*BASE.socket_body, t, align=(Align.CENTER, Align.CENTER, Align.MAX))
        tabs = Pos(mid_x - half, y0, top) * Box(2.0, 1.6, t, align=(Align.MIN, Align.CENTER, Align.MAX))
        tabs += Pos(mid_x + half, y1, top) * Box(2.0, 1.6, t, align=(Align.MAX, Align.CENTER, Align.MAX))
        return Pos(0, dy, dz) * (body + tabs)

    def test_socket_fits_in_its_channel(self):
        self.assertLess(overlap(self.module, self._socket()), EPS)

    def test_socket_slides_in_from_the_side(self):
        for dy in range(1, 20):
            self.assertLess(overlap(self.module, self._socket(dy=dy)), EPS)

    def test_skin_holds_the_socket_against_the_switch(self):
        self.assertGreater(overlap(self.module, self._socket(dz=-0.3)), EPS)

class TactileAdapterTest(Case):
    def setUp(self):
        self.adapter = built("left")["tactile_adapter"]
        self.module = built("left")["key_module"]
        self.seat = parts.tactile_seat(BASE)

    def _button(self, dz: float = 0.0, leg_pitch: float = 12.5):
        size, body = BASE.tactile_size, BASE.tactile_body_height
        button = Pos(0, 0, self.seat + dz) * Box(size, size, body, align=(Align.CENTER, Align.CENTER, Align.MIN))
        for sx, sy in itertools.product((-1, 1), repeat=2):
            leg = Pos(sx * BASE.tactile_legs[2] / 2, sy * leg_pitch / 2, self.seat + dz + 0.5)
            button += leg * Box(0.8, 0.8, 0.5 + BASE.tactile_leg_cut, align=(Align.CENTER, Align.CENTER, Align.MAX))
        return button

    def test_actuator_sits_just_under_the_pusher(self):
        self.assertAlmostEqual(self.seat + BASE.tactile_height, BASE.switch_stem_height - BASE.tactile_gap, places=6)
        self.assertLess(BASE.tactile_gap, BASE.tactile_travel)  # the cap still presses it

    def test_button_and_its_legs_fit(self):
        for pitch in BASE.tactile_legs[:2]:
            with self.subTest(pitch=pitch):
                button = self._button(leg_pitch=pitch)
                self.assertLess(overlap(button, self.adapter), EPS)
                self.assertLess(overlap(button, self.module), EPS)
        self.assertGreater(overlap(self._button(dz=-0.2), self.adapter), EPS)  # it rests on the seat

    def test_plug_fits_the_switch_hole_snugly(self):
        self.assertLess(overlap(self.adapter, self.module), EPS)
        self.assertGreater(overlap(Pos(0.2, 0, 0) * self.adapter, self.module), EPS)

    def test_fits_in_the_shells_switch_pocket(self):
        size = BASE.switch_clip_clearance
        room = Box(size, size, BASE.switch_housing_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
        above = self.adapter & Box(40, 40, 40, align=(Align.CENTER, Align.CENTER, Align.MIN))
        self.assertLess(above.volume - overlap(above, room), EPS)


class AssemblyTest(Case):
    @cases(hand=HANDS)
    def test_parts_do_not_collide(self, hand):
        params = BASE.with_(hand=hand)
        p = built(hand)
        modules = parts.placed_modules(params, p["key_module"])
        pico = parts.pico_envelope(params)
        led = parts.led_envelope(params)
        pairs = [
            ("shell", "base", p["shell"], p["base"]),
            ("pico", "shell", pico, p["shell"]),
            ("status LED", "shell", led, p["shell"]),
            ("status LED", "base", led, p["base"]),
            ("status LED", "pico", led, pico),
        ]
        for i, m in enumerate(modules):
            pairs.append((f"module {i}", "shell", m, p["shell"]))
            pairs.append((f"module {i}", "base", m, p["base"]))
            pairs.append((f"module {i}", "pico", m, pico))
            pairs.append((f"module {i}", "status LED", m, led))
            for j, other in enumerate(modules[i + 1 :], i + 1):
                pairs.append((f"module {i}", f"module {j}", m, other))
        for i, wires in enumerate(parts.wiring_envelopes(params)):
            pairs.append((f"wiring {i}", "pico", wires, pico))
            pairs.append((f"wiring {i}", "base", wires, p["base"]))
        placed = caps(hand)
        names = list(placed)
        for i, name in enumerate(names):
            pairs.append((f"cap {name}", "shell", placed[name], p["shell"]))
            for other in names[i + 1 :]:
                pairs.append((f"cap {name}", f"cap {other}", placed[name], placed[other]))
            pairs.append((f"cap {name}", "status LED", placed[name], led))
        for a_name, b_name, a, b in pairs:
            with self.subTest(hand=hand, a=a_name, b=b_name):
                self.assertLess(overlap(a, b), EPS)

    def test_socket_wires_reach_the_cavity(self):
        (x0, y0), (x1, y1) = BASE.switch_pins
        mid_x = (x0 + x1) / 2
        half = BASE.socket_tabs_width / 2
        z = -BASE.switch_plate_to_pcb - BASE.pcb_thickness - BASE.socket_thickness / 2
        end = BASE.module_outer / 2 + 2
        for hand in HANDS:
            params = BASE.with_(hand=hand)
            p = built(hand)
            for pose in parts.poses(params):
                for x, y in ((mid_x - half + 0.8, y0), (mid_x + half - 0.8, y1)):
                    along = Pos(x, y, z) * Box(1.0, end - y, 1.0, align=(Align.CENTER, Align.MIN, Align.CENTER))
                    wire = pose.plate * along
                    with self.subTest(hand=hand, key=pose.name, x=x):
                        self.assertLess(overlap(wire, p["shell"]), EPS)
                        self.assertLess(overlap(wire, pose.plate * p["key_module"]), EPS)

    @cases(hand=HANDS)
    def test_modules_are_seated_and_held_without_screws(self, hand):
        params = BASE.with_(hand=hand)
        p = built(hand)
        for pose, module in zip(parts.poses(params), parts.placed_modules(params, p["key_module"])):
            with self.subTest(hand=hand, key=pose.name):
                out = Pos(*(pose.axis * 0.3)) * module  # the lip stops on the shell's seat
                self.assertGreater(overlap(out, p["shell"]), EPS)
                down = Pos(*(pose.axis * -0.3)) * module  # a post or the thumb block holds it there
                self.assertGreater(overlap(down, p["base"]), EPS)

    @cases(hand=HANDS)
    def test_modules_go_in_from_below(self, hand):
        params = BASE.with_(hand=hand)
        shell = built(hand)["shell"]
        # Each module goes in with its switch clipped in: the top housing and the stem.
        up = (Align.CENTER, Align.CENTER, Align.MIN)
        switch = Box(BASE.switch_clip_clearance, BASE.switch_clip_clearance, BASE.switch_housing_height, align=up)
        switch += Cylinder(2.5, BASE.switch_stem_height, align=up)
        for pose, module in zip(parts.poses(params), parts.placed_modules(params, built(hand)["key_module"])):
            module += pose.plate * switch
            # Fingers slide in along their press axis; the thumb rises straight up into its bay.
            path = Vector(0, 0, -1) if pose.name == "thumb" else -pose.axis
            height = module.bounding_box().max.Z
            steps = int(height / abs(path.Z)) + 2
            for d in range(0, steps, 2):
                with self.subTest(hand=hand, key=pose.name, d=d):
                    self.assertLess(overlap(Pos(*(path * d)) * module, shell), EPS)

    @cases(hand=HANDS)
    def test_thumb_module_is_held_every_way(self, hand):
        params = BASE.with_(hand=hand)
        p = built(hand)
        module = parts.placed_modules(params, p["key_module"])[0]
        both = p["shell"] + p["base"]
        for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            with self.subTest(hand=hand, direction=v):
                self.assertGreater(overlap(Pos(*(Vector(*v) * 0.3)) * module, both), EPS)

    def test_inner_cavities_keep_a_skin(self):
        params = BASE
        inner = parts._core(params) + parts._troughs(params)
        outside = inner - parts.body_solid(params, -params.skin)
        self.assertLess(sum(s.volume for s in outside.solids()), 1.0)

    def test_base_rim_guides_the_shell(self):
        params = BASE
        p = built("left")
        rim = parts._rim(params)
        self.assertGreater(rim.volume, 500)  # a wall round the whole outline, not a stub
        self.assertGreater(overlap(rim, p["base"]) / rim.volume, 0.95)  # cut back round the cavities
        self.assertLess(overlap(rim, p["shell"]), EPS)  # it sits in the shell's groove
        play = params.clearance + 0.2
        for dx, dy in ((play, 0), (-play, 0), (0, play), (0, -play)):
            with self.subTest(shift=(dx, dy)):  # and the groove holds it, so it locates the shell
                self.assertGreater(overlap(Pos(dx, dy, 0) * rim, p["shell"]), EPS)

    def test_base_bottom_is_closed_under_the_modules(self):
        params = BASE
        base = built("left")["base"]
        bottom = -params.base_thickness
        slab = parts._footprint(params, -1, bottom, params.base_floor)
        modules = parts.placed_modules(params, built("left")["key_module"])
        for pose, module in zip(key_poses(params)[1:], modules[1:]):
            with self.subTest(key=pose.name):
                self.assertGreaterEqual(module.bounding_box().min.Z, bottom + params.base_floor)
                under = parts._module_seat(params, pose, params.clearance) & slab
                if under.solids():  # a pocket reaching down to the floor keeps it
                    self.assertAlmostEqual(overlap(under, base), under.volume, delta=0.01)

    @cases(hand=("left", "right"))
    def test_heel_clears_the_modules(self, hand):
        params = BASE.with_(hand=hand)
        cut = parts._heel_cut(params)
        trim = cut + parts._heel_side(params, parts._heel_base_end(params))
        above_desk = parts._above(-params.base_thickness)
        c = params.clearance
        for pose in key_poses(params)[1:]:
            with self.subTest(key=pose.name):  # a skin stays between the pocket and the rounding
                self.assertLess(overlap(parts._module_seat(params, pose, c + params.skin), cut), EPS)
                tunnel = parts._module_box(params, pose, c, length=parts._insertion_length(params, pose))
                self.assertLess(overlap(tunnel & above_desk, trim), EPS)  # the tunnel stays closed
                self.assertLess(overlap(parts._post(params, pose), trim), EPS)

    def test_shell_screw_bosses_keep_their_walls(self):
        params = BASE
        shell = built("left")["shell"]
        for point in parts._boss_points(params):
            with self.subTest(point=point):
                r = params.insert_hole / 2
                wall = Pos(point.X, point.Y, 0) * (
                    Cylinder(r + params.insert_wall, params.insert_depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
                    - Cylinder(r + 0.05, 40)
                )
                self.assertGreater(overlap(wall, shell) / wall.volume, 0.99)

    @cases(hand=HANDS)
    def test_usb_cable_exits_nearly_level_at_every_tilt(self, hand):
        params = BASE.with_(hand=hand)
        p = built(hand)
        plug = parts.usb_plug_envelope(params)
        self.assertLess(overlap(plug, p["shell"]), EPS)
        self.assertLess(overlap(plug, p["base"]), EPS)
        for angle in params.wedge_angles:
            with self.subTest(hand=hand, angle=angle):
                at = parts.placement(params, angle)
                direction = at * Pos(0, 1, 0)
                origin = at * Pos(0, 0, 0)
                axis = direction.position - origin.position
                # The heel line runs nearly along the length, so the cable stays nearly level.
                self.assertLess(abs(axis.Z), math.sin(math.radians(angle / 2)) + 1e-6)
                self.assertLess(overlap(at * plug, p[f"wedge_{angle:02d}"]), EPS)
                self.assertGreater((at * plug).bounding_box().min.Z, 0)

    @cases(hand=HANDS)
    def test_base_sits_on_each_wedge(self, hand):
        params = BASE.with_(hand=hand)
        p = built(hand)
        for angle in params.wedge_angles:
            with self.subTest(hand=hand, angle=angle):
                at = parts.placement(params, angle)
                wedge = p[f"wedge_{angle:02d}"]
                self.assertLess(overlap(at * p["base"], wedge), EPS)
                pressed = at * Pos(0, 0, -0.3) * p["base"]
                self.assertGreater(overlap(pressed, wedge), EPS)

    @cases(hand=HANDS)
    def test_wedges_print_without_supports(self, hand):
        for angle in BASE.wedge_angles:
            wedge = built(hand)[f"wedge_{angle:02d}"]
            for face in wedge.faces():
                if face.geom_type != GeomType.PLANE or face.bounding_box().max.Z < 1e-6:
                    continue  # the bed face; the sides are vertical
                down = -face.normal_at().Z
                with self.subTest(hand=hand, angle=angle, face=face.center()):
                    self.assertLessEqual(down, math.cos(math.radians(45)) + 1e-6)

    def test_tilt_raises_the_thumb_side(self):
        for hand, thumb_side in (("left", 1), ("right", -1)):
            params = BASE.with_(hand=hand)
            _, _, inward = parts.heel_line(params.with_(hand="left"))
            inward = Vector(thumb_side * inward.X, inward.Y, 0)
            for angle in (10, 20):
                at = parts.placement(params, angle)
                rise = (at * Pos(inward)).position - (at * Pos(0, 0, 0)).position
                self.assertAlmostEqual(rise.Z, math.sin(math.radians(angle)), places=6)
                x_axis = (at * Pos(thumb_side, 0, 0)).position - (at * Pos(0, 0, 0)).position
                self.assertGreater(x_axis.Z, 0)

    @cases(hand=HANDS)
    def test_heel_rests_on_the_desk_on_every_wedge(self, hand):
        params = BASE.with_(hand=hand)
        p = built(hand)
        for angle in params.wedge_angles:
            at = parts.placement(params, angle)
            for name in ("shell", "base"):
                lowest = min(v.Z for v in (at * p[name]).vertices())
                with self.subTest(hand=hand, angle=angle, part=name):
                    self.assertGreater(lowest, -0.01)  # nothing below the desk
            if angle:
                with self.subTest(hand=hand, angle=angle, part="heel"):
                    # the rounded heel touches the desk, so the wrist corner rests on it
                    lowest = min(v.Z for name in ("shell", "base") for v in (at * p[name]).vertices())
                    self.assertLess(lowest, 0.3)

    @cases(hand=HANDS)
    def test_base_sits_flat_without_a_wedge(self, hand):
        base = built(hand)["base"]
        bottom = [f for f in base.faces() if f.geom_type == GeomType.PLANE and f.normal_at().Z < -0.999]
        lowest = min(f.center().Z for f in bottom)
        self.assertAlmostEqual(lowest, -BASE.base_thickness, places=6)
        self.assertGreater(sum(f.area for f in bottom if abs(f.center().Z - lowest) < 1e-6), 3000)


def _pose(params, name):
    return next(p for p in parts.poses(params) if p.name == name)


class CapTest(Case):
    @cases(hand=HANDS)
    def test_caps_are_the_set_width_and_length(self, hand):
        for pose in parts.poses(BASE.with_(hand=hand)):
            size = built(hand)[f"cap_{pose.name}"].bounding_box().size
            width, tip, back = BASE.cap_reach(pose.name)
            length = tip + back + BASE.flexure_length + BASE.anchor_length
            with self.subTest(hand=hand, key=pose.name):
                # Where the shell rolls away under a cap's corners, the cap narrows and follows the curve.
                self.assertLessEqual(size.Z, width + 0.01)
                self.assertGreater(size.Z, 0.6 * width)
                self.assertLessEqual(size.Y, length + 0.01)
                self.assertGreater(size.Y, 0.8 * length)

    def test_cap_top_over_the_switch_is_proud_less_the_dish(self):
        for pose in key_poses(BASE):
            cap = caps("left")[pose.name]
            # Points, not boxes: a tiny box against a thin curved cap can
            # come back whole from OpenCASCADE's boolean. The offset body's
            # surface wanders a little, so the cap's top is checked to within 0.3.
            # Over the switch the top is dished by cap_dish.
            top = BASE.cap_proud - BASE.cap_dish
            proud = pose.surface + pose.normal * (top - 0.3)
            above = pose.surface + pose.normal * (top + 0.3)
            with self.subTest(key=pose.name):
                self.assertTrue(cap.is_inside(proud))
                self.assertFalse(cap.is_inside(above))

    def test_pressed_caps_clear_shell_switch_and_neighbours(self):
        # The stop pad meets the well's floor at cap_stop; nothing may touch before then.
        travel = BASE.cap_stop - 0.01
        for hand in HANDS:
            params = BASE.with_(hand=hand)
            p = built(hand)
            placed = caps(hand)
            moving = caps(hand, True)
            # The pusher may land anywhere in its bore: it swings as the cap turns.
            column = Cylinder(BASE.pusher_diameter / 2 + parts.PUSHER_SWING, 40)
            for pose, housing, module in zip(
                parts.poses(params), parts.switch_envelopes(params), parts.placed_modules(params, p["key_module"])
            ):
                down = parts.pressed(params, pose.name, moving[pose.name], travel)
                with self.subTest(hand=hand, key=pose.name):
                    self.assertTrue(down.is_valid)
                    self.assertLess(overlap(down, p["shell"]), EPS)
                    self.assertLess(overlap(down, housing - pose.plate * column), EPS)
                    self.assertLess(overlap(down, module), EPS)
                    for other in placed:
                        if other != pose.name:
                            self.assertLess(overlap(down, placed[other]), EPS)

    def test_pusher_rests_on_the_stem(self):
        for pose in key_poses(BASE):
            cap = caps("left")[pose.name]
            disc = Cylinder(1.0, 0.1, align=(Align.CENTER, Align.CENTER, Align.MIN))
            with self.subTest(key=pose.name):
                self.assertGreater(overlap(pose.plate * Pos(0, 0, BASE.switch_stem_height + 0.05) * disc, cap), 0)
                self.assertLess(overlap(pose.plate * Pos(0, 0, BASE.switch_stem_height - 0.15) * disc, cap), EPS)

    def test_stop_pad_lands_on_the_shell(self):
        shell = built("left")["shell"]
        for pose in key_poses(BASE):
            down = parts.pressed(BASE, pose.name, caps("left", True)[pose.name], BASE.cap_stop + 0.3)
            with self.subTest(key=pose.name):
                self.assertGreater(overlap(down, shell), EPS)

    def test_cap_stops_after_the_switch_actuates(self):
        # Choc v2 actuates at 1.3 +/- 0.3 mm of travel [CHOC-V2]; the stop leaves room past the worst case.
        self.assertGreaterEqual(BASE.cap_stop, 1.6 + 0.5)
        self.assertLess(BASE.cap_stop, BASE.switch_travel)

    def test_anchor_screw_lines_up_with_its_insert(self):
        p = built("left")
        for pose in key_poses(BASE):
            frame = parts._anchor_frame(BASE, pose)
            # The screw passes right through the tab, its head sunk below the top.
            screw = frame * Cylinder(BASE.m2_clearance / 2 - 0.2, 20, align=(Align.CENTER, Align.CENTER, Align.CENTER))
            head = frame * Pos(0, 0, BASE.anchor_thickness - BASE.m2_head_height) * Cylinder(
                BASE.m2_head / 2, 10, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )
            insert = frame * Cylinder(
                BASE.m2_insert_hole / 2 - 0.2, BASE.m2_insert_depth - 0.2, align=(Align.CENTER, Align.CENTER, Align.MAX)
            )
            with self.subTest(key=pose.name):
                self.assertLess(overlap(screw, caps("left")[pose.name]), EPS)
                self.assertLess(overlap(head, caps("left")[pose.name]), EPS)
                self.assertLess(overlap(insert, p["shell"]), EPS)

    def test_cap_inserts_keep_their_walls(self):
        shell = built("left")["shell"]
        r = BASE.m2_insert_hole / 2
        mid = r + BASE.insert_wall / 2
        for pose in key_poses(BASE):
            # Points round the middle of the wall: a volume check here trips on
            # OpenCASCADE dropping the wall from a valid-looking intersection.
            frame = parts._anchor_frame(BASE, pose)
            points = [
                (frame * Pos(mid * math.cos(a * math.pi / 12), mid * math.sin(a * math.pi / 12), -z)).position
                for a in range(24)
                for z in (0.5, BASE.m2_insert_depth / 2, BASE.m2_insert_depth - 0.5)
            ]
            with self.subTest(key=pose.name):  # all but the sliver where the ring meets the curved seat
                self.assertGreater(sum(shell.is_inside(p) for p in points) / len(points), 0.97)

    def test_cap_screw_heads_sit_in_solid_tab(self):
        r = BASE.m2_head / 2 + BASE.clearance
        for pose in key_poses(BASE):
            # Points in a 1 mm ring round the head pocket, through the tab's
            # thickness; as in test_cap_inserts_keep_their_walls, points
            # rather than a volume, which OpenCASCADE can drop.
            frame = parts._anchor_frame(BASE, pose)
            cap = caps("left")[pose.name]
            points = [
                (frame * Pos(d * math.cos(a * math.pi / 12), d * math.sin(a * math.pi / 12), z)).position
                for a in range(24)
                for d in (r + 0.3, r + 0.7)
                for z in (0.3, BASE.anchor_thickness / 2, BASE.anchor_thickness - 0.3)
            ]
            with self.subTest(key=pose.name):  # the tab's edges curve, so allow a little open at the rim
                self.assertGreater(sum(cap.is_inside(p) for p in points) / len(points), 0.9)

    def test_flexure_is_a_thin_strip(self):
        for pose in key_poses(BASE):
            cap = caps("left")[pose.name]
            back = BASE.cap_reach(pose.name)[2]
            point = parts._surface_at(BASE, pose, back + BASE.flexure_length / 2)
            normal = Body.of(BASE).normal(point)
            probe = Box(0.1, 0.1, 0.1)
            with self.subTest(key=pose.name):
                self.assertGreater(overlap(Pos(*(point + normal * (BASE.cap_proud - 0.1))) * probe, cap), 0)
                below = BASE.cap_proud - BASE.flexure_thickness - 0.15
                self.assertLess(overlap(Pos(*(point + normal * below)) * probe, cap), EPS)

    def test_status_led_is_ahead_of_the_thumb_tip(self):
        led = led_pose(BASE).surface
        self.assertGreater(led.Y, BASE.wrist_y + BASE.thumb_reach)


class HingeTestTest(Case):
    @cases(hand=HANDS)
    def test_slices_are_the_real_shell_and_base_round_the_key(self, hand):
        with self.subTest(hand=hand):
            p = built(hand)
            for piece, whole in (("hinge_test", "shell"), ("hinge_test_base", "base")):
                kept = (p[piece] & p[whole]).volume
                # booleans on the mirrored, lofted body round off up to ~0.2 % of the slice
                self.assertAlmostEqual(kept / p[piece].volume, 1.0, delta=0.003)
            self.assertLess(overlap(p["hinge_test"], p["hinge_test_base"]), EPS)

    @cases(flexure=BASE.hinge_test_flexures)
    def test_each_test_cap_fits_the_slice_and_presses_fully(self, flexure):
        key = parts.HINGE_TEST_KEY
        slice_ = built("left")["hinge_test"]
        params = BASE.with_(flexure_thickness=flexure)
        self.assertLess(overlap(parts.cap(params, key), slice_), EPS)
        moving = parts.cap(params, key, moving=True)
        down = parts.pressed(params, key, moving, params.cap_stop - 0.01)
        self.assertLess(overlap(down, slice_), EPS)

    def test_slices_hold_the_whole_module_and_post(self):
        pose = next(p for p in key_poses(BASE) if p.name == parts.HINGE_TEST_KEY)
        box = parts._hinge_test_box(BASE)
        module = parts._module_box(BASE, pose)
        self.assertLess(abs((module & box).volume - module.volume), 0.01)

    def test_test_caps_cover_distinct_flexure_thicknesses(self):
        flexures = BASE.hinge_test_flexures
        self.assertGreaterEqual(len(flexures), 2)
        self.assertEqual(len(set(flexures)), len(flexures))
        self.assertIn(BASE.flexure_thickness, flexures)


class GeometryTest(Case):
    def test_keys_are_in_firmware_order(self):
        self.assertEqual([p.name for p in key_poses(BASE)], ["thumb", "index", "middle", "ring", "pinky"])

    def test_thumb_is_on_the_side_and_fingers_on_the_front(self):
        thumb, *fingers = key_poses(BASE)
        self.assertGreater(thumb.normal.X, 0.7)
        for finger in fingers:
            self.assertGreater(finger.axis.Y, 0.3)
            self.assertGreater(finger.axis.Z, 0.3)
        xs = [f.surface.X for f in fingers]
        self.assertEqual(xs, sorted(xs, reverse=True))  # index nearest the thumb

    def test_finger_keys_sit_at_the_fingertip_spacing(self):
        fingers = key_poses(BASE)[1:]
        tips = fingertip_xs(BASE)
        low, high = fingertip_room(BASE)
        self.assertGreaterEqual(tips[-1], low - 1e-6)
        self.assertLessEqual(tips[0], high + 1e-6)
        scale = (tips[0] - tips[-1]) / sum(BASE.fingertip_spacing)
        self.assertLessEqual(scale, 1 + 1e-6)
        for a, b, gap in zip(fingers, fingers[1:], BASE.fingertip_spacing):
            with self.subTest(keys=(a.name, b.name)):
                # The spacings keep their proportions when they shrink to fit the body.
                self.assertAlmostEqual(a.surface.X - b.surface.X, gap * scale, delta=1.0)

    def test_keys_point_out_of_the_shell(self):
        for pose in key_poses(BASE):
            self.assertGreater(pose.normal.dot(pose.surface), 0)
            # The finger axes lean towards a shared one so the modules fit side by
            # side; the pinky, on the sloping side, leans the most.
            self.assertGreater(pose.axis.dot(pose.normal), math.cos(math.radians(25)))
            self.assertAlmostEqual(pose.along.dot(pose.axis), 0, places=6)

    def test_longer_fingers_reach_further_down_the_front(self):
        middle = key_poses(BASE)[2]
        longer = key_poses(BASE.with_(hand_length=BASE.hand_length + 20))[2]
        self.assertLess(longer.surface.Z, middle.surface.Z)

if __name__ == "__main__":
    unittest.main()
