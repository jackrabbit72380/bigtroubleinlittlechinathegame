"""Wing Kong Trading Co Lobby: the reception the company keeps for visitors.

Painted from the plan reference: a curved reception counter in warm timber with
a brass foot rail, the safe and the mail cabinet behind it, two leather chairs
standing at the desk, the studded double doors on the left under their brass
plate, a stone column, framed certificates, and the corridor on the right with
its green light spilling across the floor.

A stage is seen across the play plane, so the lobby is painted as a wall
wall-to-wall: the counter runs against the back wall and its front stops at the
floor line, the doors sit in the wall, and the fighters stand on the stone floor
in front of it. The safe, chairs, cabinet and tables all stay in the wall band
behind that line, so nothing comes out to stand on anybody's feet.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960, localcoord 1920x1080, camera travel +/-3136.

Run:  python3 tools/stage_wingkong_lobby.py     (part of tools/build_all.py)
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

CEIL = px(46)                      # 207: the ceiling band
DADO_Y = px(150)                   # 675: the top of the timber dado
PLINTH = FLOOR_Y - px(14)          # 837: the skirting meets the stone
COUNTER_Y = px(116)                # 522: the counter's top
DOORS = (px(168), px(440))         # the studded double doors
DOOR_TOP = px(66)
COL_X = px(1322)                   # the stone column by the corridor
BAY_B = (px(560), px(1240))        # the reception
BAY_C = (px(1290), px(1770))       # the corridor and the side room
PIER_A, PIER_B = px(540), px(1262)
CORRIDOR = (px(1352), px(1502))
SIDE = (px(1596), px(1738))

PLASTER = (124, 108, 82)           # ochre distemper, the colour of the reference
PLASTER_L = (152, 134, 102)
PLASTER_D = (86, 74, 56)
TIMBER = (58, 40, 30)              # dark stained wood
TIMBER_L = (96, 66, 44)
TIMBER_D = (32, 22, 16)
BRASS = (176, 138, 68)
BRASS_L = (238, 206, 140)
IRON = (56, 58, 56)
IRON_L = (96, 98, 94)
LEATHER = (48, 42, 36)
LEATHER_L = (72, 62, 52)
GREEN = (120, 168, 118)
STONE_F = (128, 108, 80)           # the ochre stone floor
STONE_F_L = (158, 134, 100)
WARM = (255, 208, 148)
PAPER = (232, 226, 210)
RED_GLASS = (128, 34, 26)

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


# ------------------------------------------------------------------ the wall
def ceiling(base):
    """A panelled office ceiling, and the cornice under it."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, 0, W, CEIL), fill=(62, 57, 48))
    for x in range(-px(20), W, px(170)):
        d.line([(x, 0), (x, CEIL)], fill=(42, 38, 32), width=max(1, int(px(1.0))))
    for y in (px(14), px(30)):
        d.line([(0, y), (W, y)], fill=(44, 39, 33), width=max(1, int(px(1.0))))
    d.rectangle(box(0, CEIL - px(9), W, CEIL), fill=(86, 78, 62))
    d.line([(0, CEIL - px(9)), (W, CEIL - px(9))], fill=(196, 178, 138),
           width=max(1, int(px(1.2))))
    d.line([(0, CEIL - px(4)), (W, CEIL - px(4))], fill=(120, 106, 82),
           width=max(1, int(px(0.8))))
    d.line([(0, CEIL), (W, CEIL)], fill=(14, 12, 10), width=max(2, int(px(1.4))))


def plaster(base):
    """The ochre distemper: mottled, with a picture rail and its shadow."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, CEIL, W, DADO_Y), fill=PLASTER)
    rnd = random.Random(7)
    for i in range(420):
        x = rnd.uniform(0, W)
        y = rnd.uniform(CEIL, DADO_Y)
        w = rnd.uniform(px(40), px(160))
        h = rnd.uniform(px(16), px(60))
        c = rnd.choice((PLASTER_L, PLASTER_D, (140, 118, 88), (104, 90, 68)))
        d.ellipse(box(x, y, x + w, y + h), fill=mix(PLASTER, c, rnd.uniform(0.10, 0.34)))
    # the picture rail, and the shadow it drops
    d.rectangle(box(0, CEIL + px(2), W, CEIL + px(8)), fill=mix(PLASTER, PLASTER_L, 0.4))
    d.line([(0, CEIL + px(2)), (W, CEIL + px(2))], fill=(214, 196, 156),
           width=max(1, int(px(1.0))))
    for i in range(px(12)):
        a = int(54 * (1 - i / float(px(12))))
        d.line([(0, DADO_Y - i), (W, DADO_Y - i)], fill=mix(PLASTER, (40, 32, 24), a / 255.0))


def dado(base):
    """The dark stained timber dado, panelled, with a moulded cap."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, DADO_Y, W, PLINTH), fill=TIMBER)
    d.rectangle(box(0, DADO_Y, W, DADO_Y + px(6)), fill=TIMBER_L)
    d.line([(0, DADO_Y), (W, DADO_Y)], fill=mix(BRASS, TIMBER_L, 0.55),
           width=max(1, int(px(1.0))))
    d.line([(0, DADO_Y + px(6)), (W, DADO_Y + px(6))], fill=TIMBER_D,
           width=max(1, int(px(1.0))))
    pw = px(118)
    x = px(14)
    while x + px(50) < W:
        d.rectangle(box(x, DADO_Y + px(16), x + pw, PLINTH - px(10)), fill=mix(TIMBER, TIMBER_D, 0.28))
        d.line([(x, DADO_Y + px(16)), (x + pw, DADO_Y + px(16))],
               fill=mix(TIMBER, TIMBER_L, 0.55), width=max(1, int(px(0.8))))
        d.line([(x, PLINTH - px(10)), (x + pw, PLINTH - px(10))], fill=(18, 12, 8),
               width=max(2, int(px(1.2))))
        d.line([(x, DADO_Y + px(16)), (x, PLINTH - px(10))], fill=(18, 12, 8),
               width=max(1, int(px(0.8))))
        x += pw + px(14)
    # skirting
    d.rectangle(box(0, PLINTH, W, FLOOR_Y), fill=mix(TIMBER, (26, 18, 12), 0.4))
    d.line([(0, PLINTH), (W, PLINTH)], fill=mix(TIMBER, TIMBER_L, 0.6),
           width=max(1, int(px(0.9))))
    d.line([(0, FLOOR_Y - px(2)), (W, FLOOR_Y - px(2))], fill=(10, 8, 6),
           width=max(2, int(px(1.2))))


