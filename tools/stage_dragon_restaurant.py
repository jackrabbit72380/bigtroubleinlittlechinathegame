"""Inside Dragon of the Black Pool Restaurant: the dining room, after hours.

Painted from the top-down restaurant reference: olive flocked wallpaper hung with
landscape scrolls, brass sconces, a dark wood wainscot, a red curtain over the
kitchen door, a gold dragon on black lacquer at the centre of the room, a bar
whose bottles are lit from below, a wall of glass block at one end, and round
tables in white cloth with the plates still out.

The reference is a plan seen from above and a stage here is seen across the play
plane, so the room is laid out as a wall of furniture rather than copied as a
map: the tables are pushed back against the wainscot with their chairs behind
them, and the floor the fighters stand on runs out towards the camera.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960 (nothing painted in the play plane blocks the fighters' feet),
localcoord 1920x1080, camera travel +/-3136. Group 3 is the foreground layer and
is drawn in front of the fighters.

Run:  python3 tools/stage_dragon_restaurant.py     (part of tools/build_all.py)
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

WALL_TOP = px(46)                  # 207: top of the wallpaper, under the beam
RAIL = FLOOR_Y - px(30)            # 765: chair rail, where the wainscot starts
MURAL_CX = CX                      # 4096: the gold dragon on black lacquer
DOOR_CX = px(450)                  # 2025: the kitchen door and its red curtain
BAR_X0, BAR_X1 = px(1060), px(1300)
GLASS_X0, GLASS_X1 = px(1330), px(1550)

WALLC = (94, 100, 64)              # olive flocked paper
WALLC_L = (116, 122, 80)
WALLC_D = (68, 74, 46)
WOOD = (78, 54, 36)
WOOD_L = (120, 86, 54)
WOOD_D = (44, 30, 20)
CREAM = (214, 204, 176)
CLOTH = (230, 224, 204)
CLOTH_D = (184, 178, 158)
RED = (142, 40, 32)
RED_L = (184, 62, 46)
BRASS = (178, 140, 68)
WARM = (255, 214, 150)
GOLD = (198, 152, 72)
GOLD_L = (238, 202, 126)
GOLD_D = (124, 88, 36)
LACQUER = (24, 30, 26)
FLOOR_L = (126, 114, 90)          # the light square of the chequer
FLOOR_D = (68, 60, 48)            # the dark square
GRID = (40, 34, 27)               # grout between them
SMOKE = (36, 32, 26)

# every warm source is collected here while the room is painted and blended in
# once at the end, so a lamp lights the paper around it instead of sitting on
# top of it as a decal
LIGHTS = []


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def tint(c, rnd, amt=0.09):
    return tuple(max(0, min(255, int(v * (1 + rnd.uniform(-amt, amt))))) for v in c)


def box(x0, y0, x1, y1):
    """Normalised corners: PIL refuses a rectangle drawn bottom-up."""
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def lamp(cx, cy, r, color=WARM, peak=150):
    LIGHTS.append((cx, cy, r, color, peak))


def grain_lines(d, x0, y0, x1, y1, rnd, n=5, tone=0.3):
    """A few wavy lines so a flat panel of wood reads as timber."""
    for _ in range(n):
        gy = rnd.uniform(y0, y1)
        d.line([(x0, gy), (x1, gy + rnd.uniform(-px(0.8), px(0.8)))],
               fill=mix(WOOD, WOOD_D, tone), width=1)


# ------------------------------------------------------------------ the ceiling
def ceiling(base):
    """Dark joisted ceiling, the beam the lanterns hang from, and its gilt line."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, 0, W, WALL_TOP), fill=(22, 18, 15))

    for x in range(-px(24), W, px(48)):
        d.rectangle(box(x, 0, x + px(15), WALL_TOP - px(8)), fill=(36, 28, 21))
        d.line([(x + px(1), 0), (x + px(1), WALL_TOP - px(8))],
               fill=(62, 46, 32), width=max(1, int(px(0.8))))
        d.line([(x + px(14), 0), (x + px(14), WALL_TOP - px(8))],
               fill=(14, 10, 8), width=max(1, int(px(0.9))))
        d.rectangle(box(x + px(15), 0, x + px(48), WALL_TOP - px(8)), fill=(28, 22, 17))

    # the beam the lanterns hang from
    d.rectangle(box(0, WALL_TOP - px(15), W, WALL_TOP), fill=(54, 38, 26))
    grain_lines(d, 0, WALL_TOP - px(13), W, WALL_TOP - px(3), random.Random(2), n=9, tone=0.35)
    d.line([(0, WALL_TOP - px(15)), (W, WALL_TOP - px(15))],
           fill=(96, 70, 44), width=max(1, int(px(1.0))))
    d.line([(0, WALL_TOP - px(11)), (W, WALL_TOP - px(11))],
           fill=(126, 96, 46), width=max(1, int(px(0.7))))
    d.line([(0, WALL_TOP - px(1)), (W, WALL_TOP - px(1))],
           fill=(10, 8, 6), width=max(2, int(px(1.6))))


