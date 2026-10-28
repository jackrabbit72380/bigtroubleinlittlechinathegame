"""Build the Big Trouble in Little China stages (art + SFF v2 + DEF).

Canvas geometry: one screen is VIEW_W x H and the camera scrolls SCROLL px each
way, and the backdrop paints COVER px past each camera limit, so the view stays
covered no matter how far the camera or the zoom travels.
Players are clamped to PLAYER_BOUND px from centre, which is SCREEN_MARGIN inside
the painted edge, so they can be pushed to the screen border but can never step
off the artwork. Focal elements are centred on CX so they read at match start.

Run:  python3 tools/build_stages.py            (set STAGE_DEBUG=1 to dump layers)
Outputs stages/<id>.sff, stages/<id>.def and artifacts/<id>_preview.png
"""

from __future__ import annotations

import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VIEW_W, H = 320, 240                 # one screen, in stage pixels
SCROLL = 260                         # camera travel each way -> 520px-wide arena
HALF = VIEW_W // 2                   # 160
COVER = 240                          # overpaint past each camera limit
W = 2 * (SCROLL + COVER)             # 1000: full scrollable backdrop
CX = W // 2                          # 500: horizontal centre of the scene
START_X = -(SCROLL + COVER)          # -500: left edge of the backdrop
FLOOR_Y = 200                        # zoffset
VIEW = (CX - HALF, 0, CX + HALF, H)  # on-screen window at camera centre
SCREEN_MARGIN = 15                   # matches [Bound] screenleft/screenright
PLAYER_BOUND = SCROLL + HALF - SCREEN_MARGIN   # 405: still on painted floor


