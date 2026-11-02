"""HD (1280x960) procedural stages for Big Trouble in Little China.

tools/build_stages.py paints at arcade resolution (localcoord 320x240), so a
1080p window shows a 240-line image stretched across 1080 rows. This module
paints the same four arenas at four times that resolution and writes the same
stages/<id>.def + .sff pair with localcoord 1280x960.

Why 1280x960 and not 1280x720: Ikemen derives the vertical framing from the
stage's localcoord height. src/camera.go does

    cutlow = (localcoord[1] - zoffset) - localcoord[1] * 0.05

so a 960-row canvas with zoffset 800 only resolves when localcoord[1] is 960
(arcade: 240 with zoffset 200). With localcoord 720 the floor sits past the
bottom of the coordinate space and the whole backdrop is framed wrong.

Everything derives from one SCALE constant, so arena geometry matches the
arcade stages exactly:

    canvas       4000 x 960   (camera travel 2080 + 960 overpaint each side)
    camera       boundleft/right +/-1040
    players      leftbound/rightbound +/-1620, 60 px inside the painted edge
    floor        zoffset 800; art row 800 of 960 is the ground line
    localcoord   1280, 960

A stage with real art in art_src/<id>/backdrop.png still wins, because
tools/build_hd_stage.py runs after this and overwrites the same files.

Run:  python3 tools/stages_hd.py          (part of tools/build_all.py)
"""

from __future__ import annotations

import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCALE = 4.5
LOCAL_W, LOCAL_H = 1920, 1080
S = SCALE
H = int(240 * S)                         # 1080 painted height
SCROLL = 3136                            # camera travel each way
# Reach of the view from centre at the far camera limit: the camera stops
# SCROLL out and the screen is LOCAL_W wide, so the art has to run SCROLL +
# LOCAL_W each side of centre. It used to stop at SCROLL + 1012, and that is
# exactly why a wide window (21:9, 32:9) showed black bars down both edges: the
# screen ran past the end of the canvas, so the hall looked like a card pasted
# into the middle of the stage instead of the stage itself.
OVERSCAN = 96                            # slack for aspect and rounding
HALF_SPAN = SCROLL + LOCAL_W // 2        # 4096: art reach each side
# The canvas now ends exactly where the camera stops, so the outer art is
# reachable instead of painted and then locked away: at full pan the screen
# edge meets the canvas edge. It used to be SCROLL + LOCAL_W + OVERSCAN, which
# put a whole extra view of art past the camera limit - the front of the rig on
# Pork Chop Express sat out there, and walking to the screen edge just stopped.
W = 2 * HALF_SPAN                        # 8192: full stage canvas
CX = W // 2                              # 4096
FLOOR_Y = int(200 * S)                   # 900: ground line = zoffset
START_X = -HALF_SPAN                     # -4096: canvas left edge in stage x
PLAYER_BOUND = SCROLL + LOCAL_W // 2 - 68   # 4028: one screen margin in from the edge
SCREEN_MARGIN = int(round(15 * S))       # 68
VIEW_W = int(LOCAL_H * 16 / 9)           # 1707: what a 16:9 window shows
# The VS / select stage card. Those screens draw it at stage.portrait.scale
# = .4 inside a motif whose localcoord is 1280x720, and a stage sprite is
# scaled by motif.localcoord[1] / stage.localcoord[1] = 1280/1920, so one art
# pixel lands on .4 * 1280/1920 = .2667 screen pixels. The card window is
# 477,516,801,622 - 324x106 - and wants 1215x398 of art to fill it exactly.
PREVIEW_W, PREVIEW_H = 1215, 398


# ------------------------------------------------------------------ primitives
def px(n):
    """Arcade pixel -> HD units, so painters read like the 320x240 versions."""
    return int(round(n * S))


def blank(stops):
    """Vertical gradient over the full canvas. stops are arcade-space rows."""
    return art.vgrad((W, H), [(int(y * S), c) for y, c in stops])


def shade(base, layers):
    """Screen-blend light layers onto base (see art.screen for ordering)."""
    for layer, radius, gain in layers:
        base = art.screen(base, layer, glow_radius=radius, gain=gain)
    return base


def light(cx, cy, r, color, peak=150):
    """Soft round pool of light, HD coordinates."""
    return art.radial_light((W, H), (cx, cy), r, color, peak)


def arch(d, cx, y_base, w, h, color):
    """Segmental arch: straight jambs and an elliptical head h tall overall."""
    r = w / 2
    spring = y_base - h / 2
    d.rectangle([cx - r, spring, cx + r, y_base], fill=color)
    d.chord([cx - r, y_base - h, cx + r, y_base], 180, 360, fill=color)


def column(d, cx, y_top, y_bot, w, body, edge, cap=None):
    """Fluted column with a plinth and capital, width in HD units."""
    d.rectangle([cx - w / 2, y_top, cx + w / 2, y_bot], fill=body)
    for k in range(1, 4):
        x = cx - w / 2 + w * k / 4
        d.line([(x, y_top), (x, y_bot)], fill=edge, width=max(2, int(w * 0.05)))
    d.rectangle([cx - w / 2 - w * 0.12, y_top - w * 0.18, cx + w / 2 + w * 0.12, y_top],
                fill=cap or body)
    d.rectangle([cx - w / 2 - w * 0.16, y_bot - w * 0.22, cx + w / 2 + w * 0.16, y_bot],
                fill=cap or body)


def hang_lantern(d, cx, cy, r, body=(202, 40, 36), cap=(232, 192, 102)):
    """Paper lantern; radius in HD units."""
    d.line([(cx, cy - r * 3.0), (cx, cy - r * 0.95)], fill=(48, 38, 32),
           width=max(2, int(r * 0.06)))
    d.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], fill=body)
    for k in range(-2, 3):
        rx = r * (0.42 + 0.18 * abs(k))
        d.arc([cx - rx, cy - r * 0.8, cx + rx, cy + r * 0.8], -74, 74,
              fill=(150, 22, 22), width=max(1, int(r * 0.06)))
    d.rectangle([cx - r * 0.34, cy - r * 0.99, cx + r * 0.34, cy - r * 0.66], fill=cap)
    d.rectangle([cx - r * 0.34, cy + r * 0.66, cx + r * 0.34, cy + r * 0.99], fill=cap)


def stone(d, x0, y0, x1, y1, base, mortar, rows=40, seed=4, jitter=0.35):
    """Masonry fill: one block at a time, each a slightly different tone."""
    rnd = random.Random(seed)
    d.rectangle([x0, y0, x1, y1], fill=mortar)
    row_h = max(4.0, (y1 - y0) / rows)
    gap = max(1.0, row_h * 0.09)
    y, shift = y0, False
    while y < y1:
        x = x0 - (row_h * (1.6 if shift else 0.2))
        while x < x1:
            w = row_h * rnd.uniform(1.6, 1.6 + 4.8 * jitter)
            tone = rnd.randint(-11, 11)
            y2 = min(y1, y + row_h)
            x2 = min(x1, x + w)
            if y2 - gap > y + gap and x2 - gap > x + gap:
                d.rectangle([x + gap, y + gap, x2 - gap, y2 - gap],
                            fill=tuple(max(0, min(255, c + tone)) for c in base))
            x += w
        y += row_h
        shift = not shift


def glyph(d, x, y, size, color, seed=0, width=None):
    art.fake_glyph(d, x, y, size, color, seed=seed, width=width)


def banner(d, cx, y_top, w, h, cloth=(126, 22, 24), trim=(214, 172, 96), seed=0):
    d.polygon([(cx - w / 2, y_top), (cx + w / 2, y_top),
               (cx + w / 2, y_top + h), (cx, y_top + h + w * 0.35),
               (cx - w / 2, y_top + h)], fill=cloth)
    d.line([(cx - w / 2, y_top), (cx + w / 2, y_top)], fill=trim, width=max(2, int(w * 0.06)))
    for i in range(3):
        glyph(d, cx - w * 0.28, y_top + h * 0.14 + i * h * 0.26, w * 0.56,
              trim, seed=seed + i, width=max(2, int(w * 0.07)))


def skull(d, cx, y_top, w, h, bone=(206, 198, 176), shadow=(150, 142, 124)):
    """Frontal skull relief w wide and h tall, top edge at y_top."""
    cr_h = h * 0.60
    # cranium, then the temple shading that gives it depth
    d.ellipse([cx - w / 2, y_top, cx + w / 2, y_top + cr_h * 1.5], fill=bone)
    d.chord([cx - w / 2, y_top + cr_h * 0.05, cx + w / 2, y_top + cr_h * 0.95],
            195, 345, fill=shadow)
    # cheekbones tapering into the jaw
    d.polygon([(cx - w * 0.44, y_top + cr_h * 0.62), (cx - w * 0.30, y_top + h),
               (cx + w * 0.30, y_top + h), (cx + w * 0.44, y_top + cr_h * 0.62)],
              fill=bone)
    d.polygon([(cx - w * 0.20, y_top + h), (cx + w * 0.20, y_top + h),
               (cx + w * 0.16, y_top + h * 0.94), (cx - w * 0.16, y_top + h * 0.94)],
              fill=shadow)
    # eye sockets, angled inward, with a green ember inside
    for sx in (-1, 1):
        ex = cx + sx * w * 0.225
        ey = y_top + cr_h * 0.50
        d.ellipse([ex - w * 0.140, ey - w * 0.108, ex + w * 0.140, ey + w * 0.098],
                  fill=(26, 20, 20))
        d.ellipse([ex - w * 0.105, ey - w * 0.078, ex + w * 0.105, ey + w * 0.072],
                  fill=(9, 8, 9))
        d.ellipse([ex - w * 0.048, ey - w * 0.032, ex + w * 0.048, ey + w * 0.034],
                  fill=(40, 204, 106))
    # nasal cavity
    d.polygon([(cx, y_top + cr_h * 0.70), (cx - w * 0.085, y_top + cr_h * 1.02),
               (cx + w * 0.085, y_top + cr_h * 1.02)], fill=(11, 9, 10))
    # teeth band with vertical grooves
    tb = y_top + h * 0.86
    d.rectangle([cx - w * 0.27, tb, cx + w * 0.27, y_top + h], fill=(226, 220, 200))
    for i in range(-4, 5):
        tx = cx + i * w * 0.06
        d.line([(tx, tb), (tx, y_top + h)], fill=(128, 120, 104), width=max(2, int(w * 0.012)))
    d.line([(cx - w * 0.27, tb), (cx + w * 0.27, tb)], fill=(96, 88, 76),
           width=max(2, int(w * 0.012)))


