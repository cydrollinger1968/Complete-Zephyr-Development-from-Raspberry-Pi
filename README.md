# Complete Zephyr Development from Raspberry Pi

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Zephyr Version](https://img.shields.io/badge/Zephyr-4.3-blue)](https://zephyrproject.org/)
[![Nordic nRF52840](https://img.shields.io/badge/Board-nRF52840-green)](https://www.nordicsemi.com/Products/nRF52840)
[![Nordic nRF52832](https://img.shields.io/badge/Board-nRF52832%20e--ink-lightgrey)](https://www.nordicsemi.com/Products/nRF52832)
[![Raspberry Pi](https://img.shields.io/badge/Host-Raspberry%20Pi-red)](https://www.raspberrypi.com/)

[![Donate with PayPal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/ncp/payment/JVET7MJ54B9DJ)

Cutting-edge automated setup for developing Zephyr RTOS applications hosted on a Raspberry Pi. Nordic's nRF52840 USB dongle is the example hardware running blinky, however Zephyr RTOS development environment supports ~1k boards with endless firmware for embedded application solutions. No soldering, no external probes—just GPIO SWD for initial MCUboot flash and USB DFU for seamless updates. Perfect for BLE/Thread/Mesh prototyping, swarm projects, and scaling for remote development, utilizing ssh extention from your VScode.

The same Raspberry Pi Zephyr environment also hosts Cy's custom **nRF52832 e-ink display lab** (splash mosaic, NFC Type 2, BLE UI sync, Hubble Network page). That path is documented in [Custom nRF52832 e-ink lab](#custom-nrf52832-e-ink-lab-progress). The original nRF52840 dongle / MCUboot / `install100.sh` story below remains the on-ramp.

![Descriptive alt text for the image](wiring.png)



## Features
- **Automated Installation**: One script sets up Zephyr SDK, toolchain, openOCD, and builds MCUboot + blinky sample.
- **MCUboot Bootloader**: Replaces native Nordic bootloader for secure OTA updates via USB serial (CDC ACM).
- **SWD Flashing via RPi GPIO**: Use bitbang OpenOCD—no extra hardware needed.
- **Multi-Dongle Ready**: Leverage Pi's 4 USB ports for parallel flashing/updates; scale to production volumes.
- **No-Soldering Option**: Pogo pins or clips for SWD pads.
- **Tested on Ubuntu's 24.04 Server OS**: From bare OS to blinking RGB LED in under an hour.
- **Two hardware paths, one host**: The nRF52840 USB dongle (MCUboot + USB DFU) and the custom nRF52832 e-ink mosaic (GPIO SWD / OpenOCD) share the same Pi 5 Zephyr workspace.

## Prerequisites
- Raspberry Pi 5 running Ubuntu 24.04 Server.
- Nordic nRF52840 USB Dongle (PCA10059).
- SWD connections: RPi GPIO 24 (SWDIO) → Dongle SWDIO, GPIO 25 (SWCLK) → Dongle SWCLK, GND → GND (optional 3.3V VCC).



## Installation
1. Download and run the setup script:
   ```
   wget https://raw.githubusercontent.com/cydrollinger1968/Complete-Zephyr-Development-from-Raspberry-Pi/refs/heads/main/install100.sh
   chmod +x install100.sh
   ./install100.sh
   ```
2. Reboot and log in as `dev`.

The script installs zephyr, and builds MCUboot.

## Project Structure
```
├── install100.sh  # Main automation script
├── └── zephyrproject/             # Zephyr workspace (auto-created)
    ├── build-mcuboot/         # MCUboot build
    ├── build/blinky/          # Blinky build
    └── ...                    # Zephyr sources
```

## Custom nRF52832 e-ink lab (progress)

This is **lab progress** on custom nRF52832 e-ink boards, not a replacement for the dongle path above. Both use the same Pi-hosted Zephyr toolchain (`install100.sh` / west / OpenOCD). Firmware trees, keys, and device credentials stay on the lab host and are **not** committed here.

### Host

| Item | Lab value |
|------|-----------|
| Board | Raspberry Pi 5 |
| OS | Ubuntu |
| User | `dev` |
| Hostname | often `zephyr` |
| Workspace | `~/zephyrproject` (same environment as the dongle / MCUboot install) |

### Target hardware

Custom **nRF52832** boards driving a Good Display **GDEY042T81-FT02** (SSD1683 panel + FT6336 touch). Optional pieces in the same demo:

- MX35 SPI NAND for icon storage
- NFC Type 2
- BLE manufacturer-data UI sync
- Hubble Network page (QR to the Hubble dashboard)

Lab application path:

```
~/zephyrproject/apps/ssd1683_demo
```

### Multi-board SWD (Pi GPIO + OpenOCD)

Flashing uses **linuxgpiod** on **gpiochip4** and OpenOCD. **SRST is often disabled** (blocked halt); RST pins in the mosaic wiring are frequently left off.

Example mosaic wiring (800×600 logical canvas → four 400×300 e-ink tiles):

| Position | Tile | SWDIO | SWCLK | RST | OpenOCD config |
|----------|------|-------|-------|-----|----------------|
| C — top-left | TILE0 | 13 | 19 | 26, often off | `pi5-nrf52-swd-c.cfg` |
| D — top-right | TILE1 | 22 | 27 | 17, often off | `pi5-nrf52-swd-d.cfg` |
| B — bottom-left | TILE2 | 16 | 20 | 21, often off | `pi5-nrf52-swd-b.cfg` |
| A — bottom-right | TILE3 | 24 | 25 | — | `pi5-nrf52-swd.cfg` |

Board A reuses the same GPIO 24 / 25 SWD pair documented for the nRF52840 dongle.

### Splash UX

Left: logo. Right zones (and mosaic composition):

- Craft
- NFC Tap
- Icons
- Hubble Network
- Mosaic — 800×600 composed as four 400×300 e-ink tiles (A/B/C/D)

### NFC, BLE, and Hubble

- **NFC**: NCS `libnfc_t2t` URI records.
- **BLE**: manufacturer-data used to sync UI state.
- **Hubble**: splash / QR points at [https://dash.hubble.com/devices](https://dash.hubble.com/devices).

Upstream Hubble Zephyr reference (link only — do not fork, clone, or vendor it from this repo):

**[HubbleNetwork/hubble-reference-zephyr-simple](https://github.com/HubbleNetwork/hubble-reference-zephyr-simple)** — minimal Zephyr app demonstrating Hubble BLE advertisement.

**Never commit Hubble org IDs, API tokens, device keys, or other secrets.** Keep credentials on the lab Pi (or Hubble’s own secrets flow); this repository stays docs-only for the e-ink work.

### Flash helpers

From the lab app tree, per-tile helpers (argument is board letter `A` `B` `C` or `D`):

```
./build_demo_board.sh A|B|C|D
./flash_demo_board.sh A|B|C|D
```

Build outputs are named `zephyr_A.hex`, `zephyr_B.hex`, `zephyr_C.hex`, and `zephyr_D.hex`. Hex images are lab artifacts — do not dump them into this repository.

## Bill of Materials
https://www.digikey.com/short/p804r9wf
## Contributing
Fork, PRs welcome! Add multi-dongle batch flashing, mesh samples, or RPi 5 optimizations. Issues for bugs/suggestions.

## License
MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments
- xAI Grok for hammering out the script.
- Zephyr Project for RTOS excellence.
- Raspberry Pi for the perfect host.
- [Hubble Network](https://github.com/HubbleNetwork/hubble-reference-zephyr-simple) for the public Zephyr Hubble reference (linked, not vendored).

Star if useful—let's build wireless swarms! 🚀