# -------------------------------------------------------------------- the paper
def wallpaper(base):
    """Olive flocked paper: tonal stripes with a stencilled sprig in each cell."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, WALL_TOP, W, RAIL), fill=WALLC)

    stripe = px(9)
    for i, x in enumerate(range(0, W, stripe)):
        k = i % 3
        c = WALLC_L if k == 0 else (WALLC_D if k == 2 else WALLC)
        d.rectangle(box(x, WALL_TOP, x + stripe, RAIL), fill=mix(WALLC, c, 0.22))

    for i, gx in enumerate(range(px(18), W, px(44))):
        r = random.Random(400 + i)
        for gy in range(WALL_TOP + px(26), RAIL - px(14), px(42)):
            bx = gx + r.uniform(-px(3), px(3))
            d.line([(bx, gy + px(11)), (bx, gy - px(2))],
                   fill=mix(WALLC, (152, 158, 114), 0.30), width=max(1, int(px(0.5))))
            for k in range(3):
                ly = gy + px(7) - k * px(6)
                side = 1 if k % 2 else -1
                tipx = bx + side * px(7)
                d.line([(bx, ly), (tipx, ly - px(4))],
                       fill=mix(WALLC, (152, 158, 114), 0.26), width=max(1, int(px(0.5))))
                d.ellipse(box(tipx - px(1.7), ly - px(5.8), tipx + px(1.7), ly - px(2.4)),
                          fill=mix(WALLC, (164, 170, 122), 0.32))

    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for i in range(px(18)):
        a = int(132 * (1 - i / float(px(18))) ** 1.5)
        sd.line([(0, WALL_TOP + i), (W, WALL_TOP + i)], fill=(0, 0, 0, a))
    base.alpha_composite(shade)


def wainscot(base):
    """Raised wood panels under the chair rail, with a lit rail and a baseboard."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, RAIL, W, FLOOR_Y), fill=WOOD)
    rnd = random.Random(23)

    for x in range(-px(10), W, px(40)):
        d.rectangle(box(x + px(4), RAIL + px(6), x + px(36), FLOOR_Y - px(8)),
                    fill=mix(WOOD, WOOD_D, 0.18))
        d.line([(x + px(4), RAIL + px(6)), (x + px(36), RAIL + px(6))],
               fill=mix(WOOD, (152, 110, 68), 0.32), width=max(1, int(px(0.7))))
        d.line([(x + px(4), RAIL + px(6)), (x + px(4), FLOOR_Y - px(8))],
               fill=mix(WOOD, (152, 110, 68), 0.24), width=max(1, int(px(0.6))))
        d.line([(x + px(36), RAIL + px(6)), (x + px(36), FLOOR_Y - px(8))],
               fill=mix(WOOD, WOOD_D, 0.55), width=max(1, int(px(0.7))))
        for _ in range(3):
            gy = rnd.uniform(RAIL + px(10), FLOOR_Y - px(12))
            d.line([(x + px(8), gy), (x + px(32), gy + rnd.uniform(-px(0.6), px(0.6)))],
                   fill=mix(WOOD, WOOD_D, 0.30), width=1)

    d.rectangle(box(0, RAIL - px(4), W, RAIL + px(5)), fill=mix(WOOD, (134, 96, 58), 0.48))
    d.line([(0, RAIL - px(5)), (W, RAIL - px(5))], fill=CREAM, width=max(1, int(px(0.8))))
    d.line([(0, RAIL + px(5)), (W, RAIL + px(5))], fill=(20, 14, 10),
           width=max(1, int(px(1.0))))
    d.rectangle(box(0, FLOOR_Y - px(7), W, FLOOR_Y), fill=(38, 26, 18))
    d.line([(0, FLOOR_Y - px(7)), (W, FLOOR_Y - px(7))], fill=(92, 64, 40),
           width=max(1, int(px(0.6))))


def pilaster(base, x):
    """A dark wood pilaster: lit left face, shadowed right face, gilt reed."""
    d = ImageDraw.Draw(base)
    w = px(13)
    d.rectangle(box(x - w, WALL_TOP, x + w, FLOOR_Y), fill=mix(WOOD, WOOD_D, 0.24))
    d.rectangle(box(x - w, WALL_TOP, x - w + px(4), FLOOR_Y), fill=mix(WOOD, WOOD_L, 0.34))
    d.line([(x + w, WALL_TOP), (x + w, FLOOR_Y)], fill=(14, 10, 8),
           width=max(1, int(px(1.0))))
    d.line([(x, WALL_TOP + px(12)), (x, FLOOR_Y - px(18))],
           fill=mix(BRASS, WOOD, 0.42), width=max(1, int(px(0.6))))

    for yy, hh in ((WALL_TOP, px(8)), (FLOOR_Y - px(13), px(13))):
        d.rectangle(box(x - w - px(3), yy, x + w + px(3), yy + hh),
                    fill=mix(WOOD, WOOD_L, 0.28))
        d.line([(x - w - px(3), yy), (x + w + px(3), yy)],
               fill=(184, 154, 104), width=max(1, int(px(0.6))))


def painting(base, cx, cy, w, h, seed):
    """A framed landscape scroll: gilt frame, silk ground, ridges, bamboo, seal."""
    d = ImageDraw.Draw(base)
    x0, y0 = cx - w / 2.0, cy - h / 2.0

    d.rectangle(box(x0 - px(2), y0 + px(3), x0 + w + px(5), y0 + h + px(7)),
                fill=(8, 8, 6, 140))
    d.rectangle(box(x0 - px(5), y0 - px(5), x0 + w + px(5), y0 + h + px(5)),
                fill=(96, 70, 30))
    d.rectangle(box(x0 - px(3), y0 - px(3), x0 + w + px(3), y0 + h + px(3)),
                fill=mix(GOLD, GOLD_L, 0.4))

    rnd = random.Random(seed)
    scene = Image.new("RGBA", (max(2, int(w)), max(2, int(h))))
    sd = ImageDraw.Draw(scene)
    for i in range(int(h)):
        t = i / max(1.0, h - 1)
        sd.line([(0, i), (w, i)], fill=mix((178, 174, 148), (110, 118, 96), t) + (255,))

    for base_y, tone in ((0.50, 0.28), (0.66, 0.42), (0.84, 0.58)):
        pts = [(0, h)]
        for i in range(9):
            tx = w * i / 8.0
            lift = 0.10 + 0.15 * rnd.random()
            ty = h * base_y - h * lift * (1 - abs(i - 4) / 6.0)
            pts.append((tx, ty))
        pts.append((w, h))
        sd.polygon(pts, fill=mix((136, 144, 118), (66, 74, 60), tone) + (255,))

    for _ in range(3):
        bx = rnd.uniform(0.12, 0.88) * w
        sd.line([(bx, h * 0.96), (bx + rnd.uniform(-px(6), px(6)), h * 0.20)],
                fill=(88, 102, 66, 255), width=max(1, int(px(0.7))))
        for j in range(4):
            ty = h * (0.30 + 0.14 * j)
            side = -1 if rnd.random() < 0.5 else 1
            sd.line([(bx, ty), (bx + side * px(7), ty - px(5))],
                    fill=(78, 92, 58, 255), width=1)
    sd.rectangle(box(w - px(9), h - px(9), w - px(4), h - px(4)), fill=(148, 44, 36, 255))

    base.paste(scene, (int(x0), int(y0)), scene)
    d.rectangle(box(x0, y0, x0 + w, y0 + h), outline=(58, 46, 28), width=max(1, int(px(1.0))))
    d.line([(x0, y0 + h), (x0 + w, y0 + h)], fill=(24, 20, 14), width=max(1, int(px(0.8))))