def pier(base, cx):
    """A timber pilaster with a brass capital, standing between two bays."""
    d = ImageDraw.Draw(base)
    w = px(18)
    d.rectangle(box(cx - w, CEIL, cx + w, PLINTH), fill=mix(TIMBER, TIMBER_L, 0.18))
    for k in (-0.55, 0.0, 0.55):
        d.line([(cx + w * k, CEIL), (cx + w * k, PLINTH)],
               fill=mix(TIMBER, TIMBER_D, 0.4 if k else 0.2), width=max(1, int(px(0.7))))
    d.line([(cx - w, CEIL), (cx - w, PLINTH)], fill=mix(TIMBER, (150, 110, 78), 0.30),
           width=max(1, int(px(1.0))))
    d.line([(cx + w, CEIL), (cx + w, PLINTH)], fill=(14, 10, 8),
           width=max(2, int(px(1.2))))
    for y, h in ((CEIL, px(10)), (PLINTH - px(10), px(10))):
        d.rectangle(box(cx - w - px(6), y, cx + w + px(6), y + h),
                    fill=mix(TIMBER, TIMBER_L, 0.35))
        d.line([(cx - w - px(6), y), (cx + w + px(6), y)], fill=mix(BRASS, BRASS_L, 0.3),
               width=max(1, int(px(1.0))))
        d.line([(cx - w - px(6), y + h), (cx + w + px(6), y + h)], fill=(16, 10, 8),
               width=max(1, int(px(0.8))))