# ---------------------------------------------------------------- Lo Pan's Throne
def stage_throne():
    """The skull gate hall: neon-rimmed skull between two temple arches."""
    base = art.vgrad((W, H), [
        (0, (16, 9, 10)), (36, (40, 19, 17)), (110, (28, 15, 15)),
        (168, (20, 12, 13)), (FLOOR_Y, (15, 11, 12)), (H, (7, 6, 8)),
    ])
    base.alpha_composite(art.radial_light((W, H), (CX, 92), 200, (152, 62, 46), 104))
    d = ImageDraw.Draw(base)

    # --- stone arches flanking the gate ---------------------------------
    for ax in (CX - 118, CX + 118):
        art.arch_shape(d, ax, FLOOR_Y + 8, 162, 146, (108, 92, 78))
        art.arch_shape(d, ax, FLOOR_Y + 8, 132, 128, (18, 11, 13))
        d.arc([ax - 66, FLOOR_Y + 8 - 128, ax + 66, FLOOR_Y + 8 - 128 + 132],
              180, 360, fill=(70, 58, 50), width=3)
        for k in range(9):
            ang = math.pi * (1.0 + k / 8.0)
            sx = ax + math.cos(ang) * 72
            sy = FLOOR_Y + 8 - 146 + 81 + math.sin(ang) * 81
            d.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(150, 130, 108))
        for yy in (FLOOR_Y - 40, FLOOR_Y - 14):
            d.rectangle([ax - 66, yy, ax - 58, yy + 4], fill=(92, 78, 66))
            d.rectangle([ax + 58, yy, ax + 66, yy + 4], fill=(92, 78, 66))

    # red neon temple glyphs inside the arches
    glyph = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glyph)
    lx, ly = CX - 118, 136
    gd.rectangle([lx - 26, ly - 32, lx + 26, ly + 28], outline=(255, 44, 40, 255), width=5)
    gd.line([(lx - 26, ly - 2), (lx + 26, ly - 2)], fill=(255, 44, 40, 255), width=5)
    fx, fy = CX + 118, 140
    gd.line([(fx, fy - 34), (fx, fy + 6)], fill=(255, 52, 40, 255), width=5)
    gd.line([(fx - 2, fy - 6), (fx - 26, fy + 22)], fill=(255, 52, 40, 255), width=5)
    gd.line([(fx + 2, fy - 6), (fx + 26, fy + 22)], fill=(255, 52, 40, 255), width=5)
    gd.line([(fx - 6, fy - 20), (fx - 22, fy - 34)], fill=(255, 52, 40, 255), width=5)
    gd.line([(fx + 6, fy - 20), (fx + 22, fy - 34)], fill=(255, 52, 40, 255), width=5)
    base = art.screen(base, glyph, glow_radius=9, gain=1.45, passes=2)

    # wall torches
    flames = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(flames)
    for tx, ty in ((CX - 168, 112), (CX - 78, 120), (CX + 78, 120), (CX + 168, 112)):
        fd.rectangle([tx - 14, ty + 2, tx + 14, ty + 7], fill=(52, 40, 28, 255))
        fd.polygon([(tx - 10, ty + 6), (tx, ty + 20), (tx + 10, ty + 6)],
                   fill=(44, 32, 22, 255))
        fd.polygon([(tx - 11, ty + 2), (tx - 4, ty - 24), (tx + 2, ty - 6),
                    (tx + 7, ty - 30), (tx + 12, ty + 2)], fill=(255, 150, 48, 255))
        fd.polygon([(tx - 5, ty + 1), (tx - 1, ty - 14), (tx + 3, ty - 2),
                    (tx + 5, ty + 1)], fill=(255, 246, 200, 255))
        base.alpha_composite(art.radial_light((W, H), (tx, ty - 6), 62,
                                              (255, 142, 48), 128))
    base = art.screen(base, flames, glow_radius=8, gain=1.3)

    # --- white stone balustrade -----------------------------------------
    d = ImageDraw.Draw(base)
    d.rectangle([0, 148, W, 196], fill=(168, 158, 140))
    d.rectangle([0, 144, W, 152], fill=(208, 198, 176))
    d.rectangle([0, 144, W, 146], fill=(236, 228, 210))
    d.rectangle([0, 190, W, 196], fill=(142, 132, 116))
    for x in range(4, W, 24):
        d.rectangle([x + 7, 152, x + 13, 190], fill=(188, 178, 156))
        d.ellipse([x + 2, 156, x + 18, 172], fill=(200, 190, 168),
                  outline=(152, 142, 124))
        d.ellipse([x + 5, 160, x + 15, 168], fill=(218, 208, 186))
    for x in range(0, W, 124):
        d.rectangle([x, 144, x + 14, 196], fill=(196, 186, 164))
        d.rectangle([x, 144, x + 14, 150], fill=(230, 222, 202))

    rails = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rails)
    rd.line([(0, 196), (W, 196)], fill=(70, 150, 255, 255), width=2)
    rd.line([(0, 199), (W, 199)], fill=(255, 46, 44, 255), width=2)
    base = art.screen(base, rails, glow_radius=7, gain=1.5)

    # --- the skull gate -------------------------------------------------
    top, jaw_y = 40, 152
    mask = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(mask)
    sd.ellipse([CX - 92, top, CX + 92, top + 100], fill=255)
    sd.polygon([(CX - 66, top + 62), (CX + 66, top + 62),
                (CX + 54, jaw_y), (CX - 54, jaw_y)], fill=255)
    sd.ellipse([CX - 52, jaw_y - 10, CX + 52, jaw_y + 22], fill=255)
    sd.polygon([(CX - 46, jaw_y + 14), (CX - 22, jaw_y + 14),
                (CX - 22, FLOOR_Y - 8), (CX - 58, FLOOR_Y - 8)], fill=255)
    sd.polygon([(CX + 22, jaw_y + 14), (CX + 46, jaw_y + 14),
                (CX + 58, FLOOR_Y - 8), (CX + 22, FLOOR_Y - 8)], fill=255)

    bone = art.vgrad((W, H), [(0, (198, 194, 182)), (120, (152, 146, 134)),
                              (200, (100, 96, 88)), (H, (70, 66, 60))])
    skull = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    skull.paste(bone, (0, 0), mask)
    sk = ImageDraw.Draw(skull)
    sk.ellipse([CX - 60, top + 26, CX - 10, top + 70], fill=(8, 12, 10, 255))
    sk.ellipse([CX + 10, top + 26, CX + 60, top + 70], fill=(8, 12, 10, 255))
    sk.ellipse([CX - 54, top + 32, CX - 16, top + 64], fill=(2, 6, 5, 255))
    sk.ellipse([CX + 16, top + 32, CX + 54, top + 64], fill=(2, 6, 5, 255))
    sk.polygon([(CX - 9, top + 66), (CX + 9, top + 66), (CX, top + 96)],
               fill=(4, 8, 7, 255))
    sk.ellipse([CX - 46, jaw_y - 22, CX + 46, jaw_y + 16], fill=(12, 10, 10, 255))
    for i in range(6):
        tx = CX - 40 + i * 16
        ln = 18 if i % 2 == 0 else 12
        sk.polygon([(tx, jaw_y - 16), (tx + 12, jaw_y - 16),
                    (tx + 6, jaw_y - 16 + ln)], fill=(236, 230, 212, 255))
    for s in (-1, 1):
        sk.polygon([(CX + s * 52, jaw_y - 20), (CX + s * 34, jaw_y - 20),
                    (CX + s * 40, jaw_y + 20)], fill=(240, 234, 216, 255))
    base.alpha_composite(skull)

    neon = art.outline(mask, (66, 255, 156), thickness=2)
    nd = ImageDraw.Draw(neon)
    for box in ([CX - 54, top + 32, CX - 16, top + 64],
                [CX + 16, top + 32, CX + 54, top + 64]):
        nd.ellipse(box, outline=(66, 255, 156, 255), width=2)
    nd.line([(CX - 45, jaw_y - 16), (CX + 45, jaw_y - 16)],
            fill=(66, 255, 156, 235), width=2)
    base = art.screen(base, neon, glow_radius=12, gain=1.45, passes=2)

    # green neon ring arching over the hall
    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rg = ImageDraw.Draw(ring)
    rg.arc([-40, 8, 660, 150], 202, 338, fill=(70, 255, 168, 255), width=4)
    base = art.screen(base, ring, glow_radius=12, gain=1.4)

    # --- floor -----------------------------------------------------------
    d = ImageDraw.Draw(base)
    d.rectangle([0, FLOOR_Y, W, H], fill=(30, 26, 30))
    d.line([(0, FLOOR_Y), (W, FLOOR_Y)], fill=(116, 104, 92))
    base = art.wet_floor(base, FLOOR_Y + 3, (150, 200, 170), 34, seed=9)
    base = art.vignette(base, 0.55)
    base = art.grain(base, 5)

    # --- foreground pedestals -------------------------------------------
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    fd.rectangle([0, 232, W, H], fill=(6, 7, 9))
    rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd2 = ImageDraw.Draw(rim)
    for px in (CX - 132, CX + 132):
        fd.polygon([(px - 36, H), (px - 26, 208), (px + 26, 208), (px + 36, H)],
                   fill=(58, 54, 50))
        fd.rectangle([px - 30, 202, px + 30, 212], fill=(86, 80, 72))
        rd2.line([(px - 28, 205), (px + 28, 205)], fill=(70, 240, 160, 255), width=2)
    fg = Image.alpha_composite(fg, art.glow(rim, 8, 1.6))
    fg = Image.alpha_composite(fg, rim)
    return [
        ("bg", 0, 0, base, (START_X, 0), (1, 1), 0),
        ("fg", 3, 0, fg, (START_X, 0), (1, 1), 1),
    ]


