"""Lo Pan's Throne, painted from the throne-room concept art (1280x960).

Runs after tools/stages_hd.py in tools/build_all.py and replaces that arena's
files with a composition built around the reference art: a balconied mezzanine
whose recessed niches each hold a red neon ideogram, a cyan and red neon strip
along the balcony, a colossal skull gate whose open mouth is the doorway, and a
stone staircase that climbs off the plaza straight into that mouth.

Four things in this painter are worth keeping in mind before editing:

* Geometry is in *canvas* pixels. A 4:3 match view is 1280 of the 4000-wide
  canvas, so anything wider than ~600 px each side of CX is off-screen at match
  start however good it looks in the file.
* ``niche()`` builds every archway as a *recess*. Filling an arch flat in one
  stone tone makes it read as a bump standing proud of the wall; here the cavity
  is a set of concentric arch heads that darken toward the middle.
* ``skull_layer()`` models the face from a height field and **leaves the mouth
  hole transparent**. The staircase is painted into the base image first, so it
  shows through the mouth, and the teeth belong to the skull layer, so they
  overhang the stairs.
* ``art.screen()`` returns RGB with a fresh opaque alpha channel. Anything
  screened inside a cut-out layer needs its original alpha put back, or the
  whole layer box composites as a black rectangle.

The skull is composited after ``hd.finish()``: it is lit by its own neon, and
the frame's edge darkening turned it into a glass outline when it went through
the same pass as the wall behind it.

Run:  python3 tools/stage_throne.py          (part of tools/build_all.py)
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

BAY = px(64)                  # niche pitch along the hall
BALCONY = px(74)              # balcony line (parapet top) at the centre
GALLERY_AMP = px(44)          # how far the balcony dips out at the sides
GALLERY_SPAN = px(360)

SKULL_W = px(86)              # 344 canvas px
SKULL_H = px(92)              # 368
SKULL_TOP = px(6)             # whole dome stays in frame, like the reference
MOUTH_LIP_Y = SKULL_TOP + int(0.612 * SKULL_H)     # where the mouth opens
MOUTH_HALF = int(0.335 * SKULL_W)

STAIR_TOP = MOUTH_LIP_Y + 6   # first step, inside the mouth under the teeth
STAIR_KNEE = SKULL_TOP + SKULL_H + 8               # flight meets the cheek walls
STAIR_TOP_HALF = 36
STAIR_KNEE_HALF = 108
STAIR_FOOT_HALF = 304

LIGHTS = []                   # (cx, cy, radius, colour, peak) filled while painting


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rbox(x0, y0, x1, y1):
    """Ordered box: mirrored (sx=-1) coordinates otherwise fail in ImageDraw."""
    a, b = sorted((x0, x1))
    c, d = sorted((y0, y1))
    return [a, c, b, d]


def oval_pts(cx, cy, rx, ry, rot=0.0, n=22):
    """Tilted oval as a polygon: ImageDraw cannot rotate an ellipse in place."""
    ca, sa = math.cos(rot), math.sin(rot)
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        x, y = math.cos(a) * rx, math.sin(a) * ry
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return pts


# ------------------------------------------------------------------ the hall
def ring_y(x, off=0.0):
    """Height of the balcony line at x: flat behind the gate, dipping outward."""
    t = min(1.0, abs(x - CX) / float(GALLERY_SPAN)) ** 1.5
    return int(BALCONY + off + GALLERY_AMP * t)


def ring_line(d, off, color, width, gap=0):
    """Neon strip along the balcony, optionally broken around the gate."""
    pts = [(x, ring_y(x, off)) for x in range(0, W + 1, px(6))]
    w = max(1, int(width))
    if not gap:
        d.line(pts, fill=color, width=w, joint="curve")
        return
    for seg in ([p for p in pts if p[0] <= CX - gap],
                [p for p in pts if p[0] >= CX + gap]):
        if len(seg) > 1:
            d.line(seg, fill=color, width=w, joint="curve")


# ------------------------------------------------------------------ arches
def niche(d, cx, y_base, w, h, face=(104, 88, 70), reveal=(52, 40, 32),
          deep=(11, 8, 10), lacquer=(64, 38, 26), lights=False):
    """A recessed arched niche: dressed surround, stepped reveal, dark cavity.

    The cavity is painted as concentric arch heads that darken toward the
    middle, so the head curves away from the viewer instead of bulging out.
    """
    rv = max(2, int(px(3)))
    hd.arch(d, cx, y_base, w, h, face)
    hd.arch(d, cx, y_base - rv, w - 4 * rv, h - rv, reveal)

    inw, inh = w - 8 * rv, h - 3 * rv
    if inw < 8 or inh < 16:
        return
    r = inw / 2
    spring = y_base - inh / 2

    segs = 12
    for i in range(segs):
        t0 = i / segs
        y0 = spring + (y_base - spring) * t0
        y1 = spring + (y_base - spring) * (i + 1) / segs + 1
        d.rectangle([cx - r, y0, cx + r, y1],
                    fill=mix(deep, mix(deep, lacquer, 0.8), t0 ** 1.6))
    rings = 18
    for i in range(rings):
        f = i / (rings - 1)
        scale = 1.0 - f * 0.96
        rx, ry = r * scale, (inh / 2) * scale
        ccy = y_base - inh / 2
        d.chord([cx - rx, ccy - ry, cx + rx, ccy + ry], 180, 360,
                fill=mix(mix(deep, (26, 17, 15), 0.6), deep, f))

    side = max(1, rv // 2)
    d.line([(cx - r - rv * 0.6, spring), (cx - r - rv * 0.6, y_base - rv)],
           fill=(138, 118, 94), width=side)
    d.line([(cx + r + rv * 0.6, spring), (cx + r + rv * 0.6, y_base - rv)],
           fill=(44, 34, 28), width=side)
    d.polygon([(cx - px(3.2), y_base - inh + px(0.5)),
               (cx + px(3.2), y_base - inh + px(0.5)),
               (cx + px(5.0), y_base - inh + px(7)),
               (cx - px(5.0), y_base - inh + px(7))],
              fill=mix(face, (255, 240, 210), 0.16))
    d.rectangle([cx - r - rv, y_base - rv, cx + r + rv, y_base],
                fill=mix(face, (20, 14, 12), 0.45))
    d.line([(cx - r - rv, y_base - rv), (cx + r + rv, y_base - rv)],
           fill=mix(face, (255, 240, 210), 0.24), width=max(1, px(1)))
    if lights:
        LIGHTS.append((cx, y_base - px(9), px(24), (206, 128, 66), 96))


def corridor(d, cx, y_top, y_bot, w):
    """Lit floor visible at the back of a niche, so it reads as a passage."""
    d.rectangle([cx - w, y_bot - px(10), cx + w, y_bot - px(3)], fill=(96, 62, 38))
    d.line([(cx - w, y_bot - px(10)), (cx + w, y_bot - px(10))],
           fill=(140, 96, 58), width=max(1, px(1.2)))
    LIGHTS.append((cx, y_bot - px(14), px(13), (255, 170, 90), 96))
    _ = y_top


# ------------------------------------------------------------------ the gate
def stair(d, cx, y_top, y_bot, w_top, w_bot, steps, far_tone, near_tone, curve=1.0):
    """Perspective flight: lit treads, dark risers, a shadow under each nosing."""
    for i in range(steps):
        t0, t1 = i / steps, (i + 1) / steps
        y0 = y_top + (y_bot - y_top) * t0 ** curve
        y1 = y_top + (y_bot - y_top) * t1 ** curve
        w0 = w_top + (w_bot - w_top) * t0
        w1 = w_top + (w_bot - w_top) * t1
        tone = int(far_tone + (near_tone - far_tone) * t0)
        d.polygon([(cx - w0, y0), (cx + w0, y0), (cx + w1, y1), (cx - w1, y1)],
                  fill=(tone, int(tone * 0.90), int(tone * 0.80)))
        d.line([(cx - w1, y1), (cx + w1, y1)],
               fill=(max(0, tone - 40),) * 3, width=max(1, int(px(1.4))))
        d.line([(cx - w0, y0 + px(0.5)), (cx + w0, y0 + px(0.5))],
               fill=(min(255, tone + 22),) * 3, width=max(1, int(px(1))))


def cheek_wall(d, sx, y_top, w_top, band_top, y_bot, w_bot, band_bot):
    """Sloped wall alongside the stairs, topped by a lit coping."""
    pts = [(CX + sx * w_top, y_top), (CX + sx * (w_top + band_top), y_top),
           (CX + sx * (w_bot + band_bot), y_bot), (CX + sx * w_bot, y_bot)]
    d.polygon(pts, fill=(92, 78, 63))
    d.line([(CX + sx * w_top, y_top), (CX + sx * w_bot, y_bot)],
           fill=(150, 130, 104), width=max(2, int(px(1.6))))
    d.line([(CX + sx * (w_top + band_top), y_top),
            (CX + sx * (w_bot + band_bot), y_bot)],
           fill=(48, 39, 32), width=max(2, int(px(2))))
    # courses running down the slope
    for k in range(1, 6):
        t = k / 6
        x0 = CX + sx * (w_top + (w_bot - w_top) * t)
        x1 = CX + sx * (w_top + band_top + (w_bot - w_top + band_bot - band_top) * t)
        y = y_top + (y_bot - y_top) * t
        d.line([(x0, y), (x1, y)], fill=(70, 58, 46), width=max(1, int(px(1))))


def throat(base):
    """Dark passage behind the gate: depth, not a black rectangle.

    The shape is inset inside the bone frame and runs from near-black at the
    lip to a warm floor tone where the stairs enter, so the mouth reads as an
    opening with something behind it.
    """
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.polygon([(CX - MOUTH_HALF + 6, MOUTH_LIP_Y - 4),
                (CX, MOUTH_LIP_Y - 16),
                (CX + MOUTH_HALF - 6, MOUTH_LIP_Y - 4),
                (CX + MOUTH_HALF + 4, STAIR_KNEE - 10),
                (CX - MOUTH_HALF - 4, STAIR_KNEE - 10)], fill=255)
    grad = art.vgrad((W, H), [(MOUTH_LIP_Y - 20, (7, 7, 9)),
                              (MOUTH_LIP_Y + 40, (16, 12, 13)),
                              (STAIR_KNEE, (34, 26, 21))]).convert("RGBA")
    base.paste(grad, (0, 0), mask)
    LIGHTS.append((CX, MOUTH_LIP_Y + px(16), px(30), (46, 168, 104), 80))


# ------------------------------------------------------------------ the skull
def skull_layer():
    """Return (skull, neon) layers for the gate, mouth left transparent.

    The face is modelled from a height field rather than stacked flat shapes:
    the dome, brow, cheekbones and maxilla are smooth volumes, and hillshade()
    turns their gradients into light. Only the cavities (sockets, nasal
    aperture, mouth) and the teeth are painted as separate colours, which is
    what keeps it from reading as a cartoon face made of stickers.
    """
    ss = 2
    ws, hs = SKULL_W * ss, SKULL_H * ss
    color = Image.new("RGB", (ws, hs), (0, 0, 0))
    height = Image.new("L", (ws, hs), 0)
    dc, dh = ImageDraw.Draw(color), ImageDraw.Draw(height)
    bone = (206, 198, 178)

    def both(fn, fill, hv):
        fn(dc, fill)
        fn(dh, hv)

    def poly(pts, fill, hv):
        both(lambda d, f: d.polygon(pts, fill=f), fill, hv)

    def ell(box, fill, hv):
        both(lambda d, f: d.ellipse(box, fill=f), fill, hv)

    # --- bone volumes -------------------------------------------------------
    ell([0.020 * ws, 0.000 * hs, 0.980 * ws, 0.640 * hs], bone, 208)
    # frontal bossing: a soft keel down the forehead
    ell([0.390 * ws, 0.030 * hs, 0.610 * ws, 0.400 * hs], (210, 202, 182), 218)
    # brow ridge: an arc band, not a slab, so it can sit above the sockets
    for sx in (-1, 1):
        poly([(ws * 0.5 + sx * ws * 0.455, hs * 0.352),
              (ws * 0.5 + sx * ws * 0.400, hs * 0.300),
              (ws * 0.5 + sx * ws * 0.230, hs * 0.278),
              (ws * 0.5 + sx * ws * 0.060, hs * 0.286),
              (ws * 0.5 + sx * ws * 0.020, hs * 0.330),
              (ws * 0.5 + sx * ws * 0.090, hs * 0.360),
              (ws * 0.5 + sx * ws * 0.300, hs * 0.352),
              (ws * 0.5 + sx * ws * 0.445, hs * 0.365)], (210, 202, 182), 238)
        # zygomatic ridge sweeping back from the outer orbit
        dc.line([(ws * 0.5 + sx * ws * 0.300, hs * 0.398),
                 (ws * 0.5 + sx * ws * 0.452, hs * 0.372)],
                fill=(224, 216, 196), width=max(1, int(ws * 0.010)))
        poly([(ws * 0.5 + sx * ws * 0.300, hs * 0.380),
              (ws * 0.5 + sx * ws * 0.492, hs * 0.384),
              (ws * 0.5 + sx * ws * 0.486, hs * 0.470),
              (ws * 0.5 + sx * ws * 0.292, hs * 0.492)], (196, 188, 168), 224)
        # cheek: a soft fossa under the orbit
        ell(rbox(ws * 0.5 + sx * ws * 0.120, hs * 0.500,
                 ws * 0.5 + sx * ws * 0.310, hs * 0.590), bone, 190)
    # glabella
    ell([0.462 * ws, hs * 0.296, 0.538 * ws, hs * 0.372], (212, 204, 184), 232)
    # maxilla, and the alveolar ridge the teeth hang from
    poly([(ws * 0.180, hs * 0.430), (ws * 0.820, hs * 0.430),
          (ws * 0.845, hs * 0.700), (ws * 0.820, hs * 1.02),
          (ws * 0.180, hs * 1.02), (ws * 0.155, hs * 0.700)],
         (196, 188, 168), 202)
    poly([(ws * 0.190, hs * 0.568), (ws * 0.810, hs * 0.568),
          (ws * 0.822, hs * 0.606), (ws * 0.178, hs * 0.606)],
         (202, 194, 174), 236)
    # nasal bridge
    poly([(0.486 * ws, hs * 0.300), (0.514 * ws, hs * 0.300),
          (0.522 * ws, hs * 0.470), (0.500 * ws, hs * 0.486),
          (0.478 * ws, hs * 0.470)], (200, 192, 172), 226)

    # bone darkens toward the jaw: faces read better with a vertical falloff
    grad = art.vgrad((ws, hs), [(0, (255, 251, 242)),
                                (int(hs * 0.52), (228, 222, 206)),
                                (hs, (140, 134, 118))]).convert("RGB")
    color = ImageChops.multiply(color, grad)
    mottle = Image.effect_noise((ws // 8, hs // 8), 46).resize((ws, hs), Image.BILINEAR)
    mottle = mottle.point(lambda v: 226 + min(29, v // 9))
    color = ImageChops.multiply(color, Image.merge("RGB", (mottle, mottle, mottle)))

    # --- cavities -----------------------------------------------------------
    for sx in (-1, 1):
        cxs = ws * 0.5 + sx * ws * 0.168
        poly(oval_pts(cxs, hs * 0.430, ws * 0.162, hs * 0.104, rot=sx * 0.22),
             (14, 12, 13), 38)
        poly(oval_pts(cxs + sx * ws * 0.012, hs * 0.442, ws * 0.126, hs * 0.074,
                      rot=sx * 0.22), (4, 4, 5), 20)
        # the notch the optic nerve leaves, and the tear duct at the inner corner
        poly([(cxs + sx * ws * 0.100, hs * 0.352), (cxs + sx * ws * 0.150, hs * 0.372),
              (cxs + sx * ws * 0.090, hs * 0.410)], (20, 17, 18), 44)
        poly([(cxs - sx * ws * 0.140, hs * 0.436), (cxs - sx * ws * 0.108, hs * 0.408),
              (cxs - sx * ws * 0.096, hs * 0.468)], (10, 9, 10), 34)
        dc.ellipse([cxs - ws * 0.030, hs * 0.478, cxs + ws * 0.030, hs * 0.518],
                   fill=(26, 106, 68))
        dc.ellipse([cxs - ws * 0.013, hs * 0.490, cxs + ws * 0.013, hs * 0.508],
                   fill=(118, 210, 148))
    # nasal aperture
    poly([(0.500 * ws, hs * 0.470), (0.462 * ws, hs * 0.520),
          (0.444 * ws, hs * 0.588), (0.472 * ws, hs * 0.610),
          (0.500 * ws, hs * 0.590), (0.528 * ws, hs * 0.610),
          (0.556 * ws, hs * 0.588), (0.538 * ws, hs * 0.520)], (7, 6, 7), 24)
    dc.line([(0.500 * ws, hs * 0.545), (0.500 * ws, hs * 0.600)],
            fill=(150, 142, 124), width=max(1, int(ws * 0.008)))

    # --- mouth: transparent, the staircase shows through it -----------------
    mouth = [(0.176 * ws, hs * 0.606), (0.500 * ws, hs * 0.580),
             (0.824 * ws, hs * 0.606), (0.856 * ws, hs * 0.780),
             (0.828 * ws, hs * 1.02), (0.172 * ws, hs * 1.02),
             (0.144 * ws, hs * 0.780)]
    poly(mouth, (0, 0, 0), 0)

    # --- teeth --------------------------------------------------------------
    def tooth(bx, y0, half, tip, lean=0.0):
        pts = [(bx - half, y0), (bx + half, y0),
               (bx + half * 0.72 + lean, y0 + (tip - y0) * 0.5),
               (bx + lean, tip),
               (bx - half * 0.62 + lean, y0 + (tip - y0) * 0.58)]
        poly(pts, (232, 226, 206), 250)
        dc.line([(bx - half * 0.30, y0 + px(1)), (bx + lean * 0.7, tip - px(2))],
                fill=(196, 188, 166), width=max(1, int(ws * 0.005)))

    row_y = hs * 0.586
    for k in range(-2, 3):
        bx = ws * 0.5 + k * ws * 0.066
        tooth(bx, row_y, ws * 0.025, row_y + hs * (0.070 if abs(k) < 2 else 0.080))
    for sx in (-1, 1):
        tooth(ws * 0.5 + sx * ws * 0.232, hs * 0.592, ws * 0.037,
              hs * 0.790, lean=sx * ws * 0.012)
        tooth(ws * 0.5 + sx * ws * 0.322, hs * 0.588, ws * 0.030,
              hs * 0.706, lean=sx * ws * 0.007)
    # gum line shadow
    dc.line([(ws * 0.19, hs * 0.590), (ws * 0.81, hs * 0.590)],
            fill=(116, 92, 74), width=max(1, int(hs * 0.007)))

    # --- cracks and a chipped dome -----------------------------------------
    rnd = random.Random(11)

    def crack(x0, y0, x1, y1, wid):
        pts = [(ws * x0, hs * y0)]
        for i in range(1, 6):
            t = i / 6
            pts.append((ws * (x0 + (x1 - x0) * t) + rnd.uniform(-ws * 0.006, ws * 0.006),
                        hs * (y0 + (y1 - y0) * t)))
        pts.append((ws * x1, hs * y1))
        dc.line(pts, fill=(126, 118, 102), width=max(1, wid), joint="curve")
        dh.line(pts, fill=198, width=max(1, wid))

    crack(0.500, 0.040, 0.500, 0.240, int(ws * 0.006))
    crack(0.330, 0.060, 0.215, 0.250, int(ws * 0.005))
    crack(0.690, 0.055, 0.805, 0.245, int(ws * 0.005))
    crack(0.610, 0.030, 0.648, 0.140, int(ws * 0.004))
    poly([(0.842 * ws, hs * 0.052), (0.896 * ws, hs * 0.078),
          (0.884 * ws, hs * 0.138), (0.836 * ws, hs * 0.112)], (0, 0, 0), 0)

    # --- downsample, shade, then paint soft light on top --------------------
    color = color.resize((SKULL_W, SKULL_H), Image.LANCZOS)
    height = height.resize((SKULL_W, SKULL_H), Image.LANCZOS)

    alpha = height.point(lambda v: 255 if v > 24 else 0)
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.8))
    shade = hd.hillshade(height, 4.6)
    rgb = ImageChops.multiply(color, Image.merge("RGB", (shade, shade, shade)))
    layer = rgb.convert("RGBA")
    layer.putalpha(alpha)

    def overlay(fn, blur):
        ov = Image.new("RGBA", (SKULL_W, SKULL_H), (0, 0, 0, 0))
        fn(ImageDraw.Draw(ov))
        ov = ov.filter(ImageFilter.GaussianBlur(blur))
        ov.putalpha(ImageChops.multiply(ov.split()[3], alpha))
        return ov

    def shadows(d):
        for sx in (-1, 1):
            cxs = SKULL_W * 0.5 + sx * SKULL_W * 0.168
            d.ellipse(rbox(cxs - SKULL_W * 0.150, SKULL_H * 0.372,
                           cxs + SKULL_W * 0.150, SKULL_H * 0.492),
                      fill=(0, 0, 0, 120))
            d.ellipse(rbox(SKULL_W * 0.5 + sx * SKULL_W * 0.140, SKULL_H * 0.322,
                           SKULL_W * 0.5 + sx * SKULL_W * 0.340, SKULL_H * 0.398),
                      fill=(0, 0, 0, 104))
        d.polygon([(SKULL_W * 0.470, SKULL_H * 0.500), (SKULL_W * 0.530, SKULL_H * 0.500),
                   (SKULL_W * 0.545, SKULL_H * 0.600), (SKULL_W * 0.455, SKULL_H * 0.600)],
                  fill=(20, 14, 12, 56))

    def highlights(d):
        d.polygon([(SKULL_W * 0.12, SKULL_H * 0.055), (SKULL_W * 0.40, SKULL_H * 0.008),
                   (SKULL_W * 0.44, SKULL_H * 0.050), (SKULL_W * 0.16, SKULL_H * 0.112)],
                  fill=(255, 250, 232, 58))
        for sx in (-1, 1):
            cxs = SKULL_W * 0.5 + sx * SKULL_W * 0.168
            d.arc(rbox(cxs - SKULL_W * 0.138, SKULL_H * 0.330,
                       cxs + SKULL_W * 0.138, SKULL_H * 0.522), 16, 96,
                  fill=(255, 250, 232, 66), width=max(1, int(SKULL_W * 0.010)))

    layer = Image.alpha_composite(layer, overlay(shadows, SKULL_W * 0.016))
    layer = Image.alpha_composite(layer, overlay(highlights, SKULL_W * 0.010))

    # green underlight spilling up out of the mouth
    under = Image.new("RGBA", (SKULL_W, SKULL_H), (0, 0, 0, 0))
    ud = ImageDraw.Draw(under)
    for i in range(40):
        t = i / 40
        a = int(74 * (1 - t) ** 2)
        ud.rectangle(rbox(0, SKULL_H * (1.0 - t * 0.50), SKULL_W,
                          SKULL_H * (1.0 - (i + 1) / 40 * 0.50)),
                     fill=(34, 176, 108, a))
    under.putalpha(ImageChops.multiply(under.split()[3], alpha))
    layer = art.screen(layer, under, glow_radius=SKULL_W * 0.02, gain=1.0)
    layer.putalpha(alpha)          # screen() returns an opaque alpha channel

    # --- neon rim -----------------------------------------------------------
    sil = alpha.copy()
    sd = ImageDraw.Draw(sil)
    sd.polygon([(0.150 * SKULL_W, 0.604 * SKULL_H), (0.500 * SKULL_W, 0.578 * SKULL_H),
                (0.850 * SKULL_W, 0.604 * SKULL_H), (0.870 * SKULL_W, 1.0 * SKULL_H),
                (0.130 * SKULL_W, 1.0 * SKULL_H)], fill=255)
    rim = art.outline(sil, (46, 208, 128), thickness=max(2, int(SKULL_W * 0.009)),
                      expand=1)
    hot = art.outline(sil, (150, 246, 196), thickness=max(1, int(SKULL_W * 0.003)),
                      expand=2)
    neon = Image.alpha_composite(rim, hot)

    def full(img):
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        out.alpha_composite(img, (int(CX - SKULL_W / 2), int(SKULL_TOP)))
        return out

    return full(layer), full(neon)


# ------------------------------------------------------------------ the floor
def plaza(d, y_top):
    """Tiled plaza in one-point perspective with an engraved inlay ring."""
    d.rectangle([0, y_top, W, H], fill=(56, 44, 42))
    y, gap = y_top, px(3)
    while y < H:
        y2 = min(H, y + gap)
        lift = int(12 * (y - y_top) / max(1, H - y_top))
        d.rectangle([0, y, W, y2], fill=(62 + lift, 49 + lift, 45 + lift))
        d.line([(0, y), (W, y)], fill=(31, 24, 24), width=max(1, int(px(0.7))))
        y = y2
        gap *= 1.30
    for k in range(-40, 41):
        x_top = CX + k * px(20)
        d.line([(x_top, y_top), (CX + (x_top - CX) * 3.6, H)],
               fill=(34, 26, 26), width=max(1, int(px(0.7))))
    for rx, ry, col, wdt in ((px(330), px(120), (116, 98, 80), px(1.8)),
                             (px(316), px(114), (38, 31, 30), px(1.4)),
                             (px(150), px(58), (108, 90, 74), px(1.4))):
        d.arc([CX - rx, y_top - ry + px(8), CX + rx, y_top + ry + px(8)],
              16, 164, fill=col, width=max(1, int(wdt)))


# ------------------------------------------------------------------ the arena
def paint():
    LIGHTS.clear()
    base = hd.blank([
        (0, (14, 8, 9)), (40, (52, 24, 20)), (86, (62, 30, 23)),
        (130, (44, 24, 20)), (170, (32, 20, 19)), (200, (18, 12, 13)),
        (240, (8, 7, 9)),
    ])
    d = ImageDraw.Draw(base)

    hd.stone(d, 0, 0, W, FLOOR_Y, (54, 39, 35), (29, 21, 20), rows=62, seed=12,
             jitter=0.55)
    for x in range(0, W, px(44)):
        d.rectangle([x + px(3), px(1), x + px(38), px(9)], fill=(21, 13, 13))

    # balcony mezzanine: a recessed niche per bay, holding a neon ideogram
    neon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nd = ImageDraw.Draw(neon)
    for i in range(-9, 10):
        if i == 0:
            continue
        x = CX + i * BAY
        if not (-BAY < x < W + BAY):
            continue
        y0 = ring_y(x)
        niche(d, x, y0 - px(3), BAY * 0.60, px(40), face=(94, 78, 63),
              deep=(9, 7, 9), lights=False)
        hd.glyph(nd, x - BAY * 0.10, y0 - px(31), BAY * 0.20, (255, 54, 38),
                 seed=i + 4, width=px(1.8))
        nd.rectangle([x - BAY * 0.115, y0 - px(36), x + BAY * 0.115, y0 - px(6)],
                     outline=(255, 46, 34), width=max(1, px(0.9)))

    # balustrade: dark rail, lit coping, slim balusters, neon along the curve
    for i in range(-9, 10):
        x = CX + i * BAY
        if not (-BAY < x < W + BAY):
            continue
        y0 = ring_y(x)
        d.rectangle([x - BAY / 2, y0, x + BAY / 2, y0 + px(12)], fill=(46, 34, 30))
        for k in range(-4, 5):
            bxx = x + k * BAY * 0.105
            d.rectangle([bxx - px(1.3), y0 + px(2), bxx + px(1.3), y0 + px(12)],
                        fill=(102, 88, 72))
        d.line([(x - BAY / 2, y0), (x + BAY / 2, y0)], fill=(158, 138, 114),
               width=max(1, px(1.6)))
    gate_gap = MOUTH_HALF + px(10)
    ring_line(nd, px(1.5), (58, 214, 240), px(2.2), gap=gate_gap)
    ring_line(nd, px(4.5), (238, 52, 42), px(1.6), gap=gate_gap)

    # ground-floor arcade: recessed arches into lit corridors
    for i in range(-9, 10):
        if i == 0:
            continue
        x = CX + i * BAY
        if not (-BAY < x < W + BAY):
            continue
        y0 = ring_y(x)
        base_y = FLOOR_Y - px(8)
        h = min(px(104), base_y - (y0 + px(24)))
        if h < px(46):
            continue
        niche(d, x, base_y, BAY * 0.80, h, face=(86, 72, 58),
              deep=(12, 9, 10), lacquer=(74, 42, 28), lights=False)
        corridor(d, x, base_y - h, base_y, BAY * 0.26)
        if i % 2 == 0:
            hd.torch(d, x + BAY * 0.33, base_y - px(52))

    # gate: dark throat, then the staircase climbing into the mouth
    throat(base)
    d = ImageDraw.Draw(base)
    stair(d, CX, STAIR_TOP, STAIR_KNEE, STAIR_TOP_HALF, STAIR_KNEE_HALF, 6, 96, 66,
          curve=1.4)
    stair(d, CX, STAIR_KNEE, FLOOR_Y, STAIR_KNEE_HALF, STAIR_FOOT_HALF, 10, 58, 132)
    for sx in (-1, 1):
        cheek_wall(d, sx, STAIR_KNEE, STAIR_KNEE_HALF, 12, FLOOR_Y,
                   STAIR_FOOT_HALF, 36)
    LIGHTS.append((CX, FLOOR_Y - px(30), px(110), (40, 190, 114), 60))
    LIGHTS.append((CX, MOUTH_LIP_Y + px(16), px(34), (46, 176, 106), 92))

    # guardians either side of the stair foot, fire bowls between them
    for sx in (-1, 1):
        base = hd.guardian(base, CX + sx * px(126), FLOOR_Y, px(30))
    d = ImageDraw.Draw(base)
    for sx in (-1, 1):
        hd.brazier(d, CX + sx * px(88), FLOOR_Y, px(26))
        LIGHTS.append((CX + sx * px(88), FLOOR_Y - px(16), px(52), (255, 168, 88), 140))
    plaza(d, FLOOR_Y)

    base = hd.shade(base, [(hd.light(cx, cy, r, col, peak), px(10), 1.15)
                           for cx, cy, r, col, peak in LIGHTS])

    # foreground lip: a dark stone edge across the bottom of the frame
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    for i in range(px(26)):
        a = int(200 * (1 - i / px(26)) ** 1.6)
        fd.line([(0, H - i), (W, H - i)], fill=(6, 5, 8, a))

    painted = hd.finish(base, 5, 3, 0.34, FLOOR_Y)
    painted = art.screen(painted, neon, glow_radius=px(3), gain=1.5, passes=2)

    # green ring arching over the hall, behind the skull
    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rg = ImageDraw.Draw(ring)
    rg.arc([CX - px(190), -px(10), CX + px(190), px(210)], 196, 344,
           fill=(64, 246, 160), width=max(2, px(1.6)))
    painted = art.screen(painted, ring, glow_radius=px(4), gain=1.3)

    skull, rim = skull_layer()
    painted = Image.alpha_composite(painted, skull)
    painted = art.screen(painted, rim, glow_radius=px(1.5), gain=0.26, passes=2)
    return [("bg", 0, 0, painted, 0),
            ("fg", 3, 0, fg, 1)]


def main():
    hd.STAGES["lopans_throne"] = ("Lo Pan's Throne", paint)
    hd.build("lopans_throne")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
