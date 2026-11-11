"""The Buddha Garden: a temple garden at night, lit by stone lanterns.

Painted from the top-down garden reference: a stone pavilion with a blue tiled
roof and a warm-lit altar, a round moon gate in a mossy wall, a seated Buddha on
a lotus plinth in a lit niche, a pool with a curved stone footbridge under
bamboo, and flagstones running between beds of flowers.

The reference is a plan seen from above and a stage here is seen across the play
plane, so the garden is laid out as a courtyard rather than copied as a map: the
same furniture is spread across the 8192-wide canvas, and what would be underfoot
in the plan is painted on the floor plane the fighters stand on.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960 (nothing painted in the play plane blocks the fighters' feet),
localcoord 1920x1080, camera travel +/-3136. Group 3 is the foreground layer and
is drawn in front of the fighters.

Run:  python3 tools/stage_buddha_garden.py     (part of tools/build_all.py)
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

WALL_TOP = px(56)                # 252: top of the garden wall
COPING = px(7)
GATE_CX, GATE_R = px(640), px(58)          # 2880, 261
SHRINE_CX, SHRINE_TOP = CX, px(80)         # 4096, 360
PAVILION_CX = px(330)                      # 1485
WATER_X0, WATER_X1 = px(1240), px(1750)    # 5580 - 7875: the pool
BED_Y0 = FLOOR_Y - px(22)                  # 900 - the beds sit on the wall base

NIGHT_HIGH = (8, 14, 22)
NIGHT_LOW = (28, 46, 44)
STONE = (104, 106, 96)
STONE_DARK = (62, 66, 58)
MOSS = (52, 78, 42)
LEAF = (30, 54, 32)
LEAF_LIT = (74, 108, 54)
LEAF_DARK = (16, 32, 20)
TILE = (44, 70, 92)
TILE_LIT = (74, 104, 128)
TILE_DARK = (22, 36, 50)
GOLD = (238, 192, 106)
LAMP = (255, 214, 146)
WATER = (14, 28, 32)
SOIL = (34, 27, 22)
STONE_FIG = (116, 112, 98)
FIG_RIM = (236, 200, 140)

# every warm source is collected here while the garden is painted and blended in
# once at the end, so a lantern lights the stone around it instead of sitting on
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


def lamp(cx, cy, r, color=LAMP, peak=150):
    LIGHTS.append((cx, cy, r, color, peak))


# --------------------------------------------------------------------- the sky
def night(base):
    """Sky above the wall: stars, a low moon and haze off the garden."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(4)
    for _ in range(560):
        x, y = rnd.randint(0, W), rnd.randint(0, WALL_TOP - px(4))
        r = 1 if rnd.random() < 0.82 else 2
        a = rnd.randint(90, 190)
        d.ellipse(box(x - r, y - r, x + r, y + r),
                  fill=(int(196 * a / 190), int(212 * a / 190), int(232 * a / 190)))

    mx, my = px(250), px(30)
    moon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(moon)
    md.ellipse(box(mx - px(22), my - px(22), mx + px(22), my + px(22)),
               fill=(236, 240, 236, 200))
    md.ellipse(box(mx - px(30), my - px(30), mx + px(30), my + px(30)),
               fill=(200, 220, 232, 24))
    base.alpha_composite(moon.filter(ImageFilter.GaussianBlur(px(1.4))))
    lamp(mx, my, px(210), (176, 204, 218), 104)


def haze(base):
    """A band of damp air sitting on the wall top, so the sky meets it softly."""
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(band)
    for i in range(px(26)):
        a = int(38 * (1 - i / float(px(26))) ** 1.4)
        d.line([(0, WALL_TOP - px(20) + i), (W, WALL_TOP - px(20) + i)],
               fill=(150, 176, 176, a))
    base.alpha_composite(band.filter(ImageFilter.GaussianBlur(px(3))))


def canopy(base, cx, width, seed, top=None):
    """Foliage over the wall: dark leaf masses breaking the roof line."""
    rnd = random.Random(seed)
    d = ImageDraw.Draw(base)
    top = px(30) if top is None else top
    bottom = WALL_TOP + px(4)
    for _ in range(int(width / px(7))):
        x = cx + rnd.uniform(-width / 2, width / 2)
        spread = 1 - abs(x - cx) / (width * 0.62)
        if spread <= 0:
            continue
        y = rnd.uniform(top, bottom - px(26) * spread)
        r = rnd.uniform(px(7), px(20)) * (0.55 + 0.45 * spread)
        d.ellipse(box(x - r, y - r * 0.8, x + r, y + r * 0.8),
                  fill=tint(LEAF_DARK if rnd.random() < 0.6 else LEAF, rnd, 0.2))
    for _ in range(int(width / px(18))):
        x = cx + rnd.uniform(-width / 2, width / 2)
        spread = 1 - abs(x - cx) / (width * 0.62)
        if spread <= 0:
            continue
        y = rnd.uniform(top + px(8), top + px(36) + px(16) * spread)
        r = rnd.uniform(px(2), px(7))
        d.ellipse(box(x - r, y - r * 0.7, x + r, y + r * 0.7),
                  fill=tint((48, 78, 46), rnd, 0.2))


