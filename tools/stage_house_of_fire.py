"""House of Fire: the old shop the car is kept in.

Painted from the plan reference: grey-green boarded walls between brick piers, a
run of glass-fronted cabinets crowded with jars and bowls, a dining table with
its chairs pushed in under the hanging bulbs, the long work counter laid out with
pottery and plates, the timber double gate at the back with the green light
coming under it, the old yellow car standing against the wall with its chrome
grille and whitewall tyres, and barrels, tyres, rope and sacks stacked round it.
The floor is worn stone slabs, oiled and littered, with the light of the place
lying across it.

A stage is seen across the play plane, so the shop is painted as a wall
wall-to-wall: the cabinets, counter, table and the car stand against the back of
the shop with their bases on the floor line, and the fighters stand on the slabs
in front of them. Nothing comes out into the play plane to stand on anybody's
feet.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960, localcoord 1920x1080, camera travel +/-3136.

Run:  python3 tools/stage_house_of_fire.py     (part of tools/build_all.py)
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

CEIL = px(40)                      # 180: the ceiling and its beams
PLINTH = FLOOR_Y - px(12)          # 846
SHELF_X = (px(0), px(300))
CAB_X = (px(300), px(620))
GATE_X = (px(628), px(756))
TABLE_X = px(866)
COUNTER_X = (px(980), px(1460))
CAR_X = (px(1478), px(1772))
BARREL_X = px(1822)

BOARD = (94, 106, 98)              # the green-grey boarding
BOARD_L = (124, 136, 126)
BOARD_D = (56, 66, 60)
BRICK = (118, 74, 58)              # the piers and the outside wall
BRICK_L = (150, 98, 76)
BRICK_D = (72, 44, 34)
TIMBER = (110, 76, 44)             # shelves, counter, gate
TIMBER_L = (152, 112, 68)
TIMBER_D = (62, 42, 22)
COUNTER_TOP = (180, 140, 88)
COUNTER_HI = (216, 178, 120)
CAR = (204, 188, 70)               # the old yellow car
CAR_L = (232, 218, 116)
CAR_D = (148, 132, 42)
CABIN = (44, 44, 46)               # its black roof
GLASS = (46, 58, 54)
JAR = (214, 210, 192)
POT = (150, 96, 58)
SLAB = (96, 98, 94)                # the floor
SLAB_L = (124, 126, 120)
SLAB_D = (62, 64, 62)
GREEN = (104, 224, 152)
WARM = (255, 206, 150)
RED_LAMP = (226, 74, 60)
STEEL = (150, 156, 152)

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
    """Boarded ceiling, beams, and the bulbs strung under it."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, 0, W, CEIL), fill=(34, 32, 28))
    for y in range(0, int(CEIL), int(px(9))):
        d.line([(0, y), (W, y)], fill=(26, 24, 21), width=max(1, int(px(1.0))))
        d.line([(0, y + px(1)), (W, y + px(1))], fill=(48, 44, 38),
               width=max(1, int(px(0.8))))
    d.rectangle(box(0, CEIL - px(10), W, CEIL), fill=(58, 44, 30))
    d.line([(0, CEIL - px(10)), (W, CEIL - px(10))], fill=(96, 74, 46),
           width=max(1, int(px(1.6))))
    d.line([(0, CEIL), (W, CEIL)], fill=(16, 14, 12), width=max(2, int(px(2.2))))
    # the bulbs: cord, shade, filament
    for bx in (px(560), px(1010), px(1560)):
        d.line([(bx, CEIL), (bx, CEIL + px(52))], fill=(26, 24, 20), width=max(1, int(px(1.4))))
        d.polygon([(bx - px(20), CEIL + px(52)), (bx + px(20), CEIL + px(52)),
                   (bx + px(9), CEIL + px(38)), (bx - px(9), CEIL + px(38))],
                  fill=(74, 70, 60))
        d.ellipse(box(bx - px(7), CEIL + px(50), bx + px(7), CEIL + px(64)),
                  fill=(255, 240, 200))
        lamp(bx, CEIL + px(74), px(190), WARM, 92)
    for i in range(px(16)):
        a = int(120 * (1 - i / float(px(16))) ** 1.4)
        d.line([(0, CEIL + i), (W, CEIL + i)], fill=(12, 11, 10, a))


