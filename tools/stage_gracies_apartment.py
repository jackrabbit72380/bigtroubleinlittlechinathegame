"""Gracie's Apartment: the living room she never gets to tidy.

Painted from the plan reference: a warm plaster wall with a picture rail, a
window with venetian blinds and a plant on the sill, a bookshelf of paperbacks,
framed pictures, a cream sofa with its cushions and a throw left over the arm,
the television on its wooden stand, and the kitchen at the far end with its wall
cabinets, counter, sink and kettle. The floor is the tan carpet, with the round
red rug lying on it.

A stage is seen across the play plane, so the apartment is painted as a wall
wall-to-wall: the furniture stands against the back of the room with its feet on
the floor line, and the fighters stand on the carpet in front of it. Nothing
comes out into the play plane to stand on anybody's feet.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960, localcoord 1920x1080, camera travel +/-3136.

Run:  python3 tools/stage_gracies_apartment.py     (part of tools/build_all.py)
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

CEIL = px(46)                      # 207: the ceiling line
RAIL = px(58)                      # 261: the picture rail
PLINTH = FLOOR_Y - px(12)          # 846
WINDOW_A = (px(104), px(340))
WIN_TOP, WIN_BOT = px(74), px(146)
SHELF = (px(392), px(516))
SOFA = (px(596), px(884))
TV = (px(920), px(1112))
KITCHEN = (px(1290), px(1770))

WALL = (198, 186, 164)             # warm plaster
WALL_L = (224, 214, 192)
WALL_D = (156, 146, 126)
SKIRT = (142, 124, 102)
CARPET = (190, 172, 140)           # the tan carpet
CARPET_L = (214, 196, 164)
CARPET_D = (152, 136, 108)
RUG = (142, 38, 32)                # the round rug
RUG_L = (186, 66, 48)
WOOD = (116, 78, 46)               # the furniture
WOOD_L = (156, 112, 68)
WOOD_D = (72, 46, 26)
CREAM = (208, 200, 182)            # the sofa
CREAM_D = (172, 164, 146)
TEAL = (74, 112, 100)              # the vinyl chair
BLIND = (214, 208, 190)
GLASSW = (250, 232, 186)           # the light through the window
TVSET = (58, 52, 46)
STEEL = (168, 172, 170)
WARM = (255, 202, 142)

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
    """The line where the ceiling meets the wall, and its shadow."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, 0, W, CEIL), fill=(120, 112, 96))
    d.rectangle(box(0, CEIL - px(6), W, CEIL), fill=(150, 140, 120))
    d.line([(0, CEIL - px(6)), (W, CEIL - px(6))], fill=(178, 168, 148),
           width=max(1, int(px(1.0))))
    d.line([(0, CEIL), (W, CEIL)], fill=(64, 58, 50), width=max(2, int(px(1.4))))
    for i in range(px(18)):
        a = int(104 * (1 - i / float(px(18))))
        d.line([(0, CEIL + i), (W, CEIL + i)], fill=(40, 36, 30, a))


