"""The Upside Down: the sewer under Chinatown (4000x960 canvas, 1280x960).

Painted from the reference art. What has to read on screen:

  * a brick sewer vault, not a cave: courses, pilasters, a ribbed brick roof
  * iron pipes running the walls, with flanges, valves and drips
  * a steel sump sunk into the floor - the water is grey metal, not green -
    with a round green platform at the bottom of it glowing up through the water
  * a ladder on the far left wall and a curved stone stair climbing away on the
    far right, both lit by gratings in the ceiling
  * a dead tree fallen across the left of the floor, planks bridging the
    channel on the right: the two things fighters walk across
  * a tunnel in the back wall with a dragon in it, hidden except for its eyes

Light direction is the thing to keep straight. Every green source is a grating
in the roof, so the shafts fall downwards and the metal reflects them. Nothing
glows up out of the floor except the round platform under the water, and that
light stays inside the tank.

Run:  python3 tools/stage_upside_down.py     (part of tools/build_all.py)
"""

from __future__ import annotations

import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import stages_hd as hd

W, H = hd.W, hd.H
CX, FLOOR_Y, px = hd.CX, hd.FLOOR_Y, hd.px

ROOF = px(34)                     # underside of the brick vault
GREEN = (92, 224, 148)
BRICK = (94, 84, 74)
MORTAR = (42, 38, 34)
STEEL = (122, 134, 144)
STEEL_LIT = (198, 210, 220)
WATER = (74, 84, 94)

# Where each feature sits. Kept together so the composition can be re-framed
# without hunting through the painting code.
LADDER_X = CX - px(150)
STAIR_TOP, STAIR_BOT = CX + px(260), CX + px(120)
SUMP_CX, SUMP_CY = CX - px(40), FLOOR_Y + px(10)
TUNNEL_CX = CX + px(60)
TREE_CX = CX - px(150)
PLANK_CX = CX + px(95)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ------------------------------------------------------------------- masonry
def brick_wall(base):
    """Damp brick courses, pilasters and moss - a built sewer, not a cave."""
    rnd = random.Random(23)
    d = ImageDraw.Draw(base)
    d.rectangle([0, 0, W, FLOOR_Y], fill=(56, 52, 50))
    row_h = px(9)
    for row, y in enumerate(range(int(ROOF - px(6)), int(FLOOR_Y), row_h)):
        offset = (row % 2) * px(11)
        for x in range(-px(22) + offset, W, px(22)):
            tone = rnd.randint(-8, 10)
            col = mix(BRICK, (78, 68, 58), rnd.random() * 0.5)
            col = tuple(max(0, min(255, c + tone)) for c in col)
            d.rectangle([x, y, x + px(21), y + row_h - px(1)], fill=col)
            d.line([(x, y + row_h - px(1)), (x + px(21), y + row_h - px(1))],
                   fill=MORTAR, width=1)
    # pilasters every 150 arcade units, with a lit edge
    for x in range(-px(20), W, px(150)):
        d.rectangle([x, ROOF - px(8), x + px(26), FLOOR_Y], fill=(78, 70, 62))
        d.line([(x, ROOF - px(8)), (x, FLOOR_Y)], fill=(96, 88, 78), width=max(1, px(1)))
        d.line([(x + px(26), ROOF - px(8)), (x + px(26), FLOOR_Y)],
               fill=(18, 17, 16), width=max(1, px(1.5)))
        for y in range(int(ROOF), int(FLOOR_Y), px(46)):
            d.rectangle([x + px(4), y, x + px(22), y + px(9)], fill=(52, 48, 44))
    # damp: vertical streaks and moss gathering at the skirting
    damp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(damp)
    for _ in range(150):
        x = rnd.randint(0, W)
        y = rnd.randint(int(ROOF), int(FLOOR_Y - px(30)))
        dd.rectangle([x, y, x + rnd.randint(int(px(3)), int(px(12))),
                      y + rnd.randint(int(px(40)), int(px(230)))],
                     fill=(18, 26, 24, rnd.randint(12, 34)))
    for _ in range(900):
        x = rnd.randint(0, W)
        y = rnd.randint(int(FLOOR_Y - px(90)), int(FLOOR_Y))
        r = rnd.randint(int(px(2)), int(px(9)))
        dd.ellipse([x, y, x + r, y + r * 0.6],
                   fill=(38, 62, 32, rnd.randint(16, 76)))
    base.alpha_composite(damp.filter(ImageFilter.GaussianBlur(px(2))))