def walls(base):
    """Green-grey boarding between brick piers, damp at the foot."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(5)
    d.rectangle(box(0, CEIL, W, PLINTH), fill=BOARD_D)
    bw = px(19)
    x = 0
    while x < W:
        c = tint(mix(BOARD, rnd.choice((BOARD_L, BOARD_D, (108, 120, 110))),
                     rnd.uniform(0.08, 0.40)), rnd, 0.05)
        d.rectangle(box(x + px(1), CEIL, x + bw - px(1), PLINTH), fill=c)
        d.line([(x + px(1), CEIL), (x + px(1), PLINTH)], fill=mix(c, (170, 180, 168), 0.22),
               width=max(1, int(px(0.8))))
        d.line([(x + bw - px(1), CEIL), (x + bw - px(1), PLINTH)],
               fill=mix(c, (22, 26, 22), 0.5), width=max(1, int(px(1.0))))
        # knots and splits
        if rnd.random() < 0.4:
            ky = rnd.uniform(CEIL + px(20), PLINTH - px(20))
            d.ellipse(box(x + bw * 0.4, ky, x + bw * 0.6, ky + px(5)),
                      fill=mix(c, (60, 44, 30), 0.35))
        x += bw
    # brick piers, and the brick showing where the boarding has come away
    for px0 in (px(300) - px(14), px(620) - px(14), px(1460) - px(14)):
        d.rectangle(box(px0, CEIL, px0 + px(26), PLINTH), fill=BRICK_D)
        ry = CEIL
        row = 0
        while ry < PLINTH:
            off = px(13) if row % 2 else 0
            for bx in range(0, int(px(26)), int(px(13))):
                d.rectangle(box(px0 + bx + off - px(6), ry + px(1), px0 + bx + off + px(5),
                                ry + px(7)), fill=tint(BRICK, rnd, 0.09))
            ry += px(8)
            row += 1
        d.line([(px0, CEIL), (px0, PLINTH)], fill=(40, 30, 24), width=max(1, int(px(1.4))))
    for k in range(14):
        sx = rnd.uniform(0, W)
        sw = rnd.uniform(px(18), px(60))
        sh = rnd.uniform(px(16), px(54))
        sy = rnd.uniform(CEIL + px(40), PLINTH - sh)
        d.rectangle(box(sx, sy, sx + sw, sy + sh), fill=tint(BRICK, rnd, 0.10))
    # what the shop's walls carry: a pinned calendar, a paper notice, a torn
    # poster, all of them yellowed
    for (wx, ww, wh, seed) in ((px(410), px(66), px(84), 3), (px(944), px(52), px(66), 4),
                               (px(1300), px(72), px(58), 5)):
        wy = CEIL + rnd.uniform(px(50), px(120))
        d.rectangle(box(wx, wy, wx + ww, wy + wh), fill=(206, 194, 160))
        d.rectangle(box(wx, wy, wx + ww, wy + wh), outline=(96, 84, 62), width=max(1, int(px(1.2))))
        for row in range(4):
            d.line([(wx + px(4), wy + px(10) + row * wh / 5.0),
                    (wx + ww - px(4), wy + px(10) + row * wh / 5.0)],
                   fill=(140, 128, 104), width=max(1, int(px(1.0))))
        d.ellipse(box(wx + ww / 2.0 - px(3), wy - px(4), wx + ww / 2.0 + px(3), wy + px(2)),
                  fill=(180, 60, 50))

    # a wainscot rail, and the dark at the foot
    d.rectangle(box(0, PLINTH - px(8), W, PLINTH), fill=mix(TIMBER_D, (40, 30, 20), 0.5))
    d.line([(0, PLINTH - px(8)), (W, PLINTH - px(8))], fill=mix(TIMBER, (150, 116, 74), 0.4),
           width=max(1, int(px(1.4))))
    for i in range(px(20)):
        a = int(120 * (1 - i / float(px(20))) ** 1.4)
        d.line([(0, PLINTH - i), (W, PLINTH - i)], fill=(12, 14, 12, a))


def shelves(base, x0, x1):
    """A tall shelf stack of jars and crocks against the brick."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(23)
    top = PLINTH - px(196)
    d.rectangle(box(x0, top, x1, PLINTH), fill=TIMBER_D)
    for sy in range(0, 4):
        y = top + sy * (PLINTH - top) / 4.0
        d.rectangle(box(x0 - px(4), y, x1 + px(4), y + px(7)), fill=TIMBER)
        d.line([(x0 - px(4), y), (x1 + px(4), y)], fill=TIMBER_L, width=max(1, int(px(1.4))))
        # what sits on that shelf: crocks, jars, a jar of sticks
        jx = x0 + px(10)
        while jx < x1 - px(16):
            jw = rnd.uniform(px(14), px(26))
            jh = rnd.uniform(px(18), px(34))
            jy = y - jh
            col = tint(rnd.choice((POT, (176, 132, 84), (198, 176, 140))), rnd, 0.09)
            d.rectangle(box(jx, jy, jx + jw, y), fill=col)
            d.ellipse(box(jx, jy - px(4), jx + jw, jy + px(5)), fill=mix(col, (232, 222, 196), 0.35))
            d.line([(jx, jy + px(4)), (jx, y)], fill=mix(col, (40, 28, 18), 0.35),
                   width=max(1, int(px(1.0))))
            jx += jw + rnd.uniform(px(6), px(14))
    d.rectangle(box(x0, top, x1, PLINTH), outline=(38, 26, 16), width=max(2, int(px(2.0))))
    lamp((x0 + x1) / 2.0, top + px(40), px(180), WARM, 26)


