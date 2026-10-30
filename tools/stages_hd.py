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
W, H = int(640 * S), int(240 * S)        # 2880 x 1080 painted area per screen
SCROLL = 1788                            # camera travel, from MK Trilogy HD
COVER = 1012                             # overpaint: art reaches +/-2800
W = 2 * (SCROLL + COVER)                 # 4000: full stage canvas
CX = W // 2                              # 2000
FLOOR_Y = int(200 * S)                   # 900: ground line = zoffset
START_X = -(SCROLL + COVER)              # -2000
PLAYER_BOUND = SCROLL + 580              # 2368
SCREEN_MARGIN = int(round(15 * S))       # 68
VIEW_W = int(LOCAL_H * 16 / 9)           # 1707: what a 16:9 window shows


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
def stage_highway():
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
    for x in range(px(14), W, px(45)):
        fd.rectangle([x, H - px(34), x + px(2), H], fill=(14, 14, 20))
    return [("bg", 0, 0, finish(base, 33, 6, 0.55, FLOOR_Y), 0),
            ("fg", 3, 0, fg, 1)]


# Each stage may name its own fight music; the engine resolves the path
# relative to the game root, so tracks live in sound/.
MUSIC = {
    "airport_terminal": "sound/Airport.ogg",
}

STAGES = {
    "lopans_throne": ("Lo Pan's Throne", stage_throne),
    "wingkong_exchange": ("Wing Kong Exchange", stage_wingkong),
    "chinatown_alley": ("Chinatown Back Alley", stage_alley),
    "porkchop_express": ("Pork Chop Express", stage_highway),
}

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

[BG bg]
type = normal
spriteno = 0,0
layerno = 0
start = {start_x},0
delta = 1,1
trans = none
mask = 0
tile = 0,0

[BG fg]
type = normal
spriteno = 3,0
layerno = 1
start = {start_x},0
delta = 1,1
trans = none
mask = 1
tile = 0,0
"""


def build(sid):
    name, fn = STAGES[sid]
    layers = fn()

    sprites = [{"group": g, "number": n, "image": img, "axis": (0, 0)}
               for _key, g, n, img, _layerno in layers]

    # select preview: match-start view, downscaled to the motif's 320x240
    comp = layers[0][3].copy()
    for _key, _g, _n, img, _layerno in layers[1:]:
        comp.alpha_composite(img, (0, 0))
    view = comp.crop((CX - LOCAL_W // 2, 0, CX + LOCAL_W // 2, H)) .resize((320, 240), Image.LANCZOS)
    sprites.append({"group": 9000, "number": 1, "image": view, "axis": (160, 120)})

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
        ))
    # README preview: the 4:3 match-start view, same path build_stages.py uses so
    # the docs show what actually ships
    arts = os.path.join(ROOT, "artifacts")
    os.makedirs(arts, exist_ok=True)
    view_43 = comp.crop((CX - LOCAL_W // 2, 0, CX + LOCAL_W // 2, H)) 
    view_43.save(os.path.join(arts, f"{sid}_preview.png"))
    view_169 = comp.crop((CX - VIEW_W // 2, 0, CX + VIEW_W // 2, H))
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
