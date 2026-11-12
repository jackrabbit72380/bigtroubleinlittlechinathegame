"""Shadow Alley: the lane behind the exchange, at night, under the neon.

Painted from the reference: the alley seen at night with the tiled eaves hanging
over it, shutters and brick down both sides, vertical shop boards and a horizontal
sign burning red, a green neon at the far end, bamboo scaffold poles wrapped
red-and-yellow crossing the lane, a pedicab left standing between them, crates and
a barrel against the wall, and brick paving under the lot with the signs' colour
lying across it in pools.

A stage is seen across the play plane, so the lane is painted as a wall
wall-to-wall: the shutters, the signs and the pedicab stand against the back of
the lane with their bases on the floor line, and the fighters stand on the wet
bricks in front of them. Nothing comes out into the play plane to stand on
anybody's feet.

Distinct from the earlier Shadow Alleys stage, which is the daytime lane with its
awnings and handcart: this one is the night side, and the neon is what does the
painting.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960, localcoord 1920x1080, camera travel +/-3136.

Run:  python3 tools/stage_shadow_alley.py     (part of tools/build_all.py)
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

EAVES = px(44)                     # 198: the tiled eaves over the lane
CEIL = px(58)                      # 261: the wall starts here
PLINTH = FLOOR_Y - px(12)          # 846
SHUTTER_L = (px(10), px(430))
SHUTTER_R = (px(1330), px(1740))
DOOR = (px(690), px(810))
GREEN_END = px(1830)

BRICK = (74, 54, 48)               # the wall, at night
BRICK_L = (108, 80, 68)
BRICK_D = (40, 28, 24)
PLASTER = (96, 88, 78)
TIMBER = (56, 38, 26)
SLAT = (86, 78, 74)                # the shutter's steel slats
SLAT_L = (128, 118, 110)
SLAT_D = (46, 40, 38)
PAVE = (70, 52, 46)                # the paving
PAVE_L = (104, 78, 68)
PAVE_D = (38, 26, 22)
RED = (150, 28, 26)
RED_L = (206, 56, 44)
NEON_R = (255, 76, 72)
NEON_Y = (255, 194, 104)
NEON_G = (92, 240, 150)
NEON_P = (255, 116, 176)
BAMBOO = (168, 140, 88)
BAMBOO_D = (104, 84, 50)
RUSTY = (108, 62, 40)

LIGHTS = []


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def tint(c, rnd, amt=0.07):
    return tuple(max(0, min(255, int(v * (1 + rnd.uniform(-amt, amt))))) for v in c)


def box(x0, y0, x1, y1):
    """Normalised corners: PIL refuses a rectangle drawn bottom-up."""
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def lamp(cx, cy, r, color=NEON_Y, peak=150):
    LIGHTS.append((cx, cy, r, color, peak))


def neon(d, x0, y0, x1, y1, color, body=(20, 12, 16)):
    """A lit board: dark plate, a coloured tube and a white-hot core inside it.

    A single thin outline reads as a picture frame; neon is a tube, so the frame
    is drawn wide in the colour and narrow in near-white on top of it, and the
    bloom pass does the rest.
    """
    d.rectangle(box(x0, y0, x1, y1), fill=body)
    d.rectangle(box(x0, y0, x1, y1), outline=mix(color, body, 0.30),
                width=max(3, int(px(7.0))))
    d.rectangle(box(x0 + px(2), y0 + px(2), x1 - px(2), y1 - px(2)),
                outline=mix(color, (255, 255, 255), 0.55), width=max(2, int(px(2.6))))
    d.rectangle(box(x0 + px(14), y0 + px(14), x1 - px(14), y1 - px(14)),
                outline=mix(color, body, 0.55), width=max(1, int(px(1.4))))


# ------------------------------------------------------------------ the lane
def eaves(base):
    """Night over the lane, and the tiled eaves hanging over it."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, 0, W, EAVES), fill=(11, 10, 16))
    for i in range(int(EAVES) - int(px(8))):
        d.line([(0, i), (W, i)], fill=mix((20, 18, 26), (9, 8, 12), i / float(EAVES)))
    # the tile course seen end on: half rounds, dark between them
    x = -px(8)
    n = 0
    while x < W:
        c = mix((92, 68, 46), (48, 34, 24), 0.25 + 0.5 * ((n % 3) / 2.0))
        d.pieslice(box(x, EAVES - px(24), x + px(20), EAVES + px(2)), 180, 360, fill=c)
        d.line([(x + px(2), EAVES - px(22)), (x + px(2), EAVES - px(2))],
               fill=mix(c, (140, 106, 70), 0.3), width=max(1, int(px(0.8))))
        x += px(19)
        n += 1
    d.rectangle(box(0, EAVES, W, EAVES + px(7)), fill=mix(TIMBER, (24, 16, 10), 0.5))
    d.line([(0, EAVES + px(7)), (W, EAVES + px(7))], fill=(10, 8, 8),
           width=max(2, int(px(2.0))))
    # the wire the lanterns hang from, and the shadow of the eaves on the wall
    wy = CEIL + px(10)
    for x in range(0, int(W), int(px(6))):
        d.line([(x, wy + int(math.sin(x / float(px(120))) * px(4))),
                (x + px(6), wy + int(math.sin((x + px(6)) / float(px(120))) * px(4)))],
               fill=(18, 16, 18), width=max(1, int(px(1.4))))
    for i in range(px(22)):
        a = int(150 * (1 - i / float(px(22))) ** 1.4)
        d.line([(0, EAVES + px(7) + i), (W, EAVES + px(7) + i)], fill=(7, 7, 10, a))


