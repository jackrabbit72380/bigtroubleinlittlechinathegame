"""Forbidden Hall: the guardian corridor, painted from the still.

The still is one-point perspective down a stone passage: massive dark ashlar
walls, a barrel vault overhead, rows of bronze guardian figures standing in the
shadows — horned crowns, snarling faces, layered armour, hands on their swords —
iron lanterns with red caps hanging in a line, and at the far end a doorway
washed in cold blue light.

A 2D fighting stage cannot show a corridor receding from the camera, so the hall
is painted the way the other arenas are: as a wall of statue bays seen across the
play plane, the fighters travelling along it. Depth comes from three planes per
bay — the ashlar wall behind, the guardian standing off it on its plinth, and
the hanging lantern in front of both — and the cold doorway at the centre of the
hall is the one landmark, so a fight that runs the length of the corridor always
has the light to turn back towards.

Every prop is placed off BAY, so a clean checkout reproduces the art.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960, localcoord 1920x1080, camera travel +/-3136.

Run:  python3 tools/stage_forbidden_hall.py     (part of tools/build_all.py)
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

BAY = px(132)                      # 594: one guardian, one bay of wall
WALL_TOP = px(46)                  # 207: the spring of the vault
VAULT = px(30)                     # 135: the shadowed band of the vault itself
PLINTH = px(13)                    # 59: the stone block each guardian stands on
GATE_HALF = px(60)                 # 270: the cold doorway at the centre

STONE = (60, 55, 48)               # ashlar in shadow
STONE_L = (112, 104, 90)
STONE_D = (28, 25, 21)
STONE_C = (72, 76, 74)             # the colder, bluer blocks near the door
MORTAR = (26, 23, 20)

BRONZE = (104, 76, 42)             # the guardians: dark cast bronze
BRONZE_L = (182, 140, 78)
BRONZE_D = (40, 28, 16)
VERDIGRIS = (74, 92, 74)           # the green that gathers in the recesses

IRON = (52, 50, 48)
IRON_L = (110, 108, 102)
RED = (124, 32, 28)
RED_L = (176, 58, 44)
GOLD = (196, 154, 82)
FLAME = (255, 190, 112)
COOL = (176, 206, 218)
BONE = (216, 208, 186)

FL_L = (150, 146, 134)             # the pale flagstones of the corridor
FL_D = (124, 120, 110)
FL_GRID = (86, 82, 74)

LIGHTS = []


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def tint(c, rnd, amt=0.08):
    return tuple(max(0, min(255, int(v * (1 + rnd.uniform(-amt, amt))))) for v in c)


def box(x0, y0, x1, y1):
    """Normalised corners: PIL refuses a rectangle drawn bottom-up."""
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def lamp(cx, cy, r, color=FLAME, peak=150):
    LIGHTS.append((cx, cy, r, color, peak))


def ashlar(d, x0, x1, y0, y1, seed, block_h=None, tone=1.0, cold=0.0):
    """Large dressed stone, laid in staggered courses with a lit top edge.

    Kitchen-tile sized blocks read as brick; the still's are nearly waist high,
    so the courses are tall and each block is a couple of hand-widths of stone.
    """
    rnd = random.Random(seed)
    block_h = block_h or px(15)
    d.rectangle(box(x0, y0, x1, y1), fill=MORTAR)
    row = 0
    y = y0
    while y < y1:
        h = block_h * rnd.uniform(0.85, 1.15)
        x = x0 - (px(40) if row % 2 else px(4))
        while x < x1:
            w = block_h * rnd.uniform(1.4, 2.9)
            base = mix(STONE, STONE_L, rnd.uniform(0.0, 0.5))
            if rnd.random() < cold:
                base = mix(base, STONE_C, 0.55)
            c = tuple(int(v * tone) for v in tint(base, rnd, 0.10))
            xa, xb = max(x0, x), min(x1, x + w)
            ya, yb = y, min(y1, y + h)
            if xb - xa > px(1) and yb - ya > px(1):
                d.rectangle(box(xa + px(0.7), ya + px(0.7), xb - px(0.7), yb - px(0.7)),
                            fill=c)
                d.line([(xa + px(1), ya + px(1)), (xb - px(1), ya + px(1))],
                       fill=mix(c, (255, 250, 236), 0.34), width=max(1, int(px(0.5))))
                d.line([(xa + px(1), yb - px(1)), (xb - px(1), yb - px(1))],
                       fill=mix(c, (16, 14, 12), 0.45), width=max(1, int(px(0.7))))
                d.line([(xb - px(1), ya + px(1)), (xb - px(1), yb - px(1))],
                       fill=mix(c, (16, 14, 12), 0.30), width=max(1, int(px(0.5))))
                if rnd.random() < 0.10:                       # a chipped corner
                    cw = rnd.uniform(px(3), px(7))
                    d.polygon([(xb - cw, ya + px(1)), (xb - px(1), ya + px(1)),
                               (xb - px(1), ya + cw)],
                              fill=mix(c, (255, 250, 236), 0.30))
            x += w
        y += h
        row += 1


# ------------------------------------------------------------------ the vault
def vault(base):
    """The barrel vault: ribs, smoke, and the chains the lanterns hang from."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, 0, W, WALL_TOP), fill=(20, 19, 17))

    # courses of stone carried up over the vault, so it is the same masonry
    ashlar(d, 0, W, 0, WALL_TOP - px(6), 3, block_h=px(11), tone=0.62)

    # transverse ribs: one per bay, each a shallow arch with a lit face
    for i in range(-8, 9):
        x = CX + i * BAY + BAY // 2
        if x < -BAY or x > W + BAY:
            continue
        w = px(16)
        d.rectangle(box(x - w / 2.0, 0, x + w / 2.0, WALL_TOP - px(4)), fill=(44, 40, 34))
        d.line([(x - w / 2.0, 0), (x - w / 2.0, WALL_TOP - px(4))],
               fill=(96, 88, 74), width=max(1, int(px(0.7))))
        d.line([(x + w / 2.0, 0), (x + w / 2.0, WALL_TOP - px(4))],
               fill=(20, 18, 16), width=max(1, int(px(1.0))))
        # the arch itself: a segment over the rib, catching the lantern light
        d.arc(box(x - BAY * 0.46, -BAY * 0.30, x + BAY * 0.46, WALL_TOP + BAY * 0.30),
              200, 340, fill=(78, 72, 62), width=max(2, int(px(1.6))))
        d.arc(box(x - BAY * 0.46, -BAY * 0.30, x + BAY * 0.46, WALL_TOP + BAY * 0.30),
              200, 340, fill=(112, 104, 90), width=max(1, int(px(0.7))))

    # soot over each lantern, and the shadow the vault drops on the wall below
    soot = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(soot)
    for i in range(-8, 9):
        x = CX + i * BAY
        if x < -BAY or x > W + BAY:
            continue
        sd.ellipse(box(x - px(30), 0, x + px(30), px(40)), fill=(14, 12, 10, 84))
    base.alpha_composite(soot.filter(ImageFilter.GaussianBlur(px(8))))
    d = ImageDraw.Draw(base)
    for i in range(px(18)):
        a = int(150 * (1 - i / float(px(18))) ** 1.4)
        d.line([(0, WALL_TOP - px(6) + i), (W, WALL_TOP - px(6) + i)],
               fill=(8, 7, 6, a))
    d.line([(0, WALL_TOP - px(6)), (W, WALL_TOP - px(6))], fill=(70, 64, 54),
           width=max(1, int(px(0.8))))


