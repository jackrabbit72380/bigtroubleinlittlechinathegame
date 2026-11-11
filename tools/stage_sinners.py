"""The Upside Down: the punishment floor under Lo Pan's palace.

The film's torture rooms are three ideas in one place, and the stage takes all
three:

  * a rusted steel works - riveted plate walls, piers, flues - lit from a slot
    of fire at the foot of the wall, so the light comes UP the wall and every
    shadow falls the wrong way
  * victims hung by the ankles from chains, decaying, still in their rags. They
    are the stage's repeating motif: the rows are as regular as the hallway's
    statues, which is what makes them read as a punishment and not as gore
  * flooded sumps in the floor with the chained dead lying in them, wrists
    hauled out to iron stakes

Light is the whole point of the room and it is deliberately upside down. Every
source in here is low: the wall slot, the furnace mouths, the firelight lying
on the water. Nothing comes from the ceiling except the dark, so the bodies are
lit from below, their shadows run up the wall, and the room reads as a place
where the natural order has been inverted - which is the stage's name.

Two things were worth fixing after the first build of this painter and are
worth not undoing: the plate wall has to stay close in tone (a per-plate random
tint turned 8192 px of wall into a checkerboard), and the fireboxes have to stay
small and hot. Painted big and pale they read as lit windows, and bloom turned
them into paper.

Geometry is in canvas pixels on the shared 8192x1080 canvas; CX and FLOOR_Y are
owned by tools/stages_hd.py. Every prop is placed off STEP constants, so a
clean checkout reproduces the art.

Run:  python3 tools/stage_sinners.py       (part of tools/build_all.py)
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

CEIL = px(20)                                    # 90: underside of the ceiling
SLOT_TOP, SLOT_BOT = FLOOR_Y - px(8), FLOOR_Y - px(1)     # the fire slot
FURNACE_STEP = px(200)                           # 900: one furnace per bay
FURNACE_W, FURNACE_H = px(56), px(74)
HANG_STEP = px(54)                               # 243: one hook per bay
PIER_STEP = FURNACE_STEP * 5                     # every fifth bay is a pier

WALL_TOP = (52, 31, 23)
WALL_LOW = (98, 54, 34)
RUST = (112, 58, 30)
RUST_DK = (38, 23, 18)
IRON = (40, 35, 32)
IRON_LT = (104, 94, 82)
IRON_DK = (18, 15, 14)
SOOT = (12, 10, 10)
FLESH = (70, 58, 48)
BONE = (170, 158, 132)
RAG = (44, 38, 30)
CHAIN = (92, 88, 80)
FIRE = (255, 138, 40)
EMBER = (255, 216, 132)

RIM = []          # light pools collected while painting, screened on at the end


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def clamp(c):
    return tuple(max(0, min(255, int(v))) for v in c)


def grad_down(d, y0, y1, c0, c1, x0=0, x1=W):
    """Vertical gradient between two rows, one line at a time."""
    n = max(1, int(y1 - y0))
    for i in range(n):
        t = i / float(n - 1)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=mix(c0, c1, t))


# --------------------------------------------------------------------- shell
def ceiling(d):
    """Girders, and the black above them: the only thing overhead is the dark."""
    d.rectangle([0, 0, W, CEIL], fill=(9, 8, 8))
    for x in range(0, W, px(120)):
        d.rectangle([x, 0, x + px(12), CEIL + px(8)], fill=(28, 22, 20))
        d.line([(x + px(1), 0), (x + px(1), CEIL + px(8))], fill=(50, 40, 33),
               width=max(1, px(1)))
        d.line([(x + px(11), 0), (x + px(11), CEIL + px(8))], fill=(12, 10, 9),
               width=max(1, px(1.6)))
        for ry in (CEIL * 0.32, CEIL * 0.68):
            for rx in range(int(x + px(4)), int(x + px(10)), int(px(3))):
                d.ellipse([rx - px(0.7), ry - px(0.7), rx + px(0.7), ry + px(0.7)],
                          fill=(70, 58, 48))
    d.rectangle([0, CEIL - px(1), W, CEIL + px(2)], fill=(58, 44, 34))
    d.line([(0, CEIL - px(1)), (W, CEIL - px(1))], fill=(84, 62, 44),
           width=max(1, px(1)))


def rust_wall(base):
    """Riveted plate steel eaten back to oxide: the room's back wall.

    Plates are laid in aligned courses and kept within a narrow tonal band. The
    variation that makes the wall interesting is the weathering painted over it,
    not the plate tint: random per-plate colour turned the wall into tiles.
    """
    rnd = random.Random(19)
    d = ImageDraw.Draw(base)
    grad_down(d, CEIL, FLOOR_Y, WALL_TOP, WALL_LOW)
    d.rectangle([0, CEIL, W, FLOOR_Y], fill=None)

    ph, pw = px(42), px(78)
    for row, y in enumerate(range(int(CEIL), int(FLOOR_Y), ph)):
        # every course a plate, butted edge to edge: seams only, no tint jumps
        for x in range(-pw, W + pw, pw):
            tone = rnd.randint(-7, 7)
            top = clamp(tuple(c + tone - 6 for c in mix(WALL_TOP, WALL_LOW,
                                                        (y - CEIL) / float(FLOOR_Y - CEIL))))
            bot = clamp(tuple(c + tone for c in mix(WALL_TOP, WALL_LOW,
                                                    (y + ph - CEIL) / float(FLOOR_Y - CEIL))))
            for i in range(int(ph)):
                t = i / float(max(1, ph - 1))
                d.line([(x, y + i), (x + pw, y + i)], fill=mix(top, bot, t))
            d.line([(x, y), (x + pw, y)], fill=(30, 18, 14), width=max(1, px(1.3)))
            d.line([(x + pw - px(0.4), y), (x + pw - px(0.4), y + ph)],
                   fill=(26, 16, 12), width=max(1, px(1.1)))
            # rivets along the top seam of every plate: dark pit, lit rim below
            for rx in range(int(x + px(6)), int(x + pw - px(4)), int(px(9))):
                d.ellipse([rx - px(1.0), y + px(2.4), rx + px(1.0), y + px(4.0)],
                          fill=(24, 15, 11))
                d.arc([rx - px(1.0), y + px(2.4), rx + px(1.0), y + px(4.0)],
                      0, 180, fill=(126, 96, 70), width=1)

    # weathering: oxide clouds, streaks running down to the slot, soot above
    stain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stain)
    for _ in range(90):                       # big soft blooms of scale
        x = rnd.randint(-int(px(60)), W)
        y = rnd.randint(int(CEIL), int(FLOOR_Y - px(20)))
        r = rnd.randint(int(px(30)), int(px(120)))
        sd.ellipse([x, y, x + r, y + r * rnd.uniform(0.5, 1.0)],
                   fill=mix((134, 60, 26), (60, 32, 20), rnd.random())
                   + (rnd.randint(10, 26),))
    for _ in range(420):                      # rust bleeding down the plates
        x = rnd.randint(0, W)
        y = rnd.randint(int(CEIL), int(FLOOR_Y - px(40)))
        sd.rectangle([x, y, x + rnd.randint(int(px(2)), int(px(9))),
                      y + rnd.randint(int(px(50)), int(px(300)))],
                     fill=(30, 15, 8, rnd.randint(14, 40)))
    for _ in range(2400):                     # pits and flakes
        x = rnd.randint(0, W)
        y = rnd.randint(int(CEIL), int(FLOOR_Y))
        r = rnd.randint(int(px(1)), int(px(6)))
        sd.ellipse([x, y, x + r, y + r * rnd.uniform(0.4, 0.8)],
                   fill=mix((150, 74, 32), (44, 24, 16), rnd.random())
                   + (rnd.randint(10, 34),))
    for _ in range(600):                      # soot gathering under the ceiling
        x = rnd.randint(0, W)
        y = rnd.randint(int(CEIL), int(CEIL + px(80)))
        r = rnd.randint(int(px(6)), int(px(26)))
        sd.ellipse([x, y, x + r, y + r * 0.65], fill=(8, 7, 7, rnd.randint(16, 44)))
    base.alpha_composite(stain.filter(ImageFilter.GaussianBlur(px(4))))
    d = ImageDraw.Draw(base)
    # a dark band where the wall meets the ceiling, and the slot's shadow line
    for i in range(int(px(40))):
        a = int(120 * (1 - i / float(px(40))) ** 1.5)
        d.line([(0, CEIL + i), (W, CEIL + i)], fill=(6, 5, 5, a))


def buttresses(base):
    """Riveted piers, one every five bays: the wall needs a beat of its own."""
    d = ImageDraw.Draw(base)
    for x in range(-PIER_STEP, W + PIER_STEP, PIER_STEP):
        w = px(16)
        d.rectangle([x - w / 2, CEIL, x + w / 2, FLOOR_Y], fill=(46, 33, 27))
        d.rectangle([x - w / 2, CEIL, x - w / 2 + px(4), FLOOR_Y], fill=(70, 50, 38))
        d.rectangle([x + w / 2 - px(4), CEIL, x + w / 2, FLOOR_Y], fill=(20, 15, 13))
        for y in range(int(CEIL + px(12)), int(FLOOR_Y), int(px(22))):
            d.line([(x - w / 2, y), (x + w / 2, y)], fill=(28, 20, 17),
                   width=max(1, px(1.2)))
            for rx in (x - w * 0.26, x + w * 0.26):
                d.ellipse([rx - px(0.9), y + px(2), rx + px(0.9), y + px(3.8)],
                          fill=(90, 78, 64))
        # brackets at the top, where a chain can be hung
        d.rectangle([x - w * 0.86, CEIL + px(9), x + w * 0.86, CEIL + px(16)],
                    fill=(56, 42, 33))
        d.line([(x - w * 0.86, CEIL + px(16)), (x + w * 0.86, CEIL + px(16))],
               fill=(88, 64, 46), width=max(1, px(1)))


def pipe_runs(base):
    """Two runs of heavy pipe along the wall, with flanges and a valve each."""
    rnd = random.Random(53)
    d = ImageDraw.Draw(base)
    for y, thick in ((px(58), px(9)), (px(96), px(6))):
        d.rectangle([0, y, W, y + thick], fill=(38, 30, 26))
        d.rectangle([0, y, W, y + thick * 0.28], fill=(74, 58, 44))
        d.line([(0, y + thick), (W, y + thick)], fill=(16, 12, 11),
               width=max(1, px(1.4)))
        for x in range(int(px(30)), W, int(px(86))):
            d.rectangle([x, y - px(2.4), x + px(5), y + thick + px(2.4)],
                        fill=(44, 34, 28))
            d.line([(x, y - px(2.4)), (x, y + thick + px(2.4))], fill=(84, 64, 46),
                   width=max(1, px(1)))
        for x in range(int(px(140)), W, int(px(300))):
            r = thick * 0.9
            cy = y + thick * 0.5
            d.ellipse([x - r, cy - r, x + r, cy + r], outline=(66, 52, 40),
                      width=max(2, px(1.6)))
            d.line([(x - r, cy), (x + r, cy)], fill=(80, 62, 46), width=max(1, px(1.6)))
            d.line([(x, cy - r), (x, cy + r)], fill=(80, 62, 46), width=max(1, px(1.6)))
            if rnd.random() < 0.4:            # a hand wheel, sticking up
                d.line([(x, cy - r), (x, cy - r * 2.4)], fill=(58, 46, 36),
                       width=max(1, px(1.6)))
                d.ellipse([x - px(4), cy - r * 2.4 - px(4), x + px(4),
                           cy - r * 2.4 + px(4)], outline=(72, 56, 42),
                          width=max(1, px(1.4)))
    # vertical drops from the pipes down the wall
    for x in range(int(px(90)), W, int(px(430))):
        d.rectangle([x, px(58), x + px(4), px(200)], fill=(34, 27, 23))
        d.line([(x, px(58)), (x, px(200))], fill=(62, 48, 36), width=max(1, px(1)))


def floor_slot(base):
    """The fire slot at the foot of the wall: the room's one real light."""
    d = ImageDraw.Draw(base)
    # recess, with its iron lip above and the grate floor below
    d.rectangle([0, SLOT_TOP - px(4), W, SLOT_BOT + px(2)], fill=(20, 13, 10))
    grad_down(d, SLOT_TOP + px(1), SLOT_BOT, (238, 120, 34), (255, 216, 140),
              0, W)
    # the fire does not burn evenly: brighter pockets along the run
    rnd = random.Random(61)
    x = 0
    while x < W:
        w_ = px(rnd.uniform(60, 200))
        lvl = rnd.uniform(0.2, 1.0)
        if lvl > 0.62:
            d.rectangle([x, SLOT_TOP + px(1), x + w_, SLOT_BOT],
                        fill=clamp(mix((255, 196, 108), (255, 240, 200), lvl - 0.6)))
        x += w_ * 0.8
    # grate bars over it, and the slot's own iron lip
    for x in range(0, W, px(12)):
        d.rectangle([x, SLOT_TOP - px(1), x + px(1.3), SLOT_BOT], fill=(30, 19, 14))
        d.line([(x + px(0.5), SLOT_TOP), (x + px(0.5), SLOT_BOT)],
               fill=(58, 34, 20), width=1)
    # and the same fire thrown down onto the floor in front of it
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    for i in range(int(px(30))):
        t = i / float(px(30))
        wd.line([(0, SLOT_BOT + i), (W, SLOT_BOT + i)],
                fill=(255, 118, 42, int(56 * (1 - t) ** 1.7)))
    base.alpha_composite(wash.filter(ImageFilter.GaussianBlur(px(3))))
    d.rectangle([0, SLOT_TOP - px(6), W, SLOT_TOP - px(1)], fill=(38, 28, 23))
    d.line([(0, SLOT_TOP - px(6)), (W, SLOT_TOP - px(6))], fill=(96, 66, 42),
           width=max(1, px(1.2)))
    d.rectangle([0, SLOT_BOT, W, SLOT_BOT + px(3)], fill=(26, 18, 15))


