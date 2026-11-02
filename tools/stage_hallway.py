"""Lo Pan's Hallway: the long approach to the throne, lined with gold statues.

The film's throne hall (and the concept art in concept_art/stages) is one very
long corridor: a deep blue lacquer wall under a gilded cornice, red lacquer
wainscot at the floor, dark teal columns every few bays, a runner down the
middle of the floor, rows of small gilded Buddha statues on red pedestals
either side, and red paper lanterns hanging over them.

A 2D fighting stage cannot show a corridor receding away from the camera, so
the hall is painted in side elevation: the camera looks across the corridor,
the fighters travel along it, and the depth comes from three planes per bay -
the flat wall behind, the statue standing off that wall, and the column in
front of both. It is the same trick tools/stage_throne.py uses for its niches,
in a room that has no focal point of its own: the statue rows repeat for the
whole 8192 px, so the fight can run the length of the hall.

Every prop is placed off BAY, so a clean checkout reproduces the art.

Run:  python3 tools/stage_hallway.py       (part of tools/build_all.py)
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
import stage_throne as throne

W, H = hd.W, hd.H
CX, FLOOR_Y, px = hd.CX, hd.FLOOR_Y, hd.px

BAY = px(56)                  # 252: one statue, one bay of wall
COL_EVERY = 2                 # a column at every second bay boundary
CORNICE = px(28)              # 126: underside of the gilded cornice
CEILING = px(16)              # 72: the coffered ceiling band
WAINSCOT = px(150)            # 675: top of the red lacquer wainscot

WALL = (44, 48, 76)
WALL_DK = (30, 34, 56)
WALL_LT = (56, 62, 94)
LACQ = (112, 34, 32)
LACQ_DK = (74, 20, 22)
GOLD = (196, 150, 62)
GOLD_LT = (246, 214, 132)
GOLD_DK = (116, 82, 30)
CARPET = (44, 36, 76)
CARPET_LT = (60, 50, 100)
CARPET_RED = (126, 26, 30)

LIGHTS = []                   # (cx, cy, radius, colour, peak)


# ------------------------------------------------------------------- statue
def statue_tile(h, seed=0, hand_up=False):
    """One gilded figure on its pedestal, as a (colour, height) pair.

    Painted at 2x and resampled: the shapes are small, and an arc rasterised at
    1x reads as a staircase rather than a shoulder. The height map is what
    ``throne.sculpted`` turns into the modelling, so the figure is lit from the
    upper left like every other carved prop in the game.
    """
    rnd = random.Random(seed)
    fh = int(round(h))               # figure height, pedestal excluded
    ph = int(round(fh * 0.30))       # pedestal
    tw = int(round(fh * 1.16))
    th = fh + ph
    K = 2

    colour = Image.new("RGB", (tw * K, th * K), (0, 0, 0))
    height = Image.new("L", (tw * K, th * K), 0)
    dc, dh = ImageDraw.Draw(colour), ImageDraw.Draw(height)

    gold, gold_dk, gold_lt = (190, 142, 54), (126, 86, 28), (248, 216, 134)
    cx = tw / 2.0
    base = th - ph                   # the figure sits on the pedestal top

    def ell(x, y, rx, ry, fill, hv):
        box = [(x - rx) * K, (y - ry) * K, (x + rx) * K, (y + ry) * K]
        dc.ellipse(box, fill=fill)
        dh.ellipse(box, fill=hv)

    def rect(x0, y0, x1, y1, fill, hv):
        box = [x0 * K, y0 * K, x1 * K, y1 * K]
        dc.rectangle(box, fill=fill)
        dh.rectangle(box, fill=hv)

    def poly(pts, fill, hv):
        p = [(x * K, y * K) for x, y in pts]
        dc.polygon(p, fill=fill)
        dh.polygon(p, fill=hv)

    # ---- pedestal: red lacquer drum with gilt mouldings
    pw = tw * 0.33
    rect(cx - pw, base + ph * 0.06, cx + pw, th, LACQ, 196)
    rect(cx - pw, base + ph * 0.06, cx + pw, base + ph * 0.20, GOLD, 226)
    rect(cx - pw * 1.06, base + ph * 0.20, cx + pw * 1.06, base + ph * 0.30, GOLD_DK, 206)
    rect(cx - pw * 1.02, th - ph * 0.16, cx + pw * 1.02, th, GOLD, 224)
    for k in range(-2, 3):
        gf = cx + k * pw * 0.34
        dc.line([(gf * K, (base + ph * 0.24) * K), (gf * K, (th - ph * 0.18) * K)],
                fill=(70, 20, 20), width=max(1, int(fh * 0.012)))

    # ---- halo: the gilt disc behind the head. It is what makes the figure
    # read as a Buddha at stage size, where the face is only a few pixels.
    ell(cx, base - fh * 0.850, fh * 0.225, fh * 0.225, (124, 88, 32), 176)
    ell(cx, base - fh * 0.850, fh * 0.212, fh * 0.212, (164, 120, 46), 186)
    dc.ellipse([(cx - fh * 0.212) * K, (base - fh * 1.062) * K,
                (cx + fh * 0.212) * K, (base - fh * 0.638) * K],
               outline=(214, 172, 96), width=max(1, int(fh * 0.012)))

    # ---- the seat: crossed legs, the knees reading either side of the lap
    ell(cx, base - fh * 0.070, fh * 0.355, fh * 0.092, gold, 214)
    ell(cx - fh * 0.250, base - fh * 0.098, fh * 0.110, fh * 0.086, gold, 226)
    ell(cx + fh * 0.250, base - fh * 0.098, fh * 0.110, fh * 0.086, gold, 226)
    dc.line([(cx * K, (base - fh * 0.010) * K), (cx * K, (base - fh * 0.105) * K)],
            fill=(120, 80, 26), width=max(1, int(fh * 0.014)))

    # ---- belly and chest, the belly the heaviest volume on the figure
    belly_r = fh * (0.255 + rnd.uniform(-0.006, 0.006))
    ell(cx, base - fh * 0.375, belly_r, fh * 0.240, gold, 252)
    ell(cx, base - fh * 0.615, fh * 0.235, fh * 0.130, gold, 242)
    ell(cx, base - fh * 0.680, fh * 0.225, fh * 0.080, gold, 238)
    # the fold where the belly meets the crossed legs, so the volumes part
    dc.arc([(cx - belly_r * 0.98) * K, (base - fh * 0.30) * K,
            (cx + belly_r * 0.98) * K, (base - fh * 0.10) * K], 195, 345,
           fill=(126, 86, 28), width=max(1, int(fh * 0.014)))

    # ---- arms: down the flanks, the hands meeting in the lap
    for sx in (-1, 1):
        ax = cx + sx * fh * 0.215
        poly([(ax - fh * 0.052, base - fh * 0.655),
              (ax + fh * 0.052, base - fh * 0.655),
              (cx + sx * fh * 0.150, base - fh * 0.300),
              (cx + sx * fh * 0.082, base - fh * 0.285)], gold, 232)
    if hand_up:
        ell(cx + fh * 0.232, base - fh * 0.520, fh * 0.052, fh * 0.042, (206, 164, 80),
            246)
        poly([(cx + fh * 0.210, base - fh * 0.556), (cx + fh * 0.232, base - fh * 0.650),
              (cx + fh * 0.258, base - fh * 0.556)], gold, 238)
    else:
        ell(cx, base - fh * 0.286, fh * 0.070, fh * 0.044, (206, 164, 80), 246)

    # ---- robe: a narrow sash over one shoulder, and a hem across the lap
    poly([(cx - fh * 0.150, base - fh * 0.686), (cx - fh * 0.070, base - fh * 0.694),
          (cx + fh * 0.090, base - fh * 0.572), (cx + fh * 0.020, base - fh * 0.548)],
         (174, 132, 52), 250)
    dc.line([(cx - fh * 0.128, base - fh * 0.668), (cx + fh * 0.068, base - fh * 0.564)],
            fill=(122, 86, 28), width=max(1, int(fh * 0.011)))
    for k in (-1, 1):
        fxx = cx + k * fh * 0.13
        dc.arc([(fxx - fh * 0.13) * K, (base - fh * 0.275) * K,
                (fxx + fh * 0.13) * K, (base - fh * 0.035) * K], 200, 340,
               fill=(140, 98, 36), width=max(1, int(fh * 0.012)))

    # ---- neck and head: big enough to read as a head at stage size
    rect(cx - fh * 0.050, base - fh * 0.760, cx + fh * 0.050, base - fh * 0.690, gold,
         228)
    ell(cx, base - fh * 0.828, fh * 0.128, fh * 0.132, gold, 250)
    # the shadow under the chin, so the head is a head and not a bump
    dc.arc([(cx - fh * 0.104) * K, (base - fh * 0.792) * K,
            (cx + fh * 0.104) * K, (base - fh * 0.716) * K], 200, 340,
           fill=(112, 76, 24), width=max(1, int(fh * 0.013)))
    ell(cx, base - fh * 0.952, fh * 0.050, fh * 0.048, gold, 240)
    for sx in (-1, 1):
        ell(cx + sx * fh * 0.130, base - fh * 0.820, fh * 0.021, fh * 0.052, gold_dk,
            212)
        # brow ridge
        dc.arc([(cx + sx * fh * 0.062 - fh * 0.040) * K, (base - fh * 0.862) * K,
                (cx + sx * fh * 0.062 + fh * 0.040) * K, (base - fh * 0.820) * K],
               190, 350, fill=(146, 104, 40), width=max(1, int(fh * 0.011)))
        # closed eye
        dc.arc([(cx + sx * fh * 0.050 - fh * 0.026) * K, (base - fh * 0.816) * K,
                (cx + sx * fh * 0.050 + fh * 0.026) * K, (base - fh * 0.796) * K],
               200, 340, fill=(92, 62, 22), width=max(1, int(fh * 0.009)))
    dc.arc([(cx - fh * 0.030) * K, (base - fh * 0.790) * K,
            (cx + fh * 0.030) * K, (base - fh * 0.764) * K], 200, 340,
           fill=(100, 68, 24), width=max(1, int(fh * 0.010)))
    dc.ellipse([(cx - fh * 0.012) * K, (base - fh * 0.865) * K,
                (cx + fh * 0.012) * K, (base - fh * 0.847) * K], fill=(110, 76, 26))

    return (colour.resize((tw, th), Image.LANCZOS),
            height.resize((tw, th), Image.LANCZOS))


def statue(base, cx, y_base, h, seed=0, hand_up=False):
    """Composite one sculpted gold figure standing on the floor at y_base.

    sculpted() returns a canvas-sized *layer*, not a composite: returning it
    unwrapped replaces the hall with a transparent plate holding one statue,
    which is exactly what the first build of this stage looked like.
    """
    colour, height = statue_tile(h, seed, hand_up)
    return Image.alpha_composite(base, throne.sculpted(colour, height, cx, y_base))


# ------------------------------------------------------------------- the hall
def cornice(d):
    """Coffered ceiling band, gilt cornice and the shadow it casts."""
    d.rectangle([0, 0, W, CEILING], fill=(18, 16, 26))
    step = px(28)
    for x in range(0, W, step):
        d.rectangle([x + px(3), px(2), x + step - px(4), CEILING - px(3)],
                    fill=(26, 23, 36))
        d.rectangle([x + px(3), px(2), x + step - px(4), CEILING - px(3)],
                    outline=(74, 62, 44), width=max(1, px(0.7)))
        d.ellipse([x + step * 0.40, CEILING * 0.34, x + step * 0.60, CEILING * 0.66],
                  fill=(150, 116, 54))
    d.rectangle([0, CEILING, W, CORNICE], fill=GOLD)
    d.rectangle([0, CEILING, W, CEILING + px(3)], fill=GOLD_LT)
    d.rectangle([0, CORNICE - px(5), W, CORNICE], fill=GOLD_DK)
    for x in range(0, W, px(22)):
        d.line([(x, CEILING + px(4)), (x, CORNICE - px(6))], fill=(160, 120, 48),
               width=max(1, px(0.8)))
    for i in range(px(10)):
        a = int(120 * (1 - i / float(px(10))) ** 1.6)
        d.line([(0, CORNICE + i), (W, CORNICE + i)], fill=(10, 8, 14, a))


def wall(d):
    """Blue lacquer field, gold cartouches, and the red wainscot at the floor."""
    d.rectangle([0, CORNICE, W, FLOOR_Y], fill=WALL)
    for i in range(-18, 19):
        x = CX + i * BAY
        if x < -BAY or x > W + BAY:
            continue
        # a panel per bay, its frame gilded and its field a shade deeper
        pw = BAY * 0.44
        top, bot = CORNICE + px(8), WAINSCOT - px(8)
        d.rectangle([x - pw, top, x + pw, bot], fill=WALL_DK)
        d.rectangle([x - pw, top, x + pw, bot],
                    outline=(146, 112, 54), width=max(2, px(1.1)))
        d.rectangle([x - pw + px(3), top + px(3), x + pw - px(3), bot - px(3)],
                    outline=(70, 56, 34), width=max(1, px(0.8)))
        # gilt cartouche high on the panel: the seal of the house, repeated
        cy0 = top + px(18)
        d.rectangle([x - pw * 0.58, cy0, x + pw * 0.58, cy0 + px(64)],
                    fill=(40, 35, 54))
        d.rectangle([x - pw * 0.58, cy0, x + pw * 0.58, cy0 + px(64)],
                    outline=GOLD, width=max(2, px(1.0)))
        d.rectangle([x - pw * 0.58 + px(4), cy0 + px(4), x + pw * 0.58 - px(4),
                     cy0 + px(60)], outline=(112, 88, 42), width=max(1, px(0.7)))
        hd.glyph(d, x - px(6.5), cy0 + px(14), px(19), (216, 178, 102), seed=i + 7,
                 width=px(1.5))
        # the lower register, so the panel is two fields and not one void
        ly0 = cy0 + px(76)
        d.rectangle([x - pw * 0.78, ly0, x + pw * 0.78, bot - px(8)],
                    fill=(26, 30, 48))
        d.rectangle([x - pw * 0.78, ly0, x + pw * 0.78, bot - px(8)],
                    outline=(98, 78, 40), width=max(1, px(0.8)))
        for k in (-1, 1):
            ccx = x + k * pw * 0.40
            d.arc([ccx - pw * 0.30, ly0 + px(6), ccx + pw * 0.30, ly0 + px(34)],
                  196, 344, fill=(58, 62, 94), width=max(1, px(1.1)))
        d.line([(x - pw * 0.78, ly0 + px(2)), (x + pw * 0.78, ly0 + px(2))],
               fill=GOLD_DK, width=max(1, px(1.0)))

    # wainscot: red lacquer, gilt rails top and bottom, gilt beading between
    d.rectangle([0, WAINSCOT, W, FLOOR_Y], fill=LACQ)
    for i in range(-18, 19):
        x = CX + i * BAY
        if x < -BAY or x > W + BAY:
            continue
        d.rectangle([x - BAY * 0.46, WAINSCOT + px(4), x + BAY * 0.46, FLOOR_Y],
                    fill=LACQ_DK)
        d.rectangle([x - BAY * 0.46, WAINSCOT + px(4), x + BAY * 0.46, FLOOR_Y],
                    outline=(148, 112, 54), width=max(1, px(0.9)))
        for k in (-2, 0, 2):
            d.line([(x + k * BAY * 0.16, WAINSCOT + px(7)),
                    (x + k * BAY * 0.16, FLOOR_Y - px(3))], fill=(140, 44, 38),
                   width=max(1, px(1.0)))
    d.rectangle([0, WAINSCOT, W, WAINSCOT + px(3)], fill=GOLD)
    d.rectangle([0, WAINSCOT + px(3), W, WAINSCOT + px(6)], fill=GOLD_DK)


def emblem(base):
    """The gilded wheel over the middle of the hall: the one landmark on it."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cy = CORNICE + px(62)
    r = px(30)
    d.ellipse([CX - r - px(6), cy - r - px(6), CX + r + px(6), cy + r + px(6)],
              fill=(22, 20, 32))
    d.ellipse([CX - r, cy - r, CX + r, cy + r], fill=(150, 112, 44))
    d.ellipse([CX - r * 0.94, cy - r * 0.94, CX + r * 0.94, cy + r * 0.94],
              fill=(206, 160, 70))
    for k in range(24):
        a = 2 * math.pi * k / 24
        d.line([(CX + math.cos(a) * r * 0.80, cy + math.sin(a) * r * 0.80),
                (CX + math.cos(a) * r * 0.97, cy + math.sin(a) * r * 0.97)],
               fill=(120, 86, 32), width=max(1, px(1.4)))
    d.ellipse([CX - r * 0.60, cy - r * 0.60, CX + r * 0.60, cy + r * 0.60],
              fill=(182, 138, 56))
    d.ellipse([CX - r * 0.52, cy - r * 0.52, CX + r * 0.52, cy + r * 0.52],
              fill=(30, 26, 40))
    d.ellipse([CX - r * 0.42, cy - r * 0.42, CX + r * 0.42, cy + r * 0.42],
              outline=GOLD_LT, width=max(1, px(1.2)))
    hd.glyph(d, CX - px(9), cy - px(9), px(18), (238, 204, 126), seed=5, width=px(2.2))
    d.ellipse([CX - r * 0.10, cy - r * 0.10, CX + r * 0.10, cy + r * 0.10],
              fill=(252, 224, 148))
    base.alpha_composite(layer)
    LIGHTS.append((CX, cy, px(62), (255, 196, 112), 96))
    return base


