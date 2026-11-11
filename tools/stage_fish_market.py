"""Fish Market: the tiled back room where the catch is landed and gutted.

Painted from the reference: glazed green-grey tiles with dark grout, a vent high
in the wall with the daylight coming green through it, rusty iron pipework down
the left with its flanges and a valve, a riveted steel door on the right, and the
day's catch heaped on its red sheet against the tiles with ice scattered round
it. The floor is the same tile, wet, with the water and the blood of the trade
lying on it.

A stage is seen across the play plane, so the room is painted as a wall
wall-to-wall: the fish heap, the bench and the bucket stand against the back of
the room with their bases on the floor line, and the fighters stand on the wet
tiles in front of them. Nothing comes out into the play plane to stand on
anybody's feet.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960, localcoord 1920x1080, camera travel +/-3136.

Run:  python3 tools/stage_fish_market.py     (part of tools/build_all.py)
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

CEIL = px(38)                      # 171: the ceiling and its steel beam
BEAM = px(48)                      # 216: the beam's underside
PLINTH = FLOOR_Y - px(10)          # 855
VENT = (px(74), px(258))
VENT_Y = (px(54), px(104))
DOOR = (px(1436), px(1636))
PIPES = (px(300), px(360))
FISH_CX = px(880)
BENCH = (px(60), px(430))
DRAIN = px(1180)

TILE = (106, 120, 114)             # glazed tile
TILE_L = (140, 154, 146)
TILE_D = (74, 88, 82)
GROUT = (52, 58, 52)
STEEL = (152, 158, 154)
STEEL_L = (206, 210, 206)
STEEL_D = (86, 92, 88)
RUST = (134, 76, 42)
RUST_D = (84, 44, 24)
SILVER = (184, 194, 198)           # the fish
SILVER_D = (112, 122, 128)
TARP = (148, 44, 38)
FLOOR_T = (116, 126, 116)          # the floor tile
WATER = (58, 74, 66)
BLOOD = (96, 30, 26)
ICE = (216, 226, 228)
WARM = (255, 202, 142)
GREEN_LIGHT = (170, 226, 200)

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


# ------------------------------------------------------------------ the room
def ceiling(base):
    """The ceiling slab, a steel beam under it, and a strip light."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, 0, W, CEIL), fill=(52, 50, 44))
    for x in range(-px(20), W, px(150)):
        d.line([(x, 0), (x, CEIL)], fill=(40, 38, 32), width=max(1, int(px(1.2))))
    d.rectangle(box(0, CEIL, W, BEAM), fill=(66, 62, 54))
    d.line([(0, CEIL), (W, CEIL)], fill=(96, 92, 82), width=max(1, int(px(1.0))))
    d.line([(0, BEAM), (W, BEAM)], fill=(28, 26, 22), width=max(2, int(px(1.8))))
    # the strip light over the room, with its shade
    lx0, lx1 = px(700), px(1080)
    d.rectangle(box(lx0, BEAM - px(10), lx1, BEAM - px(2)), fill=(120, 124, 120))
    d.rectangle(box(lx0 + px(6), BEAM - px(6), lx1 - px(6), BEAM - px(2)),
                fill=(246, 248, 236))
    for i in range(px(16)):
        a = int(110 * (1 - i / float(px(16))))
        d.line([(0, BEAM + i), (W, BEAM + i)], fill=(24, 24, 20, a))
    lamp((lx0 + lx1) / 2.0, BEAM + px(10), px(420), (236, 244, 226), 96)


