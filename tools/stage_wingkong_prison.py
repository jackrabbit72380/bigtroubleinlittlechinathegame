"""Wing Kong Prison: the holding floor under the exchange.

Painted from the plan reference: a concrete block wall with barred windows and
the blue of the night coming through them, the big wire-mesh cage with its pale
sawn timber frame and its padlocked door, a plank table set out with bowls and
plates against the cage, a pail, papers dropped on the boards, and the timber
stair climbing away on the right with cobwebs in the corners.

A stage is seen across the play plane, so the cell floor is painted as a wall
wall-to-wall: the cages stand against the back of the floor, the table sits
against the mesh, and the fighters stand on the boards in front of it. The cage
frame, the table and the pail all stop at the floor line, so nothing comes out
into the play plane to stand on anybody's feet.

HD model, shared with every stage: 8192x1080 canvas, ground line at row 900,
zoffset 960, localcoord 1920x1080, camera travel +/-3136.

Run:  python3 tools/stage_wingkong_prison.py     (part of tools/build_all.py)
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

CEIL = px(50)                      # 225: the joists overhead
PLINTH = FLOOR_Y - px(12)          # 846: the foot of the wall
CAGE = (px(566), px(1234))         # the big cage
CAGE_TOP = px(56)
WINDOW_A = (px(112), px(268))
WINDOW_B = (px(330), px(478))
WIN_TOP, WIN_BOT = px(62), px(130)
STAIR = (px(1316), px(1782))       # the stair, rising to the right
TABLE = (px(690), px(1012))        # the table against the cage
TABLE_Y = px(150)

CONCRETE = (98, 106, 112)          # the block wall, cold beside the warm wood
CONCRETE_L = (132, 140, 146)
CONCRETE_D = (58, 64, 70)
PLANK = (108, 76, 46)              # the floor boards
PLANK_L = (146, 106, 66)
PLANK_D = (62, 42, 24)
FRAME = (176, 138, 84)             # the cage's sawn timber
FRAME_L = (216, 180, 118)
FRAME_D = (108, 80, 42)
MESH = (176, 178, 168)
DARK = (20, 18, 16)
NIGHT = (86, 120, 158)             # the blue through the bars
IRON = (58, 60, 60)
TIN = (154, 156, 148)
PAPER = (228, 224, 206)
WARM = (255, 204, 144)

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


# ------------------------------------------------------------------ the shell
def ceiling(base):
    """The joists over the cell floor, and the shadow they throw."""
    d = ImageDraw.Draw(base)
    d.rectangle(box(0, 0, W, CEIL), fill=(30, 25, 20))
    for x in range(-px(30), W, px(118)):
        d.rectangle(box(x, 0, x + px(20), CEIL), fill=(48, 38, 28))
        d.line([(x, 0), (x, CEIL)], fill=(74, 58, 42), width=max(1, int(px(0.8))))
        d.line([(x + px(20), 0), (x + px(20), CEIL)], fill=(14, 12, 10),
               width=max(1, int(px(1.0))))
    # a header beam over the whole wall, and the wall's top shadow
    d.rectangle(box(0, CEIL - px(10), W, CEIL), fill=(58, 44, 30))
    d.line([(0, CEIL - px(10)), (W, CEIL - px(10))], fill=(108, 84, 54),
           width=max(1, int(px(1.2))))
    d.line([(0, CEIL), (W, CEIL)], fill=(12, 10, 8), width=max(2, int(px(1.6))))
    for i in range(px(14)):
        a = int(92 * (1 - i / float(px(14))))
        d.line([(0, CEIL + i), (W, CEIL + i)], fill=(14, 16, 18, a))


def concrete(base, x0, x1, top=CEIL, bottom=PLINTH, seed=3):
    """Block courses: mortar joints, mottle, damp along the foot."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(seed)
    d.rectangle(box(x0, top, x1, bottom), fill=CONCRETE)
    for i in range(300):
        x = rnd.uniform(x0, x1)
        y = rnd.uniform(top, bottom)
        w = rnd.uniform(px(30), px(120))
        h = rnd.uniform(px(12), px(44))
        c = rnd.choice((CONCRETE_L, CONCRETE_D, (112, 120, 126), (78, 86, 94)))
        d.ellipse(box(x, y, x + w, y + h), fill=mix(CONCRETE, c, rnd.uniform(0.10, 0.32)))

    bh = px(26)
    y = top
    row = 0
    while y < bottom:
        yy = min(y + bh, bottom)
        off = 0 if row % 2 == 0 else px(30)
        x = x0 - off
        while x < x1:
            xx = x + px(60)
            c = tint(mix(CONCRETE, CONCRETE_L if rnd.random() < 0.5 else CONCRETE_D,
                         rnd.uniform(0.04, 0.16)), rnd, 0.05)
            d.rectangle(box(max(x, x0), y, min(xx, x1), yy), fill=c)
            d.line([(max(x, x0), y), (min(xx, x1), y)], fill=mix(c, (18, 20, 22), 0.55),
                   width=max(1, int(px(0.8))))
            d.line([(min(xx, x1), y), (min(xx, x1), yy)], fill=mix(c, (18, 20, 22), 0.55),
                   width=max(1, int(px(0.8))))
            d.line([(max(x, x0), y + px(1)), (min(xx, x1), y + px(1))],
                   fill=mix(c, (196, 202, 204), 0.22), width=max(1, int(px(0.4))))
            x = xx
        y = yy
        row += 1

    # damp rising out of the boards, and the grime under the beams
    for i in range(px(26)):
        a = int(78 * (1 - i / float(px(26))) ** 1.4)
        d.line([(x0, bottom - i), (x1, bottom - i)],
               fill=mix(CONCRETE, (24, 28, 30), a / 255.0))


