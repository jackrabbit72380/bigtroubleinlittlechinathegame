"""White Tiger Bar: the bar itself, with its rooms behind beaded curtains.

Painted from the plan reference: jade striped wallpaper over a red lacquer
wainscot, brass candle sconces, a back bar of mirrors and bottles with the sign
hung low over the counter, a bead curtain onto a room with the red bed standing
in it, and the lounge's velvet chairs and round table at the other end. The
floor is polished boards carrying the warm light of the room.

A stage is seen across the play plane, so the bar is painted as a wall
wall-to-wall: the counter runs against the back wall, its foot rail and front
panel stop above the floor line, and the fighters stand on the boards in front
of it. Chairs, table, bed and curtains all sit in the wall band behind that
line, so nothing comes out to stand on anybody's feet.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960, localcoord 1920x1080, camera travel +/-3136.

Run:  python3 tools/stage_white_tiger_bar.py     (part of tools/build_all.py)
"""

from __future__ import annotations

import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import stages_hd as hd

W, H = hd.W, hd.H
CX, FLOOR_Y, px = hd.CX, hd.FLOOR_Y, hd.px

CEIL = px(62)                      # 279: ceiling band, where the wallpaper starts
WAIN_Y = px(146)                   # 657: the top of the red lacquer wainscot
PLINTH = FLOOR_Y - px(14)          # 837: the skirting meets the boards
COUNTER_Y = px(114)                # 513: the bar counter's top surface
BAY_A = (px(64), px(546))          # the room behind the bead curtain
BAY_B = (px(576), px(1244))        # the bar
BAY_C = (px(1272), px(1756))       # the lounge
PIER_A, PIER_B = px(560), px(1258)  # the pilasters between the bays
SIGN = (px(716), px(1104))         # the sign over the counter, centred on CX
SIGN_Y = (px(40), px(96))

JADE = (72, 100, 80)               # the striped wallpaper
JADE_L = (104, 132, 102)
JADE_D = (48, 70, 56)
LAC = (122, 30, 24)                # red lacquer
LAC_L = (162, 52, 40)
LAC_D = (74, 16, 14)
GOLD = (178, 138, 66)
GOLD_L = (238, 204, 132)
BOARD = (52, 36, 28)               # the polished floor
BOARD_L = (78, 54, 40)
VELVET = (100, 30, 32)
VELVET_L = (128, 44, 42)
VELVET_D = (62, 18, 20)
PAPER = (236, 214, 170)            # lantern paper
RED = (156, 34, 26)
WARM = (255, 202, 138)

LIGHTS = []


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def tint(c, rnd, amt=0.07):
    return tuple(max(0, min(255, int(v * (1 + rnd.uniform(-amt, amt))))) for v in c)


def box(x0, y0, x1, y1):
    """Normalised corners: PIL refuses a rectangle drawn bottom-up."""
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def lamp(cx, cy, r, color=WARM, peak=150):
    LIGHTS.append((cx, cy, r, color, peak))


# ------------------------------------------------------------------ the room
def ceiling(base):
    """A low painted ceiling with a beam over every bay, and its cornice."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, 0, W, CEIL), fill=(22, 17, 16))
    for x in range(-px(20), W, px(150)):
        d.rectangle(box(x, 0, x + px(20), CEIL), fill=(30, 23, 20))
        d.line([(x, 0), (x, CEIL)], fill=(46, 34, 28), width=max(1, int(px(0.8))))
        d.line([(x + px(20), 0), (x + px(20), CEIL)], fill=(10, 8, 7),
               width=max(1, int(px(1.0))))
    # the cornice where the ceiling meets the wall, catching a little light
    d.rectangle(box(0, CEIL - px(7), W, CEIL), fill=mix(GOLD, (52, 40, 26), 0.72))
    d.line([(0, CEIL - px(7)), (W, CEIL - px(7))], fill=mix(GOLD, (150, 126, 92), 0.5),
           width=max(1, int(px(0.9))))
    d.line([(0, CEIL), (W, CEIL)], fill=(10, 8, 7), width=max(1, int(px(1.0))))


def wallpaper(base, x0, x1, seed):
    """Jade wallpaper: fine stripes with a small gilt damask through them."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(x0, CEIL, x1, WAIN_Y), fill=JADE)
    step = px(10)
    for i, x in enumerate(range(int(x0), int(x1), int(step))):
        c = JADE_L if i % 2 == 0 else JADE_D
        d.rectangle(box(x, CEIL, x + step * 0.58, WAIN_Y), fill=mix(JADE, c, 0.5))

    for r, gy in enumerate(range(int(CEIL) + int(px(12)), int(WAIN_Y) - int(px(4)),
                                 int(px(26)))):
        off = px(13) if r % 2 else 0
        for gx in range(int(x0) + int(px(14)) + off, int(x1) - int(px(6)), int(px(26))):
            cy = gy + px(9)
            d.polygon([(gx, cy - px(5)), (gx + px(3), cy), (gx, cy + px(5)), (gx - px(3), cy)],
                      fill=mix(JADE, (146, 132, 86), 0.30))

    # the shadow the cornice drops down the wallpaper
    for i in range(px(14)):
        a = int(58 * (1 - i / float(px(14))) ** 1.4)
        d.line([(x0, CEIL + i), (x1, CEIL + i)], fill=mix(JADE, (16, 24, 18), a / 255.0))
    # and the grime that collects over the wainscot
    for i in range(px(10)):
        d.line([(x0, WAIN_Y - i), (x1, WAIN_Y - i)],
               fill=mix(JADE, (24, 30, 24), 0.30 * (1 - i / float(px(10)))))


