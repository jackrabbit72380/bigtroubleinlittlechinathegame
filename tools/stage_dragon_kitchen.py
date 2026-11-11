"""Dragon of the Black Pool Restaurant Kitchen: the working kitchen behind the
swing door, painted from the top-down kitchen reference.

The reference is a plan seen from above: white tiled walls, a window with herbs
on the sill, shelves of stoneware and jars, a sink, a radiator, a big range under
an extractor hood, hanging pans, and steel prep tables covered in plates, bowls,
dumplings and a pile of chrysanthemums, with a dark red table and chairs in the
middle of the room.

A stage is seen across the play plane, not from above, so the plan is painted as
one long wall of kitchen: everything sits against the tiled wall, the tables and
counters are drawn up to the skirting, and the tiled floor the fighters stand on
runs out towards the camera. Nothing is placed out in the play plane, so no prop
ever stands across the fighters' feet.

This is the room on the other side of the dining room's kitchen door, so it
borrows the dining room's red chairs and its red cloth, and ends at the same
warm light spilling through the swing door.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960, localcoord 1920x1080, camera travel +/-3136.

Run:  python3 tools/stage_dragon_kitchen.py     (part of tools/build_all.py)
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

WALL_TOP = px(44)                  # 198: ceiling line above the tiled wall
RAIL = FLOOR_Y - px(26)            # 783: where the tiled dado starts

# glazed wall tile, grout and the darker course at the bottom of the wall
TILE = (206, 200, 182)
TILE_D = (178, 172, 154)
GROUT = (146, 138, 120)
DADO = (86, 88, 80)
DADO_L = (122, 124, 114)

# brushed steel: counters, hood, sink, pans
STEEL = (148, 152, 150)
STEEL_L = (200, 204, 202)
STEEL_D = (86, 90, 90)

# painted cupboards and shelving
CREAM = (226, 220, 198)
CREAM_D = (188, 182, 160)

WOOD = (92, 56, 34)
WOOD_L = (138, 90, 54)
WOOD_D = (52, 30, 18)

RED = (128, 40, 30)
RED_L = (172, 58, 44)
BRASS = (176, 138, 66)
GOLD = (198, 152, 72)
GOLD_L = (238, 202, 126)
GOLD_D = (124, 88, 36)
WARM = (255, 212, 148)

PORCELAIN = (236, 232, 218)
GREEN = (84, 106, 58)
GREEN_L = (128, 152, 78)
CLAY = (168, 98, 62)

# the floor: white square tile, grey grout, so it reads as a working kitchen
FL_L = (206, 198, 178)
FL_D = (198, 190, 170)
FL_GRID = (140, 132, 112)

# every warm source is collected here while the room is painted and blended in
# once at the end, so a lamp lights the tile around it instead of sitting on top
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


def grain_lines(d, x0, y0, x1, y1, rnd, n=5, tone=0.3):
    """A few wavy lines so a flat panel of timber reads as wood."""
    for _ in range(n):
        gy = rnd.uniform(y0, y1)
        d.line([(x0, gy), (x1, gy + rnd.uniform(-px(0.8), px(0.8)))],
               fill=mix(WOOD, WOOD_D, tone), width=1)


def slab(d, x0, y0, x1, y1, c, hi=0.35, lo=0.30):
    """A metal or painted panel: lit top edge, shaded bottom edge, flat middle."""
    d.rectangle(box(x0, y0, x1, y1), fill=c)
    d.line([(x0, y0), (x1, y0)], fill=mix(c, (255, 250, 236), hi),
           width=max(1, int(px(0.8))))
    d.line([(x0, y1), (x1, y1)], fill=mix(c, (24, 22, 20), lo),
           width=max(1, int(px(0.9))))
    d.line([(x0, y0), (x0, y1)], fill=mix(c, (255, 250, 236), hi * 0.7),
           width=max(1, int(px(0.6))))
    d.line([(x1, y0), (x1, y1)], fill=mix(c, (24, 22, 20), lo * 0.8),
           width=max(1, int(px(0.6))))


# ------------------------------------------------------------------ the ceiling
def ceiling(base):
    """Concrete ceiling, the extractor duct and the steel beam over the tiles."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, 0, W, WALL_TOP), fill=(26, 24, 22))

    # shuttered concrete panels, lit along their top edges
    for x in range(-px(30), W, px(60)):
        d.rectangle(box(x, 0, x + px(58), WALL_TOP - px(14)), fill=(34, 32, 29))
        d.line([(x, 0), (x, WALL_TOP - px(14))], fill=(48, 45, 40),
               width=max(1, int(px(0.8))))
        d.line([(x + px(58), 0), (x + px(58), WALL_TOP - px(14))], fill=(18, 17, 15),
               width=max(1, int(px(1.0))))

    # the extractor duct running the length of the ceiling, with its flanges
    d.rectangle(box(0, px(2), W, px(26)), fill=(52, 55, 54))
    d.line([(0, px(2)), (W, px(2))], fill=(96, 100, 98), width=max(1, int(px(0.7))))
    d.line([(0, px(26)), (W, px(26))], fill=(20, 21, 20), width=max(1, int(px(1.0))))
    for x in range(0, W + px(1), px(150)):
        d.rectangle(box(x, px(1), x + px(6), px(27)), fill=(72, 76, 74))
        d.line([(x, px(1)), (x, px(27))], fill=(112, 116, 112), width=max(1, int(px(0.6))))

    # a steel beam, painted dark, that the pendants and the pan rail hang from
    d.rectangle(box(0, WALL_TOP - px(13), W, WALL_TOP), fill=(58, 60, 58))
    d.line([(0, WALL_TOP - px(13)), (W, WALL_TOP - px(13))],
           fill=(122, 126, 122), width=max(1, int(px(0.8))))
    d.line([(0, WALL_TOP - px(9)), (W, WALL_TOP - px(9))],
           fill=(84, 88, 84), width=max(1, int(px(0.6))))
    d.line([(0, WALL_TOP - px(1)), (W, WALL_TOP - px(1))],
           fill=(12, 12, 11), width=max(2, int(px(1.6))))
    for x in range(0, W + px(1), px(84)):
        d.line([(x, WALL_TOP - px(8)), (x, WALL_TOP - px(1))], fill=(40, 42, 40),
               width=max(1, int(px(1.0))))


# -------------------------------------------------------------------- the wall
def tile_wall(base):
    """White glazed square tile, floor to ceiling, with a working kitchen's grime.

    Every tile is drawn a little off its neighbours so the wall reads as laid
    by hand rather than printed, and the course above the range is stained by
    years of frying.
    """
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, WALL_TOP, W, RAIL), fill=GROUT)
    t = px(9)
    rnd = random.Random(31)

    for r, y in enumerate(range(WALL_TOP, RAIL, t)):
        for c, x in enumerate(range(-t, W + t, t)):
            k = rnd.uniform(-0.05, 0.05)
            c0 = tuple(max(0, min(255, int(v * (1 + k)))) for v in TILE)
            if rnd.random() < 0.05:                     # a tile that has aged
                c0 = mix(c0, TILE_D, rnd.uniform(0.2, 0.55))
            d.rectangle(box(x + px(1), y + px(1), x + t - px(1), y + t - px(1)), fill=c0)
            d.line([(x + px(1.6), y + px(1.6)), (x + t - px(1.6), y + px(1.6))],
                   fill=mix(c0, (255, 252, 238), 0.45), width=max(1, int(px(0.4))))
            d.line([(x + px(1.6), y + t - px(1.6)), (x + t - px(1.6), y + t - px(1.6))],
                   fill=mix(c0, (116, 110, 96), 0.22), width=max(1, int(px(0.5))))
            if rnd.random() < 0.006:                    # a hairline crack
                cx0 = x + rnd.uniform(px(2), px(6))
                d.line([(cx0, y + px(2)), (cx0 + rnd.uniform(-px(3), px(3)), y + t - px(2))],
                       fill=mix(c0, (96, 90, 78), 0.5), width=1)

    # shadow under the ceiling, so the wall is not lit flat to its top edge
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for i in range(px(34)):
        a = int(150 * (1 - i / float(px(34))) ** 1.4)
        sd.line([(0, WALL_TOP + i), (W, WALL_TOP + i)], fill=(0, 0, 0, a))

    # frying: soot above the range, grease either side of it
    for i in range(px(70)):
        tt = 1 - i / float(px(70))
        a = int(84 * tt ** 1.4)
        sd.rectangle(box(px(690), WALL_TOP + i, px(950), min(RAIL, WALL_TOP + i + px(1))),
                     fill=(74, 60, 38, a))
    for i in range(px(46)):
        a = int(46 * (1 - i / float(px(46))) ** 1.2)
        sd.rectangle(box(px(640), WALL_TOP + i, px(1000), min(RAIL, WALL_TOP + i + 1)),
                     fill=(72, 58, 36, a))
    base.alpha_composite(shade.filter(ImageFilter.GaussianBlur(px(5))))
    base.alpha_composite(shade)


