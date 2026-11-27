#!/usr/bin/env python3
"""Hardware block diagram of Cy Drollinger's four-panel e-ink mosaic prototype.

Renders a 1600x1100 PNG, a 3200x2200 hi-res PNG, plus SVG and PDF.
Facts live in this file so the drawing can be revised without rediscovering them.
"""

import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from PIL import Image

OUT_DIR = Path(__file__).resolve().parent
PNG_OUT = OUT_DIR / "four_panel_mosaic_block_diagram.png"
# Intermediate only. The committed drawing is the 1600x1100 PNG plus SVG and PDF.
PNG_HIRES = Path(tempfile.gettempdir()) / "four_panel_mosaic_block_diagram_hires.png"
SVG_OUT = OUT_DIR / "four_panel_mosaic_block_diagram.svg"
PDF_OUT = OUT_DIR / "four_panel_mosaic_block_diagram.pdf"

SANS = font_manager.FontProperties(
    fname="/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
)
SANS_B = font_manager.FontProperties(
    fname="/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
)
SANS_I = font_manager.FontProperties(
    fname="/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf"
)
MONO = font_manager.FontProperties(
    fname="/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"
)

INK = "#1B1B1B"
MUTED = "#4A4A4A"
WHITE = "#FFFFFF"
BG = "#FFFFFF"
PI_FILL, PI_EDGE = "#E7F0F7", "#2C5F8A"
MB_FILL, MB_EDGE = "#F3F3F0", "#4A4A4A"
SLOT_FILL, SLOT_EDGE = "#FFF6E5", "#7A4E1E"
MCU_FILL, MCU_EDGE = "#EDE7F6", "#4A3B78"
EPD_FILL, EPD_EDGE = "#E7F5EA", "#1E6B36"
TCH_FILL, TCH_EDGE = "#F6EAF8", "#6A3A7A"
NAND_FILL, NAND_EDGE = "#FFF1DC", "#8A5A16"
NFC_FILL, NFC_EDGE = "#E8EEF8", "#334B7A"
FL_FILL, FL_EDGE = "#FFF8DC", "#8A6A00"
PWR_FILL, PWR_EDGE = "#FDECEE", "#8A3038"
CAM_FILL, CAM_EDGE = "#E4F5F7", "#1A6A72"
BLE_FILL, BLE_EDGE = "#ECEAF8", "#3C3A78"
ETH_FILL, ETH_EDGE = "#E8F4EC", "#2A5A3A"
SWD_FILL, SWD_EDGE = "#F4EFE6", "#5A4030"
NOTE_FILL, NOTE_EDGE = "#F7F7F5", "#666666"

W, H = 16.0, 11.0


def font(prop, size):
    p = font_manager.FontProperties(fname=prop.get_file())
    p.set_size(size)
    return p


def rbox(ax, x, y, w, h, facecolor, edgecolor, lw=1.15, radius=0.07, z=3, ls="-"):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.0,rounding_size={radius}",
        facecolor=facecolor, edgecolor=edgecolor, linewidth=lw,
        linestyle=ls, zorder=z, clip_on=False,
    )
    ax.add_patch(patch)
    return patch


def hrule(ax, x1, x2, y, color="#6A6A6A", lw=0.6, z=4):
    ax.plot([x1, x2], [y, y], color=color, lw=lw,
            solid_capstyle="butt", zorder=z, clip_on=False)


def txt(ax, x, y, s, prop, size, color=INK, ha="left", va="top", z=5, **kw):
    return ax.text(
        x, y, s, fontproperties=font(prop, size), color=color,
        ha=ha, va=va, zorder=z, clip_on=False, **kw,
    )


def label_box(ax, x, y, s, prop, size, color, ha="center", va="center", z=7):
    """Text with a white backing so it stays legible over lines."""
    return ax.text(
        x, y, s, fontproperties=font(prop, size), color=color,
        ha=ha, va=va, zorder=z, clip_on=False,
        bbox=dict(boxstyle="round,pad=0.12,rounding_size=0.08",
                  facecolor=WHITE, edgecolor="none", alpha=0.94),
    )


