"""Lost Souls Cemetery: the burial ground behind the Wing Kong compound, at night.

Painted as a wall across the play plane: a moon over the cypress row, the family
vault with its pediment and black doorway, iron railings with spear finials and
one panel pushed through, leaning headstones and crosses, a weathered angel on
her plinth, dead trees at the ends, and lanterns burning cold green over packed
earth and mist. The fighters stand on the gravel in front of the graves; every
stone is based on the floor line and nothing comes out into the play plane.

The match-start view is the centre 1920 px of the 8192-wide canvas, so the vault,
the angel, the lanterns and the nearest stones are placed between units 620 and
1180; the rest carries the level as the camera travels.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960, localcoord 1920x1080, camera travel +/-3136.

Run:  python3 tools/stage_lost_souls_cemetery.py     (part of tools/build_all.py)
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

SKY = px(54)                       # 243: the hill line
HILL = px(70)                      # 315: the base of the far hills
PLINTH = FLOOR_Y - px(2)           # 891: the line every stone stands on

VAULT = (px(690), px(924))         # the family vault, doorway in the match view
FENCE_L = (0, px(690))
FENCE_R = (px(924), W)
GAP = (px(1030), px(1102))         # the panel that has been pushed through
ANGEL_X = px(1148)
TREE_L, TREE_R, TREE_MID = px(64), px(1730), px(620)

MOON_X, MOON_Y, MOON_R = px(1004), px(24), px(22)

SKY_T = (7, 9, 22)
SKY_B = (30, 36, 62)
HILL_C = (16, 20, 34)
HILL_L = (34, 40, 58)
CYPRESS = (9, 13, 18)
STONE = (92, 94, 90)
STONE_L = (156, 160, 156)
STONE_D = (48, 50, 54)
WARM_STONE = (104, 97, 84)
IRON = (16, 16, 19)
IRON_L = (74, 78, 84)
GRASS = (28, 36, 26)
GRASS_L = (54, 66, 42)
EARTH = (42, 38, 33)
EARTH_L = (72, 66, 56)
EARTH_D = (20, 18, 17)
FOG = (152, 172, 192)
MOON_C = (234, 242, 255)
LANTERN = (146, 240, 194)

LIGHTS = []


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def tint(c, rnd, amt=0.05):
    return tuple(max(0, min(255, int(v * (1 + rnd.uniform(-amt, amt))))) for v in c)


def box(x0, y0, x1, y1):
    """Normalised corners: PIL refuses a rectangle drawn bottom-up."""
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def lamp(cx, cy, r, color=MOON_C, peak=120):
    LIGHTS.append((cx, cy, r, color, peak))


def contact(base, cx, base_y, w, alpha=170, depth=None):
    """The soft shadow a stone drops where its base meets the ground."""
    depth = px(8) if depth is None else depth
    bw = w * 1.30
    pad = int(px(12))
    lw, lh = int(bw) + 2 * pad, int(depth * 4) + 2 * pad
    sh = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    d.ellipse(box(pad, pad + lh * 0.22, lw - pad, pad + lh * 0.78), fill=(5, 6, 7, alpha))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(px(5))),
                         (int(cx - bw / 2.0 - pad), int(base_y - pad - lh * 0.5)))


# --------------------------------------------------------------------- the night
def night_sky(base):
    """Indigo night, the moon and her halo, thin cloud across her."""
    d = ImageDraw.Draw(base)
    for i in range(int(HILL)):
        d.line([(0, i), (W, i)], fill=mix(SKY_T, SKY_B, (i / float(HILL)) ** 0.85))
    rnd = random.Random(13)
    for _ in range(150):
        sx, sy = rnd.uniform(0, W), rnd.uniform(0, HILL * 0.8)
        r = rnd.uniform(px(0.3), px(0.8))
        d.ellipse(box(sx - r, sy - r, sx + r, sy + r),
                  fill=mix((112, 120, 152), (242, 248, 255), rnd.uniform(0.2, 1.0)))
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd_ = ImageDraw.Draw(halo)
    for k in range(6):
        r = MOON_R * (1.7 + k * 0.44)
        hd_.ellipse(box(MOON_X - r, MOON_Y - r, MOON_X + r, MOON_Y + r),
                    fill=MOON_C + (int(30 * (1 - k / 6.0)),))
    base.alpha_composite(halo.filter(ImageFilter.GaussianBlur(px(12))))
    d.ellipse(box(MOON_X - MOON_R, MOON_Y - MOON_R, MOON_X + MOON_R, MOON_Y + MOON_R), fill=MOON_C)
    for _ in range(7):
        mx = MOON_X + rnd.uniform(-MOON_R * 0.6, MOON_R * 0.6)
        my = MOON_Y + rnd.uniform(-MOON_R * 0.6, MOON_R * 0.6)
        r = rnd.uniform(px(2), px(5))
        d.ellipse(box(mx - r, my - r * 0.8, mx + r, my + r * 0.8), fill=(208, 216, 236))
    lamp(MOON_X, MOON_Y, px(620), MOON_C, 96)


def hills(base):
    """The far hills, the cypress row, and the mist sitting in the dip."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(17)
    for depth, col in ((0.0, mix(HILL_C, HILL_L, 0.3)), (1.0, HILL_C)):
        pts = []
        y0 = SKY + px(8) - depth * px(10)
        for x in range(0, int(W) + int(px(40)), int(px(40))):
            y = y0 + math.sin(x / float(px(420)) + depth * 2.1) * px(9) + \
                math.sin(x / float(px(150)) + depth) * px(4)
            pts.append((x, y))
        pts += [(W, HILL + px(8)), (0, HILL + px(8))]
        d.polygon(pts, fill=col)
    # the cypress row: soft dark canopies, not spikes, against the sky
    for x in range(int(-px(20)), int(W), int(px(64))):
        h = rnd.uniform(px(52), px(82))
        w = rnd.uniform(px(26), px(40))
        base_y = SKY + px(20) + math.sin(x / float(px(420))) * px(9)
        cx = x + w / 2.0
        for k in range(7):
            f = k / 6.0
            cy = base_y - h * (0.16 + 0.84 * f)
            r = w * (0.50 - 0.30 * f) + px(1)
            d.ellipse(box(cx - r, cy - r * 1.35, cx + r, cy + r * 0.7), fill=CYPRESS)
        d.line([(cx - px(1.4), base_y), (cx - px(0.8), base_y - h * 0.8)],
               fill=mix(CYPRESS, (58, 74, 64), 0.5), width=max(1, int(px(0.8))))
    mist = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(mist)
    for _ in range(9):
        cx = rnd.uniform(0, W)
        cy = rnd.uniform(HILL - px(24), HILL + px(12))
        rw = rnd.uniform(px(220), px(560))
        md.ellipse(box(cx, cy, cx + rw, cy + px(14)), fill=FOG + (rnd.randint(10, 20),))
    base.alpha_composite(mist.filter(ImageFilter.GaussianBlur(px(16))))


