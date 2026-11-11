"""Shadow Alleys: the narrow back lane off the exchange.

Painted from the plan reference: a brick wall closing the lane, tiled eaves over
it, red awnings and vertical shop boards, paper lanterns on their brackets, lit
shopfronts and a recessed doorway, drainpipes, stacked crates and a handcart
left against the bricks, with the paving wet and every sign dropping its colour
into it.

A stage is seen across the play plane, so the lane is painted as a wall
wall-to-wall: the shops and the doorway stand against the back of the lane, the
cart and the crates stop at the floor line, and the fighters stand on the wet
bricks in front of them. Nothing comes out into the play plane to stand on
anybody's feet.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960, localcoord 1920x1080, camera travel +/-3136.

Run:  python3 tools/stage_shadow_alleys.py     (part of tools/build_all.py)
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

EAVES = px(30)                     # 135: the tiled eaves at the top
CEIL = px(50)                      # 225: the wall starts here
PLINTH = FLOOR_Y - px(12)          # 846
SHOP_A = (px(92), px(338))
SHOP_B = (px(1078), px(1330))
DOORWAY = (px(600), px(742))
WINDOW_C = (px(1478), px(1618))

BRICK = (92, 56, 44)               # the wall
BRICK_L = (128, 82, 62)
BRICK_D = (54, 32, 26)
PLASTER = (116, 100, 82)
TILE = (118, 88, 60)               # the eaves
TILE_D = (58, 42, 28)
TIMBER = (68, 44, 28)
RED = (150, 28, 25)
RED_L = (200, 56, 42)
LANTERN = (198, 44, 32)
AMBER = (255, 176, 96)
GREEN = (86, 206, 130)
WARM = (255, 202, 140)
BRICKS = (74, 48, 42)              # the paving
BRICKS_L = (104, 70, 58)
BRICKS_D = (44, 28, 24)
STONE = (110, 104, 92)

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


# ------------------------------------------------------------------ the lane
def eaves(base):
    """The tiled eaves over the lane, and the dark they hang under."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, 0, W, EAVES), fill=(22, 18, 16))
    # the tiles: half-round courses seen from below, edge on
    for i in range(int(EAVES) - int(px(6)), int(EAVES)):
        tt = (i - (EAVES - px(6))) / float(px(6))
        d.line([(0, i), (W, i)], fill=mix(TILE, TILE_D, tt), width=1)
    x = -px(10)
    n = 0
    while x < W:
        c = mix(TILE, (150, 116, 78), 0.3 + 0.35 * ((n % 3) / 2.0))
        d.pieslice(box(x, EAVES - px(26), x + px(22), EAVES + px(2)), 180, 360, fill=c)
        d.line([(x, EAVES - px(13)), (x + px(22), EAVES - px(13))],
               fill=mix(c, (70, 50, 32), 0.35), width=max(1, int(px(0.7))))
        d.line([(x + px(2), EAVES - px(24)), (x + px(2), EAVES - px(2))],
               fill=mix(c, (176, 140, 96), 0.35), width=max(1, int(px(0.8))))
        x += px(20)
        n += 1
    # the fascia under the tiles, and the shadow the eaves throw down the wall
    d.rectangle(box(0, EAVES, W, EAVES + px(8)), fill=mix(TIMBER, (34, 22, 14), 0.4))
    d.line([(0, EAVES + px(8)), (W, EAVES + px(8))], fill=(16, 12, 10),
           width=max(2, int(px(2.0))))
    for i in range(px(20)):
        a = int(120 * (1 - i / float(px(20))) ** 1.4)
        d.line([(0, EAVES + px(8) + i), (W, EAVES + px(8) + i)], fill=(10, 9, 8, a))