def picture(base, x0, x1, y0, y1, seed):
    """A framed certificate on the plaster, with its gilt edge."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(x0 - px(4), y0 - px(4), x1 + px(4), y1 + px(4)), fill=(36, 26, 18))
    d.rectangle(box(x0, y0, x1, y1), fill=mix(BRASS, (120, 90, 40), 0.45))
    d.rectangle(box(x0 + px(3), y0 + px(3), x1 - px(3), y1 - px(3)),
                fill=mix((214, 202, 176), (176, 162, 134), 0.35))
    # the writing on it, and a seal
    rnd = random.Random(seed)
    yy = y0 + (y1 - y0) * 0.22
    while yy < y1 - (y1 - y0) * 0.24:
        d.line([(x0 + (x1 - x0) * 0.14, yy),
                (x0 + (x1 - x0) * rnd.uniform(0.55, 0.86), yy)],
               fill=(96, 84, 66), width=max(1, int(px(0.7))))
        yy += (y1 - y0) * 0.10
    d.ellipse(box(x1 - (x1 - x0) * 0.30, y1 - (y1 - y0) * 0.34,
                  x1 - (x1 - x0) * 0.14, y1 - (y1 - y0) * 0.14),
              outline=mix(RED_GLASS, (170, 84, 60), 0.35), width=max(1, int(px(0.8))))


def column(base, cx):
    """A stone column with a moulded base and capital, against the wall."""
    d = ImageDraw.Draw(base)
    w = px(34)
    # the shadow it casts to the left, and its shaft
    d.rectangle(box(cx - w - px(6), CEIL, cx + w + px(6), PLINTH), fill=(56, 48, 36))
    d.rectangle(box(cx - w, CEIL, cx + w, PLINTH), fill=(142, 126, 98))
    for k in range(-3, 4):
        fx = cx + w * k / 3.6
        d.line([(fx, CEIL + px(8)), (fx, PLINTH - px(8))],
               fill=mix((142, 126, 98), (96, 82, 62), 0.35), width=max(1, int(px(1.0))))
    # a lit left edge and a dark right one
    d.line([(cx - w, CEIL), (cx - w, PLINTH)], fill=(196, 178, 142),
           width=max(2, int(px(1.6))))
    d.line([(cx + w, CEIL), (cx + w, PLINTH)], fill=(48, 40, 30),
           width=max(2, int(px(1.6))))
    for y, h in ((CEIL, px(12)), (PLINTH - px(12), px(12))):     # capital and base
        d.rectangle(box(cx - w - px(8), y, cx + w + px(8), y + h), fill=(160, 144, 112))
        d.line([(cx - w - px(8), y), (cx + w + px(8), y)], fill=(212, 194, 158),
               width=max(1, int(px(1.0))))
        d.line([(cx - w - px(8), y + h), (cx + w + px(8), y + h)], fill=(44, 36, 26),
               width=max(1, int(px(0.9))))


# ----------------------------------------------------------------- the doors
def studded_doors(base, x0, x1):
    """The company's double doors: studded timber, red glass, a brass plate."""
    d = ImageDraw.Draw(base)
    # the casing and the reveal
    d.rectangle(box(x0 - px(14), DOOR_TOP - px(14), x1 + px(14), PLINTH + px(2)),
                fill=(30, 20, 14))
    d.rectangle(box(x0 - px(6), DOOR_TOP - px(6), x1 + px(6), PLINTH), fill=TIMBER_D)

    mid = (x0 + x1) / 2.0
    for lx0, lx1 in ((x0, mid - px(2)), (mid + px(2), x1)):
        d.rectangle(box(lx0, DOOR_TOP, lx1, PLINTH), fill=TIMBER)
        # red glass at the head of each leaf, with the light behind it
        gx0, gx1 = lx0 + px(14), lx1 - px(14)
        gy0, gy1 = DOOR_TOP + px(14), DOOR_TOP + px(52)
        d.rectangle(box(gx0, gy0, gx1, gy1), fill=mix(RED_GLASS, (58, 16, 12), 0.3))
        d.rectangle(box(gx0 + px(3), gy0 + px(3), gx1 - px(3), gy1 - px(3)),
                    fill=mix(RED_GLASS, (206, 96, 70), 0.34))
        d.line([(gx0 + (gx1 - gx0) * 0.5, gy0), (gx0 + (gx1 - gx0) * 0.5, gy1)],
               fill=mix(TIMBER, TIMBER_D, 0.3), width=max(1, int(px(1.2))))
        d.rectangle(box(gx0, gy0, gx1, gy1), outline=mix(TIMBER, BRASS, 0.25),
                    width=max(1, int(px(1.0))))
        # the studs, in rows down the leaf
        rnd = random.Random(int(lx0))
        for r in range(9):
            sy = gy1 + px(14) + r * px(13)
            if sy > PLINTH - px(8):
                break
            for c in range(4):
                sx = lx0 + px(16) + c * (lx1 - lx0 - px(32)) / 3.0
                rr = px(2.6)
                d.ellipse(box(sx - rr, sy - rr, sx + rr, sy + rr),
                          fill=mix(BRASS, BRASS_L, 0.25 + rnd.uniform(0.0, 0.3)))
                d.ellipse(box(sx - rr * 0.6, sy - rr * 0.8, sx + rr * 0.2, sy),
                          fill=mix(BRASS_L, (255, 246, 214), 0.4))
        # a brass push plate at the bottom, and the handle
        d.rectangle(box(lx0 + px(8), PLINTH - px(26), lx1 - px(8), PLINTH - px(14)),
                    fill=mix(BRASS, (120, 90, 40), 0.4))
        d.line([(lx0 + px(8), PLINTH - px(26)), (lx1 - px(8), PLINTH - px(26))],
               fill=mix(BRASS, BRASS_L, 0.4), width=max(1, int(px(1.0))))
        hx = lx1 - px(10) if lx1 < mid + px(10) else lx0 + px(10)
        d.ellipse(box(hx - px(5), DOOR_TOP + px(78), hx + px(5), DOOR_TOP + px(90)),
                  fill=mix(BRASS, BRASS_L, 0.3))
        d.line([(hx - px(3), DOOR_TOP + px(84)), (hx + px(3), DOOR_TOP + px(84))],
               fill=(96, 72, 30), width=max(1, int(px(1.0))))

    # the meeting stile, the fanlight over the doors, and the brass plate
    d.rectangle(box(mid - px(3), DOOR_TOP, mid + px(3), PLINTH), fill=(24, 16, 10))
    d.rectangle(box(x0 - px(10), DOOR_TOP - px(16), x1 + px(10), DOOR_TOP - px(6)),
                fill=mix(TIMBER, TIMBER_L, 0.3))
    d.line([(x0 - px(10), DOOR_TOP - px(16)), (x1 + px(10), DOOR_TOP - px(16))],
           fill=mix(BRASS, BRASS_L, 0.35), width=max(1, int(px(1.2))))
    # the name plate, hung on the lintel between the ceiling and the doors. It
    # used to sit at DOOR_TOP - 52, which was above the top of the canvas.
    px0, px1 = mid - px(92), mid + px(92)
    d.rectangle(box(px0, px(44), px1, px(62)), fill=mix(BRASS, (110, 82, 36), 0.42))
    d.rectangle(box(px0 + px(3), px(46), px1 - px(3), px(60)), fill=mix(BRASS, BRASS_L, 0.22))
    for k in range(3):
        hd.glyph(d, px0 + px(26) + k * px(26), px(47), px(12), (92, 66, 24),
                 seed=31 + k, width=px(1.4))
    lamp(mid, px(52), px(130), (255, 196, 132), 54)