def wall_band(base):
    """The ground band goes down dark behind the graves, so the stones read."""
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(veil)
    for i in range(0, int(px(260)), int(px(4))):
        a = int(64 * (1 - i / float(px(260))))
        d.rectangle(box(0, HILL + i, W, HILL + i + px(4)), fill=(6, 8, 10, a))
    base.alpha_composite(veil.filter(ImageFilter.GaussianBlur(px(20))))


def fence(base, x0, x1, gap=None):
    """Iron railings on a low stone kerb: three rails, spear finials, stone posts."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(int(x0) + 7)
    top = HILL + px(22)
    # the kerb the fence is set into, so it stands on stone and not on air
    d.rectangle(box(x0, PLINTH - px(17), x1, PLINTH), fill=mix(WARM_STONE, STONE_D, 0.42))
    for bx in range(int(x0), int(x1), int(px(34))):
        d.rectangle(box(bx, PLINTH - px(17), bx + px(30), PLINTH - px(2)),
                    fill=tint(mix(WARM_STONE, STONE_D, 0.34), rnd, 0.05))
        d.line([(bx, PLINTH - px(17)), (bx, PLINTH - px(2))],
               fill=mix(WARM_STONE, STONE_D, 0.62), width=max(1, int(px(1.0))))
    d.rectangle(box(x0, PLINTH - px(20), x1, PLINTH - px(15)), fill=mix(WARM_STONE, STONE_L, 0.22))
    d.line([(x0, PLINTH - px(20)), (x1, PLINTH - px(20))], fill=mix(WARM_STONE, STONE_L, 0.5),
           width=max(1, int(px(1.2))))
    # three heavy rails
    for ry in (top + px(8), PLINTH - px(64), PLINTH - px(30)):
        d.rectangle(box(x0, ry, x1, ry + px(6)), fill=IRON)
        d.line([(x0, ry), (x1, ry)], fill=IRON_L, width=max(1, int(px(1.1))))
        d.line([(x0, ry + px(6)), (x1, ry + px(6))], fill=(12, 12, 14),
               width=max(1, int(px(1.0))))
    # the spears, with their heads
    for x in range(int(x0) + int(px(6)), int(x1), int(px(24))):
        bent = gap is not None and gap[0] <= x <= gap[1]
        lean = px(10) if bent else 0.0
        d.rectangle(box(x + lean, top + px(10), x + px(4) + lean, PLINTH - px(16)), fill=IRON)
        d.line([(x + lean, top + px(10)), (x + lean, PLINTH - px(16))],
               fill=IRON_L, width=max(1, int(px(1.0))))
        d.polygon([(x + lean - px(4), top + px(12)), (x + lean + px(2), top - px(9)),
                   (x + lean + px(8), top + px(12))], fill=IRON)
        d.line([(x + lean + px(2), top - px(9)), (x + lean + px(2), top + px(10))],
               fill=mix(IRON, IRON_L, 0.7), width=max(1, int(px(0.9))))
    # stone posts at the runs' ends
    posts = list(range(int(x0), int(x1), int(px(260)))) + [int(x1) - int(px(14))]
    for pxx in posts:
        contact(base, pxx + px(8), PLINTH, px(34), alpha=170, depth=px(10))
        d.rectangle(box(pxx, top - px(10), pxx + px(17), PLINTH), fill=mix(WARM_STONE, STONE_D, 0.30))
        d.line([(pxx, top - px(10)), (pxx, PLINTH)], fill=mix(WARM_STONE, STONE_L, 0.45),
               width=max(1, int(px(1.2))))
        d.rectangle(box(pxx - px(5), top - px(20), pxx + px(22), top - px(9)),
                    fill=mix(WARM_STONE, STONE_D, 0.16))
        d.line([(pxx - px(5), top - px(20)), (pxx + px(22), top - px(20))],
               fill=mix(WARM_STONE, STONE_L, 0.55), width=max(1, int(px(1.2))))
        d.polygon([(pxx - px(5), top - px(20)), (pxx + px(8), top - px(30)),
                   (pxx + px(22), top - px(20))], fill=mix(WARM_STONE, STONE_L, 0.24))
    if gap is not None:
        # the panel that was pushed through: a bent rail and a fallen length of it
        gx = (gap[0] + gap[1]) / 2.0
        d.line([(gap[0], top + px(12)), (gx, PLINTH - px(52)), (gap[1], top + px(14))],
               fill=IRON, width=max(2, int(px(2.2))))
        d.line([(gap[0] + px(16), PLINTH - px(6)), (gx + px(34), PLINTH - px(14))],
               fill=IRON, width=max(2, int(px(2.2))))
        for k in range(5):
            fx = gap[0] + px(18) + k * px(12)
            d.line([(fx, PLINTH - px(6)), (fx + px(4), PLINTH - px(2))], fill=IRON_L,
                   width=max(1, int(px(1.0))))


def gravestone(base, cx, w, h, kind="round", lean=0.0, rnd=None):
    """One headstone or cross, based on the floor line, leaning a little."""
    rnd = rnd or random.Random(int(cx))
    d = ImageDraw.Draw(base)
    w = float(w)
    top = PLINTH - h
    contact(base, cx, PLINTH, w + px(8), alpha=170, depth=px(10))
    body = tint(STONE, rnd, 0.05)
    dark = mix(body, STONE_D, 0.45)
    light = mix(body, STONE_L, 0.5)
    if kind == "cross":
        arm = w * 0.40
        d.rectangle(box(cx - w / 2.0, top, cx + w / 2.0, PLINTH), fill=body)
        d.rectangle(box(cx - w / 2.0 - arm, top + h * 0.20, cx + w / 2.0 + arm, top + h * 0.34),
                    fill=body)
        d.line([(cx - w / 2.0, top), (cx - w / 2.0, PLINTH)], fill=light,
               width=max(1, int(px(1.2))))
        d.line([(cx + w / 2.0, top), (cx + w / 2.0, PLINTH)], fill=dark,
               width=max(2, int(px(2.0))))
        d.line([(cx - w / 2.0 - arm, top + h * 0.20), (cx + w / 2.0 + arm, top + h * 0.20)],
               fill=light, width=max(1, int(px(1.2))))
    elif kind == "obelisk":
        d.polygon([(cx - w / 2.0, PLINTH), (cx - w / 2.0, top + h * 0.14), (cx, top),
                   (cx + w / 2.0, top + h * 0.14), (cx + w / 2.0, PLINTH)], fill=body)
        d.line([(cx - w / 2.0, PLINTH), (cx - w / 2.0, top + h * 0.14), (cx, top)],
               fill=light, width=max(1, int(px(1.2))))
        d.line([(cx + w / 2.0, PLINTH), (cx + w / 2.0, top + h * 0.14), (cx, top)],
               fill=dark, width=max(2, int(px(1.8))))
        d.rectangle(box(cx - w * 0.72, PLINTH - px(8), cx + w * 0.72, PLINTH),
                    fill=mix(body, STONE_D, 0.2))
    else:
        if kind == "round":
            d.rectangle(box(cx - w / 2.0 + lean * 0.4, top + w * 0.5, cx + w / 2.0 + lean * 0.4, PLINTH),
                        fill=body)
            d.pieslice(box(cx - w / 2.0, top, cx + w / 2.0, top + w), 180, 360, fill=body)
        else:
            d.rectangle(box(cx - w / 2.0 + lean * 0.4, top + w * 0.12, cx + w / 2.0 + lean * 0.4, PLINTH),
                        fill=body)
            d.polygon([(cx - w / 2.0 + lean * 0.4, top + w * 0.14),
                       (cx + w / 2.0 + lean * 0.4, top + w * 0.14),
                       (cx + w / 2.0 + lean * 0.4, top + w * 0.02)], fill=body)
        d.line([(cx - w / 2.0 + lean * 0.6, top + w * 0.6), (cx - w / 2.0 + lean * 0.4, PLINTH)],
               fill=light, width=max(1, int(px(1.2))))
        d.line([(cx + w / 2.0 + lean * 0.6, top + w * 0.6), (cx + w / 2.0 + lean * 0.4, PLINTH)],
               fill=dark, width=max(2, int(px(1.8))))
    # the inscription, weathered to a few bars, and the lichen
    for k in range(min(4, max(2, int(h // px(12))))):
        y = top + h * (0.44 + 0.09 * k)
        span = w * (0.24 - 0.02 * k)
        if span <= px(3):
            continue
        d.line([(cx - span, y), (cx + span, y)], fill=mix(body, STONE_D, 0.55),
               width=max(1, int(px(1.1))))
    for _ in range(5):
        lx = cx + rnd.uniform(-w / 2.0, w / 2.0)
        ly = PLINTH - rnd.uniform(px(4), h * 0.9)
        r = rnd.uniform(px(1.2), px(3.2))
        d.ellipse(box(lx - r, ly - r, lx + r, ly + r),
                  fill=mix((60, 74, 46), (102, 114, 70), rnd.uniform(0.2, 0.8)))


def vault(base):
    """The family vault: pediment, fluted columns, a black doorway, a carved rail."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(37)
    x0, x1 = VAULT
    w = x1 - x0
    cx = (x0 + x1) / 2.0
    eave = HILL + px(40)
    contact(base, cx, PLINTH, w * 1.02, alpha=200, depth=px(16))
    d.rectangle(box(x0, eave, x1, PLINTH), fill=mix(WARM_STONE, STONE_D, 0.45))
    for row, y in enumerate(range(int(eave), int(PLINTH), int(px(13)))):
        x = x0 - (px(22) if row % 2 else 0)
        while x < x1:
            bw = rnd.uniform(px(38), px(70))
            d.rectangle(box(x, y, min(x + bw - px(2), x1), y + px(12)),
                        fill=tint(mix(WARM_STONE, STONE_D, 0.26 + 0.30 * rnd.random()), rnd))
            x += bw
    # pediment and cornice
    peak = eave - px(46)
    d.polygon([(x0 - px(12), eave), (cx, peak), (x1 + px(12), eave)],
              fill=mix(WARM_STONE, STONE_L, 0.16))
    d.line([(x0 - px(12), eave), (cx, peak)], fill=mix(WARM_STONE, STONE_L, 0.55),
           width=max(2, int(px(2.0))))
    d.line([(cx, peak), (x1 + px(12), eave)], fill=mix(WARM_STONE, STONE_D, 0.35),
           width=max(2, int(px(2.0))))
    d.rectangle(box(x0 - px(16), eave, x1 + px(16), eave + px(10)), fill=mix(WARM_STONE, STONE_L, 0.10))
    d.line([(x0 - px(16), eave), (x1 + px(16), eave)], fill=mix(WARM_STONE, STONE_L, 0.62),
           width=max(2, int(px(1.8))))
    d.ellipse(box(cx - px(18), peak + px(12), cx + px(18), peak + px(36)),
              outline=mix(WARM_STONE, STONE_D, 0.25), width=max(2, int(px(2.0))))
    # columns
    for colx in (x0 + px(34), x1 - px(34)):
        contact(base, colx, PLINTH, px(36), alpha=180, depth=px(12))
        d.rectangle(box(colx - px(14), eave + px(12), colx + px(14), PLINTH),
                    fill=mix(WARM_STONE, STONE_L, 0.20))
        for k in range(5):
            fx = colx - px(10) + k * px(5)
            d.line([(fx, eave + px(18)), (fx, PLINTH - px(10))],
                   fill=mix(WARM_STONE, STONE_D, 0.30), width=max(1, int(px(1.0))))
        d.line([(colx - px(13), eave + px(14)), (colx - px(13), PLINTH - px(10))],
               fill=mix(WARM_STONE, STONE_L, 0.58), width=max(1, int(px(1.2))))
        d.rectangle(box(colx - px(17), eave + px(5), colx + px(17), eave + px(16)),
                    fill=mix(WARM_STONE, STONE_L, 0.3))
        d.rectangle(box(colx - px(17), PLINTH - px(12), colx + px(17), PLINTH),
                    fill=mix(WARM_STONE, STONE_D, 0.2))
    # the doorway: black, arched, its iron gate hanging open
    dx0, dx1 = cx - px(36), cx + px(36)
    dtop = eave + px(26)
    d.rectangle(box(dx0, dtop + px(14), dx1, PLINTH - px(8)), fill=(4, 5, 7))
    d.pieslice(box(dx0, dtop, dx1, dtop + px(48)), 180, 360, fill=(4, 5, 7))
    d.rectangle(box(dx0 - px(5), dtop + px(14), dx0, PLINTH - px(8)), fill=mix(IRON, (10, 10, 12), 0.4))
    d.rectangle(box(dx1, dtop + px(14), dx1 + px(5), PLINTH - px(8)), fill=mix(IRON, (10, 10, 12), 0.4))
    d.polygon([(dx1 - px(5), dtop + px(22)), (dx1 - px(5), PLINTH - px(10)),
               (dx1 - px(21), PLINTH - px(14)), (dx1 - px(21), dtop + px(28))],
              fill=mix(IRON, (58, 46, 36), 0.5))
    for gy in range(int(dtop + px(28)), int(PLINTH - px(14)), int(px(11))):
        d.line([(dx1 - px(21), gy), (dx1 - px(5), gy)], fill=(78, 62, 46), width=max(1, int(px(1.0))))
    lamp(cx, dtop + px(34), px(230), (132, 196, 206), 62)
    # the stoop, flat against the wall
    for k in range(3):
        sw = px(104) - k * px(8)
        d.rectangle(box(cx - sw / 2.0, PLINTH - px(8) + k * px(8), cx + sw / 2.0,
                        PLINTH - px(1) + k * px(8)),
                    fill=mix(WARM_STONE, STONE_D, 0.36 + 0.06 * k))
    # ivy on the west corner
    for _ in range(70):
        vx = rnd.uniform(x0, x0 + px(52))
        vy = rnd.uniform(eave + px(14), PLINTH - px(8))
        r = rnd.uniform(px(2.2), px(5.4))
        d.ellipse(box(vx - r, vy - r * 0.7, vx + r, vy + r * 0.7),
                  fill=mix((36, 52, 32), (70, 92, 48), rnd.uniform(0.2, 0.9)))