def columns(base):
    """Lacquer columns, painted after the statues so the row has depth."""
    d = ImageDraw.Draw(base)
    for i in range(-9, 10):
        if i % COL_EVERY:
            continue
        # between two bays, never on the centre line: a column at CX cut the
        # gilt wheel in half down the middle of the hall
        x = CX + i * BAY + BAY // 2
        if x < -BAY or x > W + BAY:
            continue
        w = px(13)
        hd.column(d, x, CEILING + px(4), FLOOR_Y, w, (34, 40, 66), (20, 24, 44),
                  cap=GOLD)
        d.rectangle([x - w / 2, CEILING + px(4), x - w / 2 + px(2.4), FLOOR_Y],
                    fill=(60, 68, 102))
        d.rectangle([x + w / 2 - px(2.0), CEILING + px(4), x + w / 2, FLOOR_Y],
                    fill=(18, 21, 38))
        # gilt collar at the capital and a bead line down the front
        for yy in (CEILING + px(9), FLOOR_Y - px(13)):
            d.rectangle([x - w * 0.72, yy, x + w * 0.72, yy + px(3)], fill=GOLD)
        d.line([(x, CEILING + px(16)), (x, FLOOR_Y - px(16))], fill=(150, 124, 64),
               width=max(1, px(0.9)))
    return base


