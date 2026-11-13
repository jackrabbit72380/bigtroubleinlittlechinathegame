"""Waterfront Docks: the harbour quay at night.

Painted as a wall across the play plane: a night sky over a far bank of towers,
the harbour water with a junk riding at her mooring, the stone quay wall with its
coping and iron rings, the corrugated shed at the west end, a stack of shipping
containers at the east, crates and barrels and a hawser along the wall, and dock
lamps burning warm over wet planks. The fighters stand on the plank deck in front
of all of it; every prop is based on the floor line and nothing comes out into the
play plane to stand on anybody's feet.

The match-start view is the centre 1920 px of the 8192-wide canvas, so the shed,
the junk, the lamps and the cargo that read at once are placed between units 640
and 1180; the rest carries the level as the camera travels.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960, localcoord 1920x1080, camera travel +/-3136.

Run:  python3 tools/stage_waterfront_docks.py     (part of tools/build_all.py)
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

SKY = px(50)                       # 225: the far bank's towers begin
CITY = px(74)                      # 333: the waterline under them
QUAY = px(126)                     # 567: the top of the quay wall
PLINTH = FLOOR_Y - px(2)           # 891: the line everything stands on

SHED = (px(300), px(742))          # the corrugated shed, its door at the left edge
JUNK = (px(806), px(1114))         # the junk riding at her mooring, centre of the view
CONTAINERS = (px(1140), px(1364))  # the box stack at the east end
CRANE = (px(640), px(704))         # the jib crane over the quay

NIGHT_T = (6, 7, 16)
NIGHT_B = (18, 24, 42)
HORIZON = (52, 62, 92)
FAR = (14, 18, 30)
FAR_L = (34, 42, 64)
HULL = (30, 26, 26)
WATER_C = (16, 26, 40)
WATER_L = (48, 68, 94)
STONE = (64, 62, 58)
STONE_L = (104, 100, 92)
STONE_D = (30, 28, 28)
STEEL = (104, 110, 116)
STEEL_D = (44, 48, 54)
RUST = (128, 64, 40)
RUST_L = (176, 98, 58)
RUST_D = (72, 34, 22)
PINE = (124, 86, 48)
PINE_L = (176, 128, 78)
PINE_D = (62, 42, 24)
ROPE = (158, 134, 92)
WARM = (255, 198, 132)
LAMP_GLASS = (255, 238, 198)
DECK = (50, 43, 38)
DECK_L = (78, 67, 58)
DECK_D = (22, 19, 18)

LIGHTS = []

def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def tint(c, rnd, amt=0.06):
    return tuple(max(0, min(255, int(v * (1 + rnd.uniform(-amt, amt))))) for v in c)


def box(x0, y0, x1, y1):
    """Normalised corners: PIL refuses a rectangle drawn bottom-up."""
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def lamp(cx, cy, r, color=WARM, peak=140):
    LIGHTS.append((cx, cy, r, color, peak))


def contact(base, cx, base_y, w, alpha=170, depth=None):
    """The soft shadow a prop drops where its base meets what it stands on."""
    depth = px(8) if depth is None else depth
    bw = w * 1.28
    pad = int(px(12))
    lw, lh = int(bw) + 2 * pad, int(depth * 4) + 2 * pad
    sh = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    d.ellipse(box(pad, pad + lh * 0.22, lw - pad, pad + lh * 0.78), fill=(5, 4, 4, alpha))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(px(5))),
                         (int(cx - bw / 2.0 - pad), int(base_y - pad - lh * 0.5)))


# ----------------------------------------------------------------- the harbour
def night_sky(base):
    """Night over the harbour: the gradient, cloud bars, a few stars."""
    d = ImageDraw.Draw(base)
    for i in range(int(SKY)):
        d.line([(0, i), (W, i)], fill=mix(NIGHT_T, NIGHT_B, (i / float(SKY)) ** 0.8))
    for i in range(int(px(30))):
        y = SKY - px(30) + i
        d.line([(0, y), (W, y)], fill=mix(NIGHT_B, (78, 62, 60), 0.5 * (1 - i / float(px(30)))))
    rnd = random.Random(11)
    for _ in range(10):
        cy = rnd.uniform(px(6), SKY - px(14))
        cw = rnd.uniform(px(240), px(620))
        cx = rnd.uniform(0, W)
        ch = rnd.uniform(px(4), px(10))
        d.ellipse(box(cx, cy, cx + cw, cy + ch), fill=mix(NIGHT_B, (66, 62, 78), rnd.uniform(0.12, 0.4)))
        d.line([(cx, cy + ch), (cx + cw, cy + ch)],
               fill=mix(NIGHT_T, (116, 102, 100), rnd.uniform(0.1, 0.3)),
               width=max(1, int(px(1.0))))
    for _ in range(90):
        sx, sy = rnd.uniform(0, W), rnd.uniform(0, SKY * 0.7)
        r = rnd.uniform(px(0.3), px(0.7))
        d.ellipse(box(sx - r, sy - r, sx + r, sy + r),
                  fill=mix((120, 130, 160), (235, 240, 255), rnd.uniform(0.2, 1.0)))


def far_bank(base):
    """The town across the harbour: two hazed rows of towers and their windows."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(5)
    for i in range(int(CITY) - int(SKY)):
        d.line([(0, SKY + i), (W, SKY + i)],
               fill=mix(HORIZON, (22, 24, 36), i / float(max(1, CITY - SKY))))
    for layer, (col, hmax) in enumerate(((mix(FAR, HORIZON, 0.4), px(36)),
                                         (FAR, px(56)))):
        x = -rnd.uniform(0, px(60))
        while x < W:
            bw = rnd.uniform(px(58), px(168))
            bh = rnd.uniform(px(10), hmax)
            top = SKY + px(16) - bh
            d.rectangle(box(x, top, x + bw, CITY),
                        fill=mix(col, FAR_L, rnd.uniform(0.0, 0.2) + 0.1 * layer))
            for ci in range(max(1, int(bw // px(24)))):
                if rnd.random() < 0.34:
                    continue
                wx = x + px(9) + ci * px(24)
                lit = rnd.random() < 0.55
                for wy in range(int(top + px(7)), int(CITY - px(6)), int(px(9))):
                    if not lit and rnd.random() < 0.72:
                        continue
                    d.rectangle(box(wx, wy, wx + px(5), wy + px(5)),
                                fill=mix((42, 44, 54), (244, 208, 148), rnd.uniform(0.1, 0.8)))
            x += bw + rnd.uniform(px(2), px(16))
    for bx in (px(300), px(1500)):
        d.rectangle(box(bx, CITY - px(72), bx + px(6), CITY), fill=(20, 22, 28))
        d.line([(bx + px(3), CITY - px(72)), (bx + px(3), CITY)],
               fill=(50, 54, 64), width=max(1, int(px(1.1))))
        d.line([(bx + px(3), CITY - px(72)), (bx - px(48), CITY - px(62))],
               fill=(26, 28, 34), width=max(2, int(px(2.2))))
    haze = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(haze).rectangle(box(0, CITY - px(30), W, CITY + px(4)),
                                   fill=(84, 106, 140, 42))
    base.alpha_composite(haze.filter(ImageFilter.GaussianBlur(px(14))))
    for lx in (px(180), px(470), px(760), px(1240), px(1620)):
        lamp(lx, CITY + px(2), px(150), (244, 200, 140), 24)


def water(base):
    """The harbour between the far bank and the quay, and the town's reflection."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(23)
    top, bot = CITY, QUAY
    for i in range(int(bot - top)):
        d.line([(0, top + i), (W, top + i)],
               fill=mix(WATER_L, WATER_C, (i / float(bot - top)) ** 0.8))
    for _ in range(520):
        y = rnd.uniform(top + px(2), bot - px(26))
        x = rnd.uniform(0, W)
        ln = rnd.uniform(px(5), px(26))
        d.line([(x, y), (x + ln, y)],
               fill=mix(WATER_C, (150, 174, 200), rnd.uniform(0.08, 0.40)), width=1)
    for lx in (px(180), px(470), px(760), px(1240), px(1620)):
        refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        rd = ImageDraw.Draw(refl)
        for k in range(int(bot - top - px(26))):
            a = int(52 * (1 - k / float(bot - top)) ** 1.4)
            rd.line([(lx - px(5) + rnd.uniform(-px(2), px(2)), top + px(3) + k),
                     (lx + px(5) + rnd.uniform(-px(2), px(2)), top + px(3) + k)],
                    fill=(240, 198, 142, a), width=max(1, int(px(1.0))))
        base.alpha_composite(refl.filter(ImageFilter.GaussianBlur(px(2.4))))
    for i in range(int(px(26))):
        d.line([(0, bot - px(26) + i), (W, bot - px(26) + i)],
               fill=mix(WATER_C, (6, 8, 12), 0.65 * (i / float(px(26)))))


def junk(base):
    """The junk at her mooring: upswept bow, high stern, battened lug sails."""
    d = ImageDraw.Draw(base)
    x0, x1 = JUNK
    L = x1 - x0
    wl = QUAY - px(9)                   # floating right against the quay face
    sheer = wl - px(10)
    top = [(x0, sheer + px(12)), (x0 + L * 0.05, sheer - px(3)),
           (x0 + L * 0.18, sheer + px(1)), (x0 + L * 0.44, sheer + px(6)),
           (x0 + L * 0.70, sheer + px(3)), (x1 - L * 0.05, sheer - px(5)),
           (x1, sheer - px(12))]
    d.polygon(top + [(x1, wl + px(2)), (x0 + L * 0.02, wl + px(2))], fill=HULL)
    for k, off in enumerate((px(5), px(12), px(19))):
        d.line([(x + px(1), y + off) for x, y in top],
               fill=mix(HULL, (86, 70, 60), 0.26 - 0.07 * k), width=max(1, int(px(1.2))))
    d.line(top, fill=mix(HULL, (146, 116, 94), 0.5), width=max(2, int(px(2.0))))
    d.line([(x0 + L * 0.02, wl + px(2)), (x1, wl + px(2))], fill=(6, 8, 10),
           width=max(2, int(px(2.0))))
    band = base.crop((int(x0), int(sheer - px(8)), int(x1), int(wl + px(2)))).convert("RGBA")
    refl = band.transpose(Image.FLIP_TOP_BOTTOM).filter(ImageFilter.GaussianBlur(px(3)))
    refl.putalpha(Image.new("L", refl.size, 52))
    base.alpha_composite(refl, (int(x0), int(wl + px(2))))
    d.rectangle(box(x0 + L * 0.03, wl + px(2), x1, wl + px(6)), fill=(4, 5, 8, 120))
    d.polygon([(x1 - L * 0.20, sheer - px(2)), (x1 - px(2), sheer - px(14)),
               (x1 - px(2), sheer + px(4)), (x1 - L * 0.19, sheer + px(8))],
              fill=mix(HULL, (56, 46, 42), 0.42))
    d.rectangle(box(x1 - L * 0.165, sheer - px(24), x1 - L * 0.055, sheer + px(1)),
                fill=(22, 18, 18))
    d.rectangle(box(x1 - L * 0.142, sheer - px(20), x1 - L * 0.082, sheer - px(6)),
                fill=(226, 176, 108))
    d.line([(x1 - L * 0.142, sheer - px(13)), (x1 - L * 0.082, sheer - px(13))],
           fill=(60, 44, 30), width=max(1, int(px(1.0))))
    d.line([(x1 - L * 0.035, sheer - px(22)), (x1 - L * 0.035, sheer + px(1))],
           fill=(30, 26, 24), width=max(2, int(px(2.0))))
    # the roof of the stern house, and a rail along it
    d.polygon([(x1 - L * 0.19, sheer - px(24)), (x1 - L * 0.03, sheer - px(30)),
               (x1 - L * 0.01, sheer - px(26)), (x1 - L * 0.17, sheer - px(20))],
              fill=mix(HULL, (74, 62, 52), 0.5))
    for k in range(5):
        rxp = x1 - L * (0.185 - 0.036 * k)
        d.line([(rxp, sheer - px(26)), (rxp, sheer - px(18))], fill=(30, 26, 24),
               width=max(1, int(px(1.0))))
    lamp(x1 - L * 0.112, sheer - px(13), px(190), (255, 206, 150), 74)
    d.rectangle(box(x0 + L * 0.07, sheer - px(7), x0 + L * 0.15, sheer + px(2)),
                fill=mix(HULL, (74, 62, 54), 0.4))
    d.ellipse(box(x0 + L * 0.085, sheer - px(11), x0 + L * 0.135, sheer - px(3)),
              outline=(120, 108, 92), width=max(1, int(px(1.2))))
    d.line([(x0 + L * 0.11, sheer + px(2)), (x0 + L * 0.09, wl + px(8))],
           fill=(84, 76, 62), width=max(1, int(px(1.0))))
    for mast_x, mast_top, spread, shade in (
            (x0 + L * 0.30, sheer - px(56), px(52), 0.0),
            (x0 + L * 0.62, sheer - px(66), px(58), 0.05)):
        d.rectangle(box(mast_x - px(2), mast_top, mast_x + px(2), sheer + px(2)),
                    fill=(24, 20, 20))
        d.line([(mast_x + px(2), mast_top), (mast_x + px(2), sheer + px(2))],
               fill=(96, 84, 72), width=max(1, int(px(1.0))))
        sail_top, sail_bot = mast_top + px(8), sheer - px(8)
        cloth = mix((40, 35, 32), (86, 74, 62), 0.32 + shade)
        d.polygon([(mast_x - spread * 0.30, sail_top),
                   (mast_x + spread * 0.58, sail_top + px(9)),
                   (mast_x + spread, sail_bot),
                   (mast_x - spread * 0.86, sail_bot - px(4))], fill=cloth)
        n = max(3, int((sail_bot - sail_top) / px(10)))
        for b in range(n):
            f = (b + 0.5) / n
            y = sail_top + (sail_bot - sail_top) * f
            lx = mast_x - spread * (0.30 + 0.56 * f)
            rx = mast_x + spread * (0.58 + 0.42 * f)
            d.line([(lx, y), (rx - px(2), y + px(2))],
                   fill=mix(cloth, (18, 15, 14), 0.55), width=max(1, int(px(1.4))))
            d.line([(lx, y + px(2)), (rx - px(2), y + px(4))],
                   fill=mix(cloth, (150, 126, 100), 0.28), width=max(1, int(px(1.0))))
        d.line([(mast_x, sail_top), (mast_x, sail_bot)], fill=(30, 25, 22),
               width=max(1, int(px(1.2))))
        d.line([(mast_x, sail_top), (mast_x - spread * 1.45, sheer + px(6))],
               fill=(64, 56, 46), width=max(1, int(px(1.0))))
        d.line([(mast_x, sail_top + px(3)), (mast_x + spread * 0.95, sheer - px(2))],
               fill=(56, 48, 40), width=max(1, int(px(1.0))))
    lamp(x0 + L * 0.30, sheer - px(60), px(210), (255, 224, 172), 44)
    d.line([(x0 + L * 0.06, sheer), (x0 - px(24), QUAY - px(2))],
           fill=(96, 86, 68), width=max(2, int(px(1.8))))


def quay_wall(base):
    """The stone face of the quay: courses, its dark coping, rings and weed."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(31)
    d.rectangle(box(0, QUAY, W, PLINTH), fill=STONE_D)
    course = px(11)
    row = 0
    y = QUAY
    while y < PLINTH:
        x = -rnd.uniform(0, px(50))
        while x < W:
            bw = rnd.uniform(px(50), px(104))
            depth = (y - QUAY) / float(max(1.0, PLINTH - QUAY))
            c = mix(STONE, STONE_D, 0.30 + 0.34 * depth + 0.08 * (row % 2))
            d.rectangle(box(x, y, x + bw - px(2), y + course - px(1)), fill=tint(c, rnd, 0.05))
            d.line([(x, y), (x + bw - px(2), y)], fill=mix(c, STONE_L, 0.38),
                   width=max(1, int(px(1.0))))
            x += bw
        y += course
        row += 1
    d.rectangle(box(0, QUAY - px(7), W, QUAY + px(3)), fill=mix(STONE_D, STONE, 0.30))
    d.line([(0, QUAY - px(7)), (W, QUAY - px(7))], fill=mix(STONE, STONE_L, 0.30),
           width=max(1, int(px(1.4))))
    d.line([(0, QUAY + px(3)), (W, QUAY + px(3))], fill=(9, 9, 11),
           width=max(2, int(px(1.8))))
    for _ in range(420):
        x = rnd.uniform(0, W)
        if rnd.random() < 0.7:
            y = rnd.uniform(PLINTH - px(46), PLINTH - px(2))
        else:
            y = rnd.uniform(QUAY + px(4), QUAY + px(22))
        r = rnd.uniform(px(0.9), px(2.6))
        d.ellipse(box(x - r, y - r, x + r, y + r),
                  fill=mix((28, 40, 26), (66, 84, 48), rnd.uniform(0.1, 0.8)))
    # a repaired patch, and the stain running down from the coping
    patch = box(px(1020), QUAY + px(30), px(1108), QUAY + px(92))
    d.rectangle(patch, fill=mix(STONE, STONE_D, 0.26))
    for k in range(6):
        yy = patch[1] + k * (patch[3] - patch[1]) / 6.0
        d.line([(patch[0], yy), (patch[2], yy)], fill=mix(STONE_D, (16, 16, 18), 0.4),
               width=max(1, int(px(1.0))))
    stain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(stain).polygon(
        [(px(700), QUAY), (px(742), QUAY), (px(754), PLINTH), (px(686), PLINTH)],
        fill=(8, 10, 12, 90))
    base.alpha_composite(stain.filter(ImageFilter.GaussianBlur(px(7))))
    # the ladder, bolted to the face, going down into the harbour
    lx = px(1092)
    for k in range(2):
        d.line([(lx + k * px(16), QUAY + px(4)), (lx + k * px(16), PLINTH - px(4))],
               fill=(66, 66, 62), width=max(2, int(px(1.8))))
        d.line([(lx + k * px(16) - px(1), QUAY + px(4)), (lx + k * px(16) - px(1), PLINTH - px(4))],
               fill=(112, 112, 104), width=max(1, int(px(0.8))))
    for ry in range(int(QUAY + px(10)), int(PLINTH - px(6)), int(px(13))):
        d.line([(lx, ry), (lx + px(16), ry)], fill=(76, 76, 72), width=max(2, int(px(1.6))))
    for rx in (px(700), px(760), px(980), px(1040), px(1240), px(240), px(1500)):
        d.ellipse(box(rx - px(9), QUAY + px(30), rx + px(9), QUAY + px(48)),
                  outline=(56, 56, 54), width=max(2, int(px(2.2))))
        d.ellipse(box(rx - px(9), QUAY + px(30), rx + px(9), QUAY + px(48)),
                  outline=(112, 110, 100), width=max(1, int(px(0.9))))


def shed(base):
    """Corrugated steel with a roller door half up, and a lamp over it."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(41)
    x0, x1 = SHED
    top = SKY + px(10)
    d.rectangle(box(x0, top, x1, PLINTH), fill=mix(STEEL_D, (32, 34, 40), 0.35))
    for x in range(int(x0), int(x1), int(px(8))):
        d.rectangle(box(x, top, x + px(5), PLINTH), fill=mix(STEEL, STEEL_D, 0.74))
        d.line([(x, top), (x, PLINTH)], fill=mix(STEEL, (128, 136, 146), 0.28),
               width=max(1, int(px(0.9))))
        d.line([(x + px(5), top), (x + px(5), PLINTH)], fill=(22, 24, 28),
               width=max(1, int(px(0.8))))
    # the roller door, half up, with the dark of the shed inside
    dx0, dx1 = x0 + px(46), x0 + px(214)
    dtop = top + px(26)
    d.rectangle(box(dx0, dtop, dx1, PLINTH), fill=(9, 10, 12))
    slats = dtop + px(64)
    for sy in range(int(dtop), int(slats), int(px(6))):
        d.line([(dx0, sy), (dx1, sy)], fill=mix(STEEL, (92, 96, 102), 0.5),
               width=max(2, int(px(1.8))))
    d.rectangle(box(dx0 - px(5), slats, dx1 + px(5), slats + px(5)), fill=(26, 28, 32))
    for _ in range(3):
        d.ellipse(box(rnd.uniform(dx1 + px(10), x1 - px(10)), rnd.uniform(top + px(20), PLINTH - px(30)),
                      rnd.uniform(px(8), px(24)), rnd.uniform(px(12), px(32))),
                  fill=mix(RUST_D, RUST, rnd.uniform(0.2, 0.6)))
    # the wall lamp over the door
    lx, ly = (dx0 + dx1) / 2.0, top + px(12)
    d.line([(lx, ly), (lx, ly + px(8))], fill=(28, 28, 30), width=max(2, int(px(1.6))))
    d.polygon([(lx - px(10), ly + px(8)), (lx + px(10), ly + px(8)),
               (lx + px(7), ly + px(20)), (lx - px(7), ly + px(20))], fill=(56, 54, 50))
    d.rectangle(box(lx - px(7), ly + px(11), lx + px(7), ly + px(18)), fill=LAMP_GLASS)
    lamp(lx, ly + px(16), px(330), WARM, 165)


def wall_dressing(base):
    """A net hung on the quay wall, a pier sign, a tarpaulin over a low stack."""
    d = ImageDraw.Draw(base)
    nx0, nx1 = px(846), px(986)
    ny0, ny1 = QUAY + px(26), QUAY + px(96)
    for hx in (nx0, nx1):
        d.line([(hx, ny0 - px(12)), (hx, ny0)], fill=(66, 64, 58), width=max(2, int(px(2.2))))
        d.rectangle(box(hx - px(3), ny0 - px(14), hx + px(3), ny0 - px(8)), fill=(80, 78, 70))
    # the net hangs in slack folds: its foot sags between the hooks
    net = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nd = ImageDraw.Draw(net)
    mesh = px(13)
    for k in range(int((nx1 - nx0) / mesh) + 2):
        x = nx0 + k * mesh
        sag = math.sin(k * 0.7) * px(5)
        nd.line([(x, ny0), (x + (ny1 - ny0) * 0.13, ny1 + sag)],
                fill=(186, 182, 160, 190), width=max(1, int(px(0.9))))
        nd.line([(x, ny0), (x - (ny1 - ny0) * 0.13, ny1 + sag)],
                fill=(186, 182, 160, 190), width=max(1, int(px(0.9))))
    for k in range(int((ny1 - ny0) / mesh) + 1):
        y = ny0 + k * mesh
        bow = math.sin(k * 1.3) * px(4)
        nd.line([(nx0, y), (nx1, y + bow)], fill=(170, 166, 146, 175), width=1)
    base.alpha_composite(net.filter(ImageFilter.GaussianBlur(px(0.8))))
    for k in range(8):
        fx = nx0 + px(11) + k * (nx1 - nx0 - px(22)) / 7.0
        fy = ny1 + math.sin(k * 1.1) * px(4)
        d.ellipse(box(fx - px(4), fy - px(3), fx + px(4), fy + px(5)), fill=(178, 140, 90))
        d.line([(fx, fy - px(9)), (fx, fy - px(3))], fill=(120, 112, 92),
               width=max(1, int(px(1.0))))
    sx0, sx1 = px(1030), px(1168)
    sy0 = QUAY + px(20)
    sy1 = sy0 + px(44)
    d.rectangle(box(sx0 - px(6), sy0 + px(10), sx0 + px(4), sy0 + px(16)), fill=(40, 36, 30))
    d.rectangle(box(sx1 - px(4), sy0 + px(10), sx1 + px(6), sy0 + px(16)), fill=(40, 36, 30))
    d.rectangle(box(sx0, sy0, sx1, sy1), fill=mix(PINE_D, (24, 20, 18), 0.45))
    for k in range(4):
        d.line([(sx0 + px(2), sy0 + px(6) + k * px(11)), (sx1 - px(2), sy0 + px(6) + k * px(11))],
               fill=mix(PINE, PINE_D, 0.72), width=1)
    d.rectangle(box(sx0, sy0, sx1, sy1), outline=(28, 24, 20), width=max(2, int(px(2.4))))
    d.rectangle(box(sx0 + px(5), sy0 + px(5), sx1 - px(5), sy1 - px(5)),
                outline=mix(RUST_D, RUST, 0.30), width=max(1, int(px(1.6))))
    for k, wfrac in enumerate((0.62, 0.78, 0.44)):
        bx0 = sx0 + px(16)
        bx1 = bx0 + (sx1 - sx0 - px(32)) * wfrac
        d.rectangle(box(bx0, sy0 + px(11) + k * px(10), bx1, sy0 + px(19) + k * px(10)),
                    fill=mix((196, 188, 164), PINE_D, 0.34))
    d.line([(sx0 + px(14), sy1 - px(9)), (sx1 - px(16), sy1 - px(9))],
           fill=mix((150, 74, 52), PINE_D, 0.3), width=max(2, int(px(1.6))))
    tx0, tx1 = px(688), px(800)
    ty0 = PLINTH - px(30)
    d.polygon([(tx0, PLINTH), (tx0 + px(6), ty0), (tx0 + px(34), ty0 - px(8)),
               (tx1 - px(40), ty0 - px(6)), (tx1 - px(6), ty0 + px(4)), (tx1, PLINTH)],
              fill=mix((58, 64, 52), (30, 34, 28), 0.35))
    for k in range(5):
        fx = tx0 + px(12) + k * (tx1 - tx0 - px(24)) / 4.0
        d.line([(fx, ty0 + px(2)), (fx + px(3), PLINTH)], fill=(24, 28, 24),
               width=max(1, int(px(1.2))))
    d.line([(tx0 + px(8), ty0 + px(4)), (tx1 - px(10), ty0 + px(6))], fill=(18, 20, 18),
           width=max(2, int(px(2.0))))
    contact(base, (tx0 + tx1) / 2.0, PLINTH, tx1 - tx0, alpha=180, depth=px(10))


def containers(base):
    """The stack of boxes at the east end, with their corner castings."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(53)
    x0, x1 = CONTAINERS
    y = PLINTH
    for h, col in ((px(52), RUST), (px(46), (46, 78, 96)), (px(44), (60, 88, 50))):
        y -= h
        d.rectangle(box(x0, y, x1, y + h), fill=mix(col, (12, 12, 14), 0.42))
        for rx in range(int(x0 + px(10)), int(x1) - int(px(10)), int(px(20))):
            d.rectangle(box(rx, y + px(8), rx + px(11), y + h - px(8)),
                        fill=mix(col, (20, 18, 18), 0.32))
            d.line([(rx, y + px(8)), (rx, y + h - px(8))],
                   fill=mix(col, RUST_L if col == RUST else (132, 162, 182), 0.35),
                   width=max(1, int(px(1.0))))
        d.line([(x0, y), (x1, y)], fill=mix(col, (196, 196, 188), 0.35), width=max(2, int(px(1.6))))
        d.rectangle(box(x0, y, x1, y + px(5)), fill=mix(col, (12, 12, 14), 0.4))
        d.rectangle(box(x0, y + h - px(5), x1, y + h), fill=mix(col, (12, 12, 14), 0.5))
        for _ in range(3):
            d.rectangle(box(rnd.uniform(x0 + px(40), x1 - px(70)), y + px(12),
                            rnd.uniform(x0 + px(70), x1 - px(40)), y + px(24)),
                        fill=mix((198, 192, 172), col, 0.55))
    contact(base, (x0 + x1) / 2.0, PLINTH, (x1 - x0), alpha=210, depth=px(18))
    lamp(x1 - px(10), PLINTH - px(40), px(250), (255, 204, 152), 52)


def crane(base):
    """A little jib crane on the quay, its hook hanging over the water."""
    d = ImageDraw.Draw(base)
    x0, x1 = CRANE
    post = (x0 + x1) / 2.0
    d.rectangle(box(post - px(8), SKY + px(30), post + px(8), PLINTH), fill=(54, 58, 64))
    d.line([(post - px(8), SKY + px(30)), (post - px(8), PLINTH)], fill=(124, 132, 142),
           width=max(1, int(px(1.2))))
    tip = (post - px(104), SKY + px(2))
    d.line([(post, SKY + px(40)), tip], fill=(60, 64, 70), width=max(3, int(px(2.6))))
    d.line([(post, SKY + px(40)), tip], fill=(128, 136, 146), width=max(1, int(px(1.0))))
    d.line([(post, SKY + px(18)), (tip[0] + px(14), tip[1] + px(8))], fill=(74, 78, 84),
           width=max(1, int(px(1.2))))
    d.line([tip, (tip[0] + px(4), CITY + px(60))], fill=(104, 108, 112),
           width=max(1, int(px(1.0))))
    d.rectangle(box(tip[0], CITY + px(60), tip[0] + px(8), CITY + px(72)), fill=(88, 92, 96))
    contact(base, post, PLINTH, px(30), alpha=190, depth=px(12))
    lamp(post, SKY + px(46), px(150), (255, 214, 164), 34)


def lamp_post(base, cx, height, arm_dir=-1):
    """An iron post on the deck, its arm out over the quay, the lamp under it."""
    d = ImageDraw.Draw(base)
    top = PLINTH - height
    contact(base, cx, PLINTH, px(22), alpha=190, depth=px(12))
    d.rectangle(box(cx - px(5), top, cx + px(5), PLINTH), fill=(44, 46, 50))
    d.line([(cx - px(5), top), (cx - px(5), PLINTH)], fill=(120, 128, 138),
           width=max(1, int(px(1.1))))
    # the base plate and its bolts
    d.rectangle(box(cx - px(12), PLINTH - px(7), cx + px(12), PLINTH), fill=(38, 40, 44))
    d.line([(cx - px(12), PLINTH - px(7)), (cx + px(12), PLINTH - px(7))],
           fill=(96, 100, 106), width=max(1, int(px(1.0))))
    # the arm, braced, and the shade hanging off it
    ax = cx + arm_dir * px(30)
    d.line([(cx, top + px(6)), (ax, top + px(2))], fill=(44, 46, 50), width=max(2, int(px(2.0))))
    d.line([(cx, top + px(18)), (ax, top + px(3))], fill=(58, 62, 68), width=max(1, int(px(1.2))))
    d.polygon([(ax - px(11), top + px(2)), (ax + px(11), top + px(2)),
               (ax + px(7), top + px(13)), (ax - px(7), top + px(13))], fill=(54, 52, 48))
    d.rectangle(box(ax - px(7), top + px(5), ax + px(7), top + px(11)), fill=LAMP_GLASS)
    lamp(ax, top + px(22), px(320), WARM, 120)


def cargo(base):
    """Crates, barrels, a hawser and a fish box, all based on the planks."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(67)

    def crate(cx, w, h):
        y1 = PLINTH
        y0 = y1 - h
        contact(base, cx, y1, w + px(6), alpha=190, depth=px(12))
        d.rectangle(box(cx - w / 2.0, y0, cx + w / 2.0, y1), fill=mix(PINE, PINE_D, 0.40))
        for k in range(max(2, int(h // px(10)))):
            y = y0 + px(6) + k * px(10)
            d.rectangle(box(cx - w / 2.0 + px(2), y, cx + w / 2.0 - px(2), y + px(8)),
                        fill=tint(mix(PINE, PINE_L, 0.22 + 0.12 * (k % 2)), rnd))
            d.line([(cx - w / 2.0 + px(2), y), (cx + w / 2.0 - px(2), y)],
                   fill=mix(PINE, PINE_L, 0.55), width=max(1, int(px(1.0))))
        d.rectangle(box(cx - w / 2.0, y0, cx + w / 2.0, y1),
                    outline=mix(PINE, PINE_D, 0.55), width=max(2, int(px(1.4))))

    def barrel(cx, w, h):
        y1 = PLINTH
        y0 = y1 - h
        contact(base, cx, y1, w + px(4), alpha=190, depth=px(10))
        d.rectangle(box(cx - w / 2.0, y0 + px(4), cx + w / 2.0, y1 - px(3)),
                    fill=mix(RUST_D, (50, 32, 24), 0.3))
        for k in range(6):
            y = y0 + px(6) + k * (h - px(12)) / 6.0
            d.line([(cx - w / 2.0, y), (cx + w / 2.0, y)],
                   fill=mix((58, 36, 26), (132, 80, 48), 0.35 + 0.12 * (k % 2)),
                   width=max(1, int(px(1.2))))
        for hy in (y0 + h * 0.26, y0 + h * 0.74):
            d.rectangle(box(cx - w / 2.0 - px(2), hy, cx + w / 2.0 + px(2), hy + px(5)), fill=(60, 60, 56))
            d.line([(cx - w / 2.0 - px(2), hy), (cx + w / 2.0 + px(2), hy)],
                   fill=(126, 124, 116), width=max(1, int(px(0.9))))
        d.ellipse(box(cx - w / 2.0, y0, cx + w / 2.0, y0 + px(10)), fill=mix(PINE_D, (36, 26, 18), 0.4))

    def hawser(cx, w):
        y1 = PLINTH
        contact(base, cx, y1, w + px(8), alpha=150, depth=px(8))
        for k in range(3):
            ry = y1 - px(4) - k * px(5)
            d.ellipse(box(cx - w / 2.0, ry - px(5), cx + w / 2.0, ry + px(5)),
                      outline=mix(ROPE, (76, 60, 38), 0.25), width=max(2, int(px(2.2))))
            d.ellipse(box(cx - w / 3.0, ry - px(2), cx + w / 3.0, ry + px(2)),
                      outline=mix(ROPE, (56, 44, 28), 0.35), width=max(1, int(px(1.2))))

    def fishbox(cx, w, h):
        y1 = PLINTH
        y0 = y1 - h
        contact(base, cx, y1, w + px(4), alpha=170, depth=px(9))
        d.rectangle(box(cx - w / 2.0, y0, cx + w / 2.0, y1), fill=mix((226, 220, 202), (168, 160, 146), 0.45))
        d.rectangle(box(cx - w / 2.0, y0, cx + w / 2.0, y0 + px(6)), fill=mix((238, 232, 214), (190, 184, 170), 0.2))
        d.line([(cx - w / 2.0, y0 + h * 0.5), (cx + w / 2.0, y0 + h * 0.5)],
               fill=(150, 144, 130), width=max(1, int(px(1.2))))

    crate(px(732), px(36), px(30))
    crate(px(778), px(28), px(22))
    crate(px(760), px(24), px(40))
    barrel(px(818), px(26), px(34))
    crate(px(1006), px(38), px(34))
    crate(px(1052), px(28), px(24))
    fishbox(px(884), px(38), px(15))
    hawser(px(940), px(50))
    barrel(px(1096), px(28), px(34))
    crate(px(1246), px(38), px(30))
    crate(px(1292), px(26), px(19))
    # and the rest of the run, out along the camera's travel
    crate(px(150), px(34), px(24))
    barrel(px(196), px(26), px(30))
    crate(px(320), px(30), px(20))
    crate(px(1420), px(34), px(24))
    barrel(px(1470), px(24), px(26))
    crate(px(1660), px(32), px(22))


def deck(base):
    """Wet planks running with the camera, holding the lamps' light."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(71)
    d.rectangle(box(0, PLINTH, W, H), fill=DECK)
    plank = px(17)
    for k, y in enumerate(range(int(PLINTH), int(H), int(plank))):
        c = mix(DECK, DECK_D, 0.22 + 0.22 * (k % 2))
        d.rectangle(box(0, y, W, y + plank - px(1)), fill=tint(c, rnd, 0.05))
        d.line([(0, y), (W, y)], fill=mix(c, DECK_L, 0.32), width=max(1, int(px(1.0))))
        d.line([(0, y + plank - px(1)), (W, y + plank - px(1))], fill=(9, 9, 10),
               width=max(2, int(px(1.5))))
        for jx in range(int(rnd.uniform(0, px(170))), int(W), int(px(190))):
            d.line([(jx, y), (jx, y + plank - px(1))], fill=(11, 11, 12),
                   width=max(1, int(px(1.0))))
    # wet sheen, and the lamps lying on the planks
    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    for _ in range(760):
        x = rnd.uniform(0, W)
        y = rnd.uniform(PLINTH, H)
        ln = rnd.uniform(px(4), px(26))
        a = int(44 * (1 - (y - PLINTH) / float(H - PLINTH)))
        sd.line([(x, y), (x + ln, y)], fill=(126, 152, 190, a), width=1)
    base.alpha_composite(sheen.filter(ImageFilter.GaussianBlur(px(1.8))))
    for lx, col in ((px(690), (255, 208, 154)), (px(950), (214, 230, 255)), (px(1240), (255, 202, 150))):
        base = hd.shade(base, [(hd.light(lx, PLINTH + px(16), px(120), col, 30), px(10), 0.85)])
    for i in range(px(28)):
        a = int(150 * (1 - i / float(px(28))) ** 1.6)
        d.line([(0, H - i), (W, H - i)], fill=(5, 5, 6, a))


def foreground():
    """The near plane: the dark under the camera, and spray off the harbour."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(83)
    for i in range(px(30)):
        a = int(140 * (1 - i / float(px(30))) ** 1.6)
        d.line([(0, H - i), (W, H - i)], fill=(4, 5, 7, a))
    for _ in range(70):
        x = rnd.uniform(0, W)
        y = rnd.uniform(px(90), H)
        r = rnd.uniform(px(1.0), px(2.4))
        d.ellipse(box(x - r, y - r, x + r, y + r), fill=(198, 220, 246, rnd.randint(12, 34)))
    return fg.filter(ImageFilter.GaussianBlur(px(2.4)))


def paint():
    LIGHTS.clear()
    base = hd.blank([(0, (9, 11, 22)), (50, (32, 40, 66)),
                     (110, (34, 38, 50)), (200, (36, 36, 40)), (240, (22, 22, 26))])
    night_sky(base)
    far_bank(base)
    water(base)
    junk(base)
    quay_wall(base)
    crane(base)
    shed(base)
    wall_dressing(base)
    containers(base)
    cargo(base)
    lamp_post(base, px(704), px(150))
    lamp_post(base, px(1122), px(142), arm_dir=1)
    lamp_post(base, px(300), px(146))
    lamp_post(base, px(1460), px(150), arm_dir=1)
    deck(base)

    base = hd.shade(base, [(hd.light(cx, cy, max(px(60), int(r * 0.62)), col,
                                     int(peak * 0.52)),
                            max(8, int(r * 0.26)), 1.0)
                           for cx, cy, r, col, peak in LIGHTS])
    base = hd.bloom(base, 196, px(4), 0.38)
    base = art.vignette(base, 0.58)
    base = art.grain(base, 2, seed=71)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


def main():
    hd.STAGES["waterfront_docks"] = ("Waterfront Docks", paint)
    hd.build("waterfront_docks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