def dado(base):
    """The darker tile course at the foot of the wall, with a chrome rail."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, RAIL, W, FLOOR_Y), fill=DADO)
    t = px(7)
    rnd = random.Random(57)
    for r, y in enumerate(range(RAIL + px(3), FLOOR_Y, t)):
        for x in range(-t, W + t, t):
            c0 = tint(DADO, rnd, 0.10)
            d.rectangle(box(x + px(1), y + px(1), x + t - px(1), y + t - px(1)), fill=c0)
            d.line([(x + px(1.5), y + px(1.5)), (x + t - px(1.5), y + px(1.5))],
                   fill=mix(c0, DADO_L, 0.6), width=max(1, int(px(0.4))))
            d.line([(x + px(1.5), y + t - px(1.5)), (x + t - px(1.5), y + t - px(1.5))],
                   fill=mix(c0, (34, 38, 38), 0.4), width=max(1, int(px(0.5))))

    d.rectangle(box(0, RAIL, W, RAIL + px(4)), fill=mix(STEEL, STEEL_L, 0.45))
    d.line([(0, RAIL), (W, RAIL)], fill=(226, 230, 226), width=max(1, int(px(0.8))))
    d.line([(0, RAIL + px(4)), (W, RAIL + px(4))], fill=(88, 90, 86),
           width=max(1, int(px(0.8))))
    d.rectangle(box(0, FLOOR_Y - px(6), W, FLOOR_Y), fill=(46, 48, 46))
    d.line([(0, FLOOR_Y - px(6)), (W, FLOOR_Y - px(6))], fill=(120, 124, 120),
           width=max(1, int(px(0.6))))


# ------------------------------------------------------------------ the window
def pot(d, cx, base_y, w, seed):
    """A terracotta pot of kitchen herbs: rim, taper, and a few leafy sprigs."""
    r = random.Random(seed)
    h = w * 0.95
    d.polygon([(cx - w * 0.5, base_y - h), (cx + w * 0.5, base_y - h),
               (cx + w * 0.38, base_y), (cx - w * 0.38, base_y)], fill=CLAY)
    d.polygon([(cx - w * 0.5, base_y - h), (cx + w * 0.5, base_y - h),
               (cx + w * 0.46, base_y - h * 0.78), (cx - w * 0.46, base_y - h * 0.78)],
              fill=mix(CLAY, (222, 152, 104), 0.4))
    d.line([(cx - w * 0.38, base_y), (cx + w * 0.38, base_y)], fill=(104, 54, 32),
           width=max(1, int(px(1.0))))
    d.rectangle(box(cx - w * 0.44, base_y - h - px(1), cx + w * 0.44, base_y - h + px(1.5)),
                fill=mix(CLAY, (60, 34, 20), 0.3))
    for i in range(5):
        a = (i / 5.0) * 6.28 + r.uniform(-0.3, 0.3)
        tipx = cx + math.cos(a) * w * 0.62
        tipy = base_y - h - w * (0.30 + 0.5 * abs(math.sin(a)))
        d.line([(cx, base_y - h), (tipx, tipy)], fill=mix(GREEN, (44, 62, 30), 0.35),
               width=max(1, int(px(0.7))))
        for k in range(3):
            ly = tipy + (base_y - h - tipy) * (0.25 + 0.22 * k)
            lx = cx + (tipx - cx) * (0.25 + 0.22 * k)
            rr = w * 0.15
            d.ellipse(box(lx - rr, ly - rr * 0.6, lx + rr, ly + rr * 0.6),
                      fill=mix(GREEN_L, (64, 86, 44), 0.3))


def window(base, cx, w=px(150), top=px(54), bot=px(116)):
    """The window over the sink: daylight, leaves outside, and herbs on the sill."""
    d = ImageDraw.Draw(base)
    x0, x1 = cx - w / 2.0, cx + w / 2.0

    d.rectangle(box(x0 - px(7), top - px(7), x1 + px(7), bot + px(7)), fill=(64, 66, 62))
    d.rectangle(box(x0 - px(3), top - px(3), x1 + px(3), bot + px(3)), fill=(198, 194, 178))
    d.rectangle(box(x0, top, x1, bot), fill=(206, 222, 214))
    for i in range(int(bot - top)):
        tt = i / max(1.0, bot - top - 1)
        d.line([(x0, top + i), (x1, top + i)],
               fill=mix((206, 226, 228), (250, 250, 242), tt ** 0.7))

    # leaves outside, soft and out of focus: a yard behind the service door
    leaf = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(leaf)
    rnd = random.Random(9)
    for i in range(90):
        lx = rnd.uniform(x0 - px(4), x1 + px(4))
        ly = rnd.uniform(top + (bot - top) * 0.34, bot + px(2))
        rr = rnd.uniform(px(5), px(16))
        ld.ellipse(box(lx - rr, ly - rr, lx + rr, ly + rr),
                   fill=mix((92, 122, 74), (168, 196, 142), rnd.uniform(0.1, 0.8)) +
                   (rnd.randint(90, 170),))
    base.alpha_composite(leaf.filter(ImageFilter.GaussianBlur(px(3))))

    # frame: two lights with muntins, a lit internal edge and a deep sill
    d.rectangle(box(cx - px(2.5), top, cx + px(2.5), bot), fill=(206, 202, 186))
    d.line([(cx - px(2.5), top), (cx - px(2.5), bot)], fill=(246, 244, 232),
           width=max(1, int(px(0.6))))
    for i in range(1, 3):
        gy = top + (bot - top) * i / 3.0
        d.rectangle(box(x0, gy - px(1.6), x1, gy + px(1.6)), fill=(206, 202, 186))
    d.rectangle(box(x0, top, x1, top + px(3)), fill=(150, 146, 132))
    d.line([(x0, top), (x1, top)], fill=(242, 240, 228), width=max(1, int(px(0.7))))

    # the sill and the herbs standing on it
    d.rectangle(box(x0 - px(9), bot, x1 + px(9), bot + px(8)), fill=(214, 210, 194))
    d.line([(x0 - px(9), bot), (x1 + px(9), bot)], fill=(250, 248, 238),
           width=max(1, int(px(0.8))))
    d.line([(x0 - px(9), bot + px(8)), (x1 + px(9), bot + px(8))], fill=(112, 108, 96),
           width=max(1, int(px(0.8))))
    for i, fx in enumerate((0.18, 0.46, 0.76)):
        pot(d, x0 + w * fx, bot - px(1), w * 0.15, 60 + i)

    lamp(cx, bot - px(6), px(190), (206, 232, 226), 132)
    lamp(cx, FLOOR_Y + px(20), px(150), (196, 222, 216), 40)


# ------------------------------------------------------------------ the joinery
def cabinet(d, x0, x1, top, seed, body=CREAM, doors=2, knobs=True):
    """A painted cupboard: cornice, framed doors, plinth, brass knobs."""
    rnd = random.Random(seed)
    slab(d, x0, top, x1, FLOOR_Y - px(6), body, hi=0.30, lo=0.34)
    d.rectangle(box(x0 - px(2), top - px(5), x1 + px(2), top + px(1)),
                fill=mix(body, (255, 250, 232), 0.35))
    d.line([(x0 - px(2), top - px(5)), (x1 + px(2), top - px(5))],
           fill=(252, 248, 234), width=max(1, int(px(0.7))))

    w = (x1 - x0) / float(max(1, doors))
    for i in range(doors):
        dx0 = x0 + i * w + px(4)
        dx1 = x0 + (i + 1) * w - px(4)
        d.rectangle(box(dx0, top + px(7), dx1, FLOOR_Y - px(16)),
                    fill=mix(body, CREAM_D, 0.44))
        d.line([(dx0, top + px(7)), (dx1, top + px(7))], fill=mix(body, (60, 56, 44), 0.35),
               width=max(1, int(px(0.7))))
        d.line([(dx0, top + px(7)), (dx0, FLOOR_Y - px(16))], fill=mix(body, (255, 252, 240), 0.5),
               width=max(1, int(px(0.6))))
        d.line([(dx1, top + px(7)), (dx1, FLOOR_Y - px(16))], fill=mix(body, (60, 56, 44), 0.3),
               width=max(1, int(px(0.7))))
        # an inner bead, so the door is a frame and not a flat rectangle
        d.rectangle(box(dx0 + px(4), top + px(12), dx1 - px(4), FLOOR_Y - px(22)),
                    outline=mix(body, CREAM_D, 0.45), width=max(1, int(px(0.6))))
        if knobs:
            kx = dx1 - px(6) if i % 2 == 0 else dx0 + px(6)
            d.ellipse(box(kx - px(2), top + px(34), kx + px(2), top + px(40)),
                      fill=mix(BRASS, GOLD_L, 0.35))
        for _ in range(2):
            gy = rnd.uniform(top + px(16), FLOOR_Y - px(26))
            d.line([(dx0 + px(7), gy), (dx1 - px(7), gy + rnd.uniform(-1, 1))],
                   fill=mix(body, CREAM_D, 0.3), width=1)
    d.rectangle(box(x0 - px(2), FLOOR_Y - px(10), x1 + px(2), FLOOR_Y), fill=(48, 46, 40))


def crock(d, cx, base_y, w, h, body=(196, 188, 166), lid=True, seed=0):
    """A stoneware jar: bulged body, a band or two, and a lid with a knob."""
    rnd = random.Random(seed)
    # a soft contact shadow only: at full strength it read as a black pad stuck
    # under every jar on every shelf
    d.ellipse(box(cx - w * 0.44, base_y - px(1.4), cx + w * 0.44, base_y + px(1.4)),
              fill=(20, 16, 12, 44))
    x0, x1 = cx - w * 0.42, cx + w * 0.42
    top = base_y - h
    # straight sides and a shoulder, not a dome: a row of domes with knobs read
    # as grey hats sitting on the shelf instead of as storage
    d.rectangle(box(x0, top + h * 0.22, x1, base_y - px(1)), fill=body)
    d.pieslice(box(x0, top + h * 0.02, x1, top + h * 0.46), 180, 360, fill=body)
    d.line([(x0 + px(0.9), top + h * 0.26), (x0 + px(0.9), base_y - px(3))],
           fill=mix(body, (255, 250, 236), 0.42), width=max(1, int(px(1.0))))
    d.line([(x1 - px(1.4), top + h * 0.26), (x1 - px(1.4), base_y - px(3))],
           fill=mix(body, (54, 46, 34), 0.45), width=max(1, int(px(1.4))))
    for f in (0.46, 0.66):
        d.line([(x0, base_y - h * f), (x1, base_y - h * f)],
               fill=mix(body, (110, 96, 74), 0.35), width=max(1, int(px(0.6))))
        d.line([(x0, base_y - h * f + px(1)), (x1, base_y - h * f + px(1))],
               fill=mix(body, (246, 240, 222), 0.3), width=max(1, int(px(0.5))))
    d.rectangle(box(x0, base_y - h * 0.10, x1, base_y), fill=mix(body, (96, 86, 68), 0.3))
    if lid:
        lw = w * 0.47
        d.rectangle(box(cx - lw, top - px(2), cx + lw, top + h * 0.18),
                    fill=mix(body, (234, 228, 208), 0.3))
        d.line([(cx - lw, top - px(2)), (cx + lw, top - px(2))],
               fill=mix(body, (255, 252, 240), 0.45), width=max(1, int(px(0.8))))
        d.ellipse(box(cx - px(3), top - px(5), cx + px(3), top), fill=mix(body, (148, 136, 110), 0.4))
    _ = rnd


def bottle(d, cx, base_y, w, h, c):
    """A stoppered bottle or a tin: body, shoulder, and a lit left edge."""
    d.rounded_rectangle(box(cx - w / 2.0, base_y - h, cx + w / 2.0, base_y),
                        radius=max(1, int(px(1.2))), fill=mix(c, (24, 22, 18), 0.22))
    d.rectangle(box(cx - w * 0.17, base_y - h - px(4), cx + w * 0.17, base_y - h + px(1)),
                fill=mix(c, (240, 230, 198), 0.28))
    d.line([(cx - w * 0.34, base_y - h + px(2)), (cx - w * 0.34, base_y - px(1))],
           fill=mix(c, (248, 238, 210), 0.34), width=max(1, int(px(0.6))))
    d.line([(cx + w * 0.36, base_y - h + px(2)), (cx + w * 0.36, base_y - px(1))],
           fill=mix(c, (30, 26, 20), 0.4), width=max(1, int(px(0.6))))


def shelf(base, x0, x1, y0, seed, rows=2, gap=px(30)):
    """Open shelving of stoneware, tins and bottles, each shelf lit from below."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(seed)
    for r in range(rows):
        sy = y0 + r * gap
        d.rectangle(box(x0 - px(3), sy, x1 + px(3), sy + px(4)), fill=mix(WOOD, WOOD_L, 0.3))
        d.line([(x0 - px(3), sy), (x1 + px(3), sy)], fill=(228, 206, 162),
               width=max(1, int(px(0.6))))
        d.line([(x0 - px(3), sy + px(4)), (x1 + px(3), sy + px(4))],
               fill=(30, 22, 16), width=max(1, int(px(0.8))))
        x = x0 + px(5)
        while x < x1 - px(12):
            kind = rnd.random()
            if kind < 0.34:
                cw = rnd.uniform(px(9), px(14))
                ch = rnd.uniform(px(12), px(18))
                crock(d, x + cw / 2.0, sy, cw, ch,
                      mix((190, 182, 158), (150, 156, 146), rnd.random()), seed=int(x))
            elif kind < 0.72:
                bw = rnd.uniform(px(5), px(8))
                bh = rnd.uniform(px(10), px(17))
                bottle(d, x + bw / 2.0, sy, bw, bh,
                       rnd.choice(((72, 96, 58), (128, 88, 40), (96, 40, 34),
                                   (150, 128, 60), (176, 172, 158))))
            else:
                jw = rnd.uniform(px(10), px(15))
                jh = rnd.uniform(px(9), px(13))
                d.rounded_rectangle(box(x, sy - jh, x + jw, sy), radius=max(1, int(px(1.2))),
                                    fill=mix((206, 214, 198), (150, 168, 148), 0.4))
                d.ellipse(box(x + jw * 0.18, sy - jh * 0.8, x + jw * 0.82, sy - jh * 0.05),
                          fill=mix((188, 150, 92), (206, 176, 118), rnd.random()))
                d.rectangle(box(x + px(1), sy - jh - px(2), x + jw - px(1), sy - jh + px(1)),
                            fill=mix(BRASS, GOLD_D, 0.4))
            x += rnd.uniform(px(2), px(5)) + (cw if kind < 0.34 else
                                              bw if kind < 0.72 else jw)
        lamp(x0, sy + px(1), (x1 - x0) * 0.55, (255, 206, 146), 48)