def bamboo(base, cx, seed, count=9, spread=px(120), top=None, base_y=None):
    """A clump of bamboo: jointed stalks with leaf sprays at the top."""
    rnd = random.Random(seed)
    d = ImageDraw.Draw(base)
    top = WALL_TOP - px(44) if top is None else top
    base_y = FLOOR_Y - px(26) if base_y is None else base_y
    for _ in range(count):
        x = cx + rnd.uniform(-spread, spread)
        lean = rnd.uniform(-px(8), px(8))
        colour = tint((54, 84, 46), rnd, 0.18)
        w = max(2, int(px(1.4) + rnd.random() * px(1.3)))
        d.line([(x, base_y), (x + lean * 0.4, (base_y + top) / 2), (x + lean, top)],
               fill=colour, width=w)
        for t in (0.18, 0.36, 0.54, 0.72, 0.88):
            ny = base_y + (top - base_y) * t
            nx = x + lean * t * 0.9
            d.line([(nx - w, ny), (nx + w, ny)], fill=mix(colour, (16, 22, 16), 0.5),
                   width=max(1, int(px(0.5))))
        for _k in range(9):
            t = rnd.uniform(0.32, 1.0)
            lx = x + lean * t
            ly = base_y + (top - base_y) * t
            ang = rnd.uniform(-2.7, -0.4)
            ln = rnd.uniform(px(5), px(13))
            tipx = lx + math.cos(ang) * ln
            tipy = ly + math.sin(ang) * ln
            d.line([(lx, ly), (tipx, tipy)], fill=tint(LEAF, rnd, 0.25),
                   width=max(1, int(px(0.45))))
            for f in (0.55, 0.82, 1.0):
                ex = lx + (tipx - lx) * f
                ey = ly + (tipy - ly) * f
                r = px(1.7)
                d.ellipse(box(ex - r, ey - r * 0.55, ex + r, ey + r * 0.55),
                          fill=tint(LEAF_LIT, rnd, 0.3))


# ------------------------------------------------------------------ the garden
def stone_courses(base, rnd, y0, y1, block_h=None, tone=1.0, mossy=0.42):
    """A wall of dressed stone: courses of blocks with moss in the joints."""
    d = ImageDraw.Draw(base)
    block_h = block_h or px(7)
    y = y0
    while y < y1:
        h = block_h + rnd.randint(-px(0.4), px(0.4))
        x = -rnd.randint(0, px(22))
        while x < W:
            w = rnd.randint(px(13), px(32))
            c = tint(tuple(int(v * tone) for v in STONE), rnd, 0.07)
            d.rectangle(box(x + px(0.7), y + px(0.7), x + w - px(0.7), y + h - px(0.7)),
                        fill=c)
            d.line([(x + px(1.2), y + px(1.2)), (x + w - px(1.2), y + px(1.2))],
                   fill=mix(c, (255, 244, 216), 0.1), width=max(1, int(px(0.4))))
            d.line([(x + px(1.2), y + h - px(1.2)), (x + w - px(1.2), y + h - px(1.2))],
                   fill=mix(c, (12, 16, 14), 0.34), width=max(1, int(px(0.5))))
            if rnd.random() < mossy:
                mx = x + rnd.uniform(0, w)
                r = rnd.uniform(px(2), px(4.6))
                d.ellipse(box(mx - r, y + h - r, mx + r, y + h + r * 0.5),
                          fill=tint(MOSS, rnd, 0.2))
            x += w
        y += h


def vines(base, rnd):
    """Ivy coming over the coping and hanging down the wall in thin strands."""
    d = ImageDraw.Draw(base)
    for _ in range(180):
        x = rnd.randint(-px(20), W)
        top = WALL_TOP + rnd.randint(0, px(10))
        length = rnd.randint(px(12), px(70))
        pts = [(x, top)]
        for i in range(1, 7):
            pts.append((x + math.sin(i * 0.8 + x * 0.01) * px(2.2) + rnd.uniform(-px(0.8), px(0.8)),
                        top + length * i / 6.0))
        d.line(pts, fill=tint((44, 68, 40), rnd, 0.24), width=max(1, int(px(0.4))))
        for i in range(1, 7):
            lx, ly = pts[i]
            for _l in range(2):
                r = px(0.9) + rnd.random() * px(0.9)
                ox = lx + rnd.uniform(-px(2.4), px(2.4))
                oy = ly + rnd.uniform(-px(1.6), px(1.6))
                d.ellipse(box(ox - r, oy - r, ox + r, oy + r),
                          fill=tint(LEAF_LIT if rnd.random() < 0.5 else LEAF, rnd, 0.3))


def wall(base):
    """The garden wall: courses, coping, string course, piers and damp at the base."""
    stone_courses(base, random.Random(9), WALL_TOP, FLOOR_Y)

    d = ImageDraw.Draw(base)
    course_y = WALL_TOP + int((FLOOR_Y - WALL_TOP) * 0.34)
    d.rectangle(box(0, course_y, W, course_y + px(8)), fill=(112, 114, 104))
    d.line([(0, course_y), (W, course_y)], fill=(158, 160, 146), width=max(1, int(px(0.6))))
    d.line([(0, course_y + px(8)), (W, course_y + px(8))], fill=(54, 58, 50),
           width=max(1, int(px(0.8))))

    d.rectangle(box(0, WALL_TOP - COPING, W, WALL_TOP), fill=(66, 72, 70))
    for x in range(-px(6), W, px(6)):
        d.arc(box(x, WALL_TOP - px(9), x + px(9), WALL_TOP + px(1)), 190, 350,
              fill=(120, 126, 120), width=max(1, int(px(0.55))))
    d.line([(0, WALL_TOP - COPING), (W, WALL_TOP - COPING)],
           fill=(146, 154, 148), width=max(1, int(px(0.5))))

    # piers, the same stone as the wall so they read as structure, not stripes
    for x in range(px(40), W, px(240)):
        d.rectangle(box(x, WALL_TOP - COPING, x + px(24), FLOOR_Y), fill=(112, 112, 102))
        d.rectangle(box(x + px(2), WALL_TOP - COPING, x + px(22), FLOOR_Y),
                    fill=(104, 104, 94))
        d.line([(x, WALL_TOP - COPING), (x, FLOOR_Y)], fill=(70, 74, 66),
               width=max(1, int(px(0.7))))
        d.line([(x + px(24), WALL_TOP - COPING), (x + px(24), FLOOR_Y)],
               fill=(148, 150, 136), width=max(1, int(px(0.6))))
        d.rectangle(box(x - px(4), course_y - px(4), x + px(28), course_y + px(12)),
                    fill=(126, 126, 114))

    vines(base, random.Random(17))

    damp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(damp)
    for i in range(px(18)):
        a = int(104 * (1 - i / float(px(18))) ** 1.6)
        dd.line([(0, FLOOR_Y - px(16) + i), (W, FLOOR_Y - px(16) + i)],
                fill=(10, 18, 14, a))
    base.alpha_composite(damp)