def wall(base):
    """Warm plaster, a picture rail, and the grime that gathers at the foot."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, CEIL, W, PLINTH), fill=WALL)
    rnd = random.Random(9)
    for i in range(240):
        x = rnd.uniform(0, W)
        y = rnd.uniform(CEIL, PLINTH)
        d.ellipse(box(x, y, x + rnd.uniform(px(50), px(200)), y + rnd.uniform(px(20), px(70))),
                  fill=mix(WALL, rnd.choice((WALL_L, WALL_D, (212, 202, 178))),
                           rnd.uniform(0.05, 0.16)))
    # the picture rail, and the moulding under it
    d.rectangle(box(0, RAIL, W, RAIL + px(7)), fill=mix(WALL, WALL_L, 0.35))
    d.line([(0, RAIL), (W, RAIL)], fill=(228, 220, 198), width=max(1, int(px(1.0))))
    d.line([(0, RAIL + px(7)), (W, RAIL + px(7))], fill=mix(WALL, WALL_D, 0.5),
           width=max(1, int(px(0.9))))
    for i in range(px(12)):
        a = int(52 * (1 - i / float(px(12))))
        d.line([(0, RAIL + px(7) + i), (W, RAIL + px(7) + i)], fill=(60, 54, 44, a))
    # the skirting
    d.rectangle(box(0, PLINTH, W, FLOOR_Y), fill=SKIRT)
    d.line([(0, PLINTH), (W, PLINTH)], fill=mix(SKIRT, (200, 184, 156), 0.4),
           width=max(1, int(px(1.0))))
    d.line([(0, FLOOR_Y - px(2)), (W, FLOOR_Y - px(2))], fill=(40, 32, 24),
           width=max(2, int(px(1.2))))


def window(base, x0, x1):
    """A window with venetian blinds, and the daylight coming round them."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(x0 - px(10), WIN_TOP - px(10), x1 + px(10), WIN_BOT + px(10)),
                fill=(228, 222, 206))
    # the glass, and a pale block of buildings beyond it
    for i in range(int(WIN_BOT - WIN_TOP)):
        tt = i / max(1.0, WIN_BOT - WIN_TOP)
        d.line([(x0, WIN_TOP + i), (x1, WIN_TOP + i)],
               fill=mix((255, 246, 216), (216, 200, 162), tt))
    d.rectangle(box(x0, WIN_TOP + (WIN_BOT - WIN_TOP) * 0.55, x1, WIN_BOT),
                fill=mix((206, 190, 156), (176, 158, 126), 0.4))
    # the blinds: slats, with the light between them
    slat = px(7)
    for y in range(int(WIN_TOP) + int(px(4)), int(WIN_BOT) - int(px(2)), int(slat)):
        d.rectangle(box(x0 + px(2), y, x1 - px(2), y + px(5)), fill=BLIND)
        d.line([(x0 + px(2), y), (x1 - px(2), y)], fill=(236, 232, 216),
               width=max(1, int(px(0.8))))
        d.line([(x0 + px(2), y + px(5)), (x1 - px(2), y + px(5))],
               fill=mix(BLIND, (140, 132, 112), 0.55), width=max(1, int(px(0.9))))
    for k in range(2):                                   # the cords
        cxx = x0 + (x1 - x0) * (0.2 + 0.6 * k)
        d.line([(cxx, WIN_TOP + px(2)), (cxx, WIN_BOT)], fill=(150, 142, 120),
               width=max(1, int(px(1.2))))
    # the frame, the sill, and a plant stood on it
    d.rectangle(box(x0, WIN_TOP, x1, WIN_BOT), outline=(232, 226, 208),
                width=max(3, int(px(3.0))))
    d.rectangle(box(x0 - px(14), WIN_BOT, x1 + px(14), WIN_BOT + px(10)),
                fill=mix((216, 208, 190), (176, 168, 150), 0.4))
    d.line([(x0 - px(14), WIN_BOT), (x1 + px(14), WIN_BOT)], fill=(250, 246, 232),
           width=max(1, int(px(1.2))))
    # a pot with a trailing plant on the sill
    px_ = x0 + (x1 - x0) * 0.78
    d.polygon([(px_ - px(12), WIN_BOT), (px_ + px(12), WIN_BOT),
               (px_ + px(9), WIN_BOT - px(16)), (px_ - px(9), WIN_BOT - px(16))],
              fill=mix((176, 96, 62), (120, 60, 38), 0.3))
    rnd = random.Random(4)
    for k in range(11):
        ang = rnd.uniform(-2.6, -0.5)
        ln = rnd.uniform(px(14), px(30))
        d.line([(px_, WIN_BOT - px(16)),
                (px_ + math.cos(ang) * ln, WIN_BOT - px(16) + math.sin(ang) * ln)],
               fill=mix((86, 132, 78), (58, 96, 54), rnd.uniform(0.0, 0.6)),
               width=max(1, int(px(1.6))))
    lamp((x0 + x1) / 2.0, (WIN_TOP + WIN_BOT) / 2.0, (x1 - x0) * 0.85, (255, 226, 174), 50)