# ------------------------------------------------------- Wing Kong Exchange
def stage_wingkong():
    base = art.vgrad((W, H), [
        (0, (16, 20, 38)), (54, (34, 38, 62)), (96, (56, 48, 50)),
        (FLOOR_Y, (42, 36, 38)), (H, (14, 14, 18)),
    ])
    d = ImageDraw.Draw(base)

    # distant Chinatown rooflines and a pagoda
    rnd = random.Random(4)
    for i in range(18):
        x = i * 36 - 10
        h = 44 + rnd.randint(0, 30)
        d.rectangle([x, 104 - h, x + 28, 106], fill=(24, 28, 46))
        d.polygon([(x - 8, 104 - h), (x + 14, 104 - h - 16), (x + 36, 104 - h)],
                  fill=(28, 32, 52))
    for i in range(4):
        y = 44 + i * 16
        d.polygon([(CX - 74, y), (CX, y - 14), (CX + 74, y)], fill=(34, 38, 60))
        d.rectangle([CX - 62, y, CX + 62, y + 5], fill=(30, 34, 54))

    # lantern strings in the distance
    far = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(far)
    for row in range(2):
        y0 = 74 + row * 12
        fd.arc([30, y0 - 22, 590, y0 + 22], 0, 180, fill=(70, 46, 32, 255), width=1)
        for x in range(56, 600, 42):
            art.lantern(fd, x, y0 + 4 + int(5 * math.sin(x / 40)), 5,
                        (222, 70, 44), (232, 186, 104))
    base = art.screen(base, far, glow_radius=7, gain=1.1)

    # brick warehouse facade
    d = ImageDraw.Draw(base)
    d.rectangle([0, 96, W, FLOOR_Y], fill=(84, 62, 50))
    for y in range(100, FLOOR_Y, 9):
        off = 0 if (y // 9) % 2 == 0 else 9
        for x in range(-off, W, 18):
            d.rectangle([x, y, x + 16, y + 7], fill=(94, 70, 56), outline=(62, 46, 38))
    # brick band under the sign
    d.rectangle([0, 96, W, 104], fill=(112, 86, 66))

    # loading bay: roll-up door with a lit lamp over it
    d.rectangle([CX - 84, 118, CX + 84, FLOOR_Y], fill=(50, 52, 58))
    for y in range(122, FLOOR_Y - 2, 7):
        d.rectangle([CX - 80, y, CX + 80, y + 4], fill=(66, 68, 76))
    d.rectangle([CX - 88, 112, CX + 88, 120], fill=(74, 76, 84))
    d.rectangle([CX - 6, 96, CX + 6, 114], fill=(40, 42, 48))

    # crates stacked either side
    for cx, cy, cw, ch in ((CX - 148, 158, 74, 44), (CX - 152, 120, 48, 34),
                           (CX + 84, 162, 70, 40), (CX + 132, 128, 44, 32)):
        d.rectangle([cx, cy, cx + cw, cy + ch], fill=(122, 88, 52))
        d.rectangle([cx + 3, cy + 3, cx + cw - 3, cy + ch - 3],
                    outline=(78, 54, 30), width=2)
        d.line([(cx + 4, cy + 4), (cx + cw - 4, cy + ch - 4)],
               fill=(96, 66, 38), width=2)
        d.line([(cx + cw - 4, cy + 4), (cx + 4, cy + ch - 4)],
               fill=(96, 66, 38), width=2)

    # wet asphalt + kerb
    d.rectangle([0, FLOOR_Y, W, H], fill=(38, 38, 44))
    d.rectangle([0, FLOOR_Y, W, FLOOR_Y + 4], fill=(92, 90, 92))
    for x in range(0, W, 58):
        d.rectangle([x, 214, x + 30, 224], fill=(82, 82, 88))

    # neon signage
    sign = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sign)
    big = art.font(30)
    small = art.font(11)
    sd.rectangle([CX - 132, 12, CX + 132, 62], fill=(12, 8, 12, 240))
    sd.rectangle([CX - 132, 12, CX + 132, 62], outline=(140, 32, 40, 255), width=2)
    sd.text((CX - 122, 15), "WING KONG", font=big, fill=(120, 255, 186, 255))
    sd.text((CX - 40, 44), "IMPORTS  *  EXCHANGE", font=small, fill=(255, 130, 200, 255))
    art.fake_glyph(sd, CX - 156, 104, 40, (255, 96, 62, 255), seed=5, width=4)
    sd.text((CX + 96, 78), "BAKERY", font=small, fill=(255, 206, 96, 255))
    sd.text((CX - 150, 82), "WING KONG TRADING CO.", font=small,
            fill=(214, 224, 255, 255))
    base = art.screen(base, sign, glow_radius=12, gain=1.55, passes=2)

    # hanging work lamps over the bay
    lamps = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lamps)
    for lx in (CX - 62, CX, CX + 62):
        ly = 74
        ld.line([(lx, 0), (lx, ly - 9)], fill=(58, 48, 38, 255), width=2)
        ld.polygon([(lx - 15, ly + 9), (lx + 15, ly + 9), (lx + 6, ly - 9),
                    (lx - 6, ly - 9)], fill=(84, 74, 62, 255))
        ld.ellipse([lx - 6, ly + 2, lx + 6, ly + 14], fill=(255, 244, 206, 255))
        base.alpha_composite(art.radial_light((W, H), (lx, ly + 46), 96,
                                              (255, 216, 154), 96))
    base = art.screen(base, lamps, glow_radius=8, gain=1.25)

    base = art.wet_floor(base, FLOOR_Y + 4, (128, 176, 210), 44, seed=13)
    base = art.rain(base, count=110, alpha=36, seed=21)
    base = art.vignette(base, 0.42)
    base = art.grain(base, 6)

    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    fd.rectangle([0, 232, W, H], fill=(6, 6, 8))
    for x in range(0, W, 78):
        fd.rectangle([x + 10, 224, x + 30, 234], fill=(9, 9, 12))
    return [
        ("bg", 0, 0, base, (START_X, 0), (1, 1), 0),
        ("fg", 3, 0, fg, (START_X, 0), (1, 1), 1),
    ]


