"""Outside the Dragon of the Black Pool Restaurant: the pavement at closing time.

Painted from the street reference: a long restaurant window in a bright white
frame with the warm room behind it, a red lacquer board over the door, red neon
ovals on the painted wall, a glass door standing open on a flight of stone
steps, and a wet pavement carrying the red and gold of every light down into
the gutter, with crosswalk paint at one end and litter blown along the kerb.

A stage is seen across the play plane, so the street is painted as the pavement
wall-to-wall: the facade stands against the back of the pavement, the steps come
down to the kerb, and the fighters stand on the wet street in front of it. The
window's sill, the steps and the kerb all stop at the pavement line, so nothing
comes out into the play plane to stand on anybody's feet.

The interior seen through the glass is the dining room this game already has, so
the window shows that room: cream tile, a steel cabinet, a laid table, the
pendants over it.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960, localcoord 1920x1080, camera travel +/-3136.

Run:  python3 tools/stage_dragon_street.py     (part of tools/build_all.py)
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

WALL_TOP = px(44)                  # 198: the top of the painted wall
CORNICE = px(52)                   # 234: the lit ledge over the wall
PLINTH = FLOOR_Y - px(18)          # 819: the stone course at the pavement
# Two windows either side of the door, so the match-start view lands on the
# entrance and its neon instead of on one long pane of glass.
WIN_A = (px(250), px(730))
WIN_B = (px(1090), px(1570))
WIN_Y0, WIN_Y1 = px(58), px(140)
DOOR_CX = px(910)                  # the entrance, at the centre of the stage
STEP_W = px(96)

RENDER = (34, 44, 52)              # the wall: dark blue-green painted render
RENDER_L = (52, 64, 74)
RENDER_D = (20, 26, 32)
STONE = (96, 92, 84)
STONE_L = (146, 140, 128)
STONE_D = (48, 46, 42)
FRAME = (238, 236, 226)            # the window's white frame
FRAME_D = (176, 172, 158)
CREAM = (226, 214, 186)            # the interior: tiled wall
CREAM_D = (188, 176, 148)
WOOD = (92, 58, 36)
WOOD_L = (138, 92, 54)
RED = (150, 34, 28)
RED_L = (198, 62, 44)
BRASS = (176, 138, 66)
WARM = (255, 206, 140)
NEON_R = (255, 56, 44)
NEON_O = (255, 138, 40)
NEON_G = (110, 236, 180)
GLASS = (44, 56, 60)
ASPHALT = (42, 42, 44)
ASPHALT_L = (66, 66, 68)
WET_RED = (196, 44, 38)
LITTER = (216, 208, 186)

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


def slab(d, x0, y0, x1, y1, c, hi=0.32, lo=0.34):
    """A flat panel with a lit top edge and a shaded bottom edge."""
    d.rectangle(box(x0, y0, x1, y1), fill=c)
    d.line([(x0, y0), (x1, y0)], fill=mix(c, (255, 250, 236), hi), width=max(1, int(px(0.8))))
    d.line([(x0, y1), (x1, y1)], fill=mix(c, (16, 14, 12), lo), width=max(1, int(px(0.9))))


# ------------------------------------------------------------------- the wall
def facade(base):
    """The painted wall: render, grime, a lit cornice and a stone course."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, WALL_TOP, W, FLOOR_Y), fill=RENDER)
    rnd = random.Random(12)

    # patches of repaint and damp, so the wall is a wall and not a colour field
    for i in range(260):
        x = rnd.uniform(0, W)
        y = rnd.uniform(WALL_TOP, PLINTH)
        w = rnd.uniform(px(30), px(120))
        h = rnd.uniform(px(14), px(56))
        c = rnd.choice((RENDER_L, RENDER_D, (40, 50, 58), (30, 38, 44)))
        d.ellipse(box(x, y, x + w, y + h), fill=mix(RENDER, c, rnd.uniform(0.12, 0.40)))

    # a damp tide-mark rising from the pavement
    for i in range(px(26)):
        a = int(66 * (1 - i / float(px(26))) ** 1.5)
        d.line([(0, PLINTH - i), (W, PLINTH - i)], fill=(12, 18, 22, a))

    # the cornice over the wall, with its shadow
    d.rectangle(box(0, CORNICE - px(8), W, CORNICE), fill=mix(RENDER, RENDER_L, 0.5))
    d.line([(0, CORNICE - px(8)), (W, CORNICE - px(8))], fill=(150, 154, 148),
           width=max(1, int(px(0.8))))
    d.line([(0, CORNICE), (W, CORNICE)], fill=(10, 14, 16), width=max(1, int(px(1.0))))
    d.rectangle(box(0, 0, W, CORNICE - px(8)), fill=(20, 24, 28))

    # stone course at the pavement, and the kerb it stands on
    d.rectangle(box(0, PLINTH, W, FLOOR_Y), fill=STONE)
    for x in range(-px(10), W, px(56)):
        c = tint(mix(STONE, STONE_L, rnd.uniform(0.0, 0.4)), rnd, 0.08)
        d.rectangle(box(x + px(2), PLINTH + px(2), x + px(54), FLOOR_Y - px(1)), fill=c)
        d.line([(x, PLINTH), (x, FLOOR_Y)], fill=mix(c, STONE_D, 0.6),
               width=max(1, int(px(0.8))))
        d.line([(x + px(2), PLINTH + px(2)), (x + px(54), PLINTH + px(2))],
               fill=mix(c, (250, 246, 232), 0.28), width=max(1, int(px(0.5))))
    d.line([(0, PLINTH), (W, PLINTH)], fill=STONE_L, width=max(1, int(px(1.0))))
    d.line([(0, FLOOR_Y - px(2)), (W, FLOOR_Y - px(2))], fill=(14, 14, 12),
           width=max(1, int(px(1.2))))


