#!/usr/bin/env python3
"""THE WORLD TODAY - front page for Tuesday 24 November 2026.

Draws a 1024x1024 newspaper front page summing up the day's world news
and writes it to $MAKEFUN_OUTPUT_DIR/entry.png (or /output/entry.png).

Pure Python 3 standard library: a hand-rolled PNG encoder (zlib +
struct), a hand-defined 5x7 bitmap font, and basic shape drawing.
No network, no downloaded assets - every pixel is drawn by this code.
"""

import os
import struct
import sys
import time
import zlib

W, H = 1024, 1024

PAPER = (246, 240, 226)
INK = (22, 22, 32)
NAVY = (20, 33, 61)
RED = (178, 28, 28)
GOLD = (176, 141, 45)
GREY = (96, 96, 96)
WHITE = (255, 255, 255)
ORANGE = (214, 110, 30)

# ---------------------------------------------------------------- font
# 5x7 bitmap glyphs, defined here by hand. '#' = on, '.' = off.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
}

CHAR_W = 6  # glyph advance in font units (5 px + 1 px gap)


def text_width(text, scale):
    return len(text) * CHAR_W * scale - scale


def wrap_text(text, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def hline(self, x0, x1, y, color):
        for x in range(max(0, x0), min(self.w, x1 + 1)):
            self.set(x, y, color)

    def vline(self, x, y0, y1, color):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            self.set(x, y, color)

    def line(self, x0, y0, x1, y1, color):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def fill_rect(self, x, y, w, h, color):
        for yy in range(max(0, y), min(self.h, y + h)):
            i = (yy * self.w + max(0, x)) * 3
            n = min(self.w, x + w) - max(0, x)
            if n > 0:
                self.px[i:i + n * 3] = bytes(color) * n

    def rect(self, x, y, w, h, color, thick=1):
        for t in range(thick):
            self.hline(x, x + w - 1, y + t, color)
            self.hline(x, x + w - 1, y + h - 1 - t, color)
            self.vline(x + t, y, y + h - 1, color)
            self.vline(x + w - 1 - t, y, y + h - 1, color)

    def disc(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.hline(cx - dx, cx + dx, cy + dy, color)

    def circle(self, cx, cy, r, color):
        # Midpoint circle outline.
        x, y, d = 0, r, 1 - r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                           (cx + x, cy - y), (cx - x, cy - y),
                           (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                self.set(px, py, color)
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, color)
            cx += CHAR_W * scale
        return cx

    def text_centered(self, y, s, scale, color):
        x = (self.w - text_width(s, scale)) // 2
        self.text(x, y, s, scale, color)


# ---------------------------------------------------------------- icons
def icon_chip(cv, x, y, s, color):
    # Microchip: body, inner die, pins on four sides.
    cv.rect(x + 8, y + 8, s - 16, s - 16, color, 3)
    cv.rect(x + s // 3, y + s // 3, s // 3, s // 3, color, 2)
    for i in range(3):
        off = 18 + i * (s - 36) // 2
        cv.vline(x + off, y, y + 8, color)
        cv.vline(x + off, y + s - 8, y + s, color)
        cv.hline(x, x + 8, y + off, color)
        cv.hline(x + s - 8, x + s, y + off, color)


def icon_burst(cv, x, y, s, color):
    # Explosion / strike burst.
    cx, cy = x + s // 2, y + s // 2
    cv.disc(cx, cy, s // 6, color)
    for k in range(8):
        ang = k * 3.14159265 / 4
        dx = int((s // 2 - 4) * (1 if abs(ang) < 0.01 else 0))
        import math
        ex = cx + int(math.cos(ang) * (s // 2 - 2))
        ey = cy + int(math.sin(ang) * (s // 2 - 2))
        sx = cx + int(math.cos(ang) * (s // 6 + 2))
        sy = cy + int(math.sin(ang) * (s // 6 + 2))
        cv.line(sx, sy, ex, ey, color)


def icon_flame(cv, x, y, s, color):
    # Flame: stacked discs in warm colours, narrowing upward.
    cx = x + s // 2
    cv.disc(cx, y + s - 14, 16, color)
    cv.disc(cx, y + s - 30, 12, ORANGE)
    cv.disc(cx, y + s - 44, 8, GOLD)
    cv.disc(cx, y + s - 52, 4, GOLD)
    cv.disc(cx, y + s - 14, 8, ORANGE)


def icon_crowd(cv, x, y, s, color):
    # Three heads over three shoulders.
    for i, dx in enumerate((-22, 0, 22)):
        cx = x + s // 2 + dx
        cy = y + s // 2 - 8
        cv.disc(cx, cy, 11, color)
        cv.fill_rect(cx - 14, cy + 13, 28, 20, color)
    cv.fill_rect(x + 6, y + s - 8, s - 12, 4, color)


def icon_globe(cv, x, y, s, color):
    cx, cy, r = x + s // 2, y + s // 2, s // 2 - 4
    cv.circle(cx, cy, r, color)
    cv.hline(cx - r, cx + r, cy, color)
    cv.hline(cx - int(r * 0.87), cx + int(r * 0.87), cy - r // 2, color)
    cv.hline(cx - int(r * 0.87), cx + int(r * 0.87), cy + r // 2, color)
    cv.vline(cx, cy - r, cy + r, color)
    cv.line(cx - int(r * 0.6), cy - int(r * 0.8),
            cx + int(r * 0.6), cy + int(r * 0.8), color)


def icon_pawn(cv, x, y, s, color):
    # Chess pawn: head, collar, base.
    cx = x + s // 2
    cv.disc(cx, y + 14, 11, color)
    cv.fill_rect(cx - 16, y + 30, 32, 5, color)
    cv.line(cx - 12, y + 35, cx - 20, y + s - 12, color)
    cv.line(cx + 12, y + 35, cx + 20, y + s - 12, color)
    cv.fill_rect(cx - 22, y + s - 12, 44, 6, color)


# ---------------------------------------------------------------- layout
PANELS = [
    ("WAR IN UKRAINE", "RUSSIAN STRIKES HIT KYIV",
     "DRONE AND MISSILE STRIKES KILL AT LEAST 12 IN THE KYIV "
     "REGION. RUSSIAN CARGO SHIP SPARTA II BURNS IN THE GULF OF "
     "FINLAND AFTER A DRONE ATTACK.", icon_burst),
    ("INDONESIA", "FACTORY FIRE IN BANTEN",
     "AT LEAST 24 WORKERS ARE KILLED IN A FACTORY FIRE IN BANTEN, "
     "INDONESIA. THE SEARCH FOR THE MISSING CONTINUES.", icon_flame),
    ("PORTUGAL", "LISBON MARCHES ON COST OF LIVING",
     "THOUSANDS MARCH IN LISBON, PORTUGAL, TO PROTEST THE COST OF "
     "LIVING AS HOUSEHOLD BUDGETS ARE SQUEEZED.", icon_crowd),
    ("CLIMATE", "COP31 SPLIT ON FOSSIL FUELS",
     "CLIMATE TALKS IN ANTALYA, TURKIYE, REMAIN DIVIDED OVER FOSSIL "
     "FUELS AS COP31 DELEGATES SEARCH FOR A DEAL.", icon_globe),
    ("SPORT", "GUKESH DEFENDS CROWN",
     "GUKESH DEFENDS HIS WORLD CHESS CROWN AGAINST SINDAROV IN "
     "GENEVA. ALCARAZ WINS HIS FIRST ATP FINALS. VERSTAPPEN WINS "
     "IN LAS VEGAS.", icon_pawn),
]

INSIDE = [
    "NVIDIA - HUANG RETURNS",
    "KYIV UNDER ATTACK",
    "BANTEN FACTORY FIRE",
    "LISBON COST PROTESTS",
    "COP31 CLIMATE SPLIT",
    "SPORT - CHESS, TENNIS, F1",
]


def draw_panel(cv, x, y, w, h, kicker, title, body, icon_fn):
    cv.fill_rect(x, y, w, h, WHITE)
    cv.rect(x, y, w, h, INK, 2)
    pad = 14
    # Kicker.
    cv.text(x + pad, y + pad, kicker, 2, RED)
    # Icon, top right.
    icon_fn(cv, x + w - pad - 56, y + pad + 4, 56, INK)
    # Title, wrapped to leave room for the icon on its first lines.
    title_lines = wrap_text(title, 3, w - pad * 2 - 70)
    ty = y + pad + 24
    for ln in title_lines:
        cv.text(x + pad, ty, ln, 3, INK)
        ty += 27
    # Body, full panel width, always starting below the icon so a
    # one-line title can never collide with it.
    body_lines = wrap_text(body, 2, w - pad * 2)
    by = max(ty + 6, y + pad + 24 + 56 + 8)
    for ln in body_lines[:4]:
        cv.text(x + pad, by, ln, 2, INK)
        by += 19


def draw_inside(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, NAVY)
    cv.rect(x, y, w, h, INK, 2)
    pad = 14
    cv.text(x + pad, y + pad, "INSIDE TODAY", 2, GOLD)
    ly = y + pad + 26
    for item in INSIDE:
        cv.fill_rect(x + pad, ly + 4, 7, 7, RED)
        cv.text(x + pad + 14, ly, item, 2, WHITE)
        ly += 22


def draw_page(cv):
    # Masthead.
    cv.fill_rect(0, 0, W, 118, NAVY)
    cv.text_centered(20, "THE WORLD TODAY", 7, WHITE)
    cv.text_centered(80, "TUESDAY, 24 NOVEMBER 2026", 2, GOLD)
    cv.fill_rect(0, 118, W, 5, RED)
    cv.fill_rect(0, 127, W, 2, INK)

    # Lead story.
    lx, ly, lw, lh = 16, 142, 992, 244
    cv.fill_rect(lx, ly, lw, lh, WHITE)
    cv.rect(lx, ly, lw, lh, INK, 3)
    cv.text(lx + 18, ly + 16, "TOP STORY", 2, RED)
    icon_chip(cv, lx + lw - 150, ly + 22, 120, NAVY)
    cv.text(lx + 18, ly + 48, "HUANG BACK AT", 5, INK)
    cv.text(lx + 18, ly + 93, "NVIDIA HELM", 5, INK)
    lead = ("NVIDIA SHARES SOAR ABOUT 31% IN A DAY, ADDING NEARLY $1 "
            "TRILLION IN VALUE AS JENSEN HUANG RETURNS AS CHIEF "
            "EXECUTIVE.")
    by = ly + 152
    for ln in wrap_text(lead, 2, lw - 36 - 150):
        cv.text(lx + 18, by, ln, 2, INK)
        by += 19
    cv.text(lx + 18, ly + lh - 26, "MARKETS  -  SHARES JUMP AS FOUNDER RETURNS",
            2, GREY)

    # Grid: 2 columns x 3 rows; last cell is the index box.
    gx, gy = 16, 400
    cw, ch, gap = 491, 186, 10
    cells = [(gx, gy), (gx + cw + gap, gy),
             (gx, gy + ch + gap), (gx + cw + gap, gy + ch + gap),
             (gx, gy + 2 * (ch + gap)), (gx + cw + gap, gy + 2 * (ch + gap))]
    for (kicker, title, body, icon_fn), (px, py) in zip(PANELS, cells[:5]):
        draw_panel(cv, px, py, cw, ch, kicker, title, body, icon_fn)
    draw_inside(cv, *cells[5], cw, ch)

    # Footer.
    cv.fill_rect(0, 992, W, 2, INK)
    cv.text_centered(1000, "THE WORLD TODAY - ONE DAY, ONE PAGE - 24 NOVEMBER 2026",
                    1, GREY)


# ---------------------------------------------------------------- png
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    t0 = time.time()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = Canvas(W, H, PAPER)
    draw_page(cv)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(path, cv)
    dt = time.time() - t0
    print(f"wrote {path} ({cv.w}x{cv.h}, {size} bytes) in {dt:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