def brick_wall(base):
    """Running-bond brick, patched with plaster and running with damp."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(3)
    d.rectangle(box(0, CEIL, W, PLINTH), fill=BRICK)
    bh, bw = px(13), px(30)
    row = 0
    y = CEIL
    while y < PLINTH:
        yy = min(y + bh, PLINTH)
        off = 0 if row % 2 == 0 else bw // 2
        x = -off
        while x < W:
            xx = x + bw
            if rnd.random() < 0.06:                        # a plastered patch
                c = tint(mix(PLASTER, BRICK, 0.35), rnd, 0.06)
            else:
                c = tint(mix(BRICK, rnd.choice((BRICK_L, BRICK_D, (110, 66, 50), (76, 44, 34))),
                             rnd.uniform(0.10, 0.40)), rnd, 0.05)
            d.rectangle(box(x, y, xx, yy), fill=c)
            d.line([(x, y), (xx, y)], fill=mix(c, (206, 178, 150), 0.22),
                   width=max(1, int(px(0.4))))
            d.line([(x, yy), (xx, yy)], fill=mix(c, (26, 16, 12), 0.55),
                   width=max(1, int(px(0.5))))
            d.line([(xx, y), (xx, yy)], fill=mix(c, (26, 16, 12), 0.5),
                   width=max(1, int(px(0.4))))
            x = xx
        y = yy
        row += 1
    # grime rising from the paving, and streaks running down
    for i in range(px(24)):
        a = int(96 * (1 - i / float(px(24))) ** 1.4)
        d.line([(0, PLINTH - i), (W, PLINTH - i)], fill=mix(BRICK, (20, 14, 12), a / 255.0))
    for k in range(24):
        sx = rnd.uniform(0, W)
        d.line([(sx, CEIL), (sx + rnd.uniform(-px(6), px(6)), rnd.uniform(px(150), PLINTH))],
               fill=mix(BRICK, (30, 20, 16), 0.25), width=max(1, int(px(1.4))))


def pipes(base, x):
    """A drainpipe down the bricks, with its brackets."""
    d = ImageDraw.Draw(base)
    w = px(8)
    d.rectangle(box(x - w, EAVES + px(6), x + w, PLINTH), fill=(58, 52, 44))
    d.line([(x - w, EAVES + px(6)), (x - w, PLINTH)], fill=(126, 120, 106),
           width=max(1, int(px(1.0))))
    d.line([(x + w, EAVES + px(6)), (x + w, PLINTH)], fill=(22, 18, 14),
           width=max(2, int(px(1.2))))
    for y in range(int(EAVES) + int(px(60)), int(PLINTH), int(px(150))):
        d.rectangle(box(x - w - px(4), y, x + w + px(4), y + px(8)), fill=(44, 40, 34))


def lantern(base, cx, cy, r=px(26)):
    """A red paper lantern on a bracket, hung off the wall."""
    d = ImageDraw.Draw(base)
    # the bracket
    d.line([(cx, cy - r * 1.4), (cx, cy - r * 3.0)], fill=(40, 32, 26),
           width=max(2, int(px(2.0))))
    d.line([(cx, cy - r * 3.0), (cx + px(18), cy - r * 3.0)], fill=(40, 32, 26),
           width=max(2, int(px(2.0))))
    d.rectangle(box(cx + px(14), cy - r * 3.1, cx + px(24), cy - r * 2.9),
                fill=(54, 44, 34))
    hd.hang_lantern(d, cx, cy, r, body=LANTERN, cap=mix((226, 186, 104), (120, 84, 30), 0.35))
    d.line([(cx, cy + r * 0.98), (cx, cy + r * 1.6)], fill=(150, 30, 24),
           width=max(2, int(px(2.0))))
    d.ellipse(box(cx - px(3.4), cy + r * 1.5, cx + px(3.4), cy + r * 1.95), fill=(150, 30, 24))
    lamp(cx, cy, px(190), (255, 152, 92), 88)


def window(base, x0, x1, y0, y1, bars=True):
    """A window in the bricks: warm light behind it, iron bars in front."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(x0 - px(6), y0 - px(6), x1 + px(6), y1 + px(6)), fill=(30, 22, 16))
    for i in range(int(y1 - y0)):
        tt = i / max(1.0, y1 - y0)
        d.line([(x0, y0 + i), (x1, y0 + i)],
               fill=mix((255, 206, 138), (176, 118, 62), tt))
    # a curtain or a shelf behind the glass
    d.rectangle(box(x0, y0, x0 + (x1 - x0) * 0.42, y1), fill=mix((120, 40, 30), (60, 24, 18), 0.4))
    d.rectangle(box(x0 + (x1 - x0) * 0.55, y0 + (y1 - y0) * 0.4, x1, y0 + (y1 - y0) * 0.5),
                fill=(70, 44, 28))
    if bars:
        for k in range(3):
            bx = x0 + (x1 - x0) * (k + 0.5) / 3.0
            d.rectangle(box(bx - px(2.5), y0, bx + px(2.5), y1), fill=(38, 32, 26))
            d.line([(bx - px(2.5), y0), (bx - px(2.5), y1)], fill=(96, 90, 78),
                   width=max(1, int(px(0.6))))
    d.rectangle(box(x0 - px(6), y1 + px(2), x1 + px(6), y1 + px(8)),
                fill=mix(STONE, (150, 142, 124), 0.3))
    d.line([(x0 - px(6), y1 + px(2)), (x1 + px(6), y1 + px(2))], fill=(206, 196, 172),
           width=max(1, int(px(1.0))))
    lamp((x0 + x1) / 2.0, (y0 + y1) / 2.0, (x1 - x0) * 1.4, (255, 170, 100), 66)


