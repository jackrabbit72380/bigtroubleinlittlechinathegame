"""Chinatown Market: the market's back wall at night.

Painted from the plan reference: a lane of stalls under grey canvas awnings,
stacked slatted crates and cardboard and foam boxes, open crates of tomatoes and
oranges and greens, wire baskets, barrels and slumped sacks, a brass scale hung
over the produce, bare bulbs on poles burning hard white light over the timber
counters, the red banner with its gold flames hanging at one end of the lane, the
chain-link fence and its vines at the other, and the big round fish tub with its
green water glowing under the stall lights. The ground is wet asphalt, holding
the green of the tub, the red of the banner and the violet of the street lamp.

A stage is seen across the play plane, so the market is painted as a wall
wall-to-wall: the counters, the crates, the tubs and the fence stand against the
back of the lane with their bases on the floor line, and the fighters stand on
the wet asphalt in front of them. Nothing comes out into the play plane to stand
on anybody's feet.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960, localcoord 1920x1080, camera travel +/-3136.

Run:  python3 tools/stage_chinatown_market.py     (part of tools/build_all.py)
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

SKY = px(58)                       # 261: the roofline, where the lane's wall starts
PLINTH = FLOOR_Y - px(2)           # 891: the line the counters and crates stand on
COUNTER_FACE = px(9)               # the counter's top slab is this thick, so a
                                   # crate standing on it is based this much higher

STALL_A = (px(120), px(392))       # the crate stall
STALL_B = (px(400), px(672))       # the produce stall under the big awning
PASSAGE = (px(690), px(880))       # between the stalls: barrels, sacks, crates
STALL_C = (px(892), px(1148))      # the boxes-and-bench stall
TANK_X = px(1232)                  # the green water tub
FENCE_X = (px(1560), W)            # the chain-link end of the lane
BANNER_C = px(56)                  # the red banner at the other end

NIGHT_T = (4, 5, 9)
NIGHT_B = (14, 16, 26)
WALL = (38, 35, 34)                # damp plaster behind the stalls
WALL_L = (52, 48, 46)
WALL_D = (18, 17, 18)
PIPE = (74, 76, 74)
PINE = (152, 98, 46)               # slatted crates, warm pine
PINE_L = (206, 148, 84)
PINE_D = (86, 52, 24)
CARD = (172, 130, 82)              # cardboard cartons
CARD_L = (208, 166, 112)
CARD_D = (108, 78, 44)
FOAM = (236, 228, 210)             # foam fish boxes
FOAM_D = (176, 168, 152)
WIRE = (152, 154, 150)
TOMATO = (202, 40, 24)
ORANGE = (238, 124, 22)
LEAF = (76, 122, 40)
LEAF_L = (152, 184, 88)
TANK = (54, 188, 114)              # the green water in the fish tub
CANVAS = (116, 106, 88)            # the awning over the produce
CANVAS_L = (150, 138, 114)
CANVAS_D = (70, 64, 52)
STEEL = (150, 154, 158)
BULB = (255, 240, 202)
LANTERN = (228, 68, 46)
VIOLET = (104, 92, 200)
ASPH = (28, 30, 36)                # the wet ground
ASPH_L = (46, 50, 60)
ASPH_D = (12, 13, 16)
BANNER = (154, 24, 28)             # the red banner
BANNER_L = (198, 46, 42)
GOLD_B = (214, 170, 76)
WARM = (255, 206, 150)

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


def contact(base, cx, base_y, w, alpha=170, depth=None):
    """The soft shadow a prop drops where its base meets what it stands on.

    Drawn before the prop, so its own body covers the middle of the shadow and
    what is left is the dark rim round its foot. Without it a crate is a card
    laid on a counter: every edge is lit, nothing sits on anything.
    """
    depth = px(9) if depth is None else depth
    bw = w * 1.30
    pad = int(px(14))
    lw, lh = int(bw) + 2 * pad, int(depth * 4) + 2 * pad
    sh = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    d.ellipse(box(pad, pad + lh * 0.22, lw - pad, pad + lh * 0.78), fill=(7, 5, 4, alpha))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(px(5))),
                         (int(cx - bw / 2.0 - pad), int(base_y - pad - lh * 0.5)))


# --------------------------------------------------------------------- the lane
def night(base):
    """The strip of night over the lane: a far roof, its windows, and the wires."""
    d = ImageDraw.Draw(base)
    for i in range(int(SKY)):
        d.line([(0, i), (W, i)], fill=mix(NIGHT_T, NIGHT_B, i / float(SKY)))
    rnd = random.Random(3)
    # the building across the lane, its eaves and a few lit windows
    y = SKY - px(14)
    x = 0
    while x < W:
        bw = rnd.uniform(px(90), px(220))
        bh = rnd.uniform(px(8), px(20))
        d.rectangle(box(x, y - bh, x + bw, SKY), fill=mix(NIGHT_B, (40, 40, 52), rnd.uniform(0, 0.5)))
        for wy in range(int(y - bh + px(3)), int(SKY) - int(px(3)), int(px(6))):
            for wx in range(int(x + px(4)), int(x + bw - px(4)), int(px(7))):
                if rnd.random() < 0.30:
                    d.rectangle(box(wx, wy, wx + px(2), wy + px(3)),
                                fill=mix((70, 62, 40), (232, 190, 120), rnd.uniform(0.2, 0.9)))
        x += bw + rnd.uniform(px(6), px(30))
    # wires sagging across the lane
    for k in range(3):
        y0 = px(12) + k * px(9)
        d.line([(0, y0), (W, y0 + px(5))], fill=(14, 15, 20), width=max(1, int(px(1.1))))
    # the eave of the stall row, a dark board under the sky
    d.rectangle(box(0, SKY - px(6), W, SKY), fill=(22, 22, 26))
    d.line([(0, SKY), (W, SKY)], fill=(10, 10, 12), width=max(1, int(px(1.2))))


def back_wall(base):
    """Damp plaster behind the stalls, its pipes, its shuttered doors, its posters."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(9)
    d.rectangle(box(0, SKY, W, PLINTH), fill=WALL_D)
    step = px(9)
    for i, x in enumerate(range(0, int(W), int(step))):
        c = tint(mix(WALL, WALL_L if i % 2 else WALL_D, rnd.uniform(0.10, 0.45)), rnd, 0.05)
        d.rectangle(box(x, SKY, x + step - px(1), PLINTH), fill=c)
    # blown plaster, and the brick under it
    for k in range(30):
        sx = rnd.uniform(0, W)
        sw, sh = rnd.uniform(px(24), px(80)), rnd.uniform(px(20), px(70))
        sy = rnd.uniform(SKY + px(30), PLINTH - sh)
        d.rectangle(box(sx, sy, sx + sw, sy + sh), fill=tint((96, 62, 50), rnd, 0.10))
    # pipes running down the wall, with their brackets
    for pxx in (px(196), px(864), px(1300)):
        d.rectangle(box(pxx, SKY, pxx + px(7), PLINTH), fill=mix(PIPE, WALL_D, 0.35))
        d.line([(pxx + px(1), SKY), (pxx + px(1), PLINTH)], fill=mix(PIPE, (200, 202, 200), 0.4),
               width=max(1, int(px(1.0))))
        for by in range(int(SKY) + int(px(40)), int(PLINTH), int(px(120))):
            d.rectangle(box(pxx - px(3), by, pxx + px(10), by + px(5)), fill=(70, 70, 68))
    # two shuttered doorways, dark, with their shutters half down
    for (dx0, dx1, top) in ((px(700), px(772), px(96)), (px(1470), px(1536), px(104))):
        d.rectangle(box(dx0, top, dx1, PLINTH), fill=(16, 16, 18))
        slats = top + px(34)
        d.rectangle(box(dx0, top, dx1, slats), fill=mix(PIPE, (60, 60, 60), 0.5))
        for sy in range(int(top), int(slats), int(px(6))):
            d.line([(dx0, sy), (dx1, sy)], fill=(96, 96, 94), width=max(1, int(px(1.0))))
        d.line([(dx0, slats), (dx1, slats)], fill=(28, 28, 28), width=max(2, int(px(1.4))))
    # posters and a torn notice or two
    for (wx, wy, ww, wh, seed) in ((px(300), px(150), px(58), px(74), 4),
                                   (px(1090), px(132), px(48), px(62), 6),
                                   (px(1420), px(168), px(52), px(50), 8)):
        d.rectangle(box(wx, wy, wx + ww, wy + wh), fill=(214, 204, 176))
        d.rectangle(box(wx, wy, wx + ww, wy + wh), outline=(90, 80, 60),
                    width=max(1, int(px(1.2))))
        for row in range(3):
            d.line([(wx + px(5), wy + px(14) + row * wh / 4.0),
                    (wx + ww - px(5), wy + px(14) + row * wh / 4.0)],
                   fill=(150, 130, 96), width=max(1, int(px(1.0))))
    # grime where the wall meets the ground
    for i in range(px(26)):
        d.line([(0, PLINTH - i), (W, PLINTH - i)],
               fill=mix(WALL_D, (12, 12, 14), 0.55 * (1 - i / float(px(26)))))