# ------------------------------------------------------------- the reception
def safe(base, x0, x1, y0, y1):
    """The office safe: a stout iron door, a brass dial, heavy hinges.

    Flat bolted bars down the front made it read as a venetian blind, so the
    door is a recessed panel with one big dial and a handle on it instead.
    """
    d = ImageDraw.Draw(base)
    d.rectangle(box(x0 - px(6), y0 - px(6), x1 + px(6), y1 + px(5)), fill=(20, 20, 18))
    d.rectangle(box(x0, y0, x1, y1), fill=mix(IRON, (40, 42, 40), 0.35))
    # the door, set back in the frame, with a raised bead round it
    d.rectangle(box(x0 + px(6), y0 + px(6), x1 - px(6), y1 - px(4)), fill=IRON)
    d.rectangle(box(x0 + px(6), y0 + px(6), x1 - px(6), y1 - px(4)),
                outline=mix(IRON, (140, 142, 136), 0.45), width=max(2, int(px(1.6))))
    d.rectangle(box(x0 + px(12), y0 + px(12), x1 - px(12), y1 - px(10)),
                outline=(34, 36, 34), width=max(1, int(px(0.9))))
    d.line([(x0, y0), (x1, y0)], fill=(150, 152, 144), width=max(2, int(px(1.8))))
    d.line([(x0, y0), (x0, y1)], fill=(104, 106, 100), width=max(1, int(px(1.2))))
    # the dial, big and brass, with its index
    cx = (x0 + x1) / 2.0 - (x1 - x0) * 0.04
    cy = y0 + (y1 - y0) * 0.46
    r = (y1 - y0) * 0.26
    d.ellipse(box(cx - r, cy - r, cx + r, cy + r), fill=mix(BRASS, (86, 64, 30), 0.5))
    d.ellipse(box(cx - r * 0.86, cy - r * 0.86, cx + r * 0.86, cy + r * 0.86),
              fill=mix(BRASS, BRASS_L, 0.28))
    d.ellipse(box(cx - r * 0.30, cy - r * 0.30, cx + r * 0.30, cy + r * 0.30),
              fill=mix(BRASS, (120, 92, 42), 0.4))
    for k in range(8):                                        # the dial's ticks
        a = math.radians(k * 45.0)
        t0, t1 = r * 0.62, r * 0.82
        d.line([(cx + math.cos(a) * t0, cy + math.sin(a) * t0),
                (cx + math.cos(a) * t1, cy + math.sin(a) * t1)],
               fill=(84, 60, 24), width=max(1, int(px(1.0))))
    # the handle, and the hinges down the hinge side
    hy = y0 + (y1 - y0) * 0.80
    d.rectangle(box(x1 - px(34), hy - px(4), x1 - px(14), hy + px(4)),
                fill=mix(BRASS, (100, 76, 34), 0.4))
    d.ellipse(box(x1 - px(40), hy - px(7), x1 - px(28), hy + px(5)), fill=mix(BRASS, BRASS_L, 0.2))
    for k in range(3):
        by = y0 + (y1 - y0) * (0.20 + 0.26 * k)
        d.rectangle(box(x0 - px(2), by, x0 + px(7), by + px(11)), fill=(92, 94, 88))
        d.line([(x0 + px(2), by + px(2)), (x0 + px(2), by + px(9))], fill=(160, 162, 154),
               width=max(1, int(px(0.8))))
    lamp((x0 + x1) / 2.0, y0 - px(2), px(120), (255, 206, 148), 40)