# ------------------------------------------------------------------- the wall
def wall(base):
    """Ashlar, a shallow arch niche per bay, and a plinth course at the floor."""
    d = ImageDraw.Draw(base)
    ashlar(d, 0, W, WALL_TOP - px(2), FLOOR_Y - PLINTH, 11, block_h=px(17))
    # the recessed niche each guardian stands in front of
    for i in range(-9, 10):
        x = CX + i * BAY
        if x < -BAY or x > W + BAY:
            continue
        w = BAY * 0.34
        top = px(64)
        bot = FLOOR_Y - PLINTH
        d.rectangle(box(x - w, top, x + w, bot), fill=mix(STONE, STONE_D, 0.48))
        d.arc(box(x - w, top - w * 0.72, x + w, top + w * 0.72), 180, 360,
              fill=mix(STONE, STONE_D, 0.48))
        for k, tone in ((px(3), (78, 72, 62)), (px(7), (18, 16, 14))):
            d.arc(box(x - w - k, top - w * 0.72 - k, x + w + k, top + w * 0.72 + k),
                  180, 360, fill=tone, width=max(1, int(px(1.2))))
        d.line([(x - w, top), (x - w, bot)], fill=(88, 80, 68), width=max(1, int(px(0.9))))
        d.line([(x + w, top), (x + w, bot)], fill=(16, 14, 12), width=max(1, int(px(1.1))))
        # a keystone in the arch, so the niche is built and not cut out
        d.polygon([(x - px(5), top - w * 0.70), (x + px(5), top - w * 0.70),
                   (x + px(8), top - w * 0.30), (x - px(8), top - w * 0.30)],
                  fill=mix(STONE, STONE_L, 0.35))

    # plinth course, a step out of the wall, and its shadow
    d.rectangle(box(0, FLOOR_Y - PLINTH, W, FLOOR_Y), fill=mix(STONE, STONE_D, 0.25))
    d.line([(0, FLOOR_Y - PLINTH), (W, FLOOR_Y - PLINTH)], fill=(126, 116, 100),
           width=max(1, int(px(1.0))))
    d.line([(0, FLOOR_Y - PLINTH + px(2)), (W, FLOOR_Y - PLINTH + px(2))],
           fill=(20, 18, 16), width=max(1, int(px(0.6))))
    for i in range(px(8)):
        a = int(130 * (1 - i / float(px(8))) ** 1.5)
        d.line([(0, FLOOR_Y - i), (W, FLOOR_Y - i)], fill=(6, 6, 6, a))