def wainscot(base, x0, x1):
    """The red lacquer dado, panelled, with gilt beads top and bottom."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(x0, WAIN_Y, x1, PLINTH), fill=LAC)
    d.rectangle(box(x0, WAIN_Y, x1, WAIN_Y + px(3)), fill=mix(GOLD, LAC, 0.22))
    d.rectangle(box(x0, PLINTH - px(3), x1, PLINTH), fill=mix(GOLD, LAC_D, 0.5))

    pw = px(140)
    gap = px(16)
    x = x0 + px(16)
    while x + px(60) < x1 - px(10):
        w = min(pw, x1 - px(16) - x)
        if w < px(60):
            break
        d.rectangle(box(x, WAIN_Y + px(8), x + w, PLINTH - px(8)), fill=mix(LAC, LAC_D, 0.22))
        d.line([(x, WAIN_Y + px(8)), (x + w, WAIN_Y + px(8))],
               fill=mix(LAC, (214, 156, 112), 0.30), width=max(1, int(px(0.9))))
        d.line([(x, PLINTH - px(8)), (x + w, PLINTH - px(8))], fill=(34, 8, 6),
               width=max(2, int(px(1.2))))
        d.line([(x, WAIN_Y + px(8)), (x, PLINTH - px(8))],
               fill=mix(LAC, LAC_D, 0.4), width=max(1, int(px(0.8))))
        d.rectangle(box(x + px(4), WAIN_Y + px(12), x + w - px(4), PLINTH - px(12)),
                    outline=mix(LAC, LAC_D, 0.45), width=max(1, int(px(0.7))))
        x += w + gap


def skirting(base):
    """The dark plinth board along the bottom of the wall."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, PLINTH, W, FLOOR_Y), fill=mix(LAC_D, (30, 16, 12), 0.4))
    d.line([(0, PLINTH), (W, PLINTH)], fill=mix(GOLD, LAC_D, 0.55),
           width=max(1, int(px(0.8))))
    d.line([(0, FLOOR_Y - px(2)), (W, FLOOR_Y - px(2))], fill=(12, 8, 6),
           width=max(2, int(px(1.2))))


def pilaster(base, cx):
    """A lacquer pilaster with a gilt capital, standing between two bays."""
    d = ImageDraw.Draw(base)
    w = px(16)
    d.rectangle(box(cx - w, CEIL, cx + w, PLINTH), fill=mix(LAC, LAC_D, 0.12))
    for k in (-0.5, 0.0, 0.5):
        d.line([(cx + w * k, CEIL), (cx + w * k, PLINTH)],
               fill=mix(LAC, LAC_D, 0.34 if k else 0.18), width=max(1, int(px(0.7))))
    d.line([(cx - w, CEIL), (cx - w, PLINTH)], fill=mix(LAC, (204, 120, 92), 0.24),
           width=max(1, int(px(0.9))))
    d.line([(cx + w, CEIL), (cx + w, PLINTH)], fill=(24, 8, 6),
           width=max(2, int(px(1.2))))
    for y, h in ((CEIL, px(10)), (PLINTH - px(12), px(12))):     # capital and base
        d.rectangle(box(cx - w - px(5), y, cx + w + px(5), y + h), fill=mix(LAC, LAC_L, 0.30))
        d.line([(cx - w - px(5), y), (cx + w + px(5), y)], fill=mix(GOLD, GOLD_L, 0.3),
               width=max(1, int(px(1.0))))
        d.line([(cx - w - px(5), y + h), (cx + w + px(5), y + h)], fill=(30, 12, 8),
               width=max(1, int(px(0.8))))