def sconce(base, x, y, seed):
    """A brass wall sconce: backplate, arm, shallow shade and its pool of light."""
    d = ImageDraw.Draw(base)
    r = random.Random(seed)
    d.rounded_rectangle(box(x - px(4), y - px(6), x + px(4), y + px(6)), radius=px(2),
                        fill=mix(BRASS, (92, 66, 30), 0.3))
    d.line([(x - px(1), y - px(4)), (x - px(1), y + px(4))],
           fill=mix(BRASS, GOLD_L, 0.4), width=max(1, int(px(0.6))))
    d.line([(x, y + px(5)), (x, y + px(13))], fill=(124, 94, 44),
           width=max(2, int(px(1.6))))
    d.line([(x - px(2), y + px(5)), (x - px(2), y + px(13))],
           fill=mix(BRASS, GOLD_L, 0.25), width=max(1, int(px(0.7))))
    d.polygon([(x - px(11), y + px(15)), (x - px(6), y + px(6)),
               (x + px(6), y + px(6)), (x + px(11), y + px(15))],
              fill=mix((134, 100, 46), WOOD_D, 0.1))
    d.line([(x - px(11), y + px(15)), (x + px(11), y + px(15))],
           fill=(220, 186, 112), width=max(1, int(px(1.0))))
    d.ellipse(box(x - px(4), y + px(13), x + px(4), y + px(19)), fill=(255, 228, 172))
    for k in range(3):
        yy = y + px(16) + k * px(3)
        d.line([(x - px(4) + k, yy), (x + px(4) - k, yy)],
               fill=(255, 214, 150, 120 - k * 30), width=1)
    _ = r
    lamp(x, y + px(16), px(62), (255, 208, 142), 150)


# ------------------------------------------------------------------- the door
def kitchen_door(base, cx):
    """Doors to the kitchen: warm light behind them, a red curtain over the frame."""
    d = ImageDraw.Draw(base)
    half = px(44)
    top = px(92)

    # the opening, lit from the kitchen so the room's one strong light is here
    d.rectangle(box(cx - half, top, cx + half, FLOOR_Y), fill=(52, 36, 24))
    for i in range(px(82)):
        t = i / float(px(82))
        d.line([(cx - half, top + i), (cx + half, top + i)],
               fill=mix((96, 64, 36), (176, 126, 66), t ** 0.8))

    for lx0, lx1, hinge in ((cx - half + px(2), cx - px(3), -1), (cx + px(3), cx + half - px(2), 1)):
        d.rectangle(box(lx0, top + px(4), lx1, FLOOR_Y), fill=mix(WOOD, WOOD_D, 0.08))
        grain_lines(d, lx0, top + px(8), lx1, FLOOR_Y - px(20), random.Random(int(lx0)), n=4, tone=0.4)
        # a glazed panel in each leaf, with muntins
        gx0, gx1 = lx0 + px(4), lx1 - px(4)
        gy0, gy1 = top + px(12), top + px(52)
        d.rectangle(box(gx0 - px(1), gy0 - px(1), gx1 + px(1), gy1 + px(1)), fill=(30, 22, 16))
        d.rectangle(box(gx0, gy0, gx1, gy1), fill=mix((214, 186, 138), (168, 130, 84), 0.3))
        d.line([(gx0, (gy0 + gy1) / 2), (gx1, (gy0 + gy1) / 2)], fill=(48, 34, 24),
               width=max(1, int(px(0.8))))
        d.line([((gx0 + gx1) / 2, gy0), ((gx0 + gx1) / 2, gy1)], fill=(48, 34, 24),
               width=max(1, int(px(0.8))))
        d.line([(gx0, gy0), (gx0, gy1)], fill=(236, 214, 172), width=max(1, int(px(0.6))))
        # brass handle and kick plate
        hx = lx1 - px(7) if hinge < 0 else lx0 + px(7)
        d.rounded_rectangle(box(hx - px(2), top + px(66), hx + px(2), top + px(78)),
                            radius=px(1.6), fill=mix(BRASS, GOLD_L, 0.35))
        d.rectangle(box(lx0 + px(2), FLOOR_Y - px(12), lx1 - px(2), FLOOR_Y - px(3)),
                    fill=mix(BRASS, (96, 70, 32), 0.45))

    # threshold and the light spilling onto the floor
    d.rectangle(box(cx - half - px(4), FLOOR_Y - px(3), cx + half + px(4), FLOOR_Y + px(4)),
                fill=(86, 62, 40))
    d.line([(cx - half - px(4), FLOOR_Y - px(3)), (cx + half + px(4), FLOOR_Y - px(3))],
           fill=(196, 162, 108), width=max(1, int(px(0.7))))

    # the curtain: a scalloped valance, then two panels tied back
    d.rectangle(box(cx - half - px(10), top - px(20), cx + half + px(10), top + px(4)),
                fill=mix(RED, (86, 22, 18), 0.25))
    for k in range(7):
        sx = cx - half - px(8) + k * (2 * (half + px(8)) / 7.0)
        d.polygon([(sx, top + px(2)), (sx + (2 * (half + px(8)) / 7.0) * 0.5, top + px(16)),
                   (sx + 2 * (half + px(8)) / 7.0, top + px(2))], fill=RED_L)
    d.line([(cx - half - px(10), top - px(20)), (cx + half + px(10), top - px(20))],
           fill=mix(GOLD, GOLD_L, 0.3), width=max(1, int(px(1.0))))
    for side in (-1, 1):
        px0 = cx + side * (half - px(2))
        px1 = cx + side * (half + px(24))
        d.rectangle(box(px0, top - px(16), px1, FLOOR_Y - px(26)), fill=mix(RED, (92, 24, 20), 0.2))
        for f in range(4):
            fx = px0 + (px1 - px0) * (f + 0.5) / 4.0
            d.line([(fx, top - px(12)), (fx, FLOOR_Y - px(28))],
                   fill=mix(RED, (58, 14, 12), 0.45), width=max(1, int(px(0.8))))
            d.line([(fx - px(1.4), top - px(12)), (fx - px(1.4), FLOOR_Y - px(28))],
                   fill=mix(RED_L, (210, 120, 96), 0.3), width=max(1, int(px(0.5))))
        d.rectangle(box(px0 - px(2), FLOOR_Y - px(34), px1 + px(2), FLOOR_Y - px(26)),
                    fill=mix(GOLD, GOLD_D, 0.3))
    lamp(cx, FLOOR_Y - px(66), px(210), (255, 200, 132), 120)
    lamp(cx, FLOOR_Y + px(6), px(150), (255, 196, 128), 54)