def fence(base, x0, x1):
    """Chain-link on its posts, sagging, with vines grown through it."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(17)
    top = SKY + px(6)
    d.rectangle(box(x0, top, x1, PLINTH), fill=(30, 32, 40))
    # the lane beyond: night, a wet wall, one violet lamp
    for i in range(int(PLINTH) - int(top)):
        d.line([(x0, top + i), (x1, top + i)],
               fill=mix((18, 20, 28), (44, 40, 52), i / float(PLINTH - top)))
    d.ellipse(box(x0 + (x1 - x0) * 0.55, top + px(20), x0 + (x1 - x0) * 0.55 + px(40),
                  top + px(44)), fill=mix(VIOLET, (30, 30, 40), 0.55))
    # the mesh: two families of diagonals, clipped to the panel
    mesh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(mesh)
    step = px(11)
    x = x0 - (PLINTH - top)
    while x < x1:
        md.line([(x, top), (x + (PLINTH - top), PLINTH)], fill=(126, 130, 132, 150),
                width=max(1, int(px(1.0))))
        md.line([(x, PLINTH), (x + (PLINTH - top), top)], fill=(126, 130, 132, 150),
                width=max(1, int(px(1.0))))
        x += step
    base.alpha_composite(mesh)
    # posts and rails
    for pxx in list(range(int(x0), int(x1), int(px(150)))) + [int(x1) - int(px(4))]:
        d.rectangle(box(pxx, top - px(4), pxx + px(6), PLINTH), fill=(96, 98, 96))
        d.line([(pxx + px(1), top - px(4)), (pxx + px(1), PLINTH)], fill=(168, 170, 166),
               width=max(1, int(px(0.9))))
    d.rectangle(box(x0, top - px(5), x1, top), fill=(88, 90, 88))
    d.rectangle(box(x0, PLINTH - px(6), x1, PLINTH), fill=(88, 90, 88))
    # vines: little clusters of leaves climbing the mesh
    for c in range(26):
        vx = rnd.uniform(x0, x1)
        vy = rnd.uniform(top + px(10), PLINTH - px(10))
        n = rnd.randint(3, 7)
        for k in range(n):
            lx = vx + rnd.uniform(-px(14), px(14))
            ly = vy + rnd.uniform(-px(12), px(12))
            r = rnd.uniform(px(3), px(6))
            d.ellipse(box(lx - r, ly - r * 0.7, lx + r, ly + r * 0.7),
                      fill=tint(mix(LEAF, LEAF_L, rnd.uniform(0.2, 0.8)), rnd, 0.15))
    lamp(x0 + (x1 - x0) * 0.6, top + px(30), px(260), (120, 104, 210), 54)


def banner(base, cx):
    """The red banner with its gold flames, hanging down the end of the lane."""
    d = ImageDraw.Draw(base)
    w = px(56)
    y1 = px(360)
    d.rectangle(box(cx - w / 2.0, 0, cx + w / 2.0, y1), fill=mix(BANNER, (58, 12, 14), 0.25))
    # the cloth's folds, so it hangs rather than sticks
    for k in range(5):
        fx = cx - w / 2.0 + w * (k + 0.5) / 5.0
        d.line([(fx, 0), (fx + px(2), y1)],
               fill=mix(BANNER, BANNER_L if k % 2 else (92, 14, 16), 0.35),
               width=max(2, int(px(3.0))))
    # a gilt border down both edges
    for ex in (cx - w / 2.0 + px(3), cx + w / 2.0 - px(3)):
        d.line([(ex, 0), (ex, y1)], fill=mix(GOLD_B, (150, 96, 34), 0.25),
               width=max(2, int(px(1.6))))
    # gold flames, small and many, licking up the cloth
    for k in range(9):
        fy = px(24) + k * px(34)
        fl = px(17)
        d.polygon([(cx - w * 0.26, fy + fl), (cx - w * 0.08, fy + fl * 0.18),
                   (cx + px(2), fy), (cx + w * 0.12, fy + fl * 0.28),
                   (cx + w * 0.26, fy + fl)], fill=GOLD_B)
    # the tattered hem
    for k in range(9):
        hx = cx - w / 2.0 + w * k / 9.0
        d.polygon([(hx, y1), (hx + w / 9.0, y1), (hx + w / 18.0, y1 + px(8 + (k % 3) * 5))],
                  fill=(66, 12, 14))
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shade).rectangle(box(cx - w, 0, cx + w * 0.9, y1 + px(16)),
                                    fill=(0, 0, 0, 130))
    base.alpha_composite(shade.filter(ImageFilter.GaussianBlur(px(14))))
    lamp(cx, px(110), px(280), (255, 96, 66), 44)


def awning(base, x0, x1, y_top, y_front, col=CANVAS):
    """A canvas awning over a stall: sloping out of the wall, with a valance."""
    d = ImageDraw.Draw(base)
    tilt = px(14)
    d.polygon([(x0, y_top), (x1, y_top), (x1 + tilt, y_front), (x0 - tilt, y_front)],
              fill=col)
    # the canvas's panels and its wear
    n = 6
    for k in range(0, n, 2):
        f0, f1 = k / float(n), (k + 1) / float(n)
        t0, t1 = x0 + (x1 - x0) * f0, x0 + (x1 - x0) * f1
        b0, b1 = t0 - tilt + 2 * tilt * f0, t1 - tilt + 2 * tilt * f1
        d.polygon([(t0, y_top), (t1, y_top), (b1, y_front), (b0, y_front)],
                  fill=mix(col, CANVAS_L, 0.35))
    rnd = random.Random(int(x0) + 7)
    for k in range(14):
        sx = rnd.uniform(x0, x1)
        sy = rnd.uniform(y_top, y_front)
        d.ellipse(box(sx, sy, sx + rnd.uniform(px(10), px(34)), sy + rnd.uniform(px(4), px(14))),
                  fill=mix(col, CANVAS_D, rnd.uniform(0.2, 0.5)))
    d.line([(x0, y_top), (x1, y_top)], fill=mix(col, (224, 226, 210), 0.4),
           width=max(2, int(px(1.6))))
    # the valance over the front edge, and its shadow
    d.polygon([(x0 - tilt, y_front), (x1 + tilt, y_front),
               (x1 + tilt, y_front + px(18)), (x0 - tilt, y_front + px(18))],
              fill=mix(col, CANVAS_D, 0.22))
    step = (x1 - x0 + 2 * tilt) / 9.0
    for k in range(9):
        hx = x0 - tilt + step * (k + 0.5)
        d.pieslice(box(hx - step / 2.0, y_front + px(10), hx + step / 2.0, y_front + px(26)),
                   0, 180, fill=mix(col, CANVAS_D, 0.30))
    for i in range(px(10)):
        d.line([(x0 - tilt, y_front + px(18) + i), (x1 + tilt, y_front + px(18) + i)],
               fill=mix(col, (14, 14, 18), 0.7 * (1 - i / float(px(10)))))
    # the rods holding it out
    for rx in (x0 + px(6), x1 - px(6)):
        d.line([(rx, y_top), (rx, y_front + px(16))], fill=mix(STEEL, (60, 62, 66), 0.4),
               width=max(2, int(px(1.8))))
    lamp((x0 + x1) / 2.0, y_front + px(30), px(280), (255, 214, 168), 44)


def counter(base, x0, x1, top):
    """A rough timber stall counter: a thick top, plank front, and its legs."""
    d = ImageDraw.Draw(base)
    contact(base, (x0 + x1) / 2.0, PLINTH, (x1 - x0) * 1.03, alpha=200, depth=px(16))
    d.rectangle(box(x0, top, x1, PLINTH), fill=mix(PINE, PINE_D, 0.45))
    # the front planks, each lit along its top edge, over a vertical shade
    y = top + px(8)
    k = 0
    while y < PLINTH - px(4):
        depth = (y - top) / max(1.0, PLINTH - top)
        c = mix(PINE, PINE_D, 0.28 + 0.30 * depth + 0.12 * (k % 2))
        d.rectangle(box(x0 + px(2), y, x1 - px(2), y + px(16)), fill=tint(c, random.Random(k + int(x0))))
        d.line([(x0 + px(2), y), (x1 - px(2), y)], fill=mix(c, PINE_L, 0.45),
               width=max(1, int(px(1.1))))
        d.line([(x0 + px(2), y + px(16)), (x1 - px(2), y + px(16))], fill=(24, 13, 6),
               width=max(2, int(px(1.6))))
        y += px(18)
        k += 1
    # the shadow the slab throws down its own front, and the plank joints
    for i in range(px(16)):
        d.line([(x0 + px(2), top + px(6) + i), (x1 - px(2), top + px(6) + i)],
               fill=mix(PINE_D, (10, 6, 3), 0.85 * (1 - i / float(px(16)))))
    rnd = random.Random(int(x0) + 3)
    for jx in range(int(x0) + int(px(30)), int(x1) - int(px(20)), int(px(60))):
        d.line([(jx, top + px(24)), (jx + rnd.uniform(-px(3), px(3)), PLINTH)],
               fill=(40, 22, 10), width=max(1, int(px(1.2))))
    # the top slab, standing proud
    d.rectangle(box(x0 - px(8), top - px(10), x1 + px(8), top + px(6)),
                fill=mix(PINE, PINE_L, 0.12))
    for i in range(px(10)):
        d.line([(x0 - px(8), top - px(10) + i), (x1 + px(8), top - px(10) + i)],
               fill=mix(PINE_L, PINE, 0.35 + 0.5 * (i / float(px(10)))))
    d.line([(x0 - px(8), top - px(10)), (x1 + px(8), top - px(10))], fill=(232, 200, 152),
           width=max(2, int(px(2.0))))
    d.line([(x0 - px(8), top + px(6)), (x1 + px(8), top + px(6))], fill=(22, 12, 6),
           width=max(2, int(px(1.8))))
    lamp((x0 + x1) / 2.0, top - px(6), px(260), (255, 196, 140), 38)


def crate(base, cx, base_y, w, h, seed=0):
    """One slatted pine crate, seen from its side."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(seed)
    x0, x1 = cx - w / 2.0, cx + w / 2.0
    y1 = base_y
    y0 = base_y - h
    contact(base, cx, base_y, w)
    d.rectangle(box(x0, y0, x1, y1), fill=(26, 14, 6))
    # the slats, with the gaps showing the dark behind. Each slat is lit along
    # its top edge only and goes dark toward its foot, which is what makes a
    # stack of them read as boards rather than as a printed card.
    n = 4
    slat = (h - px(8)) / n
    for k in range(n):
        sy = y0 + px(3) + k * (slat + px(2))
        base_c = mix(PINE, PINE_D, 0.30 + 0.22 * (k / float(n)))
        c = tint(mix(base_c, PINE_L, rnd.uniform(0.0, 0.22)), rnd, 0.04)
        d.rectangle(box(x0 + px(2), sy, x1 - px(2), sy + slat), fill=c)
        for i in range(int(slat)):
            d.line([(x0 + px(2), sy + i), (x1 - px(2), sy + i)],
                   fill=mix(c, PINE_D, 0.55 * (i / max(1.0, slat))))
        d.line([(x0 + px(2), sy), (x1 - px(2), sy)], fill=mix(c, (240, 206, 152), 0.42),
               width=max(1, int(px(1.0))))
    # the corner posts, the diagonal brace, and a stencilled mark
    for bxx in (x0 + px(2), x1 - px(8)):
        d.rectangle(box(bxx, y0, bxx + px(6), y1), fill=mix(PINE, PINE_D, 0.30))
    d.line([(x0 + px(4), y1 - px(4)), (x1 - px(10), y0 + px(6))],
           fill=mix(PINE, PINE_D, 0.15), width=max(2, int(px(2.4))))
    d.rectangle(box(x0 + px(10), y0 + px(8), x0 + px(34), y0 + px(20)), fill=(196, 176, 132))
    d.line([(x0 + px(13), y0 + px(14)), (x0 + px(31), y0 + px(14))], fill=(96, 76, 50),
           width=max(1, int(px(1.2))))
    # the shade under the crate's own lip, and the dark where it meets the
    # crate or the counter it stands on
    for i in range(px(7)):
        d.line([(x0 + px(2), y0 + i), (x1 - px(2), y0 + i)],
               fill=mix(PINE_D, (18, 10, 5), 0.55 * (1 - i / float(px(7)))))
    for i in range(px(5)):
        d.line([(x0 + px(2), y1 - i), (x1 - px(2), y1 - i)],
               fill=mix(PINE_D, (14, 8, 4), 0.6 * (1 - i / float(px(5)))))
    d.rectangle(box(x0, y0, x1, y1), outline=(30, 18, 8), width=max(1, int(px(1.4))))