def brick_wall(base):
    """Running-bond brick between the shutters, dark and damp."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(3)
    d.rectangle(box(0, CEIL, W, PLINTH), fill=BRICK_D)
    bh, bw = px(13), px(30)
    row = 0
    y = CEIL
    while y < PLINTH:
        x = -bw // 2 if row % 2 else 0
        while x < W:
            c = tint(mix(BRICK, rnd.choice((BRICK_L, BRICK_D, (94, 66, 56))),
                         rnd.uniform(0.10, 0.45)), rnd, 0.06)
            d.rectangle(box(x + px(1), y + px(1), x + bw - px(1), y + bh - px(1)), fill=c)
            d.line([(x + px(1), y + px(1)), (x + bw - px(1), y + px(1))],
                   fill=mix(c, (150, 116, 100), 0.22), width=max(1, int(px(0.6))))
            x += bw
        y += bh
        row += 1
    # patches of old plaster, and the damp at the foot
    for k in range(18):
        px0 = rnd.uniform(0, W)
        pw = rnd.uniform(px(40), px(120))
        ph = rnd.uniform(px(24), px(70))
        d.rectangle(box(px0, rnd.uniform(CEIL, PLINTH - ph), px0 + pw,
                        rnd.uniform(CEIL, PLINTH)), fill=tint(PLASTER, rnd, 0.10))
    for i in range(px(26)):
        a = int(140 * (1 - i / float(px(26))) ** 1.5)
        d.line([(0, PLINTH - i), (W, PLINTH - i)], fill=(12, 10, 12, a))


def shutters(base):
    """Roller shutters down both sides, with their guide rails and graffiti."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(17)
    for (x0, x1), sign_col in ((SHUTTER_L, NEON_R), (SHUTTER_R, NEON_Y)):
        d.rectangle(box(x0 - px(8), CEIL, x1 + px(8), PLINTH), fill=(28, 24, 24))
        d.rectangle(box(x0, CEIL, x1, PLINTH), fill=SLAT_D)
        # the slats
        sy = CEIL + px(4)
        while sy < PLINTH - px(6):
            tt = (sy - CEIL) / max(1.0, PLINTH - CEIL)
            d.rectangle(box(x0, sy, x1, sy + px(7)),
                        fill=mix(mix(SLAT, SLAT_L, 0.35), (34, 30, 30), 0.25 + 0.4 * tt))
            d.line([(x0, sy), (x1, sy)], fill=mix(SLAT_L, (170, 160, 150), 0.3),
                   width=max(1, int(px(0.8))))
            sy += px(9)
        # the box the shutter rolls into, and the guide rails
        d.rectangle(box(x0 - px(10), CEIL - px(10), x1 + px(10), CEIL + px(6)),
                    fill=mix(SLAT_D, (30, 26, 26), 0.4))
        d.line([(x0 - px(10), CEIL - px(10)), (x1 + px(10), CEIL - px(10))],
               fill=(150, 142, 134), width=max(1, int(px(1.6))))
        for rx in (x0 - px(10), x1 + px(2)):
            d.rectangle(box(rx, CEIL - px(10), rx + px(8), PLINTH), fill=(64, 58, 56))
            d.line([(rx + px(1), CEIL), (rx + px(1), PLINTH)], fill=(126, 118, 110),
                   width=max(1, int(px(1.0))))
        # rust and tags
        for k in range(6):
            sx = rnd.uniform(x0, x1)
            for i in range(int(px(60))):
                a = int(70 * (1 - i / float(px(60))))
                d.line([(sx, PLINTH - px(60) + i), (sx, PLINTH - px(60) + i)],
                       fill=mix(RUSTY, (30, 22, 18), a / 255.0), width=max(1, int(px(2.0))))
        for k in range(3):
            gx = rnd.uniform(x0 + px(20), x1 - px(80))
            gy = rnd.uniform(PLINTH - px(70), PLINTH - px(30))
            hd.glyph(d, gx, gy, px(26), tint(sign_col, rnd, 0.1), seed=k + 5,
                     width=max(2, int(px(3))))


