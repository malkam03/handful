"""Checks that hand measurements turn into the right parameters."""

import tempfile
import unittest
from pathlib import Path

from handful_cad.hand import Hand, load
from handful_cad.params import DEFAULT

EXAMPLE = Path(__file__).resolve().parent.parent / "hand.example.toml"


def write(text: str) -> Path:
    file = tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False)
    file.write(text)
    file.close()
    return Path(file.name)


class HandTest(unittest.TestCase):
    def test_example_file_keeps_the_defaults(self):
        self.assertEqual(DEFAULT.with_(**load(EXAMPLE)), DEFAULT)

    def test_example_defaults_match_params(self):
        text = EXAMPLE.read_text()
        middle = DEFAULT.middle_finger
        for name, value in (("hand_length", DEFAULT.hand_length), ("palm_length", DEFAULT.palm_length),
                            ("hand_breadth", DEFAULT.hand_breadth), ("middle_length", middle),
                            ("index_length", middle * DEFAULT.finger_ratios[0]),
                            ("ring_length", middle * DEFAULT.finger_ratios[2]),
                            ("pinky_length", middle * DEFAULT.finger_ratios[3]),
                            ("ring_knuckle_back", -DEFAULT.knuckle_offsets[2]),
                            ("pinky_knuckle_back", -DEFAULT.knuckle_offsets[3]),
                            ("thumb_reach", DEFAULT.thumb_reach),
                            ("thumb_tip_length", DEFAULT.thumb_tip_length)):
            self.assertIn(f"# {name} = {value:.1f}", text.replace("  ", " ").replace("  ", " "))

    def test_missing_measurements_keep_their_defaults(self):
        params = DEFAULT.with_(**Hand(hand_breadth=90.0).overrides())
        self.assertEqual(params.hand_breadth, 90.0)
        self.assertEqual(params.hand_length, DEFAULT.hand_length)
        self.assertEqual(params.finger_ratios, DEFAULT.finger_ratios)

    def test_finger_lengths_become_ratios_of_the_middle_finger(self):
        params = DEFAULT.with_(**Hand(middle_length=80.0, index_length=72.0, pinky_length=60.0).overrides())
        self.assertEqual(params.finger_ratios, (0.9, 1.0, DEFAULT.finger_ratios[2], 0.75))

    def test_middle_finger_fills_in_the_palm_or_the_hand(self):
        self.assertEqual(Hand(hand_length=190.0, middle_length=80.0).overrides()["palm_length"], 110.0)
        self.assertEqual(Hand(palm_length=110.0, middle_length=80.0).overrides()["hand_length"], 190.0)

    def test_middle_finger_alone_sets_its_length(self):
        params = DEFAULT.with_(**Hand(middle_length=80.0, index_length=75.0).overrides())
        self.assertAlmostEqual(params.middle_finger, 80.0)
        self.assertAlmostEqual(params.middle_finger * params.finger_ratios[0], 75.0)

    def test_knuckle_steps_may_be_zero_or_forward(self):
        overrides = load(write("[hand]\nindex_knuckle_back = 0.0\nring_knuckle_back = -1.5\n"))
        self.assertEqual(overrides["knuckle_offsets"][:3], (0.0, 0.0, 1.5))

    def test_knuckle_steps_sit_behind_the_middle_finger(self):
        params = DEFAULT.with_(**Hand(pinky_knuckle_back=10.0).overrides())
        self.assertEqual(params.knuckle_offsets, (0.0, 0.0, DEFAULT.knuckle_offsets[2], -10.0))

    def test_thumb_measurements_set_its_cap_and_place_it(self):
        params = DEFAULT.with_(**Hand(thumb_reach=125.0, thumb_tip_length=30.0).overrides())
        self.assertEqual(params.thumb_tip_length, 30.0)
        self.assertEqual(params.cap_reach("thumb")[1], 15.0)
        self.assertEqual(params.cap_reach("index"), DEFAULT.cap_reach("index"))
        # The cap ends under the thumb tip, moved back as the hand turns with the fingers' slant.
        self.assertAlmostEqual(params.thumb_y + 15.0, params.wrist_y + 125.0 - params.thumb_back)

    def test_params_table_sets_any_parameter(self):
        overrides = load(write("[hand]\nhand_breadth = 90\n[params]\nthumb_z = 20.0\nwedge_angles = [0, 15]\n"))
        self.assertEqual(overrides, {"hand_breadth": 90.0, "thumb_z": 20.0, "wedge_angles": (0, 15)})

    def test_nested_arrays_keep_params_hashable(self):
        overrides = load(write("[params]\nswitch_pins = [[0.0, 5.9], [5.0, 3.8]]\n"))
        params = DEFAULT.with_(**overrides)
        self.assertEqual(params.switch_pins, DEFAULT.switch_pins)
        hash(params)  # the geometry builders cache on Params

    def test_mistakes_are_reported(self):
        for text in ("[hand]\nhand_lenght = 190\n", "[hand]\nhand_length = -1\n", "[params]\nhand = 'right'\n",
                     "hand_length = 190\n", "[hand]\nhand_length = 100\npalm_length = 120\n",
                     "[hand]\nhand_length = 190\npalm_length = 110\nmiddle_length = 70\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                load(write(text))


if __name__ == "__main__":
    unittest.main()