# ------------------------------------------------------------------ the dragon
def dragon_mural(base, cx):
    """A gold dragon on black lacquer, the room's centrepiece and its namesake."""
    w = px(200)
    half = w / 2.0
    top, bot = px(56), px(146)
    cy = (top + bot) / 2.0 + px(6)
    d = ImageDraw.Draw(base)

    # the panel
    d.rectangle(box(cx - half - px(8), top - px(8), cx + half + px(8), bot + px(8)),
                fill=mix(WOOD, WOOD_D, 0.35))
    d.rectangle(box(cx - half, top, cx + half, bot), fill=LACQUER)
    for i in range(px(24)):
        t = i / float(px(24))
        d.line([(cx - half, top + i), (cx + half, top + i)],
               fill=mix((46, 52, 46), LACQUER, t))
    for x0, y0, x1, y1 in ((cx - half, top, cx + half, top), (cx - half, bot, cx + half, bot)):
        d.line([(x0, y0), (x1, y1)], fill=mix(GOLD, GOLD_D, 0.35),
               width=max(1, int(px(1.0))))
    for x in (cx - half, cx + half):
        d.line([(x, top), (x, bot)], fill=mix(GOLD, GOLD_D, 0.35),
               width=max(1, int(px(1.0))))

    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    span = w * 0.78
    pts = []
    for i in range(0, 121):
        t = i / 120.0
        x = cx - span / 2.0 + span * t
        y = cy + math.sin(t * math.pi * 2.3 - 0.7) * px(15) * (1 - 0.3 * t)
        pts.append((x, y, t))

    def thick(t):
        return px(2.6) + px(5.4) * (math.sin(math.pi * min(1.0, t * 1.04)) ** 0.55)

    for i in range(len(pts) - 1):
        x0, y0, t0 = pts[i]
        x1, y1, _ = pts[i + 1]
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        w0, w1 = thick(t0), thick(min(1.0, t0 + 0.012))
        bd.polygon([(x0 + nx * w0, y0 + ny * w0), (x1 + nx * w1, y1 + ny * w1),
                    (x1 - nx * w1, y1 - ny * w1), (x0 - nx * w0, y0 - ny * w0)],
                   fill=GOLD)
        bd.line([(x0 - nx * w0 * 0.55, y0 - ny * w0 * 0.55), (x1 - nx * w1 * 0.55, y1 - ny * w1 * 0.55)],
                fill=GOLD_L, width=max(1, int(px(1.0))))
        bd.line([(x0 + nx * w0 * 0.72, y0 + ny * w0 * 0.72), (x1 + nx * w1 * 0.72, y1 + ny * w1 * 0.72)],
                fill=GOLD_D, width=max(1, int(px(0.9))))

    # dorsal fins and a mane along the spine
    for i in range(4, len(pts) - 6, 5):
        x, y, t = pts[i]
        fin = px(3.0) + px(3.4) * math.sin(math.pi * t)
        bd.polygon([(x - px(3), y - thick(t) * 0.7), (x, y - thick(t) - fin),
                    (x + px(4), y - thick(t) * 0.7)], fill=GOLD_D)
        bd.line([(x, y - thick(t)), (x, y - thick(t) - fin)], fill=GOLD_L,
                width=max(1, int(px(0.7))))

    # scales
    for i in range(6, len(pts) - 6, 3):
        x, y, t = pts[i]
        r = thick(t) * 0.42
        bd.arc(box(x - r, y - r * 0.5, x + r, y + r * 1.1), 190, 350, fill=GOLD_L,
               width=max(1, int(px(0.6))))

    # two forelegs, thick enough to hold the body up, ending in a paw of claws
    for t, up in ((0.30, 1), (0.60, -1)):
        i = int(t * 120)
        x, y, _ = pts[i]
        ax, ay = x, y + thick(t) * 0.35
        bx, by = x + px(11), y + px(17) * up
        ex, ey = x + px(22), y + px(26) * up
        bd.line([(ax, ay), (bx, by)], fill=GOLD, width=max(3, int(px(6.0))), joint="curve")
        bd.line([(bx, by), (ex, ey)], fill=GOLD, width=max(3, int(px(5.0))), joint="curve")
        bd.line([(ax, ay - px(2)), (bx, by - px(2)), (ex, ey - px(2))], fill=GOLD_L,
                width=max(2, int(px(1.6))), joint="curve")
        for k in (-1, 0, 1):
            bd.line([(ex, ey),
                     (ex + px(6) + k * px(2.4), ey + (px(7) + abs(k) * px(2.5)) * up)],
                    fill=GOLD_L, width=max(2, int(px(1.6))))

    # the head, at the right end, turning back over its own shoulder
    hx, hy, _ = pts[-1]
    r = px(11)
    bd.ellipse(box(hx - r, hy - r * 0.92, hx + r, hy + r * 0.92), fill=GOLD)
    bd.polygon([(hx + r * 0.2, hy - r * 0.5), (hx + r * 1.9, hy - r * 0.22),
                (hx + r * 1.9, hy + r * 0.3), (hx + r * 0.2, hy + r * 0.55)],
               fill=GOLD)
    bd.polygon([(hx + r * 0.3, hy + r * 0.42), (hx + r * 1.7, hy + r * 0.34),
                (hx + r * 1.6, hy + r * 1.15), (hx + r * 0.4, hy + r * 0.9)],
               fill=GOLD_D)
    for k in range(4):
        bd.line([(hx + r * (0.5 + 0.3 * k), hy + r * 0.5),
                 (hx + r * (0.5 + 0.3 * k), hy + r * 0.95)], fill=(250, 244, 220),
                width=max(1, int(px(0.6))))
    bd.line([(hx - r * 0.6, hy - r * 0.6), (hx - r * 1.9, hy - r * 2.0)], fill=GOLD_L,
            width=max(2, int(px(1.6))))
    bd.line([(hx - r * 0.2, hy - r * 0.9), (hx - r * 0.6, hy - r * 2.4)], fill=GOLD_L,
            width=max(2, int(px(1.4))))
    bd.line([(hx - r * 0.1, hy - r * 0.2), (hx - r * 2.4, hy - r * 0.5),
             (hx - r * 3.2, hy + r * 0.4)], fill=GOLD_L, width=max(1, int(px(1.0))))
    bd.line([(hx + r * 0.2, hy + r * 0.6), (hx - r * 2.2, hy + r * 1.2),
             (hx - r * 3.0, hy + r * 2.0)], fill=GOLD_L, width=max(1, int(px(1.0))))
    bd.ellipse(box(hx + r * 0.55, hy - r * 0.55, hx + r * 1.15, hy - r * 0.05),
               fill=(28, 22, 14))
    bd.ellipse(box(hx + r * 0.7, hy - r * 0.48, hx + r * 0.95, hy - r * 0.22),
               fill=(250, 246, 226))

    # cloud scrolls: a filled head with a curling tail, so they read as clouds
    # a cloud scroll is a spiral with a tail, not a disc: a filled disc read as a
    # bowl sitting on the panel
    for sx, sy, sr, flip in ((cx - w * 0.40, cy - px(30), px(11), 1),
                             (cx + w * 0.02, cy + px(30), px(13), -1),
                             (cx + w * 0.34, cy - px(26), px(9), 1)):
        for k, (rr, wd) in enumerate(((sr, px(2.1)), (sr * 0.56, px(1.5)))):
            oy = sy + flip * sr * 0.34 * k
            a0 = 205 + k * 45
            bd.arc(box(sx - rr, oy - rr * 0.74, sx + rr, oy + rr * 0.74),
                   a0, a0 + 255, fill=mix(GOLD, GOLD_D, 0.32), width=max(1, int(wd)))
        bd.line([(sx + sr * 1.05, sy - flip * sr * 0.15),
                 (sx + sr * 1.55, sy - flip * sr * 0.62),
                 (sx + sr * 2.05, sy - flip * sr * 0.5)],
                fill=mix(GOLD, GOLD_D, 0.45), width=max(1, int(px(1.1))), joint="curve")

    # the pearl, above and ahead of the head, the way the motif is always drawn
    pearl = px(15)
    prx, pry = hx + r * 0.2, hy - r * 2.9
    bd.ellipse(box(prx - pearl, pry - pearl * 0.9, prx + pearl, pry + pearl * 0.9),
               fill=mix(GOLD_L, (255, 248, 220), 0.45))
    bd.arc(box(prx - pearl, pry - pearl * 0.9, prx + pearl, pry + pearl * 0.9), 0, 360,
           fill=GOLD_D, width=max(1, int(px(1.0))))

    base.alpha_composite(body)
    d = ImageDraw.Draw(base)
    for k in (-1, 1):
        d.rectangle(box(cx + k * (half - px(8)) - px(5), bot + px(12),
                        cx + k * (half - px(8)) + px(5), bot + px(30)),
                    fill=mix(GOLD, GOLD_D, 0.45))
    lamp(cx, bot + px(20), px(150), (255, 196, 124), 62)