def sconce(base, x, y):
    """A brass candle sconce on the wallpaper, with its little flame."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(x - px(8), y - px(2), x + px(8), y + px(3)), fill=mix(GOLD, (96, 72, 34), 0.4))
    d.ellipse(box(x - px(6), y - px(14), x + px(6), y + px(2)),
              fill=mix(GOLD, GOLD_L, 0.25))
    d.ellipse(box(x - px(4), y - px(12), x + px(4), y - px(4)), fill=(110, 82, 36))
    d.rectangle(box(x - px(1.4), y - px(22), x + px(1.4), y - px(13)), fill=(238, 230, 206))
    d.polygon([(x, y - px(32)), (x + px(2), y - px(24)), (x - px(2), y - px(24))],
              fill=(255, 224, 148))
    d.ellipse(box(x - px(1.2), y - px(28), x + px(1.2), y - px(22)), fill=(255, 252, 224))
    lamp(x, y - px(26), px(96), (255, 200, 132), 74)


def lantern(base, cx, cy, r=px(27)):
    """A red paper lantern hanging over the bar: a ribbed ellipsoid, gold capped.

    A box on a cord read as a framed panel at stage scale: a rounded lantern with
    its ribs is unmistakable.
    """
    d = ImageDraw.Draw(base)
    top = cy - r * 3.0
    if top > 0:                                  # the cord up into the ceiling
        d.line([(cx, 0), (cx, top + r * 0.6)], fill=(36, 28, 24),
               width=max(2, int(px(2.0))))
        for gy in range(int(top) + int(r * 0.6), 0, -int(px(26))):
            d.ellipse(box(cx - px(4), gy, cx + px(4), gy + px(11)),
                      outline=mix(GOLD, (86, 64, 30), 0.4), width=max(1, int(px(1.2))))
    hd.hang_lantern(d, cx, cy, r, body=RED, cap=mix(GOLD, (96, 70, 34), 0.3))
    # a short cord and the knot below the lantern
    d.line([(cx, cy + r * 0.98), (cx, cy + r * 1.6)], fill=(150, 34, 28),
           width=max(2, int(px(2.0))))
    d.ellipse(box(cx - px(3.4), cy + r * 1.5, cx + px(3.4), cy + r * 1.95),
              fill=(150, 34, 28))
    lamp(cx, cy, px(150), (255, 186, 118), 78)


# ------------------------------------------------------------------- the bar
def back_bar(base, x0, x1):
    """The back bar: mirror panels, two shelves of bottles, and their light."""
    d = ImageDraw.Draw(base)
    y0, y1 = CEIL + px(2), COUNTER_Y - px(4)
    d.rectangle(box(x0, y0, x1, y1), fill=(26, 18, 15))

    n = 4
    for k in range(n):
        m0 = x0 + (x1 - x0) * k / n + px(9)
        m1 = x0 + (x1 - x0) * (k + 1) / n - px(9)
        d.rectangle(box(m0, y0 + px(4), m1, y1 - px(4)), fill=(74, 86, 82))
        # the mirror keeps a dim reflection of the room: warm smears, a lantern
        for j in range(3):
            gy = y0 + px(12) + j * px(11)
            d.line([(m0 + px(5), gy), (m0 + (m1 - m0) * 0.55, gy)],
                   fill=mix((74, 86, 82), (150, 128, 96), 0.35), width=max(1, int(px(1.2))))
        cx0 = m0 + (m1 - m0) * 0.62
        d.ellipse(box(cx0 - px(9), y0 + px(12), cx0 + px(9), y0 + px(24)),
                  fill=mix((74, 86, 82), (206, 150, 96), 0.45))
        d.line([(m0 + (m1 - m0) * 0.2, y0 + px(4)), (m0 + (m1 - m0) * 0.45, y1 - px(4))],
               fill=mix((74, 86, 82), (196, 214, 210), 0.30), width=max(2, int(px(2.4))))
        d.rectangle(box(m0, y0 + px(4), m1, y1 - px(4)), outline=(40, 30, 22),
                    width=max(1, int(px(1.0))))

    # two shelves in front of the mirror, with the bottles standing on them
    for sh in (0.42, 0.80):
        sy = y0 + (y1 - y0) * sh
        d.rectangle(box(x0 + px(4), sy, x1 - px(4), sy + px(5)), fill=(62, 40, 24))
        d.line([(x0 + px(4), sy), (x1 - px(4), sy)], fill=(160, 118, 72),
               width=max(1, int(px(1.0))))
        d.line([(x0 + px(4), sy + px(5)), (x1 - px(4), sy + px(5))], fill=(18, 12, 10),
               width=max(2, int(px(1.4))))
        rnd = random.Random(int(x0) + int(sh * 1000))
        x = x0 + px(12)
        while x < x1 - px(22):
            bw = rnd.uniform(px(7), px(12))
            bh = rnd.uniform(px(15), px(25))
            col = rnd.choice(((156, 96, 40), (70, 104, 68), (122, 132, 122),
                              (150, 62, 46), (196, 166, 104)))
            d.rectangle(box(x, sy - bh, x + bw, sy), fill=mix(col, (34, 24, 18), 0.22))
            d.rectangle(box(x + bw * 0.30, sy - bh - px(7), x + bw * 0.70, sy - bh),
                        fill=mix(col, (44, 32, 20), 0.3))
            d.rectangle(box(x + bw * 0.22, sy - bh - px(9), x + bw * 0.78, sy - bh - px(6)),
                        fill=mix(col, (206, 176, 118), 0.5))
            d.line([(x + px(2), sy - bh + px(3)), (x + px(2), sy - px(4))],
                   fill=mix(col, (252, 240, 214), 0.55), width=max(1, int(px(0.7))))
            x += bw + rnd.uniform(px(4), px(10))


def counter(base, x0, x1):
    """The bar counter: a lit wood top, a fluted lacquer front, a brass rail."""
    d = ImageDraw.Draw(base)
    top = COUNTER_Y
    # the top, standing proud of the front, bright along its front edge
    d.rectangle(box(x0 - px(12), top - px(9), x1 + px(12), top + px(5)),
                fill=mix((128, 92, 54), (168, 128, 78), 0.3))
    d.line([(x0 - px(12), top - px(9)), (x1 + px(12), top - px(9))],
           fill=(240, 212, 164), width=max(2, int(px(1.6))))
    d.line([(x0 - px(12), top + px(5)), (x1 + px(12), top + px(5))], fill=(38, 22, 12),
           width=max(2, int(px(1.6))))

    # the front: fluted lacquer, brighter at the top where the bar light falls
    d.rectangle(box(x0, top + px(5), x1, PLINTH), fill=mix(LAC, LAC_D, 0.30))
    for x in range(int(x0), int(x1), int(px(14))):
        d.line([(x, top + px(9)), (x, PLINTH - px(2))], fill=mix(LAC, LAC_D, 0.62),
               width=max(1, int(px(0.7))))
        d.line([(x + px(3), top + px(9)), (x + px(3), PLINTH - px(2))],
               fill=mix(LAC, (204, 118, 86), 0.16), width=max(1, int(px(0.5))))

    # the brass foot rail, on its brackets
    rail_y = PLINTH - px(26)
    for x in range(int(x0) + int(px(50)), int(x1), int(px(210))):
        d.rectangle(box(x - px(3), rail_y, x + px(3), PLINTH - px(6)),
                    fill=mix(GOLD, (92, 70, 34), 0.4))
    d.rectangle(box(x0 + px(8), rail_y, x1 - px(8), rail_y + px(5)),
                fill=mix(GOLD, GOLD_L, 0.3))
    d.line([(x0 + px(8), rail_y), (x1 - px(8), rail_y)], fill=(255, 236, 186),
           width=max(1, int(px(0.9))))
    d.line([(x0 + px(8), rail_y + px(5)), (x1 - px(8), rail_y + px(5))],
           fill=(74, 54, 22), width=max(1, int(px(1.0))))

    # glasses and a bottle left on the counter
    rnd = random.Random(77)
    for gx in (x0 + (x1 - x0) * 0.16, x0 + (x1 - x0) * 0.72, x0 + (x1 - x0) * 0.86):
        gw = px(11)
        d.polygon([(gx - gw / 2.0, top - px(16)), (gx + gw / 2.0, top - px(16)),
                   (gx + gw * 0.36, top - px(8)), (gx - gw * 0.36, top - px(8))],
                  fill=(210, 224, 216))
        d.line([(gx - gw * 0.32, top - px(14)), (gx + gw * 0.32, top - px(14))],
               fill=(255, 246, 208), width=max(1, int(px(0.7))))
    bx = x0 + (x1 - x0) * 0.44
    d.rectangle(box(bx - px(8), top - px(28), bx + px(8), top - px(8)), fill=(126, 60, 34))
    d.rectangle(box(bx - px(3), top - px(38), bx + px(3), top - px(28)), fill=(112, 52, 30))
    d.line([(bx - px(6), top - px(26)), (bx - px(6), top - px(10))],
           fill=(214, 160, 108), width=max(1, int(px(0.9))))

    lamp((x0 + x1) / 2.0, top + px(6), px(300), (255, 190, 124), 54)
    lamp((x0 + x1) / 2.0, PLINTH + px(16), px(200), (255, 176, 110), 30)


def sign(base, x0, x1, y0, y1):
    """The White Tiger sign, hung over the counter on two chains."""
    d = ImageDraw.Draw(base)
    for sx in (x0 + px(30), x1 - px(30)):
        d.line([(sx, y0), (sx, -px(4))], fill=mix(GOLD, (86, 66, 30), 0.35),
               width=max(2, int(px(2.0))))
        for gy in range(int(y0) - int(px(24)), 0, int(px(28))):
            d.ellipse(box(sx - px(3), gy, sx + px(3), gy + px(10)),
                      outline=mix(GOLD, GOLD_L, 0.2), width=max(1, int(px(1.0))))

    # the body: a red lacquer field, gilded round the edge
    d.rectangle(box(x0 - px(9), y0 - px(9), x1 + px(9), y1 + px(9)), fill=(26, 14, 10))
    for i in range(int(y1 - y0)):
        tt = i / max(1.0, y1 - y0 - 1)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=mix((186, 48, 34), (112, 20, 16), tt))
    d.rectangle(box(x0, y0, x1, y1), outline=mix(GOLD, GOLD_L, 0.4),
                width=max(2, int(px(1.8))))
    d.rectangle(box(x0 + px(4), y0 + px(4), x1 - px(4), y1 - px(4)),
                outline=mix((92, 62, 26), GOLD, 0.5), width=max(1, int(px(0.9))))

    # the tiger's head, struck in gold, at the left of the sign
    mx, my = x0 + px(42), (y0 + y1) / 2.0
    r = px(21)
    for ex in (mx - r * 0.84, mx + r * 0.84):                   # ears, laid back
        d.polygon([(ex - px(8), my - r * 0.52), (ex + px(6), my - r * 0.60),
                   (ex + px(1), my - r * 1.06)],
                  fill=mix(GOLD, (118, 82, 32), 0.45))
    d.ellipse(box(mx - r, my - r * 0.80, mx + r, my + r * 0.92),
              fill=mix(GOLD, (118, 82, 32), 0.45))
    d.ellipse(box(mx - r * 0.88, my - r * 0.68, mx + r * 0.88, my + r * 0.80),
              fill=mix(GOLD, (212, 172, 96), 0.30))
    for sx in (-0.40, 0.40):                                    # slit eyes
        d.polygon([(mx + r * sx - px(7), my - r * 0.06),
                   (mx + r * sx + px(7), my - r * 0.20),
                   (mx + r * sx + px(7), my - r * 0.07),
                   (mx + r * sx - px(7), my + px(2))], fill=(44, 24, 12))
    for sx in (-0.62, -0.34, 0.34, 0.62):                       # cheek stripes
        d.line([(mx + r * sx, my + r * 0.12), (mx + r * (sx + 0.16), my + r * 0.42)],
               fill=(70, 40, 18), width=max(2, int(px(2.2))))
    for sx in (-0.30, 0.0, 0.30):                               # brow stripes
        d.line([(mx + r * sx, my - r * 0.60), (mx + r * (sx + 0.10), my - r * 0.32)],
               fill=(70, 40, 18), width=max(2, int(px(2.0))))
    d.polygon([(mx - px(5), my + r * 0.44), (mx + px(5), my + r * 0.44), (mx, my + r * 0.60)],
              fill=(70, 40, 18))

    # the gilt rule that parts the tiger from the characters, and the characters
    d.line([(x0 + px(100), y0 + px(10)), (x0 + px(100), y1 - px(10))],
           fill=mix(GOLD, (156, 112, 54), 0.30), width=max(1, int(px(1.2))))
    for k in range(5):
        gx = x1 - px(158) + k * px(27)
        hd.glyph(d, gx, my - px(12), px(24), (252, 208, 134), seed=11 + k,
                 width=px(2.2))

    lamp((x0 + x1) / 2.0, (y0 + y1) / 2.0, (x1 - x0) * 0.95, (255, 118, 62), 104)
    lamp((x0 + x1) / 2.0, FLOOR_Y + px(30), (x1 - x0) * 0.7, (255, 96, 52), 34)


# ----------------------------------------------------------- the room beyond
def bead_curtain(base, x0, x1, top, bottom, seed):
    """A bead curtain, drawn on its own layer so it really is translucent."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(seed)
    x = x0 + px(4)
    while x < x1 - px(2):
        parted = rnd.random() < 0.12
        if not parted:
            y = top + px(3)
            while y < bottom:
                r = px(1.0)
                a = rnd.randint(66, 146)
                c = mix((234, 196, 122), (182, 134, 68), rnd.random())
                d.ellipse(box(x - r, y, x + r, y + r * 1.9),
                          fill=c + (a,))
                y += px(4.0)
        x += px(3.6)
    base.alpha_composite(layer)