def bookshelf(base, x0, x1):
    """A low bookshelf, paperbacks packed along it."""
    d = ImageDraw.Draw(base)
    top = px(120)
    d.rectangle(box(x0, top, x1, PLINTH), fill=WOOD)
    d.rectangle(box(x0 + px(4), top + px(4), x1 - px(4), PLINTH - px(4)), fill=WOOD_D)
    rnd = random.Random(13)
    for shelf in range(3):
        sy = top + px(10) + shelf * px(24)
        d.rectangle(box(x0 + px(4), sy + px(20), x1 - px(4), sy + px(24)), fill=WOOD)
        d.line([(x0 + px(4), sy + px(20)), (x1 - px(4), sy + px(20))],
               fill=mix(WOOD, WOOD_L, 0.5), width=max(1, int(px(0.9))))
        bx = x0 + px(8)
        while bx < x1 - px(12):
            bw = rnd.uniform(px(5), px(9))
            bh = rnd.uniform(px(13), px(19))
            c = rnd.choice(((150, 60, 48), (70, 92, 74), (186, 156, 96), (96, 76, 104),
                            (120, 108, 92), (170, 120, 70)))
            d.rectangle(box(bx, sy + px(20) - bh, bx + bw, sy + px(20)),
                        fill=mix(c, (60, 44, 32), 0.15))
            d.line([(bx, sy + px(21) - bh), (bx + bw, sy + px(21) - bh)],
                   fill=mix(c, (236, 220, 190), 0.35), width=max(1, int(px(0.6))))
            bx += bw + px(1)
    d.line([(x0, top), (x1, top)], fill=mix(WOOD, WOOD_L, 0.6), width=max(2, int(px(1.8))))
    lamp((x0 + x1) / 2.0, top + px(30), px(150), (255, 200, 140), 34)