# ---------------------------------------------------------------------- the bar
def bar(base, x0, x1):
    """The bar: a lit back shelf of bottles, a counter, a brass rail and stools."""
    d = ImageDraw.Draw(base)
    shelf_top, shelf_bot = px(64), px(140)
    in0, in1 = x0 + px(10), x1 - px(10)

    d.rectangle(box(x0 - px(4), shelf_top - px(6), x1 + px(4), shelf_bot + px(6)),
                fill=mix(WOOD, WOOD_D, 0.26))
    d.rectangle(box(in0, shelf_top, in1, shelf_bot), fill=(30, 22, 16))
    for i in range(3):
        sy = shelf_top + px(12) + i * px(24)
        d.rectangle(box(in0, sy, in1, sy + px(4)), fill=mix(WOOD, WOOD_L, 0.24))
        d.line([(in0, sy), (in1, sy)], fill=(200, 166, 110), width=max(1, int(px(0.6))))
        rnd = random.Random(900 + i)
        bx = in0 + px(5)
        while bx < in1 - px(9):
            bw = rnd.uniform(px(4), px(7))
            bh = rnd.uniform(px(9), px(15))
            c = rnd.choice(((58, 84, 52), (126, 92, 44), (96, 40, 34), (44, 62, 78),
                            (150, 128, 60), (86, 108, 96)))
            d.rounded_rectangle(box(bx, sy - bh, bx + bw, sy), radius=px(1.4),
                                fill=mix(c, (18, 16, 14), 0.28))
            d.rectangle(box(bx + bw * 0.34, sy - bh - px(3), bx + bw * 0.66, sy - bh + px(1)),
                        fill=mix(c, (230, 220, 190), 0.32))
            d.line([(bx + px(0.9), sy - bh + px(1.5)), (bx + px(0.9), sy - px(1))],
                   fill=mix(c, (244, 230, 194), 0.34), width=max(1, int(px(0.5))))
            bx += bw + rnd.uniform(px(2), px(5))
        lamp((in0 + in1) / 2.0, sy + px(2), (in1 - in0) * 0.55, (255, 198, 132), 56)

    top_y = px(150)
    d.rectangle(box(x0 - px(10), top_y, x1 + px(10), top_y + px(8)),
                fill=mix(WOOD, WOOD_L, 0.38))
    d.line([(x0 - px(10), top_y), (x1 + px(10), top_y)], fill=(220, 190, 138),
           width=max(1, int(px(1.0))))
    d.line([(x0 - px(10), top_y + px(8)), (x1 + px(10), top_y + px(8))], fill=(24, 16, 12),
           width=max(1, int(px(1.2))))
    d.rectangle(box(x0 - px(4), top_y + px(8), x1 + px(4), FLOOR_Y),
                fill=mix(WOOD, WOOD_D, 0.14))
    rnd = random.Random(77)
    for x in range(int(x0 - px(4)), int(x1 + px(4)), int(px(32))):
        d.rectangle(box(x + px(4), top_y + px(16), x + px(28), FLOOR_Y - px(14)),
                    fill=mix(WOOD, WOOD_D, 0.26))
        d.line([(x + px(4), top_y + px(16)), (x + px(28), top_y + px(16))],
               fill=mix(WOOD, (160, 118, 72), 0.3), width=max(1, int(px(0.6))))
        grain_lines(d, x + px(6), top_y + px(20), x + px(26), FLOOR_Y - px(18), rnd, n=3)
    d.line([(x0 + px(2), FLOOR_Y - px(11)), (x1 - px(2), FLOOR_Y - px(11))],
           fill=mix(BRASS, GOLD_L, 0.35), width=max(2, int(px(2.0))))
    for x in range(int(x0), int(x1) + 1, int(px(26))):
        d.line([(x, FLOOR_Y - px(11)), (x, FLOOR_Y - px(6))], fill=mix(BRASS, GOLD_D, 0.4),
               width=max(1, int(px(0.9))))

    # what is on the counter: a register, glasses, a bottle and a small lamp
    reg_x = x0 + (x1 - x0) * 0.24
    d.rectangle(box(reg_x - px(11), top_y - px(16), reg_x + px(11), top_y), fill=(72, 62, 48))
    d.rectangle(box(reg_x - px(8), top_y - px(13), reg_x + px(8), top_y - px(5)), fill=(36, 34, 30))
    for k in range(3):
        d.rectangle(box(reg_x - px(6) + k * px(5), top_y - px(10), reg_x - px(3) + k * px(5), top_y - px(7)),
                    fill=(196, 176, 120))
    gx = x0 + (x1 - x0) * 0.56
    for k in range(5):
        d.polygon([(gx + k * px(6) - px(3), top_y), (gx + k * px(6) + px(3), top_y),
                   (gx + k * px(6) + px(2), top_y - px(9)), (gx + k * px(6) - px(2), top_y - px(9))],
                  fill=(178, 200, 196))
        d.line([(gx + k * px(6) - px(2), top_y - px(8)), (gx + k * px(6) + px(2), top_y - px(8))],
               fill=(232, 240, 236), width=1)
    for k, c in enumerate(((72, 96, 58), (128, 88, 40), (92, 36, 30))):
        bx = x0 + (x1 - x0) * 0.74 + k * px(9)
        d.rounded_rectangle(box(bx - px(4), top_y - px(22), bx + px(4), top_y), radius=px(1.6),
                            fill=mix(c, (20, 16, 14), 0.2))
        d.rectangle(box(bx - px(1.4), top_y - px(26), bx + px(1.4), top_y - px(21)),
                    fill=mix(c, (240, 226, 190), 0.25))
    lamp(x1 - px(18), top_y - px(10), px(90), (255, 202, 138), 96)

    for k in range(3):
        sx = x0 + (x1 - x0) * (0.20 + 0.30 * k)
        seat_y = FLOOR_Y - px(24)
        d.ellipse(box(sx - px(13), seat_y - px(5), sx + px(13), seat_y + px(6)),
                  fill=mix(WOOD, WOOD_D, 0.2))
        d.ellipse(box(sx - px(13), seat_y - px(8), sx + px(13), seat_y + px(2)),
                  fill=mix(WOOD, WOOD_L, 0.3))
        d.line([(sx - px(10), seat_y + px(4)), (sx - px(10), FLOOR_Y)], fill=mix(WOOD, WOOD_D, 0.3),
               width=max(1, int(px(1.4))))
        d.line([(sx + px(10), seat_y + px(4)), (sx + px(10), FLOOR_Y)], fill=mix(WOOD, WOOD_D, 0.3),
               width=max(1, int(px(1.4))))
        d.line([(sx - px(11), seat_y + px(12)), (sx + px(11), seat_y + px(12))],
               fill=mix(BRASS, GOLD_D, 0.4), width=max(1, int(px(1.0))))