# -------------------------------------------------------------------- the sink
def sink(base, x0, x1):
    """The sink counter under the window: basin, tap, and pans left to drain."""
    d = ImageDraw.Draw(base)
    top = px(150)
    slab(d, x0, top, x1, FLOOR_Y - px(8), mix(STEEL, STEEL_D, 0.55))
    slab(d, x0 - px(5), top, x1 + px(5), top + px(9), STEEL)
    d.line([(x0 - px(5), top + px(9)), (x1 + px(5), top + px(9))], fill=(30, 32, 32),
           width=max(1, int(px(1.1))))

    # the basin, cut into the counter, with a drain and a wet shine
    bx0, bx1 = x0 + (x1 - x0) * 0.16, x0 + (x1 - x0) * 0.72
    d.rectangle(box(bx0, top - px(1), bx1, top + px(7)), fill=(58, 62, 62))
    d.rectangle(box(bx0 + px(2), top, bx1 - px(2), top + px(5)), fill=(96, 102, 102))
    d.line([(bx0 + px(2), top), (bx1 - px(2), top)], fill=(38, 42, 42),
           width=max(1, int(px(0.8))))
    d.ellipse(box((bx0 + bx1) / 2.0 - px(2.5), top + px(2), (bx0 + bx1) / 2.0 + px(2.5),
                  top + px(4.5)), fill=(58, 62, 62))

    # the tap: a brass mixer with a swan neck and two cross handles
    tx = x0 + (x1 - x0) * 0.86
    d.rectangle(box(tx - px(3), top - px(14), tx + px(3), top), fill=mix(BRASS, GOLD_D, 0.3))
    d.arc(box(tx - px(22), top - px(30), tx + px(22), top - px(6)), 200, 350,
          fill=mix(BRASS, GOLD_L, 0.35), width=max(2, int(px(2.0))))
    d.line([(tx - px(22), top - px(17)), (tx - px(22), top - px(11))],
           fill=mix(BRASS, GOLD_L, 0.3), width=max(2, int(px(1.6))))
    for side in (-1, 1):
        hx = tx + side * px(9)
        d.line([(hx, top - px(11)), (hx, top - px(2))], fill=mix(BRASS, GOLD_D, 0.35),
               width=max(2, int(px(1.6))))
        d.line([(hx - px(4), top - px(12)), (hx + px(4), top - px(12))],
               fill=mix(BRASS, GOLD_L, 0.3), width=max(2, int(px(1.4))))
    for k, sx in enumerate((0.22, 0.40)):
        px0 = x0 + (x1 - x0) * sx
        d.ellipse(box(px0 - px(12), top - px(6), px0 + px(12), top + px(2.4)),
                  fill=(18, 18, 17, 90))
        d.ellipse(box(px0 - px(11), top - px(8), px0 + px(11), top + px(1)),
                  fill=mix(STEEL, STEEL_L, 0.2))
        d.arc(box(px0 - px(11), top - px(8), px0 + px(11), top + px(1)), 0, 360,
              fill=(224, 228, 224), width=max(1, int(px(0.7))))
        d.ellipse(box(px0 - px(7), top - px(14), px0 + px(7), top - px(8)),
                  fill=mix(STEEL, STEEL_D, 0.1))
        d.ellipse(box(px0 - px(3), top - px(17), px0 + px(3), top - px(14)),
                  fill=mix(STEEL, STEEL_L, 0.4))
        lamp(px0, top - px(8), px(60), (222, 232, 232), 40)

    # a colander and a soap bottle, then two cupboard doors below
    d.arc(box(x1 - px(26), top - px(14), x1 - px(6), top + px(1)), 180, 360,
          fill=mix(STEEL, STEEL_L, 0.25), width=max(2, int(px(1.4))))
    bottle(d, x1 - px(2), top - px(1), px(7), px(12), (188, 196, 186))
    for i in range(2):
        dx0 = x0 + i * (x1 - x0) / 2.0 + px(5)
        dx1 = x0 + (i + 1) * (x1 - x0) / 2.0 - px(5)
        d.rectangle(box(dx0, top + px(16), dx1, FLOOR_Y - px(18)),
                    fill=mix(STEEL, STEEL_D, 0.55))
        d.rectangle(box(dx0 + px(3), top + px(20), dx1 - px(3), FLOOR_Y - px(22)),
                    outline=mix(STEEL, STEEL_L, 0.22), width=max(1, int(px(0.6))))
        d.line([(dx0, top + px(16)), (dx1, top + px(16))], fill=(228, 232, 228),
               width=max(1, int(px(0.7))))
    d.line([(x0, FLOOR_Y - px(12)), (x1, FLOOR_Y - px(12))], fill=mix(STEEL, STEEL_L, 0.3),
           width=max(2, int(px(1.2))))
    lamp((x0 + x1) / 2.0, top, (x1 - x0) * 0.5, (230, 236, 234), 44)


def radiator(base, x0, x1):
    """A cast-iron column radiator, painted white, with its pipes and a valve."""
    d = ImageDraw.Draw(base)
    top, bot = px(148), FLOOR_Y - px(10)
    cols = 13
    w = (x1 - x0) / float(cols)
    for i in range(cols):
        cx0 = x0 + i * w
        c = mix((216, 214, 204), (170, 170, 162), 0.18 if i % 2 else 0.05)
        d.rounded_rectangle(box(cx0 + px(1), top, cx0 + w - px(1), bot),
                            radius=max(1, int(px(2))), fill=c)
        d.line([(cx0 + px(2), top + px(4)), (cx0 + px(2), bot - px(4))],
               fill=(246, 246, 240), width=max(1, int(px(0.7))))
        d.line([(cx0 + w - px(2), top + px(4)), (cx0 + w - px(2), bot - px(4))],
               fill=(120, 120, 114), width=max(1, int(px(0.7))))
    for yy in (top - px(4), bot):
        d.rectangle(box(x0 - px(2), yy, x1 + px(2), yy + px(5)), fill=(196, 194, 184))
        d.line([(x0 - px(2), yy), (x1 + px(2), yy)], fill=(244, 244, 238),
               width=max(1, int(px(0.6))))
    d.rectangle(box(x1 - px(2), top + px(6), x1 + px(5), top + px(16)),
                fill=mix(BRASS, GOLD_D, 0.35))
    d.ellipse(box(x1 + px(1), top + px(6), x1 + px(9), top + px(14)),
              fill=mix(BRASS, GOLD_L, 0.25))
    lamp((x0 + x1) / 2.0, bot, (x1 - x0) * 0.5, (232, 236, 234), 34)