def monuments(base):
    """The tall monuments: an obelisk, and a column broken off at the waist."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(59)
    # the obelisk, on its three steps
    cx = px(944)
    steps = ((px(52), px(9)), (px(44), px(8)), (px(36), px(7)))
    y = PLINTH
    for w, h in steps:
        y -= h
        d.rectangle(box(cx - w / 2.0, y, cx + w / 2.0, y + h),
                    fill=mix(STONE, STONE_D, 0.30))
        d.line([(cx - w / 2.0, y), (cx + w / 2.0, y)], fill=mix(STONE, STONE_L, 0.45),
               width=max(1, int(px(1.2))))
    contact(base, cx, PLINTH, px(60), alpha=200, depth=px(14))
    shaft_top = y - px(66)
    d.polygon([(cx - px(13), y), (cx + px(13), y), (cx + px(8), shaft_top), (cx - px(8), shaft_top)],
              fill=mix(STONE, STONE_L, 0.10))
    d.line([(cx - px(13), y), (cx - px(8), shaft_top)], fill=mix(STONE, STONE_L, 0.55),
           width=max(1, int(px(1.3))))
    d.line([(cx + px(13), y), (cx + px(8), shaft_top)], fill=mix(STONE, STONE_D, 0.45),
           width=max(2, int(px(1.8))))
    d.polygon([(cx - px(8), shaft_top), (cx, shaft_top - px(14)), (cx + px(8), shaft_top)],
              fill=mix(STONE, STONE_L, 0.22))
    for k in range(4):
        yy = shaft_top + px(14) + k * px(13)
        d.line([(cx - px(6), yy), (cx + px(6), yy)], fill=mix(STONE, STONE_D, 0.55),
               width=max(1, int(px(1.0))))
    for _ in range(7):
        lx = cx + rnd.uniform(-px(8), px(8))
        ly = y - rnd.uniform(0, px(22))
        r = rnd.uniform(px(0.8), px(1.8))
        d.ellipse(box(lx - r, ly - r, lx + r, ly + r),
                  fill=mix((52, 62, 42), (82, 92, 60), rnd.uniform(0.2, 0.6)))
    # the broken column
    bx = px(1206)
    contact(base, bx, PLINTH, px(48), alpha=190, depth=px(12))
    d.rectangle(box(bx - px(26), PLINTH - px(12), bx + px(26), PLINTH),
                fill=mix(STONE, STONE_D, 0.26))
    d.line([(bx - px(26), PLINTH - px(12)), (bx + px(26), PLINTH - px(12))],
           fill=mix(STONE, STONE_L, 0.4), width=max(1, int(px(1.2))))
    d.polygon([(bx - px(18), PLINTH - px(12)), (bx + px(18), PLINTH - px(12)),
               (bx + px(16), PLINTH - px(58)), (bx + px(2), PLINTH - px(52)),
               (bx - px(4), PLINTH - px(60)), (bx - px(16), PLINTH - px(54))],
              fill=mix(STONE, STONE_L, 0.08))
    for k in range(5):
        fx = bx - px(13) + k * px(6)
        d.line([(fx, PLINTH - px(14)), (fx + px(1), PLINTH - px(54))],
               fill=mix(STONE, STONE_D, 0.42), width=max(1, int(px(1.1))))
    d.polygon([(bx - px(16), PLINTH - px(54)), (bx - px(4), PLINTH - px(60)),
               (bx + px(2), PLINTH - px(52)), (bx + px(16), PLINTH - px(58))],
              fill=mix(STONE, STONE_D, 0.20))


def angel(base):
    """The weathered angel on her plinth: folded wings, a robe, a bowed head."""
    d = ImageDraw.Draw(base)
    cx = ANGEL_X
    plinth_top = PLINTH - px(44)
    contact(base, cx, PLINTH, px(60), alpha=190, depth=px(14))
    d.rectangle(box(cx - px(34), plinth_top, cx + px(34), PLINTH), fill=mix(STONE, STONE_D, 0.30))
    d.rectangle(box(cx - px(38), plinth_top - px(7), cx + px(38), plinth_top + px(2)),
                fill=mix(STONE, STONE_L, 0.16))
    d.line([(cx - px(38), plinth_top - px(7)), (cx + px(38), plinth_top - px(7))],
           fill=mix(STONE, STONE_L, 0.6), width=max(1, int(px(1.2))))
    body = mix(STONE, STONE_L, 0.12)
    for side in (-1, 1):
        d.polygon([(cx + side * px(7), plinth_top - px(34)),
                   (cx + side * px(34), plinth_top - px(74)),
                   (cx + side * px(29), plinth_top - px(42)),
                   (cx + side * px(18), plinth_top - px(20))],
                  fill=mix(body, STONE_D, 0.20))
        for k in range(3):
            d.line([(cx + side * px(9), plinth_top - px(30) - k * px(11)),
                    (cx + side * px(29), plinth_top - px(58) - k * px(7))],
                   fill=mix(body, STONE_D, 0.42), width=max(1, int(px(1.0))))
    d.polygon([(cx - px(15), plinth_top), (cx - px(10), plinth_top - px(48)),
               (cx, plinth_top - px(58)), (cx + px(10), plinth_top - px(48)),
               (cx + px(16), plinth_top)], fill=body)
    for k in range(4):
        fx = cx - px(11) + k * px(7)
        d.line([(fx, plinth_top - px(2)), (fx + (fx - cx) * 0.22, plinth_top - px(50))],
               fill=mix(body, STONE_D, 0.35), width=max(1, int(px(1.1))))
    d.line([(cx - px(14), plinth_top - px(2)), (cx - px(10), plinth_top - px(48))],
           fill=mix(body, STONE_L, 0.55), width=max(1, int(px(1.2))))
    d.line([(cx - px(10), plinth_top - px(48)), (cx - px(22), plinth_top - px(36))],
           fill=mix(body, STONE_L, 0.3), width=max(3, int(px(2.2))))
    d.line([(cx + px(10), plinth_top - px(48)), (cx + px(21), plinth_top - px(58))],
           fill=mix(body, STONE_L, 0.3), width=max(3, int(px(2.2))))
    d.ellipse(box(cx - px(8), plinth_top - px(70), cx + px(8), plinth_top - px(54)), fill=body)
    d.pieslice(box(cx - px(12), plinth_top - px(76), cx + px(12), plinth_top - px(52)),
               0, 180, outline=mix(body, STONE_L, 0.5), width=max(2, int(px(1.6))))
    for k in range(8):
        sx = cx + random.Random(int(cx) + k).uniform(-px(26), px(26))
        d.line([(sx, plinth_top - px(54)), (sx + px(1), plinth_top - px(6))],
               fill=mix(body, (46, 56, 46), 0.35), width=max(1, int(px(0.9))))
    lamp(cx + px(4), plinth_top - px(44), px(160), (172, 200, 220), 30)


def dead_tree(base, cx, height, seed):
    """A bare tree at the edge of the ground: trunk, crooked limbs, roots."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(seed)
    contact(base, cx, PLINTH, px(28), alpha=180, depth=px(12))
    trunk = mix((48, 42, 36), (16, 14, 14), 0.35)
    lit = mix(trunk, (128, 120, 104), 0.35)

    def limb(x, y, dx, dy, w, depth_left):
        if depth_left <= 0 or w < px(0.9):
            return
        nx, ny = x + dx, y + dy
        d.line([(x, y), (nx, ny)], fill=trunk, width=max(1, int(w)))
        d.line([(x - w * 0.26, y), (nx - w * 0.26, ny)],
               fill=lit, width=max(1, int(max(1.0, w * 0.3))))
        limb(nx, ny, dx * rnd.uniform(0.55, 0.95) + rnd.uniform(-px(6), px(6)),
             dy * rnd.uniform(0.55, 0.95) - rnd.uniform(0, px(5)), w * 0.62, depth_left - 1)
        if rnd.random() < 0.8:
            limb(nx, ny, dx * rnd.uniform(-0.7, 0.2) + rnd.uniform(-px(9), px(2)),
                 dy * rnd.uniform(0.35, 0.8) - rnd.uniform(px(2), px(9)), w * 0.55, depth_left - 1)
        if rnd.random() < 0.45:
            limb(nx, ny, dx * rnd.uniform(-0.4, 0.9), dy * rnd.uniform(0.4, 1.0),
                 w * 0.5, depth_left - 1)

    top = PLINTH - height
    d.polygon([(cx - px(12), PLINTH), (cx - px(7), top), (cx + px(7), top), (cx + px(13), PLINTH)],
              fill=trunk)
    d.line([(cx - px(11), PLINTH), (cx - px(6), top)], fill=lit, width=max(1, int(px(1.2))))
    for _ in range(3):
        limb(cx + rnd.uniform(-px(9), px(9)), top + px(8),
             rnd.uniform(-px(22), px(22)), -rnd.uniform(px(18), px(32)), px(7), 5)
    for side in (-1, 1):
        d.line([(cx + side * px(11), PLINTH), (cx + side * px(36), PLINTH + px(3))],
               fill=mix(trunk, (8, 8, 9), 0.3), width=max(2, int(px(2.0))))