def glass_wall(base, x0, x1):
    """A wall of glass block in a dark grid: cold light, to answer the lamps."""
    d = ImageDraw.Draw(base)
    top, bot = px(70), RAIL - px(4)
    d.rectangle(box(x0 - px(9), top - px(9), x1 + px(9), bot + px(9)), fill=mix(WOOD, WOOD_D, 0.3))
    d.rectangle(box(x0, top, x1, bot), fill=(46, 58, 54))
    cell = px(15)
    for r, gy in enumerate(range(int(top), int(bot), int(cell))):
        for c, gx in enumerate(range(int(x0), int(x1), int(cell))):
            k = 0.55 + 0.45 * abs(math.sin((r * 3 + c * 5) * 0.7))
            fill = mix((108, 132, 122), (206, 224, 204), k)
            d.rectangle(box(gx + px(1.6), gy + px(1.6), gx + cell - px(1.6), gy + cell - px(1.6)),
                        fill=fill)
            d.line([(gx + px(2.4), gy + cell - px(3.4)), (gx + cell - px(3.4), gy + px(2.4))],
                   fill=mix(fill, (255, 255, 255), 0.3), width=max(1, int(px(0.5))))
    for x in range(int(x0), int(x1) + 1, int(cell)):
        d.line([(x, top), (x, bot)], fill=mix(WOOD, WOOD_D, 0.2), width=max(1, int(px(1.0))))
    for y in range(int(top), int(bot) + 1, int(cell)):
        d.line([(x0, y), (x1, y)], fill=mix(WOOD, WOOD_D, 0.2), width=max(1, int(px(1.0))))
    d.line([(x0, top), (x0, bot)], fill=mix(WOOD, WOOD_L, 0.3), width=max(1, int(px(1.2))))
    lamp((x0 + x1) / 2.0, (top + bot) / 2.0, (x1 - x0) * 0.7, (198, 222, 214), 76)
    lamp((x0 + x1) / 2.0, FLOOR_Y + px(8), px(120), (190, 214, 206), 34)


# ---------------------------------------------------------------- the lanterns
def lanterns(base):
    """Red paper lanterns on the beam, each with its pool of warm light."""
    for i, x in enumerate((px(250), px(600), px(1160), px(1420), px(1760))):
        d = ImageDraw.Draw(base)
        cy = WALL_TOP + px(24)
        r = px(22)
        d.line([(x, WALL_TOP - px(12)), (x, cy - r * 0.9)], fill=(58, 42, 30),
               width=max(1, int(px(0.7))))
        d.ellipse(box(x - r, cy - r * 0.86, x + r, cy + r * 0.86), fill=mix(RED_L, (112, 26, 20), 0.28))
        d.ellipse(box(x - r * 0.9, cy - r * 0.8, x + r * 0.9, cy + r * 0.8), fill=(206, 74, 52))
        for k in range(-2, 3):
            d.line([(x + k * r * 0.34, cy - r * 0.78), (x + k * r * 0.34, cy + r * 0.78)],
                   fill=mix(RED, (104, 22, 16), 0.42), width=max(1, int(px(0.5))))
        for k in (-1, 1):
            d.rectangle(box(x - r * 0.34, cy + k * r * 0.8 - px(2), x + r * 0.34, cy + k * r * 0.8 + px(2)),
                        fill=mix(GOLD, GOLD_D, 0.25))
        d.line([(x, cy + r * 0.86), (x, cy + r * 1.3)], fill=mix(GOLD, GOLD_L, 0.3),
               width=max(1, int(px(0.8))))
        lamp(x, cy + px(4), px(118), (255, 180, 118), 120)