# --------------------------------------------------------------------- the range
def range_cooker(base, cx, w=px(170)):
    """The range: steel front, oven door, three burners and the pans on them.

    The kitchen's working heart, and its strongest light after the window: the
    hood lamp throws warm light down over the burners and the tile behind them.
    """
    d = ImageDraw.Draw(base)
    x0, x1 = cx - w / 2.0, cx + w / 2.0
    top = px(150)

    slab(d, x0, top, x1, FLOOR_Y - px(4), mix(STEEL, STEEL_D, 0.2))
    # oven door: dark glass, a steel frame and a long bar handle
    dx0, dx1 = x0 + px(16), x1 - px(16)
    d.rectangle(box(dx0, top + px(30), dx1, FLOOR_Y - px(22)), fill=mix(STEEL, STEEL_L, 0.2))
    d.rectangle(box(dx0 + px(5), top + px(36), dx1 - px(5), FLOOR_Y - px(30)), fill=(28, 26, 24))
    d.line([(dx0 + px(5), top + px(40)), (dx1 - px(5), top + px(40))], fill=(58, 56, 52),
           width=max(1, int(px(0.8))))
    d.rectangle(box(dx0 - px(2), top + px(22), dx1 + px(2), top + px(28)),
                fill=mix(STEEL, STEEL_L, 0.35))
    d.line([(dx0 - px(2), top + px(22)), (dx1 + px(2), top + px(22))], fill=(236, 240, 236),
           width=max(1, int(px(0.8))))
    for i in range(4):                          # the control knobs
        kx = dx0 + px(10) + i * px(18)
        d.ellipse(box(kx - px(4), top + px(9), kx + px(4), top + px(17)),
                  fill=mix((44, 42, 40), STEEL, 0.3))
        d.line([(kx, top + px(9)), (kx, top + px(12))], fill=(226, 226, 222),
               width=max(1, int(px(0.8))))

    # the cooktop: cast iron over a steel deck, with its trivets
    d.rectangle(box(x0 - px(4), top - px(5), x1 + px(4), top + px(1)), fill=(52, 54, 54))
    d.line([(x0 - px(4), top - px(5)), (x1 + px(4), top - px(5))],
           fill=(160, 164, 162), width=max(1, int(px(0.8))))
    burners = ((0.22, px(34)), (0.52, px(30)), (0.80, px(26)))
    for fx, r in burners:
        bx = x0 + w * fx
        by = top - px(4)
        d.ellipse(box(bx - r, by - r * 0.42, bx + r, by + r * 0.42), fill=(38, 40, 40))
        for k in range(6):
            a = k * math.pi / 3.0
            d.line([(bx + math.cos(a) * r * 0.35, by + math.sin(a) * r * 0.15),
                    (bx + math.cos(a) * r * 0.92, by + math.sin(a) * r * 0.4)],
                   fill=(76, 78, 78), width=max(1, int(px(0.6))))
        lamp(bx, by, px(56), (232, 176, 120), 40)

    # a wok with oil and greens, a stock pot with a lid, and a small pan
    wx = x0 + w * 0.22
    d.polygon([(wx - px(34), top - px(6)), (wx + px(34), top - px(6)),
               (wx + px(22), top - px(26)), (wx - px(22), top - px(26))],
              fill=mix((54, 56, 56), STEEL_D, 0.3))
    d.ellipse(box(wx - px(34), top - px(11), wx + px(34), top - px(1)),
              fill=mix((58, 60, 60), STEEL, 0.18))
    d.ellipse(box(wx - px(30), top - px(10), wx + px(30), top - px(3)),
              fill=mix((104, 66, 28), (66, 40, 18), 0.35))
    d.arc(box(wx - px(34), top - px(11), wx + px(34), top - px(1)), 180, 360,
          fill=(222, 226, 222), width=max(2, int(px(1.6))))
    rnd = random.Random(4)
    for i in range(9):
        gx = wx + rnd.uniform(-px(22), px(22))
        gy = top - px(8) + rnd.uniform(-px(2), px(2))
        rr = rnd.uniform(px(3), px(7))
        d.ellipse(box(gx - rr, gy - rr * 0.5, gx + rr, gy + rr * 0.5),
                  fill=mix((92, 128, 58), (170, 196, 108), rnd.random()))
    d.line([(wx - px(34), top - px(6)), (wx + px(34), top - px(6))], fill=(228, 232, 228),
           width=max(1, int(px(1.0))))

    sx = x0 + w * 0.52
    d.rectangle(box(sx - px(20), top - px(30), sx + px(20), top - px(5)),
                fill=mix(STEEL, STEEL_L, 0.22))
    d.ellipse(box(sx - px(20), top - px(34), sx + px(20), top - px(26)),
              fill=mix(STEEL, STEEL_L, 0.35))
    d.ellipse(box(sx - px(5), top - px(38), sx + px(5), top - px(32)),
              fill=mix(BRASS, GOLD_D, 0.3))
    for k in (-1, 1):
        d.rectangle(box(sx + k * px(21) - px(2), top - px(26), sx + k * px(21) + px(2), top - px(20)),
                    fill=(46, 46, 44))
    d.line([(sx - px(20), top - px(30)), (sx - px(20), top - px(5))], fill=(240, 244, 240),
           width=max(1, int(px(1.0))))

    fx = x0 + w * 0.80
    d.polygon([(fx - px(18), top - px(4)), (fx + px(18), top - px(4)),
               (fx + px(13), top - px(16)), (fx - px(13), top - px(16))],
              fill=mix((62, 62, 60), STEEL_D, 0.2))
    d.ellipse(box(fx - px(18), top - px(8), fx + px(18), top - px(1)), fill=(44, 44, 42))
    d.line([(fx + px(18), top - px(6)), (fx + px(38), top - px(8))],
           fill=(58, 58, 56), width=max(2, int(px(2.4))))

    lamp(cx, top - px(14), px(230), (255, 198, 130), 128)
    lamp(cx, top + px(40), px(150), (255, 190, 124), 52)


def range_hood(base, cx, w=px(210)):
    """The extractor hood over the range, its chimney and the lamp under it."""
    d = ImageDraw.Draw(base)
    x0, x1 = cx - w / 2.0, cx + w / 2.0
    lip = px(112)

    d.polygon([(x0, lip), (x1, lip), (x1 - px(20), px(64)), (x0 + px(20), px(64))],
              fill=mix(STEEL, STEEL_D, 0.46))
    for i in range(7):
        t = i / 6.0
        yy = lip - px(3) - i * px(6)
        d.line([(x0 + (x1 - x0) * 0.05, yy), (x1 - (x1 - x0) * 0.05, yy)],
               fill=mix(STEEL, (24, 26, 26), 0.55), width=max(1, int(px(0.8))))
        d.line([(x0 + (x1 - x0) * 0.05, yy - px(1.6)),
                (x1 - (x1 - x0) * 0.05, yy - px(1.6))],
               fill=mix(STEEL, STEEL_L, 0.06 + 0.10 * (1 - t)),
               width=max(1, int(px(0.7))))
    d.polygon([(x0, lip), (x1, lip), (x1, lip + px(10)), (x0, lip + px(10))],
              fill=mix(STEEL, STEEL_L, 0.06))
    d.line([(x0, lip + px(10)), (x1, lip + px(10))], fill=(216, 220, 216),
           width=max(2, int(px(1.6))))
    d.line([(x0, lip), (x0, lip + px(10))], fill=(236, 240, 236), width=max(1, int(px(1.0))))
    d.line([(x1, lip), (x1, lip + px(10))], fill=(74, 76, 74), width=max(1, int(px(1.0))))
    # the underside, in shadow, with its filters and a warm lamp
    d.rectangle(box(x0 + px(6), lip + px(4), x1 - px(6), lip + px(9)), fill=(30, 30, 28))
    for i in range(11):
        fx = x0 + px(10) + i * (w - px(20)) / 10.0
        d.line([(fx, lip + px(4)), (fx, lip + px(9))], fill=(58, 58, 54),
               width=max(1, int(px(1.0))))
    lamp(cx, lip + px(12), px(200), (255, 200, 132), 120)

    # the chimney up into the ceiling, with a flange where it meets it
    d.rectangle(box(cx - px(30), WALL_TOP - px(4), cx + px(30), px(64)), fill=(62, 64, 62))
    d.line([(cx - px(30), px(64)), (cx - px(30), WALL_TOP - px(4))], fill=(150, 154, 150),
           width=max(1, int(px(1.2))))
    d.line([(cx + px(30), px(64)), (cx + px(30), WALL_TOP - px(4))], fill=(34, 34, 32),
           width=max(1, int(px(1.2))))
    for yy in (px(74), WALL_TOP - px(10)):
        d.rectangle(box(cx - px(34), yy, cx + px(34), yy + px(6)), fill=(78, 80, 78))
        d.line([(cx - px(34), yy), (cx + px(34), yy)], fill=(170, 174, 170),
               width=max(1, int(px(0.7))))


