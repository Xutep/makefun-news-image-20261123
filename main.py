#!/usr/bin/env python3
"""News-image entry for make.fun: news-image-20261123.

Draws one 1024x1024 PNG that sums up Monday 23 November 2026's world news:
a newspaper front page with six stories from that day (COP31 collapse, Iran
striking US bases in Bahrain, a Russian drone strike in the Kyiv region, a
deadly factory fire in Indonesia, Mexico capturing 'El Chapo Isidro', and
South Korea's education minister resigning over an AI exam-cheating scandal),
plus a sports / UN footer line.

Pure Python standard library, fully deterministic: no network, no clock, no
randomness. The same bytes are written on every run. The PNG is encoded by
hand (zlib + struct) and all text is rendered with a small built-in 5x7
bitmap font, so the program needs no fonts or image libraries.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# --------------------------------------------------------------------------
# Palette
# --------------------------------------------------------------------------
PAPER = (246, 241, 231)
CARD = (255, 255, 255)
CARD_EDGE = (216, 210, 196)
INK = (26, 26, 26)
MUTED = (90, 90, 90)
NAVY = (22, 35, 63)
GOLD = (201, 162, 39)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# --------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is 7 rows of 5 bits, '1' = ink.
# Only the characters this entry prints are defined.
# --------------------------------------------------------------------------
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
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
}

CHAR_W = 6  # 5 glyph columns + 1 column of spacing
CHAR_H = 7


def text_width(text, scale):
    """Pixel width of `text` rendered at `scale` (no trailing spacing)."""
    if not text:
        return 0
    return len(text) * CHAR_W * scale - scale


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines fitting `max_width` px."""
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        line = ""
        for word in words:
            trial = word if not line else line + " " + word
            if text_width(trial, scale) <= max_width or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


# --------------------------------------------------------------------------
# Canvas: an RGB bytearray with simple filled-shape drawing.
# --------------------------------------------------------------------------
class Canvas:
    def __init__(self, width, height, bg):
        self.w = width
        self.h = height
        self.pix = bytearray(bytes(bg) * (width * height))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.pix[i] = color[0]
            self.pix[i + 1] = color[1]
            self.pix[i + 2] = color[2]

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.pix[i] = color[0]
                self.pix[i + 1] = color[1]
                self.pix[i + 2] = color[2]

    def hline(self, x, y, w, color):
        self.rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.rect(x, y, 1, h, color)

    def line(self, x0, y0, x1, y1, color):
        """Bresenham line, 1 px thick."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
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

    def thick_line(self, x0, y0, x1, y1, color, thick):
        for k in range(-(thick // 2), thick // 2 + 1):
            if abs(x1 - x0) >= abs(y1 - y0):
                self.line(x0, y0 + k, x1, y1 + k, color)
            else:
                self.line(x0 + k, y0, x1 + k, y1, color)

    def disc(self, cx, cy, r, color):
        """Filled circle."""
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            half = int(math.sqrt(max(0, r * r - dy * dy)))
            self.rect(cx - half, yy, half * 2 + 1, 1, color)

    def ring(self, cx, cy, r, color, thick=2):
        for t in range(thick):
            rr = r - t
            for yy in range(cy - rr, cy + rr + 1):
                dy = yy - cy
                half = int(math.sqrt(max(0, rr * rr - dy * dy)))
                self.set(cx - half, yy, color)
                self.set(cx + half, yy, color)

    def poly(self, points, color):
        """Filled polygon (scanline fill)."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                    xs.append(x)
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.rect(int(math.ceil(xs[k])), y,
                          max(1, int(math.floor(xs[k + 1])) - int(math.ceil(xs[k])) + 1),
                          1, color)

    def star(self, cx, cy, r_out, r_in, color):
        pts = []
        for i in range(10):
            r = r_out if i % 2 == 0 else r_in
            ang = -math.pi / 2 + i * math.pi / 5
            pts.append((int(cx + r * math.cos(ang)), int(cy + r * math.sin(ang))))
        self.poly(pts, color)

    def text(self, x, y, s, color, scale=2):
        """Draw text with the bitmap font; returns the pixel width drawn."""
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT["?"])
            for row in range(CHAR_H):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += CHAR_W * scale
        return cx - x - scale

    def text_center(self, y, s, color, scale=2):
        w = text_width(s, scale)
        self.text((self.w - w) // 2, y, s, color, scale)


# --------------------------------------------------------------------------
# PNG encoding (hand-rolled, deterministic: fixed zlib level, no metadata).
# --------------------------------------------------------------------------
def _chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data +
            struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def encode_png(canvas):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        raw += canvas.pix[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
            _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b""))