# --------------------------------------------------------------------- the floor
def floor(base):
    """The chequered stone floor of the reference: light and dark squares that
    grow towards the camera, with grout between them and a polished sheen."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, FLOOR_Y, W, H), fill=GRID)
    rnd = random.Random(13)
    y = FLOOR_Y
    row = 0
    while y < H:
        hgt = int(px(9) + row * px(3.6))
        tw = int(px(24) * (1 + row * 0.17))
        x = (CX % tw) - tw               # the squares line up on the room's centre
        col = 0
        while x < W:
            light = (row + col) % 2 == 0
            c = tint(tuple(int(v * (0.96 + 0.08 * rnd.random()))
                           for v in (FLOOR_L if light else FLOOR_D)), rnd, 0.04)
            d.rectangle(box(x + px(1.0), y + px(1.0), x + tw - px(1.0), y + hgt - px(1.0)),
                        fill=c)
            d.line([(x + px(1.4), y + px(1.5)), (x + tw - px(1.4), y + px(1.5))],
                   fill=mix(c, (255, 238, 202), 0.20 if light else 0.11),
                   width=max(1, int(px(0.5))))
            d.line([(x + px(1.4), y + hgt - px(1.5)), (x + tw - px(1.4), y + hgt - px(1.5))],
                   fill=mix(c, (14, 11, 8), 0.45), width=max(1, int(px(0.6))))
            d.line([(x + px(1.4), y + px(1.5)), (x + px(1.4), y + hgt - px(1.5))],
                   fill=mix(c, (18, 14, 10), 0.3), width=max(1, int(px(0.5))))
            if rnd.random() < 0.20:
                sx = x + rnd.uniform(px(3), max(px(4), tw - px(3)))
                sy = y + rnd.uniform(px(2), max(px(3), hgt - px(3)))
                d.line([(sx, sy), (sx + rnd.uniform(-px(7), px(7)),
                                   sy + rnd.uniform(px(1), px(5)))],
                       fill=mix(c, (38, 32, 24), 0.35), width=max(1, int(px(0.4))))
            x += tw
            col += 1
        y += hgt
        row += 1

    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    for x in range(0, W, px(90)):
        sd.line([(x, FLOOR_Y), (x + px(26), H)], fill=(255, 226, 176, 16),
                width=max(2, int(px(4))))
    base.alpha_composite(sheen.filter(ImageFilter.GaussianBlur(px(7))))


# ------------------------------------------------------------------ furniture
def chair(base, cx, base_y, w, seed):
    """A wooden chair from behind: posts, slats with gaps, a seat and legs.

    The first pass drew the chair in the same dark walnut as the wainscot behind
    it, so at this size it read as a pot standing on the skirting. The frame is
    now red lacquered as in the reference, with a lit edge, gold lines down the
    slats and a gold medallion on the back.
    """
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
        d.rectangle(box(sx - px(3), top_y + px(6), sx + px(3), seat_y - px(3)), fill=frame)
        d.line([(sx - px(3), top_y + px(6)), (sx - px(3), seat_y - px(3))],
               fill=mix(frame, GOLD, 0.45), width=max(1, int(px(0.7))))
        d.line([(sx + px(3), top_y + px(6)), (sx + px(3), seat_y - px(3))],
               fill=frame_d, width=max(1, int(px(0.9))))
    mid_y = top_y + (seat_y - top_y) * 0.5
    d.rectangle(box(cx - w * 0.50, mid_y, cx + w * 0.52, mid_y + px(4)),
                fill=mix(RED, RED_L, 0.3))
    # the gold medallion on the back rail, with a cloud scroll inside it
    mr = w * 0.15
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


def banner(base, cx, top, w, h, seed):
    """A red temple banner: brass rod, cloth with a gold border and a medallion.

    Hung high on the wall like the red cloth in the reference, so it clears the
    tables and never reaches the fighters.
    """
    d = ImageDraw.Draw(base)
    left, right = cx - w / 2.0, cx + w / 2.0

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle(box(left + px(3), top + px(6), right + px(8), top + h + px(5)),
                 fill=(12, 10, 8, 120))
    base.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(px(4))))

    rows = 16
    edge = []
    for i in range(rows + 1):
        t = i / float(rows)
        sway = math.sin(t * 2.2 + seed) * px(3.5) * t
        edge.append((top + px(4) + h * t, left + sway, right + sway * 0.6))
    for i in range(rows):
        y0, l0, r0 = edge[i]
        y1, l1, r1 = edge[i + 1]
        d.polygon([(l0, y0), (r0, y0), (r1, y1), (l1, y1)],
                  fill=mix(RED, (92, 24, 20), 0.3 + 0.08 * (i % 2)))
    for k in (-0.62, -0.2, 0.22, 0.6):
        d.line([(l + (r - l) * (0.5 + k * 0.5), y) for y, l, r in edge],
               fill=mix(RED, (66, 15, 12), 0.5), width=max(1, int(px(0.9))))
    for k in (0.0, 1.0):
        d.line([(l + (r - l) * k, y) for y, l, r in edge],
               fill=mix(GOLD, GOLD_D, 0.25), width=max(1, int(px(1.2))))
    y_end, l_end, r_end = edge[-1]
    d.line([(l_end, y_end), (r_end, y_end)], fill=mix(GOLD_L, GOLD, 0.4),
           width=max(2, int(px(1.6))))

    d.rectangle(box(left - px(4), top, right + px(4), top + px(4)),
                fill=mix(BRASS, GOLD_D, 0.3))
    d.line([(left - px(4), top), (right + px(4), top)], fill=(216, 180, 110),
           width=max(1, int(px(0.6))))

    my = top + px(4) + h * 0.36
    mr = w * 0.26
    d.ellipse(box(cx - mr, my - mr * 0.8, cx + mr, my + mr * 0.8),
              fill=mix(GOLD, GOLD_D, 0.3))
    d.arc(box(cx - mr, my - mr * 0.8, cx + mr, my + mr * 0.8), 0, 360,
          fill=(248, 224, 164), width=max(1, int(px(0.7))))
    for k in range(2):
        rr = mr * (0.66 - 0.22 * k)
        d.arc(box(cx - rr, my - rr * 0.7, cx + rr, my + rr * 0.7), 190 + k * 40,
              190 + k * 40 + 250, fill=mix(GOLD_D, RED, 0.4), width=max(1, int(px(0.6))))


def place_setting(d, cx, cy, r, rnd):
    """One cover: plate, cup, chopsticks and a dish of food."""
    d.ellipse(box(cx - r, cy - r * 0.42, cx + r, cy + r * 0.42), fill=(204, 200, 182))
    d.ellipse(box(cx - r * 0.86, cy - r * 0.34, cx + r * 0.86, cy + r * 0.34),
              fill=(234, 230, 214))
    d.arc(box(cx - r, cy - r * 0.42, cx + r, cy + r * 0.42), 0, 360, fill=(176, 172, 156),
          width=max(1, int(px(0.6))))
    d.ellipse(box(cx - r * 0.42, cy - r * 0.2, cx + r * 0.42, cy + r * 0.22),
              fill=mix(rnd.choice(((198, 118, 68), (206, 168, 88), (128, 146, 92))),
                       (226, 220, 200), 0.25))
    d.ellipse(box(cx + r * 0.72, cy - r * 0.52, cx + r * 1.28, cy + r * 0.10),
              fill=(238, 234, 220))
    d.arc(box(cx + r * 0.72, cy - r * 0.52, cx + r * 1.28, cy + r * 0.10), 0, 360,
          fill=(186, 182, 166), width=max(1, int(px(0.5))))
    for k in (0, 1):
        d.line([(cx - r * 1.5, cy + r * 0.3 + k * px(1.6)), (cx - r * 0.7, cy + r * 0.2 + k * px(1.6))],
               fill=(196, 170, 124), width=max(1, int(px(0.6))))


def round_table(base, cx, base_y, r, seed):
    """A round table in a white cloth, laid with the covers still out."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(seed)
    d.ellipse(box(cx - r * 1.06, base_y - px(7), cx + r * 1.06, base_y + px(9)),
              fill=(18, 12, 8, 130))

    skirt = base_y - r * 0.42
    d.polygon([(cx - r, skirt), (cx + r, skirt), (cx + r * 0.88, base_y),
               (cx - r * 0.88, base_y)], fill=CLOTH_D)
    for i in range(9):
        fx = cx - r + 2 * r * i / 8.0
        d.line([(fx, skirt), (cx + (fx - cx) * 0.9, base_y)],
               fill=mix(CLOTH_D, (138, 132, 116), 0.5), width=max(1, int(px(0.7))))
    d.ellipse(box(cx - r, skirt - r * 0.38, cx + r, skirt + r * 0.38), fill=CLOTH)
    d.ellipse(box(cx - r * 0.95, skirt - r * 0.32, cx + r * 0.95, skirt + r * 0.26),
              fill=mix(CLOTH, (255, 255, 250), 0.22))
    d.arc(box(cx - r, skirt - r * 0.38, cx + r, skirt + r * 0.38), 0, 360,
          fill=(186, 182, 166), width=max(1, int(px(0.7))))

    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.4
        place_setting(d, cx + math.cos(a) * r * 0.5, skirt + math.sin(a) * r * 0.18,
                      r * 0.26, rnd)
    d.ellipse(box(cx - r * 0.24, skirt - r * 0.2, cx + r * 0.24, skirt + r * 0.14),
              fill=(226, 220, 202))
    d.ellipse(box(cx - r * 0.16, skirt - r * 0.16, cx + r * 0.16, skirt + r * 0.06),
              fill=mix((176, 60, 44), (232, 216, 190), 0.3))