def mail_cabinet(base, x0, x1, y0, y1):
    """The pigeonhole cabinet behind the counter, papers still in the slots."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(x0 - px(5), y0 - px(5), x1 + px(5), y1 + px(5)), fill=(22, 16, 12))
    d.rectangle(box(x0, y0, x1, y1), fill=(44, 30, 20))
    cols, rows = 7, 4
    cw = (x1 - x0) / cols
    rh = (y1 - y0) / rows
    rnd = random.Random(int(x0))
    for r in range(rows):
        for c in range(cols):
            sx0 = x0 + c * cw + px(2)
            sx1 = sx0 + cw - px(4)
            sy0 = y0 + r * rh + px(2)
            sy1 = sy0 + rh - px(4)
            d.rectangle(box(sx0, sy0, sx1, sy1), fill=(26, 18, 12))
            if rnd.random() < 0.62:                            # a paper in the slot
                d.rectangle(box(sx0 + px(2), sy1 - px(9), sx1 - px(2), sy1 - px(2)),
                            fill=mix(PAPER, (188, 178, 156), rnd.uniform(0.0, 0.5)))
            d.line([(sx0, sy0), (sx1, sy0)], fill=(88, 64, 42), width=max(1, int(px(0.7))))
    d.line([(x0, y0), (x1, y0)], fill=(140, 110, 74), width=max(1, int(px(1.2))))


def chair_back(base, cx):
    """The back of a leather office chair, standing at the desk."""
    d = ImageDraw.Draw(base)
    w = px(38)
    top = px(78)
    # the seat's post behind it, and the back itself
    d.rectangle(box(cx - px(6), top + px(30), cx + px(6), COUNTER_Y + px(12)),
                fill=(30, 26, 22))
    d.rounded_rectangle(box(cx - w / 2.0, top, cx + w / 2.0, COUNTER_Y + px(10)),
                        radius=max(2, int(px(12))), fill=LEATHER)
    d.rounded_rectangle(box(cx - w / 2.0, top, cx + w / 2.0, COUNTER_Y + px(10)),
                        radius=max(2, int(px(12))), outline=LEATHER_L,
                        width=max(1, int(px(1.2))))
    # a headrest seam and the tufting down the middle
    d.line([(cx - w * 0.34, top + px(13)), (cx + w * 0.34, top + px(13))],
           fill=mix(LEATHER, LEATHER_L, 0.55), width=max(1, int(px(1.0))))
    d.line([(cx, top + px(16)), (cx, COUNTER_Y + px(4))], fill=mix(LEATHER, LEATHER_L, 0.30),
           width=max(1, int(px(0.8))))
    d.line([(cx - w * 0.36, top + px(4)), (cx - w * 0.36, COUNTER_Y + px(4))],
           fill=mix(LEATHER, (120, 104, 84), 0.30), width=max(1, int(px(0.9))))
    # the armrests, just showing above the counter
    for ax in (cx - w / 2.0 - px(7), cx + w / 2.0 - px(5)):
        d.rounded_rectangle(box(ax, COUNTER_Y - px(4), ax + px(11), COUNTER_Y + px(10)),
                            radius=max(2, int(px(4))), fill=(36, 32, 28))


def counter(base, x0, x1):
    """The reception counter: lit timber top, panelled front, brass foot rail."""
    d = ImageDraw.Draw(base)
    top = COUNTER_Y
    # the top: a thick slab standing proud, bright along its front edge
    d.rectangle(box(x0 - px(14), top - px(11), x1 + px(14), top + px(6)),
                fill=mix(TIMBER_L, (150, 104, 64), 0.35))
    d.line([(x0 - px(14), top - px(11)), (x1 + px(14), top - px(11))],
           fill=(250, 224, 172), width=max(2, int(px(1.8))))
    d.line([(x0 - px(14), top - px(4)), (x1 + px(14), top - px(4))],
           fill=mix(TIMBER_L, (208, 168, 116), 0.4), width=max(1, int(px(1.0))))
    d.line([(x0 - px(14), top + px(6)), (x1 + px(14), top + px(6))], fill=(30, 18, 10),
           width=max(2, int(px(1.6))))

    # the front, in panels, catching the light from the desk lamps
    d.rectangle(box(x0, top + px(6), x1, PLINTH), fill=mix(TIMBER, TIMBER_L, 0.24))
    pw = px(150)
    x = x0 + px(10)
    while x + px(50) < x1 - px(6):
        w = min(pw, x1 - px(12) - x)
        d.rectangle(box(x, top + px(18), x + w, PLINTH - px(12)),
                    fill=mix(TIMBER, TIMBER_D, 0.22))
        d.line([(x, top + px(18)), (x + w, top + px(18))],
               fill=mix(TIMBER, (186, 138, 92), 0.4), width=max(1, int(px(0.9))))
        d.line([(x, PLINTH - px(12)), (x + w, PLINTH - px(12))], fill=(16, 10, 8),
               width=max(2, int(px(1.2))))
        d.line([(x, top + px(18)), (x, PLINTH - px(12))], fill=(16, 10, 8),
               width=max(1, int(px(0.8))))
        x += w + px(12)

    # the brass foot rail on its brackets
    rail_y = PLINTH - px(24)
    for bx in range(int(x0) + int(px(70)), int(x1), int(px(230))):
        d.rectangle(box(bx - px(3), rail_y, bx + px(3), PLINTH - px(6)),
                    fill=mix(BRASS, (92, 70, 34), 0.4))
    d.rectangle(box(x0 + px(8), rail_y, x1 - px(8), rail_y + px(5)),
                fill=mix(BRASS, BRASS_L, 0.28))
    d.line([(x0 + px(8), rail_y), (x1 - px(8), rail_y)], fill=(255, 240, 190),
           width=max(1, int(px(1.0))))
    d.line([(x0 + px(8), rail_y + px(5)), (x1 - px(8), rail_y + px(5))],
           fill=(74, 54, 22), width=max(1, int(px(1.0))))

    # the desk things: papers, a ledger, a brass lamp, the telephone
    def on_desk(cx):
        return cx

    for k in range(3):                                    # papers
        pxx = x0 + (x1 - x0) * (0.16 + 0.09 * k)
        d.polygon([(pxx, top - px(16)), (pxx + px(34), top - px(19)),
                   (pxx + px(36), top - px(13)), (pxx + px(2), top - px(11))],
                  fill=mix(PAPER, (206, 198, 178), 0.2 * k))
        d.line([(pxx + px(4), top - px(14)), (pxx + px(28), top - px(16))],
               fill=(120, 112, 96), width=max(1, int(px(0.6))))
    lx = x0 + (x1 - x0) * 0.40                           # the ledger
    d.rectangle(box(lx, top - px(22), lx + px(52), top - px(11)), fill=(72, 40, 28))
    d.line([(lx, top - px(22)), (lx + px(52), top - px(22))], fill=(158, 118, 70),
           width=max(1, int(px(1.0))))
    # a brass lamp with its green shade
    sx = x0 + (x1 - x0) * 0.62
    d.rectangle(box(sx - px(6), top - px(12), sx + px(6), top - px(6)), fill=mix(BRASS, (96, 72, 32), 0.3))
    d.line([(sx, top - px(12)), (sx, top - px(30))], fill=mix(BRASS, (110, 84, 36), 0.3),
           width=max(2, int(px(2.0))))
    d.polygon([(sx - px(20), top - px(30)), (sx + px(20), top - px(30)),
               (sx + px(13), top - px(44)), (sx - px(13), top - px(44))],
              fill=mix((48, 84, 58), (86, 132, 88), 0.35))
    d.line([(sx - px(20), top - px(30)), (sx + px(20), top - px(30))],
           fill=(150, 196, 150), width=max(1, int(px(1.0))))
    lamp(sx, top - px(28), px(150), (196, 236, 170), 62)
    # the telephone
    px_ = x0 + (x1 - x0) * 0.80
    d.rounded_rectangle(box(px_ - px(16), top - px(14), px_ + px(16), top - px(4)),
                        radius=max(2, int(px(4))), fill=(34, 32, 30))
    d.rounded_rectangle(box(px_ - px(20), top - px(20), px_ + px(20), top - px(13)),
                        radius=max(2, int(px(5))), fill=(42, 40, 36))
    d.ellipse(box(px_ - px(6), top - px(17), px_ + px(6), top - px(13)),
              fill=(72, 70, 64))

    lamp((x0 + x1) / 2.0, top + px(10), px(330), (255, 200, 140), 52)
    lamp((x0 + x1) / 2.0, PLINTH + px(18), px(210), (255, 192, 132), 26)


def plaque(base, x0, x1, y0, y1):
    """The company's brass plate on the plaster over the counter."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(x0 - px(6), y0 - px(6), x1 + px(6), y1 + px(6)), fill=(40, 30, 18))
    d.rectangle(box(x0, y0, x1, y1), fill=mix(BRASS, (128, 96, 42), 0.42))
    d.rectangle(box(x0 + px(10), y0 + px(6), x1 - px(10), y1 - px(6)),
                fill=mix(BRASS, BRASS_L, 0.20))
    d.rectangle(box(x0 + px(4), y0 + px(3), x1 - px(4), y1 - px(3)),
                outline=mix(BRASS, (96, 70, 28), 0.5), width=max(1, int(px(0.9))))
    n = 5
    for k in range(n):
        gx = x0 + (x1 - x0) * (k + 0.5) / n - px(9)
        hd.glyph(d, gx, y0 + (y1 - y0) * 0.26, px(19), (86, 60, 20), seed=41 + k,
                 width=px(1.8))
    lamp((x0 + x1) / 2.0, (y0 + y1) / 2.0, (x1 - x0) * 0.7, (255, 214, 152), 40)