def tint(color, frac):
    """Mix `color` toward white by `frac` (0 = color, 1 = white)."""
    return tuple(int(c + (255 - c) * frac) for c in color)


# --------------------------------------------------------------------------
# Pictograms. Each draws a small scene inside the band (bx, by, bw, bh).
# --------------------------------------------------------------------------
def pic_globe(c, bx, by, bw, bh):
    cx, cy, r = bx + bw // 2 - 30, by + bh // 2, 34
    c.disc(cx, cy, r, (46, 111, 183))            # ocean
    c.disc(cx - 12, cy - 8, 10, (76, 175, 80))   # land blobs
    c.disc(cx + 10, cy + 10, 12, (76, 175, 80))
    c.disc(cx + 14, cy - 14, 7, (129, 199, 132))
    c.rect(cx - r, cy - 2, r * 2, 3, (255, 255, 255))  # equator hint
    c.rect(cx - r + 6, cy - 20, r * 2 - 12, 2, (255, 255, 255))
    # rising thermometer of a warming planet
    tx = bx + bw - 78
    c.rect(tx, by + 14, 10, 52, (183, 28, 28))
    c.rect(tx + 2, by + 18, 6, 34, (255, 255, 255))
    c.rect(tx + 2, by + 40, 6, 12, (183, 28, 28))
    c.disc(tx + 5, by + 62, 9, (183, 28, 28))
    c.text(tx + 16, by + 20, "HOT", (183, 28, 28), 2)


def pic_fire(c, bx, by, bw, bh):
    base = by + bh - 12
    # dark city silhouette
    c.rect(bx + 30, base - 34, 60, 34, (38, 38, 48))
    c.rect(bx + 110, base - 48, 54, 48, (52, 52, 66))
    c.rect(bx + 184, base - 28, 70, 28, (38, 38, 48))
    c.rect(bx + 274, base - 40, 56, 40, (52, 52, 66))
    # windows
    for wx in (bx + 42, bx + 66, bx + 122, bx + 146, bx + 196, bx + 220, bx + 286, bx + 310):
        c.rect(wx, base - 24, 8, 10, (255, 213, 79))
    # flames above the rooftops (kept inside the band)
    c.poly([(bx + 48, base - 34), (bx + 62, base - 58), (bx + 76, base - 34)],
           (255, 87, 34))
    c.poly([(bx + 128, base - 48), (bx + 140, base - 62), (bx + 154, base - 48)],
           (255, 152, 0))
    c.poly([(bx + 136, base - 48), (bx + 142, base - 58), (bx + 148, base - 48)],
           (255, 235, 59))
    c.poly([(bx + 292, base - 40), (bx + 304, base - 56), (bx + 316, base - 40)],
           (255, 87, 34))
    # smoke
    c.disc(bx + 62, base - 66, 10, (120, 120, 120))
    c.disc(bx + 140, base - 70, 12, (120, 120, 120))
    c.disc(bx + 304, base - 64, 9, (120, 120, 120))


def pic_drone(c, bx, by, bw, bh):
    cx, cy = bx + bw // 2, by + 34
    # rotors
    for rx in (cx - 52, cx + 52):
        c.rect(rx - 26, cy - 16, 52, 5, (26, 26, 26))
        c.disc(rx, cy - 13, 4, (26, 26, 26))
    # arms and body
    c.thick_line(cx - 52, cy - 12, cx - 12, cy, (26, 26, 26), 4)
    c.thick_line(cx + 52, cy - 12, cx + 12, cy, (26, 26, 26), 4)
    c.rect(cx - 16, cy - 8, 32, 16, (21, 101, 192))
    c.disc(cx, cy + 12, 5, (183, 28, 28))  # payload light
    # building below, hit
    base = by + bh - 10
    c.rect(bx + 150, base - 30, 130, 30, (90, 90, 100))
    c.rect(bx + 150, base - 30, 130, 4, (60, 60, 70))
    for wx in range(bx + 160, bx + 272, 18):
        c.rect(wx, base - 22, 9, 9, (255, 213, 79))
    c.thick_line(bx + 215, base - 30, bx + 205, base - 12, (183, 28, 28), 3)
    c.thick_line(bx + 215, base - 30, bx + 228, base - 14, (183, 28, 28), 3)
    c.text(bx + 300, base - 26, "14 MISSING", (183, 28, 28), 2)