def barred_window(base, x0, x1, y0, y1):
    """A window in the block wall: a deep reveal, iron bars, blue night behind."""
    d = ImageDraw.Draw(base)
    # the reveal, and the sky beyond it
    d.rectangle(box(x0 - px(8), y0 - px(8), x1 + px(8), y1 + px(8)), fill=(40, 46, 52))
    for i in range(int(y1 - y0)):
        tt = i / max(1.0, y1 - y0)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=mix(mix(NIGHT, (150, 176, 204), 0.30),
                                                      mix(NIGHT, (32, 44, 62), 0.45), tt))
    # a far wall or roofline out there
    d.polygon([(x0, y0 + (y1 - y0) * 0.62), (x0 + (x1 - x0) * 0.42, y0 + (y1 - y0) * 0.48),
               (x0 + (x1 - x0) * 0.42, y1), (x0, y1)],
              fill=mix(NIGHT, (24, 30, 40), 0.45))
    # bars: verticals, with two cross rails
    for k in range(5):
        bx = x0 + (x1 - x0) * (k + 0.5) / 5.0
        d.rectangle(box(bx - px(3), y0, bx + px(3), y1), fill=mix(IRON, (24, 26, 26), 0.3))
        d.line([(bx - px(3), y0), (bx - px(3), y1)], fill=(126, 132, 132),
               width=max(1, int(px(0.9))))
    for k in (0.34, 0.70):
        ry = y0 + (y1 - y0) * k
        d.rectangle(box(x0, ry - px(2.4), x1, ry + px(2.4)), fill=mix(IRON, (24, 26, 26), 0.3))
        d.line([(x0, ry - px(2.4)), (x1, ry - px(2.4))], fill=(120, 126, 126),
               width=max(1, int(px(0.8))))
    # the ledge, and the light the window lays on the wall
    d.rectangle(box(x0 - px(12), y1 + px(6), x1 + px(12), y1 + px(14)),
                fill=mix(CONCRETE, CONCRETE_L, 0.4))
    d.line([(x0 - px(12), y1 + px(6)), (x1 + px(12), y1 + px(6))], fill=(176, 186, 190),
           width=max(1, int(px(1.0))))
    lamp((x0 + x1) / 2.0, (y0 + y1) / 2.0, (x1 - x0) * 1.5, (120, 164, 210), 74)
    lamp((x0 + x1) / 2.0, FLOOR_Y + px(24), (x1 - x0) * 0.9, (110, 150, 200), 26)