def tiled(base):
    """Glazed tile from the beam to the floor, with dark grout and grime."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(6)
    d.rectangle(box(0, BEAM, W, PLINTH), fill=GROUT)
    size = px(21)
    row = 0
    y = BEAM
    while y < PLINTH:
        x = -size // 2 if row % 2 else 0
        while x < W:
            c = tint(mix(TILE, rnd.choice((TILE_L, TILE_D, (118, 132, 124), (90, 104, 98))),
                         rnd.uniform(0.06, 0.30)), rnd, 0.05)
            d.rectangle(box(x + px(1.5), y + px(1.5), x + size - px(1.5), y + size - px(1.5)),
                        fill=c)
            # the glaze catches the light along the top of every tile
            d.line([(x + px(2), y + px(2)), (x + size - px(2), y + px(2))],
                   fill=mix(c, (226, 236, 228), 0.30), width=max(1, int(px(0.7))))
            d.line([(x + px(2), y + size - px(2)), (x + size - px(2), y + size - px(2))],
                   fill=mix(c, (30, 36, 32), 0.45), width=max(1, int(px(0.7))))
            x += size
        y += size
        row += 1
    # damp and fish slime down the tiles, and grime at the foot
    for k in range(26):
        sx = rnd.uniform(0, W)
        sh = rnd.uniform(px(60), px(320))
        for i in range(int(sh)):
            a = int(60 * (1 - i / sh))
            d.line([(sx, BEAM + i), (sx + px(1), BEAM + i)],
                   fill=mix(TILE, (20, 30, 26), a / 255.0), width=max(1, int(px(2.0))))
    for i in range(px(22)):
        a = int(110 * (1 - i / float(px(22))) ** 1.4)
        d.line([(0, PLINTH - i), (W, PLINTH - i)], fill=(22, 28, 24, a))


def vent(base, x0, x1):
    """A vent high in the wall, with the daylight coming green through it."""
    d = ImageDraw.Draw(base)
    y0, y1 = VENT_Y
    d.rectangle(box(x0 - px(8), y0 - px(8), x1 + px(8), y1 + px(8)), fill=(40, 46, 42))
    for i in range(int(y1 - y0)):
        tt = i / max(1.0, y1 - y0)
        d.line([(x0, y0 + i), (x1, y0 + i)],
               fill=mix(mix(GREEN_LIGHT, (240, 250, 240), 0.35),
                        mix(GREEN_LIGHT, (86, 128, 110), 0.5), tt))
    # the louvres, angled, and the light leaking between them
    n = 7
    for k in range(n):
        sy = y0 + (y1 - y0) * (k + 0.5) / n
        d.rectangle(box(x0, sy - px(2), x1, sy + px(3)), fill=(96, 100, 92))
        d.line([(x0, sy - px(2)), (x1, sy - px(2))], fill=(150, 154, 144),
               width=max(1, int(px(0.8))))
    d.rectangle(box(x0, y0, x1, y1), outline=(120, 124, 114), width=max(2, int(px(2.0))))
    lamp((x0 + x1) / 2.0, (y0 + y1) / 2.0, (x1 - x0) * 1.4, (150, 220, 186), 74)
    lamp((x0 + x1) / 2.0, FLOOR_Y + px(30), (x1 - x0) * 1.0, (140, 214, 180), 34)


def pipes(base):
    """Rusty iron pipework down the tiles: runs, flanges, a valve."""
    d = ImageDraw.Draw(base)
    x0, x1 = PIPES
    top, bottom = BEAM + px(4), PLINTH
    # two vertical runs
    for cx, wdt in ((x0, px(20)), (x1, px(15))):
        d.rectangle(box(cx - wdt, top, cx + wdt, bottom), fill=RUST_D)
        for i in range(int(wdt * 2)):
            tt = i / float(wdt * 2)
            # a real highlight and shadow across the pipe, so it is round and
            # not a brown plank
            if tt < 0.34:
                col = mix((176, 116, 70), RUST, tt / 0.34)
            else:
                col = mix(RUST, (44, 24, 12), (tt - 0.34) / 0.66)
            d.line([(cx - wdt + i, top), (cx - wdt + i, bottom)], fill=col)
        # flanges every so often
        for y in range(int(top) + int(px(50)), int(bottom), int(px(160))):
            d.rectangle(box(cx - wdt - px(3), y, cx + wdt + px(3), y + px(8)), fill=(96, 58, 34))
            d.line([(cx - wdt - px(3), y), (cx + wdt + px(3), y)], fill=(178, 124, 76),
                   width=max(1, int(px(1.0))))
            d.line([(cx - wdt - px(3), y + px(8)), (cx + wdt + px(3), y + px(8))],
                   fill=(46, 26, 14), width=max(1, int(px(1.0))))
    # a horizontal run joining them, with a valve wheel, up where the wall is
    hy = BEAM + px(58)
    d.rectangle(box(x0 - px(20), hy, x1 + px(20), hy + px(16)), fill=(104, 60, 34))
    for i in range(int(px(16))):
        tt = i / float(px(16))
        col = mix((176, 116, 70), (48, 26, 14), tt / 0.9)
        d.line([(x0 - px(20), hy + i), (x1 + px(20), hy + i)], fill=col)
    d.line([(x0 - px(20), hy), (x1 + px(20), hy)], fill=(192, 136, 84),
           width=max(2, int(px(1.8))))
    vx, vy = (x0 + x1) / 2.0, hy + px(8)
    d.ellipse(box(vx - px(16), vy - px(16), vx + px(16), vy + px(16)),
              outline=(126, 112, 90), width=max(3, int(px(2.6))))
    for k in range(3):
        a = math.radians(k * 60)
        d.line([(vx + math.cos(a) * px(15), vy + math.sin(a) * px(15)),
                (vx - math.cos(a) * px(15), vy - math.sin(a) * px(15))],
               fill=(126, 112, 90), width=max(2, int(px(2.0))))
    d.ellipse(box(vx - px(4), vy - px(4), vx + px(4), vy + px(4)), fill=(96, 88, 72))
    # rust bleeding down the tiles, and condensation
    rnd = random.Random(8)
    for k in range(10):
        sx = rnd.uniform(x0 - px(30), x1 + px(30))
        for i in range(int(px(70))):
            a = int(70 * (1 - i / float(px(70))))
            d.line([(sx, bottom - px(70) + i), (sx, bottom - px(70) + i)],
                   fill=mix(RUST, (40, 26, 16), a / 255.0), width=max(1, int(px(2.0))))


def steel_door(base, x0, x1):
    """A riveted steel door in the tiles, with its handle and a lit gap."""
    d = ImageDraw.Draw(base)
    top = BEAM + px(6)
    d.rectangle(box(x0 - px(12), top - px(12), x1 + px(12), PLINTH), fill=(54, 58, 54))
    d.rectangle(box(x0, top, x1, PLINTH), fill=STEEL_D)
    for i in range(int(x1 - x0)):                       # the brushed face
        d.line([(x0 + i, top), (x0 + i, PLINTH)],
               fill=mix(STEEL_D, STEEL, 0.15 + 0.45 * abs((i / (x1 - x0)) - 0.35)))
    # rivets round the edge, and a kick plate
    for k in range(9):
        ry = top + (PLINTH - top) * (k + 0.5) / 9.0
        for rx in (x0 + px(10), x1 - px(10)):
            d.ellipse(box(rx - px(3), ry - px(3), rx + px(3), ry + px(3)),
                      fill=mix(STEEL_L, (170, 176, 170), 0.3))
    d.rectangle(box(x0, PLINTH - px(30), x1, PLINTH - px(14)), fill=mix(STEEL_D, (60, 64, 60), 0.4))
    d.line([(x0, PLINTH - px(30)), (x1, PLINTH - px(30))], fill=STEEL,
           width=max(1, int(px(1.0))))
    # the handle, and the lit gap under the door
    d.rectangle(box(x1 - px(46), top + (PLINTH - top) * 0.46, x1 - px(14),
                    top + (PLINTH - top) * 0.46 + px(9)), fill=(58, 62, 58))
    d.line([(x1 - px(46), top + (PLINTH - top) * 0.46), (x1 - px(14), top + (PLINTH - top) * 0.46)],
           fill=STEEL_L, width=max(1, int(px(1.2))))
    d.rectangle(box(x0, PLINTH, x1, PLINTH + px(4)), fill=(58, 74, 64))
    # rust washes and streaks on the door
    rnd = random.Random(12)
    for k in range(8):
        sx = rnd.uniform(x0, x1)
        for i in range(int(px(90))):
            a = int(90 * (1 - i / float(px(90))))
            d.line([(sx, top + (PLINTH - top) * 0.2 + i), (sx, top + (PLINTH - top) * 0.2 + i)],
                   fill=mix(RUST, (30, 30, 26), a / 255.0), width=max(1, int(px(2.4))))
    d.rectangle(box(x0, top, x1, PLINTH), outline=(74, 78, 74), width=max(2, int(px(2.0))))
    lamp((x0 + x1) / 2.0, (top + PLINTH) / 2.0, px(200), (170, 190, 186), 30)


def bench(base, x0, x1):
    """A stainless bench against the tiles, with a board and a knife on it."""
    d = ImageDraw.Draw(base)
    top = px(168)
    # legs, then the top
    for lx in (x0 + px(16), x1 - px(26)):
        d.rectangle(box(lx, top + px(10), lx + px(10), PLINTH), fill=STEEL_D)
        d.line([(lx, top + px(10)), (lx, PLINTH)], fill=STEEL, width=max(1, int(px(1.0))))
    d.rectangle(box(x0, top, x1, top + px(12)), fill=STEEL)
    d.line([(x0, top), (x1, top)], fill=STEEL_L, width=max(2, int(px(2.0))))
    d.line([(x0, top + px(12)), (x1, top + px(12))], fill=(70, 74, 70),
           width=max(2, int(px(1.6))))
    # a shelf under it
    d.rectangle(box(x0 + px(10), top + px(40), x1 - px(10), top + px(46)), fill=STEEL_D)
    # a wooden board, and the knife left on it
    bx0, bx1 = x0 + (x1 - x0) * 0.12, x0 + (x1 - x0) * 0.62
    d.rectangle(box(bx0, top - px(9), bx1, top), fill=mix((150, 116, 76), (110, 82, 52), 0.3))
    d.line([(bx0, top - px(9)), (bx1, top - px(9))], fill=(196, 160, 112),
           width=max(1, int(px(1.2))))
    kx = bx0 + (bx1 - bx0) * 0.6
    d.polygon([(kx, top - px(6)), (kx + px(48), top - px(12)), (kx + px(52), top - px(8)),
               (kx + px(4), top - px(3))], fill=STEEL_L)
    d.rectangle(box(kx - px(18), top - px(8), kx, top - px(3)), fill=(48, 40, 34))
    # a hose coiled at one end
    for k in range(3):
        d.arc(box(x1 - px(70) - k * px(4), top - px(22) + k * px(4),
                  x1 - px(10) + k * px(4), top - px(2) + k * px(4)), 0, 360,
              fill=(56, 62, 58), width=max(2, int(px(2.2))))
    lamp((x0 + x1) / 2.0, top - px(6), px(220), (230, 240, 232), 48)


def fish_pile(base, cx):
    """The catch: a red sheet with the fish heaped on it, ice round the edge."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(23)
    w, h = px(230), px(74)
    cy = PLINTH - px(18)
    # the sheet, spread and creased
    d.ellipse(box(cx - w, cy - h * 0.5, cx + w, cy + h), fill=mix(TARP, (110, 28, 24), 0.35))
    for k in range(5):
        a = rnd.uniform(0, math.pi)
        d.line([(cx + math.cos(a) * w * 0.2, cy + math.sin(a) * h * 0.2),
                (cx + math.cos(a) * w * 0.95, cy + math.sin(a) * h * 0.9)],
               fill=mix(TARP, (190, 76, 60), 0.35), width=max(1, int(px(2.0))))
    # the heap: dark under-shadow, then the fish laid over it
    d.ellipse(box(cx - w * 0.78, cy - px(46), cx + w * 0.78, cy + px(30)),
              fill=mix(SILVER_D, (40, 44, 44), 0.5))
    # the fish themselves: rounded bodies laid across each other, each with its
    # tail, a bright back and a dark back line. Slivers read as debris, so every
    # body is a twelve-sided oval rather than a quad.
    for i in range(210):
        a = rnd.uniform(0, math.pi * 2)
        r = rnd.uniform(0, 1) ** 0.55
        fx = cx + math.cos(a) * w * 0.66 * r
        fy = cy - px(10) + math.sin(a) * h * 0.56 * r - px(14) * (1 - r)
        fl = rnd.uniform(px(18), px(27))
        fh = rnd.uniform(px(8), px(11))
        rot = rnd.uniform(-0.55, 0.55)
        col = mix(SILVER, SILVER_D, rnd.uniform(0.0, 0.55))
        cs, sn = math.cos(rot), math.sin(rot)

        def place(lx, ly):
            return (fx + lx * cs - ly * sn, fy + lx * sn + ly * cs)

        body = [place(math.cos(t) * fl * 0.5, math.sin(t) * fh * 0.5)
                for t in (k * math.pi / 6.0 for k in range(12))]
        d.polygon(body, fill=col)
        # the tail, fanned behind the body
        d.polygon([place(-fl * 0.46, 0),
                   place(-fl * 0.66, -fh * 0.44),
                   place(-fl * 0.60, 0),
                   place(-fl * 0.66, fh * 0.44)],
                  fill=mix(col, (66, 74, 80), 0.40))
        # the back: a dark line along it and a highlight under that
        d.line([place(-fl * 0.34, -fh * 0.26), place(fl * 0.30, -fh * 0.26)],
               fill=mix(col, (48, 56, 62), 0.55), width=max(1, int(px(1.4))))
        d.line([place(-fl * 0.30, -fh * 0.12), place(fl * 0.26, -fh * 0.12)],
               fill=mix(col, (246, 250, 252), 0.55), width=max(1, int(px(1.6))))
        d.line([place(-fl * 0.26, fh * 0.22), place(fl * 0.22, fh * 0.22)],
               fill=mix(col, (70, 78, 84), 0.35), width=max(1, int(px(1.0))))
        # the eye
        d.ellipse(box(fx + (fl * 0.30) * cs - px(2), fy + (fl * 0.30) * sn - px(2),
                      fx + (fl * 0.30) * cs + px(2), fy + (fl * 0.30) * sn + px(2)),
                  fill=(40, 46, 50))
    # ice chips and the melt water round the sheet
    for k in range(18):
        a = rnd.uniform(0, math.pi * 2)
        ix = cx + math.cos(a) * w * rnd.uniform(0.85, 1.25)
        iy = cy + math.sin(a) * h * rnd.uniform(0.55, 1.2)
        s = rnd.uniform(px(2), px(4))
        d.polygon([(ix, iy - s), (ix + s, iy), (ix, iy + s), (ix - s, iy)], fill=ICE)
    d.ellipse(box(cx - w * 1.05, cy + px(20), cx + w * 1.05, cy + px(54)),
              fill=mix(WATER, BLOOD, 0.35))
    lamp(cx, cy - px(20), px(300), (222, 238, 232), 54)


