"""Every dimension of the handful grip shell, in millimetres and degrees.

Change a value here, or pass ``DEFAULT.with_(name=value)`` to the builders,
and rebuild. Each datum names where its number comes from.

Sources
-------
[ANSUR] Gordon, C. C. et al. (2014). 2012 Anthropometric Survey of U.S. Army
    Personnel (ANSUR II), public data files ANSUR_II_MALE_Public.csv (4,082 men)
    and ANSUR_II_FEMALE_Public.csv (1,986 women),
    https://www.openlab.psu.edu/ansur2/. The defaults use the midpoint of the
    male and female means as a medium adult hand:
    hand length 193.3 / 181.1 -> 187.2, hand breadth 88.3 / 78.2 -> 83.3,
    palm length 116.5 / 108.7 -> 112.6.
[CHOC] Kailh Choc v2 low-profile switch, drawing PG135301D03 (KHA-PG1353):
    15.00 mm top housing, 13.95 mm bottom housing, plate 1.30 mm at the clips,
    plate top to PCB 2.20 mm, housing top 3.10 mm and stem top 6.40 mm above
    the plate, total travel 3.2 +/- 0.25 mm, MX-style cross stem. PCB layout:
    centre post 5.00 mm, contact pins 1.20 mm at (3.80, 5.00) and (5.90, 0)
    from the centre and a 1.60 mm peg at (-5.15, -5.00), seen from the
    pattern (solder) side. From above, with the pins towards +Y, that puts
    the pins at (0, 5.90) and (5.00, 3.80) and the peg at (-5.00, -5.15).
[CHOC-V2] Kailh, Choc V2 low-profile switch product page
    (kailh.net/products/kailh-choc-v2-low-profile-switch-set): pre-travel
    1.3 +/- 0.3 mm.
[CHOC-SOCKET] Kailh Choc hot-swap socket, drawing CPG135001S30: 13.15 mm
    across the solder tabs, body 9.95 mm across and 6.85 mm deep, 1.85 mm
    thick, contacts 2.90 mm round on 5.00 mm centres.
[B3F] Omron B3F tactile switch datasheet (B3F-4055, 12 x 12 mm, yellow
    actuator): body 3.5 mm high, 7.3 mm to the actuator's top, legs on
    12.5 x 5.0 mm centres, travel 0.25 mm.
[PICO] Raspberry Pi Pico datasheet, section 2 "Mechanical specification",
    figure 3: 51 x 21 x 1 mm PCB, four 2.1 +/- 0.05 mm holes on 11.4 x 47.0 mm
    centres (2.0 mm from the short edges), micro-USB socket about 8 mm wide,
    overhanging the top edge by 1.3 mm (typ.).
[ERGO] Logitech MX Ergo product specifications, logitech.com: height 132.5 mm,
    width 99.8 mm, depth 51.4 mm, 0 or 20 deg tilt.
[INSERT] CNC Kitchen threaded heat-set insert guidance: M2 x 4 insert (3.6 mm
    across the knurls) in a 3.2 mm hole, M3 x 5.7 insert in a 4.0 mm hole, at
    least 1.3 mm of wall and a hole 1 mm deeper than the insert. The hole is
    about 0.4 mm under the knurl diameter. Check the inserts you buy.
[SCREW] ISO 4762 (DIN 912) hexagon socket head cap screws: M2 head 3.8 mm
    across and 2.0 mm tall, M3 head 5.5 mm across and 3.0 mm tall (maximum).
[PHALANX] Buryanov, A. & Kotiuk, V. (2010). Proportions of hand segments.
    Int. J. Morphol. 28(3):755-758, doi:10.4067/S0717-95022010000300015,
    table I: thumb tip soft tissue 5.67 mm plus distal phalanx 21.67 mm,
    thumb proximal phalanx 31.57 mm; for the middle finger, the middle and
    distal phalanges plus the tip are 59.4 % of the finger.
[SPREAD] Maximum spread between neighbouring fingers, index-middle,
    middle-ring and ring-little: 17.2, 14.3 and 32.1 deg in 51 young adults
    (KoreaMed RID 2556561, 2024); 20.0-20.8, 17.3-18.2 and 27.7-29.4 deg in
    a second study (Medicine Science, medicinescience.org/article/3379, 2023).
[LED] Kingbright WP154A4SUREQBFZGC, a 5 mm (T-1 3/4) common-cathode RGB LED,
    "Package Dimensions": body 5.0 mm, flange 5.9 mm and 1.0 mm thick,
    8.6 mm from the back of the flange to the tip, four leads on a 1.27 mm
    pitch. ASSUMPTION: other makers' 5 mm RGB LEDs are close; measure yours.

Values marked ASSUMPTION have no primary source; measure your parts and tune
them on a printed shell.
"""