def picture(base, x0, x1, y0, y1, seed):
    """A framed picture on the plaster."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(x0 - px(5), y0 - px(5), x1 + px(5), y1 + px(5)), fill=(56, 44, 32))
    d.rectangle(box(x0, y0, x1, y1), fill=(186, 172, 148))
    rnd = random.Random(seed)
    # a simple landscape inside it
    for i in range(int(y1 - y0)):
        tt = i / max(1.0, y1 - y0)
        d.line([(x0 + px(3), y0 + i), (x1 - px(3), y0 + i)],
               fill=mix((186, 200, 196), (120, 132, 116), tt ** 0.7))
    d.polygon([(x0 + px(4), y1 - px(15)), (x0 + (x1 - x0) * 0.4, y0 + (y1 - y0) * 0.35),
               (x0 + (x1 - x0) * 0.75, y1 - px(15))],
              fill=mix((96, 116, 96), (64, 82, 66), rnd.uniform(0.2, 0.6)))
    d.line([(x0 + px(3), y1 - px(14)), (x1 - px(3), y1 - px(14))],
           fill=(92, 106, 84), width=max(2, int(px(2.0))))
    d.rectangle(box(x0, y0, x1, y1), outline=(232, 224, 200), width=max(1, int(px(1.2))))


def sofa(base, x0, x1):
    """The cream sofa: cushions, arms, and a throw left over one end."""
    d = ImageDraw.Draw(base)
    seat = px(158)
    top = px(112)
    d.rectangle(box(x0, top, x1, seat + px(16)), fill=CREAM)
    # the back, with a dark edge so the sofa keeps its shape against the wall
    d.rounded_rectangle(box(x0 - px(6), top - px(6), x1 + px(6), seat - px(24)),
                        radius=max(2, int(px(12))), fill=mix(CREAM, CREAM_D, 0.34))
    d.rounded_rectangle(box(x0 - px(6), top - px(6), x1 + px(6), seat - px(24)),
                        radius=max(2, int(px(12))), outline=mix(CREAM_D, (118, 108, 90), 0.45),
                        width=max(2, int(px(1.6))))
    d.line([(x0 - px(6), top - px(6)), (x1 + px(6), top - px(6))],
           fill=(244, 238, 220), width=max(1, int(px(1.2))))
    d.line([(x0 - px(6), seat - px(24)), (x1 + px(6), seat - px(24))],
           fill=mix(CREAM_D, (120, 110, 92), 0.4), width=max(2, int(px(1.6))))
    # the two seat cushions, and their seam
    for k in range(2):
        cx0 = x0 + (x1 - x0) * k / 2.0 + px(6)
        cx1 = x0 + (x1 - x0) * (k + 1) / 2.0 - px(6)
        d.rounded_rectangle(box(cx0, seat - px(14), cx1, seat + px(12)),
                            radius=max(2, int(px(8))), fill=mix(CREAM, CREAM_D, 0.32))
        d.line([(cx0 + px(4), seat - px(12)), (cx1 - px(4), seat - px(12))],
               fill=(240, 234, 218), width=max(1, int(px(1.0))))
    # the arms
    for ax in (x0 - px(12), x1 - px(4)):
        d.rounded_rectangle(box(ax, seat - px(26), ax + px(16), seat + px(20)),
                            radius=max(2, int(px(8))), fill=mix(CREAM, CREAM_D, 0.46))
        d.rounded_rectangle(box(ax, seat - px(26), ax + px(16), seat + px(20)),
                            radius=max(2, int(px(8))), outline=mix(CREAM_D, (112, 102, 86), 0.45),
                            width=max(1, int(px(1.2))))
    # the base down to the floor line
    d.rectangle(box(x0 - px(8), seat + px(16), x1 + px(8), PLINTH), fill=mix(CREAM_D, (132, 122, 104), 0.30))
    d.rectangle(box(x0 - px(8), seat + px(16), x1 + px(8), PLINTH),
                outline=mix(CREAM_D, (110, 100, 84), 0.5), width=max(2, int(px(1.4))))
    d.line([(x0 - px(8), PLINTH), (x1 + px(8), PLINTH)], fill=(76, 66, 52),
           width=max(2, int(px(1.4))))
    # a throw over the left arm, and a cushion knocked askew
    d.polygon([(x0 - px(16), seat - px(30)), (x0 + px(30), seat - px(36)),
               (x0 + px(52), seat + px(4)), (x0 - px(10), seat + px(10))],
              fill=mix(TEAL, (60, 88, 78), 0.25))
    d.line([(x0 - px(16), seat - px(30)), (x0 + px(30), seat - px(36))],
           fill=mix(TEAL, (150, 190, 176), 0.45), width=max(1, int(px(1.2))))
    d.rounded_rectangle(box(x1 - px(88), seat - px(44), x1 - px(30), seat - px(6)),
                        radius=max(2, int(px(9))), fill=mix((168, 74, 66), (120, 44, 38), 0.3))
    d.line([(x1 - px(88), seat - px(44)), (x1 - px(30), seat - px(44))],
           fill=(206, 128, 112), width=max(1, int(px(1.2))))
    lamp((x0 + x1) / 2.0, seat - px(20), px(240), (255, 208, 156), 52)


def tv_stand(base, x0, x1):
    """The television on its wooden stand, and the glow off its screen."""
    d = ImageDraw.Draw(base)
    top = px(126)
    # the stand
    d.rectangle(box(x0, top, x1, PLINTH), fill=mix(WOOD, WOOD_D, 0.25))
    for k in range(2):
        d.rectangle(box(x0 + px(8) + k * (x1 - x0) * 0.5, top + px(10),
                        x0 + px(8) + k * (x1 - x0) * 0.5 + (x1 - x0) * 0.36, PLINTH - px(10)),
                    outline=mix(WOOD, WOOD_L, 0.4), width=max(1, int(px(1.0))))
    d.line([(x0, top), (x1, top)], fill=mix(WOOD, WOOD_L, 0.6), width=max(2, int(px(1.8))))
    # the set: a squat box with a dark rounded screen
    sx0, sx1 = x0 + (x1 - x0) * 0.14, x1 - (x1 - x0) * 0.14
    sy0, sy1 = px(74), top - px(4)
    d.rectangle(box(sx0, sy0, sx1, sy1), fill=mix(TVSET, (78, 72, 66), 0.35))
    d.rectangle(box(sx0 + px(8), sy0 + px(8), sx1 - px(30), sy1 - px(8)),
                fill=(30, 34, 32))
    d.rectangle(box(sx0 + px(8), sy0 + px(8), sx1 - px(30), sy1 - px(8)),
                fill=None, outline=(92, 96, 92), width=max(1, int(px(1.0))))
    for k in range(3):                                # the screen's sheen
        d.line([(sx0 + px(14) + k * px(14), sy1 - px(12)), (sx0 + px(40) + k * px(14), sy0 + px(12))],
               fill=(74, 86, 84), width=max(2, int(px(3.0))))
    # the dials, and the aerial
    d.ellipse(box(sx1 - px(24), sy0 + px(14), sx1 - px(12), sy0 + px(26)), fill=(120, 116, 104))
    d.ellipse(box(sx1 - px(24), sy0 + px(30), sx1 - px(12), sy0 + px(42)), fill=(120, 116, 104))
    d.line([(sx0 + px(20), sy0), (sx0 - px(6), sy0 - px(30))], fill=(150, 150, 146),
           width=max(2, int(px(2.0))))
    d.line([(sx0 + px(34), sy0), (sx0 + px(58), sy0 - px(24))], fill=(150, 150, 146),
           width=max(2, int(px(2.0))))
    lamp((sx0 + sx1) / 2.0, (sy0 + sy1) / 2.0, px(220), (150, 190, 176), 40)


def kitchen(base, x0, x1):
    """The kitchen end: wall cabinets, a tiled splashback, counter and sink."""
    d = ImageDraw.Draw(base)
    counter = px(150)
    # wall cabinets with glass doors and jars inside
    for k in range(3):
        cx0 = x0 + k * (x1 - x0) / 3.0 + px(6)
        cx1 = x0 + (k + 1) * (x1 - x0) / 3.0 - px(6)
        d.rectangle(box(cx0, px(66), cx1, px(118)), fill=mix(WOOD, WOOD_L, 0.25))
        d.rectangle(box(cx0 + px(5), px(71), cx1 - px(5), px(113)),
                    fill=(156, 162, 148))
        rnd = random.Random(int(cx0))
        jx = cx0 + px(10)
        while jx < cx1 - px(14):
            jw = rnd.uniform(px(9), px(14))
            d.rectangle(box(jx, px(96), jx + jw, px(110)),
                        fill=mix(rnd.choice(((190, 150, 90), (140, 160, 130), (176, 96, 70))),
                                 (240, 234, 216), 0.25))
            d.line([(jx, px(96)), (jx + jw, px(96))], fill=(238, 232, 214),
                   width=max(1, int(px(0.8))))
            jx += jw + px(5)
        d.rectangle(box(cx0, px(66), cx1, px(118)), outline=mix(WOOD, WOOD_D, 0.3),
                    width=max(1, int(px(1.2))))
        d.rectangle(box(cx1 - px(9), px(86), cx1 - px(4), px(100)), fill=STEEL)
    # the tiled splashback
    d.rectangle(box(x0, px(118), x1, counter), fill=(206, 202, 188))
    for gx in range(int(x0), int(x1), int(px(16))):
        d.line([(gx, px(118)), (gx, counter)], fill=(178, 174, 160),
               width=max(1, int(px(0.7))))
    for gy in range(int(px(118)), int(counter), int(px(16))):
        d.line([(x0, gy), (x1, gy)], fill=(178, 174, 160), width=max(1, int(px(0.7))))
    # the counter, with the sink cut into it and the kettle on it
    d.rectangle(box(x0 - px(8), counter, x1 + px(8), counter + px(10)), fill=mix(WOOD, WOOD_L, 0.4))
    d.line([(x0 - px(8), counter), (x1 + px(8), counter)], fill=(248, 240, 216),
           width=max(2, int(px(1.6))))
    d.rectangle(box(x0 - px(8), counter + px(10), x1 + px(8), PLINTH),
                fill=mix(WOOD, WOOD_D, 0.18))
    for k in range(3):
        cx0 = x0 + k * (x1 - x0) / 3.0 + px(8)
        d.rectangle(box(cx0, counter + px(18), cx0 + (x1 - x0) / 3.0 - px(16), PLINTH - px(8)),
                    outline=mix(WOOD, WOOD_L, 0.35), width=max(1, int(px(1.0))))
    # the sink, its tap, and a kettle
    sx = x0 + (x1 - x0) * 0.26
    d.rounded_rectangle(box(sx - px(38), counter + px(2), sx + px(38), counter + px(10)),
                        radius=max(2, int(px(4))), fill=(196, 200, 198))
    d.arc(box(sx - px(16), counter - px(20), sx + px(16), counter + px(4)), 180, 360,
          fill=STEEL, width=max(2, int(px(2.6))))
    d.line([(sx, counter - px(20)), (sx, counter + px(2))], fill=STEEL,
           width=max(2, int(px(2.2))))
    kx = x0 + (x1 - x0) * 0.66
    d.ellipse(box(kx - px(16), counter - px(26), kx + px(16), counter + px(2)),
              fill=mix((190, 196, 194), (140, 148, 146), 0.3))
    d.arc(box(kx - px(14), counter - px(34), kx + px(14), counter - px(14)), 180, 360,
          fill=STEEL, width=max(2, int(px(2.2))))
    d.rectangle(box(kx + px(10), counter - px(20), kx + px(22), counter - px(14)),
                fill=(96, 98, 94))
    lamp((x0 + x1) / 2.0, counter - px(22), px(240), (255, 214, 156), 62)
    lamp((x0 + x1) / 2.0, PLINTH + px(18), px(200), (255, 206, 150), 34)


def plant(base, cx):
    """A potted plant on the floor against the wall."""
    d = ImageDraw.Draw(base)
    d.polygon([(cx - px(20), PLINTH), (cx + px(20), PLINTH),
               (cx + px(15), PLINTH - px(30)), (cx - px(15), PLINTH - px(30))],
              fill=mix((156, 96, 62), (104, 58, 36), 0.3))
    d.ellipse(box(cx - px(20), PLINTH - px(34), cx + px(20), PLINTH - px(26)),
              fill=(60, 44, 30))
    rnd = random.Random(int(cx))
    for k in range(12):
        ang = rnd.uniform(-2.9, -0.25)
        ln = rnd.uniform(px(26), px(54))
        d.line([(cx, PLINTH - px(30)),
                (cx + math.cos(ang) * ln, PLINTH - px(30) + math.sin(ang) * ln)],
               fill=mix((82, 122, 72), (52, 88, 50), rnd.uniform(0.0, 0.6)),
               width=max(1, int(px(2.0))))


# ------------------------------------------------------------------ the floor
def carpet(base):
    """The tan carpet, the round rug, and the room's light lying on it."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(21)
    d.rectangle(box(0, FLOOR_Y, W, H), fill=CARPET)
    for i in range(900):
        x = rnd.uniform(0, W)
        y = rnd.uniform(FLOOR_Y, H)
        d.ellipse(box(x, y, x + rnd.uniform(px(14), px(60)), y + rnd.uniform(px(4), px(16))),
                  fill=mix(CARPET, rnd.choice((CARPET_L, CARPET_D)),
                           rnd.uniform(0.06, 0.20)))
    # the round rug, lying at the far end of the room
    rx, ry = px(1470), FLOOR_Y + px(96)
    rw, rh = px(210), px(84)
    d.ellipse(box(rx - rw, ry - rh, rx + rw, ry + rh), fill=mix(RUG, RUG_L, 0.15))
    for k in range(6):
        t = 1 - k / 7.0
        d.ellipse(box(rx - rw * t, ry - rh * t, rx + rw * t, ry + rh * t),
                  outline=mix(RUG_L, (232, 178, 118), 0.25 + 0.10 * k),
                  width=max(1, int(px(1.6))))
    for k in range(16):                                  # its pattern
        a = k * math.pi / 8.0
        d.line([(rx, ry), (rx + math.cos(a) * rw * 0.8, ry + math.sin(a) * rh * 0.8)],
               fill=mix(RUG_L, (226, 170, 112), 0.4), width=max(1, int(px(1.2))))
    d.ellipse(box(rx - px(34), ry - px(14), rx + px(34), ry + px(14)),
              fill=mix(RUG_L, (238, 190, 130), 0.35))

    # the wall's shadow on the carpet
    for i in range(px(16)):
        a = int(120 * (1 - i / float(px(16))) ** 1.5)
        d.line([(0, FLOOR_Y + i), (W, FLOOR_Y + i)], fill=(40, 30, 20, a))

    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    for cx0, col, wdt, a in (((WINDOW_A[0] + WINDOW_A[1]) / 2.0, (255, 232, 180), px(300), 54),
                             ((SOFA[0] + SOFA[1]) / 2.0, (255, 208, 156), px(260), 34),
                             ((KITCHEN[0] + KITCHEN[1]) / 2.0, (255, 214, 156), px(280), 48)):
        rd.polygon([(cx0 - wdt / 2.0, FLOOR_Y + px(4)), (cx0 + wdt / 2.0, FLOOR_Y + px(4)),
                    (cx0 + wdt * 1.25, H), (cx0 - wdt * 1.25, H)], fill=col + (a,))
    base.alpha_composite(refl.filter(ImageFilter.GaussianBlur(px(26))))

    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.rectangle(box(0, FLOOR_Y, W, H), fill=(240, 220, 180, 14))
    base.alpha_composite(sheen.filter(ImageFilter.GaussianBlur(px(14)))) 