# ------------------------------------------------------------- Chinatown Alley
def stage_alley():
    base = art.vgrad((W, H), [
        (0, (14, 18, 34)), (56, (26, 32, 52)), (120, (34, 30, 48)),
        (FLOOR_Y, (30, 26, 36)), (H, (12, 12, 18)),
    ])
    d = ImageDraw.Draw(base)

    # glow of the far street between the two alley walls
    base.alpha_composite(art.radial_light((W, H), (CX, 120), 190, (110, 140, 215), 92))

    # far buildings at the end of the alley
    rnd = random.Random(12)
    for i in range(6):
        x = CX - 62 + i * 22
        h = 60 + rnd.randint(0, 40)
        d.rectangle([x, 150 - h, x + 20, 168], fill=(30, 34, 54))
        for wy in range(150 - h + 8, 160, 12):
            d.rectangle([x + 5, wy, x + 9, wy + 5], fill=(96, 120, 170))

    # converging alley walls (left and right of the visible window)
    left = [(0, 0), (CX - 58, 76), (CX - 58, 190), (0, H)]
    right = [(W, 0), (CX + 58, 76), (CX + 58, 190), (W, H)]
    d.polygon(left, fill=(72, 58, 62))
    d.polygon(right, fill=(64, 52, 58))
    d.line([(CX - 58, 76), (CX - 58, 190)], fill=(96, 78, 78), width=2)
    d.line([(CX + 58, 76), (CX + 58, 190)], fill=(92, 74, 74), width=2)

    # brickwork on the near walls
    for y in range(6, FLOOR_Y, 11):
        t = y / H
        span = int((CX - 58) * (0.35 + t * 0.65))
        for x in range(0, span, 20):
            d.line([(x, y), (x + 14, y)], fill=(84, 68, 70))
            d.line([(W - x, y), (W - x - 14, y)], fill=(74, 60, 64))

    # fire escapes and window frames
    for y in (56, 92, 128):
        d.line([(4, y), (CX - 96, y + 16)], fill=(40, 36, 42), width=2)
        d.line([(CX + 96, y + 16), (W - 4, y)], fill=(40, 36, 42), width=2)
    for wx, wy in ((CX - 140, 108), (CX - 140, 62), (CX + 108, 108), (CX + 108, 62)):
        d.rectangle([wx, wy, wx + 34, wy + 24], fill=(52, 62, 84))
        d.rectangle([wx, wy, wx + 34, wy + 24], outline=(96, 84, 74), width=2)
        d.line([(wx + 17, wy), (wx + 17, wy + 24)], fill=(96, 84, 74))

    # neon: vertical shop signs plus the bar sign over the street
    neon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nd = ImageDraw.Draw(neon)
    for x, y, s, col, seed in ((CX - 152, 58, 34, (255, 60, 74), 3),
                               (CX - 152, 104, 28, (96, 224, 255), 8),
                               (CX + 118, 54, 34, (255, 196, 76), 12),
                               (CX + 122, 100, 28, (255, 96, 200), 17)):
        nd.rectangle([x - 6, y - 6, x + s + 6, y + s + 6], fill=(12, 6, 10, 255))
        art.fake_glyph(nd, x, y, s, col + (255,), seed=seed, width=4)
    bar = art.font(15)
    nd.text((CX - 104, 96), "DRAGON OF THE BLACK POOL", font=bar,
            fill=(255, 78, 66, 255))
    nd.rectangle([CX - 108, 92, CX + 110, 118], outline=(255, 66, 62, 210), width=1)
    base = art.screen(base, neon, glow_radius=11, gain=1.6, passes=2)

    # strung lanterns across the alley
    lant = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lant)
    ld.arc([CX - 170, 20, CX + 170, 82], 190, 350, fill=(48, 40, 34, 255), width=1)
    for x in range(CX - 160, CX + 161, 40):
        y = 34 + int(14 * math.sin((x - CX) / 220 * math.pi))
        ld.line([(x, y - 6), (x, y)], fill=(48, 40, 34, 255), width=1)
        art.lantern(ld, x, y + 7, 7, (216, 44, 44), (232, 190, 104))
        base.alpha_composite(art.radial_light((W, H), (x, y + 10), 34,
                                              (255, 130, 76), 66))
    base = art.screen(base, lant, glow_radius=6, gain=1.05)

    # wet cobbles and puddles
    d = ImageDraw.Draw(base)
    d.rectangle([0, FLOOR_Y, W, H], fill=(34, 33, 40))
    for y in range(FLOOR_Y + 4, H, 10):
        for x in range(-10, W, 24):
            d.ellipse([x, y, x + 20, y + 7], outline=(46, 45, 54))
    base = art.wet_floor(base, FLOOR_Y + 2, (120, 160, 220), 48, seed=31)

    # steam from a street grate
    steam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdw = ImageDraw.Draw(steam)
    for i in range(18):
        r = 10 + i * 5
        sdw.ellipse([CX - r, 172 - i * 7, CX + r, 184 - i * 7],
                    fill=(206, 214, 228, max(0, 40 - i * 2)))
    base = Image.alpha_composite(base, steam.filter(ImageFilter.GaussianBlur(8)))

    base = art.rain(base, count=170, alpha=46, seed=44)
    base = art.vignette(base, 0.45)
    base = art.grain(base, 6)

    # foreground: fire-escape uprights and a bin
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    fd.rectangle([0, 228, W, H], fill=(5, 5, 8))
    for x in (CX - 148, CX + 138):
        fd.rectangle([x, 150, x + 15, H], fill=(7, 7, 10))
    fd.rectangle([CX + 76, 200, CX + 116, 236], fill=(10, 10, 13))
    fd.ellipse([CX + 76, 194, CX + 116, 208], fill=(12, 12, 15))
    return [
        ("bg", 0, 0, base, (START_X, 0), (1, 1), 0),
        ("fg", 3, 0, fg, (START_X, 0), (1, 1), 1),
    ]