def drainpipe(base, x):
    """A rainwater pipe down the wall, with its brackets."""
    d = ImageDraw.Draw(base)
    w = px(9)
    d.rectangle(box(x - w, CORNICE, x + w, PLINTH), fill=mix(RENDER, RENDER_D, 0.45))
    d.line([(x - w, CORNICE), (x - w, PLINTH)], fill=mix(RENDER, (130, 136, 132), 0.35),
           width=max(1, int(px(0.8))))
    d.line([(x + w, CORNICE), (x + w, PLINTH)], fill=(8, 10, 12),
           width=max(1, int(px(1.0))))
    for y in range(int(CORNICE) + int(px(40)), int(PLINTH), int(px(120))):
        d.rectangle(box(x - w - px(3), y, x + w + px(3), y + px(7)),
                    fill=mix(STONE_D, (80, 80, 76), 0.4))


# ------------------------------------------------------------------ the window
def window(base, x0, x1, y0, y1):
    """The long window, and the dining room standing behind its glass.

    The room is painted as a shallow box: a tiled back wall, the steel cabinet,
    the laid table and the pendants over it. It has to read through the glass at
    a glance, so the details are large and the light is warm.
    """
    d = ImageDraw.Draw(base)
    inner = box(x0 + px(10), y0 + px(10), x1 - px(10), y1 - px(6))
    # the reveal, dark, so the window is a hole in a thick wall
    d.rectangle(box(x0 - px(6), y0 - px(6), x1 + px(6), y1 + px(6)), fill=(18, 22, 26))

    # ---- the room: tiled back wall, and the floor of the room behind
    d.rectangle(inner, fill=mix(CREAM, (104, 92, 74), 0.52))
    t = px(7)
    for r, yy in enumerate(range(int(inner[1]), int(inner[3]), t)):
        for c, xx in enumerate(range(int(inner[0]), int(inner[2]), t)):
            cc = tint(mix(CREAM, (102, 90, 72),
                          0.44 + (0.10 if (r + c) % 3 == 0 else 0.0)),
                      random.Random(r * 97 + c), 0.05)
            d.rectangle(box(xx + 1, yy + 1, xx + t - 1, yy + t - 1), fill=cc)
    d.rectangle(box(inner[0], inner[1] + (inner[3] - inner[1]) * 0.74,
                    inner[2], inner[3]),
                fill=mix((120, 96, 70), (86, 66, 46), 0.2))       # the floor
    d.line([(inner[0], inner[1] + (inner[3] - inner[1]) * 0.74),
            (inner[2], inner[1] + (inner[3] - inner[1]) * 0.74)],
           fill=(60, 46, 30), width=max(1, int(px(1.0))))

    # the steel cabinet at the left end of the room, with its shelves of jars
    cx0 = inner[0] + px(8)
    d.rectangle(box(cx0, inner[1] + px(14), cx0 + px(64), inner[3]), fill=(122, 128, 124))
    for k in range(3):
        sy = inner[1] + px(20) + k * px(22)
        d.rectangle(box(cx0 + px(4), sy, cx0 + px(60), sy + px(3)), fill=(206, 210, 204))
        for j in range(5):
            jar_x = cx0 + px(8) + j * px(11)
            d.rounded_rectangle(box(jar_x, sy - px(14), jar_x + px(7), sy),
                                radius=max(1, int(px(1.2))),
                                fill=mix((150, 160, 148), (206, 196, 170), rnd_f(j)))
    d.line([(cx0, inner[1] + px(14)), (cx0, inner[3])], fill=(226, 230, 224),
           width=max(1, int(px(1.0))))

    # the laid table, with its white cloth and the plates still out
    tx = (inner[0] + inner[2]) / 2.0
    ty = inner[1] + (inner[3] - inner[1]) * 0.62
    tw = (inner[2] - inner[0]) * 0.30
    d.rectangle(box(tx - tw / 2.0, ty, tx + tw / 2.0, inner[3]),
                fill=mix((196, 190, 174), (158, 152, 136), 0.25))
    d.rectangle(box(tx - tw / 2.0, ty - px(7), tx + tw / 2.0, ty),
                fill=(210, 204, 188))
    d.line([(tx - tw / 2.0, ty), (tx + tw / 2.0, ty)], fill=(198, 192, 174),
           width=max(1, int(px(0.7))))
    for k in range(3):
        plx = tx - tw * 0.34 + k * tw * 0.34
        d.ellipse(box(plx - px(9), ty - px(11), plx + px(9), ty - px(5)),
                  fill=(246, 242, 230))
        d.ellipse(box(plx - px(5), ty - px(10), plx + px(5), ty - px(6)),
                  fill=mix((198, 176, 132), (226, 214, 190), 0.3))

    # two pendants over the room, and the warm light they throw
    for k in (0.36, 0.68):
        lx = inner[0] + (inner[2] - inner[0]) * k
        ly = inner[1] + px(16)
        d.line([(lx, inner[1]), (lx, ly - px(6))], fill=(38, 32, 26),
               width=max(1, int(px(0.6))))
        d.polygon([(lx - px(9), ly - px(6)), (lx + px(9), ly - px(6)),
                   (lx + px(5), ly + px(2)), (lx - px(5), ly + px(2))],
                  fill=mix(WOOD, (60, 40, 24), 0.3))
        d.ellipse(box(lx - px(4), ly + px(1), lx + px(4), ly + px(7)),
                  fill=(255, 240, 200))
        lamp(lx, ly + px(6), px(70), (255, 196, 126), 44)
    lamp((inner[0] + inner[2]) / 2.0, inner[1] + (inner[3] - inner[1]) * 0.5,
         (inner[2] - inner[0]) * 0.55, (255, 194, 128), 32)

    # ---- the glass: a cool tint over the room, then the frame in front of it
    glass = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glass)
    gd.rectangle(inner, fill=(28, 44, 52, 46))
    for k in range(4):                       # reflections of the street
        rx = inner[0] + (inner[2] - inner[0]) * (0.18 + 0.22 * k)
        gd.polygon([(rx, inner[1]), (rx + px(34), inner[1]),
                    (rx + px(10), inner[3]), (rx - px(24), inner[3])],
                   fill=(210, 226, 232, 20))
    base.alpha_composite(glass)

    # ---- frame: a bright white casing, mullions and a heavy sill
    # the casing is four bars of frame, not one filled rectangle: filling the
    # whole opening put a white panel over the room behind the glass
    fw = px(9)
    d.rectangle(box(x0 - fw, y0 - fw, x1 + fw, y0), fill=FRAME)
    d.rectangle(box(x0 - fw, y1, x1 + fw, y1 + fw), fill=FRAME)
    d.rectangle(box(x0 - fw, y0, x0, y1), fill=FRAME)
    d.rectangle(box(x1, y0, x1 + fw, y1), fill=FRAME)
    d.rectangle(inner, fill=None, outline=mix(FRAME, FRAME_D, 0.4),
                width=max(2, int(px(1.6))))
    d.line([(x0 - px(9), y0 - px(9)), (x1 + px(9), y0 - px(9))],
           fill=(255, 253, 246), width=max(1, int(px(1.0))))
    d.line([(x0 - px(9), y1 + px(9)), (x1 + px(9), y1 + px(9))],
           fill=mix(FRAME, FRAME_D, 0.7), width=max(2, int(px(1.6))))
    for k in range(1, 5):
        mx = x0 + (x1 - x0) * k / 5.0
        d.rectangle(box(mx - px(3), y0, mx + px(3), y1), fill=FRAME)
        d.line([(mx - px(3), y0), (mx - px(3), y1)], fill=(255, 253, 246),
               width=max(1, int(px(0.8))))
        d.line([(mx + px(3), y0), (mx + px(3), y1)], fill=mix(FRAME, FRAME_D, 0.6),
               width=max(1, int(px(0.9))))
    d.rectangle(box(x0 - px(12), y1 + px(9), x1 + px(12), y1 + px(18)),
                fill=mix(STONE, STONE_L, 0.35))
    d.line([(x0 - px(12), y1 + px(9)), (x1 + px(12), y1 + px(9))],
           fill=(252, 248, 238), width=max(1, int(px(1.0))))
    d.line([(x0 - px(12), y1 + px(18)), (x1 + px(12), y1 + px(18))],
           fill=(28, 26, 22), width=max(1, int(px(1.0))))
    lamp((x0 + x1) / 2.0, y1 + px(14), px(240), (255, 208, 150), 26)