def foreground():
    """The near plane: dust in the light, and the dark at the bottom."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(89)
    for i in range(px(38)):
        a = int(140 * (1 - i / float(px(38))) ** 1.6)
        d.line([(0, H - i), (W, H - i)], fill=(10, 8, 6, a))
    for _ in range(110):
        x = rnd.uniform(0, W)
        y = rnd.uniform(px(50), H)
        r = rnd.uniform(px(0.9), px(2.4))
        d.ellipse(box(x - r, y - r, x + r, y + r),
                  fill=(255, 226, 170, rnd.randint(16, 52)))
    return fg.filter(ImageFilter.GaussianBlur(px(2.0)))


# ------------------------------------------------------------------- the arena
def paint():
    LIGHTS.clear()
    base = hd.blank([(0, (30, 26, 22)), (CEIL, (78, 72, 60)),
                     (px(140), (120, 110, 94)), (FLOOR_Y, (128, 112, 88)),
                     (H, (86, 72, 56))])

    ceiling(base)
    wall(base)

    window(base, WINDOW_A[0], WINDOW_A[1])
    picture(base, px(376), px(432), px(96), px(150), 3)
    bookshelf(base, SHELF[0], SHELF[1])
    plant(base, px(556))
    sofa(base, SOFA[0], SOFA[1])
    picture(base, px(700), px(776), px(80), px(104), 7)
    tv_stand(base, TV[0], TV[1])
    picture(base, px(1146), px(1220), px(86), px(118), 11)
    plant(base, px(1190))
    kitchen(base, KITCHEN[0], KITCHEN[1])

    # the room's own light, so the plaster reads warm instead of muddy
    lamp(px(910), px(130), px(360), (255, 216, 174), 30)
    lamp(px(910), FLOOR_Y + px(80), px(340), (255, 214, 172), 24)

    carpet(base)

    base = hd.shade(base, [(hd.light(cx, cy, r, col, int(peak * 0.82)),
                            max(8, int(r * 0.30)), 1.05)
                           for cx, cy, r, col, peak in LIGHTS])
    base = art.vignette(base, 0.34)
    base = art.grain(base, 3, seed=41)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


def main():
    hd.STAGES["gracies_apartment"] = ("Gracie's Apartment", paint)
    hd.build("gracies_apartment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