# --------------------------------------------------------- Pork Chop Express
def stage_highway():
    base = art.vgrad((W, H), [
        (0, (16, 20, 40)), (44, (40, 44, 76)), (96, (66, 60, 78)),
        (FLOOR_Y, (34, 32, 44)), (H, (14, 14, 20)),
    ])
    d = ImageDraw.Draw(base)

    # storm clouds
    rnd = random.Random(17)
    for _ in range(30):
        cx = rnd.randint(-40, W)
        cy = rnd.randint(0, 80)
        d.ellipse([cx, cy, cx + rnd.randint(70, 160), cy + rnd.randint(20, 46)],
                  fill=(44, 50, 78))
    d.ellipse([CX - 220, 18, CX + 10, 76], fill=(52, 58, 88))
    d.ellipse([CX + 40, 8, CX + 250, 68], fill=(48, 54, 84))

    # lightning
    bolt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bolt)
    pts = [(CX + 116, 6), (CX + 92, 46), (CX + 112, 48), (CX + 84, 88),
           (CX + 108, 86), (CX + 74, 130)]
    bd.line(pts, fill=(214, 232, 255, 255), width=4, joint="curve")
    base = art.screen(base, bolt, glow_radius=11, gain=1.7, passes=2)
    d = ImageDraw.Draw(base)   # screen() returns a new image; rebind the drawer

    # mountain ridges
    d.polygon([(0, 138), (74, 96), (150, 134), (232, 100), (310, 136),
               (396, 98), (486, 134), (566, 100), (W, 128), (W, 200), (0, 200)],
              fill=(36, 40, 62))
    d.polygon([(0, 166), (96, 132), (188, 164), (292, 136), (382, 166),
               (470, 138), (566, 168), (W, 150), (W, 200), (0, 200)],
              fill=(24, 26, 42))

    # night verge under the ridges: the road is narrower than the wide backdrop,
    # so the shoulders either side of it need paint instead of empty canvas.
    d.rectangle([0, 190, W, H], fill=(20, 22, 30))

    # road with perspective, vanishing point at the centre
    d.polygon([(CX - 16, 152), (CX + 16, 152), (CX + 168, H), (CX - 168, H)],
              fill=(96, 96, 112))
    d.polygon([(CX - 16, 152), (CX + 16, 152), (CX + 34, H), (CX - 34, H)],
              fill=(120, 120, 136))
    for i in range(9):
        t0, t1 = i / 9, (i + 1) / 9
        y0 = 156 + t0 * t0 * 80
        y1 = 156 + t1 * t1 * 80
        w0 = 2 + t0 * 9
        d.polygon([(CX - w0, y0), (CX + w0, y0), (CX + w0, y1), (CX - w0, y1)],
                  fill=(246, 238, 190))
    # guard rails
    for x0, x1, sx in ((CX - 168, CX - 22, -1), (CX + 22, CX + 168, 1)):
        d.line([(x0, 196), (x1, 158)], fill=(150, 156, 168), width=2)
        for k in range(6):
            t = k / 6
            gx = x0 + (x1 - x0) * t
            gy = 196 - 38 * t
            d.line([(gx, gy), (gx, gy + 10 - 6 * t)], fill=(120, 126, 140), width=2)
        _ = sx

    # headlight wash on the wet asphalt
    base.alpha_composite(art.radial_light((W, H), (CX, 214), 220, (255, 240, 200), 74))

    # highway sign for the express
    sign = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sign)
    f = art.font(13)
    sd.rectangle([CX - 150, 106, CX - 12, 140], fill=(14, 44, 32, 240))
    sd.rectangle([CX - 150, 106, CX - 12, 140], outline=(158, 245, 186, 235), width=1)
    sd.text((CX - 144, 110), "PORK CHOP EXPRESS", font=f, fill=(200, 255, 214, 255))
    sd.text((CX - 144, 124), "SAN FRANCISCO  12 MI", font=f, fill=(160, 240, 190, 255))
    base = art.screen(base, sign, glow_radius=7, gain=1.25)

    base = art.wet_floor(base, FLOOR_Y + 2, (160, 200, 240), 40, seed=57)
    base = art.rain(base, count=190, alpha=42, seed=63, angle=-0.34)
    base = art.vignette(base, 0.28)
    base = art.grain(base, 4)

    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    fd.rectangle([0, 230, W, H], fill=(6, 6, 9))
    for x in range(16, W, 112):
        fd.rectangle([x, 212, x + 5, 236], fill=(9, 9, 12))
    return [
        ("bg", 0, 0, base, (START_X, 0), (1, 1), 0),
        ("fg", 3, 0, fg, (START_X, 0), (1, 1), 1),
    ]