def texture(img, strength=0.20, cell=46, seed=3):
    """Multiply a soft, blotchy noise over the art so surfaces read as material."""
    rnd = random.Random(seed)
    small = (max(2, W // cell), max(2, H // cell))
    noise = Image.effect_noise(small, 44).resize((W, H), Image.BILINEAR)
    noise = noise.point(lambda v: 128 + (v - 128) * 3)
    noise = noise.rotate(rnd.uniform(0, 90), resample=Image.BILINEAR)
    shade_map = Image.blend(Image.new("L", (W, H), 255), noise, strength)
    r, g, b, a = img.split()
    return Image.merge("RGBA", (ImageChops.multiply(r, shade_map),
                                ImageChops.multiply(g, shade_map),
                                ImageChops.multiply(b, shade_map), a))


def bloom(img, threshold=170, radius=18, gain=0.55):
    """Blur the brightest pixels back over the frame: lanterns and neon glow."""
    lum = img.convert("L").point(lambda v: max(0, v - threshold) * 255 // max(1, 255 - threshold))
    mask = lum.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: int(v * gain))
    halo = img.copy()
    halo.putalpha(mask)
    return art.screen(img, halo, glow_radius=radius * 2, gain=gain)


def seam(img, y):
    """Contact shadow where the wall meets the floor, plus a floor falloff."""
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(band)
    for i in range(int(px(22))):
        a = int(150 * (1 - i / px(22)) ** 2)
        d.line([(0, y - i), (W, y - i)], fill=(4, 3, 4, a))
    for i in range(int(px(6))):
        a = int(90 * (1 - i / px(6)))
        d.line([(0, y + i), (W, y + i)], fill=(0, 0, 0, a))
    return Image.alpha_composite(img, band.filter(ImageFilter.GaussianBlur(px(3))))


def finish(img, seed=7, amount=4, vig=0.6, floor=None):
    if floor is not None:
        img = seam(img, floor)
    img = texture(img, 0.20, 46, seed)
    img = bloom(img, 172, px(4), 0.6)
    return art.grain(art.vignette(img, vig), amount, seed=seed)


# ------------------------------------------------------------- Lo Pan's Throne
def stage_throne():
    base = blank([
        (0, (14, 8, 10)), (60, (58, 27, 22)), (120, (40, 20, 18)),
        (170, (30, 17, 16)), (200, (22, 15, 15)), (240, (9, 7, 9)),
    ])
    d = ImageDraw.Draw(base)

    # hall masonry, then the coffered ceiling band
    stone(d, 0, 0, W, FLOOR_Y, (44, 32, 30), (26, 19, 18), rows=42)
    for x in range(0, W, px(48)):
        d.rectangle([x + px(4), px(6), x + px(44), px(26)], fill=(30, 20, 19))

    # columns framing the gate
    for cx in (CX - px(150), CX + px(150)):
        column(d, cx, px(70), FLOOR_Y, px(30), (104, 86, 70), (68, 54, 44),
               cap=(126, 104, 84))
        d.rectangle([cx + px(6), px(70), cx + px(15), FLOOR_Y], fill=(84, 68, 56))

    # arch spanning them
    arch(d, CX, px(112), px(300), px(64), (108, 90, 74))
    arch(d, CX, px(112), px(282), px(56), (24, 16, 16))

    # gate: stone lintel and jambs around a skull relief
    gw, gh = px(48), px(122)          # gw is the half-width
    gx, gy = CX, FLOOR_Y - px(2)
    d.rectangle([gx - gw, gy - gh, gx + gw, gy], fill=(62, 50, 42))
    d.rectangle([gx - gw, gy - gh, gx + gw, gy], outline=(96, 78, 60), width=px(3))
    d.rectangle([gx - gw + px(6), gy - gh + px(6), gx + gw - px(6), gy],
                fill=(14, 10, 11))

    # skull relief inside the gate
    sk_w, sk_h = px(68), px(86)
    skull(d, gx, gy - gh + px(10), sk_w, sk_h)

    # censers flanking the gate
    for sx in (-1, 1):
        bx = gx + sx * px(120)
        d.polygon([(bx - px(16), gy - px(34)), (bx + px(16), gy - px(34)),
                   (bx + px(10), gy), (bx - px(10), gy)], fill=(74, 58, 34))
        d.ellipse([bx - px(18), gy - px(44), bx + px(18), gy - px(30)], fill=(96, 76, 44))

    # banners between the columns and the gate
    for sx in (-1, 1):
        banner(d, CX + sx * px(112), px(96), px(30), px(96), seed=sx + 3)

    # lanterns under the arch
    for sx in (-1, 1):
        hang_lantern(d, CX + sx * px(72), px(120), px(9))
        hang_lantern(d, CX + sx * px(196), px(104), px(8))

    # floor: slabs in perspective, with a wet sheen
    d.rectangle([0, FLOOR_Y, W, H], fill=(28, 19, 19))
    d.line([(0, FLOOR_Y), (W, FLOOR_Y)], fill=(132, 104, 82), width=px(2))
    for x in range(0, W, px(18)):
        d.line([(x, FLOOR_Y), (x, H)], fill=(21, 15, 15), width=px(1))
    for y in range(FLOOR_Y + px(8), H, px(10)):
        d.line([(0, y), (W, y)], fill=(24, 17, 17), width=px(1))
    base = art.wet_floor(base, FLOOR_Y + px(3), (188, 104, 78), 26, seed=9, bands=150)

    # light: warm torches on the floor, green spill from the gate, hazy centre
    base = shade(base, [
        (light(CX, gy - px(56), px(70), (52, 226, 120), 116), 28, 1.4),
        (light(CX - px(150), FLOOR_Y - px(22), px(88), (238, 152, 80), 100), 32, 1.1),
        (light(CX + px(150), FLOOR_Y - px(22), px(88), (238, 152, 80), 100), 32, 1.1),
        (light(CX - px(74), FLOOR_Y + px(14), px(78), (204, 122, 62), 74), 40, 1.0),
        (light(CX + px(74), FLOOR_Y + px(14), px(78), (204, 122, 62), 74), 40, 1.0),
    ])

    # foreground: dark lip of the dais across the bottom
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    fd.rectangle([0, H - px(10), W, H], fill=(7, 6, 9))
    for x in range(px(8), W, px(60)):
        fd.rectangle([x, H - px(26), x + px(3), H - px(4)], fill=(10, 9, 12))
    return [("bg", 0, 0, finish(base, 5, 3, 0.62, FLOOR_Y), 0),
            ("fg", 3, 0, fg, 1)]


# ---------------------------------------------------------- Wing Kong Exchange
def stage_wingkong():
    base = blank([
        (0, (11, 13, 19)), (80, (26, 28, 37)), (160, (34, 32, 39)),
        (200, (29, 27, 33)), (240, (13, 13, 18)),
    ])
    d = ImageDraw.Draw(base)

    # back wall and the roller door
    stone(d, 0, 0, W, px(60), (40, 38, 44), (26, 25, 30), rows=14, seed=8)
    d.rectangle([0, px(58), W, FLOOR_Y], fill=(42, 40, 47))
    for y in range(px(64), FLOOR_Y, px(5)):
        d.line([(0, y), (W, y)], fill=(32, 31, 36), width=px(1))
    for x in range(0, W, px(76)):
        d.rectangle([x, px(54), x + px(5), FLOOR_Y], fill=(56, 54, 62))
        d.rectangle([x - px(2), px(54), x + px(7), px(64)], fill=(48, 46, 54))

    # stacked crates and drums
    rnd = random.Random(11)
    for x in range(px(18), W, px(50)):
        for row in range(rnd.randint(1, 3)):
            cw, chh = px(32), px(24)
            y = FLOOR_Y - (row + 1) * chh
            tone = rnd.randint(-8, 8)
            d.rectangle([x, y, x + cw, y + chh],
                        fill=(88 + tone, 68 + tone, 46 + tone))
            d.rectangle([x, y, x + cw, y + chh], outline=(56, 42, 28), width=px(1))
            d.line([(x, y), (x + cw, y + chh)], fill=(56, 42, 28), width=px(1))
            d.line([(x + cw, y), (x, y + chh)], fill=(56, 42, 28), width=px(1))
    for x in range(px(38), W, px(52)):
        d.rectangle([x, FLOOR_Y - px(18), x + px(14), FLOOR_Y], fill=(74, 96, 88))
        for k in range(3):
            d.line([(x, FLOOR_Y - px(14) + k * px(5)), (x + px(14), FLOOR_Y - px(14) + k * px(5))],
                   fill=(58, 78, 72), width=px(1))
        d.ellipse([x, FLOOR_Y - px(20), x + px(14), FLOOR_Y - px(15)], fill=(92, 116, 104))

    # hanging work lamps
    for cx in (CX - px(150), CX, CX + px(150)):
        d.line([(cx, px(58)), (cx, px(104))], fill=(28, 28, 32), width=px(1))
        d.ellipse([cx - px(11), px(104), cx + px(11), px(112)], fill=(120, 122, 128))

    # neon signage
    sign = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sign)
    f = art.font(px(9))
    for sx, txt in ((CX - px(126), "WING KONG"), (CX + px(14), "EXCHANGE")):
        box = [sx, px(26), sx + px(100), px(26) + px(26)]
        sd.rectangle(box, fill=(22, 11, 15, 240))
        sd.rectangle(box, outline=(255, 66, 66, 255), width=px(1))
        sd.text((sx + px(6), px(31)), txt, font=f, fill=(255, 110, 110, 255))
    base = art.screen(base, sign, glow_radius=26, gain=1.6)

    # wet dock floor
    d = ImageDraw.Draw(base)
    d.rectangle([0, FLOOR_Y, W, H], fill=(35, 35, 42))
    d.line([(0, FLOOR_Y), (W, FLOOR_Y)], fill=(104, 104, 112), width=px(2))
    for x in range(0, W, px(24)):
        d.line([(x, FLOOR_Y), (x + px(6), H)], fill=(46, 46, 54), width=px(1))
    base = art.wet_floor(base, FLOOR_Y + px(2), (128, 176, 216), 30, seed=13, bands=170)
    base = shade(base, [
        (light(CX - px(150), FLOOR_Y - px(10), px(90), (255, 214, 160), 110), 34, 1.0),
        (light(CX, FLOOR_Y - px(10), px(90), (255, 214, 160), 110), 34, 1.0),
        (light(CX + px(150), FLOOR_Y - px(10), px(90), (255, 214, 160), 110), 34, 1.0),
    ])
    base = art.rain(base, count=560, length=(px(6), px(16)), color=(152, 188, 222),
                    alpha=52, seed=5)

    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    fd.rectangle([0, H - px(12), W, H], fill=(8, 8, 11))
    for x in range(0, W, px(54)):
        fd.rectangle([x, H - px(40), x + px(3), H], fill=(12, 12, 16))
    return [("bg", 0, 0, finish(base, 11, 4, 0.55, FLOOR_Y), 0),
            ("fg", 3, 0, fg, 1)]


# --------------------------------------------------------- Chinatown back alley
def stage_alley():
    base = blank([
        (0, (16, 11, 19)), (80, (40, 23, 29)), (150, (50, 29, 33)),
        (200, (38, 24, 28)), (240, (11, 9, 13)),
    ])
    d = ImageDraw.Draw(base)
    stone(d, 0, 0, W, FLOOR_Y - px(8), (54, 38, 38), (32, 24, 24), rows=52, seed=23)

    # storefronts: lit windows and doorways at street level
    rnd = random.Random(31)
    for x in range(px(6), W, px(64)):
        wy = FLOOR_Y - px(96)
        d.rectangle([x, wy, x + px(46), wy + px(38)], fill=(34, 26, 26))
        glowc = rnd.choice([(224, 176, 92), (196, 96, 92), (150, 190, 200)])
        d.rectangle([x + px(4), wy + px(4), x + px(42), wy + px(34)], fill=glowc)
        d.line([(x + px(23), wy + px(4)), (x + px(23), wy + px(34))],
               fill=(34, 26, 26), width=px(2))
        d.rectangle([x + px(6), FLOOR_Y - px(50), x + px(30), FLOOR_Y], fill=(26, 20, 22))

    # awnings
    for x in range(0, W, px(64)):
        d.polygon([(x, FLOOR_Y - px(100)), (x + px(52), FLOOR_Y - px(100)),
                   (x + px(46), FLOOR_Y - px(86)), (x + px(6), FLOOR_Y - px(86))],
                  fill=(96, 30, 32))

    # hanging vertical shop signs
    for i, x in enumerate(range(px(14), W, px(62))):
        h = px(rnd.randint(44, 64))
        y = px(16)
        d.rectangle([x - px(1), y - px(3), x + px(12), y + h + px(3)], fill=(146, 176, 160))
        d.rectangle([x, y, x + px(11), y + h], fill=(126, 26, 28))
        d.rectangle([x, y, x + px(11), y + h], outline=(216, 176, 96), width=px(1))
        for k in range(4):
            glyph(d, x + px(2), y + px(4) + k * (h / 4.3), px(7),
                  (236, 212, 156), seed=i * 7 + k, width=px(1))

    # lanterns strung over the alley
    for i, x in enumerate(range(0, W, px(38))):
        hang_lantern(d, x + px(18), px(38) + (i % 3) * px(6), px(6))

    # steam rolling along the ground
    steam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(steam)
    for x in range(px(30), W, px(82)):
        sd.ellipse([x, FLOOR_Y - px(44), x + px(36), FLOOR_Y - px(2)],
                   fill=(192, 192, 204, 30))
    base = Image.alpha_composite(base, steam.filter(ImageFilter.GaussianBlur(px(7))))

    d = ImageDraw.Draw(base)
    d.rectangle([0, FLOOR_Y, W, H], fill=(31, 25, 29))
    d.line([(0, FLOOR_Y), (W, FLOOR_Y)], fill=(104, 94, 96), width=px(2))
    for x in range(0, W, px(30)):
        d.line([(x, FLOOR_Y), (x + px(8), H)], fill=(39, 32, 36), width=px(1))
    base = art.wet_floor(base, FLOOR_Y + px(1), (158, 128, 116), 34, seed=31, bands=180)
    base = shade(base, [
        (light(CX - px(90), FLOOR_Y - px(6), px(70), (240, 170, 90), 90), 30, 1.0),
        (light(CX + px(90), FLOOR_Y - px(6), px(70), (240, 170, 90), 90), 30, 1.0),
    ])
    base = art.rain(base, count=400, length=(px(4), px(9)), color=(162, 172, 192),
                    alpha=40, seed=17, angle=-0.18)

    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    fd.rectangle([0, H - px(10), W, H], fill=(7, 6, 9))
    return [("bg", 0, 0, finish(base, 19, 5, 0.58, FLOOR_Y), 0),
            ("fg", 3, 0, fg, 1)]


# ------------------------------------------------------------ Pork Chop Express
# ---------------------------------------------------------------------------
# Pork Chop Express: the fight happens on the back of the rig.
#
# A 2D fighting stage cannot move a platform, so the platform is the frame of
# reference instead: the flatbed deck IS the floor plane (zoffset), and the
# highway is a separate strip that is tiled infinitely and given its own
# velocity, so it slides while the rig stays put under the fighters. Positive
# velocity on the road means the world travels right, which is a truck
# travelling left.
# ---------------------------------------------------------------------------

RAIL_TOP = FLOOR_Y - 40                  # 860 = LIP_TOP: the rail is this band
PANEL_BOT = FLOOR_Y + px(30)             # 1035: deck side meets the chassis
ROAD_TILE = 1400                         # px; every spacing below divides it
ROAD_VEL = 16                            # px/tick rightwards
ROAD_DELTA = 0.9
ROAD_TOP = FLOOR_Y - px(30)              # 765: the wall's road line
# Painted from the concept art in concept_art/stages/porkchop_express: the
# licensed model of the film's tractor. White coachwork, a blue cheat line
# edged in gold, a blue-and-gold chequered chevron raking up the sleeper,
# "BURTON TRUCKING" on the door, a ribbed chrome grille, ribbed chrome stacks,
# and a black timber flatbed trailer on tandem axles.
BODY, BODY_DK = (238, 238, 234), (198, 200, 203)
BLUE, BLUE_DK = (32, 58, 134), (19, 36, 92)
GOLD, GOLD_DK = (214, 168, 62), (146, 108, 32)
CHROME, CHROME_HI = (194, 198, 206), (240, 244, 250)
DECK_LT, DECK = (96, 78, 61), (58, 46, 37)
STEEL, STEEL_DK, STEEL_LT = (58, 60, 68), (26, 27, 33), (104, 107, 116)
CAB_TOP = FLOOR_Y - px(96)               # 468: sleeper roof
CAB_W = px(156)                          # 702 wide
# delta is measured against the world, so a delta-1 layer maps 1:1 onto the
# canvas and the camera simply crops it: the sprite's LEFT end is what you see
# when the camera is at its left bound. The cab sits there, the bed's tail at
# the right end.
CAB_SPRITE_X = px(104)                   # 468
TAIL_W = px(68)                          # 306: the bed's rear header board
BED_X0 = px(300)                         # 1350: the flatbed starts here, behind the tractor
FAR_RAIL_TOP = FLOOR_Y - px(19)          # 814: the far stake rail
FAR_RAIL_BOT = FLOOR_Y - px(15)          # 832: the deck runs from here to the near rail


def _grad(d, y0, y1, c0, c1, x0=0, x1=W):
    span = max(1, int(round(y1 - y0)))
    for i in range(span):
        t = i / float(span - 1) if span > 1 else 0.0
        d.line([(x0, y0 + i), (x1, y0 + i)],
               fill=tuple(int(c0[k] + (c1[k] - c0[k]) * t) for k in range(3)) + (255,))


class _Zoom:
    """ImageDraw proxy that scales every coordinate by `k` about (ox, oy).

    A shape rasterised at 1x gives a diagonal or an arc a staircase edge. Drawn
    at 2x and resampled back down, the same shape reads as a drawn panel, which
    is most of the difference between a painted truck and a diagram of one.
    """

    def __init__(self, d, k, ox=0.0, oy=0.0):
        self.d, self.k, self.ox, self.oy = d, float(k), float(ox), float(oy)

    def _xy(self, xy):
        if xy and isinstance(xy[0], (tuple, list)):
            return [((p[0] - self.ox) * self.k, (p[1] - self.oy) * self.k) for p in xy]
        out = []
        for i in range(0, len(xy) - 1, 2):
            out.append((xy[i] - self.ox) * self.k)
            out.append((xy[i + 1] - self.oy) * self.k)
        return out

    def _kw(self, kw):
        # A line with no width asked for is one pixel wide, which at 2x covers
        # only one of the two rows it is scaled across: the row pair then
        # averages opaque against transparent and the whole panel comes out at
        # half alpha. Every stroke is scaled, including the default width.
        w = kw.get("width") or 1
        kw["width"] = max(1, int(round(w * self.k)))
        if kw.get("radius"):
            kw["radius"] = kw["radius"] * self.k
        return kw

    def rectangle(self, xy, **kw):
        self.d.rectangle(self._xy(xy), **self._kw(kw))

    def rounded_rectangle(self, xy, **kw):
        self.d.rounded_rectangle(self._xy(xy), **self._kw(kw))

    def ellipse(self, xy, **kw):
        self.d.ellipse(self._xy(xy), **self._kw(kw))

    def polygon(self, xy, **kw):
        self.d.polygon(self._xy(xy), **self._kw(kw))

    def line(self, xy, **kw):
        self.d.line(self._xy(xy), **self._kw(kw))

    def arc(self, xy, start=0, end=360, **kw):
        self.d.arc(self._xy(xy), start, end, **self._kw(kw))

    def pieslice(self, xy, start=0, end=360, **kw):
        self.d.pieslice(self._xy(xy), start, end, **self._kw(kw))


def _vgrad(z, y0, y1, c0, c1, x0, x1):
    """A vertical light falloff between two colours, one band per pixel."""
    n = max(1, int(round(y1 - y0)))
    for i in range(n):
        t = i / float(n - 1) if n > 1 else 0.0
        z.line([(x0, y0 + i), (x1, y0 + i)],
               fill=tuple(int(c0[k] + (c1[k] - c0[k]) * t) for k in range(3)) + (255,))


def _wheel(d, cx, cy, r):
    """A wheel seen from the side: tyre, sidewall, polished rim, lug nuts.

    Every axle on the rig calls this with the same centre line and the same
    radius, so a mismatched wheel is impossible, not just unlikely.
    """
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(14, 14, 18))
    d.ellipse([cx - r * 0.90, cy - r * 0.90, cx + r * 0.90, cy + r * 0.90], fill=(38, 39, 46))
    d.ellipse([cx - r * 0.78, cy - r * 0.78, cx + r * 0.78, cy + r * 0.78], fill=(24, 24, 30))
    for i in range(28):
        a = i * math.pi / 14.0
        d.line([(cx + math.cos(a) * r * 0.90, cy + math.sin(a) * r * 0.90),
                (cx + math.cos(a) * r * 1.0, cy + math.sin(a) * r * 1.0)],
               fill=(52, 53, 62), width=max(1, int(r * 0.07)))
    d.ellipse([cx - r * 0.62, cy - r * 0.62, cx + r * 0.62, cy + r * 0.62], fill=(118, 122, 132))
    d.ellipse([cx - r * 0.58, cy - r * 0.58, cx + r * 0.58, cy + r * 0.58], fill=(198, 202, 212))
    d.ellipse([cx - r * 0.46, cy - r * 0.46, cx + r * 0.46, cy + r * 0.46], fill=(146, 150, 161))
    for i in range(8):
        a = i * math.pi / 4.0 + 0.4
        lx, ly = cx + math.cos(a) * r * 0.32, cy + math.sin(a) * r * 0.32
        d.ellipse([lx - r * 0.06, ly - r * 0.06, lx + r * 0.06, ly + r * 0.06],
                  fill=(66, 68, 78))
    d.ellipse([cx - r * 0.19, cy - r * 0.19, cx + r * 0.19, cy + r * 0.19],
              fill=(206, 210, 218))
    d.ellipse([cx - r * 0.08, cy - r * 0.08, cx + r * 0.08, cy + r * 0.08],
              fill=(104, 108, 118))


