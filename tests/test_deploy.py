import contextlib
import io
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import deploy  # noqa: E402


def write(path, text=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def read(path):
    with open(path) as f:
        return f.read()


class DeployTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.drive = self.tmp.name
        write(os.path.join(self.drive, "boot_out.txt"), "CircuitPython")

    def tearDown(self):
        self.tmp.cleanup()

    def run_deploy(self, *argv):
        with contextlib.redirect_stdout(io.StringIO()):
            deploy.main(["--drive", self.drive, *argv])

    def test_copies_the_firmware(self):
        self.run_deploy()
        self.assertEqual(read(os.path.join(self.drive, "code.py")), read(os.path.join(deploy.FIRMWARE, "code.py")))
        self.assertTrue(os.path.isfile(os.path.join(self.drive, "handful", "app.py")))
        self.assertTrue(os.path.isfile(os.path.join(self.drive, "mappings.py")))

    def test_keeps_existing_mappings_unless_asked(self):
        mappings = os.path.join(self.drive, "mappings.py")
        write(mappings, "# mine")
        self.run_deploy()
        self.assertEqual(read(mappings), "# mine")
        self.run_deploy("--mappings")
        self.assertEqual(read(mappings), read(os.path.join(deploy.FIRMWARE, "mappings.py")))

    def test_removes_stale_files_and_unused_libraries(self):
        write(os.path.join(self.drive, "handful", "gone.py"))
        write(os.path.join(self.drive, "handful", "gone.mpy"))
        write(os.path.join(self.drive, "handful", "notes.txt"))
        write(os.path.join(self.drive, "handful", "._app.py"))
        write(os.path.join(self.drive, "lib", "adafruit_hid", "keyboard.mpy"))
        self.run_deploy()
        names = os.listdir(os.path.join(self.drive, "handful"))
        self.assertNotIn("gone.py", names)
        self.assertNotIn("gone.mpy", names)
        self.assertIn("notes.txt", names)
        self.assertIn("._app.py", names)
        self.assertFalse(os.path.exists(os.path.join(self.drive, "lib", "adafruit_hid")))

    def test_lib_removal_ignores_files_that_already_vanished(self):
        deploy._ignore_missing(os.unlink, "._x.mpy", (FileNotFoundError, FileNotFoundError(), None))
        with self.assertRaises(PermissionError):
            deploy._ignore_missing(os.unlink, "x.mpy", (PermissionError, PermissionError(), None))

    def test_refuses_a_folder_that_is_not_a_circuitpython_drive(self):
        with tempfile.TemporaryDirectory() as empty, self.assertRaises(SystemExit):
            deploy.main(["--drive", empty])


if __name__ == "__main__":
    unittest.main()