def lantern_posts(base):
    """Iron lamp posts burning cold green, at the graves and along the run."""
    d = ImageDraw.Draw(base)
    for cx, height, arm in ((px(1002), px(104), -1), (px(1256), px(96), -1),
                            (px(500), px(96), 1), (px(1560), px(100), -1)):
        top = PLINTH - height
        contact(base, cx, PLINTH, px(24), alpha=180, depth=px(10))
        d.rectangle(box(cx - px(4), top, cx + px(4), PLINTH), fill=IRON)
        d.line([(cx - px(4), top), (cx - px(4), PLINTH)], fill=mix(IRON, IRON_L, 0.8),
               width=max(1, int(px(1.0))))
        d.rectangle(box(cx - px(10), PLINTH - px(9), cx + px(10), PLINTH), fill=mix(IRON, (46, 46, 50), 0.4))
        d.line([(cx - px(10), PLINTH - px(9)), (cx + px(10), PLINTH - px(9))],
               fill=IRON_L, width=max(1, int(px(1.0))))
        # the arm and its scroll bracket
        ax = cx + arm * px(26)
        d.line([(cx, top + px(4)), (ax, top - px(2))], fill=IRON, width=max(2, int(px(2.4))))
        d.arc(box(min(cx, ax), top + px(2), max(cx, ax) + px(10), top + px(22)), 200, 340,
               fill=IRON, width=max(1, int(px(1.4))))
        # the lantern: a glazed box with a pagoda cap and a finial
        lx0, lx1 = ax - px(13), ax + px(13)
        ly0, ly1 = top - px(6), top + px(20)
        d.rectangle(box(lx0, ly0, lx1, ly1), fill=(26, 30, 28))
        for k in range(3):
            gx0 = lx0 + px(3) + k * px(7)
            d.rectangle(box(gx0, ly0 + px(3), gx0 + px(5), ly1 - px(3)), fill=LANTERN)
            d.line([(gx0, ly0 + px(3)), (gx0, ly1 - px(3))], fill=(226, 255, 236),
                   width=max(1, int(px(1.0))))
        d.rectangle(box(lx0 - px(3), ly0 - px(4), lx1 + px(3), ly0 + px(1)),
                    fill=mix(IRON, (52, 60, 56), 0.3))
        d.polygon([(lx0 - px(4), ly0 - px(4)), (ax, ly0 - px(16)), (lx1 + px(4), ly0 - px(4))],
                  fill=IRON)
        d.line([(ax, ly0 - px(16)), (ax, ly0 - px(21))], fill=IRON,
               width=max(1, int(px(1.2))))
        d.rectangle(box(lx0, ly1, lx1, ly1 + px(4)), fill=mix(IRON, (52, 60, 56), 0.3))
        lamp(ax, top + px(8), px(250), LANTERN, 88)