# ------------------------------------------------------------------ def writer
DEF_HEAD = """;---------------------------------------------------------------------------
; {name}
; Part of Big Trouble in Little China: The Game (Ikemen GO)
; Art and layout are original to this project. Generated by tools/build_stages.py.
;---------------------------------------------------------------------------
[Info]
name = "{name}"
displayname = "{display}"
versiondate = 10,28,2026
mugenversion = 1.0
author = "Big Trouble in Little China: The Game"

[Camera]
startx = 0
starty = 0
boundleft = -{scroll}
boundright = {scroll}
boundhigh = -25
boundlow = 0
verticalfollow = .2
floortension = 0
tension = 60
overdrawhigh = 0
overdrawlow = 0
cuthigh = 35
cutlow = 25
zoomout = 1
zoomin = 1

[PlayerInfo]
p1startx = -70
p1starty = 0
p1facing = 1
p2startx = 70
p2starty = 0
p2facing = -1
leftbound = -{playerbound}
rightbound = {playerbound}

[Bound]
screenleft = 15
screenright = 15

[StageInfo]
zoffset = 200
autoturn = 1
resetBG = 1
localcoord = 320, 240
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
bgmusic =
bgmvolume = 100

[BGdef]
spr = {sff}
debugbg = 0

; IKEMEN GO select-screen preview
[Begin Action 9000]
9000,1, 0,0, -1
"""