def pendant(base, cx, cy):
    """A brass pendant over the counter, and the pool it throws."""
    d = ImageDraw.Draw(base)
    d.line([(cx, 0), (cx, cy - px(16))], fill=(38, 32, 26), width=max(2, int(px(2.0))))
    d.rectangle(box(cx - px(4), cy - px(20), cx + px(4), cy - px(14)),
                fill=mix(BRASS, (96, 72, 34), 0.4))
    # the shade: a narrow cone with a lit rim
    d.polygon([(cx - px(21), cy - px(4)), (cx + px(21), cy - px(4)),
               (cx + px(9), cy - px(16)), (cx - px(9), cy - px(16))],
              fill=mix(BRASS, (92, 70, 32), 0.35))
    d.line([(cx - px(21), cy - px(4)), (cx + px(21), cy - px(4))],
           fill=mix(BRASS_L, (255, 244, 208), 0.45), width=max(2, int(px(1.8))))
    d.polygon([(cx - px(18), cy - px(5)), (cx + px(18), cy - px(5)),
               (cx + px(12), cy - px(1)), (cx - px(12), cy - px(1))],
              fill=(255, 228, 176))
    d.ellipse(box(cx - px(6), cy - px(3), cx + px(6), cy + px(3)), fill=(255, 252, 226))
    lamp(cx, cy + px(2), px(190), (255, 206, 146), 86)
    lamp(cx, FLOOR_Y + px(30), px(120), (255, 200, 140), 26)