def crate_stack(base, cx, base_y, w, h, n, seed=0):
    """A stack of crates, each a little out of line with the one below it."""
    rnd = random.Random(seed)
    for k in range(n):
        off = rnd.uniform(-px(6), px(6))
        crate(base, cx + off, base_y - k * h, w, h, seed + k)


def carton(base, cx, base_y, w, h, seed=0):
    """A cardboard box, its flaps down, with a printed band."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(seed)
    x0, x1 = cx - w / 2.0, cx + w / 2.0
    y0 = base_y - h
    c = tint(CARD, rnd, 0.07)
    contact(base, cx, base_y, w)
    d.rectangle(box(x0, y0, x1, base_y), fill=c)
    d.rectangle(box(x0, y0, x1, y0 + px(6)), fill=mix(c, CARD_L, 0.45))
    d.line([(x0, y0 + px(6)), (x1, y0 + px(6))], fill=mix(c, CARD_D, 0.5),
           width=max(1, int(px(1.0))))
    # the tape seam down the middle, and the label
    d.rectangle(box(cx - px(3), y0, cx + px(3), base_y), fill=mix(c, (200, 186, 156), 0.35))
    d.rectangle(box(x0 + px(6), y0 + px(14), x1 - px(6), y0 + px(30)), fill=(150, 60, 44))
    d.line([(x0 + px(9), y0 + px(21)), (x1 - px(9), y0 + px(21))], fill=(214, 176, 120),
           width=max(1, int(px(1.2))))
    d.rectangle(box(x0, y0, x1, base_y), outline=mix(c, CARD_D, 0.6), width=max(1, int(px(1.0))))


def foam_box(base, cx, base_y, w, h):
    """A white foam fish box, lid on."""
    d = ImageDraw.Draw(base)
    x0, x1 = cx - w / 2.0, cx + w / 2.0
    y0 = base_y - h
    contact(base, cx, base_y, w)
    d.rectangle(box(x0, y0, x1, base_y), fill=FOAM)
    d.rectangle(box(x0, y0, x1, y0 + px(7)), fill=mix(FOAM, (255, 255, 252), 0.5))
    d.line([(x0, y0 + px(7)), (x1, y0 + px(7))], fill=FOAM_D, width=max(1, int(px(1.2))))
    for k in range(3):
        gx = x0 + (x1 - x0) * (k + 0.5) / 3.0
        d.line([(gx, y0 + px(9)), (gx, base_y)], fill=mix(FOAM, FOAM_D, 0.45),
               width=max(1, int(px(0.9))))
    d.rectangle(box(x0, y0, x1, base_y), outline=FOAM_D, width=max(1, int(px(1.2))))


def mesh_basket(base, cx, base_y, w, h):
    """A grey wire basket, and what is in it."""
    d = ImageDraw.Draw(base)
    x0, x1 = cx - w / 2.0, cx + w / 2.0
    y0 = base_y - h
    contact(base, cx, base_y, w)
    d.rectangle(box(x0, y0, x1, base_y), fill=(34, 36, 38))
    for gx in range(int(x0), int(x1), int(px(6))):
        d.line([(gx, y0), (gx, base_y)], fill=WIRE, width=max(1, int(px(0.9))))
    for gy in range(int(y0), int(base_y), int(px(6))):
        d.line([(x0, gy), (x1, gy)], fill=WIRE, width=max(1, int(px(0.9))))
    # the rim, and the cabbages or greens mounded over it
    d.rectangle(box(x0 - px(2), y0 - px(4), x1 + px(2), y0 + px(2)), fill=mix(WIRE, (200, 202, 198), 0.3))
    d.ellipse(box(x0 + px(4), y0 - px(14), x1 - px(4), y0 + px(4)), fill=LEAF_L)
    d.ellipse(box(x0 + px(10), y0 - px(18), x1 - px(10), y0 - px(2)), fill=mix(LEAF, LEAF_L, 0.55))


def produce(base, x0, x1, y, kind, seed=0):
    """The open top of a crate, heaped with produce."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(seed)
    d.rectangle(box(x0, y - px(10), x1, y + px(6)), fill=mix(PINE_D, (40, 26, 14), 0.4))
    base_col = {"tomato": TOMATO, "orange": ORANGE, "green": LEAF, "pale": LEAF_L}[kind]
    r = px(5.0)
    yy = y - px(6)
    row = 0
    while yy > y - px(22):
        x = x0 + r * (1.0 if row % 2 else 1.6)
        while x < x1 - r:
            c = tint(mix(base_col, (252, 214, 150) if kind != "green" else LEAF_L,
                         rnd.uniform(0.0, 0.20)), rnd, 0.05)
            d.ellipse(box(x - r, yy - r, x + r, yy + r), fill=c)
            d.ellipse(box(x - r * 0.42, yy - r * 0.78, x + r * 0.06, yy - r * 0.3),
                      fill=mix(c, (255, 248, 220), 0.66))
            x += r * 2.05
        yy -= r * 1.5
        row += 1