def lanterns(d):
    """One lantern over each bay, alternating size: the rows of the hall."""
    for i in range(-9, 10):
        x = CX + i * BAY
        if x < -BAY or x > W + BAY:
            continue
        big = (i % 2 == 0)
        cy = CORNICE + (px(22) if big else px(17))
        r = px(7.4) if big else px(5.8)
        hd.hang_lantern(d, x, cy, r)
        LIGHTS.append((x, cy + px(1), px(42) if big else px(30), (255, 172, 92),
                       120 if big else 88))


def floor(d):
    """Polished slate, and the runner down the middle of the hall."""
    d.rectangle([0, FLOOR_Y, W, H], fill=(34, 32, 44))
    y, gap = FLOOR_Y, px(3)
    while y < H:
        y2 = min(H, y + gap)
        lift = int(14 * (y - FLOOR_Y) / max(1, H - FLOOR_Y))
        d.rectangle([0, y, W, y2], fill=(40 + lift, 37 + lift, 50 + lift))
        d.line([(0, y), (W, y)], fill=(22, 20, 28), width=max(1, px(0.7)))
        y = y2
        gap *= 1.26
    for k in range(-70, 71):
        x_top = CX + k * px(12)
        d.line([(x_top, FLOOR_Y), (CX + (x_top - CX) * 4.4, H)],
               fill=(26, 24, 32), width=max(1, px(0.7)))
    d.line([(0, FLOOR_Y), (W, FLOOR_Y)], fill=(110, 92, 56), width=max(2, px(1.8)))

    # runner: red ground, gilt piping, indigo field, gilt diamonds. The floor
    # is only the band between zoffset and the bottom of the canvas, so the
    # runner has to fit inside it: run it past H and only its top border shows.
    y0, y1 = FLOOR_Y + px(3), H - px(1)
    d.rectangle([0, y0, W, y1], fill=CARPET_RED)
    d.rectangle([0, y0 + px(4), W, y1], fill=GOLD_DK)
    d.rectangle([0, y0 + px(7), W, y1], fill=CARPET)
    span = max(1, int(y1 - (y0 + px(7))))
    for i in range(span):
        t = i / float(span)
        d.line([(0, y0 + px(7) + i), (W, y0 + px(7) + i)],
               fill=tuple(int(CARPET[k] + (CARPET_LT[k] - CARPET[k]) * (1 - t) * 0.8)
                          for k in range(3)))
    d.line([(0, y0 + px(7)), (W, y0 + px(7))], fill=(126, 112, 156),
           width=max(1, px(1.0)))
    my = (y0 + px(7) + y1) / 2
    for i in range(-20, 21):
        ex = CX + i * BAY * 0.5
        if ex < -BAY or ex > W + BAY:
            continue
        d.polygon([(ex, my - px(10)), (ex + px(7), my), (ex, my + px(10)),
                   (ex - px(7), my)], fill=(64, 52, 104))
        d.polygon([(ex, my - px(10)), (ex + px(7), my), (ex, my + px(10)),
                   (ex - px(7), my)], outline=(152, 124, 64))
    # the far edge sits in a shadow, so the runner is in the floor, not on it
    for i in range(px(4)):
        a = int(96 * (1 - i / float(px(4))))
        d.line([(0, y0 - i), (W, y0 - i)], fill=(8, 6, 10, a))