def doorway(base, x0, x1):
    """A recessed door with a lamp over it, and the light it throws."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(x0 - px(14), PLINTH - px(210), x1 + px(14), PLINTH), fill=(22, 18, 18))
    d.rectangle(box(x0, PLINTH - px(190), x1, PLINTH), fill=(34, 26, 24))
    d.rectangle(box(x0 + px(6), PLINTH - px(184), x1 - px(6), PLINTH - px(6)),
                fill=mix(TIMBER, (20, 14, 10), 0.35))
    for i in range(1, 4):
        d.line([(x0 + px(6), PLINTH - px(184) + i * px(44)),
                (x1 - px(6), PLINTH - px(184) + i * px(44))],
               fill=mix(TIMBER, (90, 66, 44), 0.4), width=max(1, int(px(1.4))))
    # the glass panel, lit from inside: a pane over the top of the door, not a
    # lit shopfront, so it stays small enough for the door to read as a door
    d.rectangle(box(x0 + px(14), PLINTH - px(176), x1 - px(14), PLINTH - px(138)),
                fill=(88, 62, 38))
    d.rectangle(box(x0 + px(17), PLINTH - px(173), x1 - px(17), PLINTH - px(141)),
                fill=(214, 168, 100))
    d.line([(x0 + px(17), PLINTH - px(158)), (x1 - px(17), PLINTH - px(158))],
           fill=(132, 98, 54), width=max(1, int(px(1.4))))
    # the lamp over the door
    d.rectangle(box(x0 + (x1 - x0) * 0.4, PLINTH - px(226), x0 + (x1 - x0) * 0.6,
                    PLINTH - px(212)), fill=(58, 50, 40))
    d.ellipse(box(x0 + (x1 - x0) * 0.42, PLINTH - px(214), x0 + (x1 - x0) * 0.58,
                  PLINTH - px(202)), fill=(250, 220, 160))
    lamp((x0 + x1) / 2.0, PLINTH - px(208), px(150), (255, 214, 158), 84)
    lamp((x0 + x1) / 2.0, PLINTH - px(140), px(120), (255, 200, 140), 46)


def signs(base):
    """The boards: a tall red one, a long one over the right shutter, a green end."""
    d = ImageDraw.Draw(base)
    # the tall vertical board, hung off the left shutter
    vx0, vx1 = px(320), px(404)
    vy0, vy1 = CEIL + px(26), PLINTH - px(150)
    neon(d, vx0, vy0, vx1, vy1, NEON_R)
    for k in range(5):
        gy = vy0 + px(14) + k * (vy1 - vy0 - px(28)) / 5.0
        hd.glyph(d, vx0 + px(14), gy, px(46), mix(NEON_R, (255, 255, 255), 0.60),
                 seed=k + 11, width=max(3, int(px(4))))
    lamp((vx0 + vx1) / 2.0, (vy0 + vy1) / 2.0, px(230), NEON_R, 96)

    # the long board over the right shutter, with its bracket
    hx0, hx1 = px(1352), px(1660)
    hy0, hy1 = CEIL + px(40), CEIL + px(118)
    d.line([(hx0 + px(20), hy0), (hx0 + px(20), CEIL)], fill=(30, 26, 26),
           width=max(2, int(px(2.0))))
    d.line([(hx1 - px(20), hy0), (hx1 - px(20), CEIL)], fill=(30, 26, 26),
           width=max(2, int(px(2.0))))
    neon(d, hx0, hy0, hx1, hy1, NEON_Y)
    for k in range(6):
        hd.glyph(d, hx0 + px(16) + k * px(46), hy0 + px(18), px(44),
                 mix(NEON_Y, (255, 255, 255), 0.55), seed=k + 31,
                 width=max(3, int(px(3.6))))
    lamp((hx0 + hx1) / 2.0, hy1, px(260), (255, 206, 130), 88)

    # a smaller pink board lower down, and the green one off the far edge
    neon(d, px(1760), PLINTH - px(180), px(1900), PLINTH - px(60), NEON_P)
    for k in range(3):
        hd.glyph(d, px(1772), PLINTH - px(168) + k * px(38), px(32),
                 mix(NEON_P, (255, 255, 255), 0.58), seed=k + 51,
                 width=max(2, int(px(3))))
    lamp(px(1830), PLINTH - px(120), px(180), NEON_P, 66)

    # the green neon at the end of the lane, washing the last of the wall
    d.rectangle(box(GREEN_END - px(10), CEIL, GREEN_END + px(14), PLINTH),
                fill=(30, 60, 44))
    d.line([(GREEN_END, CEIL), (GREEN_END, PLINTH)], fill=NEON_G,
           width=max(3, int(px(4.0))))
    lamp(GREEN_END - px(4), PLINTH - px(120), px(260), NEON_G, 104)
    lamp(GREEN_END - px(4), FLOOR_Y + px(50), px(240), (86, 210, 140), 60)


def drainpipe(base, cx):
    """A downpipe with its brackets and a bend at the foot."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(cx - px(7), CEIL, cx + px(7), PLINTH), fill=(74, 66, 60))
    for i in range(int(px(14))):
        tt = i / float(px(14))
        d.line([(cx - px(7) + i, CEIL), (cx - px(7) + i, PLINTH)],
               fill=mix((132, 122, 112), (40, 36, 34), tt / 0.9))
    for k in range(4):
        by = CEIL + px(40) + k * px(140)
        d.rectangle(box(cx - px(10), by, cx + px(10), by + px(7)), fill=(52, 46, 42))
    d.polygon([(cx - px(7), PLINTH - px(30)), (cx + px(7), PLINTH - px(30)),
               (cx + px(20), PLINTH), (cx + px(4), PLINTH)], fill=(70, 62, 56))


