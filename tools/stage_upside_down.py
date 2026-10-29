"""The Upside Down: the underground arena under Lo Pan's palace (1280x960).

Painted from the reference art: a cavern roof of wet earth with roots hanging
through it, a circle of pale stone inlaid in the floor with a green shaft of
light falling into it, a stair dropping out of that circle into the dark,
gnarled trunks framing both sides, mossy rock and a red-eyed face in the wall.

Scale matters here: a 4:3 match view is 1280 of the 4000-wide canvas, so the
ring, the stair and the trunk nearest the centre all live inside +-520 px of
CX. Anything wider fills the whole screen and stops reading as a floor.

Run:  python3 tools/stage_upside_down.py     (part of tools/build_all.py)
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

CEILING = px(24)                          # average lower edge of the earth roof
RING_CX = CX
RING_CY = FLOOR_Y - px(8)                 # the circle sits under the fighters' feet
RING_RX, RING_RY = px(64), px(19)

GREEN = (86, 220, 124)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ------------------------------------------------------------------ the roof
def ceiling(base):
    """Wet earth roof: ragged lower edge, embedded stones."""
    rnd = random.Random(7)
    d = ImageDraw.Draw(base)
    edge = []
    for x in range(0, W + px(4), px(3)):
        y = CEILING + int(px(13) * math.sin(x / px(46.0)) +
                          px(6) * math.sin(x / px(13.0) + 1.7) +
                          rnd.uniform(-px(2), px(2)))
        edge.append((x, y))
    d.polygon([(0, -px(6))] + edge + [(W, -px(6))], fill=(34, 24, 16))
    for _ in range(2200):
        x = rnd.randint(0, W)
        y = rnd.randint(-px(4), int(CEILING + px(10)))
        r = rnd.randint(1, max(2, int(px(2))))
        d.ellipse([x, y, x + r, y + r * 0.7],
                  fill=mix((18, 13, 11), (46, 36, 24), rnd.random() * 0.8))
    for _ in range(120):
        x = rnd.randint(0, W)
        y = rnd.randint(int(px(2)), int(CEILING + px(6)))
        r = rnd.randint(int(px(1)), int(px(3)))
        d.ellipse([x, y, x + r, y + r * 0.8],
                  fill=mix((74, 68, 56), (116, 108, 92), rnd.random()))
    d.line([(x, y + px(1)) for x, y in edge], fill=(52, 40, 26), width=max(1, px(1)))


def roots(base, seed=12, count=40):
    """Roots breaking through the roof and hanging into the cavern."""
    rnd = random.Random(seed)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(count):
        x = rnd.randint(0, W)
        y = rnd.randint(int(CEILING - px(6)), int(CEILING + px(12)))
        ln = rnd.randint(int(px(20)), int(px(150)))
        pts, xx, yy = [], float(x), float(y)
        for _k in range(9):
            pts.append((xx, yy))
            xx += rnd.uniform(-px(4), px(4))
            yy += ln / 8
        wid = max(1, int(px(1.4) * rnd.uniform(0.7, 1.8)))
        d.line(pts, fill=(30, 22, 15, 235), width=wid)
        if ln > px(80):
            bx, by = pts[-3]
            d.line([(bx, by), (bx + rnd.uniform(-px(16), px(16)), by + ln * 0.3)],
                   fill=(27, 20, 14, 210), width=max(1, wid - 1))
        d.ellipse([pts[-1][0] - 2, pts[-1][1] - 2, pts[-1][0] + 2, pts[-1][1] + 2],
                  fill=(34, 26, 18, 210))
    return Image.alpha_composite(base, layer)


# ------------------------------------------------------------------ the wall
def rock_wall(base):
    """Cave face built from overlapping plates, not masonry courses."""
    rnd = random.Random(23)
    d = ImageDraw.Draw(base)
    d.rectangle([0, 0, W, FLOOR_Y], fill=(19, 21, 23))
    for layer in range(4):
        lit = 1.0 - layer / 4.0
        for _ in range(34):
            x = rnd.randint(-px(24), W)
            y = rnd.randint(int(CEILING - px(10)), int(FLOOR_Y))
            w = rnd.randint(int(px(26)), int(px(150)))
            h = rnd.randint(int(px(12)), int(px(64)))
            tone = int(12 + 20 * lit + rnd.uniform(-6, 9))
            pts = [(x, y), (x + w, y + rnd.randint(-8, 8)),
                   (x + w + rnd.randint(-10, 12), y + h),
                   (x + rnd.randint(-8, 10), y + h + rnd.randint(-6, 6))]
            d.polygon(pts, fill=(tone, tone + 3, tone + 6))
            d.line(pts + [pts[0]], fill=(max(0, tone - 10),) * 3,
                   width=max(1, px(1)))
    seams = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(seams)
    for i in range(7):
        y = CEILING + (FLOOR_Y - CEILING) * (i + rnd.random()) / 7
        pts = [(x, y + math.sin(x / px(120.0) + i) * px(10))
               for x in range(0, W, px(16))]
        sd.line(pts, fill=(6, 7, 8, 200), width=max(1, px(2.4)))
        sd.line([(x, yy - px(2)) for x, yy in pts], fill=(58, 62, 60, 90),
                width=max(1, px(1.4)))
    base.alpha_composite(seams.filter(ImageFilter.GaussianBlur(px(1.6))))
    moss = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(moss)
    for _ in range(1100):
        x = rnd.randint(0, W)
        y = rnd.randint(int(FLOOR_Y - px(140)), int(FLOOR_Y + px(20)))
        r = rnd.randint(int(px(2)), int(px(10)))
        md.ellipse([x, y, x + r, y + r * 0.55],
                   fill=(52, 84, 36, rnd.randint(20, 90)))
    base.alpha_composite(moss.filter(ImageFilter.GaussianBlur(px(2))))
    damp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(damp)
    for _ in range(70):
        x = rnd.randint(0, W)
        y = rnd.randint(int(CEILING + px(20)), int(FLOOR_Y - px(40)))
        dd.rectangle([x, y, x + rnd.randint(int(px(2)), int(px(9))),
                      y + rnd.randint(int(px(40)), int(px(170)))],
                     fill=(28, 44, 34, rnd.randint(10, 26)))
    base.alpha_composite(damp.filter(ImageFilter.GaussianBlur(px(4))))


def trunk(base, x, w_top, w_bot, seed, sway=0.0):
    """Gnarled root column, sculpted from a colour + height field for girth."""
    rnd = random.Random(seed)
    h = FLOOR_Y - px(16)
    ws = int(max(w_top, w_bot) * 2.4)
    color = Image.new("RGB", (ws, h), (0, 0, 0))
    height = Image.new("L", (ws, h), 0)
    dc, dh = ImageDraw.Draw(color), ImageDraw.Draw(height)
    bark = (56, 46, 34)

    def width_at(y):
        t = y / h
        return (w_top + (w_bot - w_top) * t) * (1 + 0.12 * math.sin(t * 5 + seed))

    for y in range(0, h, 3):
        t = y / h
        cxx = ws / 2 + sway * ws * 0.10 * math.sin(t * 3.1 + seed)
        w = width_at(y)
        dc.rectangle([cxx - w, y, cxx + w, y + 4], fill=bark)
        dh.rectangle([cxx - w, y, cxx + w, y + 4], fill=200)
    for k in range(10):
        off = rnd.uniform(-0.75, 0.75)
        for y in range(0, h, 5):
            t = y / h
            cxx = ws / 2 + sway * ws * 0.10 * math.sin(t * 3.1 + seed)
            w = width_at(y)
            xx = cxx + off * w + math.sin(t * 16 + k) * w * 0.06
            dc.rectangle([xx - 1, y, xx + 1, y + 6], fill=mix(bark, (96, 78, 52), 0.5))
            dh.rectangle([xx - 1, y, xx + 1, y + 6], fill=216)
    for _ in range(7):
        ky = rnd.randint(int(h * 0.15), int(h * 0.95))
        cxx = ws / 2 + sway * ws * 0.10 * math.sin(ky / h * 3.1 + seed)
        r = rnd.uniform(px(2), px(7))
        dc.ellipse([cxx - r, ky - r, cxx + r, ky + r], fill=(24, 20, 15))
        dh.ellipse([cxx - r, ky - r, cxx + r, ky + r], fill=146)
    layer = hd.sculpted(color, height, x, FLOOR_Y - px(14))
    d = ImageDraw.Draw(layer)
    for _ in range(8):
        ex = x + rnd.uniform(-w_bot * 2.4, w_bot * 2.4)
        mid = (x + ex) / 2 + rnd.uniform(-px(8), px(8))
        d.line([(x, FLOOR_Y - px(18)), (mid, FLOOR_Y - px(5)), (ex, FLOOR_Y + px(5))],
               fill=(30, 24, 18), width=max(2, int(px(2.2) * rnd.uniform(0.6, 1.2))))
    return Image.alpha_composite(base, layer)


# ------------------------------------------------------------------ the ring
def ring(base):
    """Pale inlaid circle, the lit floor inside it, and the stair down into it."""
    d = ImageDraw.Draw(base)
    d.ellipse([RING_CX - RING_RX, RING_CY - RING_RY,
               RING_CX + RING_RX, RING_CY + RING_RY], fill=(122, 122, 100))
    base.alpha_composite(art.radial_light((W, H), (RING_CX, RING_CY + px(2)),
                                          RING_RX * 0.85, (208, 210, 172), 150))
    d = ImageDraw.Draw(base)
    seg = 40
    for i in range(seg):
        a0 = 2 * math.pi * i / seg
        a1 = 2 * math.pi * (i + 1) / seg
        tone = 92 + int(26 * math.sin(i * 1.9))
        d.polygon([(RING_CX + math.cos(a0) * RING_RX, RING_CY + math.sin(a0) * RING_RY),
                   (RING_CX + math.cos(a1) * RING_RX, RING_CY + math.sin(a1) * RING_RY),
                   (RING_CX + math.cos(a1) * RING_RX * 0.86,
                    RING_CY + math.sin(a1) * RING_RY * 0.86),
                   (RING_CX + math.cos(a0) * RING_RX * 0.86,
                    RING_CY + math.sin(a0) * RING_RY * 0.86)],
                  fill=(tone + 26, tone + 24, tone + 6))
        d.line([(RING_CX + math.cos(a0) * RING_RX, RING_CY + math.sin(a0) * RING_RY),
                (RING_CX + math.cos(a0) * RING_RX * 0.86,
                 RING_CY + math.sin(a0) * RING_RY * 0.86)],
               fill=(48, 46, 36), width=max(1, px(1)))
    d.arc([RING_CX - RING_RX, RING_CY - RING_RY, RING_CX + RING_RX, RING_CY + RING_RY],
          0, 360, fill=(178, 178, 148), width=max(1, px(1.2)))

    top_y, bot_y = RING_CY - px(18), RING_CY + px(10)
    steps = 7
    for i in range(steps):
        t0, t1 = i / steps, (i + 1) / steps
        y0 = top_y + (bot_y - top_y) * t0
        y1 = top_y + (bot_y - top_y) * t1
        w0 = px(26) - px(11) * t0
        w1 = px(26) - px(11) * t1
        tone = int(88 - 74 * t0 ** 0.7)
        d.polygon([(RING_CX - w0, y0), (RING_CX + w0, y0),
                   (RING_CX + w1, y1), (RING_CX - w1, y1)],
                  fill=(tone, tone, int(tone * 0.86)))
        d.line([(RING_CX - w1, y1), (RING_CX + w1, y1)],
               fill=(max(0, tone - 30),) * 3, width=max(1, px(1)))
    d.ellipse([RING_CX - px(13), bot_y - px(3), RING_CX + px(13), bot_y + px(6)],
              fill=(5, 6, 6))


def shaft(base):
    """Green light column falling through the roof into the circle."""
    top_y, bot_y = CEILING - px(6), RING_CY + px(2)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(22):
        t = i / 21
        half = px(8) + (px(26) - px(8)) * t
        d.polygon([(RING_CX - half, bot_y), (RING_CX + half, bot_y),
                   (RING_CX + half * 0.62, top_y), (RING_CX - half * 0.62, top_y)],
                  fill=GREEN + (int(16 + 20 * (1 - t)),))
    layer = layer.filter(ImageFilter.GaussianBlur(px(6)))
    core = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(core)
    for i in range(10):
        t = i / 9
        half = px(2) + px(3) * t
        cd.rectangle([RING_CX - half, top_y, RING_CX + half, bot_y],
                     fill=(226, 255, 214, int(38 + 34 * (1 - t))))
    core = core.filter(ImageFilter.GaussianBlur(px(2)))
    out = art.screen(base, layer, glow_radius=px(10), gain=1.1, passes=2)
    return art.screen(out, core, glow_radius=px(4), gain=0.85)


# ------------------------------------------------------------------ set dressing
def log(base, cx, cy, ln, thick, seed=3):
    """Fallen trunk crossing the floor, with sawn end grain facing the camera."""
    rnd = random.Random(seed)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pts_top, pts_bot = [], []
    for i in range(21):
        t = i / 20
        x = cx - ln / 2 + ln * t
        y = cy + math.sin(t * 3.4 + seed) * thick * 0.5
        pts_top.append((x, y - thick * (1 - 0.25 * t)))
        pts_bot.append((x, y + thick * (1 - 0.25 * t)))
    d.polygon(pts_top + pts_bot[::-1], fill=(44, 36, 26))
    for k in range(9):
        d.line([(p[0], p[1] + k * thick * 0.12) for p in pts_top],
               fill=(32, 26, 19), width=max(1, px(1)))
    ex, ey = cx - ln / 2, cy
    d.ellipse([ex - thick * 0.5, ey - thick, ex + thick * 0.5, ey + thick],
              fill=(96, 76, 50))
    for r in range(3):
        rr = thick * (0.18 + r * 0.22)
        d.arc([ex - rr * 0.6, ey - rr, ex + rr * 0.6, ey + rr], 0, 360,
              fill=(72, 56, 36), width=max(1, px(1)))
    for _ in range(60):
        x = cx - ln / 2 + rnd.uniform(0, ln)
        y = cy - thick * 0.9 + rnd.uniform(-thick * 0.1, thick * 0.2)
        d.ellipse([x, y, x + rnd.uniform(px(2), px(5)), y + px(3)],
                  fill=(46, 74, 32, 150))
    return Image.alpha_composite(base, layer.filter(ImageFilter.GaussianBlur(px(0.6))))


def puddle(base, cx, cy, rx, ry, seed=0):
    rnd = random.Random(seed)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(8, 12, 11, 210))
    d.arc([cx - rx, cy - ry, cx + rx, cy + ry], 190, 350,
          fill=(70, 120, 88, 130), width=max(1, px(1.4)))
    for _ in range(6):
        sx = cx + rnd.uniform(-rx * 0.7, rx * 0.7)
        sy = cy + rnd.uniform(-ry * 0.5, ry * 0.5)
        d.line([(sx, sy), (sx + rnd.uniform(-px(8), px(8)), sy + px(1))],
               fill=(120, 190, 140, rnd.randint(40, 90)), width=max(1, px(1)))
    return Image.alpha_composite(base, layer.filter(ImageFilter.GaussianBlur(px(0.8))))


def demon(base, cx, cy, w, h):
    """A face in the rock: carved brow, and eyes that are the only warm light."""
    rnd = random.Random(41)
    d = ImageDraw.Draw(base)
    d.polygon([(cx - w * 0.60, cy + h * 0.55), (cx - w * 0.46, cy - h * 0.16),
               (cx - w * 0.18, cy - h * 0.44), (cx + w * 0.18, cy - h * 0.44),
               (cx + w * 0.46, cy - h * 0.16), (cx + w * 0.60, cy + h * 0.55)],
              fill=(14, 13, 14))
    d.polygon([(cx - w * 0.40, cy - h * 0.08), (cx - w * 0.10, cy - h * 0.22),
               (cx + w * 0.10, cy - h * 0.22), (cx + w * 0.40, cy - h * 0.08),
               (cx + w * 0.28, cy + h * 0.03), (cx - w * 0.28, cy + h * 0.03)],
              fill=(26, 23, 23))
    for sx in (-1, 1):
        d.polygon([(cx + sx * w * 0.32, cy - h * 0.28),
                   (cx + sx * w * 0.50, cy - h * 0.50),
                   (cx + sx * w * 0.42, cy - h * 0.22)], fill=(20, 18, 18))
    d.polygon([(cx - w * 0.12, cy + h * 0.14), (cx + w * 0.12, cy + h * 0.14),
               (cx + w * 0.07, cy + h * 0.32), (cx - w * 0.07, cy + h * 0.32)],
              fill=(7, 6, 7))
    for _ in range(8):
        x = cx + rnd.uniform(-w * 0.58, w * 0.58)
        d.line([(x, cy - h * 0.38), (x + rnd.uniform(-px(3), px(3)), cy + h * 0.38)],
               fill=(21, 20, 20), width=max(1, px(1)))
    eyes = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ed = ImageDraw.Draw(eyes)
    for sx in (-1, 1):
        ex = cx + sx * w * 0.19
        ed.ellipse([ex - px(4), cy - h * 0.12, ex + px(4), cy - h * 0.04],
                   fill=(255, 44, 28))
        ed.ellipse([ex - px(1.6), cy - h * 0.105, ex + px(1.6), cy - h * 0.058],
                   fill=(255, 216, 184))
        ed.ellipse([ex - px(2.6), cy + h * 0.19, ex + px(2.6), cy + h * 0.235],
                   fill=(182, 26, 18))
    return art.screen(base, eyes, glow_radius=px(6), gain=1.4, passes=2)


def mist(img, seed=5):
    rnd = random.Random(seed)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(8):
        y = FLOOR_Y - px(rnd.randint(20, 90))
        d.ellipse([rnd.randint(-px(80), W // 2), y,
                   rnd.randint(W // 2, W + px(80)), y + px(rnd.randint(14, 40))],
                  fill=(20, 74, 48, rnd.randint(10, 24)))
    return Image.alpha_composite(img, layer.filter(ImageFilter.GaussianBlur(px(18))))


# ------------------------------------------------------------------ the arena
def paint():
    base = hd.blank([(0, (6, 7, 9)), (30, (10, 12, 14)), (90, (14, 17, 19)),
                     (150, (17, 20, 21)), (200, (17, 19, 20)), (240, (8, 10, 10))])
    rock_wall(base)
    d = ImageDraw.Draw(base)

    # floor: broken paving with the ring inlaid on top of it
    d.rectangle([0, FLOOR_Y, W, H], fill=(27, 28, 27))
    rnd = random.Random(31)
    for _ in range(160):
        x = rnd.randint(-px(10), W)
        y = rnd.randint(int(FLOOR_Y), int(H))
        w = rnd.randint(int(px(20)), int(px(80)))
        h = rnd.randint(int(px(6)), int(px(20)))
        tone = rnd.randint(22, 40)
        d.polygon([(x, y), (x + w, y + rnd.randint(-3, 3)),
                   (x + w + rnd.randint(-4, 4), y + h),
                   (x + rnd.randint(-3, 3), y + h)],
                  fill=(tone, tone + 1, tone))
    base = log(base, CX - px(150), FLOOR_Y + px(14), px(150), px(11), seed=3)
    ring(base)
    base = demon(base, CX + px(146), FLOOR_Y - px(150), px(62), px(56))
    base = trunk(base, CX - px(176), px(34), px(58), seed=2, sway=-1)
    base = trunk(base, CX + px(198), px(30), px(52), seed=5, sway=1)
    ceiling(base)
    base = roots(base)
    base = puddle(base, CX - px(72), FLOOR_Y + px(32), px(46), px(13), seed=3)
    base = puddle(base, CX + px(150), FLOOR_Y + px(40), px(58), px(15), seed=8)

    base = hd.shade(base, [
        (hd.light(RING_CX, RING_CY, px(120), (66, 210, 128), 92), px(12), 1.2),
        (hd.light(RING_CX, CEILING + px(30), px(80), (52, 176, 110), 54), px(10), 1.0),
        (hd.light(RING_CX, px(120), px(300), (44, 150, 104), 40), px(16), 1.0),
        (hd.light(CX - px(176), FLOOR_Y - px(300), px(120), (70, 190, 130), 38),
         px(12), 1.0),
        (hd.light(CX + px(146), FLOOR_Y - px(152), px(44), (188, 30, 22), 62),
         px(8), 1.1),
        (hd.light(CX - px(150), FLOOR_Y + px(10), px(60), (36, 96, 70), 26),
         px(12), 1.0),
    ])
    base = shaft(base)
    base = mist(base)
    base = hd.finish(base, 9, 5, 0.44, FLOOR_Y)
    base = shaft(base)

    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    for i in range(px(20)):
        a = int(190 * (1 - i / px(20)) ** 1.4)
        fd.line([(0, H - i), (W, H - i)], fill=(4, 6, 5, a))
    for cx, w in ((CX - px(168), px(120)), (CX + px(196), px(104))):
        fd.polygon([(cx - w, H), (cx - w * 0.5, H - px(24)),
                    (cx + w * 0.4, H - px(18)), (cx + w, H)],
                   fill=(7, 9, 8, 232))
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, fg, 1)]


def main():
    hd.STAGES["the_upside_down"] = ("The Upside Down", paint)
    hd.build("the_upside_down")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