def ground(base):
    """Packed earth, the path from the vault, wet patches, leaves and mist."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(79)
    d.rectangle(box(0, PLINTH, W, H), fill=EARTH)
    for k, y in enumerate(range(int(PLINTH), int(H), int(px(10)))):
        d.line([(0, y), (W, y)], fill=mix(EARTH, EARTH_D, 0.18 + 0.20 * (k % 2)),
               width=max(1, int(px(9))))
    # the brick path from the vault door, widening as it comes toward us
    pcx = 807 * px(1)
    for k, y in enumerate(range(int(PLINTH + px(4)), int(H), int(px(9)))):
        f = (y - PLINTH) / float(H - PLINTH)
        half = px(26) + f * px(120)
        row = mix((96, 74, 60), (56, 44, 38), 0.25 + 0.5 * f)
        d.rectangle(box(pcx - half, y, pcx + half, y + px(7)), fill=row)
        n = int((2 * half) // px(16)) + 1
        off = (k % 2) * px(8)
        for b in range(n):
            bx = pcx - half + b * px(16) + off
            if bx + px(14) > pcx + half:
                break
            d.rectangle(box(bx, y, bx + px(14), y + px(7)),
                        fill=mix(row, (36, 30, 26), 0.12 + 0.12 * ((b + k) % 3 == 0)))
    for _ in range(1700):
        x = rnd.uniform(0, W)
        y = rnd.uniform(PLINTH, H)
        if abs(x - pcx) < px(30) + (y - PLINTH) / float(H - PLINTH) * px(120):
            continue
        r = rnd.uniform(px(0.7), px(2.6))
        c = mix(EARTH, EARTH_L, rnd.uniform(0.0, 0.7)) if rnd.random() < 0.65 else mix(EARTH, EARTH_D, 0.55)
        d.ellipse(box(x - r, y - r * 0.6, x + r, y + r * 0.6), fill=c)
    for _ in range(520):
        x = rnd.uniform(0, W)
        y = PLINTH + rnd.uniform(0, px(22))
        h = rnd.uniform(px(3), px(11))
        d.line([(x, y), (x + rnd.uniform(-px(3), px(3)), y - h)],
               fill=mix(GRASS, GRASS_L, rnd.uniform(0.2, 0.8)), width=max(1, int(px(0.9))))
    for _ in range(6):
        wx = rnd.uniform(0, W)
        wy = rnd.uniform(PLINTH + px(8), H - px(12))
        ww = rnd.uniform(px(80), px(240))
        wh = rnd.uniform(px(5), px(13))
        patch = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(patch).ellipse(box(wx, wy, wx + ww, wy + wh), fill=(124, 150, 180, 30))
        base.alpha_composite(patch.filter(ImageFilter.GaussianBlur(px(3))))
    for _ in range(70):
        x = rnd.uniform(0, W)
        y = rnd.uniform(PLINTH, H)
        r = rnd.uniform(px(1.4), px(3.2))
        d.ellipse(box(x - r, y - r * 0.5, x + r, y + r * 0.5),
                  fill=mix((60, 46, 28), (110, 78, 40), rnd.uniform(0.2, 0.8)))
    for lx, col, peak in ((px(1002), LANTERN, 52), (px(1256), LANTERN, 46), (MOON_X, MOON_C, 46)):
        base = hd.shade(base, [(hd.light(lx, PLINTH + px(22), px(200), col, peak), px(12), 0.85)])
    mist = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(mist)
    for _ in range(10):
        cx = rnd.uniform(0, W)
        cy = rnd.uniform(PLINTH - px(4), PLINTH + px(34))
        rw = rnd.uniform(px(200), px(520))
        md.ellipse(box(cx, cy, cx + rw, cy + px(18)), fill=FOG + (rnd.randint(10, 20),))
    base.alpha_composite(mist.filter(ImageFilter.GaussianBlur(px(14))))
    for i in range(px(28)):
        a = int(150 * (1 - i / float(px(28))) ** 1.6)
        d.line([(0, H - i), (W, H - i)], fill=(6, 6, 7, a))


def foreground():
    """The near plane: the dark under the camera, and mist rolling through it."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(97)
    for i in range(px(32)):
        a = int(150 * (1 - i / float(px(32))) ** 1.6)
        d.line([(0, H - i), (W, H - i)], fill=(5, 6, 7, a))
    for _ in range(14):
        cx = rnd.uniform(0, W)
        cy = rnd.uniform(H - px(46), H)
        rw = rnd.uniform(px(300), px(760))
        d.ellipse(box(cx, cy, cx + rw, cy + px(20)), fill=FOG + (rnd.randint(12, 26),))
    return fg.filter(ImageFilter.GaussianBlur(px(16)))