def rnd_f(seed):
    """A fixed weight from a seed, for choosing a jar's glaze."""
    return random.Random(seed * 131 + 7).random()


# ------------------------------------------------------------------- the signs
def neon_board(base, x0, x1, y0, y1, seed):
    """The red lacquer board over the door, gilded and lit from behind."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(x0 - px(6), y0 - px(6), x1 + px(6), y1 + px(6)), fill=(30, 16, 12))
    d.rectangle(box(x0, y0, x1, y1), fill=mix(RED, (104, 22, 18), 0.35))
    for i in range(int(y1 - y0)):
        tt = i / max(1.0, y1 - y0 - 1)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=mix((120, 26, 20), (168, 44, 32), tt))
    # gilt frame and corner brackets
    d.rectangle(box(x0, y0, x1, y1), outline=mix(BRASS, (240, 200, 118), 0.35),
                width=max(2, int(px(1.6))))
    d.rectangle(box(x0 + px(3), y0 + px(3), x1 - px(3), y1 - px(3)),
                outline=mix((96, 66, 28), BRASS, 0.4), width=max(1, int(px(0.8))))
    for sx in (x0 + px(7), x1 - px(7)):
        for sy in (y0 + px(7), y1 - px(7)):
            d.ellipse(box(sx - px(2.5), sy - px(2.5), sx + px(2.5), sy + px(2.5)),
                      fill=mix(BRASS, (248, 214, 140), 0.4))
    # the characters, gilt, over the red
    cols = 3
    for k in range(cols):
        gx = x0 + (x1 - x0) * (k + 0.5) / cols
        hd.glyph(d, gx - px(9), y0 + px(11), px(18), (246, 208, 128), seed=seed + k,
                 width=px(2.0))
    d.line([(x0 + px(6), y1 - px(8)), (x1 - px(6), y1 - px(8))],
           fill=mix((248, 212, 138), BRASS, 0.3), width=max(1, int(px(0.7))))
    lamp((x0 + x1) / 2.0, (y0 + y1) / 2.0, (x1 - x0) * 0.85, (255, 96, 58), 96)


def neon_oval(base, cx, cy, r):
    """One red neon oval on the wall, with the light it throws on the render."""
    d = ImageDraw.Draw(base)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for k, a in ((px(26), 40), (px(14), 70), (px(6), 96)):
        gd.ellipse(box(cx - r - k, cy - r * 0.62 - k, cx + r + k, cy + r * 0.62 + k),
                   outline=NEON_R + (a,), width=max(1, int(px(2.0))))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(px(5))))
    d.ellipse(box(cx - r, cy - r * 0.62, cx + r, cy + r * 0.62),
              outline=NEON_R, width=max(2, int(px(2.4))))
    d.ellipse(box(cx - r * 0.94, cy - r * 0.56, cx + r * 0.94, cy + r * 0.56),
              outline=(255, 176, 158), width=max(1, int(px(1.0))))
    hd.glyph(d, cx - px(7), cy - px(7), px(14), (255, 120, 96), seed=int(cx),
             width=px(1.6))
    lamp(cx, cy, px(110), (255, 62, 44), 84)


def wall_lamp(base, x, y):
    """A brass gooseneck lamp over the door, and the pool it throws."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(x - px(4), y - px(3), x + px(4), y + px(2)), fill=mix(BRASS, (92, 68, 32), 0.4))
    d.arc(box(x - px(20), y - px(22), x + px(20), y + px(6)), 250, 350,
          fill=mix(BRASS, (224, 186, 110), 0.3), width=max(2, int(px(2.0))))
    d.polygon([(x - px(14), y - px(12)), (x + px(14), y - px(12)),
               (x + px(10), y - px(20)), (x - px(10), y - px(20))],
              fill=mix((70, 52, 30), (46, 34, 20), 0.3))
    d.ellipse(box(x - px(9), y - px(13), x + px(9), y - px(5)), fill=(255, 236, 186))
    d.ellipse(box(x - px(4), y - px(12), x + px(4), y - px(6)), fill=(255, 252, 226))
    lamp(x, y - px(6), px(120), (255, 204, 140), 104)
    lamp(x, FLOOR_Y + px(20), px(70), (255, 198, 132), 30)