def wall_lantern(base, x, y, seed):
    """A small bronze lantern on the wall: bracket, glowing pane, little roof."""
    rnd = random.Random(seed)
    d = ImageDraw.Draw(base)
    d.line([(x, y), (x + px(15), y)], fill=(46, 38, 28), width=max(2, int(px(1.4))))
    d.rectangle(box(x + px(7), y - px(9), x + px(21), y + px(9)),
                fill=tint((66, 58, 40), rnd, 0.06))
    d.rectangle(box(x + px(9), y - px(5), x + px(19), y + px(6)),
                fill=(255, 216, 148))
    d.polygon([(x + px(5), y - px(9)), (x + px(14), y - px(18)),
               (x + px(23), y - px(9))], fill=(50, 42, 32))
    lamp(x + px(14), y + px(1), px(36), (255, 206, 140), 120)


def moon_gate(base, cx, r, cy):
    """A round gate of dressed stone around a lit slice of the garden beyond."""
    d = ImageDraw.Draw(base)
    outer = r + px(10)

    # the stone ring: filled, then cut into blocks by radial joints
    d.ellipse(box(cx - outer, cy - outer, cx + outer, cy + outer), fill=(100, 102, 92))
    for i in range(24):
        a = math.radians(i * 15)
        d.line([(cx + math.cos(a) * r, cy + math.sin(a) * r),
                (cx + math.cos(a) * outer, cy + math.sin(a) * outer)],
               fill=(70, 74, 66), width=max(1, int(px(0.9))))
    d.arc(box(cx - outer, cy - outer, cx + outer, cy + outer), 0, 360,
          fill=(126, 130, 118), width=max(1, int(px(1.4))))

    # what is beyond: a deep garden, kept dark so the gate reads as an opening
    seen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(seen)
    sd.ellipse(box(cx - r, cy - r, cx + r, cy + r), fill=(16, 28, 22, 255))
    for i in range(px(40)):
        t = i / float(px(40))
        sd.line([(cx - r, cy + r - i), (cx + r, cy + r - i)],
                fill=mix((28, 44, 34), (8, 14, 12), t))

    # a stepped path running away from the gate, narrowing
    sd.polygon([(cx - r * 0.92, cy + r), (cx - r * 0.14, cy + r * 0.24),
                (cx + r * 0.14, cy + r * 0.24), (cx + r * 0.92, cy + r)],
               fill=(74, 68, 54, 255))
    for i in range(7):
        t = i / 7.0
        y = cy + r - (r * 0.76) * t
        wdt = r * (0.92 - 0.78 * t)
        sd.line([(cx - wdt, y), (cx + wdt, y)], fill=(96, 88, 68, 255),
                width=max(1, int(px(0.8))))

    # bamboo canes at the sides, a low hedge behind them
    for side in (-1, 1):
        for k in range(4):
            lx = cx + side * r * (0.42 + k * 0.16)
            sd.line([(lx, cy + r * 0.9), (lx + side * px(3), cy - r * 0.9)],
                    fill=(46, 66, 42, 255), width=max(2, int(px(1.2))))
            for j in range(6):
                ly = cy + r * 0.8 - j * r * 0.3
                sd.line([(lx, ly), (lx - side * px(12), ly - px(5))],
                        fill=(56, 78, 48, 255), width=max(1, int(px(0.7))))
    for i in range(10):
        bx = cx - r * 0.9 + i * (r * 0.2)
        rr = px(13)
        sd.ellipse(box(bx - rr, cy + r * 0.62, bx + rr, cy + r * 0.62 + rr * 1.4),
                   fill=(30, 50, 34, 255))

    # a stone lantern part way down the path, with its pool of light
    ly = cy + r * 0.44
    sd.rectangle(box(cx - px(5), ly, cx + px(5), ly + px(30)), fill=(112, 108, 94, 255))
    sd.rectangle(box(cx - px(9), ly - px(14), cx + px(9), ly), fill=(255, 226, 168, 255))
    sd.polygon([(cx - px(13), ly - px(14)), (cx, ly - px(24)), (cx + px(13), ly - px(14))],
               fill=(84, 80, 68, 255))

    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse(box(cx - r, cy - r, cx + r, cy + r), fill=255)
    base.paste(seen, (0, 0), mask)

    d = ImageDraw.Draw(base)
    d.arc(box(cx - r, cy - r, cx + r, cy + r), 0, 360, fill=(34, 42, 36),
          width=max(2, int(px(1.8))))
    d.rectangle(box(cx - r - px(18), FLOOR_Y - px(5), cx + r + px(18), FLOOR_Y + px(5)),
                fill=(110, 112, 100))
    d.line([(cx - r - px(18), FLOOR_Y - px(5)), (cx + r + px(18), FLOOR_Y - px(5))],
           fill=(152, 156, 142), width=max(1, int(px(0.6))))
    lamp(cx, cy + r * 0.5, px(110), (255, 210, 150), 58)