def ceiling_vault(base):
    """Brick barrel roof with ribs and the gratings the light comes through."""
    rnd = random.Random(11)
    d = ImageDraw.Draw(base)
    d.rectangle([0, 0, W, ROOF], fill=(22, 21, 21))
    for i in range(9):                       # ribs receding into the dark
        y = int(ROOF - px(4) - i * px(4.2))
        tone = 40 - i * 3
        d.line([(0, y), (W, y)], fill=(max(6, tone),) * 3, width=max(1, px(1)))
    for _ in range(1400):                    # pitted brick
        x = rnd.randint(0, W)
        y = rnd.randint(0, int(ROOF))
        r = rnd.randint(1, int(px(2)))
        d.ellipse([x, y, x + r, y + r * 0.7],
                  fill=mix((16, 15, 15), (44, 38, 32), rnd.random()))
    d.line([(0, ROOF), (W, ROOF)], fill=(72, 64, 54), width=max(1, px(2)))
    d.line([(0, ROOF + px(2)), (W, ROOF + px(2))], fill=(14, 13, 13),
           width=max(1, px(2)))


def grating(base, cx, top=px(6), half=px(26), depth=px(14)):
    """Iron grate set into the roof: the mouth of every light shaft."""
    d = ImageDraw.Draw(base)
    d.rectangle([cx - half, top, cx + half, top + depth], fill=(12, 14, 13))
    d.rectangle([cx - half, top, cx + half, top + depth], outline=(58, 60, 56),
                width=max(1, px(1)))
    for x in range(int(cx - half), int(cx + half), px(7)):
        d.line([(x, top), (x, top + depth)], fill=(40, 42, 40), width=px(2))


# ------------------------------------------------------------------- plumbing
def niches(base):
    """Arched recesses along the wall so it does not read as flat brick."""
    for cx in (CX - px(470), CX - px(210), CX + px(340), CX + px(520)):
        top = FLOOR_Y - px(118)
        half = px(34)
        d = ImageDraw.Draw(base)
        d.rectangle([cx - half, top + px(18), cx + half, FLOOR_Y - px(6)],
                    fill=(26, 25, 25))
        d.pieslice([cx - half, top, cx + half, top + px(40)], 180, 360,
                   fill=(26, 25, 25))
        d.arc([cx - half, top, cx + half, top + px(40)], 180, 360,
              fill=(92, 82, 70), width=max(1, px(2)))
        for x in (cx - half, cx + half):
            d.line([(x, top + px(18)), (x, FLOOR_Y - px(6))],
                   fill=(92, 82, 70), width=max(1, px(2)))


def pipes(base):
    """Runs of iron pipe with flanges, valves and the drips under them."""
    rnd = random.Random(37)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    runs = ((px(62), px(4)), (px(116), px(3)), (px(170), px(2)))
    for y, thick in runs:
        d.rectangle([0, y, W, y + thick], fill=(84, 92, 100, 255))
        d.line([(0, y + 1), (W, y + 1)], fill=(158, 172, 182, 235), width=max(1, px(1)))
        d.line([(0, y + thick - 1), (W, y + thick - 1)], fill=(26, 28, 30, 255),
               width=max(1, px(1)))
        for x in range(int(px(40)), W, px(96)):
            d.rectangle([x, y - px(3), x + px(6), y + thick + px(3)],
                        fill=(84, 92, 100, 255))
            d.line([(x, y - px(3)), (x, y + thick + px(3))],
                   fill=(146, 158, 168, 210), width=max(1, px(1)))
        for x in range(int(px(72)), W, px(150)):
            r = px(9)
            d.ellipse([x - r, y - r, x + r, y + r], outline=(96, 104, 112, 255),
                      width=max(1, px(2)))
            d.line([(x - r, y), (x + r, y)], fill=(96, 104, 112, 255), width=px(2))
            d.line([(x, y - r), (x, y + r)], fill=(96, 104, 112, 255), width=px(2))
    # brackets and drips
    for x in range(int(px(20)), W, px(72)):
        d.rectangle([x, px(58), x + px(4), px(186)], fill=(30, 32, 34, 210))
    for _ in range(90):
        x = rnd.randint(0, W)
        y = rnd.choice(runs)[0] + px(6)
        ln = rnd.randint(int(px(6)), int(px(34)))
        d.line([(x, y), (x, y + ln)], fill=(150, 190, 170, rnd.randint(18, 54)),
               width=max(1, px(1)))
    base.alpha_composite(layer)
    return base