def shopfront(base, x0, x1):
    """A lit shop: a counter and shelves behind its glass, a door beside it."""
    d = ImageDraw.Draw(base)
    top = px(104)
    ww = (x1 - x0) * 0.72
    gx0, gx1 = x0, x0 + ww
    # the lit room behind the glass
    d.rectangle(box(gx0 - px(8), top - px(8), gx1 + px(8), PLINTH + px(4)), fill=(28, 20, 14))
    for i in range(int(PLINTH - top)):
        tt = i / max(1.0, PLINTH - top)
        d.line([(gx0, top + i), (gx1, top + i)],
               fill=mix((255, 214, 150), (168, 108, 58), tt ** 0.9))
    # shelves of jars, a counter, and a hanging bulb
    for k in range(2):
        sy = top + px(20) + k * px(26)
        d.rectangle(box(gx0 + px(8), sy, gx1 - px(8), sy + px(5)), fill=mix(TIMBER, (110, 74, 44), 0.4))
        rnd = random.Random(int(gx0) + k)
        jx = gx0 + px(14)
        while jx < gx1 - px(20):
            jw = rnd.uniform(px(8), px(14))
            d.rectangle(box(jx, sy - rnd.uniform(px(10), px(18)), jx + jw, sy),
                        fill=mix(rnd.choice(((190, 150, 90), (140, 60, 44), (120, 150, 120))),
                                 (255, 220, 170), 0.2))
            jx += jw + px(6)
    d.rectangle(box(gx0 + px(6), PLINTH - px(46), gx1 - px(6), PLINTH - px(38)),
                fill=mix(TIMBER, (140, 96, 56), 0.35))
    d.line([(gx0 + px(6), PLINTH - px(46)), (gx1 - px(6), PLINTH - px(46))],
           fill=(240, 206, 158), width=max(1, int(px(1.2))))
    d.line([(gx0 + ww * 0.5, top), (gx0 + ww * 0.5, top + px(10))], fill=(40, 30, 22),
           width=max(1, int(px(1.0))))
    d.ellipse(box(gx0 + ww * 0.5 - px(5), top + px(8), gx0 + ww * 0.5 + px(5), top + px(18)),
              fill=(255, 240, 196))
    # the window frame and its mullion
    d.rectangle(box(gx0, top, gx1, PLINTH), outline=mix(TIMBER, (150, 108, 66), 0.35),
                width=max(2, int(px(2.0))))
    d.rectangle(box(gx0 + ww * 0.5 - px(4), top, gx0 + ww * 0.5 + px(4), PLINTH),
                fill=mix(TIMBER, (120, 84, 50), 0.3))
    # the door in the rest of the front
    dx0 = gx1 + px(8)
    d.rectangle(box(dx0, top - px(4), x1, PLINTH), fill=mix(TIMBER, (40, 26, 16), 0.35))
    d.rectangle(box(dx0 + px(8), top + px(10), x1 - px(8), PLINTH - px(10)),
                fill=mix((176, 128, 74), (96, 62, 34), 0.35))
    d.line([(dx0 + px(8), PLINTH - px(10)), (x1 - px(8), PLINTH - px(10))],
           fill=(46, 30, 18), width=max(2, int(px(1.4))))
    d.ellipse(box(x1 - px(24), top + px(80), x1 - px(16), top + px(88)), fill=(196, 160, 96))
    lamp((gx0 + gx1) / 2.0, top + (PLINTH - top) * 0.4, (gx1 - gx0) * 1.2, (255, 178, 104), 78)


