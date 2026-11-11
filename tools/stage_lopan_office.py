"""Lo Pan's Office: the lacquer room he keeps for himself.

Painted from the plan reference: near-black lacquer panelling under a gilded
cove, a frieze of gold scrollwork, niches backed in red and set with marble
vases, a great gilded panel with a misty landscape in it, red velvet armchairs,
a black lacquer table with a gold figure on it, and the curved red bar at the
far end with its stools and its bottles.

A stage is seen across the play plane, so the office is painted as a wall
wall-to-wall: the panelling and niches stand against the back of the room, the
carpet runs out to the feet of the fighters, and the bar and the chairs stop at
the floor line, so nothing comes out into the play plane to stand on their feet.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960, localcoord 1920x1080, camera travel +/-3136.

Run:  python3 tools/stage_lopan_office.py     (part of tools/build_all.py)
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

COVE = px(36)                      # 162: the gilded cove at the head of the wall
FRIEZE = px(54)                    # 243: the bottom of the gold frieze
PLINTH = FLOOR_Y - px(12)          # 846
BAY_A = (px(56), px(530))
BAY_B = (px(566), px(1238))
BAY_C = (px(1274), px(1778))
PIER_A, PIER_B = px(548), px(1256)
NICHE_A = (px(232), px(348))
NICHE_B = (px(1024), px(1124))
PANEL_B = (px(648), px(968))
BAR = (px(1310), px(1758))
COUNTER_Y = px(148)

LACQ = (36, 26, 21)                # the panelling: near-black lacquer
LACQ_L = (62, 46, 34)
LACQ_D = (18, 13, 10)
GOLD = (188, 146, 72)
GOLD_L = (246, 216, 148)
GOLD_D = (104, 74, 30)
VELVET = (134, 26, 28)             # the armchairs
VELVET_L = (172, 44, 40)
VELVET_D = (78, 14, 16)
CARPET = (84, 94, 106)             # the blue-grey carpet
CARPET_L = (112, 122, 134)
CARPET_D = (58, 66, 78)
BORDER = (136, 30, 32)
MARBLE = (226, 220, 202)
PORCELAIN = (206, 212, 196)
BOARD = (48, 32, 22)
WARM = (255, 206, 144)

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


# ------------------------------------------------------------------ the shell
def cove(base):
    """The gilded cove, the cornice and the shadow they drop on the lacquer."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, 0, W, COVE), fill=(26, 20, 16))
    d.rectangle(box(0, COVE - px(10), W, COVE), fill=mix(GOLD, (120, 88, 38), 0.45))
    d.line([(0, COVE - px(10)), (W, COVE - px(10))], fill=GOLD_L,
           width=max(1, int(px(1.0))))
    d.line([(0, COVE - px(3)), (W, COVE - px(3))], fill=mix(GOLD, GOLD_L, 0.45),
           width=max(1, int(px(1.2))))
    d.line([(0, COVE), (W, COVE)], fill=(10, 8, 6), width=max(2, int(px(1.6))))
    for i in range(px(16)):
        a = int(120 * (1 - i / float(px(16))))
        d.line([(0, COVE + i), (W, COVE + i)], fill=(8, 6, 6, a))