def produce_crate(base, cx, base_y, w, h, kind, seed=0):
    """A crate with its produce mounded over the top."""
    crate(base, cx, base_y, w, h, seed)
    produce(base, cx - w / 2.0 + px(3), cx + w / 2.0 - px(3), base_y - h, kind, seed + 4)


def barrel(base, cx, base_y, h, tipped=False):
    """A staved barrel, standing or on its side."""
    d = ImageDraw.Draw(base)
    w = px(44)
    rnd = random.Random(int(cx))
    contact(base, cx, base_y, w * (1.15 if not tipped else 1.1))
    if not tipped:
        x0, x1 = cx - w / 2.0, cx + w / 2.0
        y0 = base_y - h
        d.rectangle(box(x0, y0 + px(6), x1, base_y - px(4)), fill=mix(PINE, PINE_D, 0.4))
        for k in range(6):
            sx = x0 + (x1 - x0) * k / 6.0
            d.line([(sx, y0 + px(6)), (sx, base_y - px(4))],
                   fill=mix(PINE, PINE_D, 0.55), width=max(1, int(px(1.2))))
        d.ellipse(box(x0, y0, x1, y0 + px(14)), fill=mix(PINE, PINE_L, 0.25))
        d.ellipse(box(x0 + px(4), y0 + px(3), x1 - px(4), y0 + px(10)), fill=(72, 48, 28))
        for hy in (y0 + px(22), base_y - px(24)):
            d.rectangle(box(x0 - px(2), hy, x1 + px(2), hy + px(7)), fill=(78, 76, 72))
            d.line([(x0 - px(2), hy), (x1 + px(2), hy)], fill=(126, 124, 118),
                   width=max(1, int(px(1.0))))
    else:
        # on its side, mouth toward us: a dark ring of staves and an open head
        h = w
        x0, x1 = cx - h / 2.0, cx + h / 2.0
        y0 = base_y - px(30)
        d.rectangle(box(x0, y0, x1, base_y - px(2)), fill=mix(PINE, PINE_D, 0.45))
        d.ellipse(box(x0 - px(6), y0 - px(10), x1 + px(6), base_y + px(4)),
                  fill=mix(PINE, PINE_L, 0.30))
        d.ellipse(box(x0 + px(2), y0 - px(4), x1 - px(2), base_y - px(2)), fill=(52, 34, 20))
        for hy in (y0 + px(4), base_y - px(16)):
            d.line([(x0 - px(4), hy), (x1 + px(4), hy)], fill=(78, 76, 72),
                   width=max(2, int(px(3.0))))