def ladder(base):
    """Steel ladder on the far left wall, standing in its own shaft of light."""
    d = ImageDraw.Draw(base)
    top, bot = px(24), FLOOR_Y + px(4)
    # the recess it is bolted into
    d.rectangle([LADDER_X - px(30), top, LADDER_X + px(30), bot], fill=(18, 18, 19))
    d.rectangle([LADDER_X - px(30), top, LADDER_X + px(30), bot],
                outline=(44, 42, 40), width=max(1, px(1)))
    for side in (-1, 1):
        x = LADDER_X + side * px(15)
        d.rectangle([x - px(3), top, x + px(3), bot], fill=(108, 120, 130))
        d.line([(x - px(3), top), (x - px(3), bot)], fill=(184, 198, 208),
               width=max(1, px(1)))
    y = top + px(6)
    while y < bot - px(5):
        d.rectangle([LADDER_X - px(16), y, LADDER_X + px(16), y + px(3)],
                    fill=(132, 146, 156))
        d.line([(LADDER_X - px(16), y), (LADDER_X + px(16), y)],
               fill=(196, 210, 220), width=max(1, px(1)))
        y += px(10)


def stairway(base):
    """Curved stone flight climbing away to the upper right."""
    steps = 17
    d = ImageDraw.Draw(base)
    for i in range(steps):
        t0, t1 = i / steps, (i + 1) / steps

        def at(t):
            x = STAIR_TOP + (STAIR_BOT - STAIR_TOP) * t
            y = px(40) + (FLOOR_Y - px(40)) * (t ** 1.25)
            w = px(30) + px(16) * t
            return x, y, w

        x0, y0, w0 = at(t0)
        x1, y1, w1 = at(t1)
        tone = 96 + int(24 * t0)
        d.polygon([(x0 - w0, y0), (x0 + w0, y0), (x1 + w1, y1), (x1 - w1, y1)],
                  fill=(tone, tone + 1, tone + 2))
        d.polygon([(x1 - w1, y1), (x1 + w1, y1),
                   (x1 + w1, y1 + px(8)), (x1 - w1, y1 + px(8))],
                  fill=(max(0, tone - 14),) * 3)
        d.line([(x1 - w1, y1), (x1 + w1, y1)], fill=(156, 238, 186),
               width=max(1, px(1)))
        # the stringer wall under the flight, so it is a solid stair
        d.polygon([(x1 - w1, y1 + px(8)), (x1 + w1, y1 + px(8)),
                   (x1 + w1, y1 + px(26)), (x1 - w1, y1 + px(24))],
                  fill=(46, 46, 47))
    # balustrade: posts and a rail following the same curve
    rail = []
    for i in range(steps + 1):
        t = i / steps
        x = STAIR_TOP + (STAIR_BOT - STAIR_TOP) * t
        y = px(40) + (FLOOR_Y - px(40)) * (t ** 1.25)
        rail.append((x, y - px(30)))
    d.line(rail, fill=(96, 100, 98), width=max(2, px(3)), joint="curve")
    for i in range(0, steps + 1, 3):
        x, y = rail[i]
        d.line([(x, y), (x, y + px(26))], fill=(88, 94, 90), width=max(1, px(2)))
    d.line([(x, y - px(2)) for x, y in rail], fill=(170, 214, 190),
           width=max(1, px(1)))


