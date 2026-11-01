import unittest

import _path  # noqa: F401
from handful.keys import parse_keys


class ParseKeysTest(unittest.TestCase):
    def test_letters_digits_and_function_keys(self):
        self.assertEqual(parse_keys("A"), (0x04,))
        self.assertEqual(parse_keys("Z"), (0x1D,))
        self.assertEqual(parse_keys("1"), (0x1E,))
        self.assertEqual(parse_keys("0"), (0x27,))
        self.assertEqual(parse_keys("F1"), (0x3A,))
        self.assertEqual(parse_keys("F12"), (0x45,))
        self.assertEqual(parse_keys("F13"), (0x68,))
        self.assertEqual(parse_keys("F24"), (0x73,))

    def test_modifiers_come_first(self):
        self.assertEqual(parse_keys("4+SHIFT+CMD"), (0xE1, 0xE3, 0x21))

    def test_aliases_and_case(self):
        self.assertEqual(parse_keys("cmd+v"), parse_keys("GUI+V"))
        self.assertEqual(parse_keys("WIN+V"), parse_keys("GUI+V"))
        self.assertEqual(parse_keys("OPTION+SPACE"), parse_keys("ALT+SPACE"))
        self.assertEqual(parse_keys("RETURN"), parse_keys("ENTER"))
        self.assertEqual(parse_keys("ESC"), parse_keys("ESCAPE"))

    def test_rejects_unknown_and_empty(self):
        for bad in ("CMD+NOPE", "", "CMD+", None, 5):
            with self.assertRaises(ValueError):
                parse_keys(bad)


if __name__ == "__main__":
    unittest.main()