def cabinets(base, x0, x1):
    """Glass-fronted cabinets: two rows of jars behind dusty glass."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(31)
    top = PLINTH - px(170)
    d.rectangle(box(x0, top, x1, PLINTH), fill=TIMBER_D)
    d.rectangle(box(x0 + px(6), top + px(8), x1 - px(6), PLINTH - px(30)), fill=GLASS)
    # three shelves of jars inside
    for s in range(3):
        y = top + px(16) + s * (PLINTH - px(46) - top) / 3.0
        d.rectangle(box(x0 + px(6), y + px(34), x1 - px(6), y + px(40)), fill=TIMBER)
        jx = x0 + px(12)
        while jx < x1 - px(18):
            jw = rnd.uniform(px(11), px(20))
            jh = rnd.uniform(px(14), px(30))
            col = tint(rnd.choice((JAR, (186, 178, 152), (206, 196, 172))), rnd, 0.07)
            d.rectangle(box(jx, y + px(34) - jh, jx + jw, y + px(34)), fill=col)
            d.ellipse(box(jx, y + px(30) - jh, jx + jw, y + px(36) - jh),
                      fill=mix(col, (250, 246, 232), 0.4))
            jx += jw + rnd.uniform(px(4), px(9))
    # the glass: mullions, a reflection, the frame
    for mx in (x0 + (x1 - x0) / 3.0, x0 + 2 * (x1 - x0) / 3.0):
        d.rectangle(box(mx - px(3), top + px(8), mx + px(3), PLINTH - px(30)), fill=TIMBER)
    d.rectangle(box(x0 + px(6), top + px(8), x1 - px(6), top + px(20)),
                fill=(120, 150, 140, 60))
    d.line([(x0 + px(24), top + px(10)), (x0 + px(60), PLINTH - px(40))],
           fill=(190, 210, 200, 40), width=max(4, int(px(8))))
    d.rectangle(box(x0, top, x1, PLINTH), outline=(38, 26, 16), width=max(2, int(px(2.4))))
    d.rectangle(box(x0, PLINTH - px(30), x1, PLINTH), fill=mix(TIMBER, TIMBER_D, 0.4))
    for hx in (x0 + (x1 - x0) * 0.3, x0 + (x1 - x0) * 0.7):
        d.ellipse(box(hx - px(4), PLINTH - px(22), hx + px(4), PLINTH - px(14)),
                  fill=mix(TIMBER_L, (230, 200, 140), 0.4))
    lamp((x0 + x1) / 2.0, top + px(60), px(200), (255, 226, 180), 30)


def double_gate(base, x0, x1):
    """The timber double gate at the back, with green light under it."""
    d = ImageDraw.Draw(base)
    top = PLINTH - px(226)
    d.rectangle(box(x0 - px(12), top - px(12), x1 + px(12), PLINTH), fill=(44, 36, 28))
    d.rectangle(box(x0, top, x1, PLINTH), fill=TIMBER_D)
    mid = (x0 + x1) / 2.0
    for (gx0, gx1) in ((x0 + px(3), mid - px(2)), (mid + px(2), x1 - px(3))):
        d.rectangle(box(gx0, top + px(4), gx1, PLINTH - px(2)), fill=mix(TIMBER, TIMBER_D, 0.3))
        for i in range(1, 7):
            d.line([(gx0, top + px(4) + i * (PLINTH - top) / 7.0),
                    (gx1, top + px(4) + i * (PLINTH - top) / 7.0)],
                   fill=mix(TIMBER_D, (52, 34, 18), 0.4), width=max(1, int(px(1.2))))
        # iron straps and their studs
        for sy in (top + px(30), PLINTH - px(70)):
            d.rectangle(box(gx0, sy, gx1, sy + px(7)), fill=(58, 56, 52))
            d.line([(gx0, sy), (gx1, sy)], fill=(120, 118, 110), width=max(1, int(px(1.2))))
            for k in range(4):
                nx = gx0 + (gx1 - gx0) * (k + 0.5) / 4.0
                d.ellipse(box(nx - px(2), sy + px(1), nx + px(2), sy + px(5)),
                          fill=(140, 136, 126))
    # the green light coming under the gate
    d.rectangle(box(x0, PLINTH - px(6), x1, PLINTH), fill=mix(GREEN, (30, 80, 56), 0.45))
    lamp(mid, PLINTH - px(2), px(150), (120, 226, 160), 66)
    lamp(mid, FLOOR_Y + px(40), px(200), (100, 210, 146), 54)
    d.rectangle(box(x0, top, x1, PLINTH), outline=(30, 22, 14), width=max(2, int(px(2.4))))


def table_chairs(base, cx):
    """The dining table with its chairs pushed in, papers and bowls on it."""
    d = ImageDraw.Draw(base)
    top = PLINTH - px(84)
    # chairs first, so the table top crosses them: the back shows above the
    # edge, which is the only thing that makes a chair a chair at this size
    for sx in (-1, 1):
        chx = cx + sx * px(58)
        d.rectangle(box(chx - px(20), top - px(40), chx + px(20), top + px(6)), fill=(104, 72, 42))
        d.rectangle(box(chx - px(20), top - px(40), chx + px(20), top + px(6)),
                    outline=(58, 38, 20), width=max(1, int(px(1.6))))
        for k in range(2):
            d.rectangle(box(chx - px(14), top - px(32) + k * px(14), chx + px(14),
                            top - px(26) + k * px(14)), fill=(72, 48, 26))
        d.rectangle(box(chx - px(16), top + px(4), chx + px(16), PLINTH), fill=(96, 66, 40))
        for k in range(3):
            d.line([(chx - px(16), top + px(10) + k * px(10)),
                    (chx + px(16), top + px(10) + k * px(10))],
                   fill=(70, 46, 26), width=max(1, int(px(1.4))))
        d.rectangle(box(chx - px(16), top + px(4), chx + px(16), top + px(14)),
                    fill=mix(TIMBER, (150, 110, 66), 0.3))
    d.rectangle(box(cx - px(78), top, cx + px(78), top + px(12)), fill=COUNTER_TOP)
    d.line([(cx - px(78), top), (cx + px(78), top)], fill=COUNTER_HI,
           width=max(2, int(px(2.0))))
    d.line([(cx - px(78), top + px(12)), (cx + px(78), top + px(12))],
           fill=(82, 58, 30), width=max(2, int(px(2.0))))
    # legs, and the bowls and papers on the top
    for lx in (cx - px(66), cx + px(56)):
        d.rectangle(box(lx, top + px(12), lx + px(10), PLINTH), fill=(84, 58, 32))
    for k, (dx, wdt) in enumerate(((-px(56), px(28)), (-px(10), px(24)), (px(34), px(18)))):
        d.ellipse(box(cx + dx, top - px(12), cx + dx + wdt, top + px(2)),
                  fill=mix(JAR, POT, 0.25 + 0.3 * k))
        d.ellipse(box(cx + dx, top - px(12), cx + dx + wdt, top - px(4)),
                  outline=mix(POT, (250, 240, 224), 0.4), width=max(1, int(px(1.4))))
    d.rectangle(box(cx - px(24), top - px(6), cx + px(2), top - px(1)), fill=(226, 220, 202))
    lamp(cx, top - px(20), px(180), WARM, 40)


def counter(base, x0, x1):
    """The long work counter: thick top, pottery along it, cupboards under."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(43)
    top = PLINTH - px(104)
    d.rectangle(box(x0, top, x1, PLINTH), fill=TIMBER_D)
    # the cupboard fronts
    n = 4
    for k in range(n):
        cx0 = x0 + (x1 - x0) * k / n
        cx1 = x0 + (x1 - x0) * (k + 1) / n
        d.rectangle(box(cx0 + px(4), top + px(14), cx1 - px(4), PLINTH - px(6)),
                    fill=tint(mix(TIMBER, TIMBER_D, 0.35), rnd, 0.06))
        # a moulded panel and its grain, so the front is a cupboard and not a slab
        d.rectangle(box(cx0 + px(12), top + px(24), cx1 - px(12), PLINTH - px(16)),
                    outline=mix(TIMBER_D, (36, 24, 12), 0.4), width=max(1, int(px(1.6))))
        for g in range(3):
            gx = cx0 + px(20) + g * ((cx1 - cx0) - px(40)) / 3.0
            d.line([(gx, top + px(28)), (gx + rnd.uniform(-px(3), px(3)), PLINTH - px(20))],
                   fill=mix(TIMBER_D, (150, 112, 66), 0.30), width=max(1, int(px(1.0))))
        d.rectangle(box(cx0 + px(4), top + px(14), cx1 - px(4), PLINTH - px(6)),
                    outline=(46, 32, 18), width=max(1, int(px(1.2))))
    # the top slab, thick, catching the bulb
    d.rectangle(box(x0 - px(10), top - px(12), x1 + px(10), top + px(14)), fill=COUNTER_TOP)
    d.line([(x0 - px(10), top - px(12)), (x1 + px(10), top - px(12))],
           fill=COUNTER_HI, width=max(2, int(px(2.4))))
    d.line([(x0 - px(10), top + px(14)), (x1 + px(10), top + px(14))],
           fill=(74, 52, 28), width=max(2, int(px(2.0))))
    # the pottery laid out on it: plates, bowls, jars, a pair of scales
    x = x0 + px(20)
    while x < x1 - px(30):
        kind = rnd.random()
        w = rnd.uniform(px(20), px(34))
        if kind < 0.5:                                   # a plate seen flat
            d.ellipse(box(x, top - px(16), x + w, top - px(8)), fill=(226, 220, 202))
            d.ellipse(box(x + px(3), top - px(14), x + w - px(3), top - px(10)),
                      outline=(178, 168, 146), width=max(1, int(px(1.2))))
        elif kind < 0.8:                                 # a bowl, side on
            d.pieslice(box(x, top - px(20), x + w, top), 180, 360, fill=mix(POT, JAR, 0.4))
            d.line([(x, top - px(10)), (x + w, top - px(10))], fill=(120, 92, 62),
                   width=max(1, int(px(1.2))))
        else:                                            # a jar
            jw = w * 0.6
            d.rectangle(box(x, top - px(26), x + jw, top - px(8)), fill=mix(JAR, POT, 0.3))
            d.ellipse(box(x, top - px(32), x + jw, top - px(22)), fill=(232, 226, 208))
        x += w + rnd.uniform(px(8), px(22))
    # a brass scale at one end
    sx = x1 - px(90)
    d.line([(sx, top - px(4)), (sx, top - px(30))], fill=(168, 140, 76), width=max(2, int(px(2.4))))
    d.line([(sx - px(22), top - px(30)), (sx + px(22), top - px(30))],
           fill=(186, 158, 92), width=max(2, int(px(2.0))))
    for ex in (sx - px(22), sx + px(22)):
        d.line([(ex, top - px(30)), (ex, top - px(20))], fill=(150, 124, 66),
               width=max(1, int(px(1.2))))
        d.ellipse(box(ex - px(9), top - px(22), ex + px(9), top - px(14)), fill=(176, 148, 84))
    lamp((x0 + x1) / 2.0, top - px(10), px(300), WARM, 54)