def slot_spill():
    """Firelight thrown up the wall from the slot, as one screened layer."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    span = px(150)
    for i in range(int(span)):
        y = SLOT_TOP - span + i
        t = i / span
        d.line([(0, y), (W, y)], fill=(255, 118, 44, int(52 * t ** 2.1)))
    for i in range(int(px(12))):
        t = i / float(px(12))
        d.line([(0, SLOT_TOP - i), (W, SLOT_TOP - i)],
               fill=(255, 176, 104, int(96 * (1 - t) ** 1.3)))
    return Image.composite(layer, Image.new("RGBA", (W, H), (0, 0, 0, 0)),
                           layer.getchannel("A"))


# ------------------------------------------------------------------- furnace
def furnace(base, cx, y_base, seed=0):
    """An iron furnace with a firebox you can see into, and its flue."""
    rnd = random.Random(seed)
    d = ImageDraw.Draw(base)
    w, hh = FURNACE_W, FURNACE_H
    x0, x1 = cx - w / 2, cx + w / 2
    top = y_base - hh

    # flue: elbow off the back of the box up into the dark
    fx0 = cx + w * 0.16
    fw = w * 0.20
    d.rectangle([fx0, CEIL + px(4), fx0 + fw, top], fill=(34, 27, 24))
    d.rectangle([fx0, CEIL + px(4), fx0 + fw * 0.34, top], fill=(58, 44, 34))
    for y in range(int(CEIL + px(8)), int(top), int(px(18))):
        d.rectangle([fx0 - px(1.4), y, fx0 + fw + px(1.4), y + px(2.6)],
                    fill=(26, 20, 18))
    d.rectangle([fx0 - px(4), top - px(9), fx0 + fw + px(4), top - px(2)],
                fill=(44, 34, 28))          # the elbow into the box

    # shell: dark iron, lit along its bottom edges by its own fire
    d.rectangle([x0, top, x1, y_base], fill=IRON)
    d.rectangle([x0 + px(3), top + px(5), x1 - px(3), y_base - px(3)],
                fill=(48, 41, 37))
    # plinth and shoulders, so the box is a mass standing on the floor and not
    # a lit panel hung on the wall
    d.rectangle([x0 - px(7), y_base - px(11), x1 + px(7), y_base], fill=(30, 24, 21))
    d.line([(x0 - px(7), y_base - px(11)), (x1 + px(7), y_base - px(11))],
           fill=(92, 64, 44), width=max(1, px(1.2)))
    d.rectangle([x0 - px(9), top - px(2), x1 + px(9), top + px(11)], fill=(44, 35, 29))
    d.line([(x0 - px(9), top - px(2)), (x1 + px(9), top - px(2))],
           fill=(110, 80, 54), width=max(1, px(1.2)))
    for k in (0.20, 0.86):
        y = top + hh * k
        d.rectangle([x0 + px(2), y, x1 - px(2), y + px(3.4)], fill=(66, 52, 40))
        d.line([(x0 + px(2), y), (x1 - px(2), y)], fill=(112, 84, 58),
               width=max(1, px(1)))
        for rx in range(int(x0 + px(8)), int(x1 - px(6)), int(px(11))):
            d.ellipse([rx - px(0.9), y + px(4.4), rx + px(0.9), y + px(6)],
                      fill=IRON_LT)
    # the box mouth: small, deep, and unmistakably a fire in a hole
    mw, mh = w * 0.21, hh * 0.33
    my0 = y_base - px(7) - mh
    d.rectangle([cx - mw - px(5), my0 - px(5), cx + mw + px(5), y_base - px(3)],
                fill=(30, 22, 18))
    d.rectangle([cx - mw, my0, cx + mw, y_base - px(5)], fill=(9, 5, 4))
    # the fire sits at the bottom of the box: dark at the top of the opening,
    # white hot along the coals, so it reads as depth instead of a lit panel
    grad_down(d, my0, y_base - px(5), (48, 13, 5), (255, 160, 56),
              cx - mw, cx + mw)
    # coals glowing in the bottom of the box: layered, not one flat blob
    for k, (wv, col) in enumerate(((0.86, (188, 68, 18)), (0.62, (255, 124, 36)),
                                   (0.36, (255, 182, 92)))):
        d.ellipse([cx - mw * wv, y_base - px(20) + k * px(2),
                   cx + mw * wv, y_base - px(5)], fill=col)
    for k in range(7):
        cxx = cx - mw * 0.86 + k * mw * 0.28
        d.ellipse([cxx - mw * 0.15, y_base - px(10), cxx + mw * 0.15,
                   y_base - px(5)], fill=mix((255, 188, 96), (168, 44, 8), rnd.random()))
    for k in range(3):
        fx = cx - mw * 0.52 + k * mw * 0.52
        fh = mh * (0.40 + 0.48 * rnd.random())
        wob = px(1.8) * math.sin(k * 2.1)
        d.polygon([(fx - mw * 0.12, y_base - px(9)),
                   (fx + mw * 0.12, y_base - px(9)),
                   (fx + wob + px(1.0), y_base - px(9) - fh),
                   (fx + wob - px(1.0), y_base - px(9) - fh * 0.78)],
                  fill=mix((255, 150, 44), (255, 214, 120), rnd.random()))
        d.polygon([(fx - mw * 0.04, y_base - px(9)),
                   (fx + mw * 0.04, y_base - px(9)),
                   (fx + wob, y_base - px(9) - fh * 0.55)], fill=(255, 244, 200))
    # grate bars, dark against the fire
    for k in (-1, 1):
        bx = cx + k * mw * 0.40
        d.rectangle([bx - px(1.1), my0, bx + px(1.1), y_base - px(5)],
                    fill=(24, 17, 14))
    d.rectangle([cx - mw, my0 + mh * 0.44, cx + mw, my0 + mh * 0.44 + px(2)],
                fill=(24, 17, 14))
    # hood and the lit lip of the firebox
    d.rectangle([x0 - px(5), top - px(7), x1 + px(5), top + px(2)], fill=(52, 40, 33))
    d.line([(x0 - px(5), top - px(7)), (x1 + px(5), top - px(7))],
           fill=(120, 88, 58), width=max(1, px(1.2)))
    d.rectangle([cx - mw - px(5), y_base - px(10), cx + mw + px(5), y_base - px(4)],
                fill=(62, 44, 32))
    d.line([(cx - mw - px(5), y_base - px(10)), (cx + mw + px(5), y_base - px(10))],
           fill=(146, 96, 56), width=max(1, px(1.4)))
    # slag and coal spilled at its foot
    for _ in range(16):
        rx = cx + rnd.uniform(-mw * 1.15, mw * 1.15)
        r = px(rnd.uniform(1.2, 3.2))
        d.ellipse([rx, y_base - px(3), rx + r, y_base - px(1)],
                  fill=mix((120, 52, 18), (40, 26, 20), rnd.random()))
    # its light lying on the floor in front of the mouth
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([cx - w * 0.80, y_base - px(6), cx + w * 0.80, y_base + px(26)],
               fill=(255, 128, 44, 66))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(px(9))))

    RIM.append((cx, y_base - mh * 0.40, px(74), (255, 142, 54), 202))
    RIM.append((cx, y_base - px(2), px(86), (255, 112, 40), 96))


def furnace_slots():
    for i in range(-6, 7):
        x = CX + i * FURNACE_STEP
        if -FURNACE_W < x < W + FURNACE_W:
            yield i, x


# --------------------------------------------------------------- the victims
def chain(d, x, y_top, y_bot, w=px(2.0), link=px(4.2), sway=0.0):
    """A hanging chain: alternating flat links and edge-on links."""
    y, k = y_top, 0
    while y < y_bot:
        y2 = min(y_bot, y + link)
        xs = x + math.sin(k * 0.6) * sway
        if k % 2:
            d.line([(xs, y), (xs, y2)], fill=CHAIN, width=max(1, int(w * 0.55)))
            d.line([(xs + w * 0.5, y), (xs + w * 0.5, y2)], fill=IRON_DK,
                   width=max(1, int(w * 0.4)))
        else:
            d.ellipse([xs - w, y, xs + w, y2], outline=CHAIN,
                      width=max(1, int(w * 0.85)))
            d.arc([xs - w, y, xs + w, y2], 200, 340, fill=(28, 24, 21), width=1)
        y, k = y2, k + 1


def hook(d, x, y, r=px(4)):
    d.arc([x - r, y, x + r, y + r * 2.2], 200, 20, fill=CHAIN, width=max(2, px(1.7)))
    d.line([(x, y), (x, y + r * 0.6)], fill=CHAIN, width=max(2, px(1.7)))


def corpse_tile(h, seed=0):
    """One victim hung by the ankles, on its own tile so it can be tilted.

    y=0 is the ankle line and the body runs down to h*1.05, so the head and the
    hair end up at the bottom. Flesh is deliberately dull and the bone is what
    catches the light: light comes from the floor, so the skull and the ribs
    should be the brightest things on the figure.
    """
    rnd = random.Random(seed)
    tw, th = int(h * 0.92), int(h * 1.26)
    img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = tw / 2.0
    y = h * 0.06
    flesh = clamp(tuple(c + rnd.randint(-8, 8) for c in FLESH))
    dark = clamp(tuple(c * 0.50 for c in flesh))
    bone = clamp(tuple(c + rnd.randint(-10, 10) for c in BONE))

    # feet, still pointing up, and the shackle that holds them
    for sx in (-1, 1):
        fx = cx + sx * h * 0.062
        d.polygon([(fx - h * 0.030, y - h * 0.045), (fx + h * 0.026, y - h * 0.052),
                   (fx + h * 0.030, y + h * 0.004), (fx - h * 0.032, y + h * 0.004)],
                  fill=dark)
    d.rectangle([cx - h * 0.048, y + h * 0.000, cx + h * 0.048, y + h * 0.020],
                fill=(74, 68, 58))
    for sx in (-1, 1):
        sx_ = cx + sx * h * 0.056
        d.ellipse([sx_ - h * 0.026, y - h * 0.008, sx_ + h * 0.026, y + h * 0.030],
                  outline=(118, 110, 96), width=max(1, int(h * 0.010)))
    d.ellipse([cx - h * 0.014, y + h * 0.006, cx + h * 0.014, y + h * 0.026],
              fill=(52, 48, 42))

    # legs: thin at the ankle, knee bump, heavier at the hip
    for sx in (-1, 1):
        lx = cx + sx * h * 0.064
        d.polygon([(lx - h * 0.036, y + h * 0.016), (lx + h * 0.036, y + h * 0.016),
                   (lx + h * 0.050, y + h * 0.130), (lx + h * 0.048, y + h * 0.235),
                   (lx - h * 0.048, y + h * 0.235), (lx - h * 0.050, y + h * 0.130)],
                  fill=flesh)
        d.ellipse([lx - h * 0.050, y + h * 0.120, lx + h * 0.050, y + h * 0.170],
                  fill=flesh)                        # knee
        d.arc([lx - h * 0.052, y + h * 0.030, lx + h * 0.052, y + h * 0.110],
              180, 360, fill=dark, width=max(1, int(h * 0.012)))  # shadow above
        # no highlight down the shin: a lit thigh reads as a stocking, and the
        # figure stops being a body and becomes a person in pyjamas


    # pelvis and torso: narrow, then widening to the shoulders below
    d.ellipse([cx - h * 0.105, y + h * 0.215, cx + h * 0.105, y + h * 0.290],
              fill=flesh)
    d.polygon([(cx - h * 0.096, y + h * 0.250), (cx + h * 0.096, y + h * 0.250),
               (cx + h * 0.150, y + h * 0.545), (cx - h * 0.150, y + h * 0.545)],
              fill=flesh)
    d.ellipse([cx - h * 0.156, y + h * 0.515, cx + h * 0.156, y + h * 0.575],
              fill=flesh)
    # sunken belly, so the ribs above it read
    d.ellipse([cx - h * 0.080, y + h * 0.420, cx + h * 0.080, y + h * 0.505],
              fill=dark + (170,))
    # ribs: bone arcs, brightest at the bottom where the firelight reaches
    for k in range(5):
        ry = y + h * (0.360 + 0.040 * k)
        rw = h * (0.128 - 0.011 * k)
        d.arc([cx - rw, ry, cx + rw, ry + h * 0.056], 195, 345,
              fill=bone + (110 + 18 * k,), width=max(1, int(h * 0.011)))
    d.line([(cx, y + h * 0.352), (cx, y + h * 0.520)], fill=(88, 78, 64, 170),
           width=max(1, int(h * 0.010)))

    # arms hang past the head, because down is still down
    for sx in (-1, 1):
        ax = cx + sx * h * 0.140
        d.polygon([(ax - h * 0.032, y + h * 0.520), (ax + h * 0.032, y + h * 0.520),
                   (cx + sx * h * 0.098 + h * 0.022, y + h * 0.845),
                   (cx + sx * h * 0.098 - h * 0.022, y + h * 0.845)], fill=flesh)
        hx = cx + sx * h * 0.098
        d.ellipse([hx - h * 0.028, y + h * 0.832, hx + h * 0.028, y + h * 0.884],
                  fill=flesh)
        for f in range(3):
            d.line([(hx + (f - 1) * h * 0.016, y + h * 0.876),
                    (hx + (f - 1) * h * 0.021, y + h * 0.922)],
                   fill=mix(flesh, dark, 0.35), width=max(1, int(h * 0.008)))
        d.arc([hx - h * 0.032, y + h * 0.858, hx + h * 0.032, y + h * 0.892],
              10, 170, fill=bone + (80,), width=max(1, int(h * 0.008)))

    # neck and head: the head is the last thing to read, which is the point
    d.rectangle([cx - h * 0.040, y + h * 0.545, cx + h * 0.040, y + h * 0.640],
                fill=mix(flesh, dark, 0.30))
    hcx, hcy = cx, y + h * 0.730
    d.ellipse([hcx - h * 0.086, hcy - h * 0.088, hcx + h * 0.086, hcy + h * 0.092],
              fill=mix(bone, flesh, 0.45))
    # jaw hanging open, and the dark of the mouth
    d.polygon([(hcx - h * 0.060, hcy + h * 0.030), (hcx + h * 0.060, hcy + h * 0.030),
               (hcx + h * 0.042, hcy + h * 0.104), (hcx - h * 0.042, hcy + h * 0.104)],
              fill=mix(bone, dark, 0.35))
    d.ellipse([hcx - h * 0.026, hcy + h * 0.038, hcx + h * 0.026, hcy + h * 0.086],
              fill=(12, 9, 8))
    for t in range(4):
        tx = hcx - h * 0.020 + t * h * 0.013
        d.line([(tx, hcy + h * 0.040), (tx, hcy + h * 0.054)],
               fill=(212, 202, 178), width=max(1, int(h * 0.006)))
    # eye sockets, brow ridges, nose
    for sx in (-1, 1):
        ex = hcx + sx * h * 0.034
        d.ellipse([ex - h * 0.024, hcy - h * 0.038, ex + h * 0.024, hcy + h * 0.008],
                  fill=(14, 10, 9))
        d.arc([ex - h * 0.028, hcy - h * 0.048, ex + h * 0.028, hcy + h * 0.016],
              190, 350, fill=mix(bone, dark, 0.5), width=max(1, int(h * 0.009)))
    d.polygon([(hcx, hcy - h * 0.008), (hcx - h * 0.010, hcy + h * 0.030),
               (hcx + h * 0.010, hcy + h * 0.030)], fill=(28, 20, 16))
    # the scalp is at the bottom now, so the hair falls away from the face
    for k in range(8):
        hx = hcx - h * 0.056 + k * h * 0.016
        ln = h * (0.10 + 0.10 * rnd.random())
        d.line([(hx, hcy + h * 0.070),
                (hx + rnd.uniform(-h * 0.010, h * 0.010), hcy + h * 0.070 + ln)],
               fill=mix((36, 30, 26), (66, 56, 46), rnd.random()),
               width=max(1, int(h * (0.006 + 0.005 * rnd.random()))))
    # warm rim where the firelight catches the lowest surface of the skull
    # a dim underlight only: a bright arc under the jaw reads as a grin
    d.arc([hcx - h * 0.086, hcy + h * 0.030, hcx + h * 0.086, hcy + h * 0.140],
          10, 170, fill=(126, 96, 70, 70), width=max(1, int(h * 0.010)))

    # the rags still on him, hanging off the hips towards the floor
    for k in range(3):
        ox = cx - h * 0.070 + k * h * 0.055
        ln = h * (0.09 + 0.10 * rnd.random())
        d.polygon([(ox, y + h * 0.246), (ox + h * 0.050, y + h * 0.246),
                   (ox + h * 0.045 + rnd.uniform(-h * 0.02, h * 0.02),
                    y + h * 0.246 + ln),
                   (ox + h * 0.010, y + h * 0.246 + ln * 0.82)],
                  fill=mix(RAG, (78, 66, 50), rnd.random() * 0.6))

    # Knock the whole figure back towards silhouette. Against a wall this lit,
    # a fully rendered body reads as pale laundry; what the eye should find
    # first is the warm rim where the firelight catches its lowest edges.
    r, g, b, a = img.split()
    img = Image.merge("RGBA", (r.point(lambda v: int(v * 0.70)),
                               g.point(lambda v: int(v * 0.62)),
                               b.point(lambda v: int(v * 0.58)), a))
    d = ImageDraw.Draw(img)
    for (rx, ry_, rw, rh) in ((cx, y + h * 0.272, h * 0.100, h * 0.034),
                              (cx + h * 0.098, y + h * 0.868, h * 0.028, h * 0.016),
                              (cx - h * 0.098, y + h * 0.868, h * 0.028, h * 0.016),
                              (cx, y + h * 0.800, h * 0.078, h * 0.030)):
        d.arc([rx - rw, ry_ - rh, rx + rw, ry_ + rh], 10, 170,
              fill=(224, 132, 62, 130), width=max(1, int(h * 0.012)))
    return img


def hanging(base):
    """The rows: chains off the girders, and on most of them a body."""
    rnd = random.Random(71)
    d = ImageDraw.Draw(base)
    for i in range(-20, 21):
        x = CX + (i + 0.5) * HANG_STEP
        if x < -HANG_STEP or x > W + HANG_STEP:
            continue
        y0 = CEIL + rnd.uniform(0, px(3))
        roll = rnd.random()
        if roll < 0.24:
            bot = y0 + rnd.uniform(px(80), px(170))
            chain(d, x, y0, bot, sway=px(1.2))
            hook(d, x, bot)
            continue
        if roll < 0.33:
            bot = y0 + rnd.uniform(px(60), px(120))
            chain(d, x, y0, bot, sway=px(1.0))
            d.line([(x - px(5), bot), (x + px(5), bot)], fill=(96, 90, 82),
                   width=max(1, px(1.2)))
            for sx in (-1, 1):
                d.ellipse([x + sx * px(6) - px(2.6), bot - px(1), x + sx * px(6) + px(2.6),
                           bot + px(5)], outline=(112, 106, 96), width=max(1, px(1)))
            continue
        # a body, hung a little below the girder, sometimes a lot
        h = px(rnd.uniform(44, 78))
        # most hang high; a few are dropped low, so the rows are not a pattern
        y_ankle = y0 + (rnd.uniform(px(4), px(44)) if rnd.random() > 0.22
                        else rnd.uniform(px(80), px(170)))
        bx = x + rnd.uniform(-px(5), px(5))
        chain(d, x, y0, y_ankle - px(1), sway=px(0.8))
        # its shadow runs UP the wall, because the light is on the floor
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.ellipse([bx - h * 0.22, y_ankle - h * 0.26, bx + h * 0.22, y_ankle + h * 0.06],
                   fill=(6, 5, 5, 130))
        sd.ellipse([bx - h * 0.30, y_ankle + h * 0.30, bx + h * 0.30, y_ankle + h * 0.70],
                   fill=(6, 5, 5, 170))
        base.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(px(7))))
        d = ImageDraw.Draw(base)
        tile = corpse_tile(h, i * 31 + 11)
        tilt = rnd.uniform(-7, 7)
        tile = tile.rotate(tilt, expand=True, resample=Image.BICUBIC)
        base.alpha_composite(tile, (int(bx - tile.width / 2.0),
                                    int(y_ankle - h * 0.06)))
        d = ImageDraw.Draw(base)


# --------------------------------------------------------------- the floor
def floor(base):
    """Wet iron plate: coarse slabs, runnels, and the stains of the work."""
    d = ImageDraw.Draw(base)
    d.rectangle([0, FLOOR_Y, W, H], fill=(28, 24, 22))
    y, gap = FLOOR_Y, px(3)
    while y < H:
        y2 = min(H, y + gap)
        lift = int(16 * (y - FLOOR_Y) / max(1, H - FLOOR_Y))
        d.rectangle([0, y, W, y2], fill=(34 + lift, 28 + lift, 25 + lift))
        d.line([(0, y), (W, y)], fill=(14, 11, 10), width=max(1, px(0.8)))
        y = y2
        gap *= 1.26
    for k in range(-90, 91):
        xt = CX + k * px(9)
        d.line([(xt, FLOOR_Y), (CX + (xt - CX) * 4.0, H)], fill=(19, 15, 14),
               width=max(1, px(0.8)))
    d.line([(0, FLOOR_Y), (W, FLOOR_Y)], fill=(108, 68, 44), width=max(2, px(1.8)))
    rnd = random.Random(83)
    for _ in range(240):                       # rust and old stains
        x = rnd.randint(0, W)
        yy = rnd.randint(int(FLOOR_Y) + 2, H)
        r = rnd.randint(int(px(3)), int(px(16)))
        d.ellipse([x - r, yy - r * 0.35, x + r, yy + r * 0.35],
                  fill=mix((30, 18, 14), (54, 26, 17), rnd.random()) + (110,))
    base.alpha_composite(art.wet_floor(base, FLOOR_Y + px(3), (200, 112, 68), 26,
                                       seed=9, bands=140))


def pool(base, cx, rx, seed=0):
    """A sump sunk into the floor, with the chained dead still in it."""
    rnd = random.Random(seed)
    d = ImageDraw.Draw(base)
    cy, ry = FLOOR_Y + px(13), px(10)
    # A stone basin, widened towards the camera. Drawn as an ellipse this read
    # as a saucer lying on the floor rather than a sump sunk into it.
    top, bot = cy - ry, cy + ry
    back_l, back_r = cx - rx * 0.84, cx + rx * 0.84
    front_l, front_r = cx - rx, cx + rx
    d.polygon([(cx - rx * 0.98, cy), (cx + rx * 0.98, cy),
               (front_r + px(4), bot + px(4)), (front_l - px(4), bot + px(4))],
              fill=(20, 16, 15))                    # the stone rim, in shadow
    d.polygon([(back_l, top), (back_r, top), (front_r, bot), (front_l, bot)],
              fill=(16, 13, 12))                    # the recess
    # water: lit at the back where the slot reaches it, black at the front lip
    for i in range(int(ry * 2)):
        t = i / float(int(ry * 2) - 1)
        y0 = top + px(2) + i
        inset = px(5) + px(4) * t
        d.line([(back_l + inset, y0), (back_r - inset, y0)],
               fill=mix((26, 36, 34), (6, 9, 10), t ** 0.80))
    # the stakes the dead were chained to, and the chains into the water
    for sx in (-1, 1):
        stake_x = cx + sx * rx * 0.88
        d.rectangle([stake_x - px(2.4), cy - ry - px(20), stake_x + px(2.4),
                     cy + ry * 0.5], fill=(52, 46, 40))
        d.line([(stake_x - px(2.4), cy - ry - px(20)), (stake_x - px(2.4), cy + ry * 0.5)],
               fill=(88, 74, 58), width=max(1, px(1)))
        d.ellipse([stake_x - px(4), cy - ry - px(23), stake_x + px(4), cy - ry - px(15)],
                  fill=(70, 62, 52))
        chain(d, stake_x, cy - ry - px(15), cy + ry * 0.25, w=px(1.3), link=px(2.8))
    # the body: shoulders and the back of the head break the surface
    bx = cx - rx * 0.12
    d.ellipse([bx - rx * 0.34, cy - ry * 0.46, bx + rx * 0.30, cy + ry * 0.34],
              fill=mix((54, 45, 37), (24, 30, 28), 0.55))
    d.ellipse([bx + rx * 0.24, cy - ry * 0.54, bx + rx * 0.52, cy + ry * 0.04],
              fill=mix((124, 114, 92), (50, 42, 34), 0.45))
    d.ellipse([bx + rx * 0.30, cy - ry * 0.46, bx + rx * 0.38, cy - ry * 0.24],
              fill=(12, 10, 9))
    d.line([(bx - rx * 0.26, cy - ry * 0.12), (cx - rx * 0.84, cy + ry * 0.20)],
           fill=mix(FLESH, (52, 60, 56), 0.4), width=max(2, px(2.4)))
    d.line([(bx + rx * 0.30, cy - ry * 0.30), (cx + rx * 0.80, cy - ry * 0.10)],
           fill=mix(FLESH, (52, 60, 56), 0.4), width=max(2, px(2.2)))
    for k in range(5):                         # hair floating on the surface
        hx = bx + rx * (0.30 + 0.055 * k)
        d.arc([hx - px(4), cy - ry * 0.36, hx + px(4), cy + ry * 0.12], 200, 340,
              fill=(48, 44, 38, 150), width=1)
    # No ripples round the body: a ring of concentric ellipses on the floor is
    # what read as a bubble drawn round the fighters' boots when one of them
    # stood over a sump. The firelight on the water stays.
    d = ImageDraw.Draw(base)
    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    for k in range(4):
        yy = cy - ry * 0.50 + k * ry * 0.28
        rd.ellipse([cx - rx * (0.58 - 0.11 * k), yy - px(2.4),
                    cx + rx * (0.04 + 0.09 * k), yy + px(2.4)],
                   fill=(236, 124, 48, 34))
    base.alpha_composite(refl.filter(ImageFilter.GaussianBlur(px(2.5))))
    d = ImageDraw.Draw(base)
    RIM.append((cx, cy, rx * 1.15, (206, 112, 48), 26))


def pool_slots(rx):
    for i in range(-3, 4):
        x = CX + (i + 0.4) * FURNACE_STEP
        if -rx < x < W + rx:
            yield x


# --------------------------------------------------------------------- air
def smoke(base):
    """Coal smoke: a ceiling full of it, and plumes off every flue."""
    rnd = random.Random(29)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(60):
        x = rnd.randint(-px(60), W)
        y = rnd.randint(-px(10), int(CEIL + px(30)))
        w_ = rnd.randint(int(px(60)), int(px(220)))
        d.ellipse([x, y, x + w_, y + w_ * 0.40], fill=SOOT + (rnd.randint(20, 60),))
    for _i, fx in furnace_slots():
        for _ in range(6):
            x = fx + rnd.uniform(-px(16), px(30))
            y = rnd.uniform(-px(10), CEIL + px(26))
            w_ = rnd.randint(int(px(18)), int(px(60)))
            d.ellipse([x, y, x + w_, y + w_ * 0.66],
                      fill=mix(SOOT, (48, 36, 30), 0.4) + (rnd.randint(16, 44),))
    return Image.alpha_composite(base, layer.filter(ImageFilter.GaussianBlur(px(18))))


def heat(base):
    """The air over the fires: warm haze, so the room breathes."""
    rnd = random.Random(13)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _i, fx in furnace_slots():
        for _ in range(4):
            x = fx + rnd.uniform(-px(40), px(40))
            y = rnd.randint(int(FLOOR_Y - px(130)), int(FLOOR_Y - px(10)))
            w_ = rnd.randint(int(px(30)), int(px(90)))
            d.ellipse([x, y, x + w_, y + px(rnd.randint(10, 30))],
                      fill=(255, 122, 48, rnd.randint(6, 16)))
    return Image.alpha_composite(base, layer.filter(ImageFilter.GaussianBlur(px(14))))


# ------------------------------------------------------------------- painting
def paint():
    RIM.clear()
    base = hd.blank([(0, (8, 6, 6)), (40, (22, 14, 11)), (95, (34, 20, 15)),
                     (150, (28, 17, 13)), (205, (19, 12, 10)), (240, (6, 5, 5))])
    d = ImageDraw.Draw(base)
    ceiling(d)
    rust_wall(base)
    d = ImageDraw.Draw(base)
    buttresses(base)
    pipe_runs(base)
    floor_slot(base)

    for i, fx in furnace_slots():
        furnace(base, fx, FLOOR_Y, seed=i * 17 + 3)

    hanging(base)

    d = ImageDraw.Draw(base)
    floor(base)
    for i, pool_cx in enumerate(pool_slots(px(48))):
        pool(base, pool_cx, px(48), seed=i * 13 + 5)

    base = smoke(base)
    base = heat(base)
    base = art.screen(base, slot_spill(), glow_radius=px(8), gain=1.0)

    lights = list(RIM)
    for _i, fx in furnace_slots():
        lights.append((fx, FLOOR_Y - px(3), px(80), (255, 118, 44), 64))
    for x in range(-px(60), W + px(60), px(260)):
        lights.append((x, SLOT_TOP, px(60), (255, 132, 54), 46))
    base = hd.shade(base, [(hd.light(cx, cy, r, col, peak), px(9), 1.15)
                           for cx, cy, r, col, peak in lights])
    base = hd.finish(base, 13, 5, 0.55, FLOOR_Y)

    # foreground: chains hanging close to the camera, and the dark under the
    # near lip, so the fight has something in front of it
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    # The near lip: short and translucent. At 117px of near-opaque black it
    # swallowed the fighters' boots and left them standing in the air above
    # their own shadow, which is what the floor looked like from the front.
    for i in range(px(12)):
        a = int(150 * (1 - i / float(px(12))) ** 1.5)
        fd.line([(0, H - i), (W, H - i)], fill=(5, 4, 4, a))
    rnd = random.Random(97)
    for k in range(-7, 8):
        cx = CX + k * px(280) + rnd.uniform(-px(30), px(30))
        bot = px(rnd.uniform(30, 70))
        for i in range(int(px(4.2))):
            fd.line([(cx + i, 0), (cx + i, bot)], fill=(9, 8, 7, 120), width=1)
        fd.ellipse([cx - px(5), bot - px(3), cx + px(5), bot + px(5)],
                   fill=(12, 10, 9, 200))
        fd.arc([cx - px(6), bot + px(1), cx + px(6), bot + px(14)], 200, 20,
               fill=(16, 13, 11, 200), width=max(2, px(2.4)))
    fg = fg.filter(ImageFilter.GaussianBlur(px(1.2)))

    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, fg, 1)]


def main():
    hd.STAGES["hell_sinners"] = ("The Upside Down", paint)
    hd.build("hell_sinners")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