# ----------------------------------------------------------- rails and counters
def utensil_rail(base, x0, x1, y, seed):
    """A steel rail of hanging pans and cleavers, with cloths at one end."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(x0, y, x1, y + px(3)), fill=mix(STEEL, STEEL_L, 0.3))
    d.line([(x0, y), (x1, y)], fill=(242, 246, 242), width=max(1, int(px(0.6))))
    d.line([(x0, y + px(3)), (x1, y + px(3))], fill=(68, 70, 68),
           width=max(1, int(px(0.8))))
    for x in range(int(x0), int(x1), int(px(76))):
        d.rectangle(box(x - px(2), y - px(4), x + px(4), y), fill=(118, 122, 118))

    rnd = random.Random(seed)
    x = x0 + px(20)
    while x < x1 - px(26):
        d.arc(box(x - px(4), y + px(2), x + px(4), y + px(10)), 180, 360,
              fill=(154, 158, 154), width=max(1, int(px(0.7))))
        kind = rnd.random()
        hy = y + px(9)
        if kind < 0.26:                            # a cleaver
            bw, bh = px(15), px(22)
            d.polygon([(x - bw / 2.0, hy), (x + bw / 2.0, hy),
                       (x + bw / 2.0, hy + bh), (x - bw / 2.0 + px(3), hy + bh)],
                      fill=mix(STEEL, STEEL_L, 0.28))
            d.line([(x - bw / 2.0 + px(3), hy + bh), (x + bw / 2.0, hy + bh)],
                   fill=(246, 250, 246), width=max(1, int(px(0.8))))
            d.line([(x - bw / 2.0, hy), (x - bw / 2.0, hy + bh)],
                   fill=(240, 244, 240), width=max(1, int(px(0.7))))
            d.rectangle(box(x + px(1), hy - px(6), x + px(6), hy), fill=WOOD)
        elif kind < 0.55:                          # a ladle
            d.arc(box(x - px(7), hy, x + px(7), hy + px(16)), 0, 360,
                  fill=mix(STEEL, STEEL_L, 0.2), width=max(2, int(px(2.0))))
            d.line([(x, hy), (x + px(6), hy - px(4))], fill=(160, 164, 160),
                   width=max(1, int(px(1.4))))
            d.arc(box(x - px(5), hy + px(4), x + px(5), hy + px(13)), 0, 360,
                  fill=(60, 62, 60), width=max(1, int(px(0.6))))
        elif kind < 0.78:                          # a pan, hung by its handle
            d.polygon([(x - px(20), hy + px(4)), (x + px(14), hy + px(4)),
                       (x + px(16), hy + px(22)), (x - px(18), hy + px(22))],
                      fill=mix((48, 50, 50), STEEL_D, 0.2))
            d.line([(x - px(20), hy + px(4)), (x - px(18), hy + px(22))],
                   fill=(150, 154, 150), width=max(1, int(px(1.0))))
            d.line([(x - px(20), hy + px(4)), (x - px(18), hy + px(22))],
                   fill=(150, 154, 150), width=max(1, int(px(1.0))))
            d.line([(x - px(18), hy + px(22)), (x + px(16), hy + px(22))],
                   fill=(196, 200, 196), width=max(1, int(px(1.0))))
            d.line([(x + px(14), hy + px(4)), (x + px(22), hy - px(4))],
                   fill=(58, 58, 56), width=max(2, int(px(2.2))))
        else:                                      # a cloth left to dry
            cw = px(26)
            d.polygon([(x - cw / 2.0, hy), (x + cw / 2.0, hy),
                       (x + cw / 2.0 - px(3), hy + px(34)), (x - cw / 2.0 + px(4), hy + px(32))],
                      fill=(228, 224, 210))
            d.line([(x - cw / 2.0, hy), (x + cw / 2.0, hy)], fill=(248, 246, 238),
                   width=max(1, int(px(0.7))))
            for k in range(3):
                fx = x - cw / 2.0 + px(5) + k * px(7)
                d.line([(fx, hy + px(3)), (fx + px(1), hy + px(31))],
                       fill=(190, 186, 172), width=max(1, int(px(0.5))))
            d.line([(x - cw / 2.0 + px(4), hy + px(32)), (x + cw / 2.0 - px(3), hy + px(34))],
                   fill=(176, 172, 158), width=max(1, int(px(0.7))))
        x += rnd.uniform(px(30), px(50))
    lamp((x0 + x1) / 2.0, y + px(10), (x1 - x0) * 0.55, (255, 206, 150), 42)


def dumpling_tray(d, cx, cy, w):
    """A tray of dumplings, folded and pinched, the way they sit on the bench."""
    d.polygon([(cx - w / 2.0, cy), (cx + w / 2.0, cy),
               (cx + w * 0.42, cy + w * 0.22), (cx - w * 0.42, cy + w * 0.22)],
              fill=mix(STEEL, STEEL_L, 0.22))
    d.line([(cx - w / 2.0, cy), (cx + w / 2.0, cy)], fill=(238, 242, 238),
           width=max(1, int(px(0.7))))
    rows = 3
    for r in range(rows):
        for c in range(4):
            gx = cx - w * 0.34 + c * w * 0.23 + (w * 0.11 if r % 2 else 0)
            gy = cy + w * 0.06 + r * w * 0.055
            rr = w * 0.085
            d.ellipse(box(gx - rr, gy - rr * 0.5, gx + rr, gy + rr * 0.5),
                      fill=(232, 226, 206))
            d.arc(box(gx - rr, gy - rr * 0.7, gx + rr, gy + rr * 0.3), 190, 350,
                  fill=(198, 190, 168), width=max(1, int(px(0.4))))


def chrysanthemums(d, cx, cy, w, seed):
    """The basket of purple chrysanthemums the reference keeps on the bench."""
    rnd = random.Random(seed)
    d.polygon([(cx - w / 2.0, cy), (cx + w / 2.0, cy),
               (cx + w * 0.38, cy + w * 0.34), (cx - w * 0.38, cy + w * 0.34)],
              fill=mix((186, 158, 104), (140, 112, 66), 0.3))
    for i in range(4):
        d.line([(cx - w / 2.0 + i * w / 3.0, cy),
                (cx - w * 0.42 + i * w / 3.0, cy + w * 0.32)],
               fill=(120, 94, 54), width=max(1, int(px(0.6))))
    for i in range(7):
        fx = cx + rnd.uniform(-w * 0.34, w * 0.34)
        fy = cy - rnd.uniform(px(2), w * 0.30)
        rr = rnd.uniform(w * 0.10, w * 0.17)
        c = mix((142, 96, 156), (196, 168, 202), rnd.uniform(0.1, 0.7))
        d.ellipse(box(fx - rr, fy - rr * 0.9, fx + rr, fy + rr * 0.9), fill=c)
        d.arc(box(fx - rr, fy - rr * 0.9, fx + rr, fy + rr * 0.9), 0, 360,
              fill=mix(c, (255, 248, 255), 0.35), width=max(1, int(px(0.5))))
        d.ellipse(box(fx - rr * 0.24, fy - rr * 0.24, fx + rr * 0.24, fy + rr * 0.24),
                  fill=mix((228, 200, 96), (246, 232, 168), 0.4))
    for i in range(6):
        gx = cx + rnd.uniform(-w * 0.4, w * 0.4)
        gy = cy - rnd.uniform(px(1), w * 0.34)
        rr = w * 0.10
        d.ellipse(box(gx - rr, gy - rr * 0.5, gx + rr, gy + rr * 0.5),
                  fill=mix(GREEN, GREEN_L, rnd.random()))


def prep_counter(base, x0, x1, seed, top=px(150), shelf=True):
    """A steel prep table drawn up to the wall: plates, bowls, board, cleaver."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(seed)
    slab(d, x0, top, x1, FLOOR_Y - px(8), mix(STEEL, STEEL_D, 0.3))
    # marble top, because a kitchen's benches are stone, not steel
    d.rectangle(box(x0 - px(6), top, x1 + px(6), top + px(10)), fill=(206, 202, 190))
    for i in range(4):
        gx = x0 + (x1 - x0) * rnd.random()
        d.line([(gx, top + px(1)), (gx + rnd.uniform(-px(30), px(30)), top + px(9))],
               fill=(178, 174, 164), width=max(1, int(px(0.5))))
    d.line([(x0 - px(6), top), (x1 + px(6), top)], fill=(244, 242, 234),
           width=max(1, int(px(0.8))))
    d.line([(x0 - px(6), top + px(10)), (x1 + px(6), top + px(10))], fill=(70, 70, 66),
           width=max(1, int(px(1.0))))
    if shelf:
        # an open shelf under the bench, in shadow, with two crates slid into it:
        # the bowls that used to sit here read as white pills stuck on the front
        d.rectangle(box(x0 + px(8), top + px(12), x1 - px(8), FLOOR_Y - px(10)),
                    fill=mix(STEEL, (26, 28, 28), 0.70))
        d.line([(x0 + px(8), top + px(12)), (x1 - px(8), top + px(12))],
               fill=mix(STEEL, STEEL_L, 0.10), width=max(1, int(px(0.8))))
        for i in range(2):
            bx = x0 + px(14) + i * (x1 - x0) * 0.50
            cw0 = (x1 - x0) * 0.32
            d.rectangle(box(bx, top + px(22), bx + cw0, FLOOR_Y - px(14)),
                        fill=mix(WOOD, WOOD_D, 0.45))
            for k in range(2):
                d.line([(bx + px(2), top + px(28) + k * px(9)),
                        (bx + cw0 - px(2), top + px(28) + k * px(9))],
                       fill=mix(WOOD, WOOD_L, 0.2), width=max(1, int(px(0.5))))
            d.line([(bx, top + px(22)), (bx, FLOOR_Y - px(14))],
                   fill=mix(WOOD, WOOD_L, 0.3), width=max(1, int(px(0.7))))
    for i in range(2):
        lx = x0 + px(14) + i * (x1 - x0 - px(28))
        d.line([(lx, top + px(10)), (lx, FLOOR_Y - px(8))], fill=(120, 124, 120),
               width=max(1, int(px(1.0))))

    # stacked plates, bowls, jars and a teapot along the bench
    for s in range(2):
        sx = x0 + (x1 - x0) * (0.16 + 0.20 * s)
        for k in range(4):
            rr = px(13)
            d.ellipse(box(sx - rr, top - px(2) - k * px(2.4), sx + rr, top + px(1) - k * px(2.4)),
                      fill=mix(PORCELAIN, (196, 192, 176), 0.1 + 0.06 * k))
            d.arc(box(sx - rr, top - px(2) - k * px(2.4), sx + rr, top + px(1) - k * px(2.4)),
                  0, 360, fill=(214, 210, 194), width=max(1, int(px(0.4))))
    for k, bx in enumerate((0.44, 0.52)):
        cx0 = x0 + (x1 - x0) * bx
        d.ellipse(box(cx0 - px(11), top - px(9), cx0 + px(11), top + px(1)),
                  fill=mix(PORCELAIN, (206, 200, 182), 0.2))
        d.arc(box(cx0 - px(11), top - px(9), cx0 + px(11), top + px(1)), 180, 360,
              fill=(238, 234, 220), width=max(1, int(px(0.6))))
        d.ellipse(box(cx0 - px(8), top - px(11), cx0 + px(8), top - px(5)),
                  fill=(150, 108, 64))
    for k in range(3):
        bottle(d, x0 + (x1 - x0) * 0.62 + k * px(11), top - px(1), px(7),
               rnd.uniform(px(12), px(20)),
               rnd.choice(((96, 40, 34), (128, 88, 40), (72, 96, 58))))
    dumpling_tray(d, x0 + (x1 - x0) * 0.80, top - px(2), (x1 - x0) * 0.26)

    # a chopping block with a cleaver in it, at the left end of the bench
    bx = x0 + (x1 - x0) * 0.05
    d.rectangle(box(bx, top - px(9), bx + px(34), top), fill=mix((176, 142, 92), (128, 98, 58), 0.3))
    d.line([(bx, top - px(9)), (bx + px(34), top - px(9))], fill=(206, 176, 128),
           width=max(1, int(px(0.7))))
    d.polygon([(bx + px(10), top - px(9)), (bx + px(24), top - px(9)),
               (bx + px(24), top - px(30)), (bx + px(13), top - px(30))],
              fill=mix(STEEL, STEEL_L, 0.3))
    d.line([(bx + px(10), top - px(9)), (bx + px(10), top - px(30))], fill=(246, 250, 246),
           width=max(1, int(px(0.7))))
    d.rectangle(box(bx + px(12), top - px(36), bx + px(18), top - px(29)), fill=WOOD)
    lamp((x0 + x1) / 2.0, top - px(4), (x1 - x0) * 0.5, (255, 208, 154), 60)


