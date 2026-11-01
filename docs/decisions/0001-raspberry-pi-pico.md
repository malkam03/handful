# 0001: Raspberry Pi Pico as the microcontroller

## Context

handful must show up on the computer as a normal USB keyboard, with no
drivers. The boards on hand are a Raspberry Pi Pico (RP2040), an Arduino Nano
(ATmega328P) and an ESP8266. Only a chip with native USB can act as a USB
keyboard.

## Options considered

- Raspberry Pi Pico: native USB, plenty of GPIO for 4–5 buttons, cheap, well
  supported by several firmware stacks.
- Arduino Nano: no native USB on the ATmega328P, so it can't be a USB keyboard.
- ESP8266: no native USB and no Bluetooth, so it can't be a keyboard either way.

## Decision

We will build handful on the Raspberry Pi Pico and connect it to the computer
over USB as a HID keyboard. A Pico W or an ESP32-S3 can be considered if
handful goes wireless.

## Consequences

- No drivers on the computer, and USB provides power.
- The Nano and ESP8266 are not used.
- Going wireless needs a different board.