def ac_boxes(base, x0, x1):
    """Air conditioning boxes bolted to the wall above the shutter."""
    d = ImageDraw.Draw(base)
    y0, y1 = CEIL + px(150), CEIL + px(212)
    d.rectangle(box(x0, y0, x1, y1), fill=(96, 92, 86))
    d.rectangle(box(x0, y0, x1, y0 + px(6)), fill=(148, 142, 132))
    d.line([(x0, y1), (x1, y1)], fill=(38, 34, 32), width=max(2, int(px(1.8))))
    for i in range(9):
        d.line([(x0 + px(8) + i * (x1 - x0 - px(16)) / 9.0, y0 + px(12)),
                (x0 + px(8) + i * (x1 - x0 - px(16)) / 9.0, y1 - px(8))],
               fill=(64, 60, 56), width=max(1, int(px(1.2))))
    lamp((x0 + x1) / 2.0, y0, px(120), (150, 160, 170), 26)


def scaffold(base):
    """Bamboo poles lashing the scaffold across the lane.

    Bamboo poles, not hazard tape: a slim cane with a highlight down its round
    and red binding wrapped at intervals. Painted as a two-tone ribbon they read
    as police tape across the stage.
    """
    d = ImageDraw.Draw(base)
    # r is the cane's half-width, so these are slimmer than they look in code:
    # a pole drawn at px(6) is 54 px across and reads as a scaffold beam
    for (ax, ay, bx, by, r) in ((px(430), CEIL + px(34), px(1236), PLINTH - px(8), px(2.8)),
                                (px(1224), CEIL + px(76), px(470), PLINTH - px(4), px(2.4)),
                                (px(626), CEIL + px(12), px(648), PLINTH, px(2.0))):
        length = math.hypot(bx - ax, by - ay)
        nx, ny = -(by - ay) / length, (bx - ax) / length
        d.line([(ax, ay), (bx, by)], fill=BAMBOO_D, width=max(3, int(r * 2)))
        d.line([(ax + nx * r * 0.30, ay + ny * r * 0.30),
                (bx + nx * r * 0.30, by + ny * r * 0.30)],
               fill=mix(BAMBOO, (222, 192, 130), 0.40), width=max(2, int(r * 0.8)))
        # the red binding, a short turn of cord at intervals, not a full wrap
        n = max(1, int(length / px(52)))
        for k in range(n):
            t = (k + 0.5) / n
            cx0, cy0 = ax + (bx - ax) * t, ay + (by - ay) * t
            d.line([(cx0 + nx * r * 1.05, cy0 + ny * r * 1.05),
                    (cx0 - nx * r * 1.05, cy0 - ny * r * 1.05)],
                   fill=RED, width=max(2, int(r * 1.3)))
            d.line([(cx0 + nx * r * 1.05, cy0 + ny * r * 1.05),
                    (cx0 + nx * r * 0.10, cy0 + ny * r * 0.10)],
                   fill=RED_L, width=max(1, int(r * 0.6)))
        for (ex, ey) in ((ax, ay), (bx, by)):
            d.ellipse(box(ex - r * 1.5, ey - r * 1.5, ex + r * 1.5, ey + r * 1.5),
                      fill=(52, 40, 28))
        lamp((ax + bx) / 2.0, (ay + by) / 2.0, px(140), (170, 120, 90), 20)