# ------------------------------------------------------------------- the tank
def sump(base):
    """Steel sump: metal rim, grey water, a green disc glowing under it."""
    cx, cy = SUMP_CX, SUMP_CY
    rx, ry = px(70), px(15)
    d = ImageDraw.Draw(base)

    # recessed steel collar
    for i in range(6):
        t = 1 - i / 6.0
        d.ellipse([cx - rx * t, cy - ry * t, cx + rx * t, cy + ry * t],
                  outline=(96 + i * 16, 106 + i * 16, 114 + i * 16),
                  width=max(1, px(2)))
    for k in range(28):                       # rim bolts
        a = 2 * math.pi * k / 28
        bx, by = cx + math.cos(a) * rx * 0.96, cy + math.sin(a) * ry * 0.96
        d.ellipse([bx - px(1.6), by - px(1.6), bx + px(1.6), by + px(1.6)],
                  fill=(176, 188, 198))

    # the hole itself: water, with the lit disc showing through from below
    water = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(water)
    wd.ellipse([cx - rx * 0.90, cy - ry * 0.86, cx + rx * 0.90, cy + ry * 0.86],
               fill=WATER + (255,))
    wd.ellipse([cx - rx * 0.66, cy - ry * 0.34, cx + rx * 0.66, cy + ry * 0.92],
               fill=mix(WATER, (150, 168, 178), 0.5) + (255,))
    base.alpha_composite(water)

    disc = art.radial_light((W, H), (cx, cy + ry * 0.22), rx * 0.52,
                            (128, 246, 176), 235)
    base.alpha_composite(disc.filter(ImageFilter.GaussianBlur(px(3))))
    d = ImageDraw.Draw(base)
    d.ellipse([cx - rx * 0.34, cy + ry * 0.02, cx + rx * 0.34, cy + ry * 0.74],
              outline=(150, 246, 186), width=max(1, px(2)))

    # metal sheen on the water, and the shaft reflected in it as a streak
    for i in range(9):
        a = math.pi * (0.12 + 0.76 * i / 8)
        x0 = cx + math.cos(a) * rx * 0.88
        y0 = cy + math.sin(a) * ry * 0.84
        d.line([(x0, y0), (x0 + px(10), y0 + px(2))],
               fill=(196, 208, 216, 120), width=max(1, px(1)))
    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    for i in range(7):
        w = px(3) + px(1.4) * i
        rd.rectangle([cx - w, cy - ry * 0.5, cx + w, cy + ry * 0.6],
                     fill=GREEN + (26 + 10 * i,))
    base.alpha_composite(refl.filter(ImageFilter.GaussianBlur(px(2))))


def tree(base):
    """Dead tree fallen across the left of the floor, walkable along its trunk."""
    rnd = random.Random(5)
    d = ImageDraw.Draw(base)
    x0, x1 = TREE_CX - px(96), TREE_CX + px(104)
    yb = FLOOR_Y + px(26)
    top, bot = [], []
    for i in range(21):
        t = i / 20
        x = x0 + (x1 - x0) * t
        y = yb - math.sin(t * 2.4) * px(7)
        thick = px(13) * (1 - 0.30 * t)
        top.append((x, y - thick))
        bot.append((x, y + thick * 0.7))
    d.polygon(top + bot[::-1], fill=(76, 63, 45))
    for k in range(7):                        # bark ridges
        d.line([(x, y - px(2) + k * px(2.6)) for x, y in top],
               fill=(54, 45, 33), width=max(1, px(1)))
    d.line(top, fill=(124, 106, 74), width=max(1, px(1)))
    # broken branch stubs and a snag of roots
    for t, up in ((0.22, -1), (0.55, 1), (0.78, -1)):
        bx = x0 + (x1 - x0) * t
        by = yb - math.sin(t * 2.4) * px(7)
        d.line([(bx, by), (bx + up * px(18), by - px(26))], fill=(66, 55, 40),
               width=max(2, px(3)))
        d.line([(bx + up * px(18), by - px(26)),
                (bx + up * px(26), by - px(38))], fill=(38, 32, 24),
               width=max(1, px(2)))
    for _ in range(90):                       # moss on the bark
        x = rnd.uniform(x0, x1)
        y = rnd.uniform(yb - px(14), yb + px(6))
        d.ellipse([x, y, x + px(3), y + px(2)], fill=(46, 74, 34, 140))