from dataclasses import dataclass, replace

KEYS = ("thumb", "index", "middle", "ring", "pinky")  # the firmware's button order
PAD_DEPTH = 0.65  # how far towards the front edge the fingertip pads lie, as a fraction of the front reach
PAD_HEIGHT = 0.55  # how high the fingertip pads lie, as a fraction of the body height
PINKY_PAD_HEIGHT = 0.3  # the pinky, shortest, lies lower on the gently sloping pinky side


@dataclass(frozen=True)
class Params:
    # Hand. Left hand by default; "right" mirrors every handed part.
    hand: str = "left"
    hand_length: float = 187.2  # [ANSUR] wrist crease to middle fingertip
    hand_breadth: float = 83.3  # [ANSUR] across the knuckles
    palm_length: float = 112.6  # [ANSUR] wrist crease to middle-finger base
    # Finger length relative to the middle finger: index, middle, ring, pinky.
    # ASSUMPTION: typical proportions; ANSUR II doesn't measure single fingers.
    finger_ratios: tuple = (0.93, 1.0, 0.95, 0.78)
    # Where the hand lies on the shell. The heel of the palm rests on the desk
    # behind the shell, the palm lies over the top and the fingers follow the
    # front down to the keys, as on a palm-supported mouse. ASSUMPTION: tune
    # these on a printed shell.
    heel_overhang: float = 34.0  # palm length behind the shell, the heel on the desk
    key_reach: float = 0.8  # key centre along each finger: under the fingertip pad
    knuckle_offsets: tuple = (0.0, 0.0, -2.0, -8.0)  # the pinky knuckle sits further back
    # Fingertip pads apart, centre to centre, with the hand relaxed: index to
    # middle, middle to ring, ring to pinky. The fingers fan out from the
    # knuckles to these spacings, centred in the room the body has at the
    # keys; where they add up to more, they shrink in proportion and the
    # body keeps its size (see geometry.fingertip_room).
    # ASSUMPTION: no survey reports relaxed spacing. Index to middle is the
    # knuckle pitch (hand breadth / 4) plus the pair's mean finger length
    # times the sine of half its maximum spread [SPREAD], rounded down to a
    # whole millimetre. On a printed grip the ring finger sits comfortably
    # nearer the pinky, so ring to pinky is a little under index to middle
    # and middle to ring takes the rest of the spread's total.
    fingertip_spacing: tuple = (31.0, 37.0, 30.0)
    finger_offset_x: float = 0.0  # moves the knuckles towards the thumb (+) or away
    # 1: the four finger switches press along one shared axis, so their
    # modules fit side by side; 0: each presses straight into the surface.
    # The pinky side falls steeply, so the axes lean well towards the shared one.
    finger_axis_blend: float = 0.85
    # Per finger, index to pinky, in degrees: each cap and its switch turn
    # about the fingertip, so the tip stays and the cap's palm end swings
    # towards the pinky (+) or the thumb (-). Slanted towards the pinky, the
    # hand turns about the fingertips and the wrist moves over the rounded
    # heel, onto the desk.
    cap_slant: tuple = (10.0, 10.0, 10.0, 10.0)
    # Per finger, index to pinky, in degrees: each switch rolls about its
    # finger, its press axis leaning out towards the side where the shell
    # falls away. Where the side falls steeply, the switch housing's outer
    # corner then drops clear of the cap wrapping down that side.
    switch_lean: tuple = (0.0, 0.0, 0.0, 18.0)
    # Per finger, mm: the switch module moves this far across its finger,
    # towards the pinky side (+), to keep clear of its neighbours and the base.
    switch_shift: tuple = (0.0, 0.0, -3.5, -2.0)
    # Thumb key on the side. The thumb rests along its cap like the fingers
    # do: the switch sits under the middle of the thumb's last segment and
    # the cap ends under the thumb tip. thumb_reach is the wrist crease to the thumb tip, with
    # the thumb laid alongside the index finger. ASSUMPTION: ANSUR II has no
    # thumb length; 119.5 puts the thumb where the first printed shell had it.
    thumb_reach: float = 119.5
    thumb_z: float = 18.0  # height of the thumb tip's end of the key above the base. ASSUMPTION.
    # The thumb follows the hand as it turns with cap_slant: with 10 degrees,
    # turning a hand about its fingertips moves the thumb tip about 8 mm back
    # (thumb_back) and the thumb's base up the side wall, so its cap turns
    # about the tip, palm end up, by thumb_cap_tilt degrees. A rigid hand
    # turns it about 18 degrees; past 12 the anchor tab behind the hinge
    # reaches the thin crown, so it stops at 10. ASSUMPTION: tune on a print.
    thumb_back: float = 8.0
    thumb_cap_tilt: float = 10.0
    # The thumb cap's tab sits where the side wall curves over into the top,
    # so its screw moves down the wall and towards the hinge by these mm
    # (down, towards the hinge), into the tab's solid part, and its insert
    # with it. A test checks every cap keeps solid tab round its screw head.
    thumb_screw_shift: tuple = (3.0, 1.5)

    # Shell body: rounded like a mouse, not a dome. Horizontal slices are
    # rounded rectangles (superellipses); seen from the side the outline is a superellipse, so the palm
    # area stays broad and gently crowned, and the highest point sits behind
    # the middle. Proportions after the Logitech MX Ergo, 132.5 x 99.8 x 51.4 mm
    # including its base [ERGO].
    body_width_margin: float = 12.7  # added to the hand breadth: 96 mm wide
    body_length_margin: float = 15.4  # added to the palm length: 128 mm, plus body_rear_extra
    # Above the base; 50.5 mm with it. Tall enough that each key's switch,
    # socket and cap, about 15 mm along its press axis, stay above the base
    # where the fingers fan out down the front; the pinky's module is the
    # one that sets it.
    body_height: float = 46.0
    # Footprint exponents: 2 is an ellipse, higher is squarer. The front stays
    # broad for the four finger keys; the back is round, like an egg.
    body_squareness: float = 4.0
    body_rear_squareness: float = 2.4
    body_crown: float = 3.5  # profile exponent: 2 is an ellipsoid, higher is flatter on top
    # The front, where the fingers lie, falls in a long, nearly straight ramp
    # rather than a rounded nose, so the fingers rest almost straight on it,
    # and it widens towards the front for the fanned fingertips.
    body_front_crown: float = 1.6  # front profile exponent: lower is a longer, straighter ramp
    # How much the front widens on the thumb and pinky side, as fractions
    # (see geometry.widening). 0 keeps the MX Ergo-sized body: the fingertips
    # fan out within it rather than the body growing round them.
    front_spread: tuple = (0.0, 0.0)
    # The outer caps' edges stay this far inside the outline at the keys'
    # height (see geometry.fingertip_room).
    body_front_margin: float = 2.0
    body_peak_shift: float = 12.0  # highest point behind the footprint centre
    # The back runs out in a long, gentle slope, so the heel of the hand
    # rests on the shell and on the desk at once, as on the MX Ergo.
    body_rear_extra: float = 10.0  # the back reaches this much further than the front
    body_rear_crown: float = 1.4  # back profile exponent: lower is a longer, gentler slope
    # Seen from the front the shell is lopsided, like the MX Ergo: the
    # highest point sits under the index knuckle, the thumb side falls
    # steeply, and the pinky side reaches further and falls away under the
    # ring and pinky knuckles, so the hand rolls towards a handshake and its
    # outer edge, from the wrist to the pinky knuckle, nears the desk.
    body_crest_shift: float = 14.0  # top of the shell this far towards the thumb
    body_pinky_extra: float = 6.0  # the pinky side reaches this much further than the thumb side, at the desk
    body_pinky_crown: float = 1.3  # pinky profile exponent: lower is a gentler slope
    # The foot of the pinky side flares out in a concave curve, so the side
    # of the hand slides down it to the desk, with no wall at the bottom.
    body_pinky_flare: float = 4.0  # of the pinky side's reach at the desk
    body_pinky_flare_height: float = 14.0
    wall: float = 2.8

    # Long caps: each key is a strip of the shell surface as long as the
    # digit's last two segments, so the whole finger rests on it, not just
    # the tip, and presses anywhere along it. The switch sits under the
    # fingertip pad; the cap's back end bends on a thin printed strip (a
    # flexure) and a tab behind it screws to the shell. The cap rests on
    # the switch stem, so it pivots freely. Print caps in PETG: the strip
    # bends about 7 degrees on every press.
    cap_widths: tuple = (22.0, 18.0, 18.0, 18.0, 16.0)  # thumb to pinky
    # Fingers: from the fingertip back to the middle joint (PIP), 59.4 % of
    # the finger [PHALANX]: the middle and distal phalanges and the tip.
    cap_pip: float = 0.594
    # Thumb: its last segment, 27.3 mm [PHALANX], centred on the switch, and
    # half its first segment, 31.6 mm [PHALANX], behind that.
    thumb_tip_length: float = 27.3
    thumb_proximal: float = 31.6
    cap_corner: float = 3.0
    cap_thickness: float = 2.0
    cap_proud: float = 0.5  # cap top above the shell surface, to feel each key
    cap_gap: float = 0.4  # all round, between a cap and its opening
    cap_travel_margin: float = 0.6  # cap underside above the shell when fully pressed
    cap_roll: float = 0.3  # a cap stops where the shell falls this far below its centre line, across it
    # The thumb cap wraps further, so it has a broad side to print on; its
    # module isn't in the base, so the deeper well costs no height.
    thumb_cap_roll: float = 1.0
    # The anchor tab, away from the switch, wraps further round, so the
    # screw head keeps a full ring of tab where the shell rolls away.
    anchor_roll: float = 2.0
    # The paddle's top dips this far along its centre line, a shallow channel
    # across the cap that the digit settles into, and runs level again over
    # the last cap_dish_fade before the flexure.
    cap_dish: float = 0.8
    cap_dish_fade: float = 10.0
    # The flexure: a strip at the cap's top face, the cap's full width.
    # ASSUMPTION: no published fatigue data for printed PETG flexures; print
    # the hinge test part and tune these.
    flexure_length: float = 5.0
    flexure_thickness: float = 0.8  # two lines of a 0.4 mm nozzle; thinner strips can slice to nothing
    flexure_room: float = 1.0  # under the strip, so it bends freely
    anchor_length: float = 10.0  # the tab behind the strip that screws down
    anchor_thickness: float = 3.2  # sinks a socket head (2.0 mm + clearance) on a 1.0 mm floor
    hinge_test_flexures: tuple = (0.6, 0.8, 1.0)  # strip thicknesses of the hinge test caps
    # Socket-head cap screws [SCREW] sit in counterbores.
    m2_head: float = 3.8  # [SCREW] M2 head diameter
    m2_head_height: float = 2.0  # [SCREW]
    # The pusher under the cap rests on the stem's top. The switch actuates
    # at 1.3 +/- 0.3 mm [CHOC-V2] and bottoms out at 3.2 mm [CHOC]. A pad
    # under the cap's tip lands on its well's floor once the stem has moved
    # cap_stop, well past actuation and short of bottoming out. The shell's
    # wells and the switches' depths leave room for that press (press_stop).
    pusher_diameter: float = 5.5
    cap_stop: float = 2.5
    stop_pad_length: float = 3.0  # along the cap, at the fingertip end

    # Kailh Choc v2 low-profile switch and its hot-swap socket.
    switch_cutout: float = 14.0  # [CHOC] 13.95 bottom housing; the common Choc plate hole
    switch_cutout_corner: float = 0.3
    switch_plate: float = 1.3  # [CHOC]
    switch_plate_to_pcb: float = 2.2  # [CHOC]
    switch_post_diameter: float = 5.0  # [CHOC]
    switch_pins: tuple = ((0.0, 5.9), (5.0, 3.8))  # [CHOC]
    switch_pegs: tuple = ((-5.0, -5.15),)  # [CHOC] 1.60 mm
    switch_peg_diameter: float = 1.6
    switch_pin_relief: float = 1.8  # through the skin under each contact pin
    switch_clip_clearance: float = 15.0  # [CHOC] top housing, 15.0 mm square; room for the plate clips
    # ASSUMPTION: the plate clips are on the switch's +-Y faces, so the
    # module is narrower across X: room for the 13.95 mm bottom housing only.
    switch_bottom_clearance: float = 14.5
    switch_housing_height: float = 3.1  # [CHOC] housing top above the plate top
    switch_stem_height: float = 6.4  # [CHOC] stem top above the plate top
    switch_travel: float = 3.2  # [CHOC]
    # The module floor stands in for a PCB. At 1.2 mm the pins reach further
    # into the socket than on a 1.6 mm board, so a hole under each lets them through.
    pcb_thickness: float = 1.2
    socket_body: tuple = (9.95, 6.85)  # [CHOC-SOCKET]
    socket_tabs_width: float = 13.15  # [CHOC-SOCKET]
    socket_thickness: float = 1.85  # [CHOC-SOCKET]
    socket_hole: float = 3.0  # [CHOC-SOCKET] round the 2.90 mm contacts
    socket_skin: float = 0.6  # holds the socket up against the switch pins
    wire_clearance: float = 5.0  # room at the socket channel mouth for the wires

    # Tactile adapter: holds a 12 x 12 mm tactile button in a key module's
    # switch hole instead of a Choc switch, for testing the grip with the
    # prototype's buttons [B3F]. The yellow actuator's top sits where the
    # stem's top would, tactile_gap below the cap's pusher, so the button sits
    # partly below the plate: cut its legs to tactile_leg_cut.
    tactile_size: float = 12.0  # [B3F] body, square
    tactile_height: float = 7.11  # body underside to actuator top (measured; [B3F] 7.3)
    tactile_body_height: float = 3.5  # [B3F]
    tactile_legs: tuple = (12.5, 13.0, 5.0)  # [B3F] 12.5 x 5.0 mm; some clones list 13 x 5
    tactile_leg_cut: float = 1.0  # legs cut to this below the body, clear of the module floor
    tactile_leg_slot: float = 1.6  # leg slot width; the legs are kinked
    tactile_travel: float = 0.25  # [B3F]
    tactile_gap: float = 0.1  # actuator top below the pusher, so the cap rests free
    tactile_wall: float = 1.2  # round the button's body
    tactile_plug_depth: float = 2.0  # below the plate's top, through the switch hole, above the floor
    tactile_plug_fit: float = 0.1  # the plug is this much under the switch cutout: a snug push fit

    # Key module (switch mount): plate, walls and a floor with the socket pocket.
    # It slides into a tunnel in the solid shell from below. Its plate's lip
    # reaches past the switch at both ends and seats against the shell, and a
    # post on the base holds it there, so it needs no screws.
    module_wall: float = 1.2
    module_seat: float = 5.0  # lip length past the module walls at each end
    # Keys with their own module, its lip's corner trimmed where the pressed
    # cap's side reaches it, so the cap keeps that corner. The pinky's lean
    # clears its cap, so every key shares one module by default.
    own_module_keys: tuple = ()
    post_size: float = 9.0  # square section of the posts that hold the finger modules
    post_gap: float = 0.0  # between a post and its module; negative presses the module harder
    thumb_block: float = 8.0  # thickness of the block that holds the thumb module
    thumb_rib: float = 4.0  # under the thumb module, so it cannot drop
    insert_wall: float = 1.3  # [INSERT] least wall round an insert
    m2_clearance: float = 2.4
    m2_insert_hole: float = 2.6  # [INSERT] 0.4 mm under the knurls of an M2 x 4 insert 3.0 mm across (measured)
    m2_insert_depth: float = 5.0  # [INSERT] insert length + 1 mm

    # Raspberry Pi Pico.
    pico_size: tuple = (21.0, 51.0, 1.0)  # [PICO]
    pico_holes: tuple = (11.4, 47.0)  # [PICO]
    pico_hole: float = 2.1  # [PICO]
    pico_usb_overhang: float = 1.3  # [PICO]
    pico_usb_width: float = 8.0  # [PICO]
    pico_usb_height: float = 2.9  # ASSUMPTION: micro-USB socket height above the board
    pico_parts_height: float = 3.5  # ASSUMPTION: tallest part on the component side, the USB socket
    # The Pico hangs in the shell, components down, screwed up under two
    # bridges across its bay. M2 screws go up through the board into inserts
    # in the bridges, so the wiring stays in the shell and the base is a lid.
    pico_face_z: float = 6.9  # the board's component face above the base: room for the socket and screw heads
    # Along the board, centred on its holes: each bridge ends 5.0 mm from the
    # board's end, clear of the GND pads at pins 3, 18, 23 and 38 (6.45 mm in).
    pico_bridge_width: float = 6.0
    pico_bridge_chamfer: float = 2.8  # 45 degrees at each wall: a shorter bridge that centres the board
    # The Pico lies under the palm, behind the finger modules, with its USB
    # socket facing forwards into the cable channel.
    pico_rear_y: float = -62.0  # rear edge of the board, from the base centre
    pico_x: float = 3.5  # the cable runs out between the middle and ring posts
    # Cable exit: room for a micro-USB plug's overmould. ASSUMPTION.
    usb_plug_size: tuple = (12.5, 8.5)
    usb_plug_length: float = 30.0
    usb_cable_diameter: float = 4.5  # ASSUMPTION

    # Base and fastening.
    base_thickness: float = 5.5  # deep enough for the leaning pinky module's pocket; sinks an M3 head on a 2.3 mm floor
    # Under a module's pocket, so the bottom stays closed and the post still
    # holds the module up: three 0.2 mm layers, resting on the wedge or desk.
    base_floor: float = 0.6
    # The locating rim on the base, and the shell's groove for it.
    locating_lip_height: float = 3.0
    locating_lip_width: float = 1.6
    locating_lip_inset: float = 1.8  # in from the body; leaves about 1.6 mm of skin outside the groove
    locating_lip_roof: float = 1.2  # the inset is measured this far above the groove
    locating_lip_boss_gap: float = 1.6  # the rim is notched to keep this far from each insert hole
    # From the thumb side, round the outline: thumb front, pinky front corner,
    # pinky back, thumb back, so the four screws hold the rim at its corners.
    boss_angles: tuple = (80.0, 140.0, 215.0, 304.0)
    boss_search: int = 60  # deg; how far a boss may slide either way to clear the cavities
    # Each boss's centre inside the inner wall. The pinky front corner's sits
    # closer to the wall, beside the pinky and ring modules; its insert keeps
    # 1.5 mm of wall outside the knurls.
    boss_insets: tuple = (3.0, 1.0, 3.0, 3.0)
    boss_roof: float = 1.5  # the inset is measured this far above the insert
    insert_hole: float = 4.0  # [INSERT] 0.5 mm under the knurls of an M3 x 6 insert 4.5 mm across (measured)
    insert_depth: float = 7.0  # [INSERT] M3 x 6 insert + 1 mm; an M3 x 8 screw reaches 5.7 mm in
    m3_clearance: float = 3.4
    m3_head: float = 5.5  # [SCREW] M3 head diameter
    m3_head_height: float = 3.0  # [SCREW]

    # Wedges: dovetail rails slide into the base from the back.
    wedge_angles: tuple = (0, 10, 20)
    wedge_min_thickness: float = 3.0
    rail_x: float = 14.0
    rail_width: float = 8.0  # at the base's bottom face
    # Flank angle from the vertical. With the wedge tilt added, the steeper flank
    # stays within 45 deg of vertical up to a 30 deg wedge, so it prints unsupported.
    rail_flank: float = 15.0
    rail_height: float = 2.4
    rail_front_stop: float = 40.0  # the slots end here, so the wedge stops

    # Rounded heel: under the corner where the wrist and the pinky side of the
    # palm rest, the underside curves up from a diagonal line with radius
    # heel_radius until it rises at heel_angle, then runs straight on. The
    # wedges stop at that line. Like a rocker, the shell rolls on the curve:
    # on any wedge up to heel_angle the curve touches the desk, so the wrist
    # corner rests on the desk on every wedge, as on the MX Ergo, whose base
    # plate stops short of that corner. Each wedge lifts the line just enough
    # for that, R(1 - cos angle). With no wedge the flat bottom sits on the
    # desk. The line runs from front to back, along the hand, so a wedge
    # rolls the hand onto its outer edge from the wrist to the pinky knuckle
    # without lifting the fingertips. heel_angle 0 turns the heel off, and
    # the wedges tilt about the pinky edge.
    heel_angle: float = 20.0  # matches the steepest wedge
    heel_radius: float = 25.0
    # The line, in mm in from the pinky edge: at the front, heel_front[1] of
    # the way from the centre to the front end, and at the back end. The further in, the lower the wrist end
    # sits on a wedge, and the more the corner lifts off the desk with none.
    # At the front, 17 is as far in as it goes before the rounding reaches the
    # pinky module's pocket and insertion tunnel (test_heel_clears_the_modules).
    heel_front: tuple = (17.0, 0.12)
    heel_back: float = 40.0
    heel_boss_gap: float = 3.5  # a screw's centre stays this far inside the line
    heel_clearance: float = 0.5  # on wedges steeper than heel_angle, the far edge stays this far above the desk
    heel_base_tip: float = 1.0  # the base ends where the curve leaves it thinner than this
    wedge_tip: float = 1.2  # a wedge ends where it gets thinner than this

    # Status LED: the 4-leg common-cathode RGB LED of ADR 0018 (GP26-GP28). It
    # sits in a window on the thumb side, just ahead of the thumb tip, where
    # the thumb never covers it. It pushes out from its bay inside until its
    # flange stops on a shoulder in the bore, with its tip just proud of the shell.
    led_size: tuple = (5.0, 5.9, 8.6)  # [LED] body, flange, flange to tip
    led_flange_thickness: float = 1.0  # [LED]
    led_proud: float = 1.0  # tip above the shell surface
    # LED centre this far ahead of the thumb tip, in the gap between the thumb
    # and index switches, so the resting thumb leaves it in view.
    led_ahead_of_thumb: float = 4.5
    led_z: float = 18.0
    # Diameter and length behind the LED for its four leads, bent and
    # soldered to wires. The resistor sits on the common wire in the main cavity.
    led_wiring_room: tuple = (7.0, 10.0)

    # The shell is solid. These cavities are cut into it, each with walls
    # and roofs no flatter than 45 degrees or short bridges (the thumb bay's
    # 9 mm roof, the 13 mm USB plug channel), so it prints rim-down without
    # supports. The finger modules' 5 mm seat ledges lean 27 degrees and
    # may sag a little; any sag sits under the lip and only seats it lower.
    core_half_width: float = 13.5  # the Pico's bay: room for the board and wires
    core_wall_height: float = 9.0  # vertical walls, then a 45 degree roof
    core_rear_y: float = -64.0
    trough_width: float = 8.0  # wire channels along the bottom face
    trough_height: float = 6.0
    skin: float = 2.4  # least shell left over a cavity

    # Printing.
    clearance: float = 0.2  # sliding and press fits
    hole_clearance: float = 0.1  # added to the switch cutout; FDM holes print small

    @property
    def mirrored(self) -> bool:
        if self.hand not in ("left", "right"):
            raise ValueError(f"hand must be 'left' or 'right', not {self.hand!r}")
        return self.hand == "right"

    def cap_roll_for(self, key: str) -> float:
        return self.thumb_cap_roll if key == "thumb" else self.cap_roll

    def cap_reach(self, key: str) -> tuple:
        """A cap's width, how far it reaches from the switch centre towards the
        digit's tip, and how far back towards the hinge."""
        width = self.cap_widths[KEYS.index(key)]
        if key == "thumb":
            half = self.thumb_tip_length / 2
            return width, half, half + self.thumb_proximal / 2
        length = self.middle_finger * self.finger_ratios[KEYS.index(key) - 1]
        return width, (1 - self.key_reach) * length, (self.cap_pip - 1 + self.key_reach) * length

    @property
    def press_stop(self) -> float:
        """How far the stem moves before the cap's stop pad lands: the deepest press the shell leaves room for."""
        return self.cap_stop

    @property
    def wrist_y(self) -> float:
        """Where the wrist crease lies: behind the shell by the heel overhang."""
        return -self.body_rear_length - self.heel_overhang

    @property
    def led_y(self) -> float:
        return self.wrist_y + self.thumb_reach + self.led_ahead_of_thumb

    @property
    def thumb_y(self) -> float:
        """The thumb key centre, with the cap level: half a cap behind the thumb tip."""
        return self.wrist_y + self.thumb_reach - self.thumb_back - self.thumb_tip_length / 2

    @property
    def led(self) -> tuple:
        """Body diameter, flange diameter and flange-to-tip length of the status LED."""
        return self.led_size

    @property
    def body_rear_length(self) -> float:
        return self.body_axes[1] + self.body_rear_extra

    @property
    def body_pinky_width(self) -> float:
        return self.body_axes[0] + self.body_pinky_extra

    @property
    def body_axes(self) -> tuple:
        a = (self.hand_breadth + self.body_width_margin) / 2
        b = (self.palm_length + self.body_length_margin) / 2
        return a, b, self.body_height

    @property
    def middle_finger(self) -> float:
        return self.hand_length - self.palm_length

    @property
    def module_lip_length(self) -> float:
        return self.module_outer + 2 * self.module_seat

    @property
    def module_outer(self) -> float:
        """Module size along the finger (Y)."""
        return self.switch_clip_clearance + 2 * self.module_wall

    @property
    def module_width(self) -> float:
        """Module size across the finger (X), at the plate."""
        return self.switch_bottom_clearance + 2 * self.module_wall

    @property
    def module_socket_x(self) -> tuple:
        """The floor's extent across the finger (X) at the socket, from the
        switch centre. The socket sits to one side of the switch, so on that
        side a ledge reaches out under its solder tabs, open at the edge."""
        (x0, _), (x1, _) = self.switch_pins
        mid, reach = (x0 + x1) / 2, self.socket_tabs_width / 2 + self.clearance
        half = self.module_width / 2
        return min(-half, mid - reach), max(half, mid + reach)

    @property
    def module_depth(self) -> float:
        return self.switch_plate_to_pcb + self.pcb_thickness + self.socket_thickness + 0.1 + self.socket_skin

    def with_(self, **changes) -> "Params":
        return replace(self, **changes)


DEFAULT = Params()