def seated_buddha(base, cx, floor_y, height):
    """A seated Buddha: one silhouette, shaded, outlined and rimmed, with a halo.

    A plain fill left the head, shoulders and lap as a single grey shape, so the
    figure is drawn on its own layer: at this size the statue reads by its
    outline and its lit edge, not by its fill.
    """
    fig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fig)
    top = floor_y - height
    r = height * 0.135
    head_cy = top + r * 1.15
    sh_cy = top + height * 0.42
    waist_cy = top + height * 0.64
    lap_cy = top + height * 0.83
    shoulder = height * 0.30
    waist = height * 0.22
    lap_rx = height * 0.37

    # halo rings behind the head
    for rr, col in ((r * 2.62, (144, 110, 54)), (r * 2.36, (186, 146, 76)),
                    (r * 2.12, (226, 182, 106))):
        d.ellipse(box(cx - rr, head_cy - rr, cx + rr, head_cy + rr), outline=col,
                  width=max(2, int(px(2.0))))

    d.ellipse(box(cx - lap_rx, lap_cy - height * 0.10,
                  cx + lap_rx, lap_cy + height * 0.12), fill=STONE_FIG)
    d.polygon([(cx - shoulder, sh_cy), (cx - waist, waist_cy),
               (cx + waist, waist_cy), (cx + shoulder, sh_cy)], fill=STONE_FIG)
    d.ellipse(box(cx - shoulder, sh_cy - height * 0.085,
                  cx + shoulder, sh_cy + height * 0.085), fill=STONE_FIG)
    for side in (-1, 1):
        d.line([(cx + side * shoulder * 0.88, sh_cy + height * 0.04),
                (cx + side * waist * 1.12, waist_cy),
                (cx + side * height * 0.14, lap_cy - height * 0.02)],
               fill=STONE_FIG, width=int(max(3, height * 0.08)), joint="curve")
    d.rectangle(box(cx - r * 0.6, head_cy + r * 0.55, cx + r * 0.6, sh_cy),
                fill=STONE_FIG)
    d.ellipse(box(cx - height * 0.11, lap_cy - height * 0.055,
                  cx + height * 0.11, lap_cy + height * 0.02), fill=(132, 128, 112))
    d.ellipse(box(cx - r, head_cy - r, cx + r, head_cy + r), fill=STONE_FIG)
    d.ellipse(box(cx - r * 0.42, head_cy - r * 1.34, cx + r * 0.42, head_cy - r * 0.86),
              fill=STONE_FIG)
    for side in (-1, 1):
        d.ellipse(box(cx + side * r * 0.97 - r * 0.12, head_cy - r * 0.04,
                      cx + side * r * 0.97 + r * 0.12, head_cy + r * 0.62),
                  fill=STONE_FIG)

    # shadow falling to the right, in soft steps rather than one hard edge
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    steps = 48
    for i in range(steps):
        a = int(88 * (i / float(steps)) ** 1.4)
        x0 = cx - height * 0.02 + (height * 0.46) * i / steps
        sd.rectangle(box(x0, 0, x0 + height * 0.46 / steps + 1, H),
                     fill=(14, 12, 10, a))
    shade.putalpha(ImageChops.multiply(shade.split()[3], fig.split()[3]))
    fig.alpha_composite(shade)

    # robe hem and folds
    d = ImageDraw.Draw(fig)
    d.arc(box(cx - lap_rx, lap_cy - height * 0.10, cx + lap_rx, lap_cy + height * 0.12),
          200, 340, fill=(96, 92, 80), width=max(1, int(px(1.6))))
    for off in (-0.05, 0.06):
        d.line([(cx + height * off, sh_cy + height * 0.05),
                (cx + height * (off + 0.02), waist_cy + height * 0.04)],
               fill=(98, 94, 82), width=max(1, int(px(1.2))))

    mask = fig.split()[3]
    fig.alpha_composite(art.outline(mask, (40, 36, 30), thickness=2))

    # warm rim light, laid only inside the figure
    rim = Image.new("RGBA", (W, H), FIG_RIM + (0,))
    rd = ImageDraw.Draw(rim)
    rd.arc(box(cx - r, head_cy - r, cx + r, head_cy + r), 140, 250,
           fill=FIG_RIM + (255,), width=max(1, int(px(1.6))))
    rd.line([(cx - shoulder * 0.99, sh_cy + height * 0.01), (cx - waist, waist_cy)],
            fill=FIG_RIM + (255,), width=max(1, int(px(1.4))))
    rd.arc(box(cx - lap_rx, lap_cy - height * 0.10, cx + lap_rx, lap_cy + height * 0.12),
           155, 225, fill=FIG_RIM + (255,), width=max(1, int(px(1.4))))
    rim.putalpha(ImageChops.multiply(rim.split()[3], mask))
    fig.alpha_composite(rim)
    base.alpha_composite(fig)

def buddha_shrine(base, cx):
    """A seated Buddha on a lotus plinth, in a lit recess in the wall."""
    d = ImageDraw.Draw(base)
    top, half = SHRINE_TOP, px(96)

    d.rectangle(box(cx - half, top, cx + half, FLOOR_Y), fill=(26, 24, 21))
    for i in range(px(110)):
        y = FLOOR_Y - i
        t = (i / float(px(110))) ** 1.8
        d.line([(cx - half, y), (cx + half, y)], fill=mix((96, 74, 46), (26, 24, 21), t))

    # hanging banners either side, so the recess is not an empty panel
    for side in (-1, 1):
        bx = cx + side * px(74)
        d.rectangle(box(bx - px(11), top + px(6), bx + px(11), FLOOR_Y - px(24)),
                    fill=(104, 30, 24))
        d.rectangle(box(bx - px(6), top + px(6), bx + px(6), FLOOR_Y - px(24)),
                    fill=(146, 46, 34))
        for k in range(6):
            d.ellipse(box(bx - px(3), top + px(22) + k * px(14),
                          bx + px(3), top + px(28) + k * px(14)), fill=(206, 168, 96))

    # lotus plinth
    plinth_top = FLOOR_Y - px(30)
    d.rectangle(box(cx - px(100), plinth_top + px(8), cx + px(100), FLOOR_Y),
                fill=(106, 102, 90))
    for i in range(8):
        px0 = cx - px(94) + i * px(25)
        d.ellipse(box(px0, plinth_top, px0 + px(28), plinth_top + px(22)),
                  fill=(118, 114, 98))
        d.arc(box(px0, plinth_top, px0 + px(28), plinth_top + px(22)), 205, 335,
              fill=(152, 146, 124), width=max(1, int(px(0.7))))

    seated_buddha(base, cx, plinth_top + px(6), px(88))

    # candles and an offering bowl on the step
    for side in (-1, 1):
        bx = cx + side * px(72)
        d.rectangle(box(bx - px(4), FLOOR_Y - px(18), bx + px(4), FLOOR_Y), fill=(150, 60, 40))
        d.ellipse(box(bx - px(2.6), FLOOR_Y - px(24), bx + px(2.6), FLOOR_Y - px(17)),
                  fill=(255, 224, 150))
        lamp(bx, FLOOR_Y - px(20), px(40), (255, 206, 140), 130)
    d.ellipse(box(cx - px(26), FLOOR_Y - px(12), cx + px(26), FLOOR_Y + px(4)),
              fill=(124, 108, 78))

    # stone frame: pilasters, lintel and a tiled cap
    for side in (-1, 1):
        d.rectangle(box(cx + side * half, top, cx + side * (half + px(22)), FLOOR_Y),
                    fill=(120, 122, 110))
        d.line([(cx + side * half, top), (cx + side * half, FLOOR_Y)],
               fill=(64, 68, 60), width=max(1, int(px(0.8))))
        d.line([(cx + side * (half + px(22)), top), (cx + side * (half + px(22)), FLOOR_Y)],
               fill=(152, 154, 140), width=max(1, int(px(0.6))))
    d.rectangle(box(cx - half - px(26), top - px(22), cx + half + px(26), top),
                fill=(126, 128, 116))
    d.line([(cx - half - px(26), top - px(22)), (cx + half + px(26), top - px(22))],
           fill=(164, 168, 152), width=max(1, int(px(0.8))))
    for x in range(int(cx - half - px(26)), int(cx + half + px(26)), int(px(7))):
        d.arc(box(x, top - px(32), x + px(10), top - px(20)), 190, 350,
              fill=(112, 120, 118), width=max(1, int(px(0.7))))
    lamp(cx, plinth_top - px(20), px(150), (255, 200, 130), 66)