def alcove(base, x0, x1):
    """The private room: bead curtain, the red bed standing in it, a lamp."""
    d = ImageDraw.Draw(base)
    # the reveal, so the opening is a hole through a thick wall
    d.rectangle(box(x0 - px(10), CEIL - px(8), x1 + px(10), PLINTH + px(2)),
                fill=(24, 16, 12))
    d.rectangle(box(x0, CEIL, x1, PLINTH), fill=mix(JADE, (26, 32, 26), 0.34))

    # its own paper, dimmer than the bar's
    step = px(10)
    for i, x in enumerate(range(int(x0), int(x1), int(step))):
        c = mix(JADE, JADE_D if i % 2 else JADE_L, 0.30)
        d.rectangle(box(x, CEIL, x + step * 0.58, PLINTH),
                    fill=mix(mix(JADE, (26, 32, 26), 0.30), c, 0.45))
    # the room's floor, and the dark under the bed
    d.rectangle(box(x0, px(166), x1, PLINTH), fill=mix(BOARD, (22, 14, 10), 0.4))

    # the bed, seen from its foot: headboard behind, pillows, sheet, red cover.
    # It is inset from the opening so the room's own wall and floor still show
    # around it, otherwise the alcove is one red block.
    bx0, bx1 = x0 + (x1 - x0) * 0.16, x1 - (x1 - x0) * 0.20
    # the headboard: a dark lacquer panel under a gilt rail
    d.rectangle(box(bx0, px(78), bx1, px(116)), fill=(52, 14, 12))
    d.rectangle(box(bx0 + px(6), px(84), bx1 - px(6), px(113)),
                fill=mix((52, 14, 12), (150, 46, 34), 0.40))
    d.rectangle(box(bx0 + px(6), px(84), bx1 - px(6), px(113)),
                outline=mix(GOLD, (150, 108, 50), 0.30), width=max(1, int(px(1.1))))
    d.line([(bx0, px(78)), (bx1, px(78))], fill=mix(GOLD, GOLD_L, 0.35),
           width=max(2, int(px(1.6))))
    # the frame, and the shadow the bed drops on the room's floor
    d.rectangle(box(bx0 - px(4), px(152), bx1 + px(4), px(166)), fill=(44, 12, 10))
    d.rectangle(box(bx0 - px(9), px(164), bx1 + px(9), px(173)), fill=(16, 7, 6))
    # the cover: warm at the head, deep at the foot, with its folds
    for i in range(int(px(152) - px(118))):
        tt = i / max(1.0, px(152) - px(118))
        d.line([(bx0, px(118) + i), (bx1, px(118) + i)],
               fill=mix((164, 42, 32), (102, 20, 16), tt))
    for k in range(3):
        fx = bx0 + (bx1 - bx0) * (0.26 + 0.24 * k)
        d.line([(fx, px(122)), (fx - px(6), px(150))], fill=(112, 22, 18),
               width=max(1, int(px(1.2))))
    # the sheet turned back at the head, and the shadow under the pillows
    d.rectangle(box(bx0 + px(3), px(112), bx1 - px(3), px(119)), fill=(196, 186, 164))
    d.line([(bx0 + px(3), px(112)), (bx1 - px(3), px(112))], fill=(238, 230, 210),
           width=max(1, int(px(1.0))))
    # two pillows
    for k in (0.12, 0.54):
        pw = (bx1 - bx0) * 0.26
        p0 = bx0 + (bx1 - bx0) * k
        d.rounded_rectangle(box(p0, px(96), p0 + pw, px(112)), radius=max(2, int(px(4))),
                            fill=(216, 204, 184))
        d.line([(p0 + px(3), px(99)), (p0 + pw - px(3), px(99))], fill=(240, 234, 216),
               width=max(1, int(px(1.0))))
        d.rectangle(box(p0, px(110), p0 + pw, px(112)), fill=(150, 138, 118))
    # a little lacquer table beside the bed, with a shaded lamp on it
    tx0 = bx1 + px(8)
    d.rectangle(box(tx0, px(136), tx0 + px(34), px(168)), fill=mix(LAC, LAC_D, 0.35))
    d.line([(tx0, px(136)), (tx0 + px(34), px(136))], fill=mix(GOLD, GOLD_L, 0.30),
           width=max(1, int(px(1.0))))
    d.polygon([(tx0 + px(6), px(122)), (tx0 + px(28), px(122)),
               (tx0 + px(24), px(135)), (tx0 + px(10), px(135))],
              fill=mix(RED, (208, 86, 58), 0.35))
    d.rectangle(box(tx0 + px(15), px(135), tx0 + px(19), px(137)), fill=(60, 40, 30))
    lamp(tx0 + px(17), px(130), px(96), (255, 140, 92), 58)

    for y, h in ((CEIL, px(8)), (PLINTH - px(8), px(8))):        # head and foot rail
        d.rectangle(box(x0 - px(10), y, x1 + px(10), y + h), fill=mix(LAC, LAC_D, 0.2))
        d.line([(x0 - px(10), y), (x1 + px(10), y)], fill=mix(GOLD, GOLD_L, 0.25),
               width=max(1, int(px(1.0))))

    # the brass rod, and the beads hanging from it
    d.rectangle(box(x0 - px(4), CEIL + px(2), x1 + px(4), CEIL + px(7)),
                fill=mix(GOLD, (112, 84, 38), 0.4))
    d.line([(x0 - px(4), CEIL + px(2)), (x1 + px(4), CEIL + px(2))],
           fill=mix(GOLD, GOLD_L, 0.4), width=max(1, int(px(1.0))))
    # the beads are drawn aside at the middle, so the bed is not hidden behind
    # a sheet of polka dots
    w = x1 - x0
    bead_curtain(base, x0, x0 + w * 0.30, CEIL + px(7), PLINTH - px(4), int(x0))
    bead_curtain(base, x1 - w * 0.30, x1, CEIL + px(7), PLINTH - px(4), int(x0) + 5)
    lamp((x0 + x1) / 2.0, px(120), px(190), (255, 126, 82), 46)