def pedicab(base, cx):
    """A pedicab standing against the wall: canopy, seat, spoked wheels."""
    d = ImageDraw.Draw(base)
    gy = PLINTH
    r = px(30)
    # the two rear wheels, seen from the side
    for wx, wr in ((cx - px(46), r), (cx + px(46), r)):
        _spoked_wheel(d, wx, gy - wr, wr)
    # the frame and the step
    d.rectangle(box(cx - px(62), gy - px(64), cx + px(62), gy - px(54)), fill=(48, 42, 38))
    d.line([(cx - px(62), gy - px(64)), (cx + px(62), gy - px(64))],
           fill=(122, 112, 100), width=max(1, int(px(1.6))))
    # the seat cushion, and the backrest behind it with its seams
    d.rounded_rectangle(box(cx - px(50), gy - px(98), cx + px(50), gy - px(64)),
                        radius=max(2, int(px(10))), fill=mix(RED, (198, 62, 48), 0.35))
    d.line([(cx - px(46), gy - px(80)), (cx + px(46), gy - px(80))],
           fill=mix(RED, (92, 20, 18), 0.4), width=max(1, int(px(1.4))))
    d.rounded_rectangle(box(cx - px(56), gy - px(152), cx + px(56), gy - px(94)),
                        radius=max(2, int(px(10))), fill=mix(RED, (84, 18, 16), 0.35))
    for k in (-1, 0, 1):
        d.line([(cx + k * px(28), gy - px(150)), (cx + k * px(28), gy - px(96))],
               fill=mix(RED, (38, 10, 10), 0.45), width=max(1, int(px(1.2))))
    d.rounded_rectangle(box(cx - px(56), gy - px(152), cx + px(56), gy - px(94)),
                        radius=max(2, int(px(10))), outline=(26, 12, 12),
                        width=max(2, int(px(2.0))))
    # the canopy hood over the seat: cloth pulled across the hoop
    d.pieslice(box(cx - px(68), gy - px(232), cx + px(68), gy - px(148)), 180, 360,
               fill=mix(RED, (64, 13, 12), 0.50))
    d.arc(box(cx - px(68), gy - px(232), cx + px(68), gy - px(148)), 180, 360,
          fill=(48, 40, 34), width=max(3, int(px(3.0))))
    for sx in (-1, 1):
        d.line([(cx + sx * px(66), gy - px(210)), (cx + sx * px(66), gy - px(150))],
               fill=(44, 36, 32), width=max(2, int(px(2.4))))
    # a folded blanket left on the seat, not over the back
    d.polygon([(cx + px(6), gy - px(146)), (cx + px(46), gy - px(142)),
               (cx + px(50), gy - px(100)), (cx + px(12), gy - px(102))],
              fill=(56, 68, 92))
    d.line([(cx + px(12), gy - px(136)), (cx + px(44), gy - px(132))],
           fill=(84, 100, 128), width=max(1, int(px(1.6))))
    # handlebars, and the small front wheel seen end on
    d.line([(cx - px(64), gy - px(112)), (cx - px(86), gy - px(122))],
           fill=(140, 130, 118), width=max(2, int(px(3.0))))
    d.line([(cx + px(64), gy - px(112)), (cx + px(86), gy - px(122))],
           fill=(140, 130, 118), width=max(2, int(px(3.0))))
    _spoked_wheel(d, cx + px(86), gy - px(15), px(15))
    lamp(cx, gy - px(150), px(220), (255, 190, 120), 44)