# ---------------------------------------------------------- the far corridor
def corridor(base, x0, x1):
    """The passage through to the back: green light, a step, a doorframe."""
    d = ImageDraw.Draw(base)
    top = px(48)
    d.rectangle(box(x0 - px(16), top - px(16), x1 + px(16), PLINTH + px(4)), fill=(28, 22, 14))
    d.rectangle(box(x0, top, x1, PLINTH), fill=mix(GREEN, (46, 66, 44), 0.62))
    # the passage going back: dark at the frame, lit at the far end, with the
    # floor of the passage running away under it
    for i in range(int(PLINTH - top)):
        tt = i / max(1.0, PLINTH - top)
        c = mix(mix(GREEN, (58, 82, 56), 0.62), mix(GREEN, (168, 214, 168), 0.35), tt ** 1.4)
        # darker down both jambs, so it is a passage and not a green panel
        d.line([(x0 + px(6), top + i), (x1 - px(6), top + i)], fill=c)
    for k in range(3):
        jx = x0 + px(6) + k * px(5)
        d.line([(jx, top), (jx, PLINTH)], fill=mix((28, 38, 26), GREEN, 0.12 + 0.10 * k),
               width=max(1, int(px(2.0))))
        d.line([(x1 - px(6) - k * px(5), top), (x1 - px(6) - k * px(5), PLINTH)],
               fill=mix((28, 38, 26), GREEN, 0.12 + 0.10 * k), width=max(1, int(px(2.0))))
    # a far door at the end of the passage, and its lit head
    fx0, fx1 = x0 + (x1 - x0) * 0.30, x1 - (x1 - x0) * 0.30
    d.rectangle(box(fx0, top + px(30), fx1, PLINTH - px(18)), fill=mix(TIMBER, (46, 62, 46), 0.55))
    d.line([(fx0, top + px(30)), (fx1, top + px(30))], fill=(196, 224, 196),
           width=max(1, int(px(1.2))))
    d.rectangle(box(fx0, top + px(30), fx1, top + px(34)), fill=(120, 156, 118))
    # the stone step at the threshold
    d.rectangle(box(x0, PLINTH - px(10), x1, PLINTH + px(2)), fill=mix((150, 142, 116), (86, 96, 78), 0.35))
    d.line([(x0, PLINTH - px(10)), (x1, PLINTH - px(10))], fill=(206, 206, 176),
           width=max(1, int(px(1.2))))
    # the frame, and the light it lays on the floor
    d.rectangle(box(x0 - px(10), top - px(10), x1 + px(10), top), fill=mix(TIMBER, TIMBER_L, 0.3))
    for sx in (x0 - px(14), x1 + px(2)):
        d.rectangle(box(sx, top, sx + px(12), PLINTH), fill=mix(TIMBER, TIMBER_L, 0.22))
        d.line([(sx, top), (sx, PLINTH)], fill=mix(TIMBER, (156, 118, 84), 0.35),
               width=max(1, int(px(1.0))))
    lamp((x0 + x1) / 2.0, (top + PLINTH) / 2.0, px(230), (150, 210, 150), 62)
    lamp((x0 + x1) / 2.0, FLOOR_Y + px(40), px(230), (140, 200, 142), 44)


def side_room(base, x0, x1):
    """The little back room: a lit table, a chair, and its own green lamp."""
    d = ImageDraw.Draw(base)
    top = px(52)
    d.rectangle(box(x0 - px(12), top - px(12), x1 + px(12), PLINTH + px(2)), fill=(26, 20, 12))
    d.rectangle(box(x0, top, x1, PLINTH), fill=mix((96, 108, 84), (52, 64, 46), 0.4))
    for i in range(int(PLINTH - top)):                       # the wall going back
        tt = i / max(1.0, PLINTH - top)
        d.line([(x0 + px(4), top + i), (x1 - px(4), top + i)],
               fill=mix((122, 136, 106), (56, 68, 50), tt))
    # the table: pale top on its legs, a green-shaded lamp, papers
    ty = px(120)
    for lx in (x0 + px(18), x1 - px(24)):
        d.rectangle(box(lx, ty + px(8), lx + px(6), PLINTH), fill=(96, 92, 76))
    d.rectangle(box(x0 + px(10), ty, x1 - px(10), ty + px(8)), fill=(206, 202, 184))
    d.line([(x0 + px(10), ty), (x1 - px(10), ty)], fill=(248, 246, 232),
           width=max(1, int(px(1.2))))
    d.rectangle(box(x0 + px(10), ty + px(8), x1 - px(10), ty + px(12)), fill=(120, 120, 108))
    for k in range(2):
        d.rectangle(box(x0 + px(16) + k * px(16), ty - px(7), x0 + px(40) + k * px(16), ty - px(1)),
                    fill=mix(PAPER, (196, 190, 170), 0.3))
    sx = x1 - px(26)
    d.line([(sx, ty), (sx, ty - px(26))], fill=(84, 92, 78), width=max(2, int(px(2.0))))
    d.polygon([(sx - px(14), ty - px(26)), (sx + px(14), ty - px(26)),
               (sx + px(9), ty - px(38)), (sx - px(9), ty - px(38))],
              fill=mix((54, 92, 60), (94, 140, 96), 0.35))
    lamp(sx, ty - px(24), px(130), (176, 226, 172), 56)


