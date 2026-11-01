# 0014: Opt-in chord usage counts

## Context

The default layout ([0009](0009-default-mappings.md)) puts the moves expected
to be most common on single fingers, but that was a guess. Real counts would
show which chords deserve the easiest spots. Every swap means relearning a
chord, so the plan is one short round of counting, then one round of swaps
where the gain is clear.

The Pico has no spare storage the firmware can write while the CIRCUITPY
drive is mounted on the computer, apart from `microcontroller.nvm`: one 4 KB
flash sector with no wear levelling, rated for about 100,000 erases. Each
write erases the whole sector. Byte 0 already holds the mode.

## Options considered

- Count on the Pico and save to nvm: no extra hardware, but every save wears
  the flash.
- Log presses to the computer over serial: no flash wear, but needs a program
  running on the computer all week and records order and timing.
- Count in RAM only: no wear, but a restart loses the counts.

## Decision

We will count, on the Pico, how often each of the 31 chords fires as a tap and
as a hold, mapped or not. Only totals are kept, with no order and no times, so
typed text can't be rebuilt from them.

Counting is off by default and turned on only with `COUNT_CHORDS = True` in
`mappings.py`; no chord turns it on. While it is on, counts are saved to nvm
one minute after the first new count, in a single write, so the flash is
erased at most once a minute: at 8 hours of typing a day that's about 7
months to the rated limit, far more than a tuning round needs. Unplugging
loses at most the last minute of counts.

The counts sit in nvm after the mode byte, behind a 3-byte marker, as 62
four-byte totals. The firmware answers `usage` and `usage reset` typed on the
serial console, and `tools/usage.py` uses them to print a ranked table, the
mapped chords not used yet and the unmapped chords pressed anyway, and to
clear the counts.

## Consequences

- Layout changes can rest on real counts instead of guesses.
- Leaving counting on for many months wears the nvm sector, which also holds
  the mode. The setting's comment in `mappings.py` says so.
- `tools/usage.py` needs pyserial (BSD) on the computer. The firmware still
  uses only built-in modules.
- The serial console now accepts these two commands while the keypad runs.