def floor_crocks(base, cx, seed):
    """Stoneware and produce against the skirting: crocks, baskets, a rice sack."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(seed)
    base_y = FLOOR_Y - px(2)
    for i, (ox, w, h) in enumerate(((-px(38), px(34), px(46)), (px(2), px(44), px(60)),
                                    (px(46), px(30), px(40)))):
        crock(d, cx + ox, base_y, w, h,
              mix((190, 182, 158), (148, 156, 148), 0.2 + 0.3 * i), seed=seed + i)
    # a crate of vegetables and a paper sack of rice
    bx = cx + px(78)
    d.polygon([(bx - px(24), base_y - px(22)), (bx + px(24), base_y - px(22)),
               (bx + px(20), base_y), (bx - px(20), base_y)],
              fill=mix(WOOD, WOOD_D, 0.2))
    for k in range(3):
        for j in range(2):
            vx = bx - px(16) + k * px(14)
            vy = base_y - px(22) + j * px(8)
            rr = px(7)
            d.ellipse(box(vx - rr, vy - rr * 0.7, vx + rr, vy + rr * 0.5),
                      fill=mix(rnd.choice(((96, 132, 58), (172, 60, 40), (196, 132, 44))),
                               (60, 78, 40), 0.2))
    for k in range(4):
        d.line([(bx - px(24), base_y - px(22) + k * px(7)), (bx + px(24), base_y - px(22) + k * px(7))],
               fill=mix(WOOD, WOOD_L, 0.3), width=max(1, int(px(0.6))))
    sx = cx - px(96)
    d.polygon([(sx - px(20), base_y - px(30)), (sx + px(20), base_y - px(30)),
               (sx + px(24), base_y - px(6)), (sx - px(24), base_y - px(6))],
              fill=(214, 208, 188))
    d.line([(sx - px(20), base_y - px(30)), (sx + px(20), base_y - px(30))], fill=(238, 234, 218),
           width=max(1, int(px(0.7))))
    d.line([(sx - px(6), base_y - px(30)), (sx - px(2), base_y - px(6))], fill=(180, 174, 156),
           width=max(1, int(px(0.6))))
    lamp(cx, base_y - px(30), px(120), (255, 204, 146), 40)


def hanging_strings(base, cx, y0, seed):
    """Strings of dried chillies and garlic hanging from the beam."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(seed)
    for i, (ox, n) in enumerate(((-px(16), 7), (px(12), 6))):
        x = cx + ox
        d.line([(x, y0), (x + px(2), y0 + n * px(11))], fill=(96, 74, 44),
               width=max(1, int(px(0.6))))
        for k in range(n):
            y = y0 + px(6) + k * px(11)
            if i == 0:
                rr = px(4)
                d.polygon([(x - rr, y), (x + rr, y), (x + rr * 0.4, y + rr * 1.9),
                           (x - rr * 0.4, y + rr * 1.9)],
                          fill=mix((158, 44, 32), (196, 84, 52), rnd.random()))
            else:
                # a garlic bulb: fat in the middle, pinched to a stalk
                rr = px(6)
                d.ellipse(box(x - rr, y + px(1), x + rr, y + rr * 1.7),
                          fill=(228, 224, 210))
                d.polygon([(x - rr * 0.5, y + px(2)), (x + rr * 0.5, y + px(2)),
                           (x, y - px(3))], fill=(206, 200, 184))
                d.line([(x - rr * 0.55, y + rr * 0.9), (x + rr * 0.55, y + rr * 1.0)],
                       fill=(188, 182, 164), width=max(1, int(px(0.5))))


# ---------------------------------------------------------------- the swing door
def swing_door(base, cx):
    """The door back into the dining room: warm light, portholes, a push plate.

    The same doorway the dining room hangs its red curtain over, seen from the
    kitchen side - so the kitchen ends in the light the dining room begins in.
    """
    d = ImageDraw.Draw(base)
    half = px(58)
    top = px(78)

    d.rectangle(box(cx - half - px(9), top - px(9), cx + half + px(9), FLOOR_Y),
                fill=(70, 72, 70))
    d.rectangle(box(cx - half, top, cx + half, FLOOR_Y), fill=(52, 34, 22))
    for i in range(px(96)):                      # warm light from the other room
        tt = i / float(px(96))
        d.line([(cx - half, top + i), (cx + half, top + i)],
               fill=mix((104, 66, 36), (192, 138, 72), tt ** 0.8))

    for i, (lx0, lx1) in enumerate(((cx - half + px(2), cx - px(2)),
                                    (cx + px(2), cx + half - px(2)))):
        slab(d, lx0, top + px(4), lx1, FLOOR_Y - px(4), mix(STEEL, STEEL_D, 0.28))
        for k in range(3):                       # rivet lines down each leaf
            ry = top + px(22) + k * px(30)
            for j in range(3):
                rx = lx0 + px(6) + j * (lx1 - lx0 - px(12)) / 2.0
                d.ellipse(box(rx - px(1.6), ry - px(1.6), rx + px(1.6), ry + px(1.6)),
                          fill=(158, 162, 158))
        # the porthole, with the room's warm light coming through the glass
        hx = (lx0 + lx1) / 2.0
        hy = top + px(34)
        rr = px(17)
        d.ellipse(box(hx - rr - px(2), hy - rr - px(2), hx + rr + px(2), hy + rr + px(2)),
                  fill=(64, 66, 64))
        d.ellipse(box(hx - rr, hy - rr, hx + rr, hy + rr), fill=(232, 186, 122))
        d.arc(box(hx - rr, hy - rr, hx + rr, hy + rr), 0, 360, fill=(150, 154, 150),
              width=max(1, int(px(1.0))))
        d.line([(hx - rr * 0.7, hy - rr * 0.7), (hx + rr * 0.3, hy + rr * 0.3)],
               fill=(250, 232, 190), width=max(2, int(px(2.0))))
        lamp(hx, hy, px(60), (255, 210, 150), 70)
        d.rectangle(box(lx0 + px(2), FLOOR_Y - px(18), lx1 - px(2), FLOOR_Y - px(6)),
                    fill=mix(STEEL, STEEL_L, 0.28))
        d.line([(lx0 + px(2), FLOOR_Y - px(18)), (lx1 - px(2), FLOOR_Y - px(18))],
               fill=(232, 236, 232), width=max(1, int(px(0.8))))
    d.line([(cx - px(1), top + px(4)), (cx - px(1), FLOOR_Y - px(4))], fill=(28, 30, 30),
           width=max(1, int(px(1.2))))
    d.line([(cx + px(1), top + px(4)), (cx + px(1), FLOOR_Y - px(4))], fill=(28, 30, 30),
           width=max(1, int(px(1.2))))

    # a rail over the doors and an apron left on a hook beside them
    d.rectangle(box(cx - half - px(9), top - px(9), cx + half + px(9), top - px(4)),
                fill=mix(STEEL, STEEL_L, 0.3))
    d.line([(cx - half - px(9), top - px(9)), (cx + half + px(9), top - px(9))],
           fill=(238, 242, 238), width=max(1, int(px(0.7))))
    ax = cx + half + px(26)
    d.line([(ax, top + px(6)), (ax, top + px(14))], fill=(150, 154, 150),
           width=max(1, int(px(1.0))))
    d.polygon([(ax - px(11), top + px(14)), (ax + px(11), top + px(14)),
               (ax + px(13), top + px(58)), (ax - px(13), top + px(58))],
              fill=(216, 212, 198))
    d.line([(ax - px(11), top + px(14)), (ax + px(11), top + px(14))], fill=(240, 238, 230),
           width=max(1, int(px(0.7))))
    for k in range(3):
        d.line([(ax - px(11) + k * px(11), top + px(16)), (ax - px(11) + k * px(11), top + px(56))],
               fill=(190, 186, 172), width=max(1, int(px(0.5))))
    lamp(cx, FLOOR_Y - px(70), px(230), (255, 202, 134), 116)
    lamp(cx, FLOOR_Y + px(10), px(160), (255, 196, 128), 50)


def pendants(base):
    """Industrial pendant lamps on long cords, hung off the ceiling beam."""
    for i, x in enumerate((px(96), px(560), px(1720))):
        d = ImageDraw.Draw(base)
        cy = px(104)
        d.line([(x, WALL_TOP - px(8)), (x, cy - px(26))], fill=(38, 38, 36),
               width=max(1, int(px(0.7))))
        d.ellipse(box(x - px(4), WALL_TOP - px(12), x + px(4), WALL_TOP - px(5)),
                  fill=(58, 58, 56))
        d.polygon([(x - px(20), cy - px(26)), (x + px(20), cy - px(26)),
                   (x + px(13), cy - px(12)), (x - px(13), cy - px(12))],
                  fill=mix((72, 86, 74), (40, 52, 44), 0.3))
        d.polygon([(x - px(20), cy - px(26)), (x + px(20), cy - px(26)),
                   (x + px(18), cy - px(29)), (x - px(18), cy - px(29))],
                  fill=mix((96, 112, 96), (60, 74, 62), 0.2))
        d.ellipse(box(x - px(13), cy - px(14), x + px(13), cy - px(8)),
                  fill=(244, 238, 216))
        d.ellipse(box(x - px(7), cy - px(13), x + px(7), cy - px(7)),
                  fill=(255, 246, 214))
        for k in range(3):
            d.line([(x - px(12) + k * px(9), cy - px(8)), (x - px(10) + k * px(9), cy - px(4))],
                   fill=(255, 226, 168, 120 - k * 30), width=1)
        lamp(x, cy - px(6), px(180), (255, 204, 144), 128)
        lamp(x, FLOOR_Y + px(30), px(120), (255, 198, 138), 30)
        _ = i