def _spoked_wheel(d, cx, cy, r):
    """A wheel seen from the side: tyre, rim, spokes, hub."""
    d.ellipse(box(cx - r, cy - r, cx + r, cy + r), fill=(16, 14, 16))
    d.ellipse(box(cx - r * 0.92, cy - r * 0.92, cx + r * 0.92, cy + r * 0.92),
              fill=(36, 32, 30))
    d.ellipse(box(cx - r * 0.84, cy - r * 0.84, cx + r * 0.84, cy + r * 0.84),
              outline=(168, 158, 146), width=max(2, int(r * 0.13)))
    for k in range(14):
        a = k * math.pi / 7.0
        d.line([(cx + math.cos(a) * r * 0.20, cy + math.sin(a) * r * 0.20),
                (cx + math.cos(a) * r * 0.82, cy + math.sin(a) * r * 0.82)],
               fill=(146, 136, 124), width=max(1, int(r * 0.07)))
    d.ellipse(box(cx - r * 0.22, cy - r * 0.22, cx + r * 0.22, cy + r * 0.22),
              fill=(190, 182, 170))
    d.ellipse(box(cx - r * 0.09, cy - r * 0.09, cx + r * 0.09, cy + r * 0.09),
              fill=(70, 62, 56))


def crates(base, cx):
    """Crates stacked against the wall, and an oil drum beside them."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(53)
    for i, (dx, w, h) in enumerate(((0, px(64), px(52)), (px(66), px(56), px(44)),
                                    (px(8), px(52), px(40)))):
        y = PLINTH - sum(s[2] for s in ((0, px(64), px(52)), (px(66), px(56), px(44)),
                                        (px(8), px(52), px(40)))[:i + 1])
        c = tint((104, 80, 54), rnd, 0.08)
        d.rectangle(box(cx + dx, y, cx + dx + w, y + h), fill=c)
        d.rectangle(box(cx + dx, y, cx + dx + w, y + h), outline=(52, 38, 24),
                    width=max(1, int(px(1.4))))
        d.line([(cx + dx, y), (cx + dx + w, y + h)], fill=(52, 38, 24),
               width=max(1, int(px(1.2))))
        d.line([(cx + dx + w, y), (cx + dx, y + h)], fill=(52, 38, 24),
               width=max(1, int(px(1.2))))
        d.line([(cx + dx + px(4), y + px(4)), (cx + dx + w - px(4), y + px(4))],
               fill=mix(c, (180, 150, 110), 0.4), width=max(1, int(px(1.2))))
    # the drum
    dx0 = cx + px(130)
    d.rectangle(box(dx0, PLINTH - px(56), dx0 + px(44), PLINTH), fill=(66, 74, 66))
    for i in range(int(px(44))):
        d.line([(dx0 + i, PLINTH - px(56)), (dx0 + i, PLINTH)],
               fill=mix((96, 106, 96), (34, 40, 34), abs(i / 44.0 - 0.32) * 1.8))
    for k in range(2):
        d.rectangle(box(dx0, PLINTH - px(46) + k * px(26), dx0 + px(44),
                        PLINTH - px(42) + k * px(26)), fill=(40, 46, 40))
    d.ellipse(box(dx0, PLINTH - px(60), dx0 + px(44), PLINTH - px(50)), fill=(84, 92, 82))
    lamp(dx0 + px(22), PLINTH - px(30), px(110), (140, 150, 140), 18)


# ------------------------------------------------------------------ the paving
def paving(base):
    """Brick paving, wet, with the neon lying across it."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(61)
    d.rectangle(box(0, FLOOR_Y, W, H), fill=PAVE_D)
    rows = [FLOOR_Y, FLOOR_Y + px(18), FLOOR_Y + px(40), FLOOR_Y + px(68),
            FLOOR_Y + px(102), H]
    row = 0
    for i in range(len(rows) - 1):
        y0, y1 = rows[i], rows[i + 1]
        bw = px(34) + i * px(6)
        x = -bw // 2 if row % 2 else 0
        while x < W:
            c = tint(mix(PAVE, rnd.choice((PAVE_L, PAVE_D, (86, 62, 52))),
                         rnd.uniform(0.10, 0.40)), rnd, 0.06)
            d.rectangle(box(x + px(1), y0 + px(1), x + bw - px(1), y1 - px(1)), fill=c)
            d.line([(x + px(1), y0 + px(1)), (x + bw - px(1), y0 + px(1))],
                   fill=mix(c, (150, 120, 104), 0.20), width=max(1, int(px(0.6))))
            d.line([(x + px(1), y1 - px(1)), (x + bw - px(1), y1 - px(1))],
                   fill=mix(c, (16, 12, 12), 0.45), width=max(1, int(px(0.7))))
            x += bw
        row += 1

    # the base course the props stand on: a lit kerb between the wall's foot and
    # the floor line, so a crate or a wheel has something under it instead of
    # hanging over a black band
    d.rectangle(box(0, PLINTH, W, FLOOR_Y), fill=mix(PAVE, (118, 100, 86), 0.38))
    d.line([(0, PLINTH), (W, PLINTH)], fill=mix(PAVE_L, (192, 172, 150), 0.45),
           width=max(2, int(px(2.2))))
    d.line([(0, FLOOR_Y), (W, FLOOR_Y)], fill=(16, 12, 12), width=max(2, int(px(2.4))))

    # the wall's shadow at the foot, then the wet
    for i in range(px(14)):
        a = int(96 * (1 - i / float(px(14))) ** 1.5)
        d.line([(0, FLOOR_Y + i), (W, FLOOR_Y + i)], fill=(8, 6, 8, a))

    wet = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wet)
    for k in range(14):
        cx0 = rnd.uniform(0, W)
        w, h = rnd.uniform(px(90), px(280)), rnd.uniform(px(18), px(44))
        wd.ellipse(box(cx0 - w / 2.0, FLOOR_Y + rnd.uniform(px(30), px(120)) - h / 2.0,
                       cx0 + w / 2.0, FLOOR_Y + rnd.uniform(px(30), px(120)) + h / 2.0),
                   fill=(30, 34, 44, 120))
    base.alpha_composite(wet.filter(ImageFilter.GaussianBlur(px(9))))

    # the neon: a pool of its colour on the bricks, and its reflection running
    # down the paving toward the viewer
    for cx0, col, wdt, a, pool in ((px(362), NEON_R, px(250), 120, 300),
                                   (px(1506), NEON_Y, px(300), 132, 330),
                                   (px(1836), NEON_G, px(230), 150, 260),
                                   (px(1830), NEON_P, px(170), 84, 200),
                                   (px(750), (255, 214, 158), px(150), 86, 170)):
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse(box(cx0 - wdt * 0.8, FLOOR_Y + px(10), cx0 + wdt * 0.8,
                       FLOOR_Y + px(40) + pool * 0.55),
                   fill=col + (a // 2,))
        gd.polygon([(cx0 - wdt * 0.34, FLOOR_Y + px(6)), (cx0 + wdt * 0.34, FLOOR_Y + px(6)),
                    (cx0 + wdt * 0.52, H), (cx0 - wdt * 0.52, H)],
                   fill=col + (a,))
        base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(px(22))))

    # scattered rubbish, and the drain
    for k in range(26):
        sx = rnd.uniform(0, W)
        sy = rnd.uniform(FLOOR_Y + px(16), H - px(10))
        w, h = rnd.uniform(px(4), px(12)), rnd.uniform(px(2), px(6))
        d.rectangle(box(sx, sy, sx + w, sy + h),
                    fill=tint(rnd.choice((PLASTER, PAVE_L, (120, 108, 96))), rnd, 0.12))
    dx = px(1240)
    d.rectangle(box(dx - px(40), FLOOR_Y + px(46), dx + px(40), FLOOR_Y + px(62)),
                fill=(26, 24, 24))
    for k in range(8):
        d.line([(dx - px(34) + k * px(9), FLOOR_Y + px(48)),
                (dx - px(34) + k * px(9), FLOOR_Y + px(60))], fill=(78, 74, 68),
               width=max(1, int(px(2.0))))