def pavilion(base, cx):
    """Stone pavilion: platform, pillars, warm altar, blue tiled roof, lanterns."""
    d = ImageDraw.Draw(base)
    half = px(150)
    plinth_y = FLOOR_Y - px(8)
    body_top = px(112)

    d.rectangle(box(cx - half - px(20), plinth_y - px(16), cx + half + px(20), plinth_y + px(10)),
                fill=(102, 104, 94))
    d.line([(cx - half - px(20), plinth_y - px(16)), (cx + half + px(20), plinth_y - px(16))],
           fill=(146, 150, 138), width=max(1, int(px(0.8))))
    for i in range(3):
        sy = plinth_y + px(10) + i * px(7)
        d.rectangle(box(cx - px(34) - i * px(7), sy, cx + px(34) + i * px(7), sy + px(7)),
                    fill=mix((94, 96, 88), (66, 68, 62), i * 0.22))

    # interior: dark, with the altar lit from the front
    d.rectangle(box(cx - half, body_top, cx + half, plinth_y - px(12)), fill=(34, 26, 22))
    for i in range(px(110)):
        d.line([(cx - half, body_top + i), (cx + half, body_top + i)],
               fill=mix((26, 20, 18), (86, 56, 40), (i / float(px(110))) ** 1.1))
    d.rectangle(box(cx - px(54), plinth_y - px(70), cx + px(54), plinth_y - px(16)),
                fill=(116, 34, 26))
    d.rectangle(box(cx - px(48), plinth_y - px(64), cx + px(48), plinth_y - px(20)),
                fill=(158, 48, 36))
    d.rectangle(box(cx - px(44), plinth_y - px(60), cx + px(44), plinth_y - px(24)),
                fill=(74, 24, 20))
    seated_buddha(base, cx, plinth_y - px(22), px(24))
    d = ImageDraw.Draw(base)
    d.rectangle(box(cx - px(56), plinth_y - px(24), cx + px(56), plinth_y - px(16)),
                fill=(96, 28, 22))

    # pillars: stone-red, a lit face and a shaded one
    for side in (-1, 1):
        for inset in (half - px(8), px(62)):
            x = cx + side * inset
            d.rectangle(box(x - px(9), body_top, x + px(9), plinth_y - px(12)),
                        fill=(98, 34, 28))
            d.rectangle(box(x - px(9), body_top, x - px(3), plinth_y - px(12)),
                        fill=(146, 58, 44))
            d.rectangle(box(x + px(3), body_top, x + px(9), plinth_y - px(12)),
                        fill=(66, 20, 16))
            d.rectangle(box(x - px(12), plinth_y - px(18), x + px(12), plinth_y - px(12)),
                        fill=(94, 96, 86))

    # eave beam, then two tiers of blue tiles with upturned corners
    d.rectangle(box(cx - half - px(26), px(100), cx + half + px(26), px(114)),
                fill=(52, 36, 26))
    for i in range(0, int(2 * half + px(52)), int(px(9))):
        x = cx - half - px(26) + i
        d.line([(x, px(100)), (x, px(114))], fill=(84, 56, 40), width=max(1, int(px(0.6))))

    for tier in range(2):
        eave_y = px(104) - tier * px(38)
        ridge_y = eave_y - px(34) - tier * px(4)
        span = half + px(36) - tier * px(54)
        rspan = px(86) - tier * px(26)
        d.polygon([(cx - span, eave_y), (cx - rspan, ridge_y),
                   (cx + rspan, ridge_y), (cx + span, eave_y)], fill=TILE)
        for i in range(1, 7):
            t = i / 7.0
            y = ridge_y + (eave_y - ridge_y) * t
            half_at = rspan + (span - rspan) * t
            d.line([(cx - half_at, y), (cx + half_at, y)],
                   fill=mix(TILE, TILE_LIT, 0.5 if i % 2 else 0.22),
                   width=max(1, int(px(0.9))))
        for k in range(-8, 9):
            tk = k / 8.0
            d.line([(cx + tk * span, eave_y), (cx + tk * rspan, ridge_y)],
                   fill=TILE_DARK, width=max(1, int(px(0.55))))
        d.line([(cx - rspan - px(7), ridge_y), (cx + rspan + px(7), ridge_y)],
               fill=(98, 108, 116), width=max(2, int(px(3))))
        for side in (-1, 1):
            xo = cx + side * span
            d.polygon([(xo, eave_y), (xo + side * px(30), eave_y - px(20)),
                       (xo + side * px(36), eave_y - px(6)), (xo, eave_y + px(5))],
                      fill=TILE_LIT)
            # an eave lantern at each corner
            lxp = cx + side * (span - px(16))
            d.line([(lxp, eave_y), (lxp, eave_y + px(14))], fill=(48, 34, 26),
                   width=max(1, int(px(0.6))))
            d.rounded_rectangle(box(lxp - px(7), eave_y + px(12), lxp + px(7), eave_y + px(32)),
                                radius=px(3), fill=(194, 62, 42))
            d.rectangle(box(lxp - px(4), eave_y + px(16), lxp + px(4), eave_y + px(28)),
                        fill=(255, 202, 130))
            d.line([(lxp, eave_y + px(32)), (lxp, eave_y + px(37))], fill=GOLD,
                   width=max(1, int(px(0.8))))
            lamp(lxp, eave_y + px(23), px(70), (255, 190, 120), 120)

    d.rectangle(box(cx - px(4), px(26), cx + px(4), px(42)), fill=GOLD)
    d.ellipse(box(cx - px(12), px(12), cx + px(12), px(36)), fill=GOLD)
    lamp(cx, plinth_y - px(32), px(150), (255, 176, 96), 84)


