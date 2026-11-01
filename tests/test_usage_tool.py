import contextlib
import io
import os
import sys
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import usage  # noqa: E402

MAPPINGS = os.path.join(ROOT, "firmware", "mappings.py")


class FakePort:
    """Answers commands the way the firmware does."""

    def __init__(self, replies):
        self.replies = replies
        self.written = []
        self.pending = []
        self.closed = False

    def reset_input_buffer(self):
        self.pending = []

    def write(self, data):
        self.written.append(data)
        command = data.decode().split()[0:2]
        self.pending = [b"usage\r\n", b"handful: something else\r\n"] + [
            (line + "\r\n").encode() for line in self.replies[" ".join(command)]]

    def readline(self):
        return self.pending.pop(0) if self.pending else b""

    def close(self):
        self.closed = True


REPLIES = {
    "usage": ["usage counting on", "usage M 40 2", "usage I 10 0", "usage T+I+P 3 0",
              "usage T+I+M+R+P 0 1", "usage end"],
    "usage reset": ["usage reset", "usage counting on", "usage end"],
}


def run_main(argv, port):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        usage.main(argv + ["--mappings", MAPPINGS], open_port=lambda device: port,
                   list_ports=lambda: [types.SimpleNamespace(device="/dev/pico", vid=usage.CIRCUITPYTHON_VID)])
    return out.getvalue()


class UsageToolTest(unittest.TestCase):
    def test_prints_a_ranked_table_with_unused_and_unmapped_chords(self):
        port = FakePort(REPLIES)
        text = run_main([], port)
        self.assertTrue(port.closed)
        self.assertIn("56 presses, counting is on", text)
        paste, enter = text.index("paste "), text.index("enter ")
        self.assertLess(paste, enter)
        self.assertIn("75.0%", text)
        self.assertIn("switch mode", text)
        unused = text.split("Mapped, not used yet:")[1]
        self.assertIn("push-to-talk", unused)
        self.assertNotIn("paste\n", unused.split("Not mapped")[0])
        self.assertIn("T+I+P      3 taps, 0 holds", text)
        self.assertEqual(len(port.written), 1)

    def test_reset_clears_after_printing(self):
        port = FakePort(REPLIES)
        text = run_main(["--reset"], port)
        self.assertEqual(port.written[-1], b"\r\nusage reset\r\n")
        self.assertIn("Counts cleared", text)

    def test_hints_how_to_turn_counting_on(self):
        port = FakePort({"usage": ["usage counting off", "usage end"]})
        text = run_main(["--port", "/dev/x"], port)
        self.assertIn("COUNT_CHORDS = True", text)
        self.assertNotIn("Not mapped", text)

    def test_no_answer_explains_what_to_check(self):
        port = FakePort({"usage": []})
        ticks = iter(range(100))
        with self.assertRaises(usage.UsageError) as ctx:
            usage.ask(port, "usage", clock=lambda: next(ticks))
        self.assertIn("No answer", str(ctx.exception))

    def test_main_exits_with_the_message(self):
        with self.assertRaises(SystemExit) as ctx:
            usage.main(["--mappings", MAPPINGS], list_ports=lambda: [])
        self.assertIn("No CircuitPython board", str(ctx.exception.code))

    def test_find_port(self):
        pico = types.SimpleNamespace(device="/dev/a", vid=usage.CIRCUITPYTHON_VID)
        other = types.SimpleNamespace(device="/dev/b", vid=0x1234)
        self.assertEqual(usage.find_port([pico, other]), "/dev/a")
        with self.assertRaises(usage.UsageError) as ctx:
            usage.find_port([pico, types.SimpleNamespace(device="/dev/c", vid=usage.CIRCUITPYTHON_VID)])
        self.assertIn("--port", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