def planks(base):
    """Boards bridging the channel on the right side of the floor."""
    rnd = random.Random(9)
    d = ImageDraw.Draw(base)
    cx, cy = PLANK_CX, FLOOR_Y + px(22)
    ln = px(120)
    d.polygon([(cx - ln * 0.6, cy - px(6)), (cx + ln * 0.6, cy - px(4)),
               (cx + ln * 0.62, cy + px(34)), (cx - ln * 0.6, cy + px(36))],
              fill=(16, 17, 18))
    for i in range(5):
        y = cy + i * px(7)
        off = i * px(3) - px(6)
        d.polygon([(cx - ln / 2 + off, y), (cx + ln / 2 - off * 0.6, y + px(2)),
                   (cx + ln / 2 - off * 0.6, y + px(8)),
                   (cx - ln / 2 + off, y + px(7))],
                  fill=(118 + i * 4, 92 + i * 3, 62 + i * 3))
        d.line([(cx - ln / 2 + off, y + px(1)), (cx + ln / 2 - off * 0.6, y + px(3))],
               fill=(146, 118, 80), width=max(1, px(1)))
        for _ in range(14):
            x = rnd.uniform(cx - ln / 2, cx + ln / 2)
            d.line([(x, y + px(2)), (x + px(10), y + px(2))],
                   fill=(84, 66, 44), width=1)
        for nx in (cx - ln / 2 + px(6), cx + ln / 2 - px(8)):
            d.ellipse([nx, y + px(3), nx + px(2), y + px(5)], fill=(150, 160, 166))


# ------------------------------------------------------------------ back wall
def tunnel(base):
    """Arched opening in the back wall, and the dragon hiding in it."""
    cx, top, half = TUNNEL_CX, FLOOR_Y - px(112), px(32)
    d = ImageDraw.Draw(base)
    d.rectangle([cx - half, top + px(20), cx + half, FLOOR_Y], fill=(9, 10, 11))
    d.pieslice([cx - half, top, cx + half, top + px(70)], 180, 360, fill=(9, 10, 11))
    # a rim of lit brick around the mouth, so it is an opening and not a hole
    d.arc([cx - half - px(4), top - px(4), cx + half + px(4), top + px(74)],
          180, 360, fill=(132, 116, 96), width=max(1, px(2)))
    # voussoirs around the opening
    for i in range(13):
        a = math.pi + math.pi * i / 12
        x0 = cx + math.cos(a) * half
        y0 = top + px(35) + math.sin(a) * px(35)
        x1 = cx + math.cos(a) * (half + px(9))
        y1 = top + px(35) + math.sin(a) * px(49)
        d.line([(x0, y0), (x1, y1)], fill=(52, 46, 42), width=max(2, px(3)))
    d.line([(cx - half, top + px(35)), (cx - half, FLOOR_Y)],
           fill=(64, 56, 48), width=max(1, px(2)))
    d.line([(cx + half, top + px(35)), (cx + half, FLOOR_Y)],
           fill=(64, 56, 48), width=max(1, px(2)))
    # the far end of the tunnel is not quite black
    haze = art.radial_light((W, H), (cx, FLOOR_Y - px(60)), px(34),
                            (60, 140, 100), 54)
    base.alpha_composite(haze)
    return dragon(base, cx, FLOOR_Y - px(72), px(38), px(46))