def paint():
    LIGHTS.clear()
    base = hd.blank([(0, (9, 11, 24)), (54, (30, 36, 58)),
                     (112, (28, 30, 38)), (200, (34, 32, 30)), (240, (20, 19, 20))])
    night_sky(base)
    hills(base)
    wall_band(base)
    fence(base, FENCE_L[0], FENCE_L[1])
    fence(base, FENCE_R[0], FENCE_R[1], gap=GAP)
    vault(base)

    rnd = random.Random(101)
    graves = (
        (px(640), 30, 44, "cross", px(2)),
        (px(730), 22, 30, "round", px(-2)),
        (px(770), 15, 22, "obelisk", px(1)),
        (px(966), 26, 38, "round", px(-3)),
        (px(1010), 16, 26, "cross", px(2)),
        (px(1090), 22, 32, "flat", px(-1)),
        (px(1180), 26, 38, "round", px(3)),
        (px(1300), 20, 28, "cross", px(-2)),
        (px(1386), 24, 34, "round", px(1)),
        (px(1470), 18, 26, "obelisk", px(-1)),
        (px(1560), 24, 36, "round", px(2)),
        (px(340), 26, 36, "round", px(-2)),
        (px(420), 18, 26, "cross", px(1)),
        (px(210), 22, 30, "flat", px(-1)),
        (px(110), 20, 28, "round", px(2)),
    )
    for (gx, gw, gh, kind, lean) in graves:
        gravestone(base, gx, px(gw), px(gh), kind=kind, lean=lean, rnd=rnd)
    monuments(base)
    angel(base)
    dead_tree(base, TREE_L, px(126), 103)
    dead_tree(base, TREE_MID, px(96), 109)
    dead_tree(base, TREE_R, px(110), 107)
    lantern_posts(base)
    ground(base)

    base = hd.shade(base, [(hd.light(cx, cy, max(px(50), int(r * 0.62)), col,
                                     int(peak * 0.62)),
                            max(8, int(r * 0.26)), 1.0)
                           for cx, cy, r, col, peak in LIGHTS])
    base = hd.bloom(base, 188, px(4), 0.36)
    base = art.vignette(base, 0.62)
    base = art.grain(base, 3, seed=103)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


def main():
    hd.STAGES["lost_souls_cemetery"] = ("Lost Souls Cemetery", paint)
    hd.build("lost_souls_cemetery")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
