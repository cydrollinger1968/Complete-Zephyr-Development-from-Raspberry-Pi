# Slot map

Physical 2×2 as viewed on the assembled unit. Letters match the OpenOCD configs and the FICR device address, not the motherboard silkscreen. The silkscreen is swapped top-to-bottom relative to this table. Do not pick a slot from the silk legend.

Read on the rig 27 Nov 2026:

| Letter | Position | Mosaic tile | FICR DEVICEADDR[0] | BLE address | Config | SWDIO | SWCLK | nRESET |
|--------|----------|-------------|--------------------|-------------|--------|-------|-------|--------|
| B | top-left | TILE0 | `944d9a60` | `CF:CB:94:4D:9A:60` | [pi5-nrf52-swd-b.cfg](openocd/pi5-nrf52-swd-b.cfg) | GPIO 16 | GPIO 20 | GPIO 21 |
| A | top-right | TILE1 | `f15c2668` | `E4:CD:F1:5C:26:68` | [pi5-nrf52-swd.cfg](openocd/pi5-nrf52-swd.cfg) | GPIO 24 | GPIO 25 | GPIO 23 |
| C | bottom-left | TILE2 | `b0749cd0` | `CA:15:B0:74:9C:D0` | [pi5-nrf52-swd-c.cfg](openocd/pi5-nrf52-swd-c.cfg) | GPIO 13 | GPIO 19 | GPIO 26 |
| D | bottom-right | TILE3 | `4bdf4558` | `F7:97:4B:DF:45:58` | [pi5-nrf52-swd-d.cfg](openocd/pi5-nrf52-swd-d.cfg) | GPIO 22 | GPIO 27 | GPIO 17 |

TILE0–TILE3 are the quadrants of the 800×600 mosaic in reading order (top-left, top-right, bottom-left, bottom-right). GPIO numbers are the BCM lines in the OpenOCD `linuxgpiod` configs (`gpiochip4`). Board A uses the same GPIO 24 / GPIO 25 pair as the nRF52840 dongle path in the root README.

## nRESET

`nRESET` is present in every config and commented out, so OpenOCD does not drive it. The board C comment says forcing nRESET blocks halt, same as board B. Leave those lines commented unless you have a reason to change that on the rig.

## Ports

Each config listens on its own ports so two sessions do not collide.

| Letter | telnet | gdb | tcl |
|--------|--------|-----|-----|
| A | 4444 | 3333 | not set (OpenOCD default 6666) |
| B | 4445 | 3334 | 6667 |
| C | 4446 | 3335 | 6668 |
| D | 4447 | 3336 | 6669 |

All four use `adapter driver linuxgpiod`, `adapter speed 500`, and `transport select swd`.

## Bring-up

The configs on the Pi are `~/pi5-nrf52-swd.cfg` and `~/pi5-nrf52-swd-{b,c,d}.cfg`. The copies in [openocd/](openocd/) are those files. OpenOCD stays in the foreground, so wrap it in `timeout`. Example for board B (top-left):

```bash
timeout 20s openocd -f ~/pi5-nrf52-swd-b.cfg -f target/nordic/nrf52.cfg
```

Always check FICR `DEVICEADDR` before flashing, and only then program. On the nRF52832, `DEVICEADDR[0]` is the 32-bit word at `0x100000A4` (`DEVICEADDR[1]` follows at `0x100000A8`). It must match the FICR column for the slot you think you are attached to (`944d9a60` for B). One-shot read:

```bash
timeout 20s openocd -f ~/pi5-nrf52-swd-b.cfg -f target/nordic/nrf52.cfg \
  -c "init; mdw 0x100000A4 2; shutdown"
```

Swap the `-b` / `-c` / `-d` config (or the base config for A) and expect that slot's FICR value. A mismatch means the silkscreen, the cable, or the config is not the board you intended.