def frieze(base):
    """A band of gold scrollwork under the cove, repeated along the wall."""
    d = ImageDraw.Draw(base)
    y0, y1 = COVE, FRIEZE
    d.rectangle(box(0, y0, W, y1), fill=mix(LACQ, (52, 38, 24), 0.4))
    d.line([(0, y1), (W, y1)], fill=mix(GOLD, GOLD_D, 0.5), width=max(2, int(px(1.8))))
    d.line([(0, y0), (W, y0)], fill=mix(GOLD, GOLD_D, 0.6), width=max(1, int(px(1.0))))
    step = px(74)
    cy = (y0 + y1) / 2.0
    r = (y1 - y0) * 0.36
    for x in range(-px(20), W, step):
        # a scroll and a bud, alternating, picked out in gold
        d.arc(box(x, cy - r, x + r * 2, cy + r), 200, 340, fill=GOLD,
              width=max(1, int(px(1.4))))
        d.arc(box(x + r, cy - r * 0.6, x + r * 3, cy + r * 1.2), 20, 160,
              fill=mix(GOLD, GOLD_L, 0.3), width=max(1, int(px(1.2))))
        d.polygon([(x + step * 0.5, cy - r * 0.5), (x + step * 0.5 + r * 0.5, cy),
                   (x + step * 0.5, cy + r * 0.5), (x + step * 0.5 - r * 0.5, cy)],
                  fill=mix(GOLD, GOLD_L, 0.20))
        d.ellipse(box(x + step * 0.5 - px(2), cy - px(2), x + step * 0.5 + px(2), cy + px(2)),
                  fill=GOLD_L)