def sack(base, cx, base_y, w, h, seed=0):
    """A slumped sack leaning against the stack."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(seed)
    c = tint((178, 152, 108), rnd, 0.08)
    contact(base, cx, base_y, w)
    d.polygon([(cx - w * 0.34, base_y), (cx - w * 0.50, base_y - h * 0.55),
               (cx - w * 0.22, base_y - h), (cx + w * 0.26, base_y - h * 0.96),
               (cx + w * 0.50, base_y - h * 0.50), (cx + w * 0.34, base_y)], fill=c)
    for k in range(3):
        fx = cx - w * 0.2 + k * w * 0.2
        d.line([(fx, base_y - h * 0.8), (fx + px(3), base_y - px(6))],
               fill=mix(c, (108, 94, 70), 0.4), width=max(1, int(px(1.4))))
    d.ellipse(box(cx - w * 0.24, base_y - h - px(4), cx + w * 0.24, base_y - h + px(8)),
              fill=mix(c, (196, 180, 146), 0.35))


def scale(base, cx, y):
    """A brass beam scale hanging over the produce."""
    d = ImageDraw.Draw(base)
    d.line([(cx, y - px(40)), (cx, y)], fill=mix(GOLD_B, (110, 82, 34), 0.4),
           width=max(2, int(px(2.2))))
    d.line([(cx - px(30), y), (cx + px(30), y)], fill=mix(GOLD_B, (236, 200, 116), 0.4),
           width=max(2, int(px(2.4))))
    for ex in (cx - px(30), cx + px(30)):
        d.line([(ex, y), (ex, y + px(16))], fill=mix(GOLD_B, (150, 110, 44), 0.4),
               width=max(1, int(px(1.4))))
        d.ellipse(box(ex - px(14), y + px(14), ex + px(14), y + px(26)),
                  fill=mix(STEEL, (170, 176, 172), 0.4))
        d.ellipse(box(ex - px(10), y + px(16), ex + px(10), y + px(22)), fill=(70, 74, 74))
    lamp(cx, y + px(6), px(120), (255, 214, 160), 26)


def bulb(base, cx, y_bulb, y_top=SKY):
    """A bare bulb on its flex, with a tin shade: the market's hard white light."""
    d = ImageDraw.Draw(base)
    d.line([(cx, y_top), (cx, y_bulb - px(12))], fill=(24, 24, 26),
           width=max(1, int(px(1.6))))
    d.polygon([(cx - px(16), y_bulb - px(10)), (cx + px(16), y_bulb - px(10)),
               (cx + px(7), y_bulb - px(24)), (cx - px(7), y_bulb - px(24))],
              fill=(96, 92, 84))
    d.ellipse(box(cx - px(6), y_bulb - px(14), cx + px(6), y_bulb - px(2)), fill=BULB)
    lamp(cx, y_bulb + px(6), px(300), (255, 232, 186), 132)