def foreground():
    """The near plane: the dark at the bottom, and the steam off the drains."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(97)
    for i in range(px(34)):
        a = int(150 * (1 - i / float(px(34))) ** 1.6)
        d.line([(0, H - i), (W, H - i)], fill=(6, 6, 9, a))
    for k in range(6):
        sx = rnd.uniform(0, W)
        sy = rnd.uniform(FLOOR_Y, H)
        for j in range(4):
            rr = px(40) + j * px(20)
            d.ellipse(box(sx - rr, sy - rr * 0.45, sx + rr, sy + rr * 0.45),
                      fill=(190, 180, 200, 9))
    for _ in range(70):
        x = rnd.uniform(0, W)
        y = rnd.uniform(px(70), H)
        r = rnd.uniform(px(1.0), px(2.4))
        d.ellipse(box(x - r, y - r, x + r, y + r),
                  fill=(250, 236, 220, rnd.randint(16, 52)))
    return fg.filter(ImageFilter.GaussianBlur(px(3.0)))


# ------------------------------------------------------------------- the arena
def paint():
    LIGHTS.clear()
    base = hd.blank([(0, (9, 8, 12)), (CEIL, (16, 14, 20)),
                     (px(140), (24, 20, 24)), (FLOOR_Y, (28, 22, 24)),
                     (H, (12, 10, 14))])

    eaves(base)
    brick_wall(base)
    shutters(base)
    ac_boxes(base, px(120), px(300))
    drainpipe(base, px(1240))
    doorway(base, DOOR[0], DOOR[1])
    signs(base)
    scaffold(base)
    pedicab(base, px(880))
    crates(base, px(1080))

    paving(base)

    base = hd.shade(base, [(hd.light(cx, cy, r, col, int(peak * 0.86)),
                            max(8, int(r * 0.30)), 1.10)
                           for cx, cy, r, col, peak in LIGHTS])
    base = hd.bloom(base, 124, px(7), 1.15)      # the signs have to burn
    base = art.vignette(base, 0.50)
    base = art.grain(base, 3, seed=57)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


def main():
    hd.STAGES["shadow_alley"] = ("Shadow Alley", paint)
    hd.build("shadow_alley")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