# --------------------------------------------------------------------- the floor
def floor(base):
    """White square tile in perspective, grout, a drain, and wet reflections.

    Laid so the joints run back to the centre of the room, the way the tiles in
    the reference converge on the drain, with the squares growing as they come
    towards the camera.
    """
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, FLOOR_Y, W, H), fill=FL_GRID)
    rnd = random.Random(13)
    y = FLOOR_Y
    row = 0
    while y < H:
        # square tiles, not paving bricks: the row grows with its distance from
        # the wall, so what the camera sees is a square getting bigger towards
        # it. Wide, flat tiles read as a brick road under the fighters.
        hgt = int(px(10) + row * px(3.1))
        tw = int(px(10) * (1 + row * 0.30))
        x = (CX % tw) - tw
        col = 0
        while x < W:
            light = (row + col) % 2 == 0
            c = tint(tuple(int(v * (0.97 + 0.06 * rnd.random()))
                           for v in (FL_L if light else FL_D)), rnd, 0.03)
            d.rectangle(box(x + px(0.9), y + px(0.9), x + tw - px(0.9), y + hgt - px(0.9)),
                        fill=c)
            d.line([(x + px(1.2), y + px(1.2)), (x + tw - px(1.2), y + px(1.2))],
                   fill=mix(c, (255, 250, 232), 0.24 if light else 0.12),
                   width=max(1, int(px(0.5))))
            d.line([(x + px(1.2), y + hgt - px(1.2)), (x + tw - px(1.2), y + hgt - px(1.2))],
                   fill=mix(c, (16, 14, 11), 0.40), width=max(1, int(px(0.6))))
            d.line([(x + px(1.2), y + px(1.2)), (x + px(1.2), y + hgt - px(1.2))],
                   fill=mix(c, (18, 16, 13), 0.26), width=max(1, int(px(0.5))))
            if rnd.random() < 0.15:                  # wear and a wet scuff
                sx = x + rnd.uniform(px(3), max(px(4), tw - px(3)))
                sy = y + rnd.uniform(px(2), max(px(3), hgt - px(3)))
                d.line([(sx, sy), (sx + rnd.uniform(-px(6), px(6)),
                                   sy + rnd.uniform(px(1), px(4)))],
                       fill=mix(c, (44, 40, 34), 0.30), width=max(1, int(px(0.4))))
            x += tw
            col += 1
        y += hgt
        row += 1

    # the drain at the centre of the kitchen, and a couple of puddles
    dx, dy = CX, FLOOR_Y + px(58)
    dw, dh = px(48), px(17)
    d.polygon([(dx - dw / 2.0, dy - dh / 2.0), (dx + dw / 2.0, dy - dh / 2.0),
               (dx + dw / 2.0 - px(6), dy + dh / 2.0), (dx - dw / 2.0 + px(6), dy + dh / 2.0)],
              fill=mix(STEEL, STEEL_D, 0.35))
    for k in range(7):
        sx = dx - dw * 0.36 + k * dw * 0.12
        d.line([(sx, dy - dh * 0.34), (sx + px(2), dy + dh * 0.34)], fill=(38, 38, 36),
               width=max(1, int(px(1.2))))
    d.line([(dx - dw / 2.0, dy - dh / 2.0), (dx + dw / 2.0, dy - dh / 2.0)],
           fill=(196, 200, 196), width=max(1, int(px(0.8))))
    d.ellipse(box(dx - px(9), dy - px(4), dx + px(9), dy + px(3)), fill=(120, 110, 92))

    puddle = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(puddle)
    for cx, cy, w, h in ((px(240), FLOOR_Y + px(30), px(120), px(26)),
                         (px(900), FLOOR_Y + px(74), px(180), px(34)),
                         (px(1480), FLOOR_Y + px(40), px(140), px(28))):
        pd.ellipse(box(cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0),
                   fill=(96, 104, 104, 40))
    base.alpha_composite(puddle.filter(ImageFilter.GaussianBlur(px(6))))

    # the lamps and the window laid on the wet floor, running towards the camera
    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    for x in (px(240), px(700), px(1180), px(1640)):
        sd.polygon([(x - px(30), FLOOR_Y), (x + px(30), FLOOR_Y),
                    (x + px(74), H), (x - px(74), H)], fill=(255, 232, 190, 26))
    for x in range(0, W, px(110)):
        sd.line([(x, FLOOR_Y), (x + px(30), H)], fill=(255, 240, 214, 13),
                width=max(2, int(px(4))))
    base.alpha_composite(sheen.filter(ImageFilter.GaussianBlur(px(9))))


# ------------------------------------------------------------------ furniture
def chair(base, cx, base_y, w, seed):
    """The dining room's red lacquered chair, carried through into the kitchen."""
    d = ImageDraw.Draw(base)
    h = w * 1.45
    seat_y = base_y - h * 0.34
    frame = (134, 44, 36)
    frame_d = (60, 20, 16)

    d.ellipse(box(cx - w * 0.62, base_y - px(5), cx + w * 0.62, base_y + px(6)),
              fill=(16, 11, 7, 130))
    for side in (-1, 1):
        d.line([(cx + side * w * 0.34, seat_y), (cx + side * w * 0.44, base_y)],
               fill=frame_d, width=max(2, int(px(2.4))))
        d.line([(cx + side * w * 0.34 - px(1), seat_y),
                (cx + side * w * 0.44 - px(1), base_y)],
               fill=mix(frame, GOLD_L, 0.35), width=max(1, int(px(0.8))))
    d.polygon([(cx - w * 0.54, seat_y - px(5)), (cx + w * 0.54, seat_y - px(5)),
               (cx + w * 0.46, seat_y + px(5)), (cx - w * 0.46, seat_y + px(5))],
              fill=mix(RED, RED_L, 0.22))
    d.line([(cx - w * 0.54, seat_y - px(5)), (cx + w * 0.54, seat_y - px(5))],
           fill=mix(GOLD_L, (250, 232, 180), 0.3), width=max(1, int(px(0.8))))
    d.line([(cx - w * 0.46, seat_y + px(5)), (cx + w * 0.46, seat_y + px(5))],
           fill=(26, 18, 12), width=max(1, int(px(1.0))))

    top_y = seat_y - h * 0.74
    for side in (-1, 1):
        d.line([(cx + side * w * 0.50, seat_y), (cx + side * w * 0.54, top_y)],
               fill=frame_d, width=max(2, int(px(3.2))))
        d.line([(cx + side * w * 0.50 - px(1.4), seat_y),
                (cx + side * w * 0.54 - px(1.4), top_y)],
               fill=mix(frame, GOLD_L, 0.38), width=max(1, int(px(1.0))))
    d.rectangle(box(cx - w * 0.58, top_y, cx + w * 0.62, top_y + px(5)), fill=frame)
    d.line([(cx - w * 0.58, top_y), (cx + w * 0.62, top_y)],
           fill=mix(GOLD_L, (252, 236, 190), 0.3), width=max(1, int(px(0.9))))
    for k in range(3):
        sx = cx - w * 0.42 + k * w * 0.42
        d.rectangle(box(sx - px(2), top_y + px(6), sx + px(2), seat_y - px(3)), fill=frame)
        d.line([(sx - px(2), top_y + px(6)), (sx - px(2), seat_y - px(3))],
               fill=mix(frame, GOLD, 0.45), width=max(1, int(px(0.7))))
        d.line([(sx + px(2), top_y + px(6)), (sx + px(2), seat_y - px(3))],
               fill=frame_d, width=max(1, int(px(0.9))))
    mid_y = top_y + (seat_y - top_y) * 0.5
    d.rectangle(box(cx - w * 0.50, mid_y, cx + w * 0.52, mid_y + px(4)),
                fill=mix(RED, RED_L, 0.3))
    mr = w * 0.10
    d.ellipse(box(cx - mr, mid_y - mr * 0.6, cx + mr, mid_y + mr * 1.2),
              fill=mix(GOLD, GOLD_D, 0.25))
    d.arc(box(cx - mr, mid_y - mr * 0.6, cx + mr, mid_y + mr * 1.2), 0, 360,
          fill=mix(GOLD_L, (252, 236, 190), 0.3), width=max(1, int(px(0.7))))
    for k in range(2):
        rr = mr * (0.62 - 0.2 * k)
        d.arc(box(cx - rr, mid_y + mr * 0.3 - rr * 0.7,
                  cx + rr, mid_y + mr * 0.3 + rr * 0.7),
              200 + k * 40, 200 + k * 40 + 250, fill=mix(GOLD_D, RED, 0.35),
              width=max(1, int(px(0.7))))
    _ = seed