def lantern(base, cx, cy, r=px(22)):
    """A red paper lantern over the passage."""
    d = ImageDraw.Draw(base)
    d.line([(cx, SKY), (cx, cy - r * 2.0)], fill=(26, 24, 24), width=max(1, int(px(1.6))))
    hd.hang_lantern(d, cx, cy, r, body=LANTERN, cap=mix(GOLD_B, (110, 80, 34), 0.3))
    lamp(cx, cy, px(150), (255, 116, 76), 70)


def tank(base, cx):
    """The big round fish tub, its water green and lit from the stall behind it."""
    d = ImageDraw.Draw(base)
    r = px(30)
    top = PLINTH - px(24)
    contact(base, cx, PLINTH - px(2), r * 2.05, alpha=190, depth=px(12))
    d.ellipse(box(cx - r, top - px(9), cx + r, top + px(10)), fill=mix(STEEL, (70, 74, 76), 0.4))
    d.rectangle(box(cx - r, top, cx + r, PLINTH - px(3)), fill=mix(STEEL, (92, 96, 96), 0.35))
    d.ellipse(box(cx - r, PLINTH - px(11), cx + r, PLINTH), fill=mix(STEEL, (58, 62, 64), 0.5))
    # the water, a brimming green disc with the light on it
    d.ellipse(box(cx - r + px(3), top - px(4), cx + r - px(3), top + px(8)), fill=TANK)
    d.ellipse(box(cx - r + px(8), top - px(1), cx + r - px(8), top + px(6)),
              fill=mix(TANK, (196, 250, 200), 0.35))
    for k in range(4):
        d.arc(box(cx - r + px(6) + k * px(4), top + px(1) + k * px(2),
                  cx + r - px(6) - k * px(4), top + px(7) + k * px(2)),
              190, 340, fill=mix(TANK, (226, 255, 226), 0.4), width=max(1, int(px(1.0))))
    # the rim, and the tub's ribs
    d.arc(box(cx - r, top - px(9), cx + r, top + px(10)), 0, 360,
          fill=mix(STEEL, (206, 210, 208), 0.35), width=max(2, int(px(2.2))))
    for k in range(3):
        ry = top + px(9) + k * px(8)
        d.arc(box(cx - r, ry, cx + r, ry + px(8)), 20, 160,
              fill=mix(STEEL, (120, 124, 124), 0.4), width=max(1, int(px(1.4))))
    lamp(cx, top + px(2), px(230), (120, 250, 160), 92)
    lamp(cx, FLOOR_Y + px(50), px(280), (90, 210, 140), 52)


def bench(base, x0, x1, top=PLINTH - px(64)):
    """A long timber bench, its boards laid side by side."""
    d = ImageDraw.Draw(base)
    contact(base, (x0 + x1) / 2.0, PLINTH, (x1 - x0) * 1.02, alpha=185, depth=px(13))
    d.rectangle(box(x0, top, x1, top + px(12)), fill=mix(PINE, PINE_L, 0.25))
    for k in range(4):
        bx = x0 + (x1 - x0) * (k + 0.5) / 4.0
        d.line([(bx, top), (bx, top + px(12))], fill=PINE_D, width=max(1, int(px(1.0))))
    d.line([(x0, top), (x1, top)], fill=(232, 204, 158), width=max(2, int(px(1.6))))
    d.rectangle(box(x0 + px(8), top + px(12), x1 - px(8), top + px(16)), fill=PINE_D)
    for lx in (x0 + px(16), x1 - px(26)):
        d.rectangle(box(lx, top + px(16), lx + px(12), PLINTH), fill=mix(PINE, PINE_D, 0.4))


# --------------------------------------------------------------------- the floor
def floor(base):
    """Wet asphalt: cracks, standing water, and the market's colours in it."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(31)
    d.rectangle(box(0, FLOOR_Y, W, H), fill=ASPH)
    for i in range(int(H - FLOOR_Y)):
        tt = i / float(H - FLOOR_Y)
        d.line([(0, FLOOR_Y + i), (W, FLOOR_Y + i)], fill=mix(ASPH_D, ASPH_L, tt * 0.9))
    # patches, tar seams, and the grain of the road
    for k in range(60):
        px0 = rnd.uniform(0, W)
        py0 = rnd.uniform(FLOOR_Y + px(6), H - px(4))
        w, h = rnd.uniform(px(30), px(180)), rnd.uniform(px(4), px(16))
        d.ellipse(box(px0, py0, px0 + w, py0 + h),
                  fill=mix(ASPH, ASPH_L if k % 2 else ASPH_D, rnd.uniform(0.15, 0.5)))
    for k in range(14):
        sx = rnd.uniform(0, W)
        d.line([(sx, FLOOR_Y + px(4)), (sx + rnd.uniform(-px(60), px(60)), H)],
               fill=mix(ASPH_D, (14, 14, 16), 0.6), width=max(1, int(px(1.4))))
    # the wall's shadow at the foot
    for i in range(px(18)):
        d.line([(0, FLOOR_Y + i), (W, FLOOR_Y + i)],
               fill=mix(ASPH, (8, 8, 10), 0.55 * (1 - i / float(px(18)))))

    # standing water: dark pools with the lamps laid in them
    puddles = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(puddles)
    pools = []
    for k in range(16):
        wx = rnd.uniform(0, W)
        wy = rnd.uniform(FLOOR_Y + px(10), H - px(8))
        w, h = rnd.uniform(px(70), px(260)), rnd.uniform(px(10), px(30))
        pools.append((wx, wy, w, h))
        pd.ellipse(box(wx - w / 2.0, wy - h / 2.0, wx + w / 2.0, wy + h / 2.0),
                   fill=(14, 18, 26, 190))
    base.alpha_composite(puddles.filter(ImageFilter.GaussianBlur(px(8))))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    for wx, wy, w, h in pools:
        sd.ellipse(box(wx - w * 0.42, wy - h * 0.34, wx + w * 0.42, wy + h * 0.34),
                   fill=(96, 118, 142, 30))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(px(5))))

    # the light of the market lying down the wet ground
    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    spills = [((STALL_A[0] + STALL_A[1]) / 2.0, (255, 226, 178), px(260), 54),
              ((STALL_B[0] + STALL_B[1]) / 2.0, (255, 214, 166), px(320), 50),
              ((STALL_C[0] + STALL_C[1]) / 2.0, (255, 220, 172), px(280), 46),
              (TANK_X, (110, 240, 152), px(300), 74),
              (BANNER_C, (232, 66, 48), px(220), 44),
              (FENCE_X[0] + px(120), (120, 104, 206), px(280), 46),
              (FENCE_X[0] + px(30), (96, 86, 190), px(180), 30)]
    for cx0, col, wdt, a in spills:
        rd.polygon([(cx0 - wdt / 2.0, FLOOR_Y + px(4)), (cx0 + wdt / 2.0, FLOOR_Y + px(4)),
                    (cx0 + wdt * 1.25, H), (cx0 - wdt * 1.25, H)], fill=col + (a,))
    base.alpha_composite(refl.filter(ImageFilter.GaussianBlur(px(30))))

    # a shine where the light lands, then the rubbish the market leaves
    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd2 = ImageDraw.Draw(sheen)
    for cx0, col, wdt, a in ((TANK_X, (150, 255, 190), px(150), 40),
                             ((STALL_B[0] + STALL_B[1]) / 2.0, (255, 226, 186), px(180), 26),
                             (FENCE_X[0] + px(120), (150, 132, 232), px(160), 30)):
        for k in range(6):
            yy = FLOOR_Y + px(16) + k * px(18)
            ww = wdt * (1 + k * 0.2)
            sd2.line([(cx0 - ww / 2.0, yy), (cx0 + ww / 2.0, yy)], fill=col + (a,),
                     width=max(2, int(px(3.0))))
    base.alpha_composite(sheen.filter(ImageFilter.GaussianBlur(px(12))))

    for k in range(40):
        lx = rnd.uniform(0, W)
        ly = rnd.uniform(FLOOR_Y + px(12), H - px(6))
        w, h = rnd.uniform(px(8), px(22)), rnd.uniform(px(3), px(8))
        col = rnd.choice(((186, 186, 176), (128, 120, 100), (72, 96, 56)))
        d.ellipse(box(lx, ly, lx + w, ly + h), fill=col)
    lamp(CX, FLOOR_Y + px(90), px(560), (255, 214, 168), 24)


def foreground():
    """The near plane: the dark at the bottom, and the night's haze."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(43)
    for i in range(px(34)):
        a = int(160 * (1 - i / float(px(34))) ** 1.6)
        d.line([(0, H - i), (W, H - i)], fill=(6, 7, 9, a))
    for _ in range(130):
        x = rnd.uniform(0, W)
        y = rnd.uniform(px(60), H)
        r = rnd.uniform(px(0.9), px(2.6))
        d.ellipse(box(x - r, y - r, x + r, y + r),
                  fill=(255, 226, 190, rnd.randint(12, 40)))
    return fg.filter(ImageFilter.GaussianBlur(px(2.6)))