def square_table(base, cx, base_y, w, seed):
    """The same table square, cloth hanging square at the corners."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(seed)
    half = w / 2.0
    d.ellipse(box(cx - half * 1.06, base_y - px(7), cx + half * 1.06, base_y + px(9)),
              fill=(18, 12, 8, 130))
    skirt = base_y - w * 0.22
    d.polygon([(cx - half, skirt), (cx + half, skirt), (cx + half * 0.88, base_y),
               (cx - half * 0.88, base_y)], fill=CLOTH_D)
    for i in range(7):
        fx = cx - half + 2 * half * i / 6.0
        d.line([(fx, skirt), (cx + (fx - cx) * 0.9, base_y)],
               fill=mix(CLOTH_D, (138, 132, 116), 0.5), width=max(1, int(px(0.7))))
    d.rectangle(box(cx - half, skirt - w * 0.22, cx + half, skirt + w * 0.16), fill=CLOTH)
    d.rectangle(box(cx - half * 0.94, skirt - w * 0.18, cx + half * 0.94, skirt + w * 0.11),
                fill=mix(CLOTH, (255, 255, 250), 0.2))
    d.line([(cx - half, skirt - w * 0.22), (cx + half, skirt - w * 0.22)], fill=(240, 236, 220),
           width=max(1, int(px(0.7))))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        place_setting(d, cx + math.cos(a) * half * 0.52, skirt - w * 0.05 + math.sin(a) * w * 0.06,
                      w * 0.13, rnd)
    d.ellipse(box(cx - w * 0.1, skirt - w * 0.1, cx + w * 0.1, skirt + w * 0.02),
              fill=(226, 220, 202))


def table_bay(base, cx, seed, r=px(58), square=False):
    """A table pushed back to the wall with its chairs behind and beside it."""
    base_y = FLOOR_Y - px(2)
    chair(base, cx - r * 1.5, base_y - px(3), r * 0.62, seed + 1)
    chair(base, cx + r * 1.5, base_y - px(3), r * 0.62, seed + 2)
    chair(base, cx - r * 0.55, base_y - px(6), r * 0.56, seed + 3)
    if square:
        square_table(base, cx, base_y, r * 1.5, seed)
    else:
        round_table(base, cx, base_y, r, seed)


# ------------------------------------------------------------------- the front
def foreground():
    """The camera's own table: a cloth corner and a chair back at either end."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(53)
    for i in range(px(44)):
        a = int(158 * (1 - i / float(px(44))) ** 1.7)
        d.line([(0, H - i), (W, H - i)], fill=(24, 15, 10, a))
    for cx in (px(230), px(1600)):
        d.polygon([(cx - px(130), H), (cx + px(130), H), (cx + px(160), H - px(58)),
                   (cx - px(150), H - px(50))], fill=CLOTH + (238,))
        d.polygon([(cx - px(130), H), (cx + px(130), H), (cx + px(134), H - px(20)),
                   (cx - px(126), H - px(20))], fill=CLOTH_D + (238,))
        for k in range(9):
            fx = cx - px(126) + k * px(30)
            d.line([(fx, H - px(20)), (fx + px(2), H)], fill=mix(CLOTH_D, (140, 134, 118), 0.5) + (150,),
                   width=max(1, int(px(1.0))))
        place_setting(d, cx + px(40), H - px(26), px(26), rnd)
    for _ in range(90):
        x = rnd.uniform(0, W)
        y = H - rnd.uniform(px(10), px(90))
        r = rnd.uniform(px(1), px(3))
        d.ellipse(box(x - r, y - r, x + r, y + r), fill=(255, 214, 160, rnd.randint(24, 70)))
    return fg.filter(ImageFilter.GaussianBlur(px(1.4)))


# -------------------------------------------------------------------- the arena
def paint():
    LIGHTS.clear()
    base = hd.blank([(0, (18, 15, 13)), (WALL_TOP, (42, 42, 34)),
                     (RAIL, (60, 54, 42)), (FLOOR_Y, (58, 44, 32)),
                     (H, (32, 24, 18))])

    ceiling(base)
    wallpaper(base)
    wainscot(base)
    for x in range(0, W + px(1), px(260)):
        pilaster(base, x)

    painting(base, px(130), px(84), px(112), px(52), 11)
    painting(base, px(650), px(84), px(112), px(52), 12)
    painting(base, px(1690), px(84), px(112), px(52), 13)
    for i, x in enumerate((px(130), px(330), px(560), px(650), px(1690))):
        sconce(base, x, px(126), 300 + i)

    kitchen_door(base, DOOR_CX)
    dragon_mural(base, MURAL_CX)
    bar(base, BAR_X0, BAR_X1)
    glass_wall(base, GLASS_X0, GLASS_X1)
    lanterns(base)
    for i, (bx, bh) in enumerate(((px(60), px(74)), (px(1585), px(66)),
                                  (px(1770), px(78)))):
        banner(base, bx, px(56), px(30), bh, 7 + i)

    floor(base)
    table_bay(base, px(130), 41)
    table_bay(base, px(650), 42, r=px(40), square=True)
    table_bay(base, px(1690), 43, r=px(50))

    base = hd.shade(base, [(hd.light(cx, cy, r, col, peak), max(8, int(r * 0.34)), 1.1)
                           for cx, cy, r, col, peak in LIGHTS])
    base = art.vignette(base, 0.44)
    base = art.grain(base, 3, seed=53)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


def main():
    hd.STAGES["dragon_restaurant"] = ("Inside Dragon of the Black Pool Restaurant", paint)
    hd.build("dragon_restaurant")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
