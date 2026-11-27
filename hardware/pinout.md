# Pinout

Pins below are the V_2_1 display boards on this motherboard, from the notes read on 27 Nov 2026, plus the Pi GPIO lines those boards' SWD configs use. Boards A–D are the same population. The regulator part and the charger pin called out at the bottom are not confirmed; see [Unverified](README.md#unverified).

## nRF52832 (each of A–D)

Crystals: Y1 32 MHz, Y2 32.768 kHz on P0.00 / P0.01. BLE antenna 2450AT18A100E plus 3.9 nH (V_2 schematic). Console is Segger RTT over SWD. `uart0` is disabled; on this pinout it would take P0.05–P0.08, which are panel control lines.

### GDEY042T81 / SSD1683 (SPIM0, manual CS)

4.2" 400×300 panel, 4-wire SPI, J3 24-pin 0.5 mm FPC.

| Signal | Pin |
|--------|-----|
| MOSI | P0.02 |
| SCK | P0.03 |
| CS | P0.04 |
| DC | P0.05 |
| RST | P0.06 |
| BUSY | P0.07 |
| BS1 | P0.08 (driven low) |
| POW | P0.25 (panel / regulator enable) |

### FT6336U touch (J102, TWIM1, I2C 0x38)

10 kΩ pull-ups. This is the V_2_1 pinout. V_2 was SCL P0.30, SDA P0.29, INT P0.28, RST P0.27.

| Signal | V_2_1 pin |
|--------|-----------|
| SCL | P0.27 |
| SDA | P0.28 |
| INT | P0.29 |
| RST | P0.30 |

### MX35LF1GE4AB 1 Gb SPI NAND (SPIM2)

| Signal | Pin |
|--------|-----|
| CS | P0.15 |
| MISO | P0.14 |
| MOSI | P0.18 |
| SCLK | P0.17 |
| WP | P0.13 |
| HOLD | P0.16 |

### NFC and front light

| Function | Pin |
|----------|-----|
| NFC antenna, NFCT Type 2, COIL_P / COIL_Q | P0.09 / P0.10 |
| Front light GDEY042T81-FL02 on J103, TPS61042 CTRL | P0.31 |

R51 is 18 Ω, about 14 mA, on the TPS61042 current set.

The block diagram also notes a panel-temperature I2C pair on P0.11 / P0.12 that firmware does not use.

## Raspberry Pi 5 GPIO

SWD only. OpenOCD `linuxgpiod` on `gpiochip4`, adapter speed 500 kHz. The numbers are the BCM lines in [the configs](openocd/). `nRESET` is commented out in every config; the GPIO is still the one named there.

| Slot | SWDIO | SWCLK | nRESET (cfg off) | Config |
|------|-------|-------|------------------|--------|
| A top-right | GPIO 24 | GPIO 25 | GPIO 23 | [pi5-nrf52-swd.cfg](openocd/pi5-nrf52-swd.cfg) |
| B top-left | GPIO 16 | GPIO 20 | GPIO 21 | [pi5-nrf52-swd-b.cfg](openocd/pi5-nrf52-swd-b.cfg) |
| C bottom-left | GPIO 13 | GPIO 19 | GPIO 26 | [pi5-nrf52-swd-c.cfg](openocd/pi5-nrf52-swd-c.cfg) |
| D bottom-right | GPIO 22 | GPIO 27 | GPIO 17 | [pi5-nrf52-swd-d.cfg](openocd/pi5-nrf52-swd-d.cfg) |

The OV5647 is on CSI camera port 0, not on these GPIOs.

## Motherboard power and slot header

From a motherboard schematic review (not re-measured on 27 Nov 2026):

- The Pi is powered from its USB-C 5 V port.
- Pi HAT pin 1 (3.3 V) feeds pin 4 of all four slot headers (J2, J4, J6, J8). That run is a 0.4 mm bottom-layer trace.
- Pi HAT 5 V (pins 2 and 4) is unused.
- Pi HAT pin 17 (3.3 V) is an unrouted airwire.
- GND is HAT pins 6, 9, 14, 20, 25, 30, 34, and 39, and slot pin 5, on the bottom-layer pour.

Slot header:

| Pin | Signal |
|-----|--------|
| 1 | SWDIO |
| 2 | SWDCLK |
| 3 | nRESET |
| 4 | 3.3 V from Pi HAT pin 1 |
| 5 | GND |
| 6–10 | P0.22, P0.23, P0.24, P0.20, P0.19 stubs |

## Not confirmed on V_2_1

- TLV70033 as the on-board 3.3 V regulator, with P0.25 POW to EN through a Schottky, and how that rail shares with the Pi 3.3 V feed.
- LTC4124 CHRG on P0.26, and USB-C SBU SWD. Those are display-board schematic features, not motherboard connections.