def cobweb(base, cx, cy, r, side="left"):
    """A cobweb in a corner, drawn as threads so it stays a drawing.

    The threads fan from along the wall down to straight below it: 0 to 90
    degrees in a left corner, 90 to 180 in a right one.
    """
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    arms = 7
    a0, a1 = (0.0, 90.0) if side == "left" else (90.0, 180.0)
    tips = []
    for k in range(arms):
        a = math.radians(a0 + (a1 - a0) * k / (arms - 1))
        tipx, tipy = cx + math.cos(a) * r, cy + math.sin(a) * r
        tips.append((a, tipx, tipy))
        d.line([(cx, cy), (tipx, tipy)], fill=(208, 210, 200, 86), width=max(1, int(px(0.7))))
    for k in range(arms - 1):
        for j in range(1, 5):
            t = j / 5.0
            _, ax, ay = tips[k]
            _, bx, by = tips[k + 1]
            d.line([(cx + (ax - cx) * t, cy + (ay - cy) * t),
                    (cx + (bx - cx) * t, cy + (by - cy) * t)],
                   fill=(208, 210, 200, 66), width=max(1, int(px(0.55))))
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(px(0.6))))


# -------------------------------------------------------------------- the cage
def mesh_patch(base, x0, y0, x1, y1, alpha=58, step=None):
    """Diagonal wire mesh, masked to a box so it cannot run out of its panel."""
    step = step or px(11)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    span = y1 - y0
    for k in range(-int(span), int(x1 - x0) + int(span), int(step)):
        mx = x0 + k
        d.line([(mx, y0), (mx + span, y1)], fill=MESH + (alpha,), width=max(1, int(px(0.6))))
        d.line([(mx, y0), (mx - span, y1)], fill=MESH + (alpha,), width=max(1, int(px(0.6))))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rectangle(box(x0, y0, x1, y1), fill=255)
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
    base.alpha_composite(layer)