def gate(base, cx):
    """The cold doorway at the end of the corridor: the one way out.

    Not a door that can be walked through on the stage — it is painted past the
    wall, so it reads as the lit passage beyond the hall, and everything in the
    hall is lit warm against it.
    """
    d = ImageDraw.Draw(base)
    hw = GATE_HALF
    top = px(54)
    bot = FLOOR_Y - px(2)

    # the arch, built of dressed voussoirs around the opening
    d.rectangle(box(cx - hw - px(16), top - px(10), cx + hw + px(16), bot), fill=STONE)
    for k in range(11):
        a0 = 180 + k * (180.0 / 11)
        a1 = a0 + (180.0 / 11)
        r0, r1 = hw + px(2), hw + px(17)
        d.polygon([(cx + math.cos(math.radians(a0)) * r0, top + px(6) + math.sin(math.radians(a0)) * r0 * 0.36),
                   (cx + math.cos(math.radians(a1)) * r0, top + px(6) + math.sin(math.radians(a1)) * r0 * 0.36),
                   (cx + math.cos(math.radians(a1)) * r1, top + px(6) + math.sin(math.radians(a1)) * r1 * 0.36),
                   (cx + math.cos(math.radians(a0)) * r1, top + px(6) + math.sin(math.radians(a0)) * r1 * 0.36)],
                  fill=mix(STONE, STONE_L, 0.18 + 0.30 * (k % 3 == 0)))

    # the opening: a dark passage that lifts to cold light at its far end
    d.rectangle(box(cx - hw, top, cx + hw, bot), fill=(18, 22, 24))
    d.arc(box(cx - hw, top - hw * 0.36, cx + hw, top + hw * 0.36), 180, 360,
          fill=(18, 22, 24))
    for i in range(int(bot - top)):
        t = i / max(1.0, bot - top - 1)
        d.line([(cx - hw, top + i), (cx + hw, top + i)],
               fill=mix((9, 12, 14), (112, 140, 152), t ** 2.6))
    # the reveal of the opening, in shadow, so the passage is a hole in stone
    for k in range(3):
        a = 150 - k * 45
        d.line([(cx - hw + k * px(1.5), top), (cx - hw + k * px(1.5), bot)],
               fill=(6, 7, 8, a), width=max(1, int(px(1.4))))
        d.line([(cx + hw - k * px(1.5), top), (cx + hw - k * px(1.5), bot)],
               fill=(6, 7, 8, a), width=max(1, int(px(1.4))))
    # the far door, small and pale, and the steps that lead up to it
    dw, dh = hw * 0.30, px(30)
    dy = bot - px(30)
    d.rectangle(box(cx - dw, dy - dh, cx + dw, dy), fill=mix(COOL, (255, 255, 250), 0.45))
    d.arc(box(cx - dw, dy - dh - dw * 0.5, cx + dw, dy - dh + dw * 0.5), 180, 360,
          fill=mix(COOL, (255, 255, 250), 0.5))
    for k in range(3):
        sy = dy + k * px(7)
        d.rectangle(box(cx - dw - px(4) - k * px(3), sy, cx + dw + px(4) + k * px(3),
                        sy + px(5)),
                    fill=mix((96, 104, 104), (150, 160, 160), 0.4 - 0.1 * k))
        d.line([(cx - dw - px(4) - k * px(3), sy), (cx + dw + px(4) + k * px(3), sy)],
               fill=(198, 206, 204), width=max(1, int(px(0.6))))
    # the light coming out of the passage, cold on the stone either side
    lamp(cx, top + px(26), px(150), (176, 210, 226), 76)
    lamp(cx, FLOOR_Y - px(30), px(112), (168, 200, 220), 46)
    lamp(cx, FLOOR_Y + px(14), px(86), (160, 192, 210), 24)