def dragon(base, cx, cy, w, h):
    """Only the skull and a coil of neck catch the light; the eyes are red."""
    rnd = random.Random(63)
    d = ImageDraw.Draw(base)
    dark, lit = (26, 26, 28), (78, 88, 82)
    # skull: long snout running left, heavy brow, jaw hanging open
    d.polygon([(cx - w * 0.10, cy - h * 0.42), (cx + w * 0.30, cy - h * 0.52),
               (cx + w * 0.48, cy - h * 0.20), (cx + w * 0.40, cy + h * 0.10),
               (cx + w * 0.10, cy + h * 0.22), (cx - w * 0.18, cy + h * 0.10),
               (cx - w * 0.26, cy - h * 0.16)], fill=dark)
    d.polygon([(cx - w * 0.24, cy - h * 0.06), (cx - w * 0.60, cy + h * 0.02),
               (cx - w * 0.58, cy + h * 0.16), (cx - w * 0.20, cy + h * 0.20)],
              fill=dark)
    d.polygon([(cx - w * 0.22, cy + h * 0.20), (cx - w * 0.54, cy + h * 0.30),
               (cx - w * 0.44, cy + h * 0.40), (cx - w * 0.08, cy + h * 0.34)],
              fill=(12, 12, 13))
    # horns swept back
    for sx, sy in ((cx + w * 0.18, cy - h * 0.50), (cx + w * 0.34, cy - h * 0.34)):
        d.polygon([(sx, sy), (sx + w * 0.16, sy - h * 0.30),
                   (sx + w * 0.22, sy - h * 0.06), (sx + w * 0.06, sy + h * 0.04)],
                  fill=(30, 30, 32))
    for k in range(7):                        # teeth
        tx = cx - w * 0.50 + k * w * 0.055
        d.polygon([(tx, cy + h * 0.12), (tx + w * 0.02, cy + h * 0.12),
                   (tx + w * 0.01, cy + h * 0.20)], fill=(120, 116, 104))
    for _ in range(16):                       # scales catching the green
        x = cx + rnd.uniform(-w * 0.3, w * 0.45)
        y = cy + rnd.uniform(-h * 0.45, h * 0.2)
        d.arc([x, y, x + px(4), y + px(3)], 200, 340, fill=lit, width=1)
    eyes = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ed = ImageDraw.Draw(eyes)
    for sx in (cx - w * 0.06, cx + w * 0.16):
        ed.ellipse([sx - px(4), cy - h * 0.22, sx + px(4), cy - h * 0.13],
                   fill=(255, 40, 28))
        ed.ellipse([sx - px(1.6), cy - h * 0.205, sx + px(1.6), cy - h * 0.155],
                   fill=(255, 220, 190))
    return art.screen(base, eyes, glow_radius=px(7), gain=1.5, passes=2)