def chair(base, cx, w=px(112), top=px(112), seat=px(148)):
    """A velvet armchair against the wall, seen from the front."""
    d = ImageDraw.Draw(base)
    half = w / 2.0
    d.rounded_rectangle(box(cx - half, top, cx + half, seat + px(10)),
                        radius=max(2, int(px(12))), fill=VELVET)
    # two buttons low on the back, and the gold piping round it
    for c in range(2):
        bxx = cx - half * 0.34 + c * half * 0.68
        byy = top + px(46)
        d.ellipse(box(bxx - px(3), byy - px(3), bxx + px(3), byy + px(3)),
                  fill=VELVET_D)
    d.rounded_rectangle(box(cx - half, top, cx + half, seat + px(10)),
                        radius=max(2, int(px(12))), outline=mix(GOLD, VELVET, 0.45),
                        width=max(1, int(px(1.0))))
    # arms, and the seat cushion between them
    for ax in (cx - half - px(4), cx + half + px(4) - px(20)):
        d.rounded_rectangle(box(ax, seat - px(16), ax + px(20), seat + px(22)),
                            radius=max(2, int(px(8))), fill=VELVET_D)
        d.line([(ax + px(2), seat - px(14)), (ax + px(18), seat - px(14))],
               fill=mix(GOLD, VELVET, 0.35), width=max(1, int(px(0.9))))
    d.rounded_rectangle(box(cx - half + px(10), seat - px(6), cx + half - px(10), seat + px(12)),
                        radius=max(2, int(px(7))), fill=VELVET_L)
    # the skirt down to the floor
    d.rectangle(box(cx - half + px(8), seat + px(12), cx + half - px(8), PLINTH),
                fill=VELVET_D)
    d.line([(cx - half + px(8), PLINTH), (cx + half - px(8), PLINTH)],
           fill=(20, 8, 8), width=max(2, int(px(1.2))))