def lantern(base, x, y, seed):
    """An iron lantern with a red lacquer cap, hung from the vault on a chain."""
    d = ImageDraw.Draw(base)
    r = px(13)
    d.line([(x, 0), (x, y - r * 1.9)], fill=(48, 46, 44), width=max(1, int(px(0.7))))
    for k in range(4):
        d.ellipse(box(x - px(1.6), k * px(12), x + px(1.6), k * px(12) + px(5)),
                  fill=None, outline=(66, 64, 60), width=max(1, int(px(0.5))))
    # the red cap, the way the still's lanterns hang theirs
    d.polygon([(x - r * 1.25, y - r * 1.35), (x + r * 1.25, y - r * 1.35),
               (x + r * 0.55, y - r * 2.0), (x - r * 0.55, y - r * 2.0)],
              fill=mix(RED, RED_L, 0.25))
    d.line([(x - r * 1.25, y - r * 1.35), (x + r * 1.25, y - r * 1.35)],
           fill=mix(GOLD, (124, 88, 36), 0.3),
           width=max(1, int(px(0.8))))
    d.rectangle(box(x - r * 0.42, y - r * 2.5, x + r * 0.42, y - r * 1.9),
                fill=mix(IRON, IRON_L, 0.2))
    # the frame: iron uprights, glass, and the flame behind them
    d.rectangle(box(x - r, y - r * 1.3, x + r, y + r * 1.3), fill=(28, 24, 20))
    # amber glass, and a small flame inside it: a big pale disc read as a paper
    # lantern, not as an iron one with a wick in it
    d.rectangle(box(x - r * 0.82, y - r * 1.1, x + r * 0.82, y + r * 1.1),
                fill=mix((86, 50, 20), FLAME, 0.24))
    d.polygon([(x - r * 0.17, y + r * 0.55), (x + r * 0.17, y + r * 0.55),
               (x + r * 0.05, y - r * 0.30), (x - r * 0.05, y - r * 0.30)],
              fill=(255, 214, 142))
    d.ellipse(box(x - r * 0.26, y + r * 0.16, x + r * 0.26, y + r * 0.60),
              fill=mix((255, 206, 128), (236, 142, 52), 0.35))
    d.ellipse(box(x - r * 0.11, y + r * 0.24, x + r * 0.11, y + r * 0.52),
              fill=(255, 246, 210))
    for k in (-1, 0, 1):
        d.line([(x + k * r * 0.62, y - r * 1.2), (x + k * r * 0.62, y + r * 1.2)],
               fill=mix(IRON, (18, 16, 14), 0.35), width=max(1, int(px(1.5))))
    d.line([(x - r * 0.9, y), (x + r * 0.9, y)], fill=mix(IRON, (18, 16, 14), 0.3),
           width=max(1, int(px(1.1))))
    d.rectangle(box(x - r * 1.1, y + r * 1.2, x + r * 1.1, y + r * 1.5),
                fill=mix(IRON, IRON_L, 0.25))
    d.line([(x - r * 1.1, y + r * 1.2), (x + r * 1.1, y + r * 1.2)],
           fill=(150, 146, 138), width=max(1, int(px(0.6))))
    # a tassel under the lantern, as the still hangs them
    d.line([(x, y + r * 1.5), (x, y + r * 2.1)], fill=mix(RED, (60, 14, 12), 0.3),
           width=max(1, int(px(1.0))))
    d.polygon([(x - px(3), y + r * 2.0), (x + px(3), y + r * 2.0),
               (x + px(1.4), y + r * 2.9), (x - px(1.4), y + r * 2.9)],
              fill=mix(RED, RED_L, 0.3))
    lamp(x, y, px(84), (255, 180, 104), 86)
    _ = seed