# -------------------------------------------------------------------- the door
def door(base, cx):
    """The entrance: a recessed doorway, a glass door, and the steps down."""
    d = ImageDraw.Draw(base)
    half = px(48)
    top = px(62)

    # the reveal, painted stone, going back into the wall
    d.rectangle(box(cx - half - px(10), top - px(10), cx + half + px(10), FLOOR_Y),
                fill=mix(STONE, STONE_D, 0.45))
    d.rectangle(box(cx - half, top, cx + half, FLOOR_Y), fill=(38, 28, 20))
    for i in range(px(96)):                      # the warm room beyond the door
        tt = i / float(px(96))
        d.line([(cx - half, top + i), (cx + half, top + i)],
               fill=mix((60, 38, 24), (172, 116, 62), tt ** 0.9))

    # the leaves: dark frames with big panes, one standing open
    leaves = ((cx - half + px(2), cx - px(2)), (cx + px(2), cx + half - px(2)))
    for lx0, lx1 in leaves:
        d.rectangle(box(lx0, top + px(4), lx1, FLOOR_Y - px(2)),
                    fill=mix(WOOD, (34, 22, 14), 0.35))
        gx0, gx1 = lx0 + px(5), lx1 - px(5)
        gy0, gy1 = top + px(10), FLOOR_Y - px(20)
        d.rectangle(box(gx0, gy0, gx1, gy1), fill=mix((176, 132, 84), (120, 86, 52), 0.35))
        d.rectangle(box(gx0, gy0, gx1, gy1), fill=None, outline=(32, 22, 14),
                    width=max(2, int(px(1.4))))
        d.line([(gx0 + px(6), gy1 - px(4)), (gx1 - px(10), gy0 + px(8))],
               fill=(236, 216, 176, 90), width=max(2, int(px(3.0))))
        # brass push bar across the glass
        d.rectangle(box(gx0, gy0 + (gy1 - gy0) * 0.52, gx1, gy0 + (gy1 - gy0) * 0.52 + px(4)),
                    fill=mix(BRASS, (232, 196, 122), 0.3))
        d.line([(lx0 + px(2), FLOOR_Y - px(16)), (lx1 - px(2), FLOOR_Y - px(4))],
               fill=mix(BRASS, (96, 70, 32), 0.4), width=max(2, int(px(2.0))))
    d.line([(cx - px(1), top + px(4)), (cx - px(1), FLOOR_Y - px(2))], fill=(18, 12, 8),
           width=max(1, int(px(1.4))))
    d.line([(cx + px(1), top + px(4)), (cx + px(1), FLOOR_Y - px(2))], fill=(18, 12, 8),
           width=max(1, int(px(1.4))))

    # the frame round the opening, and a lit lampshade under the transom
    d.rectangle(box(cx - half - px(12), top - px(14), cx + half + px(12), top - px(6)),
                fill=mix(STONE, STONE_L, 0.35))
    d.line([(cx - half - px(12), top - px(14)), (cx + half + px(12), top - px(14))],
           fill=(236, 230, 214), width=max(1, int(px(0.9))))

    # ---- the steps down to the pavement, and the light lying on them
    for i in range(3):
        sy = FLOOR_Y - px(4) + i * px(9)
        sw = half + px(16) + i * px(10)
        d.rectangle(box(cx - sw, sy, cx + sw, sy + px(9)), fill=mix(STONE, STONE_L, 0.42 - 0.10 * i))
        d.line([(cx - sw, sy), (cx + sw, sy)], fill=(244, 238, 224),
               width=max(1, int(px(1.0))))
        d.line([(cx - sw, sy + px(9)), (cx + sw, sy + px(9))], fill=(30, 28, 24),
               width=max(1, int(px(1.0))))
        for k in range(4):
            gx = cx - sw + (2 * sw) * (k + 0.5) / 4.0
            d.line([(gx, sy + px(1)), (gx, sy + px(8))], fill=mix(STONE, STONE_D, 0.4),
                   width=max(1, int(px(0.6))))
    d.rectangle(box(cx - STEP_W, FLOOR_Y, cx + STEP_W, FLOOR_Y + px(10)),
                fill=mix(STONE, STONE_L, 0.30))
    lamp(cx, top + px(50), px(200), (255, 196, 128), 120)
    lamp(cx, FLOOR_Y + px(26), px(150), (255, 188, 120), 62)