def awning(base, x0, x1):
    """A red awning over a shopfront, scalloped and strutted."""
    d = ImageDraw.Draw(base)
    top, bottom = px(58), px(104)
    d.polygon([(x0, bottom), (x1, bottom), (x1 + px(18), top), (x0 - px(18), top)],
              fill=RED)
    for k in range(6):
        fx = x0 + (x1 - x0) * k / 6.0
        d.line([(fx, bottom), (fx + px(3), top)], fill=mix(RED, (110, 18, 16), 0.4),
               width=max(1, int(px(1.4))))
    # the scalloped hem
    for k in range(6):
        sx0 = x0 + (x1 - x0) * k / 6.0
        sx1 = x0 + (x1 - x0) * (k + 1) / 6.0
        d.pieslice(box(sx0, bottom - px(6), sx1, bottom + px(8)), 0, 180,
                   fill=mix(RED, RED_L, 0.25))
    d.line([(x0 - px(18), top), (x1 + px(18), top)], fill=mix(RED_L, (240, 140, 96), 0.3),
           width=max(2, int(px(1.8))))
    # struts back to the wall
    for fx in (x0 + px(10), x1 - px(10)):
        d.line([(fx, bottom), (fx - px(4), bottom + px(26))], fill=(54, 40, 28),
               width=max(2, int(px(2.0))))
    lamp((x0 + x1) / 2.0, bottom + px(10), (x1 - x0) * 0.6, (255, 140, 92), 40)


def vertical_sign(base, cx, y0, y1, seed):
    """A red vertical shop board with gilt characters down it."""
    d = ImageDraw.Draw(base)
    w = px(34)
    d.rectangle(box(cx - w - px(4), y0 - px(4), cx + w + px(4), y1 + px(4)), fill=(28, 18, 12))
    d.rectangle(box(cx - w, y0, cx + w, y1), fill=RED)
    d.rectangle(box(cx - w, y0, cx + w, y1), outline=mix((226, 186, 108), (120, 86, 34), 0.35),
                width=max(1, int(px(1.2))))
    n = max(2, int((y1 - y0) / px(40)))
    for k in range(n):
        gy = y0 + (y1 - y0) * (k + 0.5) / n - px(9)
        hd.glyph(d, cx - px(9), gy, px(18), (250, 214, 140), seed=seed * 7 + k, width=px(1.8))
    lamp(cx, (y0 + y1) / 2.0, px(150), (255, 96, 64), 58)


def neon(base, x0, x1, y):
    """A green neon tube over the lane, and the green it drops on the wall."""
    d = ImageDraw.Draw(base)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for k, a in ((px(22), 40), (px(12), 70), (px(5), 96)):
        gd.line([(x0, y), (x1, y)], fill=GREEN + (a,), width=max(2, int(px(4.0) + k)))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(px(6))))
    d.line([(x0, y), (x1, y)], fill=GREEN, width=max(2, int(px(3.0))))
    d.line([(x0, y - px(1)), (x1, y - px(1))], fill=(206, 255, 220),
           width=max(1, int(px(1.0))))
    for k in (0.2, 0.8):
        bx = x0 + (x1 - x0) * k
        d.line([(bx, y - px(10)), (bx, y)], fill=(70, 90, 80), width=max(1, int(px(1.4))))
    lamp((x0 + x1) / 2.0, y, (x1 - x0) * 1.2, (90, 220, 140), 66)
    lamp((x0 + x1) / 2.0, FLOOR_Y + px(26), (x1 - x0) * 0.8, (90, 220, 140), 44)