def wheel(d, cx, cy, r):
    """A car wheel: tyre, whitewall, hub, and the shadow under it."""
    d.ellipse(box(cx - r, cy - r, cx + r, cy + r), fill=(20, 18, 18))
    d.ellipse(box(cx - r * 0.94, cy - r * 0.94, cx + r * 0.94, cy + r * 0.94),
              fill=(36, 34, 34))
    d.ellipse(box(cx - r * 0.74, cy - r * 0.74, cx + r * 0.74, cy + r * 0.74),
              fill=(206, 200, 186))
    d.ellipse(box(cx - r * 0.58, cy - r * 0.58, cx + r * 0.58, cy + r * 0.58),
              fill=(120, 118, 112))
    d.ellipse(box(cx - r * 0.30, cy - r * 0.30, cx + r * 0.30, cy + r * 0.30),
              fill=(172, 170, 162))
    for k in range(6):
        a = k * math.pi / 3.0
        d.ellipse(box(cx + math.cos(a) * r * 0.20 - r * 0.05,
                      cy + math.sin(a) * r * 0.20 - r * 0.05,
                      cx + math.cos(a) * r * 0.20 + r * 0.05,
                      cy + math.sin(a) * r * 0.20 + r * 0.05), fill=(96, 94, 90))


def car(base, x0, x1):
    """The old yellow car standing against the wall, side on.

    Order matters here: the coachwork is painted first and the wheels after it,
    because a side elevation shows the tyre in front of the body's lower edge.
    Painted the other way round the body covers them and the car becomes a slab
    on skids.
    """
    d = ImageDraw.Draw(base)
    gy = PLINTH
    r = px(28)
    a, b = x0 + px(8), x1 - px(2)
    body_y0, body_y1 = gy - px(96), gy - px(34)      # the flank
    roof_y0 = gy - px(148)
    bon_h, boot_h = px(6), px(5)
    # The car is only ~290 units long, so every offset below is a fraction of
    # that: pillars placed at px(124) from the nose of a 294-unit car put the
    # left one past the right one and the cabin collapsed to a crossed pair of
    # struts.
    cab_l, cab_r = a + px(74), b - px(66)

    # a soft shadow of the car on the wall behind it, not a black placard
    shade_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sld = ImageDraw.Draw(shade_layer)
    sld.rectangle(box(a + px(14), gy - px(152), b - px(14), gy - px(4)),
                  fill=(30, 26, 22, 150))
    base.alpha_composite(shade_layer.filter(ImageFilter.GaussianBlur(px(12))))

    # the flank, lit along its shoulder and shading down to the sill
    d.rounded_rectangle(box(a, body_y0, b, body_y1), radius=max(2, int(px(8))), fill=CAR)
    for i in range(int(body_y1 - body_y0)):
        tt = i / max(1.0, body_y1 - body_y0)
        d.line([(a, body_y0 + i), (b, body_y0 + i)],
               fill=mix(CAR_L, mix(CAR, CAR_D, 0.55), 0.06 + 0.85 * tt), width=1)
    # the bonnet and the boot, a touch lower than the flank's shoulder
    d.rounded_rectangle(box(a + px(2), body_y0 + bon_h, cab_l + px(2), body_y1),
                        radius=max(2, int(px(8))), fill=mix(CAR, CAR_D, 0.10))
    d.rounded_rectangle(box(cab_r - px(2), body_y0 + boot_h, b - px(2), body_y1),
                        radius=max(2, int(px(8))), fill=mix(CAR, CAR_D, 0.10))
    d.line([(a + px(4), body_y0 + bon_h), (cab_l, body_y0 + bon_h)],
           fill=(246, 238, 200), width=max(1, int(px(1.6))))
    d.line([(cab_r, body_y0 + boot_h), (b - px(4), body_y0 + boot_h)],
           fill=(246, 238, 200), width=max(1, int(px(1.6))))

    # the cabin: an opaque shell, then the glass inside it, then the roof
    d.polygon([(cab_l, body_y0 + px(2)), (cab_l + px(16), roof_y0),
               (cab_r - px(14), roof_y0), (cab_r, body_y0 + px(2))], fill=CAR_D)
    d.polygon([(cab_l + px(7), body_y0), (cab_l + px(20), roof_y0 + px(7)),
               (cab_r - px(18), roof_y0 + px(7)), (cab_r - px(7), body_y0)],
              fill=(84, 100, 94))
    d.rectangle(box(cab_l + px(14), roof_y0 - px(2), cab_r - px(12), roof_y0 + px(8)),
                fill=CABIN)
    d.line([(cab_l + px(14), roof_y0 - px(2)), (cab_r - px(12), roof_y0 - px(2))],
           fill=(126, 124, 116), width=max(2, int(px(2.2))))
    # the split screen, and the light lying down the glass
    mid = (cab_l + cab_r) / 2.0
    d.line([(mid, roof_y0 + px(6)), (mid, body_y0)], fill=(44, 40, 34),
           width=max(2, int(px(2.2))))
    d.line([(cab_l + px(24), roof_y0 + px(12)), (cab_l + px(30), body_y0 - px(2))],
           fill=(168, 192, 182), width=max(2, int(px(2.6))))
    d.line([(cab_l + px(18), roof_y0 + px(4)), (cab_l + px(16), body_y0)],
           fill=CAR_D, width=max(2, int(px(2.4))))
    d.line([(cab_r - px(16), roof_y0 + px(4)), (cab_r - px(14), body_y0)],
           fill=CAR_D, width=max(2, int(px(2.4))))

    # the doors, their seams and handles, and the chrome waist strip
    for dx in (cab_l, cab_r):
        d.line([(dx, body_y0 + px(6)), (dx, body_y1)], fill=mix(CAR_D, (60, 48, 18), 0.4),
               width=max(1, int(px(1.8))))
    for hx in (cab_l + px(14), cab_r - px(30)):
        d.rectangle(box(hx, body_y0 + px(34), hx + px(14), body_y0 + px(40)),
                    fill=(212, 208, 196))
    d.line([(a + px(8), body_y0 + px(26)), (b - px(8), body_y0 + px(26))],
           fill=(240, 234, 214), width=max(2, int(px(2.2))))
    d.line([(a + px(8), body_y0 + px(30)), (b - px(8), body_y0 + px(30))],
           fill=(120, 106, 52), width=max(1, int(px(1.6))))

    # running board between the wheels, and the sills
    d.rectangle(box(a + px(40), body_y1, b - px(38), body_y1 + px(12)), fill=(46, 42, 36))
    d.line([(a + px(40), body_y1), (b - px(38), body_y1)], fill=(150, 146, 134),
           width=max(1, int(px(1.6))))

    # the front: grille, bumper, headlamp, all standing proud of the bonnet
    d.rectangle(box(a - px(4), body_y0 - px(14), a + px(22), body_y1 + px(8)), fill=(178, 176, 168))
    for i in range(8):
        d.line([(a - px(1), body_y0 - px(10) + i * px(8)), (a + px(19), body_y0 - px(10) + i * px(8))],
               fill=(86, 84, 80), width=max(1, int(px(1.4))))
    d.rectangle(box(a - px(12), body_y1 + px(4), a + px(28), body_y1 + px(18)), fill=(198, 196, 186))
    d.line([(a - px(12), body_y1 + px(4)), (a + px(28), body_y1 + px(4))],
           fill=(242, 240, 228), width=max(1, int(px(1.6))))
    d.ellipse(box(a + px(2), body_y0 - px(30), a + px(30), body_y0 - px(4)),
              fill=(210, 206, 188))
    d.ellipse(box(a + px(8), body_y0 - px(24), a + px(24), body_y0 - px(10)),
              fill=(250, 248, 234))
    d.rectangle(box(b - px(26), body_y1 + px(4), b + px(14), body_y1 + px(18)),
                fill=(190, 188, 178))
    # a scraped band low on the flank
    d.line([(a + px(24), body_y1 - px(6)), (b - px(24), body_y1 - px(6))],
           fill=(94, 82, 38), width=max(3, int(px(4))))

    # the wheels last, so the tyres sit in front of the sills
    for wx in (a + px(62), b - px(56)):
        wheel(d, wx, gy - r, r)
    lamp((a + b) / 2.0, gy - px(84), px(300), (255, 226, 168), 40)