def _fender(z, cx, cy, r):
    """A wheel arch drawn just outside the cut wheel well, so the band hugs the
    tyre instead of lying over it, with a lit outer lip."""
    z.arc([cx - r, cy - r, cx + r, cy + r], 212, 328, fill=BODY, width=px(7))
    z.arc([cx - r, cy - r, cx + r, cy + r], 212, 328, fill=(252, 253, 254), width=px(2.5))


def _stack(z, x, y_top, y_bot, w):
    """A chrome stack: pipe, a louvred heat shield, and a cut-back tip."""
    z.rectangle([x, y_top, x + w, y_bot], fill=(148, 152, 162))
    z.rectangle([x, y_top, x + w * 0.34, y_bot], fill=(224, 228, 238))
    z.rectangle([x + w * 0.74, y_top, x + w, y_bot], fill=(104, 108, 118))
    sy0 = y_top + (y_bot - y_top) * 0.30
    sy1 = y_top + (y_bot - y_top) * 0.72
    z.rectangle([x - px(2), sy0, x + w + px(2), sy1], fill=(176, 180, 190))
    z.rectangle([x - px(2), sy0, x + w * 0.34, sy1], fill=(238, 242, 250))
    for i in range(4):
        yy = sy0 + (sy1 - sy0) * (i + 0.5) / 4.0
        z.line([(x - px(2), yy), (x + w + px(2), yy)], fill=(128, 132, 142),
               width=max(1, w * 0.12))
    z.polygon([(x - px(1), y_top - px(6)), (x + w + px(1), y_top - px(6)),
               (x + w + px(1), y_top - px(2)), (x - px(1), y_top + px(2))],
              fill=(238, 242, 250))
    z.rectangle([x - px(1), y_top + px(2), x + w + px(1), y_top + px(4)],
                fill=(120, 124, 134))