def stone_lantern(base, cx, y, h, seed):
    """A pedestal lantern: foot, post, lit box, flared cap and finial."""
    rnd = random.Random(seed)
    d = ImageDraw.Draw(base)
    w = h * 0.22
    box_top = y - h * 0.84
    box_bot = y - h * 0.50

    d.ellipse(box(cx - w * 0.86, y - px(5), cx + w * 0.86, y + px(7)),
              fill=tint((86, 88, 80), rnd, 0.06))
    d.rectangle(box(cx - w * 0.34, box_bot, cx + w * 0.34, y + px(2)),
                fill=tint((102, 104, 94), rnd, 0.06))
    d.line([(cx - w * 0.34, box_bot), (cx - w * 0.34, y)], fill=(138, 140, 126),
           width=max(1, int(px(0.5))))

    d.rectangle(box(cx - w * 0.62, box_top, cx + w * 0.62, box_bot), fill=(90, 92, 84))
    d.rectangle(box(cx - w * 0.46, box_top + px(2), cx + w * 0.46, box_bot - px(2)),
                fill=(255, 214, 146))
    d.rectangle(box(cx - w * 0.46, box_top + px(2), cx + w * 0.46, box_top + px(8)),
                fill=(222, 176, 114))
    for k in (-0.22, 0.22):
        d.line([(cx + w * k, box_top + px(2)), (cx + w * k, box_bot - px(2))],
               fill=(146, 106, 66), width=max(1, int(px(0.5))))

    d.polygon([(cx - w * 1.08, box_top), (cx - w * 0.56, box_top - px(11)),
               (cx + w * 0.56, box_top - px(11)), (cx + w * 1.08, box_top)],
              fill=(76, 78, 72))
    d.line([(cx - w * 1.08, box_top), (cx + w * 1.08, box_top)],
           fill=(126, 128, 116), width=max(1, int(px(0.7))))
    d.ellipse(box(cx - px(4), box_top - px(20), cx + px(4), box_top - px(11)),
              fill=(94, 96, 88))
    lamp(cx, (box_top + box_bot) / 2, h * 1.0, (255, 206, 140), 160)


def lanterns(base):
    """The stone lanterns, placed in the gaps between the garden's furniture."""
    spots = ((px(90), px(64)), (px(530), px(78)), (px(756), px(64)),
             (px(1070), px(78)), (px(1170), px(64)), (px(1800), px(78)))
    for i, (x, h) in enumerate(spots):
        stone_lantern(base, x, FLOOR_Y - px(6), h, 100 + i)
        d = ImageDraw.Draw(base)
        rnd = random.Random(31 + i)
        for _ in range(3):
            for _f in range(9):
                fx = x + rnd.uniform(-px(26), px(26))
                fy = FLOOR_Y - px(9) + rnd.uniform(-px(5), px(5))
                rr = rnd.uniform(px(1.4), px(2.6))
                d.ellipse(box(fx - rr, fy - rr, fx + rr, fy + rr),
                          fill=mix(rnd.choice([(206, 120, 140), (212, 186, 118),
                                               (210, 208, 194), (168, 142, 190)]),
                                   (150, 148, 138), 0.2))
    for i, x in enumerate(range(px(120), W, px(420))):
        wall_lantern(base, x, WALL_TOP + px(130), 300 + i)