def cage(base, x0, x1, top):
    """The cell: pale timber framing over wire mesh, and the dark behind it."""
    d = ImageDraw.Draw(base)
    # the dark of the cell, and what little can be seen in it
    d.rectangle(box(x0, top, x1, PLINTH), fill=DARK)
    for i in range(px(60)):                       # a little light from the window
        a = int(30 * (1 - i / float(px(60))))
        d.line([(x0, top + i), (x0 + (x1 - x0) * 0.5, top + i)],
               fill=mix(DARK, (32, 40, 48), a / 255.0))
    # a bench along the back, and straw on the floor of the cell
    bench_y = top + (PLINTH - top) * 0.72
    d.rectangle(box(x0 + px(24), bench_y, x1 - px(24), bench_y + px(10)),
                fill=mix((72, 54, 34), DARK, 0.35))
    d.line([(x0 + px(24), bench_y), (x1 - px(24), bench_y)], fill=(96, 74, 46),
           width=max(1, int(px(1.0))))
    d.rectangle(box(x0 + px(24), bench_y + px(10), x1 - px(24), PLINTH),
                fill=mix((58, 44, 28), DARK, 0.45))
    rnd = random.Random(11)
    for i in range(40):                           # straw
        sx = rnd.uniform(x0 + px(20), x1 - px(20))
        sy = rnd.uniform(bench_y + px(12), PLINTH - px(4))
        d.line([(sx, sy), (sx + rnd.uniform(px(6), px(18)), sy - rnd.uniform(px(1), px(5)))],
               fill=mix((150, 124, 74), DARK, 0.35), width=max(1, int(px(0.7))))

    # the mesh, over the dark. The diagonals run past the cage on both sides, so
    # the layer is masked to the cage box: without that the wire drew itself
    # across the whole wall.
    mesh_patch(base, x0, top, x1, PLINTH)

    # the frame: posts, rails, and a lit edge on every member
    posts = [x0, x0 + (x1 - x0) / 3.0, x0 + (x1 - x0) * 2 / 3.0, x1]
    for k, cx in enumerate(posts):
        w = px(13) if k in (0, len(posts) - 1) else px(10)
        d.rectangle(box(cx - w, top, cx + w, PLINTH), fill=FRAME)
        d.line([(cx - w, top), (cx - w, PLINTH)], fill=FRAME_L, width=max(2, int(px(1.6))))
        d.line([(cx + w, top), (cx + w, PLINTH)], fill=FRAME_D, width=max(1, int(px(1.2))))
    for y, h in ((top, px(14)), (top + (PLINTH - top) * 0.46, px(11)),
                 (PLINTH - px(14), px(14))):
        d.rectangle(box(x0 - px(8), y, x1 + px(8), y + h), fill=FRAME)
        d.line([(x0 - px(8), y), (x1 + px(8), y)], fill=FRAME_L, width=max(2, int(px(1.8))))
        d.line([(x0 - px(8), y + h), (x1 + px(8), y + h)], fill=FRAME_D,
               width=max(1, int(px(1.2))))

    # the door in the last bay: wire like the rest of the cage, on its own frame,
    # hung on hinges and padlocked through a hasp
    dx0 = x0 + (x1 - x0) * 2 / 3.0 + px(14)
    dx1 = x1 - px(14)
    dy0, dy1 = top + px(16), PLINTH - px(16)
    d.rectangle(box(dx0, dy0, dx1, dy1), fill=mix(DARK, (44, 36, 26), 0.28))
    mesh_patch(base, dx0, dy0, dx1, dy1, alpha=64)
    # the door's own stiles and rails
    for x in (dx0, dx1 - px(9)):
        d.rectangle(box(x, dy0, x + px(9), dy1), fill=FRAME)
        d.line([(x, dy0), (x, dy1)], fill=FRAME_L, width=max(1, int(px(1.2))))
    for y in (dy0, dy1 - px(9)):
        d.rectangle(box(dx0, y, dx1, y + px(9)), fill=FRAME)
        d.line([(dx0, y), (dx1, y)], fill=FRAME_L, width=max(1, int(px(1.2))))
    # hinges on the hung edge
    for hy in (top + px(30), PLINTH - px(40)):
        d.rectangle(box(dx0 - px(9), hy, dx0 + px(2), hy + px(10)), fill=IRON)
        d.line([(dx0 - px(9), hy), (dx0 + px(2), hy)], fill=(128, 130, 126),
               width=max(1, int(px(0.8))))
        d.ellipse(box(dx0 - px(6), hy + px(2), dx0 - px(2), hy + px(7)), fill=(92, 94, 90))
    # the hasp crossing the door's edge, with the padlock through it
    hy = top + (PLINTH - top) * 0.50
    d.rectangle(box(dx1 - px(60), hy, dx1 + px(10), hy + px(9)),
                fill=mix(IRON, (96, 98, 92), 0.35))
    d.line([(dx1 - px(60), hy), (dx1 + px(10), hy)], fill=(146, 148, 142),
           width=max(1, int(px(0.9))))
    d.ellipse(box(dx1 - px(6), hy + px(8), dx1 + px(14), hy + px(26)), outline=IRON,
              width=max(2, int(px(2.6))))
    d.rectangle(box(dx1 - px(9), hy + px(16), dx1 + px(16), hy + px(36)),
                fill=mix(IRON, (112, 114, 108), 0.3))
    d.rectangle(box(dx1 - px(9), hy + px(16), dx1 + px(16), hy + px(36)),
                outline=(84, 86, 82), width=max(1, int(px(1.0))))
    d.ellipse(box(dx1 + px(1), hy + px(24), dx1 + px(6), hy + px(29)), fill=(22, 22, 20))

    # a bulb hanging in the cell, and the pool it makes on the straw
    bx = x0 + (x1 - x0) * 0.42
    d.line([(bx, top), (bx, top + px(26))], fill=(40, 38, 34), width=max(1, int(px(0.9))))
    d.ellipse(box(bx - px(5), top + px(24), bx + px(5), top + px(36)), fill=(255, 232, 178))
    for k in range(3):                            # its little cage
        d.arc(box(bx - px(9) + k * px(1.5), top + px(22), bx + px(9) - k * px(1.5), top + px(42)),
              -60, 60, fill=(70, 70, 66), width=max(1, int(px(0.8))))
    lamp(bx, top + px(34), px(150), (255, 200, 138), 52)