def doorway(base, x0, x1):
    """A recessed doorway with a step, a warm interior and a lantern over it."""
    d = ImageDraw.Draw(base)
    top = px(86)
    d.rectangle(box(x0 - px(12), top - px(14), x1 + px(12), PLINTH + px(2)), fill=(26, 18, 12))
    d.rectangle(box(x0, top, x1, PLINTH), fill=(38, 26, 18))
    for i in range(int(PLINTH - top)):
        tt = i / max(1.0, PLINTH - top)
        d.line([(x0 + px(4), top + i), (x1 - px(4), top + i)],
               fill=mix((60, 40, 26), (196, 132, 72), tt ** 1.2))
    # the door itself, standing half open: the room beyond it stays darker than
    # the leaf, so the opening is an opening and not a brown panel
    d.polygon([(x0 + (x1 - x0) * 0.58, top + px(4)), (x1 - px(2), top + px(8)),
               (x1 - px(2), PLINTH - px(6)), (x0 + (x1 - x0) * 0.58, PLINTH - px(4))],
              fill=mix((120, 78, 44), (58, 36, 22), 0.35))
    d.polygon([(x0 + px(6), top + px(10)), (x0 + (x1 - x0) * 0.56, top + px(4)),
               (x0 + (x1 - x0) * 0.56, PLINTH - px(6)), (x0 + px(6), PLINTH)],
              fill=mix(TIMBER, (40, 26, 16), 0.35))
    for k in range(3):
        fx = x0 + px(14) + k * px(16)
        d.line([(fx, top + px(16)), (fx, PLINTH - px(12))], fill=(30, 20, 12),
               width=max(1, int(px(1.4))))
    # the lit edge of the open leaf
    d.line([(x0 + (x1 - x0) * 0.56, top + px(4)), (x0 + (x1 - x0) * 0.56, PLINTH - px(6))],
           fill=(236, 190, 132), width=max(2, int(px(1.8))))
    # the frame, a stone step, and the lantern over the lintel
    d.rectangle(box(x0 - px(12), top - px(14), x1 + px(12), top - px(4)),
                fill=mix(TIMBER, (140, 98, 58), 0.35))
    d.line([(x0 - px(12), top - px(14)), (x1 + px(12), top - px(14))],
           fill=(216, 186, 140), width=max(1, int(px(1.2))))
    d.rectangle(box(x0 - px(20), PLINTH - px(6), x1 + px(20), PLINTH + px(6)),
                fill=mix(STONE, (150, 140, 120), 0.3))
    d.line([(x0 - px(20), PLINTH - px(6)), (x1 + px(20), PLINTH - px(6))],
           fill=(212, 202, 178), width=max(1, int(px(1.0))))
    lantern(base, (x0 + x1) / 2.0, top - px(34), px(24))
    lamp((x0 + x1) / 2.0, top + px(70), px(240), (255, 168, 100), 84)