def wall_lamp(base, x, y):
    """A brass wall lamp on the plaster, and the pool it throws."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(x - px(10), y, x + px(10), y + px(4)), fill=mix(BRASS, (96, 72, 34), 0.4))
    d.polygon([(x - px(22), y - px(4)), (x + px(22), y - px(4)),
               (x + px(13), y - px(18)), (x - px(13), y - px(18))],
              fill=mix(BRASS, (126, 96, 44), 0.3))
    d.line([(x - px(22), y - px(4)), (x + px(22), y - px(4))],
           fill=(255, 236, 186), width=max(1, int(px(1.4))))
    d.ellipse(box(x - px(7), y - px(5), x + px(7), y + px(3)), fill=(255, 246, 212))
    lamp(x, y + px(8), px(160), (255, 202, 140), 62)


# ----------------------------------------------------------------- the floor
def floor(base):
    """Ochre stone flags, with the room's light lying on them."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(19)
    d.rectangle(box(0, FLOOR_Y, W, H), fill=STONE_F)
    rows = [FLOOR_Y, FLOOR_Y + px(22), FLOOR_Y + px(50), FLOOR_Y + px(86), H]
    for i in range(len(rows) - 1):
        y0, y1 = rows[i], rows[i + 1]
        c = mix(STONE_F, STONE_F_L, 0.08 + 0.10 * (i % 2))
        d.rectangle(box(0, y0, W, y1), fill=c)
        d.line([(0, y0), (W, y0)], fill=mix(c, (196, 172, 132), 0.30),
               width=max(1, int(px(0.8))))
        # joints across the flags
        x = rnd.uniform(-px(260), 0)
        while x < W:
            d.line([(x, y0), (x, y1)], fill=mix(c, (56, 44, 30), 0.55),
                   width=max(1, int(px(0.9))))
            x += rnd.uniform(px(240), px(430))
        # the mottling of the stone
        for k in range(9):
            gx = rnd.uniform(0, W)
            gy = rnd.uniform(y0, y1)
            d.ellipse(box(gx, gy, gx + rnd.uniform(px(60), px(220)),
                          gy + rnd.uniform(px(4), px(16))),
                      fill=mix(c, rnd.choice((STONE_F_L, (110, 92, 66), (150, 128, 94))),
                               rnd.uniform(0.10, 0.30)))

    # the wall's shadow on the flags
    for i in range(px(18)):
        a = int(132 * (1 - i / float(px(18))) ** 1.5)
        d.line([(0, FLOOR_Y + i), (W, FLOOR_Y + i)],
               fill=mix(STONE_F, (20, 14, 10), a / 255.0))

    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    for cx0, col, wdt, a in (((BAY_B[0] + BAY_B[1]) / 2.0, (255, 198, 132), px(360), 50),
                             ((DOORS[0] + DOORS[1]) / 2.0, (255, 150, 96), px(200), 42),
                             ((CORRIDOR[0] + CORRIDOR[1]) / 2.0, (150, 210, 150), px(190), 46),
                             ((SIDE[0] + SIDE[1]) / 2.0, (176, 226, 172), px(150), 36)):
        rd.polygon([(cx0 - wdt / 2.0, FLOOR_Y + px(4)), (cx0 + wdt / 2.0, FLOOR_Y + px(4)),
                    (cx0 + wdt * 1.25, H), (cx0 - wdt * 1.25, H)], fill=col + (a,))
    base.alpha_composite(refl.filter(ImageFilter.GaussianBlur(px(26))))

    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.rectangle(box(0, FLOOR_Y, W, H), fill=(214, 190, 150, 14))
    base.alpha_composite(sheen.filter(ImageFilter.GaussianBlur(px(14))))


def foreground():
    """The near plane: dust in the light, and the dark at the bottom."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(61)
    for i in range(px(38)):
        a = int(148 * (1 - i / float(px(38))) ** 1.6)
        d.line([(0, H - i), (W, H - i)], fill=(10, 8, 6, a))
    for _ in range(120):
        x = rnd.uniform(0, W)
        y = rnd.uniform(px(60), H)
        r = rnd.uniform(px(0.9), px(2.6))
        d.ellipse(box(x - r, y - r, x + r, y + r),
                  fill=(255, 214, 158, rnd.randint(18, 58)))
    return fg.filter(ImageFilter.GaussianBlur(px(2.0)))


# ------------------------------------------------------------------- the arena
def paint():
    LIGHTS.clear()
    base = hd.blank([(0, (16, 13, 10)), (CEIL, (34, 28, 22)),
                     (px(140), (58, 46, 34)), (FLOOR_Y, (62, 48, 34)),
                     (H, (30, 22, 16))])

    ceiling(base)
    plaster(base)
    dado(base)
    pier(base, PIER_A)
    pier(base, PIER_B)

    # the doors, the reception and the far rooms
    studded_doors(base, DOORS[0], DOORS[1])
    column(base, COL_X)
    picture(base, px(486), px(534), px(74), px(132), 3)     # on the pier, narrow
    picture(base, px(1272), px(1300), px(80), px(130), 4)

    # behind the counter: safe, plate, mail cabinet, chairs
    safe(base, px(610), px(724), px(62), px(112))
    plaque(base, px(752), px(1012), px(62), px(96))
    mail_cabinet(base, px(1042), px(1188), px(58), px(108))
    picture(base, px(880), px(980), px(108), px(140), 5)
    chair_back(base, px(800))
    chair_back(base, px(944))
    counter(base, px(596), px(1210))
    pendant(base, px(680), px(92))
    pendant(base, px(1130), px(92))

    corridor(base, CORRIDOR[0], CORRIDOR[1])
    side_room(base, SIDE[0], SIDE[1])
    wall_lamp(base, px(96), px(96))
    wall_lamp(base, px(1564), px(96))

    floor(base)

    base = hd.shade(base, [(hd.light(cx, cy, r, col, int(peak * 0.82)),
                            max(8, int(r * 0.30)), 1.05)
                           for cx, cy, r, col, peak in LIGHTS])
    base = art.vignette(base, 0.46)
    base = art.grain(base, 3, seed=23)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


def main():
    hd.STAGES["wingkong_lobby"] = ("Wing Kong Trading Co Lobby", paint)
    hd.build("wingkong_lobby")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