# ------------------------------------------------------------------- the stair
def stair(base, x0, x1):
    """The timber stair climbing to the right, with its handrail."""
    d = ImageDraw.Draw(base)
    steps = 10
    sw = (x1 - x0) / float(steps)
    rise = px(10.5)
    # the shadow the stair throws on the wall behind it
    d.polygon([(x0 - px(20), PLINTH), (x1, PLINTH), (x1, px(80)), (x0 - px(20), PLINTH)],
              fill=(30, 32, 34))
    for i in range(steps):
        sx0 = x0 + i * sw
        sx1 = sx0 + sw
        top = PLINTH - (i + 1) * rise
        c = mix(PLANK, (168, 124, 76), 0.30 + 0.05 * (i % 2))
        d.rectangle(box(sx0, top, sx1, PLINTH), fill=c)
        # the tread's nosing, lit, and the riser's shadow under it
        d.line([(sx0, top), (sx1, top)], fill=(232, 200, 148), width=max(2, int(px(1.6))))
        d.rectangle(box(sx0, top + px(1), sx1, top + px(4)), fill=mix(c, (80, 54, 30), 0.4))
        d.line([(sx0, top), (sx0, PLINTH)], fill=mix(c, (50, 34, 20), 0.55),
               width=max(1, int(px(1.0))))
        # grain along the riser
        for k in range(2):
            gy = top + px(6) + k * px(3)
            d.line([(sx0 + px(3), gy), (sx1 - px(3), gy)], fill=mix(c, (70, 48, 26), 0.3),
                   width=max(1, int(px(0.6))))
    # the stringer along the top of the flight, and the handrail above it
    d.line([(x0, PLINTH - rise), (x1, PLINTH - steps * rise)], fill=FRAME_L,
           width=max(2, int(px(2.2))))
    rail_y0 = PLINTH - rise - px(58)
    rail_y1 = PLINTH - steps * rise - px(58)
    d.line([(x0, rail_y0), (x1, rail_y1)], fill=mix(FRAME, FRAME_L, 0.35),
           width=max(3, int(px(4.0))))
    d.line([(x0, rail_y0 - px(2)), (x1, rail_y1 - px(2))], fill=(240, 208, 158),
           width=max(1, int(px(1.2))))
    for i in range(0, steps, 2):
        bx = x0 + (i + 0.5) * sw
        by = PLINTH - (i + 1) * rise
        ty = by - px(56)
        d.line([(bx, by), (bx, ty)], fill=mix(FRAME, FRAME_D, 0.3),
               width=max(2, int(px(2.0))))
    # the newel post at the foot of the stair
    d.rectangle(box(x0 - px(16), PLINTH - px(74), x0 - px(2), PLINTH), fill=FRAME)
    d.line([(x0 - px(16), PLINTH - px(74)), (x0 - px(2), PLINTH - px(74))],
           fill=FRAME_L, width=max(2, int(px(1.8))))
    d.ellipse(box(x0 - px(18), PLINTH - px(84), x0 - px(0), PLINTH - px(72)), fill=mix(FRAME, FRAME_L, 0.4))
    lamp(x0 + (x1 - x0) * 0.5, PLINTH - px(120), px(240), (255, 186, 126), 44)


# ------------------------------------------------------------------- furniture
def table(base, x0, x1):
    """The plank table against the cage, set out with bowls and plates."""
    d = ImageDraw.Draw(base)
    top = TABLE_Y
    # legs first, so the top sits over them
    for lx in (x0 + px(16), x1 - px(26)):
        d.rectangle(box(lx, top + px(8), lx + px(10), PLINTH), fill=mix(PLANK, PLANK_D, 0.35))
        d.line([(lx, top + px(8)), (lx, PLINTH)], fill=mix(PLANK, (140, 100, 60), 0.4),
               width=max(1, int(px(0.9))))
    # the top: three planks, with the light on the front edge
    d.rectangle(box(x0, top, x1, top + px(10)), fill=mix(PLANK, PLANK_L, 0.35))
    for k in (1, 2):
        d.line([(x0, top + px(10) * k / 3.0), (x1, top + px(10) * k / 3.0)],
               fill=mix(PLANK, PLANK_D, 0.4), width=max(1, int(px(0.7))))
    d.line([(x0, top), (x1, top)], fill=(238, 206, 156), width=max(2, int(px(1.8))))
    d.line([(x0, top + px(10)), (x1, top + px(10))], fill=(48, 32, 18),
           width=max(2, int(px(1.6))))
    # a bench beside it, a little lower
    d.rectangle(box(x0 + px(40), top + px(26), x1 - px(40), top + px(32)),
                fill=mix(PLANK, PLANK_L, 0.25))
    d.line([(x0 + px(40), top + px(26)), (x1 - px(40), top + px(26))], fill=(210, 176, 126),
           width=max(1, int(px(1.2))))
    for lx in (x0 + px(52), x1 - px(60)):
        d.rectangle(box(lx, top + px(32), lx + px(7), PLINTH), fill=mix(PLANK, PLANK_D, 0.4))

    # the bowls, plates and the big wooden bowl
    rnd = random.Random(23)
    items = [(0.10, 30), (0.24, 22), (0.36, 26), (0.50, 44), (0.64, 24), (0.74, 28), (0.88, 30)]
    for fx, r in items:
        cx = x0 + (x1 - x0) * fx
        rr = px(r / 2.2)
        d.ellipse(box(cx - rr, top - rr * 0.9, cx + rr, top + rr * 0.15),
                  fill=mix(TIN, (190, 190, 180), 0.25) if r > 32 else mix(TIN, (120, 122, 112), 0.2))
        d.ellipse(box(cx - rr * 0.72, top - rr * 0.74, cx + rr * 0.72, top - rr * 0.10),
                  fill=mix((150, 130, 96), (58, 46, 30), 0.45))
        d.ellipse(box(cx - rr, top - rr * 0.9, cx + rr, top + rr * 0.15),
                  outline=mix(TIN, (210, 210, 200), 0.4), width=max(1, int(px(0.9))))
        if rnd.random() < 0.4:                       # a plate standing on edge
            d.polygon([(cx + rr * 1.2, top), (cx + rr * 1.9, top - px(10)),
                       (cx + rr * 2.1, top - px(1)), (cx + rr * 1.5, top + px(2))],
                      fill=mix(TIN, (206, 204, 192), 0.35))
    lamp((x0 + x1) / 2.0, top - px(10), px(220), (255, 198, 140), 40)


