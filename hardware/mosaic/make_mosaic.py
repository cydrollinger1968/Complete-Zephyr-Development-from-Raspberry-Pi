#!/usr/bin/env python3
"""Four-panel e-ink mosaic of the hardware block diagram (preview art only).

Virtual canvas is 800x600 1-bit, split into 400x300 tiles:

    tile B (top-left)     tile A (top-right)
    tile C (bottom-left)  tile D (bottom-right)

No text or boxes cross a tile seam (x=400 / y=300). Lines may.
Text is Terminus at integer sizes, 1-bit, no antialiasing or dithering.
Packed the same way as mosaic_hi_lori: MSB = leftmost, 1 = white, 0 = black.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
W, H, TW, TH = 800, 600, 400, 300
SEAM_X, SEAM_Y = 400, 300
TEXT_INSET = 18  # text and important boxes stay this far from a seam
MARGIN = 6
BLACK, WHITE = 0, 255

FONT_TITLE = ImageFont.truetype("/usr/share/fonts/opentype/terminus/terminus-bold.otb", 20)
FONT_BODY = ImageFont.truetype("/usr/share/fonts/truetype/terminus/TerminusTTF-4.46.0.ttf", 18)
FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/terminus/TerminusTTF-4.46.0.ttf", 16)
CW20, CH20 = 10, 20
CW18, CH18 = 10, 18
CW16, CH16 = 8, 16

BOARDS = {
    "B": dict(pos="top-left",     ox=0,   oy=0,
              ficr="944d9a60", ble="CF:CB:94:4D:9A:60",
              swdio=16, swclk=20, nreset=21),
    "A": dict(pos="top-right",    ox=400, oy=0,
              ficr="f15c2668", ble="E4:CD:F1:5C:26:68",
              swdio=24, swclk=25, nreset=23),
    "C": dict(pos="bottom-left",  ox=0,   oy=300,
              ficr="b0749cd0", ble="CA:15:B0:74:9C:D0",
              swdio=13, swclk=19, nreset=26),
    "D": dict(pos="bottom-right", ox=400, oy=300,
              ficr="4bdf4558", ble="F7:97:4B:DF:45:58",
              swdio=22, swclk=27, nreset=17),
}

# Pi-hub copy lives entirely inside each tile's inner corner (not on the seam).
HUB_TEXT = {
    "B": ["Raspberry Pi 5", "SWD  linuxgpiod", "gpiochip4  500 kHz", "nRESET cfg off"],
    "A": ["Raspberry Pi 5", "BLE  hci0  UART", "88:A2:9E:EE:B8:BC", "DFU + UI sync"],
    "C": ["Raspberry Pi 5", "CSI  camera 0", "OV5647  2592x1944", "I2C 0x36  rpicam"],
    "D": ["Raspberry Pi 5", "Ethernet  eth0", "the motherboard Pi", "USB-C 5V   3.3V"],
}

PI_W, PI_H = 160, 76  # title 20 + 3*16 + pad 8; 168 fits the BLE MAC at 8 px/cell


def rect2(d, x0, y0, x1, y1, fill=None, width=2, outline=BLACK):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    if fill is not None:
        d.rectangle([x0, y0, x1, y1], fill=fill)
    for i in range(width):
        d.rectangle([x0 + i, y0 + i, x1 - i, y1 - i], outline=outline)


def hbar(d, x0, x1, y, w=2, fill=BLACK):
    a, b = sorted((int(x0), int(x1)))
    d.rectangle([a, int(y), b, int(y) + w - 1], fill=fill)


def vbar(d, x, y0, y1, w=2, fill=BLACK):
    a, b = sorted((int(y0), int(y1)))
    d.rectangle([int(x), a, int(x) + w - 1, b], fill=fill)


def text(d, x, y, s, font=FONT_BODY, fill=BLACK):
    d.text((int(x), int(y)), s, font=font, fill=fill)


def text_w(s, font=FONT_BODY):
    if font is FONT_TITLE:
        return len(s) * CW20
    if font is FONT_SMALL:
        return len(s) * CW16
    return len(s) * CW18


def boxed(d, x0, y0, x1, y1, lines, pad=3):
    """lines is a list of (font, string). Height must already fit."""
    rect2(d, x0, y0, x1, y1, fill=WHITE, width=2)
    ty = y0 + pad
    for font, s in lines:
        text(d, x0 + pad + 1, ty, s, font=font)
        ty += CH20 if font is FONT_TITLE else (CH16 if font is FONT_SMALL else CH18)
    return y1


def usable(letter):
    b = BOARDS[letter]
    ox, oy = b["ox"], b["oy"]
    left = ox + (TEXT_INSET if ox == SEAM_X else MARGIN)
    right = ox + TW - 1 - (TEXT_INSET if ox == 0 else MARGIN)
    top = oy + (TEXT_INSET if oy == SEAM_Y else MARGIN)
    bot = oy + TH - 1 - (TEXT_INSET if oy == 0 else MARGIN)
    return left, top, right, bot


def pi_rect(letter):
    """Inner-corner Pi box, TEXT_INSET away from any seam."""
    left, top, right, bot = usable(letter)
    b = BOARDS[letter]
    # inner x is toward the vertical seam
    if b["ox"] == 0:
        x1 = right
        x0 = x1 - PI_W + 1
    else:
        x0 = left
        x1 = x0 + PI_W - 1
    if b["oy"] == 0:
        y1 = bot
        y0 = y1 - PI_H + 1
    else:
        y0 = top
        y1 = y0 + PI_H - 1
    return x0, y0, x1, y1


def draw_board(d, letter):
    b = BOARDS[letter]
    ox, oy = b["ox"], b["oy"]
    left, top, right, bot = usable(letter)
    px0, py0, px1, py1 = pi_rect(letter)

    # Per-tile frame, inset from the seam so it does not sit on it.
    fx0 = ox + (3 if ox == 0 else TEXT_INSET - 8)
    fy0 = oy + (3 if oy == 0 else TEXT_INSET - 8)
    fx1 = ox + TW - 1 - (3 if ox == SEAM_X else TEXT_INSET - 8)
    fy1 = oy + TH - 1 - (3 if oy == SEAM_Y else TEXT_INSET - 8)
    # Inner sides run to the tile edge so the frame is not clipped at the
    # bezel; lines may sit on the seam. Outer sides stay inset.
    if ox == 0:
        fx1 = SEAM_X - 1
    else:
        fx0 = SEAM_X
    if oy == 0:
        fy1 = SEAM_Y - 1
    else:
        fy0 = SEAM_Y
    rect2(d, fx0, fy0, fx1, fy1, width=2)

    title_h = CH20 + 8
    # Title always at the TOP of the usable area, but on C/D the Pi box
    # occupies the inner top corner, so the title bar only spans the outer side.
    if oy == 0:
        tx0, tx1 = left, right
        ty0 = top
    else:
        ty0 = top
        if ox == 0:  # C: title on the left, Pi on the right
            tx0, tx1 = left, px0 - 4
        else:        # D: title on the right, Pi on the left
            tx0, tx1 = px1 + 4, right

    ty1 = ty0 + title_h - 1
    rect2(d, tx0, ty0, tx1, ty1, fill=BLACK, width=0)
    title = f"Board {letter}  ({b['pos']})"
    # If the long title does not fit (C/D share the top row with the Pi box),
    # use a short one-line form rather than a taller two-line bar.
    short_pos = {"top-left": "top-left", "top-right": "top-right",
                 "bottom-left": "bot-left", "bottom-right": "bot-right"}[b["pos"]]
    if text_w(title, FONT_TITLE) + 8 > (tx1 - tx0 + 1):
        title = f"Board {letter}  ({short_pos})"
    tw = text_w(title, FONT_TITLE)
    text(d, tx0 + max(4, (tx1 - tx0 + 1 - tw) // 2), ty0 + 4, title,
         font=FONT_TITLE, fill=WHITE)

    # Identity starts under the title. On C/D, stay left/right of the Pi box
    # until we're below it, then go full width.
    y = ty1 + 3
    # 16 px body (cap 10 px). Lines are kept to 25 chars so they also
    # fit in the narrow column beside the Pi box (~204 px).
    ident = [
        (FONT_SMALL, "nRF52832  V_2_1  MCUboot"),
        (FONT_SMALL, f"FICR   {b['ficr']}"),
        (FONT_SMALL, f"BLE    {b['ble']}"),
        (FONT_SMALL, f"SWD  GPIO{b['swdio']}/{b['swclk']}  nRST {b['nreset']} off"),
    ]

    def line_right(yy):
        # If this row horizontally overlaps the Pi box, shrink the right/left.
        if yy <= py1 and yy + CH18 - 1 >= py0:
            if b["ox"] == 0:
                return px0 - 4
            return right
        return right

    def line_left(yy):
        if yy <= py1 and yy + CH18 - 1 >= py0:
            if b["ox"] == SEAM_X:
                return px1 + 4
            return left
        return left

    for font, line in ident:
        text(d, line_left(y), y, line, font=font)
        y += CH16 if font is FONT_SMALL else CH18
    y += 2

    # Peripheral boxes: full usable width once past the Pi box; otherwise dodge it.
    def box_lr(y0, y1):
        # If the box vertically overlaps the Pi box, dodge it.
        if y1 >= py0 and y0 <= py1:
            if b["ox"] == 0:
                return left, px0 - 4
            return px1 + 4, right
        return left, right

    def pick(wide, narrow, width):
        # 8 px/cell for SMALL, 10 px/cell for BODY; leave a 10 px pad.
        out = []
        for font, s in wide:
            budget = (width - 12) // (8 if font is FONT_SMALL else 10)
            if len(s) <= budget:
                out.append((font, s))
            else:
                # fall back to the matching narrow line (same index).
                out.append(narrow[len(out)])
        return out

    epd_w = [
        (FONT_BODY,  'GDEY042T81  4.2"  SSD1683  SPIM0'),
        (FONT_SMALL, "MOSI P0.02  SCK P0.03  CS P0.04  DC P0.05"),
        (FONT_SMALL, "RST P0.06  BUSY P0.07  BS1 P0.08  POW P0.25"),
    ]
    epd_n = [
        (FONT_BODY,  "GDEY042T81  SSD1683"),
        (FONT_SMALL, "SPIM0  MOSI02 SCK03 CS04"),
        (FONT_SMALL, "DC05 RST06 BUSY07 POW25"),
    ]
    eh = 5 + CH18 + 2 * CH16
    bx0, bx1 = box_lr(y, y + eh - 1)
    boxed(d, bx0, y, bx1, y + eh - 1, pick(epd_w, epd_n, bx1 - bx0 + 1))
    y += eh + 2

    tch_w = [
        (FONT_BODY,  "FT6336U  touch  J102  TWIM1  0x38"),
        (FONT_SMALL, "SCL P0.27  SDA P0.28  INT P0.29  RST P0.30"),
    ]
    tch_n = [
        (FONT_BODY,  "FT6336U  J102  0x38"),
        (FONT_SMALL, "SCL27 SDA28 INT29 RST30"),
    ]
    th = 5 + CH18 + CH16
    bx0, bx1 = box_lr(y, y + th - 1)
    boxed(d, bx0, y, bx1, y + th - 1, pick(tch_w, tch_n, bx1 - bx0 + 1))
    y += th + 2

    nand_w = [
        (FONT_BODY,  "MX35LF1GE4AB  1Gb NAND  SPIM2"),
        (FONT_SMALL, "CS15  MISO14  MOSI18  SCLK17  WP13  HOLD16"),
    ]
    nand_n = [
        (FONT_BODY,  "MX35  1Gb NAND  SPIM2"),
        (FONT_SMALL, "CS15 MISO14 MOSI18 SCLK17"),
    ]
    nh = 5 + CH18 + CH16
    bx0, bx1 = box_lr(y, y + nh - 1)
    boxed(d, bx0, y, bx1, y + nh - 1, pick(nand_w, nand_n, bx1 - bx0 + 1))
    y += nh + 2

    # NFC + front light: share the remaining outer width; they must not
    # overlap the Pi box or the bottom usable edge.
    fh = 5 + 2 * CH16
    if y + fh - 1 > bot:
        # Should not happen if the title bar stays 28 px; clip rather than spill.
        print(f"WARN {letter} NFC/FL clipped to bot: y={y} fh={fh} bot={bot}")
        fh = max(8, bot - y + 1)
    bx0, bx1 = box_lr(y, y + fh - 1)
    mid = (bx0 + bx1) // 2
    half = mid - 2 - bx0 + 1
    # 16 px font is 8 px/cell; leave 10 px of pad.
    budget = max(0, (half - 10) // 8)
    if budget >= 13:
        nfc = [(FONT_SMALL, "NFC  Type 2"), (FONT_SMALL, "P0.09 / P0.10")]
        fl = [(FONT_SMALL, "Front light"), (FONT_SMALL, "TPS61042 P0.31")]
    else:
        nfc = [(FONT_SMALL, "NFC Type 2"), (FONT_SMALL, "P0.09/P0.10")]
        fl = [(FONT_SMALL, "Front light"), (FONT_SMALL, "CTRL P0.31")]
    boxed(d, bx0, y, mid - 2, y + fh - 1, nfc)
    boxed(d, mid + 1, y, bx1, y + fh - 1, fl)
    y += fh
    if y - 1 > bot:
        print(f"WARN {letter} content overflow: y={y} bot={bot}")

    # Pi 5 box in the inner corner
    hub_lines = [(FONT_TITLE, HUB_TEXT[letter][0])] + [
        (FONT_SMALL, s) for s in HUB_TEXT[letter][1:]
    ]
    boxed(d, px0, py0, px1, py1, hub_lines, pad=4)

    # 2 px leader from the Pi box toward the canvas centre (may cross the seam).
    cx, cy = SEAM_X, SEAM_Y
    # Start at the inner corner of the Pi box.
    if b["ox"] == 0:
        sx = px1
    else:
        sx = px0
    if b["oy"] == 0:
        sy = py1
    else:
        sy = py0
    # Orthogonal: go to a point near the centre, stopping a few px short of
    # the exact seam crossing if we want a visible stub into the margin.
    # Stop in the seam margin so the line points at the bezel, not into it.
    end_x = cx - 8 if b["ox"] == 0 else cx + 7
    end_y = cy - 8 if b["oy"] == 0 else cy + 7
    ly = sy - 1 if b["oy"] == 0 else sy
    if b["ox"] == 0:
        hbar(d, sx, end_x, ly, w=2)
        vbar(d, end_x, ly, end_y, w=2)
    else:
        hbar(d, end_x, sx, ly, w=2)
        vbar(d, end_x, ly, end_y, w=2)


def to_1bit(img_l):
    # getdata() is the flattened pixel sequence on Pillow 10 (Ubuntu 24.04).
    levels = set(img_l.getdata())
    if not set(levels).issubset({0, 255}):
        raise SystemExit(f"non-binary pixels present: {sorted(levels)[:12]}...")
    return img_l.convert("1", dither=Image.Dither.NONE)


def preview_bezels(tiles):
    gap, margin = 20, 16
    cw = margin + TW + gap + TW + margin
    ch = margin + TH + gap + TH + margin
    paper = (244, 238, 220)
    ink = (16, 16, 14)
    bg = (36, 36, 34)
    canvas = Image.new("RGB", (cw, ch), bg)
    order = [("B", 0, 0), ("A", 1, 0), ("C", 0, 1), ("D", 1, 1)]
    for letter, col, row in order:
        tile = tiles[letter].convert("L")
        rgb = Image.new("RGB", (TW, TH))
        src = tile.load()
        dst = rgb.load()
        for y in range(TH):
            for x in range(TW):
                dst[x, y] = paper if src[x, y] >= 128 else ink
        canvas.paste(rgb, (margin + col * (TW + gap), margin + row * (TH + gap)))
    return canvas.resize((cw * 2, ch * 2), Image.Resampling.NEAREST)


def seam_text_report(full_1):
    """Flag any black pixel of... we just report ink near seams for a sanity check."""
    pix = full_1.convert("L").load()
    def ink_in(x0, y0, x1, y1):
        n = 0
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if 0 <= x < W and 0 <= y < H and pix[x, y] < 128:
                    n += 1
        return n
    # A 1 px strip on the seam itself should only contain crossing lines.
    print("ink on vertical seam x=399..400:", ink_in(399, 0, 400, 599))
    print("ink on horizontal seam y=299..300:", ink_in(0, 299, 799, 300))


def draw():
    OUT.mkdir(parents=True, exist_ok=True)
    img = Image.new("L", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    for letter in "BADC":
        draw_board(d, letter)

    full = to_1bit(img)
    full.save(OUT / "mosaic_800x600.png")

    tiles = {}
    names = {"B": "tile_B.png", "A": "tile_A.png", "C": "tile_C.png", "D": "tile_D.png"}
    for letter, b in BOARDS.items():
        tile = full.crop((b["ox"], b["oy"], b["ox"] + TW, b["oy"] + TH))
        assert tile.size == (400, 300) and tile.mode == "1"
        tile.save(OUT / names[letter])
        tiles[letter] = tile

    prev = preview_bezels(tiles)
    prev.save(OUT / "preview_bezels.png")

    print(f"wrote {OUT / 'mosaic_800x600.png'}  mode={full.mode} size={full.size}")
    for letter in "ABCD":
        print(f"  {names[letter]}  mode={tiles[letter].mode} size={tiles[letter].size}")
    print(f"  preview_bezels.png  size={prev.size}")
    for letter in "BADC":
        print(f"{letter} usable={usable(letter)}  pi={pi_rect(letter)}")
    seam_text_report(full)


def write_header(full, tiles, path):
    """Same packing as mosaic_hi_lori art/make_art.py (MSB leftmost, 1=white)."""
    order = ["B", "A", "C", "D"]  # tile0..3
    blobs = [tiles[k].tobytes() for k in order]
    assert all(len(b) == 15000 for b in blobs)
    with open(path, "w") as h:
        h.write(
            "/* Auto-generated by make_mosaic.py — hardware block-diagram mosaic.\n"
            " * 1 bit/pixel, MSB = leftmost, 1 = white, 0 = black, rows of 50 bytes.\n"
            " * tile0=top-left(B) tile1=top-right(A) tile2=bottom-left(C) tile3=bottom-right(D). */\n"
            "#pragma once\n#include <stdint.h>\n#define MOSAIC_TILE_BYTES 15000U\n"
            "static const uint8_t mosaic_tiles[4][MOSAIC_TILE_BYTES] = {\n"
        )
        for b in blobs:
            h.write("{\n")
            for i in range(0, len(b), 25):
                h.write("".join(f"0x{v:02X}," for v in b[i:i + 25]) + "\n")
            h.write("},\n")
        h.write("};\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    import sys
    draw()
    if "--header" in sys.argv:
        from PIL import Image
        full = Image.open(OUT / "mosaic_800x600.png")
        tiles = {L: Image.open(OUT / f"tile_{L}.png") for L in "ABCD"}
        write_header(full, tiles, OUT / "mosaic_tiles.h")