def _deck(img):
    """The flatbed trailer, as a part of its own, coupled behind the tractor.

    It begins at BED_X0 and runs to the tail: timber planks the fighters stand
    on, the black stake rail behind them, the steel channel at the floor line in
    front of them, the trailer's black side and frame below the deck, and its own
    tandem close together at the back of the bed. Nothing of it is drawn left of
    BED_X0, so the tractor's rear wheels are not painted over by the trailer.
    """
    d = ImageDraw.Draw(img)
    x0 = BED_X0

    # ---- the deck: planks laid across the bed, lit at their far edge
    _grad(d, FAR_RAIL_BOT, FLOOR_Y, DECK_LT, DECK, x0=x0, x1=W)
    for x in range(int(x0), W, int(px(11))):
        d.line([(x, FAR_RAIL_BOT), (x, FLOOR_Y)], fill=(44, 35, 28), width=px(1))
        d.line([(x + px(1), FAR_RAIL_BOT), (x + px(1), FLOOR_Y)],
               fill=(116, 95, 74), width=px(1))
    d.line([(x0, FLOOR_Y - px(2)), (W, FLOOR_Y - px(2))],
           fill=(122, 100, 78), width=px(1))

    # ---- far stake rail: black channel with a worn top edge and stakes on it,
    # so the bed has a back wall for the fighters to stand in front of
    d.rectangle([x0, FAR_RAIL_TOP, W, FAR_RAIL_BOT], fill=STEEL_DK)
    d.rectangle([x0, FAR_RAIL_TOP, W, FAR_RAIL_TOP + px(2)], fill=STEEL_LT)
    for x in range(int(x0 + px(18)), W, int(px(96))):
        d.rectangle([x, FAR_RAIL_TOP - px(3), x + px(6), FAR_RAIL_BOT], fill=(42, 44, 52))
        d.ellipse([x + px(1), FAR_RAIL_TOP - px(2), x + px(5), FAR_RAIL_TOP + px(2)],
                  fill=(128, 131, 140))

    # ---- the near channel: a hard steel edge at the floor line, and a row of
    # bolts where the deck is bolted to it
    _grad(d, FLOOR_Y, FLOOR_Y + px(10), (88, 91, 100), (38, 39, 46), x0=x0, x1=W)
    d.rectangle([x0, FLOOR_Y, W, FLOOR_Y + px(2)], fill=(154, 158, 166))
    for x in range(int(x0 + px(6)), W, int(px(64))):
        d.rectangle([x, FLOOR_Y + px(3), x + px(5), FLOOR_Y + px(10)], fill=(22, 23, 28))
        d.ellipse([x - px(1), FLOOR_Y + px(4), x + px(7), FLOOR_Y + px(10)],
                  fill=(134, 138, 147))

    # ---- the trailer's black side, its frame, and the rail under the bed
    _grad(d, FLOOR_Y + px(10), PANEL_BOT - px(6), STEEL, (36, 37, 43), x0=x0, x1=W)
    for x in range(int(x0), W, int(px(150))):
        d.line([(x, FLOOR_Y + px(12)), (x, PANEL_BOT - px(8))], fill=(74, 77, 85),
               width=px(1))
        for y in (FLOOR_Y + px(16), PANEL_BOT - px(12)):
            d.ellipse([x - px(1), y - px(1), x + px(1), y + px(1)], fill=(98, 102, 110))
    d.rectangle([x0, PANEL_BOT - px(6), W, PANEL_BOT], fill=(20, 20, 25))
    d.rectangle([x0, PANEL_BOT, W, H], fill=(13, 13, 17))
    for x in range(int(x0), W, int(px(74))):
        d.rectangle([x, PANEL_BOT + px(4), x + px(34), PANEL_BOT + px(11)], fill=(26, 27, 32))

    # ---- the trailer's own tandem: two axles close together at the back of the
    # bed, on the same ground line and with the same wheel as the tractor
    WY, R = FLOOR_Y + px(40), px(22)
    for ax in (px(1044), px(1091)):      # 4698, 4910: adjacent, not overlapping
        d.rectangle([ax - px(24), WY - R - px(4), ax + px(24), WY - R], fill=(20, 20, 26))
        _wheel(d, ax, WY, R)

    # ---- cargo lashed down by the tail, clear of the fighting space
    for cx_, r, body in ((W - px(150), px(13), (54, 60, 70)),
                         (W - px(125), px(13), (44, 70, 88))):
        cy = FLOOR_Y - r + px(4)
        d.rectangle([cx_ - r, cy - r, cx_ + r, cy + r], fill=body)
        d.ellipse([cx_ - r, cy - r, cx_ + r, cy + r],
                  fill=tuple(min(255, c + 16) for c in body))
        d.rectangle([cx_ - r, cy - r // 2, cx_ + r, cy + r // 2], fill=(178, 92, 42))
        d.ellipse([cx_ - r, cy - r, cx_ + r, cy + r], outline=(22, 22, 28), width=px(1))


def _cab(img):
    """The tractor in side elevation, painted from the concept art in
    concept_art/stages/porkchop_express: a chrome grille and bumper standing
    proud of the nose, the long white hood under the blue cheat line edged in
    gold, an arch fender over the steer tyre, the door with its Burton Trucking
    sign, the air cleaner on the flank, the twin stacks rising behind the cab,
    and the sleeper carrying the chequered chevron and the pork chop badge.

    The body is painted at 2x and resampled so arcs and diagonals are smooth,
    and each wheel well is cut out of it so the wheels drawn underneath sit in
    a real arch. Everything is placed in units of px(): the cab runs from the
    windscreen at 111 to the back of the sleeper at 267, and the tall panels
    (grille, window, hood, sign) are fractions of that, not fixed offsets.
    """
    ground = FLOOR_Y + px(40)
    R = px(22)
    steer, drive_a, drive_b = px(76), px(215), px(262)     # 342, 968, 1179
    nose, grille0, grille1, hood1 = px(20), px(27), px(46), px(111)
    back_x = px(284)                                        # 1278
    roof, hem = FLOOR_Y - px(98), FLOOR_Y + px(22)          # 459, 999
    belt = FLOOR_Y - px(57)                                 # 645: hood top, window sill

    # ---- frame and running gear on the canvas itself, so the tyres are exact
    d0 = ImageDraw.Draw(img)
    d0.rectangle([nose, hem - px(6), back_x, PANEL_BOT], fill=(24, 25, 31))
    d0.rectangle([nose, hem - px(6), back_x, hem], fill=(46, 48, 56))
    for ax in (steer, drive_a, drive_b):
        _wheel(d0, ax, ground, R)

    # ---- the coachwork, at 2x
    K = 2
    X0, Y0, X1, Y1 = 40, 330, 1430, 1070
    layer = Image.new("RGBA", (int((X1 - X0) * K), int((Y1 - Y0) * K)), (0, 0, 0, 0))
    z = _Zoom(ImageDraw.Draw(layer), K, X0, Y0)

    # ---- the twin stacks first: they rise from behind the cab, so the body
    # covers their lower half and only the chrome above the roof shows
    for sxx in (px(177), px(189)):
        _stack(z, sxx, roof - px(13), hem - px(4), px(6))

    # ---- the body as one lit mass: bright under the roof, shading to grey at
    # the sill, so the panels read as painted metal rather than paper
    _vgrad(z, roof, hem, (250, 251, 252), (218, 220, 224), grille0, back_x)
    z.rectangle([grille0, roof, back_x, roof + px(4)], fill=(253, 254, 255))
    z.rectangle([grille0, hem - px(6), back_x, hem], fill=(178, 181, 188))

    # ---- the hood: a low slab, its top crowning forward to the grille
    _vgrad(z, belt, hem, (248, 249, 251), (219, 221, 225), grille1, hood1)
    z.line([(grille1, belt), (hood1, belt - px(3))], fill=(255, 255, 255), width=px(3))
    z.line([(grille1, belt + px(4)), (hood1, belt + px(1))], fill=(198, 201, 207), width=px(2))
    z.line([(grille1 + px(4), hem - px(4)), (hood1, hem - px(4))], fill=(198, 201, 207), width=px(2))
    z.line([(grille1 + px(6), belt + px(15)), (hood1 - px(2), belt + px(12))],
           fill=(212, 215, 221), width=px(2))
    z.polygon([(grille1 + px(4), belt), (grille1 + px(10), belt - px(9)),
               (grille1 + px(14), belt - px(9)), (grille1 + px(17), belt)],
              fill=(208, 212, 222))

    # ---- the grille: a chrome-framed frontal plane standing proud of the nose
    gy0, gy1 = belt - px(10), hem - px(11)                  # 600, 950
    z.rounded_rectangle([grille0, gy0, grille1, gy1], radius=px(4), fill=(190, 194, 204))
    z.rectangle([grille0 + px(3), gy0 + px(4), grille1 - px(3), gy1 - px(4)], fill=(34, 36, 43))
    slats = 14
    for i in range(slats):
        yy = gy0 + px(6) + (gy1 - gy0 - px(12)) * i / float(slats)
        z.line([(grille0 + px(4), yy), (grille1 - px(4), yy)], fill=(206, 211, 221),
               width=px(1.8))
        z.line([(grille0 + px(4), yy + px(3)), (grille1 - px(4), yy + px(3))],
               fill=(70, 74, 83), width=px(1.4))
    z.rectangle([grille0 + px(2), gy0 + px(2), grille1 - px(2), gy1 - px(2)],
                outline=(240, 244, 251), width=px(2))
    z.line([(grille0 + px(1), gy0 + px(2)), (grille0 + px(1), gy1 - px(2))],
           fill=(248, 250, 253), width=px(3))
    z.rectangle([grille0 + px(5), gy0 + px(26), grille1 - px(5), gy0 + px(36)],
                fill=(214, 217, 226))                       # badge bar
    z.rectangle([grille0 + px(8), gy0 + px(28), grille0 + px(19), gy0 + px(34)], fill=BLUE)

    # ---- bumper: chrome, wrapping the corner, lit along its top
    z.rounded_rectangle([nose - px(2), gy1 + px(2), grille1 + px(6), gy1 + px(15)],
                        radius=px(4), fill=(176, 180, 190))
    z.rectangle([nose - px(2), gy1 + px(2), grille1 + px(6), gy1 + px(6)], fill=(234, 238, 246))
    z.rectangle([nose - px(2), gy1 + px(11), grille1 + px(6), gy1 + px(15)],
                fill=(106, 110, 120))
    z.rectangle([nose + px(2), gy1 + px(5), nose + px(13), gy1 + px(11)], fill=BLUE)

    # ---- the blue light bar on the hood's leading edge, as on the model
    z.rectangle([grille1 + px(2), belt - px(13), grille1 + px(34), belt - px(7)], fill=BLUE)
    for lamp_x in (grille1 + px(5), grille1 + px(20)):
        z.ellipse([lamp_x, belt - px(19), lamp_x + px(9), belt - px(10)], fill=(206, 212, 224))
        z.ellipse([lamp_x + px(2), belt - px(17), lamp_x + px(7), belt - px(12)],
                  fill=(250, 246, 214))

    # ---- cab and sleeper: the roof flat, the front raked back from the cowl
    _vgrad(z, roof, hem, (250, 251, 252), (218, 220, 224), hood1, back_x)
    z.rectangle([hood1, roof, back_x, roof + px(4)], fill=(253, 254, 255))
    z.line([(hood1, roof + px(4)), (back_x, roof + px(4))], fill=(200, 203, 209), width=px(2))
    z.rectangle([hood1, hem - px(6), back_x, hem], fill=(178, 181, 188))

    # the windscreen, raking back from the cowl to a chrome-framed roof edge
    z.polygon([(hood1, belt), (hood1 + px(10), roof + px(3)),
               (hood1 + px(21), roof + px(3)), (hood1 + px(12), belt)],
              fill=(30, 38, 54))
    z.polygon([(hood1 + px(2), belt - px(3)), (hood1 + px(11), roof + px(6)),
               (hood1 + px(17), roof + px(6)), (hood1 + px(9), belt - px(3))],
              fill=(62, 84, 120))
    z.line([(hood1 + px(4), belt - px(8)), (hood1 + px(13), roof + px(9))],
           fill=(150, 180, 214), width=px(3))
    z.line([(hood1 + px(21), roof + px(3)), (hood1 + px(12), belt)],
           fill=(210, 216, 226), width=px(2))
    # a visor over the screen, so the roof edge is not a bare line
    z.polygon([(hood1 - px(2), roof - px(1)), (hood1 + px(18), roof - px(1)),
               (hood1 + px(15), roof + px(5)), (hood1 - px(1), roof + px(5))],
              fill=(216, 220, 228))

    # ---- the door: window, handle, shut lines and the Burton Trucking sign
    door_x, door_r = px(124), px(164)
    z.rectangle([door_x, roof + px(6), door_r, hem - px(8)],
                outline=(206, 209, 215), width=px(2))
    glass_top, glass_bot = roof + px(6), belt - px(3)
    z.rectangle([door_x + px(3), glass_top, door_r - px(3), glass_bot], fill=(26, 32, 46))
    z.rectangle([door_x + px(3), glass_top, door_r - px(3),
                 glass_top + (glass_bot - glass_top) * 0.42], fill=(58, 78, 114))
    z.rectangle([door_x + px(3), roof + px(6), door_r - px(3), belt - px(3)],
                outline=(204, 208, 216), width=px(2))
    z.rectangle([door_r - px(16), belt - px(34), door_r - px(4), belt - px(28)],
                fill=(214, 218, 226))                       # handle
    # the sign plate, its two lines of lettering picked out as small blue ticks
    z.rectangle([door_x + px(4), hem - px(33), door_r - px(4), hem - px(12)],
                fill=(250, 251, 252), outline=(182, 186, 196), width=px(1))
    for row, count in ((0, 9), (1, 6)):
        for i in range(count):
            xx = door_x + px(7) + i * px(6)
            yy = hem - px(29) + row * px(9)
            z.rectangle([xx, yy, xx + px(4), yy + px(6)], fill=BLUE_DK)

    # ---- the cheat line, at hood height and carried the whole length
    z.rectangle([grille1, belt + px(24), back_x, belt + px(31)], fill=GOLD)
    z.rectangle([grille1, belt + px(31), back_x, belt + px(40)], fill=BLUE)
    z.rectangle([grille1, belt + px(40), back_x, belt + px(47)], fill=GOLD)
    z.line([(grille1, belt + px(31)), (back_x, belt + px(31))], fill=BLUE_DK, width=px(2))
    z.line([(grille1, belt + px(40)), (back_x, belt + px(40))], fill=BLUE_DK, width=px(2))
    z.rectangle([hood1, hem - px(18), back_x, hem - px(13)], fill=BLUE)
    for gx in (hood1, door_x, door_r, px(196)):
        z.line([(gx, roof + px(4)), (gx, hem - px(6))], fill=(158, 162, 170), width=px(2))

    # ---- the sleeper: the chequered chevron in real rhombi, and the pig badge
    for row in range(2):
        for i in range(13):
            cxq = px(202) + i * px(7) + row * px(3.5)
            cyq = roof + px(44) + i * px(7)
            if cyq > hem - px(34):
                continue
            col = BLUE if (i + row) % 2 == 0 else GOLD
            z.polygon([(cxq, cyq - px(3.5)), (cxq + px(3.5), cyq),
                       (cxq, cyq + px(3.5)), (cxq - px(3.5), cyq)], fill=col)
    bxc, byc = px(232), hem - px(26)
    z.ellipse([bxc - px(12), byc - px(12), bxc + px(12), byc + px(12)], fill=(240, 242, 246))
    z.ellipse([bxc - px(12), byc - px(12), bxc + px(12), byc + px(12)],
              outline=(152, 156, 166), width=px(2))
    z.polygon([(bxc - px(8), byc + px(1)), (bxc - px(4), byc - px(4)),
               (bxc + px(1), byc - px(6)), (bxc + px(6), byc - px(4)),
               (bxc + px(9), byc), (bxc + px(6), byc + px(5)),
               (bxc - px(1), byc + px(6)), (bxc - px(5), byc + px(4))],
              fill=(214, 168, 62))
    z.ellipse([bxc - px(5), byc - px(3), bxc + px(1), byc + px(2)], fill=(232, 146, 146))
    z.polygon([(bxc - px(5), byc - px(3)), (bxc - px(8), byc - px(6)),
               (bxc - px(3), byc - px(5))], fill=(232, 146, 146))

    # ---- the air cleaner on the cab's flank, behind the door
    ac_x = px(166)
    z.rounded_rectangle([ac_x, belt + px(8), ac_x + px(9), hem - px(6)],
                        radius=px(4), fill=(168, 172, 182))
    z.rectangle([ac_x + px(1), belt + px(10), ac_x + px(3), hem - px(8)],
                fill=(234, 238, 246))
    for i in range(3):
        yy = belt + px(34) + i * px(28)
        z.rectangle([ac_x, yy, ac_x + px(9), yy + px(3)], fill=(122, 126, 136))

    # ---- roof: marker lamps, the chrome light bar with its blue lamps, horns
    for i in range(4):
        lx = px(203) + i * px(18)
        z.rounded_rectangle([lx, roof - px(7), lx + px(9), roof + px(1)], radius=px(2),
                            fill=(255, 176, 74))
        z.rectangle([lx + px(2), roof - px(5), lx + px(7), roof - px(2)],
                    fill=(255, 238, 196))
    lb_x = px(124)
    z.rectangle([lb_x + px(2), roof - px(2), lb_x + px(30), roof + px(3)], fill=(124, 128, 138))
    z.rectangle([lb_x, roof - px(10), lb_x + px(32), roof - px(3)], fill=(80, 82, 92))
    for i in range(3):
        lx = lb_x + px(2) + i * px(10)
        z.rounded_rectangle([lx, roof - px(9), lx + px(8), roof - px(4)], radius=px(2),
                            fill=(198, 222, 250))
        z.rounded_rectangle([lx + px(1), roof - px(8), lx + px(7), roof - px(5)],
                            radius=px(1), fill=(240, 249, 255))
    for hx in (px(162), px(171)):
        z.line([(hx, roof - px(3)), (hx + px(2), roof - px(15))],
               fill=(190, 194, 204), width=px(3))
        z.ellipse([hx - px(1), roof - px(21), hx + px(5), roof - px(14)],
                  fill=(198, 202, 212))

    # ---- mirror on its arm, reaching forward of the screen
    z.line([(px(113), belt - px(4)), (px(104), belt - px(16))],
           fill=(72, 76, 86), width=px(3))
    z.rounded_rectangle([px(96), belt - px(30), px(106), belt - px(12)],
                        radius=px(3), fill=(172, 176, 186))
    z.rectangle([px(98), belt - px(28), px(104), belt - px(15)], fill=(218, 224, 234))

    # ---- fuel tank and step under the cab, between the axles
    z.rounded_rectangle([px(124), hem - px(2), px(200), hem + px(11)],
                        radius=px(5), fill=(118, 122, 132))
    z.rectangle([px(127), hem + px(1), px(197), hem + px(5)], fill=(166, 170, 180))
    for i in range(7):
        xx = px(130) + i * px(10)
        z.rectangle([xx, hem + px(5), xx + px(3), hem + px(10)], fill=(124, 128, 138))
    z.rectangle([px(118), hem + px(4), px(126), hem + px(9)], fill=(196, 200, 210))

    # ---- cut the wheel wells out of the coachwork, then arch outside each one
    mask = Image.new("L", layer.size, 255)
    mz = _Zoom(ImageDraw.Draw(mask), K, X0, Y0)
    for ax in (steer, drive_a, drive_b):
        mz.ellipse([ax - R - px(6), ground - R - px(6), ax + R + px(6), ground + R + px(6)],
                   fill=0)
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
    for ax in (steer, drive_a, drive_b):
        _fender(z, ax, ground, R + px(13))

    # ---- the back of the tractor, and the bed's own headboard behind it.
    # Drawn after the wheel wells are cut, so nothing punches through it.
    z.rectangle([back_x, roof - px(8), back_x + px(4), PANEL_BOT], fill=(206, 209, 215))
    z.rectangle([back_x + px(4), roof - px(4), back_x + px(5), PANEL_BOT], fill=(96, 100, 110))
    for ly in (FLOOR_Y - px(14), FLOOR_Y - px(2)):
        z.rounded_rectangle([back_x + px(1), ly, back_x + px(4), ly + px(5)],
                            radius=px(1), fill=(198, 44, 44))
    # the gap where the two parts meet: dark, with the frame crossing it
    z.rectangle([back_x + px(5), FAR_RAIL_TOP - px(6), back_x + px(20), PANEL_BOT],
                fill=(17, 18, 22))
    for yy in (FLOOR_Y - px(2), FLOOR_Y + px(9)):
        z.rectangle([back_x + px(4), yy, back_x + px(22), yy + px(4)], fill=(62, 64, 72))
    z.rectangle([back_x + px(6), FLOOR_Y + px(13), back_x + px(20), FLOOR_Y + px(20)],
                fill=(30, 31, 37))                       # coupling plate
    # mud flaps behind the rear wheels of the tractor
    for mx in (px(268), px(281)):
        z.rectangle([mx, hem + px(1), mx + px(4), hem + px(10)], fill=(18, 19, 23))
    # the flatbed's headboard: its own part, standing proud of the deck
    z.rectangle([back_x + px(20), FLOOR_Y - px(30), back_x + px(28), PANEL_BOT],
                fill=STEEL)
    z.rectangle([back_x + px(20), FLOOR_Y - px(30), back_x + px(28), FLOOR_Y - px(25)],
                fill=STEEL_LT)
    z.rectangle([back_x + px(20), FLOOR_Y - px(16), back_x + px(28), FLOOR_Y - px(14)],
                fill=(42, 44, 52))

    img.alpha_composite(layer.resize((X1 - X0, Y1 - Y0), Image.LANCZOS), (X0, Y0))


def _trailer_end(img):
    """The back of the bed: header board, tail lights, mud flaps."""
    d = ImageDraw.Draw(img)
    x0, x1 = W - TAIL_W, W
    d.rectangle([x0, FLOOR_Y - px(52), x1, RAIL_TOP], fill=STEEL)
    d.rectangle([x0, FLOOR_Y - px(52), x1, FLOOR_Y - px(48)], fill=STEEL_LT)
    for x in range(int(x0), int(x1), int(px(22))):
        d.rectangle([x, FLOOR_Y - px(48), x + px(6), RAIL_TOP], fill=(42, 44, 52))
    d.rectangle([x0, FLOOR_Y - px(48), x0 + px(4), FLOOR_Y - px(44)], fill=GOLD)
    for tx in (x0 + px(8), x0 + px(44)):
        d.rectangle([tx, FLOOR_Y - px(40), tx + px(24), FLOOR_Y - px(20)], fill=(196, 40, 40))
        d.rectangle([tx + px(4), FLOOR_Y - px(36), tx + px(20), FLOOR_Y - px(24)],
                    fill=(255, 108, 96))
    d.rectangle([x0, FLOOR_Y + px(4), x1, FLOOR_Y + px(10)], fill=(34, 34, 40))
    for mx in (x0 + px(4), x0 + px(38)):
        d.rectangle([mx, FLOOR_Y + px(10), mx + px(22), PANEL_BOT], fill=(20, 20, 26))


def road_layer():
    """The moving part of the highway: dashes, catenary poles and oncoming
    traffic, on a strip that travels by itself.

    Tiled infinitely in x with a velocity, it slides even while the camera is
    still, which is the illusion the whole stage rests on: the rig never moves,
    the road does. Every spacing divides ROAD_TILE so the seam is invisible.
    """
    tile = Image.new("RGBA", (ROAD_TILE, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    # asphalt that matches the wall's, darker towards the near verge
    for i in range(FLOOR_Y - ROAD_TOP):
        t = i / float(max(1, FLOOR_Y - ROAD_TOP - 1))
        d.line([(0, ROAD_TOP + i), (ROAD_TILE, ROAD_TOP + i)],
               fill=tuple(int((56, 56, 64)[k] + ((27, 27, 32)[k] - (56, 56, 64)[k]) * t)
                          for k in range(3)) + (255,))
    rnd = random.Random(23)
    # lane dashes: 4 per tile, so the rhythm holds across the seam
    for x in range(0, ROAD_TILE, 350):
        d.rectangle([x, ROAD_TOP + px(6), x + 200, ROAD_TOP + px(10)],
                    fill=(200, 194, 144))
    # scratches of light where the wet surface throws the headlights back
    for _ in range(80):
        y = rnd.uniform(ROAD_TOP + px(1), ROAD_TOP + px(10))
        x = rnd.uniform(0, ROAD_TILE)
        ln = rnd.uniform(px(10), px(44))
        d.line([(x, y), (x + ln, y)],
               fill=(198, 216, 244, int(rnd.uniform(18, 54))),
               width=max(1, int(px(0.6))))
    # catenary poles, bases in the verge, arms out over the carriageway
    for px_x in (px(78), px(234)):
        x = int(px_x) % ROAD_TILE
        d.rectangle([x, ROAD_TOP - px(40), x + px(6), ROAD_TOP + px(8)], fill=(44, 46, 54))
        d.line([(x + px(6), ROAD_TOP - px(38)), (x + px(78), ROAD_TOP - px(50))],
               fill=(44, 46, 54), width=px(4))
        d.rectangle([x + px(68), ROAD_TOP - px(54), x + px(90), ROAD_TOP - px(48)],
                    fill=(34, 36, 44))
        d.ellipse([x + px(70), ROAD_TOP - px(50), x + px(88), ROAD_TOP - px(44)],
                  fill=(248, 226, 172))
    # a big rig coming the other way, headlights blazing through the rain
    cx0 = int(px(150)) % ROAD_TILE
    d.rectangle([cx0, ROAD_TOP - px(4), cx0 + px(64), ROAD_TOP + px(9)], fill=(20, 20, 28))
    d.rectangle([cx0 + px(48), ROAD_TOP - px(14), cx0 + px(64), ROAD_TOP - px(3)],
                fill=(28, 28, 38))
    d.rectangle([cx0 + px(8), ROAD_TOP - px(15), cx0 + px(42), ROAD_TOP - px(3)],
                fill=(24, 24, 32))
    for hx in (cx0 + px(1), cx0 + px(50)):
        d.ellipse([hx, ROAD_TOP - px(3), hx + px(8), ROAD_TOP + px(5)],
                  fill=(255, 246, 214))
    return tile


def _highway_wall():
    """The stormy desert highway, as it shipped: storm bank, horizon haze, the
    mesas, a rig coming the other way, lightning, wet asphalt, guard rail and
    rain. The truck is painted on top of this, it does not replace it."""
    base = blank([
        (0, (9, 11, 21)), (70, (24, 30, 52)), (140, (34, 38, 60)),
        (200, (28, 28, 42)), (240, (11, 11, 19)),
    ])
    d = ImageDraw.Draw(base)

    # storm bank
    clouds = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(clouds)
    for i in range(34):
        x = (i * px(45)) % W
        y = px(4) + (i % 5) * px(5)
        cd.ellipse([x, y, x + px(70), y + px(30)], fill=(44, 50, 78, 150))
    base = Image.alpha_composite(base, clouds.filter(ImageFilter.GaussianBlur(px(8))))

    d = ImageDraw.Draw(base)
    # horizon haze, then mesas with a lit rim
    for i in range(px(30)):
        a = int(76 * (1 - i / px(30)))
        d.line([(0, FLOOR_Y - px(30) - i), (W, FLOOR_Y - px(30) - i)],
               fill=(104, 112, 148, a))
    for x, w, h in ((px(40), px(110), px(34)), (px(220), px(136), px(44)),
                    (px(420), px(118), px(36)), (px(640), px(140), px(48)),
                    (px(830), px(104), px(30))):
        d.polygon([(x, FLOOR_Y - px(30)), (x + w * 0.22, FLOOR_Y - px(30) - h),
                   (x + w * 0.78, FLOOR_Y - px(30) - h), (x + w, FLOOR_Y - px(30))],
                  fill=(42, 40, 60))
        d.line([(x + w * 0.20, FLOOR_Y - px(30) - h),
                (x + w * 0.80, FLOOR_Y - px(30) - h)],
               fill=(78, 80, 108), width=px(1))
    # a big rig coming the other way, lights on
    tx, ty = CX + px(300), FLOOR_Y - px(34)
    d.rectangle([tx, ty - px(20), tx + px(92), ty + px(4)], fill=(18, 18, 24))
    d.rectangle([tx + px(66), ty - px(14), tx + px(92), ty + px(2)], fill=(26, 26, 34))
    for hx in (tx + px(6), tx + px(26), tx + px(78)):
        d.ellipse([hx, ty - px(4), hx + px(9), ty + px(4)], fill=(255, 238, 190))

    # lightning
    bolt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bolt)
    for bx, seed in ((px(170), 3), (px(580), 9)):
        rnd = random.Random(seed)
        x, y = bx, px(2)
        pts = [(x, y)]
        while y < FLOOR_Y - px(80):
            x += rnd.randint(-px(5), px(5))
            y += rnd.randint(px(4), px(9))
            pts.append((x, y))
        for i in range(len(pts) - 1):
            bd.line([pts[i], pts[i + 1]], fill=(216, 234, 255, 238), width=px(1))
    base = art.screen(base, bolt, glow_radius=34, gain=2.1)

    # road, verge, markings
    d = ImageDraw.Draw(base)
    d.rectangle([0, FLOOR_Y - px(30), W, FLOOR_Y], fill=(32, 32, 37))
    d.line([(0, FLOOR_Y - px(30)), (W, FLOOR_Y - px(30))], fill=(56, 56, 64), width=px(2))
    d.rectangle([0, FLOOR_Y, W, H], fill=(25, 25, 29))
    for x in range(0, W, px(56)):
        d.rectangle([x, FLOOR_Y + px(10), x + px(28), FLOOR_Y + px(15)],
                    fill=(200, 194, 144))
    # guard rail posts
    for x in range(0, W, px(46)):
        d.rectangle([x, FLOOR_Y - px(44), x + px(3), FLOOR_Y - px(14)], fill=(70, 70, 78))
    base = art.wet_floor(base, FLOOR_Y + px(3), (136, 176, 226), 40, seed=57, bands=190)
    base = shade(base, [
        (light(CX, FLOOR_Y - px(6), px(120), (120, 150, 210), 70), 50, 1.0),
    ])
    base = art.rain(base, count=700, length=(px(5), px(13)), color=(174, 204, 234),
                    alpha=50, seed=41, angle=-0.30)

    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    fd.rectangle([0, H - px(9), W, H], fill=(8, 8, 12))
    # no posts here: a near-verge guard rail crosses the rig's tyres and makes
    # the wheels look like they are behind bars
    for x in range(px(14), W, px(45)):
        fd.rectangle([x, H - px(4), x + px(2), H], fill=(14, 14, 20))
    return finish(base, 33, 6, 0.55, FLOOR_Y), fg




def stage_highway():
    """The stormy highway, with the rig driving through it.

    The wall is the road as it shipped; the strip carries the traffic that
    moves; the truck sits in front of both, its flatbed the floor the fighters
    stand on. Three planes, three speeds, one picture.
    """
    wall, fg = _highway_wall()
    truck = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _deck(truck)
    _cab(truck)
    _trailer_end(truck)
    return [("bg", 0, 0, wall, 0), ("truck", 14, 0, truck, 0), ("fg", 3, 0, fg, 1)]


def _scene(sid, layers):
    """Full-canvas composite as the engine lays it out at camera 0.

    Used for the select preview and the README shots, so those show what ships:
    the far plate at its own delta, the highway strip tiled under the rig, then
    every sprite in stage order.
    """
    comp = Image.new("RGBA", (W, H), PLATE.get(sid, PLATE["chinatown_alley"])[0] + (255,))
    comp.alpha_composite(sky_layer(sid).resize((SKY_W, H), Image.BILINEAR),
                         (CX - SKY_W // 2, 0))
    for _key, g, _n, img, _layerno in layers:
        comp.alpha_composite(img, (0, 0))
        if g == 0 and sid in EXTRA_AFTER_BG:     # the strip rides on the wall
            strip = road_layer()
            for x in range(-ROAD_TILE, W + ROAD_TILE, ROAD_TILE):
                comp.alpha_composite(strip, (x, 0))
    return comp

# Each stage may name its own fight music# Each stage may name its own fight music; the engine resolves the path
# relative to the game root, so tracks live in sound/.
# Every stage gets its own cue. These are synthesised by
# tools/build_stage_music.py rather than shipped from outside the project, so a
# clean checkout still has music: without them `bgmusic` was blank in every
# stage except the airport, and the airport's file did not exist either.
MUSIC = {
    "lopans_throne": "sound/LoPansDemise.ogg",
    "wingkong_exchange": "sound/WingKongExchange.ogg",
    "chinatown_alley": "sound/AlleyWar.ogg",
    "porkchop_express": "sound/PorkChopExpress.ogg",
    "the_upside_down": "sound/Hide.ogg",
    "airport_terminal": "sound/Airport.ogg",
}

STAGES = {
    "lopans_throne": ("Lo Pan's Throne", stage_throne),
    "wingkong_exchange": ("Wing Kong Exchange", stage_wingkong),
    "chinatown_alley": ("Chinatown Back Alley", stage_alley),
    "porkchop_express": ("Pork Chop Express", stage_highway),
}

# Depth layers. The canvas is 5600 wide for a 1788-travel camera, so the far
# plate only has to span LOCAL_W + delta*2*SCROLL, and the floor lip only the
# strip the fighters stand in.
SKY_DELTA = 0.35
SKY_W = int(LOCAL_W + SKY_DELTA * 2 * SCROLL)   # 3172 px on screen
LIP_TOP = FLOOR_Y                                # 900: the lip starts at the ground line
LIP_H = H - LIP_TOP                             # 180 px
LIP_FADE = 70                                   # soft top edge, no hard cut
# Stages whose near foreground art genuinely reaches above the ground line keep
# their own top edge. Pork Chop Express builds a near side wall from y=666 down
# to RAIL_TOP (860), and that wall has to stay in front of the fighters all the
# way, so its lip still starts at 860. Everywhere else the band between 860 and
# 900 is wall/floor junction paint: cutting it there pasted the junction (luma
# 8-21) in front of the fighters' feet, which sat on a lit floor plate (luma
# 9-27), so their feet vanished into a dark strip and they read as floating.
LIP_TOP_BY_STAGE = {"porkchop_express": FLOOR_Y - 40}
# Layers ship at the size they are drawn. They used to be painted at half
# size and blown back up with `scale = 2,2` in the .def, but that scale is
# not honoured for BG sprites: the floor lip went down 2800px wide from
# x=-2800, covering only the LEFT half of the stage, and the floor past it
# was drawn bare - the hard black step on every map. Same for the sky, so
# the upper right of every stage was bare too.
HALF = 1
# A painted floor wants a soft lip so feet sink into it; a steel bed edge wants
# a hard one, or the fighters look like they are standing on the road outside.
# The truck's lip is cut through its own side wall, so it needs the softest edge
# in the build or the wall's bottom rail draws a hard line across the fighters.
LIP_FADE_BY_STAGE = {"porkchop_express": int(px(7))}
# Where the select-screen card looks: the stage centre, except on the highway,
# where the cab is off the left edge and the card should still show the truck.
PREVIEW_CX = {"porkchop_express": px(240)}


# What the far plate is made of, per stage: (sky top, sky bottom, haze,
# silhouette, accent). The distance is painted, not blurred out of the wall, so
# it can hold its own detail while the camera moves at a different speed.
PLATE = {
    "lopans_throne": ((8, 6, 10), (26, 17, 18), (44, 30, 28), (15, 10, 11), (86, 214, 126)),
    "wingkong_exchange": ((8, 10, 16), (26, 30, 42), (44, 50, 64), (13, 15, 21), (226, 108, 96)),
    "chinatown_alley": ((12, 9, 16), (44, 26, 32), (74, 40, 44), (19, 13, 16), (238, 172, 92)),
    "porkchop_express": ((9, 12, 26), (38, 46, 78), (88, 100, 140), (17, 19, 31), (206, 226, 255)),
}

# Motion that belongs to the air# Motion that belongs to the air, not the wall: (kind, colour, count).
FX = {
    "lopans_throne": ("ember", (240, 168, 96), 620),
    "wingkong_exchange": ("rain", (168, 200, 234), 1500),
    "chinatown_alley": ("dust", (232, 200, 148), 1800),
    "porkchop_express": ("rain", (188, 216, 248), 1800),
}


def sky_layer(sid):
    """The painted far plate: a hazy distant city beyond the play plane.

    Two zones, so the same plate is believable seen under open sky (Pork Chop
    Express) and through a doorway (Lo Pan's gate): a gradient sky with a light
    pool above the horizon, and a hazed ground plane below it, with silhouettes
    standing on the join.
    """
    top, low, haze, sil, accent = PLATE.get(sid, PLATE["chinatown_alley"])
    horizon = int(H * 0.66)
    plate = Image.new("RGBA", (SKY_W, H), top + (255,))
    d = ImageDraw.Draw(plate)
    for y in range(horizon):
        t = (y / float(max(1, horizon - 1))) ** 0.85
        d.line([(0, y), (SKY_W, y)],
               fill=tuple(int(top[i] + (low[i] - top[i]) * t) for i in range(3)) + (255,))
    for y in range(horizon, H):
        t = (y - horizon) / float(max(1, H - horizon))
        d.line([(0, y), (SKY_W, y)],
               fill=tuple(int(low[i] * (1 - 0.5 * t) + sil[i] * 0.5 * t) for i in range(3)) + (255,))

    # light pooling above the horizon, where the city glows through the haze
    plate = shade(plate, [
        (light(SKY_W * 0.34, horizon - px(6), px(120), accent, 62), 44, 1.3),
        (light(SKY_W * 0.68, horizon - px(2), px(96), accent, 46), 48, 1.2),
    ])

    rnd = random.Random(sum(ord(c) for c in sid) * 31)
    desert = sid == "porkchop_express"
    bands = 4
    for band in range(bands):
        # band 0 is furthest away: smaller, flatter, more haze over it
        near = band / float(bands - 1)
        base_y = horizon - int(px(14) * band)
        col = tuple(int(low[i] * (0.44 + 0.26 * near) + sil[i] * (0.40 - 0.16 * near))
                    for i in range(3))
        edge = tuple(min(255, c + 8) for c in col)
        x = -int(px(30))
        while x < SKY_W:
            if desert:
                w = int(px(rnd.uniform(90, 210)))
                h = int(px(rnd.uniform(10, 30)) * (1.0 - 0.26 * band))
                d.polygon([(x, base_y), (x + w * 0.16, base_y - h),
                           (x + w * 0.84, base_y - h), (x + w, base_y)], fill=col + (255,))
                d.line([(x + w * 0.16, base_y - h), (x + w * 0.84, base_y - h)],
                       fill=tuple(min(255, c + 26) for c in col) + (255,), width=max(1, int(px(0.6))))
                x += w + int(px(rnd.uniform(12, 46)))
                continue
            # a tower, sometimes with a narrower second tier and a rooftop mast
            w = int(px(rnd.uniform(28, 78)) * (1.0 + 0.34 * band))
            h = int(px(rnd.uniform(26, 104)) * (1.0 - 0.30 * band))
            top = base_y - h
            d.rectangle([x, top, x + w, base_y], fill=col + (255,))
            if rnd.random() < 0.65:
                tw = int(w * rnd.uniform(0.35, 0.62))
                th = int(px(rnd.uniform(6, 26)) * (1.0 - 0.20 * band))
                tx = x + int((w - tw) * rnd.uniform(0.2, 0.8))
                d.rectangle([tx, top - th, tx + tw, top], fill=col + (255,))
                d.line([(tx, top - th), (tx + tw, top - th)], fill=edge + (255,),
                       width=max(1, int(px(0.6))))
                top -= th
            if rnd.random() < 0.40:
                mx = x + int(w * rnd.uniform(0.25, 0.75))
                mh = int(px(rnd.uniform(8, 30)))
                d.line([(mx, top), (mx, top - mh)], fill=col + (255,),
                       width=max(1, int(px(0.8))))
            if band:
                # lit windows on the nearer bands only: the far ones are haze
                for wy in range(top + int(px(10)), base_y - int(px(6)), int(px(14))):
                    for wx in range(x + int(px(5)), x + w - int(px(5)), int(px(13))):
                        if rnd.random() < 0.26:
                            d.rectangle([wx, wy, wx + int(px(4)), wy + int(px(5))],
                                        fill=tuple(int(accent[i] * (0.30 + 0.30 * near)
                                                   + col[i] * (0.70 - 0.30 * near))
                                                   for i in range(3)) + (255,))
            x += w + int(px(rnd.uniform(5, 24)))
        # atmospheric haze between the bands: further = flatter
        plate = Image.alpha_composite(
            plate, Image.new("RGBA", (SKY_W, H), haze + (int(16 + 26 * (1.0 - near)),)))

    if desert:
        # a thin, snaking bolt over the far mesas, so the plate carries its own
        # weather instead of inheriting the wall's
        bolt = Image.new("RGBA", (SKY_W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bolt)
        rnd2 = random.Random(91)
        for bx in (int(SKY_W * 0.18), int(SKY_W * 0.71)):
            x, y, pts = bx, px(4), []
            while y < horizon - px(30):
                pts.append((x, y))
                x += rnd2.randint(-int(px(5)), int(px(5)))
                y += rnd2.randint(int(px(4)), int(px(9)))
            for i in range(len(pts) - 1):
                bd.line([pts[i], pts[i + 1]], fill=(214, 232, 255, 210),
                        width=max(1, int(px(0.7))))
        plate = art.screen(plate, bolt, glow_radius=px(18), gain=1.8)

    if desert:
        plate = art.rain(plate, count=1100, length=(px(4), px(11)),
                         color=(178, 206, 236), alpha=44, seed=41, angle=-0.30)

    plate = art.vignette(plate, 0.42)
    return plate.resize((max(1, SKY_W // HALF), max(1, H // HALF)), Image.LANCZOS)


def fx_layer(sid):
    """Air, on its own plane: embers in the throne room, rain at the docks,
    drifting dust in the alley. Drawn with trans = add so it lights the wall
    instead of pasting a rectangle over it."""
    kind, color, count = FX.get(sid, ("dust", (226, 214, 190), 1200))
    size = (max(1, W // HALF), max(1, H // HALF))
    fx = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(fx)
    rnd = random.Random(sum(ord(c) for c in sid) * 7 + count)
    for _ in range(count):
        x = rnd.uniform(0, size[0])
        y = rnd.uniform(0, size[1])
        if kind == "rain":
            ln = rnd.uniform(2.0, 7.0)
            d.line([(x, y), (x - ln * 0.34, y + ln)],
                   fill=color + (int(rnd.uniform(38, 108)),), width=1)
        elif kind == "ember":
            r = rnd.uniform(0.6, 2.1)
            d.ellipse([x - r, y - r, x + r, y + r],
                      fill=color + (int(rnd.uniform(60, 170)),))
        else:
            r = rnd.uniform(0.5, 1.7)
            d.ellipse([x - r, y - r, x + r, y + r],
                      fill=color + (int(rnd.uniform(26, 86)),))
    fx = fx.filter(ImageFilter.GaussianBlur(0.6))
    # keep RGB black wherever the pixel is transparent: trans = add adds colour,
    # so a transparent pixel must contribute nothing at all
    return Image.composite(fx, Image.new("RGBA", size, (0, 0, 0, 0)), fx.getchannel("A"))


def lip_layer(comp, fade=LIP_FADE, top=LIP_TOP):
    """The floor's front lip, drawn in FRONT of the fighters.

    Same pixels, same place, but on layerno 1 with a gradient top edge: feet
    sink into the floor instead of being pasted on top of it.
    """
    depth = H - top
    lip = comp.crop((0, top, W, H)).convert("RGBA")
    lip = lip.resize((max(1, W // HALF), max(1, depth // HALF)), Image.BILINEAR)
    w, h = lip.size
    grad = Image.new("L", (w, h), 255)
    fade = max(1, int(round((fade * h) / float(depth))))
    for y in range(fade):
        grad.paste(int(255 * (y + 1) / float(fade)), (0, y, w, y + 1))
    lip.putalpha(ImageChops.multiply(lip.getchannel("A"), grad))
    return lip


# A stage 8192 px wide is a texture at the hardware maximum, and the engine
# holds four of them open at once (wall, foreground, floor, lip). On some GPUs
# that allocation is refused and the device is dropped - the "vk.QueueSubmit
# failed with vulkan error: device lost" seen in play. Every wide layer is cut
# into columns of at most this many pixels, each its own sprite, with a [BG]
# block per column so the stage still reads as one uninterrupted picture.
MAX_TEX = 4096


def split_wide(img):
    """Cut a layer into abutting column textures no wider than MAX_TEX."""
    w, h = img.size
    if w <= MAX_TEX:
        return [(0, img)]
    parts = []
    x = 0
    while x < w:
        parts.append((x, img.crop((x, 0, min(w, x + MAX_TEX), h))))
        x += MAX_TEX
    return parts


# Where each split layer's extra columns go: label, start y, delta, layerno,
# trans, tile, velocity. "FLOOR"/"LIP" resolve to this stage's ground line.
WIDE_META = {
    0: ("bg", 0, "1", 0, "none", 0, None),
    3: ("fg", 0, "1", 1, "none", 0, None),
    10: ("sky", 0, "SKY", 0, "none", 0, None),
    11: ("lip", "LIP", "1", 1, "none", 0, None),
    12: ("fx", 0, "1.02", 1, "add", 0, None),
    13: ("road", 0, "ROAD", 0, "none", 1, "ROAD"),
    14: ("truck", 0, "1", 0, "none", 0, None),
    15: ("floor", "FLOOR", "1", 0, "none", 0, None),
}


def wide_blocks(splits, lip_top):
    """[BG] blocks for the second and later column of every split layer."""
    out = []
    for group, offsets in splits.items():
        meta = WIDE_META.get(group)
        if not meta or len(offsets) < 2:
            continue
        label, sy, delta, layerno, trans, tile, vel = meta
        y = {"FLOOR": FLOOR_Y, "LIP": lip_top}.get(sy, sy)
        step = {"SKY": repr(SKY_DELTA), "ROAD": repr(ROAD_DELTA)}.get(delta, delta)
        speed = {"ROAD": repr(ROAD_VEL)}.get(vel)
        base = -(SKY_W // 2) if group == 10 else START_X
        for i, off in enumerate(offsets[1:], start=1):
            out.append(
                "\n; column %d of the %s plate: %d px wide, past the %d px a\n"
                "; single texture may be on some GPUs, so it ships in abutting\n"
                "; columns that line up with the first one\n[BG %s %d]\n"
                "type = normal\nspriteno = %d,%d\nlayerno = %d\n"
                "start = %d,%s\ndelta = %s,1\n%s"
                "trans = %s\nmask = 1\ntile = %d,0\n"
                % (i + 1, label, W, MAX_TEX, label, i, group, i, layerno,
                   base + off, y, step,
                   ("velocity = %s,0\n" % speed) if speed else "",
                   trans, tile))
    return "".join(out)


DEF_TEMPLATE = """;---------------------------------------------------------------------------
; {name}
; Part of Big Trouble in Little China: The Game (Ikemen GO)
; HD stage: painted at {localw}x{localh} by tools/stages_hd.py.
;---------------------------------------------------------------------------
[Info]
name = "{name}"
displayname = "{name}"
versiondate = 10,28,2026
mugenversion = 1.0
author = "Big Trouble in Little China: The Game"

[Camera]
startx = 0
starty = 0
boundleft = -{scroll}
boundright = {scroll}
boundhigh = {boundhigh}
boundlow = 0
verticalfollow = .2
floortension = 0
tension = 60
overdrawhigh = 0
overdrawlow = 0
cuthigh = {cuthigh}
cutlow = {cutlow}
zoomout = 1
zoomin = 1

[PlayerInfo]
p1startx = {startx}
p1starty = 0
p1facing = 1
p2startx = {p2startx}
p2starty = 0
p2facing = -1
leftbound = -{playerbound}
rightbound = {playerbound}

[Bound]
screenleft = {margin}
screenright = {margin}

[StageInfo]
zoffset = {zoffset}
autoturn = 1
resetBG = 1
localcoord = {localw}, {localh}
xscale = 1
yscale = 1

[Shadow]
intensity = 96
color = 0,0,0
yscale = -.1
fade.range = -400,-100

[Reflection]
intensity = 0

[Music]
bgmusic = {bgmusic}
bgmvolume = 100

[BGdef]
spr = {sid}.sff
debugbg = 0

; IKEMEN GO select-screen preview
[Begin Action 9000]
9000,1, 0,0, -1

; far parallax: a softened crop of the backdrop, travelling at 0.35 speed
[BG sky]
type = normal
spriteno = 10,0
layerno = 0
start = {sky_start},0
delta = {sky_delta},1
scale = 1,1
trans = none
mask = 1
tile = 0,0

{extra_bg}[BG bg]
type = normal
spriteno = 0,0
layerno = 0
start = {start_x},0
delta = 1,1
trans = none
mask = 1
tile = 0,0

{extra_after_bg}[BG fg]
type = normal
spriteno = 3,0
layerno = 1
start = {start_x},0
delta = 1,1
trans = none
mask = 1
tile = 0,0

; foreground floor lip: the bottom of the backdrop drawn in FRONT of the
; fighters, so their feet sit in the floor rather than on top of it
[BG lip]
type = normal
spriteno = 11,0
layerno = 1
start = {start_x},{lip_y}
delta = 1,1
scale = 1,1
trans = none
mask = 1
tile = 0,0

; air: embers, dust or rain on its own plane, drifting faster than the wall
[BG fx]
type = normal
spriteno = 12,0
layerno = 1
start = {start_x},0
delta = 1.02,1
scale = 1,1
trans = add
mask = 1
tile = 0,0
{wide}"""


# sid -> extra [BG] elements drawn before the painted hall, for the one stage
# that paints an opening to something else (Lo Pan's gate).
# sid -> [BG] elements that belong in front of the painted wall but behind the
# fighters. The highway puts its moving strip and the truck there.
# The floor plate every stage gets, dropped in right after the wall so it sits
# behind the fighters and in front of the backdrop's own transparent floor gap.
FLOOR_BG = """
; the floor: its own bitmap, cut from the backdrop at the ground line
[BG floor]
type = normal
spriteno = 15,0
layerno = 0
start = {sx},{sy}
delta = 1,1
trans = none
mask = 1
tile = 0,0
"""

EXTRA_AFTER_BG = {
    "porkchop_express": (
        "; the highway as traffic, not as paint: an infinitely tiled strip with\n"
        "; its own velocity, so the road slides past while the rig holds still.\n"
        "; +x velocity moves the world right, which is the truck driving left.\n"
        "[BG road]\n"
        "type = normal\n"
        "spriteno = 13,0\n"
        "layerno = 0\n"
        "start = %d,0\n"
        "delta = %s,1\n"
        "velocity = %d,0\n"
        "tile = 1,0\n"
        "tilespacing = 0,0\n"
        "trans = none\n"
        "mask = 1\n\n"
        "; the rig itself: its flatbed is the floor the fighters stand on\n"
        "[BG truck]\n"
        "type = normal\n"
        "spriteno = 14,0\n"
        "layerno = 0\n"
        "start = %d,0\n"
        "delta = 1,1\n"
        "trans = none\n"
        "mask = 1\n"
        "tile = 0,0\n\n"
    ) % (START_X, ROAD_DELTA, ROAD_VEL, START_X),
}

EXTRA_BG = {}

# sid -> sprites a stage adds on top of its painted layers, as
# (group, number, image). Lo Pan's gate puts its looping fog frames here.
EXTRA_SPRITES = {}


def _split_floor(img):
    """Cut a backdrop at the ground line into a wall plate and a floor plate.

    The floor is a bitmap of its own, the way the reference stage has it, so the
    def carries a real floor layer instead of the floor being paint on the same
    sheet as the wall. A contact shadow along the plate's top edge makes it read
    as a plane the fighters stand on. The shadow is painted back into the source
    image as well, because the composed scene and the front lip are cut from it
    and would otherwise show an unshadowed strip behind the layer.
    """
    img = img.convert("RGBA")
    band = img.crop((0, FLOOR_Y, W, H))
    shade = Image.new("RGBA", band.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    depth = max(2, px(9))
    for i in range(depth):
        sd.line([(0, i), (band.width, i)],
                fill=(0, 0, 0, int(150 * (1 - i / float(depth)) ** 2)))
    band = Image.alpha_composite(band, shade)
    img.paste(band, (0, FLOOR_Y))
    return img.crop((0, 0, W, FLOOR_Y)), band


def build(sid):
    name, fn = STAGES[sid]
    layers = fn()

    sprites = []
    splits = {}              # group -> x offset of each column texture
    floor = None

    def add(group, img):
        parts = split_wide(img)
        splits[group] = [off for off, _piece in parts]
        for i, (_off, piece) in enumerate(parts):
            sprites.append({"group": group, "number": i, "image": piece,
                            "axis": (0, 0)})

    for _key, g, n, img, _layerno in layers:
        if g == 0:
            img, floor = _split_floor(img)
        add(g, img)
    if floor is not None:
        add(15, floor)
    for g, n, img in EXTRA_SPRITES.get(sid, ()):
        add(g, img)

    # select preview: match-start view, downscaled to the motif's 320x240
    # Composited onto black rather than onto transparency: an HD backdrop can
    # have a real hole in it (the fog in Lo Pan's gate), and the select card
    # should show that as darkness instead of letting the menu show through.
    comp = _scene(sid, layers)
    # the near foreground band, cropped from the composed scene so it carries the
    # same openings and props, then drawn on layerno 1 in front of the fighters
    lip_top = LIP_TOP_BY_STAGE.get(sid, LIP_TOP)
    lip = lip_layer(comp, LIP_FADE_BY_STAGE.get(sid, LIP_FADE), lip_top)
    shown = comp
    pcx = PREVIEW_CX.get(sid, CX)
    # The card shows the whole level, not a bite of floor. It used to crop
    # 1215x398 straight out of the art at the ground line, so it was a close-up
    # of the bottom third with the sky cut off - which is why the preview read
    # as too small and as the wrong part of the stage.
    #
    # The card is 3.05:1 and the level is 1080 tall, so covering its full height
    # means 3297 px of stage across: an establishing shot at exactly the card's
    # aspect, downscaled uniformly (0.369 both ways) - no letterbox, no
    # distortion, whole height, and more than twice the width the card used to
    # show. It is also the match-start camera position, so the card shows the
    # stage the way the fight opens on it.
    span = int(round(PREVIEW_W * H / float(PREVIEW_H)))
    x0 = max(0, min(W - span, pcx - span // 2))
    card = shown.crop((x0, 0, x0 + span, H))
    card = card.resize((PREVIEW_W, PREVIEW_H), Image.LANCZOS).convert("RGBA")
    sprites.append({"group": 9000, "number": 1, "image": card,
                    "axis": (PREVIEW_W // 2, PREVIEW_H // 2)})
    add(10, sky_layer(sid))
    add(11, lip)
    add(12, fx_layer(sid))
    if sid in EXTRA_AFTER_BG:            # the strip and the rig it drives past
        add(13, road_layer())

    data = sff.write_sff(sprites)
    with open(os.path.join(ROOT, "stages", f"{sid}.sff"), "wb") as fh:
        fh.write(data)
    with open(os.path.join(ROOT, "stages", f"{sid}.def"), "w", encoding="utf-8") as fh:
        fh.write(DEF_TEMPLATE.format(
            sid=sid, name=name,
            bgmusic=MUSIC.get(sid, ""), scroll=SCROLL, playerbound=PLAYER_BOUND,
            margin=SCREEN_MARGIN, zoffset=FLOOR_Y, localw=LOCAL_W, localh=LOCAL_H,
            boundhigh=-int(25 * S), cuthigh=int(35 * S), cutlow=int(25 * S),
            startx=-int(70 * S), p2startx=int(70 * S), start_x=START_X,
            extra_bg=EXTRA_BG.get(sid, ""),
            extra_after_bg=((FLOOR_BG.format(sx=START_X, sy=FLOOR_Y)
                             if floor is not None else "")
                            + EXTRA_AFTER_BG.get(sid, "")),
            sky_start=-(SKY_W // 2), sky_delta=SKY_DELTA,
            lip_y=lip_top, half=HALF, wide=wide_blocks(splits, lip_top),
        ))
    # README preview: the 4:3 match-start view, same path build_stages.py uses so
    # the docs show what actually ships
    arts = os.path.join(ROOT, "artifacts")
    os.makedirs(arts, exist_ok=True)
    view_43 = shown.crop((pcx - LOCAL_W // 2, 0, pcx + LOCAL_W // 2, H))
    view_43.save(os.path.join(arts, f"{sid}_preview.png"))
    view_169 = shown.crop((pcx - VIEW_W // 2, 0, pcx + VIEW_W // 2, H))
    view_169.resize((int(VIEW_W * 0.5), H // 2), Image.LANCZOS).save(
        os.path.join(arts, f"{sid}_preview_wide.png"))
    preview_dir = os.environ.get("STAGES_HD_PREVIEW_DIR")
    if preview_dir:
        os.makedirs(preview_dir, exist_ok=True)
        view_43.save(os.path.join(preview_dir, f"{sid}_43.png"))
        view_169.save(os.path.join(preview_dir, f"{sid}_169.png"))
    print(f"  {sid}: {len(sprites)} sprites, {len(data) / 1024 / 1024:.1f} MiB, "
          f"{W}x{H} at localcoord {LOCAL_W}x{LOCAL_H}")


def main():
    print("Building HD stages")
    for sid in STAGES:
        build(sid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