# ---------------------------------------------------------------- the pavement
def pavement(base):
    """Wet asphalt: the gutter, crosswalk paint, puddles, and every light in it."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(23)
    d.rectangle(box(0, FLOOR_Y, W, H), fill=ASPHALT)

    for i in range(520):                        # tar patches and worn stone
        x = rnd.uniform(0, W)
        y = rnd.uniform(FLOOR_Y, H)
        w = rnd.uniform(px(18), px(130))
        h = rnd.uniform(px(5), px(24))
        c = rnd.choice((ASPHALT_L, (28, 28, 30), (52, 50, 48), (36, 34, 32)))
        d.ellipse(box(x, y, x + w, y + h), fill=mix(ASPHALT, c, rnd.uniform(0.2, 0.6)))

    # kerb, gutter and the line of the pavement edge
    d.rectangle(box(0, FLOOR_Y, W, FLOOR_Y + px(7)), fill=(58, 56, 52))
    d.line([(0, FLOOR_Y), (W, FLOOR_Y)], fill=(112, 108, 98), width=max(2, int(px(1.8))))
    d.line([(0, FLOOR_Y + px(7)), (W, FLOOR_Y + px(7))], fill=(20, 20, 20),
           width=max(1, int(px(0.8))))

    # crosswalk paint at the left end, worn through in places
    for k in range(5):
        x0 = px(14) + k * px(54)
        d.polygon([(x0, FLOOR_Y + px(16)), (x0 + px(32), FLOOR_Y + px(16)),
                   (x0 + px(46), H), (x0 + px(6), H)],
                  fill=mix((206, 202, 186), (160, 156, 142), 0.25))
        for j in range(7):
            wx = x0 + rnd.uniform(px(2), px(28))
            wy = rnd.uniform(FLOOR_Y + px(20), H)
            d.ellipse(box(wx, wy, wx + px(14), wy + px(6)),
                      fill=mix(ASPHALT, (150, 146, 132), 0.3))

    # the drain, and the channel it sits in
    dx = px(880)
    d.rectangle(box(dx - px(38), FLOOR_Y + px(22), dx + px(38), FLOOR_Y + px(40)),
                fill=(34, 34, 36))
    for k in range(8):
        sx = dx - px(32) + k * px(8)
        d.line([(sx, FLOOR_Y + px(24)), (sx, FLOOR_Y + px(38))], fill=(96, 96, 94),
               width=max(1, int(px(2.0))))
    d.rectangle(box(dx - px(38), FLOOR_Y + px(22), dx + px(38), FLOOR_Y + px(40)),
                outline=(66, 66, 64), width=max(1, int(px(1.0))))

    # puddles, before the reflections go on: they reflect harder than dry stone
    puddle = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(puddle)
    for cx0, cy0, w, h in ((px(300), FLOOR_Y + px(46), px(230), px(30)),
                           (px(700), FLOOR_Y + px(70), px(300), px(38)),
                           (px(1180), FLOOR_Y + px(40), px(210), px(28)),
                           (px(1560), FLOOR_Y + px(66), px(260), px(34))):
        pd.ellipse(box(cx0 - w / 2.0, cy0 - h / 2.0, cx0 + w / 2.0, cy0 + h / 2.0),
                   fill=(16, 22, 26, 120))
    base.alpha_composite(puddle.filter(ImageFilter.GaussianBlur(px(9))))

    # every light in the street, laid down the wet road in long smears
    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    for cx0, col, wdt, a in (((WIN_A[0] + WIN_A[1]) / 2.0, (255, 198, 132), px(210), 40),
                             ((WIN_B[0] + WIN_B[1]) / 2.0, (255, 198, 132), px(210), 40),
                             (DOOR_CX, (255, 150, 90), px(86), 70),
                             (px(774), (255, 60, 44), px(36), 62),
                             (px(1046), (255, 60, 44), px(36), 62),
                             (px(760), (255, 204, 140), px(42), 40),
                             (px(1060), (255, 204, 140), px(42), 40)):
        rd.polygon([(cx0 - wdt / 2.0, FLOOR_Y + px(6)), (cx0 + wdt / 2.0, FLOOR_Y + px(6)),
                    (cx0 + wdt * 1.25, H), (cx0 - wdt * 1.25, H)],
                   fill=col + (a,))
    base.alpha_composite(refl.filter(ImageFilter.GaussianBlur(px(22))))

    # a wet sheen over the whole road, brightest under the window
    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.rectangle(box(0, FLOOR_Y, W, H), fill=(180, 200, 206, 16))
    sd.polygon([(WIN_A[0] - px(60), FLOOR_Y), (WIN_B[1] + px(60), FLOOR_Y),
                (WIN_B[1] + px(200), H), (WIN_A[0] - px(200), H)],
               fill=(255, 214, 160, 22))
    base.alpha_composite(sheen.filter(ImageFilter.GaussianBlur(px(16))))


def litter(base, seed):
    """Papers and cans blown along the gutter, the way the still has them."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(seed)
    for i in range(56):
        x = rnd.uniform(0, W)
        y = rnd.uniform(FLOOR_Y + px(4), H - px(4))
        w = rnd.uniform(px(8), px(17))
        h = w * rnd.uniform(0.5, 0.8)
        col = mix(LITTER, (168, 162, 142), rnd.uniform(0.0, 0.6))
        d.polygon([(x, y), (x + w, y - h * 0.3), (x + w * 1.05, y + h * 0.7),
                   (x + px(2), y + h)], fill=col)
        for k in range(2):
            d.line([(x + px(2), y + h * 0.3 + k * px(3)),
                    (x + w * 0.9, y + h * 0.1 + k * px(3))],
                   fill=mix(col, (60, 56, 48), 0.55), width=max(1, int(px(0.4))))
    for i in range(9):
        x = rnd.uniform(0, W)
        y = rnd.uniform(FLOOR_Y + px(10), H - px(6))
        rr = rnd.uniform(px(3), px(5))
        c = rnd.choice(((120, 130, 122), (150, 60, 44), (170, 156, 110)))
        d.rectangle(box(x - rr, y - rr * 2.2, x + rr, y), fill=mix(c, (26, 26, 24), 0.3))
        d.line([(x - rr, y - rr * 2.2), (x + rr, y - rr * 2.2)], fill=(200, 200, 194),
               width=max(1, int(px(0.6))))