# ------------------------------------------------------------------- the floor
def paving(base):
    """Worn flagstones with moss in the joints, running out of the wall."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, FLOOR_Y - px(30), W, H), fill=(48, 52, 46))
    rnd = random.Random(11)
    y = FLOOR_Y - px(30)
    row = 0
    while y < H:
        hgt = int(px(9) + row * px(3.6))
        x = -rnd.randint(0, px(26))
        while x < W:
            w = int(rnd.uniform(px(26), px(50)) * (1 + row * 0.16))
            tone = 0.82 + 0.24 * rnd.random()
            c = tint(tuple(int(v * tone) for v in STONE), rnd, 0.05)
            skew = rnd.uniform(-px(1.4), px(1.4))
            d.polygon([(x + px(1) + skew, y + px(1)),
                       (x + w - px(1) + skew, y + px(1)),
                       (x + w - px(1) - skew, y + hgt - px(1)),
                       (x + px(1) - skew, y + hgt - px(1))], fill=c)
            d.line([(x + px(2), y + px(1.6)), (x + w - px(2), y + px(1.6))],
                   fill=mix(c, (255, 236, 198), 0.14), width=max(1, int(px(0.5))))
            if rnd.random() < 0.5:
                mx = x + rnd.uniform(0, w)
                r = rnd.uniform(px(2), px(4.4))
                d.ellipse(box(mx - r, y + hgt - r, mx + r, y + hgt + r * 0.4),
                          fill=tint(MOSS, rnd, 0.24))
            x += w + px(1.8)
        y += hgt + px(1.6)
        row += 1

    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    for x in range(0, W, px(120)):
        sd.line([(x, FLOOR_Y), (x + px(30), H)], fill=(226, 208, 168, 14),
                width=max(2, int(px(3))))
    base.alpha_composite(sheen.filter(ImageFilter.GaussianBlur(px(6))))


def pool(base):
    """A shallow pool at the right: stone rim, dark water, lilies, reflections."""
    d = ImageDraw.Draw(base)
    y0, y1 = FLOOR_Y - px(18), FLOOR_Y + px(8)
    rnd = random.Random(23)

    d.rectangle(box(WATER_X0 - px(16), y0 - px(9), WATER_X1 + px(16), y1 + px(7)),
                fill=(84, 86, 76))
    for x in range(int(WATER_X0 - px(16)), int(WATER_X1 + px(16)), int(px(18))):
        d.rectangle(box(x + px(1), y0 - px(8), x + px(17), y0 - px(2)),
                    fill=tint((104, 106, 96), random.Random(x), 0.08))
        d.rectangle(box(x + px(1), y1 + px(1), x + px(17), y1 + px(6)),
                    fill=tint((100, 102, 92), random.Random(x + 7), 0.08))

    d.rectangle(box(WATER_X0, y0, WATER_X1, y1), fill=WATER)
    for i in range(px(9)):
        d.line([(WATER_X0, y0 + i), (WATER_X1, y0 + i)],
               fill=mix((6, 14, 18), WATER, i / float(px(9))))

    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    for _ in range(34):
        rx = rnd.uniform(WATER_X0, WATER_X1 - px(30))
        ry = rnd.uniform(y0 + px(2), y1 - px(2))
        rd.line([(rx, ry), (rx + rnd.uniform(px(8), px(30)), ry)],
                fill=(226, 180, 118, rnd.randint(16, 44)), width=max(1, int(px(1))))
    for _ in range(14):
        rx = rnd.uniform(WATER_X0, WATER_X1)
        ry = rnd.uniform(y0 + px(2), y1 - px(2))
        rd.line([(rx, ry), (rx + rnd.uniform(px(10), px(24)), ry)],
                fill=(150, 190, 190, rnd.randint(12, 28)), width=1)
    base.alpha_composite(refl.filter(ImageFilter.GaussianBlur(px(1.6))))
    d = ImageDraw.Draw(base)

    for _ in range(13):
        lx = rnd.uniform(WATER_X0 + px(14), WATER_X1 - px(14))
        ly = rnd.uniform(y0 + px(3), y1 - px(2))
        r = rnd.uniform(px(3.4), px(7))
        d.ellipse(box(lx - r, ly - r * 0.36, lx + r, ly + r * 0.36), fill=(40, 66, 42))
        if rnd.random() < 0.28:
            d.ellipse(box(lx - px(2), ly - px(3), lx + px(2), ly),
                      fill=(232, 198, 212))
    lamp((WATER_X0 + WATER_X1) / 2, y0 + px(4), px(110), (255, 200, 130), 30)


def bridge(base):
    """A stone footbridge at the far side of the pool: arch, deck and parapet."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(29)
    cx = (WATER_X0 + WATER_X1) // 2
    half = px(140)
    deck_y = FLOOR_Y - px(14)
    rise = px(22)

    pts = []
    for i in range(41):
        t = i / 40.0
        pts.append((cx - half + 2 * half * t, deck_y - rise * math.sin(math.pi * t)))

    # the arch opening: a half ellipse from the crown down to the water line, so
    # it stays inside the pool band instead of spilling onto the paving
    ax = half * 0.62
    arch = box(cx - ax, deck_y - rise * 0.95, cx + ax, FLOOR_Y + px(8))
    d.ellipse(arch, fill=(14, 20, 20))
    for i in range(14):
        a0 = 180 + i * (180 / 14.0)
        d.arc(arch, a0, a0 + 180 / 14.0, fill=(98, 98, 86), width=max(1, int(px(2.2))))

    # the deck: a thick band of stones following the arc
    for i in range(40):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        d.polygon([(x0, y0), (x1, y1), (x1, y1 + px(15)), (x0, y0 + px(15))],
                  fill=tint((112, 112, 100), rnd, 0.05))
        d.line([(x0, y0), (x1, y1)], fill=(160, 156, 132), width=max(1, int(px(0.8))))

    # parapet: posts and a cap rail on the near side
    rail = [(x, y - px(18)) for x, y in pts]
    for i in range(0, 41, 5):
        x, y = pts[i]
        d.rectangle(box(x - px(4), y - px(18), x + px(4), y + px(2)), fill=(96, 96, 84))
        d.rectangle(box(x - px(4), y - px(18), x - px(1), y + px(2)), fill=(126, 124, 108))
    d.line(rail, fill=(118, 116, 100), width=max(2, int(px(2.4))))
    d.line([(x, y - px(2)) for x, y in rail], fill=(166, 162, 138), width=max(1, int(px(0.8))))
    lamp(cx, deck_y - rise + px(14), px(120), (255, 204, 140), 30)

def flower(base, x, y, r, colour, rnd):
    d = ImageDraw.Draw(base)
    for k in range(5):
        a = k * 2 * math.pi / 5 + rnd.uniform(-0.4, 0.4)
        d.ellipse(box(x + math.cos(a) * r - r * 0.6, y + math.sin(a) * r - r * 0.6,
                      x + math.cos(a) * r + r * 0.6, y + math.sin(a) * r + r * 0.6),
                  fill=colour)
    d.ellipse(box(x - r * 0.34, y - r * 0.34, x + r * 0.34, y + r * 0.34),
              fill=(226, 212, 158))