def clutter(base, cx):
    """Barrels, a stack of tyres, coiled rope, sacks and crates."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(59)
    # barrels
    for i, dy in enumerate((0, px(38))):
        bx = cx - px(18)
        by = PLINTH - px(58) - dy * 0.5
        d.rectangle(box(bx, by, bx + px(36), PLINTH - dy * 0.5), fill=mix(POT, TIMBER, 0.35))
        for k in range(3):
            d.line([(bx, by + px(8) + k * px(16)), (bx + px(36), by + px(8) + k * px(16))],
                   fill=(76, 52, 30), width=max(1, int(px(1.6))))
        d.ellipse(box(bx, by - px(6), bx + px(36), by + px(8)), fill=mix(POT, JAR, 0.3))
    # tyres, seen edge on and stacked
    ty = PLINTH - px(24)
    for i in range(3):
        d.ellipse(box(cx + px(42), ty - px(26) - i * px(20), cx + px(94), ty + px(2) - i * px(20)),
                  fill=(34, 32, 32))
        d.ellipse(box(cx + px(48), ty - px(21) - i * px(20), cx + px(88), ty - px(3) - i * px(20)),
                  fill=(24, 22, 22))
    # rope coiled against the wall
    for k in range(4):
        d.arc(box(cx + px(104), PLINTH - px(40) + k * px(6), cx + px(152), PLINTH + k * px(6)),
              190, 350, fill=(150, 126, 86), width=max(2, int(px(2.6))))
    # sacks and a crate at the foot
    for i, (dx, w, h) in enumerate(((px(-96), px(58), px(44)), (px(-84), px(46), px(34)))):
        d.rounded_rectangle(box(cx + dx, PLINTH - h, cx + dx + w, PLINTH),
                            radius=max(2, int(px(10))), fill=(158, 146, 118))
        d.line([(cx + dx + px(6), PLINTH - h + px(8)), (cx + dx + w - px(6), PLINTH - h + px(8))],
               fill=(122, 110, 84), width=max(1, int(px(1.4))))
    d.rectangle(box(cx - px(34), PLINTH - px(52), cx + px(30), PLINTH), fill=mix(TIMBER, TIMBER_D, 0.2))
    d.line([(cx - px(34), PLINTH - px(52)), (cx + px(30), PLINTH)],
           fill=(58, 40, 22), width=max(1, int(px(1.6))))
    d.line([(cx + px(30), PLINTH - px(52)), (cx - px(34), PLINTH)],
           fill=(58, 40, 22), width=max(1, int(px(1.6))))


# ------------------------------------------------------------------ the floor
def floor(base):
    """Worn stone slabs, oiled and littered, with the light lying across them."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(71)
    d.rectangle(box(0, FLOOR_Y, W, H), fill=SLAB_D)
    rows = [FLOOR_Y, FLOOR_Y + px(20), FLOOR_Y + px(46), FLOOR_Y + px(76),
            FLOOR_Y + px(112), H]
    row = 0
    for i in range(len(rows) - 1):
        y0, y1 = rows[i], rows[i + 1]
        sw = px(52) + i * px(10)
        x = -sw // 2 if row % 2 else 0
        while x < W:
            c = tint(mix(SLAB, rnd.choice((SLAB_L, SLAB_D, (108, 110, 104))),
                         rnd.uniform(0.10, 0.40)), rnd, 0.05)
            d.rectangle(box(x + px(1), y0 + px(1), x + sw - px(1), y1 - px(1)), fill=c)
            d.line([(x + px(1), y0 + px(1)), (x + sw - px(1), y0 + px(1))],
                   fill=mix(c, (180, 184, 176), 0.20), width=max(1, int(px(0.6))))
            d.line([(x + px(1), y1 - px(1)), (x + sw - px(1), y1 - px(1))],
                   fill=mix(c, (20, 22, 20), 0.42), width=max(1, int(px(0.8))))
            # cracks across the odd slab
            if rnd.random() < 0.22:
                sx = rnd.uniform(x + px(6), x + sw - px(12))
                d.line([(sx, y0 + px(3)), (sx + rnd.uniform(-px(10), px(10)), y1 - px(3))],
                       fill=mix(c, (26, 26, 24), 0.55), width=max(1, int(px(1.0))))
            x += sw
        row += 1

    # the base course the furniture stands on
    d.rectangle(box(0, PLINTH, W, FLOOR_Y), fill=mix(SLAB, (74, 70, 62), 0.45))
    d.line([(0, PLINTH), (W, PLINTH)], fill=mix(SLAB_L, (168, 162, 148), 0.35),
           width=max(2, int(px(2.0))))
    d.line([(0, FLOOR_Y), (W, FLOOR_Y)], fill=(20, 18, 16), width=max(2, int(px(2.4))))

    # oil and water standing on the slabs
    stain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stain)
    for k in range(16):
        sx = rnd.uniform(0, W)
        sy = rnd.uniform(FLOOR_Y + px(20), H - px(10))
        w, h = rnd.uniform(px(60), px(220)), rnd.uniform(px(12), px(34))
        sd.ellipse(box(sx - w / 2.0, sy - h / 2.0, sx + w / 2.0, sy + h / 2.0),
                   fill=(22, 22, 20, 90))
    base.alpha_composite(stain.filter(ImageFilter.GaussianBlur(px(14))))

    # the light lying in the floor: the bulbs, and the green under the gate
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for cx0, col, wdt, a in ((px(560), (255, 214, 160), px(260), 60),
                             (px(1010), (255, 214, 160), px(300), 66),
                             (px(1560), (255, 214, 160), px(260), 56),
                             (px(692), (118, 224, 156), px(220), 84),
                             (px(1600), (120, 216, 150), px(260), 46)):
        gd.polygon([(cx0 - wdt * 0.34, FLOOR_Y + px(4)), (cx0 + wdt * 0.34, FLOOR_Y + px(4)),
                    (cx0 + wdt * 0.60, H), (cx0 - wdt * 0.60, H)], fill=col + (a,))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(px(26))))

    # the slabs take the light: a wet sheen under each bulb and off the gate
    for cx0, col, wdt, a in ((px(560), (255, 224, 178), px(150), 34),
                             (px(1010), (255, 224, 178), px(180), 38),
                             (px(1560), (255, 224, 178), px(150), 30),
                             (px(692), (128, 232, 168), px(120), 42)):
        sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        shd = ImageDraw.Draw(sheen)
        for k in range(7):
            yy = FLOOR_Y + px(14) + k * px(16)
            ww = wdt * (1 + k * 0.22)
            shd.line([(cx0 - ww / 2.0, yy), (cx0 + ww / 2.0, yy)], fill=col + (a,),
                     width=max(2, int(px(4.0))))
        base.alpha_composite(sheen.filter(ImageFilter.GaussianBlur(px(9))))

    # rubbish: crates knocked about, papers, a loose tyre
    for k in range(24):
        sx = rnd.uniform(0, W)
        sy = rnd.uniform(FLOOR_Y + px(18), H - px(8))
        w, h = rnd.uniform(px(10), px(28)), rnd.uniform(px(4), px(10))
        d.rectangle(box(sx, sy, sx + w, sy + h),
                    fill=tint(rnd.choice(((186, 180, 160), (128, 120, 100), SLAB_L)),
                              rnd, 0.1))
    lamp(CX, FLOOR_Y + px(90), px(520), (255, 216, 168), 26)