def table(base, cx, top=px(136)):
    """A small round table with a lamp on it."""
    d = ImageDraw.Draw(base)
    r = px(30)
    d.rectangle(box(cx - px(6), top + px(4), cx + px(6), PLINTH), fill=(52, 30, 18))
    d.ellipse(box(cx - px(14), PLINTH - px(8), cx + px(14), PLINTH), fill=(44, 26, 16))
    d.ellipse(box(cx - r, top - px(10), cx + r, top + px(4)), fill=(86, 52, 32))
    d.ellipse(box(cx - r, top - px(12), cx + r, top + px(2)), fill=(154, 108, 66))
    d.ellipse(box(cx - r * 0.7, top - px(11), cx + r * 0.2, top - px(4)),
              fill=(196, 148, 98))
    # a lamp, or a bowl, on it
    d.rectangle(box(cx - px(7), top - px(16), cx + px(7), top - px(11)), fill=mix(RED, (200, 80, 56), 0.3))
    lamp(cx, top - px(14), px(90), (255, 158, 104), 44)


def lounge(base, x0, x1):
    """The far end: two chairs, a table, sconces over them."""
    sconce(base, x0 + (x1 - x0) * 0.10, px(104))
    sconce(base, x0 + (x1 - x0) * 0.92, px(104))
    chair(base, x0 + (x1 - x0) * 0.24)
    table(base, x0 + (x1 - x0) * 0.55)
    chair(base, x0 + (x1 - x0) * 0.84)