def polyline_arrow(ax, pts, color, lw=1.15, label=None, label_pos=None, size=6.4):
    """Orthogonal (or any) polyline with an arrowhead at the end."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.plot(xs, ys, color=color, lw=lw, zorder=5,
            solid_capstyle="butt", solid_joinstyle="miter", clip_on=False)
    ax.annotate(
        "", xy=pts[-1], xytext=pts[-2],
        arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                        mutation_scale=10, shrinkA=0, shrinkB=0,
                        connectionstyle="arc3,rad=0"),
        zorder=6, clip_on=False,
    )
    if label and label_pos:
        label_box(ax, label_pos[0], label_pos[1], label, MONO, size, color)


def panel(ax, x, y, w, h, title, fill, edge, title_size=9.0, radius=0.07, lw=1.15, bar=0.30):
    rbox(ax, x, y, w, h, fill, edge, lw=lw, radius=radius)
    txt(ax, x + 0.10, y + h - 0.07, title, SANS_B, title_size, color=edge, va="top")
    hrule(ax, x + 0.08, x + w - 0.08, y + h - bar, color=edge, lw=0.7)
    return y + h - bar - 0.05


def draw():
    fig = plt.figure(figsize=(W, H), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.set_axis_off()
    ax.set_facecolor(BG)
    rbox(ax, 0.06, 0.06, W - 0.12, H - 0.12, WHITE, "#C8C8C8", lw=0.7, radius=0.04, z=0)

    # ----- Title -----
    txt(ax, 0.22, 10.84, "Four-panel e-ink mosaic prototype  —  hardware block diagram",
        SANS_B, 15.2, color=INK, va="center")
    txt(ax, 0.22, 10.58, "Cy Drollinger   ·   27 Nov 2026",
        SANS, 7.6, color=MUTED, va="center")
    hrule(ax, 0.22, 15.78, 10.42, color="#888888", lw=0.9)

    # =====================================================================
    # Raspberry Pi 5  (leave a wide corridor to the motherboard)
    # =====================================================================
    px, py, pw, ph = 0.20, 5.48, 4.62, 4.86
    ct = panel(ax, px, py, pw, ph, "Raspberry Pi 5", PI_FILL, PI_EDGE,
               title_size=11.0, bar=0.32)
    txt(ax, px + 0.12, ct, "Model B  Rev 1.1     hostname  zephyr     Ubuntu 24.04",
        SANS, 6.9, color=INK)
    txt(ax, px + 0.12, ct - 0.22, "Linux 6.8.0-1068-raspi  aarch64     headless",
        SANS, 6.9, color=MUTED)

    bx = px + 0.12
    bw = pw - 0.24

    y = py + ph - 1.14
    rbox(ax, bx, y, bw, 0.40, PWR_FILL, PWR_EDGE, lw=0.9, radius=0.05)
    txt(ax, bx + 0.10, y + 0.20, "USB-C power     5 V in  (Pi power port)",
        SANS_B, 7.1, color=PWR_EDGE, va="center")

    y = y - 0.48
    rbox(ax, bx, y, bw, 0.40, ETH_FILL, ETH_EDGE, lw=0.9, radius=0.05)
    txt(ax, bx + 0.10, y + 0.20, "Ethernet  eth0     the motherboard Pi     UP",
        SANS_B, 7.1, color=ETH_EDGE, va="center")

    y = y - 0.68
    rbox(ax, bx, y, bw, 0.60, BLE_FILL, BLE_EDGE, lw=0.9, radius=0.05)
    txt(ax, bx + 0.10, y + 0.44, "Onboard BLE     hci0  (UART, BlueZ)",
        SANS_B, 7.1, color=BLE_EDGE, va="center")
    txt(ax, bx + 0.10, y + 0.24, "88:A2:9E:EE:B8:BC     BT 5.0  Cypress",
        MONO, 6.5, color=INK, va="center")
    txt(ax, bx + 0.10, y + 0.08, "BLE DFU / MCUboot updates  and  BLE UI sync",
        SANS, 6.4, color=MUTED, va="center")

    y = y - 0.68
    rbox(ax, bx, y, bw, 0.60, CAM_FILL, CAM_EDGE, lw=0.9, radius=0.05)
    txt(ax, bx + 0.10, y + 0.44, "CSI camera port 0     OV5647",
        SANS_B, 7.1, color=CAM_EDGE, va="center")
    txt(ax, bx + 0.10, y + 0.24, "2592 × 1944     I2C  0x36     rpicam-still",
        MONO, 6.5, color=INK, va="center")
    txt(ax, bx + 0.10, y + 0.08, "Manual-focus lens, aimed at the four panels",
        SANS, 6.4, color=MUTED, va="center")

    y = y - 0.50
    rbox(ax, bx, y, bw, 0.42, PWR_FILL, PWR_EDGE, lw=0.9, radius=0.05)
    txt(ax, bx + 0.10, y + 0.27, "3.3 V out     HAT pin 1  →  each slot pin 4",
        SANS_B, 6.9, color=PWR_EDGE, va="center")
    txt(ax, bx + 0.10, y + 0.10, "HAT 5 V not used.  Pin 17 3.3 V airwire unrouted.",
        SANS, 6.15, color=MUTED, va="center")

    y = py + 0.10
    swd_h = 1.22
    rbox(ax, bx, y, bw, swd_h, SWD_FILL, SWD_EDGE, lw=0.9, radius=0.05)
    txt(ax, bx + 0.10, y + swd_h - 0.09, "SWD master     OpenOCD  linuxgpiod",
        SANS_B, 7.1, color=SWD_EDGE, va="top")
    txt(ax, bx + 0.10, y + swd_h - 0.28, "gpiochip4     500 kHz     nRESET cfg off on all slots",
        SANS, 6.2, color=MUTED, va="top")
    swd_lines = [
        "A  SWDIO GPIO24   SWCLK GPIO25   nRESET GPIO23",
        "B  SWDIO GPIO16   SWCLK GPIO20   nRESET GPIO21",
        "C  SWDIO GPIO13   SWCLK GPIO19   nRESET GPIO26",
        "D  SWDIO GPIO22   SWCLK GPIO27   nRESET GPIO17",
    ]
    for i, line in enumerate(swd_lines):
        txt(ax, bx + 0.12, y + 0.64 - i * 0.155, line, MONO, 6.25, color=INK, va="center")

    # =====================================================================
    # Motherboard + 2x2 slots
    # =====================================================================
    mx, my, mw, mh = 5.72, 5.48, 10.08, 4.86
    mct = panel(ax, mx, my, mw, mh, "Custom JLCPCB motherboard", MB_FILL, MB_EDGE,
                title_size=11.0, bar=0.32)
    txt(ax, mx + 0.12, mct,
        "Carries the Pi 5 and four display-board slots     ~246 × 154 mm",
        SANS, 6.9, color=INK)
    txt(ax, mx + 0.12, mct - 0.22,
        "Letters A–D follow OpenOCD cfg / FICR  (motherboard silkscreen is swapped top ↔ bottom)",
        SANS, 6.4, color=MUTED)
    txt(ax, mx + mw - 0.12, mct,
        "OV5647 optical view  →  all four panels",
        SANS_I, 6.4, color=CAM_EDGE, ha="right", va="top")

    gap = 0.12
    inner_x = mx + 0.12
    inner_y = my + 0.12
    inner_w = mw - 0.24
    slot_top = my + mh - 0.92
    slot_h = (slot_top - inner_y - gap) / 2
    slot_w = (inner_w - gap) / 2

    slots = {
        "B": dict(col=0, row=1, pos="top-left",
                  ficr="944d9a60", ble="CF:CB:94:4D:9A:60",
                  swdio="GPIO16", swclk="GPIO20", nreset="GPIO21"),
        "A": dict(col=1, row=1, pos="top-right",
                  ficr="f15c2668", ble="E4:CD:F1:5C:26:68",
                  swdio="GPIO24", swclk="GPIO25", nreset="GPIO23"),
        "C": dict(col=0, row=0, pos="bottom-left",
                  ficr="b0749cd0", ble="CA:15:B0:74:9C:D0",
                  swdio="GPIO13", swclk="GPIO19", nreset="GPIO26"),
        "D": dict(col=1, row=0, pos="bottom-right",
                  ficr="4bdf4558", ble="F7:97:4B:DF:45:58",
                  swdio="GPIO22", swclk="GPIO27", nreset="GPIO17"),
    }
    for letter, s in slots.items():
        sx = inner_x + s["col"] * (slot_w + gap)
        sy = inner_y + s["row"] * (slot_h + gap)
        rbox(ax, sx, sy, slot_w, slot_h, SLOT_FILL, SLOT_EDGE, lw=1.15, radius=0.07)
        txt(ax, sx + 0.12, sy + slot_h - 0.10,
            f"Board  {letter}", SANS_B, 10.4, color=SLOT_EDGE, va="top")
        txt(ax, sx + slot_w - 0.12, sy + slot_h - 0.12,
            s["pos"], SANS_I, 7.3, color=MUTED, ha="right", va="top")
        hrule(ax, sx + 0.10, sx + slot_w - 0.10, sy + slot_h - 0.36, color=SLOT_EDGE, lw=0.65)
        lines = [
            (SANS, 6.9, INK,   "nRF52832  +  GDEY042T81  4.2\"  400×300    ·    identical"),
            (MONO, 7.0, INK,   f"FICR    {s['ficr']}"),
            (MONO, 7.0, INK,   f"BLE     {s['ble']}"),
            (MONO, 6.6, INK,   f"SWD     SWDIO {s['swdio']}    SWCLK {s['swclk']}"),
            (MONO, 6.4, MUTED, f"nRESET  {s['nreset']}    (wired, OpenOCD cfg off)"),
            (SANS, 6.4, MUTED, "Header  pin 4 = 3.3 V     pin 5 = GND     pins 1–2 = SWD"),
        ]
        ty = sy + slot_h - 0.48
        for prop, size, color, line in lines:
            txt(ax, sx + 0.12, ty, line, prop, size, color=color, va="top")
            ty -= 0.225

    # Corridor buses between Pi and motherboard
    x1 = px + pw
    x2 = mx
    mid = (x1 + x2) / 2.0

    def corridor(y, color, label, ls="solid"):
        ax.annotate(
            "", xy=(x2, y), xytext=(x1, y),
            arrowprops=dict(
                arrowstyle="-|>", color=color, lw=1.3,
                linestyle=ls, mutation_scale=10, shrinkA=0, shrinkB=0,
            ),
            zorder=5, clip_on=False,
        )
        label_box(ax, mid, y, label, MONO, 6.5, color)

    corridor(py + 0.70, SWD_EDGE, "SWD  × 4")
    corridor(py + 1.52, PWR_EDGE, "3.3 V / GND")
    corridor(py + mh - 1.52, BLE_EDGE, "BLE  (OTA)", ls=(0, (2.4, 1.6)))
    corridor(py + mh - 2.20, CAM_EDGE, "CSI  optical", ls=(0, (2.4, 1.6)))

    # =====================================================================
    # Display board detail
    # =====================================================================
    dx, dy, dw, dh = 0.20, 1.40, 15.60, 3.96
    panel(ax, dx, dy, dw, dh,
          "Display board detail   —   nRF52832  V_2_1   (representative; boards A–D are identical)",
          "#FAFAF8", "#333333", title_size=10.0, bar=0.30)

    # Slot header
    hx, hy, hw, hh = 0.34, 2.24, 1.62, 2.52
    hct = panel(ax, hx, hy, hw, hh, "Slot header  ·  J2/J4/J6/J8", SWD_FILL, SWD_EDGE,
                title_size=6.8, bar=0.26)
    for i, line in enumerate([
        "1   SWDIO",
        "2   SWDCLK",
        "3   nRESET",
        "4   3.3 V in",
        "5   GND",
        "6–10  GPIO stubs",
    ]):
        txt(ax, hx + 0.10, hct - 0.02 - i * 0.26, line, MONO, 6.4, color=INK, va="top")

    # Small regulator box under the header
    rx, ry, rw, rh = 0.34, 1.48, 1.62, 0.66
    rct = panel(ax, rx, ry, rw, rh, "3.3 V regulator", PWR_FILL, PWR_EDGE,
                title_size=6.6, bar=0.22)
    txt(ax, rx + 0.08, rct, "P0.25 POW → EN", MONO, 5.9, color=INK, va="top")
    txt(ax, rx + 0.08, rct - 0.20, "TLV70033  (V_2 sch)  (?)", SANS, 5.8, color=MUTED, va="top")

    # MCU
    cx, cy, cw, ch = 2.28, 1.48, 3.42, 3.28
    cct = panel(ax, cx, cy, cw, ch, "nRF52832", MCU_FILL, MCU_EDGE,
                title_size=10.4, bar=0.30)
    mcu_lines = [
        (SANS_B, 7.2, MCU_EDGE, "Zephyr RTOS  ·  MCUboot  ·  BLE"),
        (SANS, 6.5, INK, "Y1  32 MHz      Y2  32 kHz  (P0.00 / P0.01)"),
        (SANS, 6.5, INK, "BLE ANT  2450AT18A100E  +  3.9 nH"),
        (SANS, 6.4, MUTED, "Console = Segger RTT over SWD"),
        (SANS, 6.4, MUTED, "uart0 disabled  (claims P0.05–P0.08)"),
        (SANS_B, 6.5, MCU_EDGE, "On-chip radios / ports"),
        (MONO, 6.25, INK, "2.4 GHz BLE  (peripheral + DFU)"),
        (MONO, 6.25, INK, "NFCT   P0.09 / P0.10   Type 2 tag"),
        (MONO, 6.25, INK, "SPIM0  →  SSD1683   (manual CS)"),
        (MONO, 6.25, INK, "TWIM1  →  FT6336U   (0x38)"),
        (MONO, 6.25, INK, "SPIM2  →  MX35 NAND"),
        (MONO, 6.25, INK, "P0.31  →  TPS61042 CTRL"),
        (MONO, 6.25, INK, "P0.25  POW  →  regulator EN"),
    ]
    ty = cct - 0.02
    for prop, size, color, line in mcu_lines:
        txt(ax, cx + 0.10, ty, line, prop, size, color=color, va="top")
        ty -= 0.218

    # Header → MCU
    polyline_arrow(ax, [(hx + hw, hy + hh * 0.68), (cx, hy + hh * 0.68)],
                   SWD_EDGE, label="SWD",
                   label_pos=((hx + hw + cx) / 2, hy + hh * 0.68 + 0.01), size=6.2)
    polyline_arrow(ax, [(hx + hw, hy + 0.18), (cx, hy + 0.18)],
                   PWR_EDGE, label="3.3 V",
                   label_pos=((hx + hw + cx) / 2, hy + 0.18 - 0.01), size=6.0)
    # POW from MCU down-left into regulator
    polyline_arrow(
        ax,
        [(cx, ry + rh * 0.55), (rx + rw, ry + rh * 0.55)],
        PWR_EDGE, label="P0.25",
        label_pos=((cx + rx + rw) / 2, ry + rh * 0.55 + 0.01), size=5.8,
    )

    # Peripheral geometry
    # Top alley under the detail title for TWIM1; mid-gap for NFCT / P0.31.
    ex, ey, ew, eh = 6.62, 3.16, 5.20, 1.54   # EPD
    tx, tyb, tw, th = 12.00, 3.16, 3.62, 1.54  # Touch
    nx, ny, nw, nh = 6.62, 1.48, 3.22, 1.42   # NAND
    fx, fy, fw, fh = 10.00, 1.48, 2.40, 1.42  # NFC
    lx, ly, lw_, lh = 12.56, 1.48, 3.06, 1.42  # Front light

    ect = panel(ax, ex, ey, ew, eh, "GDEY042T81   4.2\" e-ink   400 × 300",
                EPD_FILL, EPD_EDGE, title_size=7.8, bar=0.26)
    txt(ax, ex + 0.10, ect, "SSD1683     4-wire SPI     J3  24-pin 0.5 mm FPC",
        SANS, 6.5, color=INK, va="top")
    txt(ax, ex + 0.10, ect - 0.24, "MOSI P0.02    SCK P0.03    CS P0.04    DC P0.05",
        MONO, 6.4, color=INK, va="top")
    txt(ax, ex + 0.10, ect - 0.46, "RST  P0.06    BUSY P0.07    BS1 P0.08  (driven low)",
        MONO, 6.4, color=INK, va="top")
    txt(ax, ex + 0.10, ect - 0.68, "POW  P0.25  panel / regulator enable     VCI / VDDIO = 3.3 V",
        MONO, 6.15, color=MUTED, va="top")

    tct = panel(ax, tx, tyb, tw, th, "FT6336U  touch    J102",
                TCH_FILL, TCH_EDGE, title_size=7.8, bar=0.26)
    txt(ax, tx + 0.10, tct, "I2C  0x38     TWIM1     10 kΩ pull-ups",
        SANS, 6.4, color=INK, va="top")
    txt(ax, tx + 0.10, tct - 0.26, "SCL  P0.27      SDA  P0.28", MONO, 6.5, color=INK, va="top")
    txt(ax, tx + 0.10, tct - 0.48, "INT  P0.29      RST  P0.30", MONO, 6.5, color=INK, va="top")
    txt(ax, tx + 0.10, tct - 0.70, "V_2_1 pinout  (see notes)", SANS_I, 6.2, color=MUTED, va="top")

    nct = panel(ax, nx, ny, nw, nh, "MX35LF1GE4AB   1 Gb SPI NAND",
                NAND_FILL, NAND_EDGE, title_size=7.2, bar=0.24)
    txt(ax, nx + 0.10, nct, "SPIM2", SANS, 6.4, color=INK, va="top")
    txt(ax, nx + 0.10, nct - 0.22, "CS   P0.15     MISO P0.14", MONO, 6.3, color=INK, va="top")
    txt(ax, nx + 0.10, nct - 0.42, "MOSI P0.18     SCLK P0.17", MONO, 6.3, color=INK, va="top")
    txt(ax, nx + 0.10, nct - 0.62, "WP   P0.13     HOLD P0.16", MONO, 6.3, color=INK, va="top")

    fct = panel(ax, fx, fy, fw, fh, "NFC antenna", NFC_FILL, NFC_EDGE,
                title_size=7.4, bar=0.24)
    txt(ax, fx + 0.10, fct, "NFCT  Type 2 tag", SANS, 6.3, color=INK, va="top")
    txt(ax, fx + 0.10, fct - 0.24, "COIL_P  P0.09", MONO, 6.3, color=INK, va="top")
    txt(ax, fx + 0.10, fct - 0.44, "COIL_Q  P0.10", MONO, 6.3, color=INK, va="top")
    txt(ax, fx + 0.10, fct - 0.64, "not a reader", SANS_I, 6.1, color=MUTED, va="top")

    lct = panel(ax, lx, ly, lw_, lh, "Front light    J103", FL_FILL, FL_EDGE,
                title_size=7.4, bar=0.24)
    txt(ax, lx + 0.10, lct, "GDEY042T81-FL02  LED", SANS, 6.3, color=INK, va="top")
    txt(ax, lx + 0.10, lct - 0.22, "TPS61042 boost", SANS, 6.3, color=INK, va="top")
    txt(ax, lx + 0.10, lct - 0.42, "CTRL  P0.31  (PWM / EN)", MONO, 6.15, color=INK, va="top")
    txt(ax, lx + 0.10, lct - 0.62, "R51  18 Ω  ≈ 14 mA", MONO, 6.15, color=INK, va="top")

    # Signal routes from the MCU — never chained through another peripheral.
    epd_y = ey + eh * 0.52
    nand_y = ny + nh * 0.58
    alley_top = ey + eh + 0.12          # under the detail title, above EPD
    alley_hi = (ey + ny + nh) / 2 + 0.06  # upper half of the inter-row gap
    alley_lo = (ey + ny + nh) / 2 - 0.06  # lower half

    polyline_arrow(ax, [(cx + cw, epd_y), (ex, epd_y)], EPD_EDGE,
                   label="SPIM0", label_pos=((cx + cw + ex) / 2, epd_y + 0.02), size=6.3)

    # TWIM1: out of the MCU top-right, up into the title alley, across, down into Touch
    touch_y = tyb + th * 0.55
    mcu_top_y = cy + ch - 0.10
    polyline_arrow(
        ax,
        [(cx + cw, mcu_top_y), (cx + cw + 0.14, mcu_top_y),
         (cx + cw + 0.14, alley_top), (tx - 0.12, alley_top),
         (tx - 0.12, touch_y), (tx, touch_y)],
        TCH_EDGE, label="TWIM1",
        label_pos=(cx + cw + 0.55, alley_top), size=6.3,
    )

    polyline_arrow(ax, [(cx + cw, nand_y), (nx, nand_y)], NAND_EDGE,
                   label="SPIM2", label_pos=((cx + cw + nx) / 2, nand_y + 0.02), size=6.3)

    # NFCT: upper inter-row alley, drop into NFC
    nfc_y = fy + fh * 0.62
    polyline_arrow(
        ax,
        [(cx + cw, alley_hi), (fx - 0.12, alley_hi),
         (fx - 0.12, nfc_y), (fx, nfc_y)],
        NFC_EDGE, label="NFCT",
        label_pos=(cx + cw + 0.48, alley_hi), size=6.3,
    )

    # P0.31: lower inter-row alley, drop into the front-light box
    fl_y = ly + lh * 0.40
    polyline_arrow(
        ax,
        [(cx + cw, alley_lo), (lx - 0.12, alley_lo),
         (lx - 0.12, fl_y), (lx, fl_y)],
        FL_EDGE, label="P0.31",
        label_pos=((fx + fw + lx) / 2, alley_lo), size=6.3,
    )

    # =====================================================================
    # Footer notes  (two columns, readable type)
    # =====================================================================
    nx0, ny0, nw0, nh0 = 0.20, 0.10, 15.60, 1.20
    rbox(ax, nx0, ny0, nw0, nh0, NOTE_FILL, NOTE_EDGE, lw=0.8, radius=0.05, z=3)
    txt(ax, nx0 + 0.12, ny0 + nh0 - 0.07, "Notes  ·  unverified items marked (?)",
        SANS_B, 7.6, color=MUTED, va="top")

    left_notes = [
        "nRESET is routed to each slot pin 3 but is commented out in all four OpenOCD cfgs (~/pi5-nrf52-swd{,-b,-c,-d}.cfg).  SWDIO / SWCLK BCM numbers were read from those cfgs on the Pi (gpiochip4, 500 kHz, linuxgpiod).",
        "3.3 V: Pi HAT pin 1 feeds slot header pin 4 on all four slots (motherboard schematic review).  Pi HAT 5 V is unused.  HAT pin 17 (3.3 V) is an unrouted airwire.  The pin-1 run is a 0.4 mm bottom-layer trace.",
    ]
    right_notes = [
        "On-board 3.3 V regulator (P0.25 POW → EN, Schottky) is from the V_2 display schematic (TLV70033).  How that regulator and the Pi 3.3 V feed share the rail on V_2_1 is (?).  LTC4124 CHRG on P0.26 and USB-C SBU SWD are display-board schematic features, not motherboard connections (?).",
        "Touch pins shown are V_2_1 (current boards: SCL P0.27, SDA P0.28, INT P0.29, RST P0.30).  V_2 was SCL P0.30, SDA P0.29, INT P0.28, RST P0.27.  Panel temp I2C on P0.11 / P0.12 is unused by firmware.",
    ]

    def wrapped_block(ax, x, y, width_chars, lines, size=7.15):
        ty = y
        for para in lines:
            words = para.split()
            cur = ""
            paras = []
            for w_ in words:
                trial = (cur + " " + w_).strip()
                if len(trial) > width_chars:
                    paras.append(cur)
                    cur = w_
                else:
                    cur = trial
            if cur:
                paras.append(cur)
            for p_ in paras:
                txt(ax, x, ty, p_, SANS, size, color=INK, va="top")
                ty -= 0.148
            ty -= 0.055
        return ty

    wrapped_block(ax, nx0 + 0.12, ny0 + nh0 - 0.28, 96, left_notes, size=7.15)
    wrapped_block(ax, nx0 + 8.05, ny0 + nh0 - 0.28, 96, right_notes, size=7.15)

    # Hi-res at 200 dpi (3200x2200), then downsample for the 1600x1100 PNG.
    # Also write SVG and PDF; embed TrueType in the PDF.
    import matplotlib as mpl
    mpl.rcParams["pdf.fonttype"] = 42
    mpl.rcParams["ps.fonttype"] = 42

    fig.savefig(PNG_HIRES, dpi=200, facecolor=BG, edgecolor="none")
    fig.savefig(SVG_OUT, dpi=100, facecolor=BG, edgecolor="none")
    fig.savefig(PDF_OUT, dpi=200, facecolor=BG, edgecolor="none")
    plt.close(fig)

    im = Image.open(PNG_HIRES)
    assert im.size == (3200, 2200), im.size
    standard = im.resize((1600, 1100), Image.Resampling.LANCZOS)
    if standard.mode == "RGBA":
        standard = standard.convert("RGB")
    standard.save(PNG_OUT, "PNG")
    print(f"Wrote {PNG_OUT}  size={standard.size}")
    print(f"Wrote {PNG_HIRES}  size={im.size}")
    print(f"Wrote {SVG_OUT}")
    print(f"Wrote {PDF_OUT}")


if __name__ == "__main__":
    draw()
