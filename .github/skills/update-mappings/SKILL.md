---
name: update-mappings
description: Use when adding, removing or changing handful chords, key names, action names or timings (firmware/mappings.py, firmware/handful/keys.py). Keeps the README chords banner, the printable cheat sheet, the docs and the Pico in step with the mappings.
---

# Update mappings

`firmware/mappings.py` is the single source of truth for chords. The README
banner (`docs/chords.svg`) and the printable cheat sheet
(`docs/cheatsheet.svg`) are drawn from it by `tools/cheatsheet.py`, and a test
fails when either drawing is out of date.

## Steps

1. Edit `firmware/mappings.py`. Give every chord a macOS and a Windows
   action, and end each line with a short comment naming the action, such as
   `# paste`. The drawings use that comment as the action's name.
2. If you add a key name, add it to `firmware/handful/keys.py`. If it needs a
   friendlier label on the drawings, add it to `MAC_KEYS` or `WIN_KEYS` in
   `tools/drawings/labels.py`.
3. Redraw both drawings with `python3 tools/cheatsheet.py`. Each group (one
   finger, thumb +, combos) fits five chords; the script stops with a clear
   message when a group needs more room, and then the layout needs more rows.
4. Look at both SVGs in a browser and check that nothing overlaps or runs off
   a card.
5. Update any text that quotes what changed, such as timings in
   `docs/architecture.md`.
6. Changes to the default layout in `docs/decisions/0009-*` are architecture
   decisions: use the `architecture-drilldown` skill for those.
7. Run `ruff check .` and
   `coverage run -m unittest discover -s tests && coverage report`
   inside the `.venv` described under Development in the README.
8. With the Pico plugged in, run `python3 tools/deploy.py --mappings` so the
   board gets the new file. This replaces the `mappings.py` on the drive.
9. Show the user the diff and get approval before committing.