def pic_factory(c, bx, by, bw, bh):
    base = by + bh - 10
    # factory body with sawtooth roof
    c.poly([(bx + 60, base), (bx + 60, base - 34), (bx + 100, base - 52),
            (bx + 140, base - 34), (bx + 180, base - 52), (bx + 220, base - 34),
            (bx + 220, base)], (66, 66, 76))
    c.rect(bx + 240, base - 70, 16, 70, (66, 66, 76))  # chimney
    c.rect(bx + 236, base - 76, 24, 8, (52, 52, 62))
    # flame bursting from the roof (kept inside the band)
    c.poly([(bx + 96, base - 48), (bx + 118, base - 62), (bx + 140, base - 48)],
           (255, 87, 34))
    c.poly([(bx + 112, base - 48), (bx + 120, base - 56), (bx + 128, base - 48)],
           (255, 235, 59))
    # smoke from the chimney (kept inside the band)
    c.disc(bx + 248, base - 66, 7, (120, 120, 120))
    c.disc(bx + 260, base - 72, 8, (140, 140, 140))
    # windows
    for wx in (bx + 72, bx + 96, bx + 120, bx + 144, bx + 168, bx + 192):
        c.rect(wx, base - 22, 10, 12, (255, 213, 79))
    c.text(bx + 300, base - 30, "RESCUE", (183, 28, 28), 2)
    c.text(bx + 300, base - 12, "GOES ON", (183, 28, 28), 2)


def pic_badge(c, bx, by, bw, bh):
    cx, cy = bx + bw // 2 - 40, by + bh // 2
    # gold shield
    c.poly([(cx - 34, cy - 34), (cx + 34, cy - 34), (cx + 34, cy + 2),
            (cx, cy + 38), (cx - 34, cy + 2)], (201, 162, 39))
    c.poly([(cx - 26, cy - 26), (cx + 26, cy - 26), (cx + 26, cy + 2),
            (cx, cy + 30), (cx - 26, cy + 2)], (21, 101, 192))
    c.star(cx, cy - 2, 20, 8, (255, 255, 255))
    # handcuffs
    c.ring(bx + bw - 96, by + 26, 12, (38, 38, 48), 4)
    c.ring(bx + bw - 62, by + 56, 12, (38, 38, 48), 4)
    c.thick_line(bx + bw - 88, by + 36, bx + bw - 70, by + 48, (38, 38, 48), 4)


def pic_chip(c, bx, by, bw, bh):
    cx, cy = bx + bw // 2 - 30, by + bh // 2
    # chip pins
    for k in range(4):
        c.rect(cx - 34, cy - 24 + k * 16, 12, 6, (90, 90, 90))
        c.rect(cx + 30, cy - 24 + k * 16, 12, 6, (90, 90, 90))
        c.rect(cx - 24 + k * 16, cy - 34, 6, 12, (90, 90, 90))
        c.rect(cx - 24 + k * 16, cy + 30, 6, 12, (90, 90, 90))
    # chip body
    c.rect(cx - 26, cy - 26, 52, 52, (31, 41, 55))
    c.rect(cx - 26, cy - 26, 52, 4, (90, 90, 90))
    c.text(cx - 15, cy - 14, "AI", WHITE, 4)
    # graduation cap above the chip
    cap_y = by + 8
    c.poly([(bx + bw - 120, cap_y + 14), (bx + bw - 76, cap_y),
            (bx + bw - 32, cap_y + 14), (bx + bw - 76, cap_y + 28)],
           (22, 35, 63))
    c.rect(bx + bw - 92, cap_y + 16, 32, 12, (22, 35, 63))
    c.vline(bx + bw - 34, cap_y + 14, 22, (201, 162, 39))
    c.disc(bx + bw - 34, cap_y + 38, 4, (201, 162, 39))