def pail(base, cx):
    """A tin pail stood on the boards against the cage."""
    d = ImageDraw.Draw(base)
    top = PLINTH - px(34)
    d.polygon([(cx - px(17), top), (cx + px(17), top),
               (cx + px(13), PLINTH), (cx - px(13), PLINTH)], fill=mix(TIN, (96, 98, 92), 0.35))
    d.ellipse(box(cx - px(17), top - px(6), cx + px(17), top + px(6)),
              fill=mix(TIN, (60, 62, 58), 0.4))
    d.ellipse(box(cx - px(17), top - px(6), cx + px(17), top + px(6)),
              outline=mix(TIN, (226, 226, 214), 0.5), width=max(1, int(px(1.1))))
    d.arc(box(cx - px(16), top - px(20), cx + px(16), top + px(2)), 190, 350,
          fill=(120, 122, 116), width=max(1, int(px(1.4))))
    d.line([(cx - px(12), PLINTH - px(12)), (cx + px(12), PLINTH - px(12))],
           fill=(70, 72, 68), width=max(2, int(px(1.6))))
    d.line([(cx - px(20), PLINTH + px(1)), (cx + px(20), PLINTH + px(1))],
           fill=(20, 14, 10), width=max(2, int(px(1.6))))


# ----------------------------------------------------------------- the boards
def boards(base):
    """Plank flooring: long boards, nails, stains, and the room's light on it."""
    d = ImageDraw.Draw(base)
    rnd = random.Random(41)
    d.rectangle(box(0, FLOOR_Y, W, H), fill=PLANK)
    rows = [FLOOR_Y, FLOOR_Y + px(20), FLOOR_Y + px(46), FLOOR_Y + px(80), H]
    for i in range(len(rows) - 1):
        y0, y1 = rows[i], rows[i + 1]
        c = mix(PLANK, PLANK_L, 0.08 + 0.10 * (i % 2))
        d.rectangle(box(0, y0, W, y1), fill=c)
        d.line([(0, y0), (W, y0)], fill=mix(c, (34, 22, 12), 0.5), width=max(1, int(px(0.9))))
        # board ends, staggered
        x = rnd.uniform(-px(300), 0)
        while x < W:
            d.line([(x, y0), (x, y1)], fill=mix(c, (30, 20, 10), 0.55),
                   width=max(1, int(px(1.0))))
            d.ellipse(box(x + px(4), y0 + px(3), x + px(8), y0 + px(7)),
                      fill=mix(IRON, (20, 20, 18), 0.4))
            x += rnd.uniform(px(340), px(620))
        # grain and knots
        for k in range(7):
            gy = rnd.uniform(y0 + px(2), y1 - px(2))
            gx = rnd.uniform(0, W)
            d.line([(gx, gy), (gx + rnd.uniform(px(200), px(760)), gy)],
                   fill=mix(c, (44, 28, 14), 0.28), width=max(1, int(px(0.6))))
        for k in range(3):
            kx = rnd.uniform(0, W)
            ky = rnd.uniform(y0 + px(3), y1 - px(3))
            d.ellipse(box(kx, ky, kx + px(7), ky + px(4)), fill=mix(c, (40, 26, 12), 0.5))

    # the wall's shadow on the boards, and the blue from the windows
    for i in range(px(16)):
        a = int(130 * (1 - i / float(px(16))) ** 1.5)
        d.line([(0, FLOOR_Y + i), (W, FLOOR_Y + i)], fill=mix(PLANK, (14, 10, 8), a / 255.0))

    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    for cx0, col, wdt, a in (((WINDOW_A[0] + WINDOW_A[1]) / 2.0, (96, 138, 186), px(160), 44),
                             ((WINDOW_B[0] + WINDOW_B[1]) / 2.0, (96, 138, 186), px(160), 44),
                             ((CAGE[0] + CAGE[1]) / 2.0, (255, 196, 132), px(300), 34),
                             ((STAIR[0] + STAIR[1]) / 2.0, (255, 190, 128), px(250), 40)):
        rd.polygon([(cx0 - wdt / 2.0, FLOOR_Y + px(4)), (cx0 + wdt / 2.0, FLOOR_Y + px(4)),
                    (cx0 + wdt * 1.25, H), (cx0 - wdt * 1.25, H)], fill=col + (a,))
    base.alpha_composite(refl.filter(ImageFilter.GaussianBlur(px(26))))

    # papers dropped on the boards, flat, so nobody trips on them
    for k in range(6):
        pxx = rnd.uniform(0, W)
        pyy = rnd.uniform(FLOOR_Y + px(16), H - px(10))
        w = rnd.uniform(px(16), px(30))
        d.polygon([(pxx, pyy), (pxx + w, pyy - px(5)), (pxx + w * 1.05, pyy + px(9)),
                   (pxx + px(3), pyy + px(13))],
                  fill=mix(PAPER, (176, 170, 150), rnd.uniform(0.1, 0.5)))
    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.rectangle(box(0, FLOOR_Y, W, H), fill=(196, 178, 146, 14))
    base.alpha_composite(sheen.filter(ImageFilter.GaussianBlur(px(14))))