# ------------------------------------------------------------------ light, air
def shaft(base, x, top_y, bot_y, half_top, half_bot, strength=1.0):
    """Green column falling from a roof grating to a surface below it."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(18):
        t = i / 17
        half = half_top + (half_bot - half_top) * t
        d.polygon([(x - half, bot_y), (x + half, bot_y),
                   (x + half_top * 0.8, top_y), (x - half_top * 0.8, top_y)],
                  fill=GREEN + (int((9 + 15 * (1 - t)) * strength),))
    layer = layer.filter(ImageFilter.GaussianBlur(px(5)))
    core = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(core)
    for i in range(7):
        t = i / 6
        half = half_top * 0.30 + (half_bot * 0.16) * t
        cd.rectangle([x - half, top_y, x + half, bot_y],
                     fill=(230, 255, 222, int((22 + 20 * (1 - t)) * strength)))
    core = core.filter(ImageFilter.GaussianBlur(px(2)))
    out = art.screen(base, layer, glow_radius=px(8), gain=1.0, passes=2)
    return art.screen(out, core, glow_radius=px(3), gain=0.8)


def mist(img, seed=17):
    rnd = random.Random(seed)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(10):
        y = FLOOR_Y - px(rnd.randint(10, 80))
        d.ellipse([rnd.randint(-px(80), W // 2), y,
                   rnd.randint(W // 2, W + px(80)), y + px(rnd.randint(12, 34))],
                  fill=(26, 84, 58, rnd.randint(8, 22)))
    return Image.alpha_composite(img, layer.filter(ImageFilter.GaussianBlur(px(16))))


def drips(img, seed=4):
    """Water coming off the pipes and the roof - the sewer reading."""
    rnd = random.Random(seed)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(220):
        x = rnd.randint(0, W)
        y = rnd.randint(int(ROOF), int(FLOOR_Y))
        ln = rnd.randint(int(px(4)), int(px(16)))
        d.line([(x, y), (x, y + ln)], fill=(150, 196, 176, rnd.randint(14, 40)), width=1)
    return Image.alpha_composite(img, layer)


# ------------------------------------------------------------------ the arena
def paint():
    base = hd.blank([(0, (5, 7, 8)), (40, (9, 12, 13)), (110, (13, 16, 18)),
                     (170, (15, 18, 19)), (210, (14, 16, 17)), (240, (7, 9, 9))])
    brick_wall(base)
    ceiling_vault(base)
    niches(base)
    pipes(base)
    tunnel(base)
    ladder(base)
    stairway(base)

    d = ImageDraw.Draw(base)
    # floor: wet slabs
    d.rectangle([0, FLOOR_Y, W, H], fill=(70, 72, 72))
    rnd = random.Random(31)
    for _ in range(220):
        x = rnd.randint(-px(10), W)
        y = rnd.randint(int(FLOOR_Y), int(H))
        w = rnd.randint(int(px(18)), int(px(74)))
        h = rnd.randint(int(px(6)), int(px(18)))
        tone = rnd.randint(58, 86)
        d.polygon([(x, y), (x + w, y + rnd.randint(-3, 3)),
                   (x + w + rnd.randint(-4, 4), y + h),
                   (x + rnd.randint(-3, 3), y + h)], fill=(tone, tone + 1, tone + 2))
    d.line([(0, FLOOR_Y), (W, FLOOR_Y)], fill=(84, 86, 84), width=max(1, px(1.4)))

    sump(base)
    tree(base)
    planks(base)

    base = hd.shade(base, [
        (hd.light(SUMP_CX, SUMP_CY + px(4), px(120), (78, 216, 140), 122), px(14), 1.3),
        (hd.light(LADDER_X, px(120), px(120), (64, 196, 126), 84), px(12), 1.15),
        (hd.light((STAIR_TOP + STAIR_BOT) / 2, FLOOR_Y - px(60), px(150),
                  (70, 208, 134), 88), px(12), 1.15),
        (hd.light(TUNNEL_CX, FLOOR_Y - px(96), px(60), (188, 30, 22), 54),
         px(8), 1.1),
        (hd.light(SUMP_CX, FLOOR_Y, px(130), (44, 108, 80), 48), px(12), 1.1),
        (hd.light(LADDER_X, FLOOR_Y, px(90), (60, 190, 120), 62), px(14), 1.1),
        (hd.light((STAIR_TOP + STAIR_BOT) / 2, FLOOR_Y, px(110), (64, 196, 126), 62),
         px(14), 1.1),
    ])

    grating(base, SUMP_CX)
    grating(base, LADDER_X)
    grating(base, (STAIR_TOP + STAIR_BOT) / 2)
    base = shaft(base, SUMP_CX, px(14), FLOOR_Y + px(10), px(26), px(34), 1.0)
    base = shaft(base, LADDER_X, px(14), FLOOR_Y, px(20), px(22), 0.85)
    base = shaft(base, (STAIR_TOP + STAIR_BOT) / 2, px(14), FLOOR_Y, px(22), px(28), 0.9)
    base = drips(base)
    base = mist(base)
    base = hd.finish(base, 11, 5, 0.48, FLOOR_Y)

    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    for i in range(px(22)):
        a = int(200 * (1 - i / px(22)) ** 1.4)
        fd.line([(0, H - i), (W, H - i)], fill=(4, 6, 5, a))
    # a pipe crossing in front of the camera, and the tank's near lip
    fd.rectangle([0, H - px(16), W, H - px(9)], fill=(16, 18, 19, 235))
    fd.line([(0, H - px(16)), (W, H - px(16))], fill=(52, 58, 62, 200),
            width=max(1, px(1)))
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, fg, 1)]


def main():
    hd.STAGES["the_upside_down"] = ("The Upside Down", paint)
    hd.build("the_upside_down")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