def bucket(base, cx):
    """A steel bucket stood against the tiles."""
    d = ImageDraw.Draw(base)
    top = PLINTH - px(44)
    d.polygon([(cx - px(20), top), (cx + px(20), top),
               (cx + px(16), PLINTH), (cx - px(16), PLINTH)], fill=STEEL_D)
    d.ellipse(box(cx - px(20), top - px(7), cx + px(20), top + px(7)),
              fill=mix(WATER, (40, 50, 46), 0.3))
    d.ellipse(box(cx - px(20), top - px(7), cx + px(20), top + px(7)),
              outline=STEEL_L, width=max(1, int(px(1.4))))
    d.arc(box(cx - px(19), top - px(24), cx + px(19), top + px(3)), 190, 350,
          fill=STEEL, width=max(1, int(px(1.6))))


# ------------------------------------------------------------------ the floor
def floor(base):
    """Wet floor tile: grout, water, blood, ice, and the light lying in it."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(31)
    d.rectangle(box(0, FLOOR_Y, W, H), fill=GROUT)
    # the tiles get longer toward the viewer, like a floor should
    rows = [FLOOR_Y, FLOOR_Y + px(22), FLOOR_Y + px(48), FLOOR_Y + px(80),
            FLOOR_Y + px(118), H]
    row = 0
    for i in range(len(rows) - 1):
        y0, y1 = rows[i], rows[i + 1]
        tw = px(42) + i * px(6)
        x = -tw // 2 if row % 2 else 0
        while x < W:
            c = tint(mix(FLOOR_T, rnd.choice((TILE_L, TILE_D, (108, 118, 110))),
                         rnd.uniform(0.05, 0.25)), rnd, 0.05)
            d.rectangle(box(x + px(1), y0 + px(1), x + tw - px(1), y1 - px(1)), fill=c)
            d.line([(x + px(1), y0 + px(1)), (x + tw - px(1), y0 + px(1))],
                   fill=mix(c, (196, 208, 200), 0.22), width=max(1, int(px(0.6))))
            d.line([(x + px(1), y1 - px(1)), (x + tw - px(1), y1 - px(1))],
                   fill=mix(c, (24, 30, 26), 0.42), width=max(1, int(px(0.7))))
            x += tw
        row += 1

    # the wall's shadow, and water standing on the tile
    for i in range(px(18)):
        a = int(84 * (1 - i / float(px(18))) ** 1.6)
        d.line([(0, FLOOR_Y + i), (W, FLOOR_Y + i)], fill=(14, 18, 16, a))
    puddle = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(puddle)
    for cx0, cy0, w, h in ((px(300), FLOOR_Y + px(70), px(360), px(44)),
                           (px(820), FLOOR_Y + px(100), px(520), px(56)),
                           (px(1300), FLOOR_Y + px(60), px(300), px(36)),
                           (px(1620), FLOOR_Y + px(96), px(340), px(46))):
        pd.ellipse(box(cx0 - w / 2.0, cy0 - h / 2.0, cx0 + w / 2.0, cy0 + h / 2.0),
                   fill=(46, 66, 60, 140))
    base.alpha_composite(puddle.filter(ImageFilter.GaussianBlur(px(10))))
    # blood running from under the sheet
    stain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stain)
    for k in range(5):
        sx = FISH_CX + rnd.uniform(-px(220), px(220))
        sy = FLOOR_Y + rnd.uniform(px(6), px(60))
        sd.ellipse(box(sx - px(70), sy - px(12), sx + px(70), sy + px(22)),
                   fill=BLOOD + (70,))
    base.alpha_composite(stain.filter(ImageFilter.GaussianBlur(px(16))))

    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    for cx0, col, wdt, a in ((CX, (216, 238, 228), px(300), 46),
                             ((VENT[0] + VENT[1]) / 2.0, (150, 220, 186), px(170), 40),
                             ((DOOR[0] + DOOR[1]) / 2.0, (180, 196, 190), px(140), 28),
                             (FISH_CX, (206, 130, 118), px(360), 30)):
        rd.polygon([(cx0 - wdt / 2.0, FLOOR_Y + px(4)), (cx0 + wdt / 2.0, FLOOR_Y + px(4)),
                    (cx0 + wdt * 1.25, H), (cx0 - wdt * 1.25, H)], fill=col + (a,))
    base.alpha_composite(refl.filter(ImageFilter.GaussianBlur(px(26))))

    # ice and scales scattered on the tiles, and the drain
    for k in range(16):
        ix = rnd.uniform(0, W)
        iy = rnd.uniform(FLOOR_Y + px(10), H - px(8))
        s = rnd.uniform(px(2), px(4))
        d.polygon([(ix, iy - s), (ix + s * 0.8, iy), (ix, iy + s), (ix - s * 0.8, iy)],
                  fill=mix(ICE, FLOOR_T, rnd.uniform(0.20, 0.55)))
    dx = DRAIN
    d.rectangle(box(dx - px(46), FLOOR_Y + px(40), dx + px(46), FLOOR_Y + px(58)),
                fill=(34, 38, 34))
    for k in range(9):
        sx = dx - px(40) + k * px(10)
        d.line([(sx, FLOOR_Y + px(42)), (sx, FLOOR_Y + px(56))], fill=(96, 102, 96),
               width=max(1, int(px(2.0))))
    d.rectangle(box(dx - px(46), FLOOR_Y + px(40), dx + px(46), FLOOR_Y + px(58)),
                outline=(70, 76, 70), width=max(1, int(px(1.0))))


def foreground():
    """The near plane: the dark at the bottom, and cold vapour."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(97)
    for i in range(px(38)):
        a = int(150 * (1 - i / float(px(38))) ** 1.6)
        d.line([(0, H - i), (W, H - i)], fill=(8, 9, 8, a))
    for k in range(4):
        sx = rnd.uniform(0, W)
        sy = rnd.uniform(FLOOR_Y - px(30), H)
        for j in range(5):
            rr = px(34) + j * px(16)
            d.ellipse(box(sx - rr, sy - rr * 0.5, sx + rr, sy + rr * 0.5),
                      fill=(220, 232, 226, 10))
    for _ in range(90):
        x = rnd.uniform(0, W)
        y = rnd.uniform(px(60), H)
        r = rnd.uniform(px(0.9), px(2.2))
        d.ellipse(box(x - r, y - r, x + r, y + r),
                  fill=(226, 240, 232, rnd.randint(14, 46)))
    return fg.filter(ImageFilter.GaussianBlur(px(3.0)))


# ------------------------------------------------------------------- the arena
def paint():
    LIGHTS.clear()
    base = hd.blank([(0, (14, 16, 14)), (CEIL, (26, 30, 26)),
                     (px(140), (44, 52, 46)), (FLOOR_Y, (48, 56, 50)),
                     (H, (26, 32, 28))])

    ceiling(base)
    tiled(base)

    vent(base, VENT[0], VENT[1])
    pipes(base)
    steel_door(base, DOOR[0], DOOR[1])
    fish_pile(base, FISH_CX)
    bench(base, BENCH[0], BENCH[1])
    bucket(base, px(1240))

    floor(base)

    base = hd.shade(base, [(hd.light(cx, cy, r, col, int(peak * 0.82)),
                            max(8, int(r * 0.30)), 1.05)
                           for cx, cy, r, col, peak in LIGHTS])
    base = art.vignette(base, 0.48)
    base = art.grain(base, 3, seed=43)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


def main():
    hd.STAGES["fish_market"] = ("Fish Market", paint)
    hd.build("fish_market")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