def foreground():
    """The near plane: dust in the air, and the dark at the bottom."""
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    rnd = random.Random(67)
    for i in range(px(40)):
        a = int(156 * (1 - i / float(px(40))) ** 1.6)
        d.line([(0, H - i), (W, H - i)], fill=(8, 7, 6, a))
    for _ in range(130):
        x = rnd.uniform(0, W)
        y = rnd.uniform(px(50), H)
        r = rnd.uniform(px(0.9), px(2.6))
        d.ellipse(box(x - r, y - r, x + r, y + r),
                  fill=(255, 210, 152, rnd.randint(16, 54)))
    return fg.filter(ImageFilter.GaussianBlur(px(2.0)))


# ------------------------------------------------------------------- the arena
def paint():
    LIGHTS.clear()
    base = hd.blank([(0, (14, 12, 10)), (CEIL, (26, 26, 26)),
                     (px(140), (52, 50, 48)), (FLOOR_Y, (60, 46, 30)),
                     (H, (28, 20, 14))])

    ceiling(base)
    concrete(base, 0, W, seed=5)

    barred_window(base, WINDOW_A[0], WINDOW_A[1], WIN_TOP, WIN_BOT)
    barred_window(base, WINDOW_B[0], WINDOW_B[1], WIN_TOP, WIN_BOT)
    # a boarded-over vent between the windows, and the damp under it
    d = ImageDraw.Draw(base)
    d.rectangle(box(px(288), px(84), px(312), px(126)), fill=mix(CONCRETE, CONCRETE_D, 0.4))
    for k in range(4):
        yy = px(88) + k * px(9)
        d.rectangle(box(px(284), yy, px(316), yy + px(6)), fill=mix(PLANK, PLANK_D, 0.3))

    # the cell, and the framing that carries the floor above it
    cage(base, CAGE[0], CAGE[1], CAGE_TOP)
    stair(base, STAIR[0], STAIR[1])

    table(base, TABLE[0], TABLE[1])
    pail(base, px(1130))
    pail(base, px(470))

    cobweb(base, 0, CEIL, px(90), "left")
    cobweb(base, W, CEIL, px(90), "right")

    boards(base)

    base = hd.shade(base, [(hd.light(cx, cy, r, col, int(peak * 0.82)),
                            max(8, int(r * 0.30)), 1.05)
                           for cx, cy, r, col, peak in LIGHTS])
    base = art.vignette(base, 0.48)
    base = art.grain(base, 3, seed=29)
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, foreground(), 1)]


def main():
    hd.STAGES["wingkong_prison"] = ("Wing Kong Prison", paint)
    hd.build("wingkong_prison")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