# ------------------------------------------------------------------- the arena
def night_veil(base):
    """The dark the stalls are lit against: the wall goes down behind them."""
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(veil)
    for i in range(0, int(px(230)), int(px(3))):
        a = int(165 * (1 - i / float(px(230))) ** 1.05)
        d.rectangle(box(0, SKY + i, W, SKY + i + px(3)), fill=(3, 4, 7, a))
    d.rectangle(box(0, 0, W, SKY), fill=(2, 3, 5, 96))
    base.alpha_composite(veil.filter(ImageFilter.GaussianBlur(px(18))))


def stall_a(base):
    """The crate stall: a counter with produce boxes and a wall of crates behind.

    Everything here is sized to the band the wall leaves - 128 units between the
    roofline and the floor line - so a crate is 14 units, not 34. The first pass
    used the crate helpers' numbers from an interior wall and the stacks ran off
    the top of the canvas.
    """
    x0, x1 = STALL_A
    top = PLINTH - px(34)
    awning(base, x0 - px(6), x1 + px(6), SKY + px(4), SKY + px(46),
           col=mix(CANVAS, (88, 86, 76), 0.35))
    counter(base, x0, x1, top)
    # behind the counter, crates and cartons stacked up to the awning
    surf = top - COUNTER_FACE
    crate_stack(base, x0 + px(26), surf, px(22), px(14), 3, seed=1)
    crate_stack(base, x0 + px(56), surf, px(20), px(13), 2, seed=5)
    carton(base, x0 + px(86), surf, px(22), px(16), seed=2)
    crate_stack(base, x0 + px(118), surf, px(22), px(14), 3, seed=3)
    carton(base, x0 + px(150), surf, px(22), px(15), seed=4)
    foam_box(base, x0 + px(180), surf, px(20), px(13))
    # on the counter: open crates of produce, a foam box, wire baskets
    produce_crate(base, x0 + px(32), surf, px(30), px(13), "tomato", seed=11)
    produce_crate(base, x0 + px(72), surf, px(28), px(12), "orange", seed=12)
    foam_box(base, x0 + px(110), surf, px(24), px(14))
    mesh_basket(base, x0 + px(146), surf, px(26), px(15))
    crate(base, x0 + px(184), surf, px(26), px(14), seed=13)
    # the basin stack beside the counter
    d = ImageDraw.Draw(base)
    for k in range(3):
        cy = PLINTH - px(4) - k * px(4)
        d.ellipse(box(x1 - px(6), cy - px(3), x1 + px(24), cy + px(4)),
                  fill=mix(STEEL, (120, 124, 122), 0.4))
    bulb(base, x0 + px(52), SKY + px(74), y_top=SKY + px(46))


def stall_b(base):
    """The produce stall: the big awning, the sloped crates, and the scale."""
    x0, x1 = STALL_B
    top = PLINTH - px(38)
    awning(base, x0 - px(10), x1 + px(10), SKY + px(2), SKY + px(50))
    counter(base, x0, x1, top)
    # the sloped display: three crates set at an angle, heaped with produce
    kinds = ("orange", "tomato", "green")
    for k, kind in enumerate(kinds):
        cx = x0 + px(40) + k * px(58)
        surf = top - COUNTER_FACE
        crate(base, cx, surf, px(52), px(14), seed=20 + k)
        produce(base, cx - px(25), cx + px(25), surf - px(15), kind, seed=24 + k)
    # boxes stacked along the foot of the counter
    crate_stack(base, x0 + px(16), PLINTH, px(24), px(14), 2, seed=31)
    carton(base, x0 + px(52), PLINTH, px(26), px(18), seed=32)
    foam_box(base, x0 + px(88), PLINTH, px(26), px(16))
    sack(base, x0 + px(122), PLINTH, px(26), px(24), seed=33)
    crate_stack(base, x0 + px(158), PLINTH, px(24), px(14), 2, seed=34)
    produce_crate(base, x0 + px(194), PLINTH, px(30), px(14), "tomato", seed=35)
    scale(base, x0 + px(152), SKY + px(52))
    bulb(base, x0 + px(28), SKY + px(78), y_top=SKY + px(50))