def beds(base):
    """Planting between the path and the wall: hedges, flowers, ferns, stone kerb."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(31)
    y0, y1 = BED_Y0, FLOOR_Y + px(3)
    palette = [(198, 116, 134), (206, 180, 112), (206, 202, 186), (162, 138, 182),
               (204, 148, 112)]

    gaps = ((GATE_CX - GATE_R - px(24), GATE_CX + GATE_R + px(24)),
            (SHRINE_CX - px(150), SHRINE_CX + px(150)),
            (PAVILION_CX - px(160), PAVILION_CX + px(160)),
            (WATER_X0 - px(20), WATER_X1 + px(20)))

    x = 0
    while x < W:
        if any(a <= x <= b for a, b in gaps):
            x += px(6)
            continue
        width = rnd.uniform(px(54), px(110))
        d.rectangle(box(x, y0, x + width, y1), fill=tint(SOIL, rnd, 0.14))
        for _ in range(int(width / px(1.6))):
            lx = x + rnd.uniform(0, width)
            ly = y0 + rnd.uniform(px(2), y1 - y0)
            r = rnd.uniform(px(1.8), px(4.2))
            d.ellipse(box(lx - r, ly - r * 0.8, lx + r, ly + r * 0.8),
                      fill=tint(LEAF if rnd.random() < 0.72 else LEAF_LIT, rnd, 0.24))
        if rnd.random() < 0.6:
            sx = x + rnd.uniform(px(10), width - px(10))
            for _ in range(22):
                r = rnd.uniform(px(3), px(8))
                ox = sx + rnd.uniform(-px(14), px(14))
                oy = y0 - rnd.uniform(0, px(18))
                d.ellipse(box(ox - r, oy - r * 0.8, ox + r, oy + r * 0.8),
                          fill=tint(LEAF_DARK if rnd.random() < 0.55 else LEAF, rnd, 0.22))
        for _ in range(int(width / px(13))):
            fx = x + rnd.uniform(0, width)
            fy = y0 + rnd.uniform(0, (y1 - y0) * 0.7)
            stem = fy + rnd.uniform(px(4), px(10))
            d.line([(fx, fy), (fx + rnd.uniform(-px(1.6), px(1.6)), stem)],
                   fill=tint((48, 74, 40), rnd, 0.2), width=max(1, int(px(0.4))))
            flower(base, fx, fy, rnd.uniform(px(1.8), px(3.4)), rnd.choice(palette), rnd)
        if rnd.random() < 0.5:
            bx = x + rnd.uniform(px(6), width - px(6))
            for f in range(8):
                a = -math.pi / 2 + (f - 3.5) * 0.2
                ln = rnd.uniform(px(10), px(20))
                d.line([(bx, y1), (bx + math.cos(a) * ln, y1 + math.sin(a) * ln)],
                       fill=tint((54, 84, 46), rnd, 0.2), width=max(1, int(px(0.6))))
        x += width + rnd.uniform(px(4), px(16))

    d.rectangle(box(0, y1, W, y1 + px(7)), fill=(88, 90, 82))
    for kx in range(0, W, px(22)):
        d.rectangle(box(kx + px(1), y1 + px(1), kx + px(20), y1 + px(6)),
                    fill=tint((102, 104, 94), random.Random(kx), 0.08))


def foreground():
    """Near planting in front of the fighters: leaves and flowers at the edge."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(41)
    for i in range(px(30)):
        a = int(212 * (1 - i / float(px(30))) ** 1.5)
        d.line([(0, H - i), (W, H - i)], fill=(6, 14, 10, a))
    for _ in range(300):
        x = rnd.uniform(0, W)
        y = H - rnd.uniform(0, px(34))
        r = rnd.uniform(px(3), px(11))
        d.ellipse(box(x - r, y - r * 0.7, x + r, y + r * 0.7),
                  fill=tint(LEAF_LIT, rnd, 0.3) + (rnd.randint(80, 150),))
    for _ in range(60):
        x = rnd.uniform(0, W)
        y = H - rnd.uniform(px(2), px(26))
        r = rnd.uniform(px(2), px(5))
        c = mix(rnd.choice([(220, 130, 150), (228, 200, 130), (226, 222, 208)]),
                (140, 138, 130), 0.2)
        d.ellipse(box(x - r, y - r, x + r, y + r), fill=c + (rnd.randint(90, 160),))
    return fg.filter(ImageFilter.GaussianBlur(px(1.6)))


# -------------------------------------------------------------------- the arena
def paint():
    LIGHTS.clear()
    base = hd.blank([(0, NIGHT_HIGH), (px(30), NIGHT_HIGH),
                     (WALL_TOP, NIGHT_LOW), (FLOOR_Y, (26, 34, 30)),
                     (240, (16, 20, 18))])

    canopy(base, px(500), px(360), 5)
    canopy(base, px(1060), px(300), 6, top=px(60))
    canopy(base, px(1220), px(430), 7, top=px(24))
    night(base)
    haze(base)

    bamboo(base, GATE_CX - px(34), 3, count=10, spread=px(70),
           top=WALL_TOP - px(54), base_y=FLOOR_Y - px(18))
    bamboo(base, px(520), 5, count=8, spread=px(56),
           top=WALL_TOP - px(40), base_y=FLOOR_Y - px(18))
    bamboo(base, px(1700), 7, count=12, spread=px(90),
           top=WALL_TOP - px(60), base_y=FLOOR_Y - px(18))

    wall(base)
    moon_gate(base, GATE_CX, GATE_R, FLOOR_Y - GATE_R)
    buddha_shrine(base, SHRINE_CX)
    pavilion(base, PAVILION_CX)

    paving(base)
    pool(base)
    bridge(base)
    beds(base)
    lanterns(base)

    base = hd.shade(base, [(hd.light(cx, cy, r, col, peak), max(8, int(r * 0.34)), 1.1)
                           for cx, cy, r, col, peak in LIGHTS])
    base = art.vignette(base, 0.4)
    base = art.grain(base, 3, seed=41)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


def main():
    hd.STAGES["buddha_garden"] = ("The Buddha Garden", paint)
    hd.build("buddha_garden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