def panels(base, x0, x1):
    """The lacquer panelling: tall panels, each with a fine gold fillet."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(x0, FRIEZE, x1, PLINTH), fill=LACQ)
    rnd = random.Random(5)
    for i in range(90):                                    # the sheen of old lacquer
        x = rnd.uniform(x0, x1)
        y = rnd.uniform(FRIEZE, PLINTH)
        d.ellipse(box(x, y, x + rnd.uniform(px(50), px(180)), y + rnd.uniform(px(18), px(60))),
                  fill=mix(LACQ, rnd.choice((LACQ_L, LACQ_D, (48, 36, 26))),
                           rnd.uniform(0.08, 0.22)))
    pw = px(196)
    x = x0 + px(14)
    while x + px(60) < x1:
        w = min(pw, x1 - px(14) - x)
        if w < px(60):
            break
        d.rectangle(box(x, FRIEZE + px(18), x + w, PLINTH - px(14)),
                    fill=mix(LACQ, LACQ_L, 0.10))
        d.rectangle(box(x, FRIEZE + px(18), x + w, PLINTH - px(14)),
                    outline=mix(GOLD, GOLD_D, 0.55), width=max(1, int(px(0.9))))
        d.rectangle(box(x + px(6), FRIEZE + px(24), x + w - px(6), PLINTH - px(20)),
                    outline=mix(GOLD, LACQ, 0.72), width=max(1, int(px(0.6))))
        # a small gilt boss at the head of every panel
        d.polygon([(x + w / 2.0, FRIEZE + px(30)), (x + w / 2.0 + px(7), FRIEZE + px(38)),
                   (x + w / 2.0, FRIEZE + px(46)), (x + w / 2.0 - px(7), FRIEZE + px(38))],
                  fill=mix(GOLD, GOLD_D, 0.3))
        x += w + px(16)
    # the skirting, and the shadow the wall puts on the carpet
    d.rectangle(box(x0, PLINTH, x1, FLOOR_Y), fill=mix(LACQ, (24, 16, 12), 0.4))
    d.line([(x0, PLINTH), (x1, PLINTH)], fill=mix(GOLD, GOLD_D, 0.4),
           width=max(1, int(px(1.0))))
    d.line([(x0, FLOOR_Y - px(2)), (x1, FLOOR_Y - px(2))], fill=(8, 6, 5),
           width=max(2, int(px(1.4))))


def pier(base, cx):
    """A gilt-edged pilaster between two bays."""
    d = ImageDraw.Draw(base)
    w = px(16)
    d.rectangle(box(cx - w, FRIEZE, cx + w, PLINTH), fill=mix(LACQ, LACQ_L, 0.22))
    d.rectangle(box(cx - w, FRIEZE, cx - w + px(4), PLINTH), fill=mix(GOLD, GOLD_D, 0.35))
    d.rectangle(box(cx + w - px(4), FRIEZE, cx + w, PLINTH), fill=mix(GOLD, GOLD_D, 0.35))
    for k in range(3):
        dx = cx - w + px(9) + k * px(6)
        d.line([(dx, FRIEZE + px(10)), (dx, PLINTH - px(10))],
               fill=mix(GOLD_L, (150, 110, 50), 0.5), width=max(1, int(px(0.7))))
    for y, h in ((FRIEZE, px(12)), (PLINTH - px(12), px(12))):
        d.rectangle(box(cx - w - px(6), y, cx + w + px(6), y + h), fill=mix(GOLD, (150, 110, 50), 0.4))
        d.line([(cx - w - px(6), y), (cx + w + px(6), y)], fill=GOLD_L,
               width=max(1, int(px(1.0))))
        d.line([(cx - w - px(6), y + h), (cx + w + px(6), y + h)], fill=(20, 14, 8),
               width=max(1, int(px(0.9))))


def niche(base, x0, x1):
    """A niche backed in red, with a marble vase standing in it."""
    d = ImageDraw.Draw(base)
    top = FRIEZE + px(16)
    bottom = PLINTH - px(10)
    d.rectangle(box(x0 - px(10), top - px(10), x1 + px(10), bottom + px(10)),
                fill=mix(GOLD, (150, 110, 50), 0.40))
    d.rectangle(box(x0, top, x1, bottom), fill=(58, 16, 16))
    for i in range(int(bottom - top)):                     # the red goes dark at the bottom
        tt = i / max(1.0, bottom - top)
        d.line([(x0, top + i), (x1, top + i)], fill=mix((92, 22, 22), (34, 10, 10), tt))
    d.rectangle(box(x0, top, x1, bottom), outline=mix(GOLD, GOLD_D, 0.45),
                width=max(1, int(px(1.2))))
    # the bracket shelf, and the vase on it
    shelf_y = bottom - px(34)
    d.rectangle(box(x0 - px(4), shelf_y, x1 + px(4), shelf_y + px(6)),
                fill=mix(LACQ, LACQ_L, 0.3))
    d.line([(x0 - px(4), shelf_y), (x1 + px(4), shelf_y)], fill=GOLD_L,
           width=max(1, int(px(1.2))))
    cx = (x0 + x1) / 2.0
    vh = px(44)
    d.polygon([(cx - px(15), shelf_y), (cx + px(15), shelf_y),
               (cx + px(21), shelf_y - vh * 0.55), (cx + px(9), shelf_y - vh),
               (cx - px(9), shelf_y - vh), (cx - px(21), shelf_y - vh * 0.55)],
              fill=PORCELAIN)
    d.polygon([(cx - px(21), shelf_y - vh * 0.55), (cx + px(21), shelf_y - vh * 0.55),
               (cx + px(15), shelf_y - vh * 0.5), (cx - px(15), shelf_y - vh * 0.5)],
              fill=mix(GOLD, GOLD_D, 0.4))
    d.line([(cx - px(10), shelf_y - vh * 0.9), (cx + px(10), shelf_y - vh * 0.9)],
           fill=(160, 176, 158), width=max(1, int(px(1.0))))
    d.polygon([(cx - px(15), shelf_y), (cx - px(6), shelf_y), (cx - px(8), shelf_y - vh * 0.6),
               (cx - px(16), shelf_y - vh * 0.5)], fill=(240, 236, 220))
    lamp(cx, shelf_y - vh * 0.5, px(120), (255, 198, 138), 52)


def painted_panel(base, x0, x1):
    """The great gilt panel: misty mountains behind gold, like the reference."""
    d = ImageDraw.Draw(base)
    top = FRIEZE + px(16)
    bottom = PLINTH - px(20)
    d.rectangle(box(x0 - px(14), top - px(14), x1 + px(14), bottom + px(14)),
                fill=mix(GOLD, (150, 108, 46), 0.35))
    d.rectangle(box(x0 - px(6), top - px(6), x1 + px(6), bottom + px(6)),
                outline=mix(GOLD_L, GOLD, 0.4), width=max(2, int(px(1.8))))
    d.rectangle(box(x0, top, x1, bottom), fill=(132, 138, 126))
    # the landscape: bands of haze, mountain shapes, a pale sky
    for i in range(int(bottom - top)):
        tt = i / max(1.0, bottom - top)
        d.line([(x0, top + i), (x1, top + i)],
               fill=mix((176, 178, 160), (92, 98, 88), tt ** 0.8))
    rnd = random.Random(17)
    for k in range(4):
        bx = x0 + (x1 - x0) * (0.05 + 0.26 * k)
        bh = (bottom - top) * rnd.uniform(0.35, 0.72)
        base_y = top + (bottom - top) * rnd.uniform(0.62, 0.86)
        d.polygon([(bx, base_y), (bx + (x1 - x0) * 0.14, base_y - bh),
                   (bx + (x1 - x0) * 0.30, base_y)],
                  fill=mix((96, 108, 100), (140, 148, 132), rnd.uniform(0.2, 0.6)))
    # a pale mist band and a few pines
    d.rectangle(box(x0, top + (bottom - top) * 0.60, x1, top + (bottom - top) * 0.72),
                fill=(198, 200, 184))
    for k in range(5):
        tx = x0 + (x1 - x0) * (0.12 + 0.18 * k)
        ty = top + (bottom - top) * 0.74
        d.line([(tx, ty), (tx, ty - px(26))], fill=(58, 62, 48), width=max(1, int(px(1.4))))
        for j in range(3):
            d.line([(tx - px(9) + j * px(2), ty - px(8) - j * px(6)),
                    (tx + px(9) - j * px(2), ty - px(8) - j * px(6))],
                   fill=(58, 66, 50), width=max(1, int(px(1.6))))
    d.rectangle(box(x0, top, x1, bottom), outline=mix(GOLD, GOLD_D, 0.5),
                width=max(1, int(px(1.4))))
    lamp((x0 + x1) / 2.0, (top + bottom) / 2.0, (x1 - x0) * 0.8, (255, 200, 140), 64)


def lattice_screen(base, x0, x1):
    """The red lattice screen at the end of the room, backed with paper."""
    d = ImageDraw.Draw(base)
    top, bottom = FRIEZE, PLINTH
    d.rectangle(box(x0, top, x1, bottom), fill=(120, 26, 26))
    d.rectangle(box(x0 + px(6), top + px(6), x1 - px(6), bottom - px(6)),
                fill=mix((196, 170, 120), (150, 120, 78), 0.35))
    step = px(26)
    for x in range(int(x0) + int(px(8)), int(x1) - int(px(4)), int(step)):
        d.rectangle(box(x, top + px(6), x + px(7), bottom - px(6)), fill=(118, 24, 24))
        d.line([(x, top + px(6)), (x, bottom - px(6))], fill=(158, 48, 40),
               width=max(1, int(px(0.7))))
    for y in range(int(top) + int(px(8)), int(bottom) - int(px(4)), int(step)):
        d.rectangle(box(x0 + px(6), y, x1 - px(6), y + px(7)), fill=(118, 24, 24))
    d.rectangle(box(x0, top, x1, bottom), outline=(168, 120, 72), width=max(2, int(px(2.0))))
    lamp((x0 + x1) / 2.0, (top + bottom) / 2.0, (x1 - x0) * 1.1, (255, 190, 130), 48)


def armchair(base, cx):
    """A red velvet armchair with a gilt frame, seen from the front."""
    d = ImageDraw.Draw(base)
    w = px(96)
    seat = px(160)
    top = px(112)
    half = w / 2.0
    # the gilt legs
    for lx in (cx - half + px(8), cx + half - px(16)):
        d.rectangle(box(lx, seat + px(12), lx + px(8), PLINTH), fill=mix(GOLD, GOLD_D, 0.4))
        d.line([(lx, seat + px(12)), (lx, PLINTH)], fill=GOLD_L, width=max(1, int(px(0.9))))
    # the back, with its buttoning and gilt edging
    d.rounded_rectangle(box(cx - half, top, cx + half, seat + px(14)),
                        radius=max(2, int(px(14))), fill=VELVET)
    d.rounded_rectangle(box(cx - half, top, cx + half, seat + px(14)),
                        radius=max(2, int(px(14))), outline=mix(GOLD, (150, 112, 50), 0.35),
                        width=max(1, int(px(1.4))))
    for r in range(2):
        for c in range(3):
            bxx = cx - half * 0.44 + c * half * 0.44
            byy = top + px(20) + r * px(18)
            d.ellipse(box(bxx - px(3), byy - px(3), bxx + px(3), byy + px(3)), fill=VELVET_D)
    # arms
    for ax in (cx - half - px(4), cx + half - px(16)):
        d.rounded_rectangle(box(ax, seat - px(18), ax + px(20), seat + px(18)),
                            radius=max(2, int(px(8))), fill=VELVET_D)
        d.line([(ax + px(2), seat - px(16)), (ax + px(18), seat - px(16))],
               fill=mix(GOLD, VELVET, 0.4), width=max(1, int(px(1.0))))
    # the seat cushion
    d.rounded_rectangle(box(cx - half + px(12), seat - px(8), cx + half - px(12), seat + px(12)),
                        radius=max(2, int(px(6))), fill=VELVET_L)
    d.line([(cx - half + px(12), seat - px(8)), (cx + half - px(12), seat - px(8))],
           fill=(196, 96, 84), width=max(1, int(px(1.0))))
    # the skirt to the floor line
    d.rectangle(box(cx - half + px(10), seat + px(12), cx + half - px(10), PLINTH),
                fill=VELVET_D)
    lamp(cx, seat, px(120), (255, 190, 128), 40)


def side_table(base, x0, x1):
    """A black lacquer table with the gold figure standing on it."""
    d = ImageDraw.Draw(base)
    top = px(170)
    d.rectangle(box(x0 + px(10), top + px(8), x1 - px(10), PLINTH), fill=mix(LACQ, LACQ_D, 0.3))
    d.rectangle(box(x0, top, x1, top + px(9)), fill=mix(LACQ, LACQ_L, 0.35))
    d.line([(x0, top), (x1, top)], fill=GOLD_L, width=max(2, int(px(1.6))))
    d.line([(x0, top + px(9)), (x1, top + px(9))], fill=(12, 8, 6), width=max(2, int(px(1.4))))
    # a gilt apron, and the figure: a small gold beast on a black stand
    d.rectangle(box(x0 + px(6), top + px(9), x1 - px(6), top + px(18)),
                outline=mix(GOLD, GOLD_D, 0.4), width=max(1, int(px(0.8))))
    cx = (x0 + x1) / 2.0
    d.rectangle(box(cx - px(26), top - px(10), cx + px(26), top), fill=(24, 16, 12))
    d.line([(cx - px(26), top - px(10)), (cx + px(26), top - px(10))],
           fill=mix(GOLD, GOLD_D, 0.4), width=max(1, int(px(1.0))))
    d.ellipse(box(cx - px(18), top - px(34), cx + px(18), top - px(6)),
              fill=mix(GOLD, (150, 108, 42), 0.35))
    d.ellipse(box(cx - px(12), top - px(30), cx + px(12), top - px(12)),
              fill=mix(GOLD, GOLD_L, 0.30))
    d.line([(cx - px(14), top - px(22)), (cx + px(14), top - px(22))],
           fill=mix(GOLD_D, (80, 54, 18), 0.4), width=max(1, int(px(1.2))))
    d.ellipse(box(cx - px(5), top - px(26), cx + px(5), top - px(18)),
              fill=(250, 236, 190))
    lamp(cx, top - px(22), px(130), (255, 210, 148), 60)


# --------------------------------------------------------------------- the bar
def bar(base, x0, x1):
    """The red lacquer bar: a curved counter, chrome trim, bottles behind it."""
    d = ImageDraw.Draw(base)
    # the back bar: a mirror with shelves of bottles
    sy0, sy1 = FRIEZE + px(10), COUNTER_Y - px(46)
    d.rectangle(box(x0 + px(20), sy0, x1 - px(20), sy1), fill=(40, 30, 22))
    d.rectangle(box(x0 + px(26), sy0 + px(6), x1 - px(26), sy1 - px(6)), fill=(78, 88, 84))
    for k in range(3):
        d.line([(x0 + px(34) + k * px(20), sy0 + px(6)),
                (x0 + px(34) + k * px(20), sy1 - px(6))],
               fill=(128, 140, 132), width=max(1, int(px(1.6))))
    for sh in (0.30, 0.62):                                  # shelves and bottles
        yy = sy0 + (sy1 - sy0) * sh
        d.rectangle(box(x0 + px(24), yy, x1 - px(24), yy + px(5)), fill=(58, 38, 24))
        d.line([(x0 + px(24), yy), (x1 - px(24), yy)], fill=(188, 150, 96),
               width=max(1, int(px(1.0))))
        rnd = random.Random(int(x0) + int(sh * 100))
        bx = x0 + px(34)
        while bx < x1 - px(40):
            bw = rnd.uniform(px(5), px(8))
            bh = rnd.uniform(px(10), px(16))
            col = rnd.choice(((150, 92, 40), (66, 100, 66), (170, 150, 96), (140, 60, 48)))
            d.rectangle(box(bx, yy - bh, bx + bw, yy), fill=mix(col, (34, 24, 16), 0.25))
            d.rectangle(box(bx + bw * 0.3, yy - bh - px(6), bx + bw * 0.7, yy - bh),
                        fill=mix(col, (40, 28, 18), 0.3))
            d.line([(bx + px(2), yy - bh + px(2)), (bx + px(2), yy - px(4))],
                   fill=mix(col, (250, 244, 216), 0.5), width=max(1, int(px(0.7))))
            bx += bw + rnd.uniform(px(4), px(12))

    # the counter: chrome rail under a red lacquer top, curved at both ends
    top = COUNTER_Y
    d.rectangle(box(x0, top, x1, top + px(9)), fill=mix((72, 22, 22), (128, 40, 34), 0.4))
    d.line([(x0, top), (x1, top)], fill=(210, 128, 96), width=max(2, int(px(1.6))))
    d.ellipse(box(x0 - px(18), top - px(7), x0 + px(18), top + px(9)), fill=(96, 32, 28))
    d.ellipse(box(x1 - px(18), top - px(7), x1 + px(18), top + px(9)), fill=(96, 32, 28))
    # the chrome edge, and the front of the bar
    d.rectangle(box(x0 - px(10), top + px(10), x1 + px(10), top + px(15)), fill=(140, 146, 154))
    d.line([(x0 - px(10), top + px(10)), (x1 + px(10), top + px(10))], fill=(212, 218, 224),
           width=max(1, int(px(1.0))))
    d.line([(x0 - px(10), top + px(15)), (x1 + px(10), top + px(15))], fill=(82, 88, 94),
           width=max(1, int(px(1.0))))
    d.rectangle(box(x0, top + px(15), x1, PLINTH), fill=mix((126, 30, 28), (86, 18, 18), 0.4))
    for bx in range(int(x0), int(x1), int(px(20))):
        d.line([(bx, top + px(18)), (bx, PLINTH - px(4))], fill=mix((150, 44, 38), (74, 14, 14), 0.5),
               width=max(1, int(px(1.0))))
    d.line([(x0, PLINTH - px(4)), (x1, PLINTH - px(4))], fill=(30, 8, 8),
           width=max(2, int(px(1.4))))
    # the chrome foot rail
    rail_y = PLINTH - px(26)
    d.rectangle(box(x0 + px(14), rail_y, x1 - px(14), rail_y + px(6)), fill=(184, 190, 198))
    d.line([(x0 + px(14), rail_y), (x1 - px(14), rail_y)], fill=(244, 248, 250),
           width=max(1, int(px(1.0))))
    for bx in range(int(x0) + int(px(70)), int(x1), int(px(200))):
        d.rectangle(box(bx - px(3), rail_y, bx + px(3), PLINTH - px(6)), fill=(150, 156, 164))

    # glasses waiting on the counter: bowl, stem and foot
    for gx in (x0 + (x1 - x0) * 0.18, x0 + (x1 - x0) * 0.52, x0 + (x1 - x0) * 0.80):
        d.polygon([(gx - px(6), top - px(16)), (gx + px(6), top - px(16)),
                   (gx + px(4), top - px(8)), (gx - px(4), top - px(8))],
                  fill=(198, 214, 208))
        d.ellipse(box(gx - px(6), top - px(18), gx + px(6), top - px(13)),
                  outline=(240, 246, 240), width=max(1, int(px(0.8))))
        d.line([(gx, top - px(8)), (gx, top - px(3))], fill=(214, 226, 220),
               width=max(1, int(px(1.2))))
        d.ellipse(box(gx - px(4), top - px(4), gx + px(4), top), fill=(206, 220, 214))

    lamp((x0 + x1) / 2.0, top - px(20), px(240), (255, 190, 130), 58)
    lamp((x0 + x1) / 2.0, PLINTH + px(20), px(180), (255, 180, 120), 30)


def stool(base, cx):
    """A bar stool, its legs splayed on the floor line."""
    d = ImageDraw.Draw(base)
    seat_y = px(132)
    for dx in (-px(11), px(11)):
        d.line([(cx + dx * 0.3, seat_y + px(4)), (cx + dx, PLINTH)],
               fill=mix(GOLD, GOLD_D, 0.45), width=max(2, int(px(1.8))))
    d.line([(cx - px(8), seat_y + px(9)), (cx + px(8), seat_y + px(9))],
           fill=mix(GOLD, GOLD_D, 0.5), width=max(1, int(px(1.2))))
    d.ellipse(box(cx - px(17), seat_y + px(2), cx + px(17), seat_y + px(12)), fill=VELVET_D)
    d.ellipse(box(cx - px(17), seat_y - px(4), cx + px(17), seat_y + px(8)), fill=VELVET)
    d.ellipse(box(cx - px(14), seat_y - px(3), cx + px(6), seat_y + px(3)), fill=VELVET_L)
    d.arc(box(cx - px(15), seat_y - px(11), cx + px(15), seat_y + px(4)), 200, 340,
          fill=mix(GOLD, GOLD_L, 0.3), width=max(1, int(px(1.0))))


# ---------------------------------------------------------------------- floor
def carpet(base):
    """The blue-grey carpet: a fine lattice, a red border, and the room's light."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(29)
    d.rectangle(box(0, FLOOR_Y, W, H), fill=CARPET)
    # the pile: mottling, so it is wool and not a colour field
    for i in range(700):
        x = rnd.uniform(0, W)
        y = rnd.uniform(FLOOR_Y, H)
        d.ellipse(box(x, y, x + rnd.uniform(px(20), px(90)), y + rnd.uniform(px(6), px(22))),
                  fill=mix(CARPET, rnd.choice((CARPET_L, CARPET_D, (96, 106, 118))),
                           rnd.uniform(0.08, 0.22)))
    # the lattice, in a paler thread
    step = px(34)
    for k in range(-int(H - FLOOR_Y), int(W) + int(H - FLOOR_Y), int(step)):
        d.line([(k, FLOOR_Y), (k + (H - FLOOR_Y), H)],
               fill=mix(CARPET, (146, 156, 166), 0.30), width=max(1, int(px(0.8))))
        d.line([(k, FLOOR_Y), (k - (H - FLOOR_Y), H)],
               fill=mix(CARPET, (146, 156, 166), 0.30), width=max(1, int(px(0.8))))
    # the red border, running with the wall and again along the front edge
    d.rectangle(box(0, FLOOR_Y + px(6), W, FLOOR_Y + px(16)), fill=BORDER)
    d.line([(0, FLOOR_Y + px(6)), (W, FLOOR_Y + px(6))], fill=(196, 88, 62),
           width=max(1, int(px(1.2))))
    d.line([(0, FLOOR_Y + px(16)), (W, FLOOR_Y + px(16))], fill=(72, 14, 16),
           width=max(1, int(px(1.2))))
    d.rectangle(box(0, FLOOR_Y + px(18), W, FLOOR_Y + px(22)), fill=mix(GOLD, (150, 110, 50), 0.4))
    for y in (H - px(30), H - px(26)):
        d.line([(0, y), (W, y)], fill=BORDER, width=max(2, int(px(4.0))))
    # the wall's shadow on the pile
    for i in range(px(14)):
        a = int(120 * (1 - i / float(px(14))) ** 1.5)
        d.line([(0, FLOOR_Y + i), (W, FLOOR_Y + i)], fill=(10, 12, 14, a))

    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    for cx0, col, wdt, a in (((BAY_B[0] + BAY_B[1]) / 2.0, (255, 200, 140), px(320), 40),
                             ((BAR[0] + BAR[1]) / 2.0, (255, 150, 110), px(260), 40),
                             ((BAY_A[0] + BAY_A[1]) / 2.0, (255, 190, 130), px(200), 30)):
        rd.polygon([(cx0 - wdt / 2.0, FLOOR_Y + px(4)), (cx0 + wdt / 2.0, FLOOR_Y + px(4)),
                    (cx0 + wdt * 1.25, H), (cx0 - wdt * 1.25, H)], fill=col + (a,))
    base.alpha_composite(refl.filter(ImageFilter.GaussianBlur(px(26))))