# ------------------------------------------------------------------- the front
def foreground():
    """The dark the camera brings, and a paper or two blown past it."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(31)
    for i in range(px(42)):
        a = int(165 * (1 - i / float(px(42))) ** 1.6)
        d.line([(0, H - i), (W, H - i)], fill=(8, 9, 10, a))
    for k in range(7):
        x = rnd.uniform(0, W)
        y = H - rnd.uniform(px(30), px(150))
        w = rnd.uniform(px(16), px(34))
        h = w * 0.6
        d.polygon([(x, y), (x + w, y - h * 0.4), (x + w, y + h * 0.6),
                   (x - px(2), y + h)], fill=(210, 204, 186, rnd.randint(60, 110)))
    for _ in range(90):
        x = rnd.uniform(0, W)
        y = rnd.uniform(FLOOR_Y - px(60), H)
        r = rnd.uniform(px(0.8), px(2.4))
        d.ellipse(box(x - r, y - r, x + r, y + r),
                  fill=(255, 208, 150, rnd.randint(20, 66)))
    return fg.filter(ImageFilter.GaussianBlur(px(1.5)))


# -------------------------------------------------------------------- the arena
def paint():
    LIGHTS.clear()
    base = hd.blank([(0, (10, 12, 14)), (WALL_TOP, (20, 24, 28)),
                     (px(120), (28, 32, 36)), (FLOOR_Y, (36, 34, 32)),
                     (H, (18, 18, 20))])

    facade(base)
    drainpipe(base, px(150))
    drainpipe(base, px(1670))
    window(base, WIN_A[0], WIN_A[1], WIN_Y0, WIN_Y1)
    window(base, WIN_B[0], WIN_B[1], WIN_Y0, WIN_Y1)
    neon_board(base, px(802), px(1018), px(46), px(94), 5)
    neon_oval(base, px(774), px(122), px(14))
    neon_oval(base, px(1046), px(122), px(14))
    wall_lamp(base, px(760), px(96))
    wall_lamp(base, px(1060), px(96))
    door(base, DOOR_CX)

    pavement(base)
    litter(base, 9)

    base = hd.shade(base, [(hd.light(cx, cy, r, col, int(peak * 0.82)),
                            max(8, int(r * 0.32)), 1.05)
                           for cx, cy, r, col, peak in LIGHTS])
    base = art.vignette(base, 0.46)
    base = art.grain(base, 3, seed=9)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


def main():
    hd.STAGES["dragon_street"] = ("Outside Dragon of the Black Pool Restaurant", paint)
    hd.build("dragon_street")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