def foreground():
    """The near plane: the dark at the bottom, and the dust in the air."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(97)
    for i in range(px(34)):
        a = int(150 * (1 - i / float(px(34))) ** 1.6)
        d.line([(0, H - i), (W, H - i)], fill=(8, 7, 7, a))
    for _ in range(110):
        x = rnd.uniform(0, W)
        y = rnd.uniform(px(60), H)
        r = rnd.uniform(px(1.0), px(2.4))
        d.ellipse(box(x - r, y - r, x + r, y + r),
                  fill=(250, 238, 214, rnd.randint(12, 44)))
    return fg.filter(ImageFilter.GaussianBlur(px(3.0)))


# ------------------------------------------------------------------- the arena
def paint():
    LIGHTS.clear()
    base = hd.blank([(0, (16, 15, 13)), (CEIL, (26, 26, 22)),
                     (px(140), (52, 56, 48)), (FLOOR_Y, (58, 62, 54)),
                     (H, (26, 28, 24))])

    ceiling(base)
    walls(base)
    shelves(base, SHELF_X[0], SHELF_X[1])
    cabinets(base, CAB_X[0], CAB_X[1])
    double_gate(base, GATE_X[0], GATE_X[1])
    table_chairs(base, TABLE_X)
    counter(base, COUNTER_X[0], COUNTER_X[1])
    car(base, CAR_X[0], CAR_X[1])
    clutter(base, BARREL_X)

    floor(base)

    base = hd.shade(base, [(hd.light(cx, cy, r, col, int(peak * 0.84)),
                            max(8, int(r * 0.30)), 1.05)
                           for cx, cy, r, col, peak in LIGHTS])
    base = hd.bloom(base, 150, px(5), 0.55)
    base = art.vignette(base, 0.46)
    base = art.grain(base, 3, seed=61)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


def main():
    hd.STAGES["house_of_fire"] = ("House of Fire", paint)
    hd.build("house_of_fire")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
