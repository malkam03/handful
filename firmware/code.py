"""handful firmware entry point."""

from handful.app import run
from handful.pico import Pico

run(Pico(), lambda: __import__("mappings"))