# ----------------------------------------------------------------- the floor
def floor(base):
    """Polished boards: courses, butt joints, and the room's light lying on them."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(41)
    d.rectangle(box(0, FLOOR_Y, W, H), fill=BOARD)
    rows = [FLOOR_Y, FLOOR_Y + px(18), FLOOR_Y + px(38), FLOOR_Y + px(64),
            FLOOR_Y + px(96), H]
    for i in range(len(rows) - 1):
        y0, y1 = rows[i], rows[i + 1]
        c = mix(BOARD, BOARD_L, 0.10 + 0.20 * (i % 2))
        d.rectangle(box(0, y0, W, y1), fill=c)
        d.line([(0, y0), (W, y0)], fill=mix(c, (128, 92, 58), 0.22),
               width=max(1, int(px(0.8))))
        x = rnd.uniform(-px(300), 0)
        while x < W:
            d.line([(x, y0), (x, y1)], fill=mix(c, (18, 10, 8), 0.55),
                   width=max(1, int(px(0.9))))
            x += rnd.uniform(px(280), px(520))
        # grain along the board
        for k in range(6):
            gy = rnd.uniform(y0 + px(2), y1 - px(2))
            gx0 = rnd.uniform(0, W)
            d.line([(gx0, gy), (gx0 + rnd.uniform(px(200), px(700)), gy)],
                   fill=mix(c, (24, 14, 10), 0.30), width=max(1, int(px(0.6))))

    # the wall's shadow on the boards, and the warm light that pools past it
    for i in range(px(16)):
        a = int(120 * (1 - i / float(px(16))) ** 1.5)
        d.line([(0, FLOOR_Y + i), (W, FLOOR_Y + i)], fill=mix(BOARD, (10, 7, 6), a / 255.0))

    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    for cx0, col, wdt, a in (((BAY_B[0] + BAY_B[1]) / 2.0, (255, 168, 96), px(320), 54),
                             ((SIGN[0] + SIGN[1]) / 2.0, (255, 96, 52), px(240), 46),
                             ((BAY_A[0] + BAY_A[1]) / 2.0, (255, 138, 92), px(220), 44),
                             (BAY_C[0] + (BAY_C[1] - BAY_C[0]) * 0.24, (255, 190, 126), px(120), 38),
                             (BAY_C[0] + (BAY_C[1] - BAY_C[0]) * 0.84, (255, 190, 126), px(120), 38)):
        rd.polygon([(cx0 - wdt / 2.0, FLOOR_Y + px(4)), (cx0 + wdt / 2.0, FLOOR_Y + px(4)),
                    (cx0 + wdt * 1.3, H), (cx0 - wdt * 1.3, H)], fill=col + (a,))
    base.alpha_composite(refl.filter(ImageFilter.GaussianBlur(px(26))))

    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.rectangle(box(0, FLOOR_Y, W, H), fill=(208, 178, 140, 16))
    base.alpha_composite(sheen.filter(ImageFilter.GaussianBlur(px(14))))


def foreground():
    """The near plane: bead strands at the edges, and the dark at the bottom."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(53)
    for i in range(px(40)):
        a = int(150 * (1 - i / float(px(40))) ** 1.6)
        d.line([(0, H - i), (W, H - i)], fill=(8, 6, 6, a))
    # two strands of beads hanging in the very front of the shot
    for x0, x1 in ((0, px(24)), (W - px(24), W)):
        for x in range(int(x0), int(x1), int(px(9))):
            y = rnd.uniform(0, px(40))
            while y < H:
                r = px(3.2)
                d.ellipse(box(x - r, y, x + r, y + r * 2.0),
                          fill=(196, 158, 92, rnd.randint(110, 190)))
                y += px(11)
    for _ in range(110):
        x = rnd.uniform(0, W)
        y = rnd.uniform(px(60), H)
        r = rnd.uniform(px(0.9), px(2.6))
        d.ellipse(box(x - r, y - r, x + r, y + r),
                  fill=(255, 208, 150, rnd.randint(18, 60)))
    return fg.filter(ImageFilter.GaussianBlur(px(2.0)))