def crates(base, x0, x1):
    """Crates and boxes stacked against the bricks."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(int(x0))
    cols = [(150, 112, 70), (120, 86, 52), (168, 148, 112)]
    bx = x0
    stacks = [(0, px(46), 0), (1, px(38), 1), (2, px(30), 0)]
    for i, (idx, h, _) in enumerate(stacks):
        w = (x1 - x0) / len(stacks) - px(6)
        c = cols[idx % len(cols)]
        base_y = PLINTH
        for k in range(2 if i != 1 else 3):
            ch = h
            yy = base_y - (k + 1) * ch
            d.rectangle(box(bx, yy, bx + w, yy + ch), fill=mix(c, (40, 28, 18), 0.2 * k))
            d.rectangle(box(bx, yy, bx + w, yy + ch), outline=mix(c, (36, 24, 14), 0.55),
                        width=max(1, int(px(1.0))))
            d.line([(bx + px(3), yy + px(4)), (bx + w - px(3), yy + px(4))],
                   fill=mix(c, (216, 190, 150), 0.35), width=max(1, int(px(1.0))))
            d.line([(bx + w * 0.5, yy), (bx + w * 0.5, yy + ch)],
                   fill=mix(c, (60, 40, 24), 0.4), width=max(1, int(px(0.8))))
        bx += w + px(6)


def cart(base, cx):
    """A two-wheeled handcart left leaning on the wall."""
    d = ImageDraw.Draw(base)
    # the wheels, one behind the other, with their spokes
    for wx, wy, r in ((cx - px(40), PLINTH - px(30), px(30)), (cx + px(26), PLINTH - px(34), px(34))):
        d.ellipse(box(wx - r, wy - r, wx + r, wy + r), outline=(52, 46, 40),
                  width=max(3, int(px(3.0))))
        d.ellipse(box(wx - r * 0.9, wy - r * 0.9, wx + r * 0.9, wy + r * 0.9),
                  outline=(96, 88, 76), width=max(1, int(px(1.2))))
        for k in range(8):
            a = math.radians(k * 45)
            d.line([(wx, wy), (wx + math.cos(a) * r * 0.88, wy + math.sin(a) * r * 0.88)],
                   fill=(120, 112, 96), width=max(1, int(px(1.2))))
        d.ellipse(box(wx - px(5), wy - px(5), wx + px(5), wy + px(5)), fill=(70, 62, 52))
    # the bed of the cart, tipped up against the wall
    d.polygon([(cx - px(54), PLINTH - px(64)), (cx + px(56), PLINTH - px(76)),
               (cx + px(56), PLINTH - px(54)), (cx - px(54), PLINTH - px(42))],
              fill=mix(TIMBER, (150, 110, 70), 0.35))
    for k in range(4):
        fx = cx - px(50) + k * px(26)
        d.line([(fx, PLINTH - px(62)), (fx, PLINTH - px(44))], fill=(46, 32, 20),
               width=max(1, int(px(1.4))))
    # the shafts
    d.line([(cx - px(54), PLINTH - px(46)), (cx - px(96), PLINTH - px(10))],
           fill=mix(TIMBER, (150, 110, 70), 0.3), width=max(3, int(px(3.4))))
    d.line([(cx - px(56), PLINTH - px(58)), (cx - px(92), PLINTH - px(22))],
           fill=(58, 40, 26), width=max(2, int(px(2.2))))
    lamp(cx, PLINTH - px(60), px(150), (255, 180, 110), 40)


# ------------------------------------------------------------------ the paving
def paving(base):
    """Wet brick paving, and every sign in the lane lying in it."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(11)
    d.rectangle(box(0, FLOOR_Y, W, H), fill=BRICKS)
    rows = [FLOOR_Y, FLOOR_Y + px(18), FLOOR_Y + px(40), FLOOR_Y + px(68), FLOOR_Y + px(104), H]
    row = 0
    for i in range(len(rows) - 1):
        y0, y1 = rows[i], rows[i + 1]
        off = 0 if row % 2 == 0 else px(34)
        x = -off
        while x < W:
            bw = px(66) + (px(10) if (row + int(x / px(66))) % 3 == 0 else 0)
            c = tint(mix(BRICKS, rnd.choice((BRICKS_L, BRICKS_D, (86, 56, 48))),
                         rnd.uniform(0.10, 0.40)), rnd, 0.06)
            d.rectangle(box(x, y0, x + bw, y1), fill=c)
            d.line([(x, y0), (x + bw, y0)], fill=mix(c, (150, 116, 96), 0.22),
                   width=max(1, int(px(0.5))))
            d.line([(x, y1), (x + bw, y1)], fill=mix(c, (24, 16, 12), 0.5),
                   width=max(1, int(px(0.6))))
            d.line([(x, y0), (x, y1)], fill=mix(c, (24, 16, 12), 0.5),
                   width=max(1, int(px(0.5))))
            x += bw
        row += 1

    # the wall's shadow on the paving
    for i in range(px(16)):
        a = int(130 * (1 - i / float(px(16))) ** 1.5)
        d.line([(0, FLOOR_Y + i), (W, FLOOR_Y + i)], fill=(10, 8, 8, a))

    # puddles, then the light lying in them
    puddle = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(puddle)
    for cx0, cy0, w, h in ((px(260), FLOOR_Y + px(60), px(300), px(40)),
                           (px(700), FLOOR_Y + px(90), px(420), px(52)),
                           (px(1180), FLOOR_Y + px(54), px(300), px(38)),
                           (px(1560), FLOOR_Y + px(80), px(320), px(44))):
        pd.ellipse(box(cx0 - w / 2.0, cy0 - h / 2.0, cx0 + w / 2.0, cy0 + h / 2.0),
                   fill=(18, 22, 24, 130))
    base.alpha_composite(puddle.filter(ImageFilter.GaussianBlur(px(9))))

    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    for cx0, col, wdt, a in (((SHOP_A[0] + SHOP_A[1]) / 2.0, (255, 178, 104), px(320), 78),
                             ((SHOP_B[0] + SHOP_B[1]) / 2.0, (255, 178, 104), px(320), 72),
                             ((DOORWAY[0] + DOORWAY[1]) / 2.0, (255, 150, 92), px(200), 74),
                             (px(380), (255, 90, 60), px(110), 60),
                             (px(1430), (120, 226, 160), px(180), 58),
                             (px(1600), (255, 150, 90), px(130), 50)):
        rd.polygon([(cx0 - wdt / 2.0, FLOOR_Y + px(4)), (cx0 + wdt / 2.0, FLOOR_Y + px(4)),
                    (cx0 + wdt * 1.3, H), (cx0 - wdt * 1.3, H)], fill=col + (a,))
    base.alpha_composite(refl.filter(ImageFilter.GaussianBlur(px(24))))

    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.rectangle(box(0, FLOOR_Y, W, H), fill=(198, 190, 176, 16))
    base.alpha_composite(sheen.filter(ImageFilter.GaussianBlur(px(14))))

    # a drain, rubbish blown along the gutter
    dx = px(1000)
    d.rectangle(box(dx - px(30), FLOOR_Y + px(30), dx + px(30), FLOOR_Y + px(44)),
                fill=(30, 30, 30))
    for k in range(6):
        sx = dx - px(26) + k * px(9)
        d.line([(sx, FLOOR_Y + px(32)), (sx, FLOOR_Y + px(42))], fill=(92, 92, 88),
               width=max(1, int(px(1.8))))
    # a little rubbish, kept sparse: at thirty-odd pieces the pale scraps read as
    # a snowfall over the whole lane
    for k in range(13):
        pxx = rnd.uniform(0, W)
        pyy = rnd.uniform(FLOOR_Y + px(14), H - px(8))
        w = rnd.uniform(px(7), px(13))
        d.polygon([(pxx, pyy), (pxx + w, pyy - px(3)), (pxx + w * 1.05, pyy + px(5)),
                   (pxx + px(2), pyy + px(7))],
                  fill=mix((196, 182, 152), BRICKS, rnd.uniform(0.30, 0.65)))