DEF_BG = """
[BG {key}]
type = normal
spriteno = {group},{number}
layerno = {layerno}
start = {sx},{sy}
delta = {dx},{dy}
trans = none
mask = {mask}
tile = 0,0
"""

STAGES = {
    "lopans_throne": dict(
        name="Lo Pan's Throne", display="Lo Pan's Throne", fn=stage_throne),
    "wingkong_exchange": dict(
        name="Wing Kong Exchange", display="Wing Kong Exchange", fn=stage_wingkong),
    "chinatown_alley": dict(
        name="Chinatown Back Alley", display="Chinatown Back Alley", fn=stage_alley),
    "porkchop_express": dict(
        name="Pork Chop Express", display="Pork Chop Express", fn=stage_highway),
}


def build(sid, spec):
    layers = spec["fn"]()
    sprites = []
    for key, group, number, img, start, delta, layerno in layers:
        sprites.append({"group": group, "number": number, "image": img,
                        "axis": (0, 0)})

    # select-screen preview: the centre of the composed backdrop
    comp = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    for key, group, number, img, start, delta, layerno in layers:
        comp.alpha_composite(img, (int(start[0] - START_X), int(start[1])))
        if os.environ.get("STAGE_DEBUG"):
            img.save(os.path.join(ROOT, "artifacts", f"{sid}_layer_{key}.png"))
    preview = comp.crop(VIEW).resize((320, 240), Image.LANCZOS)
    sprites.append({"group": 9000, "number": 1, "image": preview, "axis": (160, 120)})

    sff_data = sff.write_sff(sprites)
    with open(os.path.join(ROOT, "stages", f"{sid}.sff"), "wb") as f:
        f.write(sff_data)

    out = DEF_HEAD.format(name=spec["name"], display=spec["display"], sff=f"{sid}.sff",
                          scroll=SCROLL, playerbound=PLAYER_BOUND)
    for key, group, number, img, start, delta, layerno in layers:
        out += DEF_BG.format(key=key, group=group, number=number,
                             layerno=layerno, sx=start[0], sy=start[1],
                             dx=delta[0], dy=delta[1],
                             mask=1 if group != 0 else 0)
    with open(os.path.join(ROOT, "stages", f"{sid}.def"), "w") as f:
        f.write(out)

    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    comp.crop(VIEW).save(os.path.join(ROOT, "artifacts", f"{sid}_preview.png"))
    print(f"  {sid}: {len(sprites)} sprites, {len(sff_data) / 1024:.0f} KiB")


def main():
    print("Building stages")
    for sid, spec in STAGES.items():
        build(sid, spec)


if __name__ == "__main__":
    main()