# ------------------------------------------------------------------- the arena
def paint():
    LIGHTS.clear()
    base = hd.blank([(0, (14, 11, 10)), (CEIL, (28, 22, 18)),
                     (px(140), (46, 34, 26)), (FLOOR_Y, (54, 38, 28)),
                     (H, (26, 18, 14))])

    ceiling(base)

    # the wall, bay by bay: paper above, lacquer below
    for x0, x1, sd in ((0, PIER_A - px(30), 1), (BAY_B[0] - px(20), BAY_B[1] + px(20), 2),
                       (BAY_C[1] + px(20), W, 3)):
        wallpaper(base, x0, x1, sd)
        wainscot(base, x0, x1)
    wallpaper(base, BAY_A[0], BAY_A[1], 4)
    wallpaper(base, BAY_C[0], BAY_C[1], 5)
    wainscot(base, BAY_A[0], BAY_A[1])
    wainscot(base, BAY_C[0], BAY_C[1])
    pilaster(base, PIER_A)
    pilaster(base, PIER_B)
    skirting(base)

    # the room behind the beads, and the lounge at the far end
    alcove(base, BAY_A[0] + px(46), BAY_A[1] - px(46))
    lounge(base, BAY_C[0], BAY_C[1])

    # the bar: back bar, counter, and the sign over it
    back_bar(base, BAY_B[0] + px(26), BAY_B[1] - px(26))
    counter(base, BAY_B[0] + px(16), BAY_B[1] - px(16))
    sign(base, SIGN[0], SIGN[1], SIGN_Y[0], SIGN_Y[1])
    lantern(base, BAY_B[0] + px(64), px(74))
    lantern(base, BAY_B[1] - px(64), px(74))

    floor(base)

    base = hd.shade(base, [(hd.light(cx, cy, r, col, int(peak * 0.82)),
                            max(8, int(r * 0.30)), 1.05)
                           for cx, cy, r, col, peak in LIGHTS])
    base = art.vignette(base, 0.44)
    base = art.grain(base, 3, seed=17)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


def main():
    hd.STAGES["white_tiger_bar"] = ("White Tiger Bar", paint)
    hd.build("white_tiger_bar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