def passage(base):
    """Between the stalls: barrels, a tipped drum, sacks and a crate stack."""
    x0, x1 = PASSAGE
    barrel(base, x0 + px(22), PLINTH, px(26))
    barrel(base, x1 - px(26), PLINTH, px(24))
    barrel(base, x0 + px(70), PLINTH, px(22), tipped=True)
    sack(base, x0 + px(112), PLINTH, px(28), px(26), seed=41)
    crate_stack(base, x1 - px(74), PLINTH - px(26), px(22), px(13), 2, seed=42)
    carton(base, x1 - px(112), PLINTH, px(24), px(18), seed=43)
    mesh_basket(base, x0 + px(44), PLINTH - px(26), px(24), px(14))
    lantern(base, (x0 + x1) / 2.0, SKY + px(56))


def stall_c(base):
    """The boxes-and-bench stall: crates of greens being sorted on a long bench."""
    x0, x1 = STALL_C
    top = PLINTH - px(30)
    awning(base, x0 - px(4), x1 + px(4), SKY + px(6), SKY + px(44),
           col=mix(CANVAS, (78, 82, 74), 0.45))
    bench(base, x0 + px(6), x1 - px(6), top)
    surf = top + px(1)
    crate(base, x0 + px(40), surf, px(54), px(12), seed=52)
    produce(base, x0 + px(14), x0 + px(66), surf - px(13), "green", seed=51)
    crate(base, x0 + px(102), surf, px(50), px(12), seed=54)
    produce(base, x0 + px(78), x0 + px(126), surf - px(13), "pale", seed=53)
    foam_box(base, x0 + px(148), surf, px(24), px(13))
    mesh_basket(base, x0 + px(178), surf, px(24), px(14))
    crate_stack(base, x0 + px(24), PLINTH, px(24), px(14), 2, seed=55)
    carton(base, x1 - px(46), PLINTH, px(26), px(20), seed=56)
    crate_stack(base, x1 - px(24), PLINTH - px(30), px(20), px(13), 2, seed=57)
    bulb(base, x1 - px(34), SKY + px(72), y_top=SKY + px(44))


def tank_corner(base):
    """The fish tubs: the green one, its lidded neighbour, buckets and a hose."""
    tank(base, TANK_X)
    d = ImageDraw.Draw(base)
    r = px(26)
    cx = TANK_X + px(78)
    top = PLINTH - px(20)
    d.ellipse(box(cx - r, top - px(8), cx + r, top + px(9)), fill=mix(STEEL, (86, 90, 92), 0.4))
    d.rectangle(box(cx - r, top, cx + r, PLINTH - px(3)), fill=mix(STEEL, (104, 108, 108), 0.35))
    d.ellipse(box(cx - r + px(2), top - px(6), cx + r - px(2), top + px(7)),
              fill=mix(STEEL, (140, 144, 142), 0.3))
    # the mesh lid, its weave drawn across the face
    for k in range(5):
        d.line([(cx - r + px(5) + k * px(10), top - px(5)),
                (cx - r + px(5) + k * px(10), top + px(6))],
               fill=mix(STEEL, (60, 64, 62), 0.4), width=max(1, int(px(1.2))))
    for k in range(2):
        d.line([(cx - r + px(6), top - px(3) + k * px(5)), (cx + r - px(6), top - px(3) + k * px(5))],
               fill=mix(STEEL, (60, 64, 62), 0.4), width=max(1, int(px(1.2))))
    # buckets and a hose at the foot
    for k in range(3):
        bx = TANK_X - px(52) + k * px(20)
        d.polygon([(bx - px(7), PLINTH), (bx + px(7), PLINTH),
                   (bx + px(6), PLINTH - px(14)), (bx - px(6), PLINTH - px(14))],
                  fill=mix(STEEL, (150, 154, 150), 0.3))
        d.ellipse(box(bx - px(7), PLINTH - px(17), bx + px(7), PLINTH - px(11)),
                  fill=mix(STEEL, (176, 180, 176), 0.3))
    for k in range(3):
        d.arc(box(TANK_X - px(86), PLINTH - px(18) + k * px(3),
                  TANK_X - px(26), PLINTH + px(4) + k * px(3)),
              200, 340, fill=(58, 70, 58), width=max(2, int(px(2.0))))


def crates_end(base):
    """The last stretch before the fence: crates, sacks, a barrel and produce."""
    x0 = px(1370)
    crate_stack(base, x0 + px(20), PLINTH, px(26), px(15), 3, seed=61)
    crate_stack(base, x0 + px(54), PLINTH, px(24), px(14), 2, seed=62)
    sack(base, x0 + px(90), PLINTH, px(28), px(26), seed=63)
    barrel(base, x0 + px(122), PLINTH, px(28))
    carton(base, x0 + px(34), PLINTH - px(45), px(24), px(16), seed=65)
    produce_crate(base, x0 + px(150), PLINTH, px(30), px(15), "orange", seed=66)
    mesh_basket(base, x0 + px(96), PLINTH - px(28), px(24), px(14))
    bulb(base, x0 + px(70), SKY + px(84))


def paint():
    LIGHTS.clear()
    base = hd.blank([(0, (10, 11, 18)), (SKY, (26, 26, 34)),
                     (px(120), (40, 38, 38)), (FLOOR_Y, (44, 44, 48)),
                     (H, (24, 24, 28))])

    night(base)
    back_wall(base)
    fence(base, FENCE_X[0], FENCE_X[1])
    banner(base, BANNER_C)
    night_veil(base)

    stall_a(base)
    stall_b(base)
    passage(base)
    stall_c(base)
    tank_corner(base)
    crates_end(base)

    floor(base)

    base = hd.shade(base, [(hd.light(cx, cy, r, col, int(peak * 0.84)),
                            max(8, int(r * 0.30)), 1.05)
                           for cx, cy, r, col, peak in LIGHTS])
    base = hd.bloom(base, 204, px(4), 0.34)
    base = art.vignette(base, 0.60)
    base = art.grain(base, 3, seed=29)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


def main():
    hd.STAGES["chinatown_market"] = ("Chinatown Market", paint)
    hd.build("chinatown_market")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