def torch(base, x, y, seed):
    """A bracket torch on the wall, between two guardians."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(seed)
    d.rectangle(box(x - px(3), y - px(3), x + px(3), y + px(12)), fill=mix(IRON, IRON_L, 0.2))
    d.line([(x - px(3), y), (x - px(11), y + px(6))], fill=(64, 60, 54),
           width=max(2, int(px(2.0))))
    d.line([(x + px(3), y), (x + px(11), y + px(6))], fill=(64, 60, 54),
           width=max(2, int(px(2.0))))
    d.polygon([(x - px(9), y - px(4)), (x + px(9), y - px(4)),
               (x + px(6), y + px(4)), (x - px(6), y + px(4))], fill=(38, 32, 26))
    d.line([(x - px(9), y - px(4)), (x + px(9), y - px(4))], fill=(126, 116, 100),
           width=max(1, int(px(0.8))))
    for i in range(8):
        t = i / 7.0
        fw = px(8) * (1 - 0.80 * t)
        fy = y - px(6) - t * px(26)
        d.polygon([(x - fw, fy), (x + fw, fy), (x + fw * 0.35, fy - px(11)),
                   (x - fw * 0.30, fy - px(11))],
                  fill=mix((255, 214, 130), (226, 104, 40), t * 0.85))
    d.ellipse(box(x - px(4), y - px(16), x + px(4), y - px(9)), fill=(255, 236, 178))
    lamp(x, y - px(16), px(120), (255, 178, 100), 96)


# ---------------------------------------------------------------- the guardian
def guardian_tile(h, seed=0):
    """One bronze guardian on its plinth, as an RGBA tile h tall.

    Painted at 2x and resampled: at stage size the face is a dozen pixels, and
    an arc rasterised at 1x reads as a staircase. The figure is the still's —
    a tall corrugated crown, a snarling face under a heavy brow, layered
    lamellar armour over a big belly, both hands resting on a sword planted in
    front of it.
    """
    rnd = random.Random(seed)
    K = 2
    tw = int(round(h * 0.66))
    th = int(round(h))
    ph = int(round(th * 0.125))                 # the plinth
    base = th - ph                              # where the figure's feet are
    cx = tw / 2.0

    img = Image.new("RGBA", (tw * K, th * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # the still's guardians are nearly black shapes against the torchlight, with
    # only the edges catching it: a mid-brown figure read as a teddy bear
    bronze = mix(mix(BRONZE, (18, 14, 10), 0.52), BRONZE_L, rnd.uniform(0.0, 0.08))
    dark = mix(BRONZE, BRONZE_D, 0.45)

    def ell(x, y, rx, ry, fill):
        d.ellipse(box((x - rx) * K, (y - ry) * K, (x + rx) * K, (y + ry) * K), fill=fill)

    def rect(x0, y0, x1, y1, fill):
        d.rectangle(box(x0 * K, y0 * K, x1 * K, y1 * K), fill=fill)

    def poly(pts, fill):
        d.polygon([(x * K, y * K) for x, y in pts], fill=fill)

    def line(pts, fill, w):
        d.line([(x * K, y * K) for x, y in pts], fill=fill,
               width=max(1, int(w * K)), joint="curve")

    # ---- plinth: a dressed block with a moulded top, in shadow at its foot
    pw = tw * 0.31
    rect(cx - pw, base, cx + pw, th, mix(STONE, STONE_D, 0.15))
    rect(cx - pw * 1.12, base, cx + pw * 1.12, base + ph * 0.30,
         mix(STONE, STONE_L, 0.30))
    line([(cx - pw * 1.12, base), (cx + pw * 1.12, base)], (156, 146, 128), h * 0.008)
    for k in range(-2, 3):
        line([(cx + k * pw * 0.42, base + ph * 0.34), (cx + k * pw * 0.42, th - ph * 0.12)],
             mix(STONE, STONE_D, 0.4), h * 0.005)
    rect(cx - pw, th - ph * 0.16, cx + pw, th, mix(STONE, (16, 14, 12), 0.45))

    # ---- the armour skirt: a flared bell of overlapping lamellae
    poly([(cx - tw * 0.145, base - h * 0.235), (cx + tw * 0.145, base - h * 0.235),
          (cx + tw * 0.235, base - h * 0.020), (cx - tw * 0.235, base - h * 0.020)],
         bronze)
    for k in range(5):
        yy = base - h * (0.045 + 0.042 * k)
        wid = tw * (0.225 - 0.017 * k)
        line([(cx - wid, yy), (cx + wid, yy)], dark, h * 0.007)
        line([(cx - wid, yy - h * 0.006), (cx + wid, yy - h * 0.006)],
             mix(bronze, BRONZE_L, 0.35), h * 0.004)
    for k in range(-3, 4):
        line([(cx + k * tw * 0.062, base - h * 0.235), (cx + k * tw * 0.078, base - h * 0.02)],
             mix(bronze, BRONZE_D, 0.30), h * 0.005)
    # ---- boots, just showing under the skirt
    for sx in (-1, 1):
        poly([(cx + sx * tw * 0.035, base - h * 0.045),
              (cx + sx * tw * 0.135, base - h * 0.045),
              (cx + sx * tw * 0.150, base - h * 0.005),
              (cx + sx * tw * 0.030, base - h * 0.005)], dark)

    # ---- belly and chest: the round mass the still gives every guardian
    ell(cx, base - h * 0.395, tw * 0.196, h * 0.135, bronze)
    ell(cx, base - h * 0.500, tw * 0.176, h * 0.090, bronze)
    # a chest plate, and the folds of the coat under it
    poly([(cx - tw * 0.170, base - h * 0.575), (cx + tw * 0.170, base - h * 0.575),
          (cx + tw * 0.190, base - h * 0.470), (cx - tw * 0.190, base - h * 0.470)],
         mix(bronze, BRONZE_L, 0.18))
    for k in range(3):
        yy = base - h * (0.455 + 0.030 * k)
        wid = tw * (0.190 - 0.012 * k)
        line([(cx - wid, yy), (cx + wid, yy)], dark, h * 0.006)
    # belt: a studded band over the waist
    rect(cx - tw * 0.175, base - h * 0.330, cx + tw * 0.175, base - h * 0.295,
         mix(bronze, BRONZE_D, 0.30))
    for k in range(-3, 4):
        ell(cx + k * tw * 0.050, base - h * 0.313, tw * 0.016, h * 0.011,
            mix(BRONZE_L, GOLD, 0.4))

    # ---- shoulders and arms: both hands come down onto the sword hilt
    for sx in (-1, 1):
        # a layered pauldron, angular and tucked in: the round ball shoulders
        # the first pass used read as ears either side of the head
        poly([(cx + sx * tw * 0.055, base - h * 0.625),
              (cx + sx * tw * 0.165, base - h * 0.612),
              (cx + sx * tw * 0.192, base - h * 0.540),
              (cx + sx * tw * 0.072, base - h * 0.548)],
             mix(bronze, BRONZE_L, 0.14))
        line([(cx + sx * tw * 0.072, base - h * 0.548),
              (cx + sx * tw * 0.192, base - h * 0.540)],
             mix(bronze, BRONZE_D, 0.55), h * 0.006)
        # the arm, carried outside the torso so a sliver of wall shows between
        line([(cx + sx * tw * 0.150, base - h * 0.590),
              (cx + sx * tw * 0.214, base - h * 0.480),
              (cx + sx * tw * 0.130, base - h * 0.398)], bronze, h * 0.050)
        line([(cx + sx * tw * 0.168, base - h * 0.575),
              (cx + sx * tw * 0.222, base - h * 0.482)],
             mix(bronze, BRONZE_L, 0.40), h * 0.012)
        # the hand, closed on the grip
        ell(cx + sx * tw * 0.062, base - h * 0.380, tw * 0.040, h * 0.030,
            mix(bronze, BRONZE_D, 0.20))

    # ---- the sword: planted point down, both hands on the pommel
    sx0 = cx
    line([(sx0, base - h * 0.395), (sx0 + tw * 0.012, base - h * 0.060)],
         mix(IRON, IRON_L, 0.35), h * 0.026)
    line([(sx0 - tw * 0.010, base - h * 0.395), (sx0 + tw * 0.002, base - h * 0.060)],
         (168, 172, 170), h * 0.008)
    rect(sx0 - tw * 0.075, base - h * 0.410, sx0 + tw * 0.075, base - h * 0.392,
         mix(BRONZE_L, GOLD, 0.3))
    rect(sx0 - tw * 0.010, base - h * 0.430, sx0 + tw * 0.010, base - h * 0.405,
         mix(BRONZE_D, BRONZE, 0.4))
    ell(sx0, base - h * 0.436, tw * 0.026, h * 0.018, mix(BRONZE_L, GOLD, 0.45))

    # ---- neck, and the collar of the coat standing up behind the jaw
    rect(cx - tw * 0.048, base - h * 0.640, cx + tw * 0.048, base - h * 0.575, dark)
    poly([(cx - tw * 0.105, base - h * 0.640), (cx - tw * 0.030, base - h * 0.660),
          (cx + tw * 0.030, base - h * 0.660), (cx + tw * 0.105, base - h * 0.640),
          (cx + tw * 0.080, base - h * 0.700), (cx - tw * 0.080, base - h * 0.700)],
         mix(bronze, BRONZE_D, 0.22))

    # ---- the face: heavy brow, staring eyes, wide moustache, snarl
    hy = base - h * 0.735
    rx, ry = tw * 0.098, h * 0.062
    ell(cx, hy, rx, ry, mix(bronze, BRONZE_L, 0.10))
    poly([(cx - rx * 0.86, hy + ry * 0.10), (cx + rx * 0.86, hy + ry * 0.10),
          (cx + rx * 0.58, hy + ry * 1.35), (cx - rx * 0.58, hy + ry * 1.35)],
         mix(bronze, BRONZE_L, 0.06))                      # the jaw
    for sx in (-1, 1):
        ell(cx + sx * rx * 0.42, hy - ry * 0.06, rx * 0.27, ry * 0.21, (12, 9, 8))
        ell(cx + sx * rx * 0.42, hy - ry * 0.10, rx * 0.09, ry * 0.07, (168, 148, 112))
        line([(cx + sx * rx * 0.10, hy - ry * 0.44), (cx + sx * rx * 0.78, hy - ry * 0.60)],
             (30, 24, 20), h * 0.010)                      # the brow
        line([(cx + sx * rx * 0.14, hy + ry * 0.52), (cx + sx * rx * 0.96, hy + ry * 0.30)],
             mix(bronze, BRONZE_D, 0.5), h * 0.012)        # moustache
    line([(cx, hy - ry * 0.02), (cx, hy + ry * 0.48)], mix(bronze, BRONZE_L, 0.3), h * 0.010)
    line([(cx - rx * 0.46, hy + ry * 0.78), (cx, hy + ry * 0.92), (cx + rx * 0.46, hy + ry * 0.78)],
         (26, 20, 18), h * 0.010)                          # the mouth

    # ---- the crown: corrugated, tapering, with a finial and two side wings
    cw = tw * 0.115
    poly([(cx - cw, hy - ry * 0.95), (cx + cw, hy - ry * 0.95),
          (cx + cw * 0.46, hy - ry * 4.5), (cx - cw * 0.46, hy - ry * 4.5)], bronze)
    for k in range(-3, 4):
        line([(cx + k * cw * 0.30, hy - ry * 1.1), (cx + k * cw * 0.13, hy - ry * 4.3)],
             mix(bronze, BRONZE_D, 0.35), h * 0.006)
    rect(cx - cw * 1.30, hy - ry * 1.05, cx + cw * 1.30, hy - ry * 0.72,
         mix(bronze, BRONZE_L, 0.25))
    for k in range(-2, 3):
        ell(cx + k * cw * 0.52, hy - ry * 0.89, cw * 0.15, h * 0.006,
            mix(BRONZE_L, GOLD, 0.5))
    for sx in (-1, 1):
        poly([(cx + sx * cw * 1.05, hy - ry * 1.0),
              (cx + sx * cw * 1.85, hy - ry * 1.70),
              (cx + sx * cw * 1.45, hy - ry * 0.80)],
             mix(bronze, BRONZE_D, 0.10))
        line([(cx + sx * cw * 1.05, hy - ry * 1.0),
              (cx + sx * cw * 1.85, hy - ry * 1.70)],
             mix(bronze, BRONZE_L, 0.55), h * 0.005)
    ell(cx, hy - ry * 4.62, cw * 0.30, h * 0.012, mix(BRONZE_L, GOLD, 0.4))

    return img.resize((tw, th), Image.LANCZOS)


def guardian(base, cx, base_y, h, seed=0):
    """One guardian at base_y, with the shadow it throws on the wall behind.

    Without that shadow a figure is a flat cut-out pasted on the ashlar; with
    it, the statue stands off the wall, which is the whole depth of the stage.
    """
    tile = guardian_tile(h, seed)
    shadow = Image.new("RGBA", tile.size, (0, 0, 0, 0))
    shadow.paste((8, 7, 6, 165), (0, 0), tile.split()[3])
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(2, int(px(2)))))
    base.alpha_composite(shadow, (int(round(cx - tile.width / 2.0 + px(7))),
                                 int(round(base_y - tile.height + px(3)))))

    # a lit edge down the left of the figure, so the bronze catches the torches
    # instead of sitting on the wall as a flat shape
    mask = tile.split()[3]
    warm = ImageChops.subtract(mask, ImageChops.offset(mask, int(px(4)), int(px(3))))
    cool = ImageChops.subtract(mask, ImageChops.offset(mask, -int(px(3)), -int(px(2))))
    rim = Image.new("RGBA", tile.size, (0, 0, 0, 0))
    rim.paste((255, 198, 126, 255), (0, 0),
              ImageChops.multiply(warm, Image.new("L", tile.size, 150)))
    rim.paste((150, 176, 190, 255), (0, 0),
              ImageChops.multiply(cool, Image.new("L", tile.size, 90)))
    tile = Image.alpha_composite(tile, rim)

    base.alpha_composite(tile, (int(round(cx - tile.width / 2.0)),
                               int(round(base_y - tile.height))))


# -------------------------------------------------------------------- the floor
def floor(base):
    """Pale flagstones worn down the middle, and the light lying on them."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, FLOOR_Y, W, H), fill=FL_GRID)
    rnd = random.Random(17)
    y = FLOOR_Y
    row = 0
    while y < H:
        hgt = int(px(12) + row * px(3.6))
        tw = int(px(30) * (1 + row * 0.17))
        x = (CX % tw) - tw
        col = 0
        while x < W:
            c = tint(mix(FL_L, FL_D, rnd.uniform(0.0, 0.55)), rnd, 0.05)
            # the stone is darker where the corridor's feet have worn it
            wear = max(0.0, 1.0 - abs(x + tw / 2.0 - CX) / (px(320)))
            c = mix(c, (86, 82, 74), wear * 0.30)
            d.rectangle(box(x + px(1.0), y + px(1.0), x + tw - px(1.0), y + hgt - px(1.0)),
                        fill=c)
            d.line([(x + px(1.4), y + px(1.4)), (x + tw - px(1.4), y + px(1.4))],
                   fill=mix(c, (250, 244, 226), 0.22), width=max(1, int(px(0.5))))
            d.line([(x + px(1.4), y + hgt - px(1.6)), (x + tw - px(1.4), y + hgt - px(1.6))],
                   fill=mix(c, (20, 18, 16), 0.42), width=max(1, int(px(0.7))))
            d.line([(x + px(1.4), y + px(1.4)), (x + px(1.4), y + hgt - px(1.6))],
                   fill=mix(c, (24, 22, 19), 0.28), width=max(1, int(px(0.5))))
            if rnd.random() < 0.18:                     # a chip or a stain
                sx = x + rnd.uniform(px(4), max(px(5), tw - px(4)))
                sy = y + rnd.uniform(px(3), max(px(4), hgt - px(3)))
                d.line([(sx, sy), (sx + rnd.uniform(-px(8), px(8)),
                                   sy + rnd.uniform(px(1), px(5)))],
                       fill=mix(c, (48, 44, 38), 0.32), width=max(1, int(px(0.4))))
            x += tw
            col += 1
        y += hgt
        row += 1

    # the light from the door lying down the middle of the corridor
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.polygon([(CX - px(60), FLOOR_Y), (CX + px(60), FLOOR_Y),
                (CX + px(190), H), (CX - px(190), H)],
               fill=(190, 214, 226, 46))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(px(16))))
    # and the lanterns' warm pools running towards the camera
    warm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(warm)
    for i in range(-8, 9):
        x = CX + i * BAY
        if x < -BAY or x > W + BAY:
            continue
        wd.polygon([(x - px(24), FLOOR_Y), (x + px(24), FLOOR_Y),
                    (x + px(58), H), (x - px(58), H)], fill=(255, 176, 96, 22))
    base.alpha_composite(warm.filter(ImageFilter.GaussianBlur(px(14))))