def wood_table(base, cx, base_y, w, seed):
    """The kitchen's own table: dark red-brown wood, plates still on it."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(seed)
    half = w / 2.0
    top_y = base_y - w * 0.26
    body = (112, 46, 32)
    depth = w * 0.17                      # how much of the top the camera sees

    d.ellipse(box(cx - half * 1.08, base_y - px(7), cx + half * 1.08, base_y + px(9)),
              fill=(18, 12, 8, 130))
    for side in (-1, 1):
        # the back legs, tucked in and shaded, then the front pair
        blx = cx + side * half * 0.84
        d.line([(blx, top_y + px(4)), (blx + side * px(3), base_y - px(3))],
               fill=mix(body, (44, 16, 10), 0.6), width=max(2, int(px(2.4))))
        lx = cx + side * half * 0.74
        d.line([(lx, top_y + px(4)), (lx + side * px(5), base_y)],
               fill=mix(body, (46, 18, 12), 0.45), width=max(2, int(px(3.2))))
        d.line([(lx - px(2), top_y + px(4)), (lx + side * px(5) - px(2), base_y)],
               fill=mix(body, (196, 112, 76), 0.32), width=max(1, int(px(1.0))))
    # a shallow apron under the top, not a box down to the floor: the first pass
    # drew the apron the whole way down and the table read as a red chest
    d.polygon([(cx - half, top_y + px(2)), (cx + half, top_y + px(2)),
               (cx + half, top_y + px(9)), (cx - half, top_y + px(9))],
              fill=mix(body, (60, 24, 16), 0.35))
    # the top itself, seen from slightly above: a parallelogram with real depth,
    # so the table reads as a table and not as a red bench
    d.polygon([(cx - half * 0.96, top_y - depth), (cx + half * 0.96, top_y - depth),
               (cx + half, top_y + px(2)), (cx - half, top_y + px(2))],
              fill=mix(body, (172, 88, 56), 0.26))
    for i in range(6):
        gy = top_y - depth * (0.84 - 0.16 * i)
        d.line([(cx - half * 0.9, gy), (cx + half * 0.9, gy + rnd.uniform(-1, 1))],
               fill=mix(body, (74, 28, 18), 0.3), width=max(1, int(px(0.5))))
    d.line([(cx - half * 0.96, top_y - depth), (cx + half * 0.96, top_y - depth)],
           fill=mix((206, 142, 104), body, 0.3), width=max(1, int(px(1.0))))
    d.line([(cx - half, top_y + px(2)), (cx + half, top_y + px(2))],
           fill=(26, 12, 8), width=max(1, int(px(1.2))))

    # laid for a meal: plates, bowls, a teapot and a mat of chopsticks
    ty = top_y - depth * 0.55
    for k in range(3):
        sx = cx - half * 0.56 + k * half * 0.52
        rr = w * 0.15
        d.ellipse(box(sx - rr, ty - rr * 0.42, sx + rr, ty + rr * 0.42),
                  fill=mix(PORCELAIN, (206, 200, 184), 0.15))
        d.ellipse(box(sx - rr * 0.8, ty - rr * 0.32, sx + rr * 0.8, ty + rr * 0.32),
                  fill=(240, 236, 222))
        d.ellipse(box(sx - rr * 0.4, ty - rr * 0.18, sx + rr * 0.4, ty + rr * 0.2),
                  fill=mix(rnd.choice(((198, 118, 68), (128, 146, 92), (206, 168, 88))),
                           (226, 220, 200), 0.2))
    mx = cx + half * 0.16
    d.polygon([(mx - px(20), ty + px(6)), (mx + px(20), ty + px(6)),
               (mx + px(24), ty - px(8)), (mx - px(24), ty - px(8))],
              fill=mix((198, 174, 120), (150, 126, 78), 0.3))
    for k in range(7):
        gx = mx - px(22) + k * px(7)
        d.line([(gx, ty + px(5)), (gx + px(3), ty - px(7))], fill=(176, 152, 100),
               width=max(1, int(px(0.6))))
    for k in range(2):
        d.line([(mx - px(14), ty + px(9) + k * px(2)), (mx + px(18), ty + px(8) + k * px(2))],
               fill=(206, 178, 128), width=max(1, int(px(0.8))))
    tx = cx - half * 0.78
    d.ellipse(box(tx - px(11), ty - px(9), tx + px(11), ty + px(3)),
              fill=mix((196, 188, 170), (150, 144, 128), 0.3))
    d.arc(box(tx - px(11), ty - px(9), tx + px(11), ty + px(3)), 0, 360,
          fill=(226, 220, 204), width=max(1, int(px(0.6))))
    d.line([(tx + px(11), ty - px(3)), (tx + px(20), ty - px(7))], fill=(160, 154, 138),
           width=max(2, int(px(1.6))))


def table_bay(base, cx, seed, r=px(52)):
    """The kitchen table drawn up to the wall, with its chairs behind and beside."""
    base_y = FLOOR_Y - px(2)
    chair(base, cx - r * 1.5, base_y - px(3), r * 0.62, seed + 1)
    chair(base, cx + r * 1.5, base_y - px(3), r * 0.62, seed + 2)
    chair(base, cx - r * 0.55, base_y - px(6), r * 0.56, seed + 3)
    wood_table(base, cx, base_y, r * 1.9, seed)


# ---------------------------------------------------------------------- the air
def steam(base, cx, cy, w, h, seed, alpha=78):
    """A plume of steam, soft enough to read as heat rather than as paint."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(seed)
    for i in range(16):
        t = i / 15.0
        sx = cx + rnd.uniform(-w * 0.30, w * 0.30) + math.sin(t * 3.4 + seed) * w * 0.22
        sy = cy - h * t
        r = w * (0.09 + 0.20 * t)
        d.ellipse(box(sx - r, sy - r * 0.72, sx + r, sy + r * 0.72),
                  fill=(240, 236, 226, int(alpha * (1 - 0.65 * t))))
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(px(7))))


def foreground():
    """The camera's own edge of the room: steam drifting across, dust in the light."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(53)
    for i in range(px(40)):
        a = int(150 * (1 - i / float(px(40))) ** 1.7)
        d.line([(0, H - i), (W, H - i)], fill=(20, 18, 15, a))
    for k in range(5):
        cx = px(300) + k * px(360)
        for i in range(12):
            t = i / 11.0
            sx = cx + rnd.uniform(-px(50), px(50)) + math.sin(t * 2.6 + k) * px(60)
            sy = H - px(20) - t * px(120)
            r = px(22) * (0.5 + 0.9 * t)
            d.ellipse(box(sx - r, sy - r * 0.5, sx + r, sy + r * 0.5),
                      fill=(232, 228, 218, int(34 * (1 - 0.5 * t))))
    for _ in range(110):
        x = rnd.uniform(0, W)
        y = H - rnd.uniform(px(10), px(150))
        r = rnd.uniform(px(1), px(3))
        d.ellipse(box(x - r, y - r, x + r, y + r),
                  fill=(255, 220, 168, rnd.randint(22, 66)))
    return fg.filter(ImageFilter.GaussianBlur(px(1.6)))


# -------------------------------------------------------------------- the arena
def paint():
    LIGHTS.clear()
    base = hd.blank([(0, (18, 18, 16)), (WALL_TOP, (46, 46, 42)),
                     (RAIL, (54, 56, 54)), (FLOOR_Y, (62, 60, 54)),
                     (H, (34, 32, 28))])

    ceiling(base)
    tile_wall(base)
    dado(base)
    d = ImageDraw.Draw(base)

    # the far end: a tall pantry, and the window over the sink
    cabinet(d, px(40), px(150), px(92), 21, doors=2)
    for i, ox in enumerate((px(22), px(62), px(104))):
        crock(d, px(40) + ox, px(92), px(30), px(22),
              mix((192, 184, 160), (146, 154, 146), 0.2 * i), seed=200 + i)
    window(base, px(240))
    sink(base, px(160), px(320))

    # crockery on the wall, over the radiator
    shelf(base, px(340), px(432), px(146), 23, rows=3, gap=-px(34))
    radiator(base, px(346), px(414))

    # cupboards and their shelf, then the range under its hood
    cabinet(d, px(620), px(740), px(150), 24, doors=3)
    for i, ox in enumerate((px(24), px(66), px(108))):
        crock(d, px(620) + ox, px(150), px(28), px(20),
              mix((190, 182, 158), (150, 158, 150), 0.25 * i), seed=210 + i)
    shelf(base, px(626), px(734), px(140), 25, rows=2, gap=-px(34))
    range_hood(base, px(850))
    range_cooker(base, px(850))

    # the benches: plates, bowls, dumplings, a board and its cleaver
    utensil_rail(base, px(985), px(1130), px(118), 26)
    prep_counter(base, px(985), px(1130), 27)
    chrysanthemums(ImageDraw.Draw(base), px(1080), px(146), px(54), 28)
    cabinet(d, px(1140), px(1215), px(150), 29, doors=1)
    shelf(base, px(1140), px(1215), px(140), 30, rows=2, gap=-px(34))
    d = ImageDraw.Draw(base)
    d.rounded_rectangle(box(px(1152), px(126), px(1202), px(150)), radius=int(px(3)),
                        fill=mix(PORCELAIN, (176, 176, 164), 0.25))
    d.ellipse(box(px(1160), px(122), px(1194), px(132)), fill=mix(STEEL, STEEL_L, 0.3))
    d.line([(px(1152), px(126)), (px(1202), px(126))], fill=(246, 242, 228),
           width=max(1, int(px(0.8))))
    utensil_rail(base, px(1225), px(1385), px(126), 31)
    prep_counter(base, px(1225), px(1385), 32, top=px(148))

    # the door back into the dining room, and the dry store beside it
    swing_door(base, px(1470))
    shelf(base, px(1560), px(1690), px(146), 33, rows=3, gap=-px(34))
    floor_crocks(base, px(1730), 34)

    hanging_strings(base, px(606), px(46), 35)
    hanging_strings(base, px(1552), px(46), 36)
    pendants(base)

    floor(base)
    table_bay(base, px(500), 41)

    # the wall is white glazed tile, so the work lamps are held back: at full
    # strength every pool blew the tile to paper and the room read as a beige
    # wash with a white slab where the hood should be
    base = hd.shade(base, [(hd.light(cx, cy, r, col, int(peak * 0.55)),
                            max(8, int(r * 0.34)), 1.0)
                           for cx, cy, r, col, peak in LIGHTS])
    steam(base, px(850), px(148), px(90), px(96), 51)
    steam(base, px(1010), px(140), px(60), px(70), 52, alpha=60)
    steam(base, px(1340), px(140), px(70), px(80), 53, alpha=64)
    base = art.vignette(base, 0.42)
    base = art.grain(base, 3, seed=61)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


# @@SECTION@@


def main():
    hd.STAGES["dragon_kitchen"] = (
        "Dragon of the Black Pool Restaurant Kitchen", paint)
    hd.build("dragon_kitchen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