def foreground():
    """The near plane: dust in the lamplight, and the dark at the bottom."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(71)
    for i in range(px(40)):
        a = int(158 * (1 - i / float(px(40))) ** 1.6)
        d.line([(0, H - i), (W, H - i)], fill=(8, 6, 6, a))
    for _ in range(120):
        x = rnd.uniform(0, W)
        y = rnd.uniform(px(40), H)
        r = rnd.uniform(px(0.9), px(2.5))
        d.ellipse(box(x - r, y - r, x + r, y + r),
                  fill=(255, 214, 156, rnd.randint(18, 58)))
    return fg.filter(ImageFilter.GaussianBlur(px(2.0)))


# ------------------------------------------------------------------- the arena
def paint():
    LIGHTS.clear()
    base = hd.blank([(0, (12, 10, 8)), (COVE, (26, 20, 16)),
                     (px(140), (40, 30, 24)), (FLOOR_Y, (54, 44, 40)),
                     (H, (34, 32, 32))])

    cove(base)
    panels(base, 0, W)
    frieze(base)
    pier(base, PIER_A)
    pier(base, PIER_B)

    lattice_screen(base, BAY_A[0], BAY_A[0] + px(84))
    niche(base, NICHE_A[0], NICHE_A[1])
    armchair(base, px(420))
    painted_panel(base, PANEL_B[0], PANEL_B[1])
    armchair(base, px(596))
    niche(base, NICHE_B[0], NICHE_B[1])
    side_table(base, px(1156), px(1236))
    bar(base, BAR[0], BAR[1])
    for sx in (px(1352), px(1452), px(1552), px(1652)):
        stool(base, sx)

    carpet(base)

    base = hd.shade(base, [(hd.light(cx, cy, r, col, int(peak * 0.82)),
                            max(8, int(r * 0.30)), 1.05)
                           for cx, cy, r, col, peak in LIGHTS])
    base = art.vignette(base, 0.46)
    base = art.grain(base, 3, seed=31)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


def main():
    hd.STAGES["lopan_office"] = ("Lo Pan's Office", paint)
    hd.build("lopan_office")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