# --------------------------------------------------------------------------
# Stories of Monday 23 November 2026.
# --------------------------------------------------------------------------
STORIES = [
    ("CLIMATE - COP31", (46, 125, 50),
     "CLIMATE TALKS FAIL: NO DEAL",
     "NATIONS SPLIT OVER FOSSIL-FUEL WORDING AS THE EU REJECTS A TEXT "
     "WITH NO PHASE-OUT.",
     pic_globe),
    ("MIDDLE EAST - GULF", (183, 28, 28),
     "IRAN STRIKES US BASES IN BAHRAIN",
     "TEHRAN HITS TWO BASES IN RETALIATION. GULF SHIPPING ON ALERT "
     "AFTER A TANKER INCIDENT.",
     pic_fire),
    ("UKRAINE - WAR", (21, 101, 192),
     "DRONE HITS KYIV REGION BUILDING",
     "AT LEAST 14 PEOPLE MISSING AFTER THE STRIKE, KYIV SAYS. "
     "A SHIP BURNS OFF FINLAND.",
     pic_drone),
    ("ASIA - INDONESIA", (230, 81, 0),
     "DEADLY FIRE AT INDONESIA FACTORY",
     "DOZENS KILLED AND MISSING AFTER A BLAZE AT A CANDY FACTORY. "
     "RESCUERS KEEP SEARCHING.",
     pic_factory),
    ("AMERICAS - MEXICO", (106, 27, 154),
     "MEXICO SEIZES 'EL CHAPO ISIDRO'",
     "FBI MOST-WANTED CARTEL BOSS CAPTURED AFTER GUNFIGHTS IN "
     "SINALOA KILL 11.",
     pic_badge),
    ("SOCIETY - EDUCATION", (0, 105, 92),
     "SEOUL MINISTER QUITS OVER AI CHEATING",
     "SOUTH KOREA'S EDUCATION CHIEF RESIGNS AMID AN AI-DRIVEN "
     "EXAM SCANDAL.",
     pic_chip),
]

FOOTER_LINES = [
    "ALSO: INDIA POST A RECORD 720/9 IN THE WELLINGTON TEST",
    "UN NATIONS AGREE TO KEEP TALKING ON LETHAL AI WEAPONS",
]


def draw_panel(c, x, y, w, h, story):
    tag, color, headline, summary, pic = story
    c.rect(x, y, w, h, CARD)
    c.rect(x, y, w, h, CARD_EDGE)  # border (drawn as outline below)
    c.rect(x + 1, y + 1, w - 2, h - 2, CARD)
    c.rect(x, y, w, 8, color)  # accent bar
    c.text(x + 16, y + 20, tag, color, 2)
    head_lines = wrap_text(headline, w - 32, 3)
    yy = y + 46
    for line in head_lines[:2]:
        c.text(x + 16, yy, line, INK, 3)
        yy += 26
    sum_lines = wrap_text(summary, w - 32, 2)
    yy = y + 104
    for line in sum_lines[:3]:
        c.text(x + 16, yy, line, MUTED, 2)
        yy += 18
    band_y = y + 164
    band_h = h - 164 - 14
    c.rect(x + 16, band_y, w - 32, band_h, tint(color, 0.88))
    pic(c, x + 16, band_y, w - 32, band_h)


def build_image():
    c = Canvas(W, H, PAPER)
    # Masthead
    c.rect(0, 0, W, 132, NAVY)
    c.text_center(20, "THE WORLD IN ONE DAY", WHITE, 5)
    c.rect(212, 66, 600, 3, GOLD)
    c.text_center(80, "MONDAY 23 NOVEMBER 2026", GOLD, 4)
    # Story grid: 2 columns x 3 rows
    margin, gap = 16, 12
    pw = (W - margin * 2 - gap) // 2
    ph = 264
    for i, story in enumerate(STORIES):
        col = i % 2
        row = i // 2
        x = margin + col * (pw + gap)
        y = 148 + row * (ph + gap)
        draw_panel(c, x, y, pw, ph, story)
    # Footer strip
    fy = 972
    c.rect(0, fy, W, H - fy, NAVY)
    c.text_center(fy + 8, FOOTER_LINES[0], WHITE, 2)
    c.text_center(fy + 28, FOOTER_LINES[1], GOLD, 2)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(build_image())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