# ------------------------------------------------------------------- the front
def foreground():
    """Dust in the lantern light and the dark the camera brings with it."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(71)
    for i in range(px(46)):
        a = int(170 * (1 - i / float(px(46))) ** 1.6)
        d.line([(0, H - i), (W, H - i)], fill=(6, 5, 5, a))
    for _ in range(220):
        x = rnd.uniform(0, W)
        y = rnd.uniform(WALL_TOP, H - px(6))
        r = rnd.uniform(px(0.8), px(2.4))
        d.ellipse(box(x - r, y - r, x + r, y + r),
                  fill=(255, 210, 152, rnd.randint(20, 64)))
    for k in range(6):
        cx0 = px(300) + k * px(1200)
        d.ellipse(box(cx0 - px(150), H - px(120), cx0 + px(150), H + px(10)),
                  fill=(24, 18, 14, 26))
    return fg.filter(ImageFilter.GaussianBlur(px(1.6)))


# -------------------------------------------------------------------- the arena
def paint():
    LIGHTS.clear()
    base = hd.blank([(0, (12, 11, 10)), (WALL_TOP, (26, 24, 21)),
                     (px(120), (40, 36, 30)), (FLOOR_Y, (48, 42, 34)),
                     (H, (26, 22, 18))])

    vault(base)
    wall(base)
    gate(base, CX)

    # the guardians: one a bay, each a little different, on its plinth
    for i in range(-9, 10):
        x = CX + i * BAY
        if x < -BAY or x > W + BAY:
            continue
        h = px(118) + (px(8) if i % 5 == 0 else 0)
        guardian(base, x, FLOOR_Y, h, seed=i * 17 + 3)
        lamp(x, FLOOR_Y - px(58), px(70), (255, 176, 98), 26)

    # brackets between the guardians, and a lantern over each of them
    for i in range(-9, 10):
        x = CX + i * BAY + BAY // 2
        if x < -BAY or x > W + BAY:
            continue
        torch(base, x, px(118), i + 40)
    for i in range(-9, 10):
        x = CX + i * BAY
        if x < -BAY or x > W + BAY:
            continue
        # hung high, off the vault: at face height the tassel fell across every
        # guardian's face and read as a red stripe painted on it
        lantern(base, x, px(36), i + 60)

    floor(base)

    base = hd.shade(base, [(hd.light(cx, cy, r, col, int(peak * 0.80)),
                            max(8, int(r * 0.30)), 1.05)
                           for cx, cy, r, col, peak in LIGHTS])
    base = hd.finish(base, 9, 3, 0.52, FLOOR_Y)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


def main():
    hd.STAGES["forbidden_hall"] = ("Forbidden Hall", paint)
    hd.build("forbidden_hall")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# @@SECTION@@