def foreground():
    """The near plane: steam drifting across, and the dark at the bottom."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(83)
    for i in range(px(38)):
        a = int(150 * (1 - i / float(px(38))) ** 1.6)
        d.line([(0, H - i), (W, H - i)], fill=(8, 7, 6, a))
    for k in range(5):                                  # steam
        sx = rnd.uniform(0, W)
        sy = rnd.uniform(FLOOR_Y - px(40), H)
        for j in range(6):
            rr = px(30) + j * px(14)
            d.ellipse(box(sx - rr, sy - rr * 0.5, sx + rr, sy + rr * 0.5),
                      fill=(220, 216, 206, 12))
    for _ in range(110):
        x = rnd.uniform(0, W)
        y = rnd.uniform(px(60), H)
        r = rnd.uniform(px(0.9), px(2.4))
        d.ellipse(box(x - r, y - r, x + r, y + r),
                  fill=(255, 214, 158, rnd.randint(16, 54)))
    return fg.filter(ImageFilter.GaussianBlur(px(3.0)))


# ------------------------------------------------------------------- the arena
def paint():
    LIGHTS.clear()
    base = hd.blank([(0, (14, 11, 9)), (EAVES, (28, 22, 18)),
                     (px(120), (48, 34, 26)), (FLOOR_Y, (52, 36, 30)),
                     (H, (28, 20, 18))])

    eaves(base)
    brick_wall(base)

    # left: a shop under its awning, with its board and lantern
    shopfront(base, SHOP_A[0], SHOP_A[1])
    awning(base, px(84), px(346))
    vertical_sign(base, px(378), px(66), px(168), 2)
    lantern(base, px(414), px(196))
    pipes(base, px(534))

    # middle: the recessed doorway, crates and the handcart
    doorway(base, DOORWAY[0], DOORWAY[1])
    crates(base, px(778), px(880))
    cart(base, px(940))
    pipes(base, px(1004))

    # right: the second shop, its board, and the green tube over the lane
    shopfront(base, SHOP_B[0], SHOP_B[1])
    awning(base, px(1070), px(1338))
    vertical_sign(base, px(1368), px(66), px(168), 5)
    neon(base, px(1404), px(1584), px(120))
    window(base, WINDOW_C[0], WINDOW_C[1], px(150), px(206))
    crates(base, px(1660), px(1748))

    paving(base)

    base = hd.shade(base, [(hd.light(cx, cy, r, col, int(peak * 0.82)),
                            max(8, int(r * 0.30)), 1.05)
                           for cx, cy, r, col, peak in LIGHTS])
    base = art.vignette(base, 0.50)
    base = art.grain(base, 3, seed=37)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


def main():
    hd.STAGES["shadow_alleys"] = ("Shadow Alleys", paint)
    hd.build("shadow_alleys")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