def paint():
    LIGHTS.clear()
    base = hd.blank([
        (0, (12, 11, 18)), (40, (26, 26, 42)), (90, (36, 34, 56)),
        (140, (34, 31, 52)), (190, (26, 23, 36)), (240, (10, 9, 14)),
    ])
    d = ImageDraw.Draw(base)

    wall(d)
    cornice(d)
    floor(d)
    base = emblem(base)

    # a shadow behind each figure, so the gold stands off the wall
    cast = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cast)
    for i in range(-18, 19):
        x = CX + i * BAY
        if x < -BAY or x > W + BAY:
            continue
        h = px(30) + (px(6) if i % 3 else 0)
        cd.ellipse([x - h * 0.58, FLOOR_Y - h * 1.28, x + h * 0.58, FLOOR_Y - px(4)],
                   fill=(6, 5, 9, 170))
        cd.rectangle([x - h * 0.52, FLOOR_Y - px(6), x + h * 0.52, FLOOR_Y],
                     fill=(6, 5, 9, 190))
    base.alpha_composite(cast.filter(ImageFilter.GaussianBlur(px(4))))

    # the rows of statues, a pair at a time, each a little different
    for i in range(-18, 19):
        x = CX + i * BAY
        if x < -BAY or x > W + BAY:
            continue
        h = px(45) + (px(6) if i % 4 == 0 else 0)
        base = statue(base, x, FLOOR_Y, h, seed=i * 13 + 5, hand_up=(i % 3 == 1))
        LIGHTS.append((x, FLOOR_Y - px(24), px(36), (255, 196, 116), 62))

    base = columns(base)
    d = ImageDraw.Draw(base)
    lanterns(d)

    base = hd.shade(base, [(hd.light(cx, cy, r, col, peak), px(9), 1.15)
                           for cx, cy, r, col, peak in LIGHTS])
    base = hd.finish(base, 7, 3, 0.34, FLOOR_Y)

    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    for i in range(px(28)):
        a = int(210 * (1 - i / px(28)) ** 1.6)
        fd.line([(0, H - i), (W, H - i)], fill=(6, 5, 9, a))

    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, fg, 1)]


def main():
    hd.STAGES["lopans_hallway"] = ("Lo Pan's Hallway", paint)
    hd.build("lopans_hallway")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
