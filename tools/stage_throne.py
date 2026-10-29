"""Lo Pan's Throne, painted from the throne-room concept art (1280x960).

Runs after tools/stages_hd.py in tools/build_all.py and replaces that arena's
files with a composition built around the reference art: a ring-shaped
mezzanine whose arched niches each hold a red neon ideogram, a cyan and red
neon strip tracing the balcony edge, a colossal fanged skull over the gate
ringed in green neon, and a stone staircase down to a tiled plaza with guardian
lions and fire bowls at its foot.

Geometry (canvas, camera travel, floor line, localcoord) is owned by
tools/stages_hd.py; only the painting lives here.

Run:  python3 tools/stage_throne.py          (part of tools/build_all.py)
"""

from __future__ import annotations

import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import stages_hd as hd

W, H = hd.W, hd.H
CX = hd.CX
FLOOR_Y = hd.FLOOR_Y
px = hd.px

GALLERY_AMP = px(92)          # how far the ring dips at the canvas ends
GALLERY_SPAN = px(520)
BAY = px(64)                  # niche pitch along the ring


# ------------------------------------------------------------------ the ring
def ring_y(x, offset=0.0):
    """Height of the mezzanine ring at x: flat behind the gate, dipping outward."""
    t = min(1.0, abs(x - CX) / float(GALLERY_SPAN))
    return int(px(26) + offset + GALLERY_AMP * t ** 1.7)


def ring_line(d, offset, color, width):
    """Bright strip that follows the ring's curve."""
    pts = [(x, ring_y(x, offset)) for x in range(0, W + 1, px(8))]
    d.line(pts, fill=color, width=max(1, int(width)), joint="curve")


# ------------------------------------------------------------------ shading
def hillshade(height, strength=5.0):
    """Emboss a height map into a shade multiplier, lit from the upper left.

    ImageChops.subtract clamps at zero, so each axis needs both a "falling
    towards the light" and a "falling away" term to keep the gradient signed.
    The multiplier itself has to sit near white: it scales the albedo, so a
    mid-grey bias would turn every sculpture into a silhouette.
    """
    radius = max(1.5, height.size[0] * 0.02)
    hmap = height.filter(ImageFilter.GaussianBlur(radius))
    right = ImageChops.offset(hmap, 2, 0)
    down = ImageChops.offset(hmap, 0, 2)

    def swing(low, high):
        lit = ImageChops.subtract(low, high).point(lambda v: min(130, int(v * strength)))
        dark = ImageChops.subtract(high, low).point(lambda v: min(130, int(v * strength)))
        return lit, dark

    shade = Image.new("L", height.size, 208)
    for lit, dark in (swing(hmap, right), swing(hmap, down)):
        shade = ImageChops.add(shade, lit)
        shade = ImageChops.subtract(shade, dark)
    return shade


def sculpted(color, height, cx, y_base):
    """Composite a colour + height pair onto the full canvas, bottom at y_base."""
    shade = hillshade(height)
    rgb = ImageChops.multiply(color, Image.merge("RGB", (shade, shade, shade)))
    rgba = rgb.convert("RGBA")
    alpha = height.point(lambda v: 255 if v > 28 else 0).filter(ImageFilter.GaussianBlur(1))
    rgba.putalpha(alpha)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.alpha_composite(rgba, (int(cx - color.size[0] / 2), int(y_base - color.size[1])))
    return layer


# ------------------------------------------------------------------ props
def torch(d, cx, cy, h=None):
    """Wall sconce: bracket, cup, three flame tongues. cy is the bracket foot."""
    h = h or px(18)
    d.rectangle([cx - px(1.4), cy - h * 0.42, cx + px(1.4), cy], fill=(56, 43, 33))
    d.rectangle([cx - px(4.4), cy - h * 0.60, cx + px(4.4), cy - h * 0.40],
                fill=(92, 71, 48))
    d.rectangle([cx - px(3.4), cy - h * 0.60, cx + px(3.4), cy - h * 0.50],
                fill=(214, 132, 52))
    for off, tall in ((-0.55, 0.72), (0.05, 1.0), (0.55, 0.66)):
        fx = cx + off * px(3.2)
        top = cy - h * 0.60 - h * 0.44 * tall
        d.polygon([(fx - px(2.2), cy - h * 0.58), (fx + px(2.2), cy - h * 0.58),
                   (fx, top)], fill=(255, 164, 62))
    d.polygon([(cx - px(1.4), cy - h * 0.58), (cx + px(1.4), cy - h * 0.58),
               (cx, cy - h * 0.86)], fill=(255, 236, 174))


def brazier(d, cx, y_base, h, flame=(255, 176, 70)):
    """Tripod fire bowl on the plaza: slim legs, wide bowl, clustered flame."""
    bw = h * 0.26
    for sx in (-1, 1):
        d.line([(cx + sx * bw * 0.45, y_base - h * 0.44),
                (cx + sx * bw * 0.95, y_base)], fill=(62, 48, 36),
               width=max(1, int(px(1.6))))
    d.rectangle([cx - px(1.6), y_base - h * 0.48, cx + px(1.6), y_base - h * 0.36],
                fill=(70, 55, 40))
    d.polygon([(cx - bw, y_base - h * 0.72), (cx + bw, y_base - h * 0.72),
               (cx + bw * 0.55, y_base - h * 0.40), (cx - bw * 0.55, y_base - h * 0.40)],
              fill=(118, 86, 48))
    d.ellipse([cx - bw, y_base - h * 0.80, cx + bw, y_base - h * 0.64], fill=(160, 116, 58))
    d.ellipse([cx - bw * 0.78, y_base - h * 0.78, cx + bw * 0.78, y_base - h * 0.66],
              fill=(226, 144, 54))
    for off, tall, wide in ((-0.58, 0.40, 1.0), (-0.20, 0.66, 1.1), (0.14, 0.84, 0.9),
                            (0.46, 0.52, 0.9)):
        fx = cx + off * bw * 1.15
        fw = bw * 0.34 * wide
        top = y_base - h * 0.76 - h * tall * 0.44
        d.polygon([(fx - fw, y_base - h * 0.78), (fx + fw, y_base - h * 0.78),
                   (fx + fw * 0.45, top + h * 0.10), (fx, top),
                   (fx - fw * 0.45, top + h * 0.10)], fill=flame)
    d.ellipse([cx - bw * 0.55, y_base - h * 0.86, cx + bw * 0.55, y_base - h * 0.74],
              fill=(255, 226, 150))


def guardian(base, cx, y_base, h):
    """Frontal stone lion on a plinth, sculpted from a height field."""
    ws, hs = int(h * 0.98), int(h * 1.04)
    color = Image.new("RGB", (ws, hs), (0, 0, 0))
    height = Image.new("L", (ws, hs), 0)
    dc, dh = ImageDraw.Draw(color), ImageDraw.Draw(height)
    body = (170, 160, 142)
    dark = (140, 131, 114)

    def both(shape, fill, hv):
        shape(dc, fill)
        shape(dh, hv)

    both(lambda d, f: d.rectangle([ws * 0.04, hs * 0.90, ws * 0.96, hs], fill=f),
         (146, 137, 120), 152)
    both(lambda d, f: d.ellipse([ws * 0.08, hs * 0.56, ws * 0.92, hs * 0.94], fill=f),
         body, 208)
    both(lambda d, f: d.polygon([(ws * 0.26, hs * 0.42), (ws * 0.74, hs * 0.42),
                                 (ws * 0.86, hs * 0.90), (ws * 0.14, hs * 0.90)], fill=f),
         body, 226)
    for lx in (0.27, 0.63):
        both(lambda d, f, lx=lx: d.rectangle(
            [ws * lx, hs * 0.60, ws * (lx + 0.10), hs * 0.92], fill=f), body, 238)
        both(lambda d, f, lx=lx: d.ellipse(
            [ws * lx - ws * 0.02, hs * 0.86, ws * (lx + 0.12), hs * 0.96], fill=f),
            (156, 147, 130), 244)
    both(lambda d, f: d.ellipse([ws * 0.16, hs * 0.02, ws * 0.84, hs * 0.60], fill=f),
         dark, 204)
    for k in range(12):
        a = 2 * math.pi * k / 12
        mx, my = ws * 0.5 + math.cos(a) * ws * 0.32, hs * 0.30 + math.sin(a) * ws * 0.28
        both(lambda d, f, mx=mx, my=my: d.ellipse(
            [mx - ws * 0.055, my - ws * 0.055, mx + ws * 0.055, my + ws * 0.055],
            fill=f), (158, 149, 132), 216)
    both(lambda d, f: d.ellipse([ws * 0.33, hs * 0.16, ws * 0.67, hs * 0.50], fill=f),
         body, 252)
    both(lambda d, f: d.rounded_rectangle([ws * 0.40, hs * 0.28, ws * 0.60, hs * 0.42],
                                          radius=hs * 0.05, fill=f),
         (182, 172, 154), 255)
    both(lambda d, f: d.ellipse([ws * 0.40, hs * 0.38, ws * 0.60, hs * 0.50], fill=f),
         (104, 96, 84), 206)
    for ex, sgn in ((0.35, -1), (0.65, 1)):
        both(lambda d, f, ex=ex, sgn=sgn: d.polygon(
            [(ws * ex, hs * 0.18), (ws * (ex + sgn * 0.09), hs * 0.16),
             (ws * (ex + sgn * 0.03), hs * 0.05)], fill=f), (156, 147, 130), 240)
    for ex in (0.42, 0.58):
        both(lambda d, f, ex=ex: d.ellipse([ws * ex - ws * 0.045, hs * 0.24,
                                            ws * ex + ws * 0.045, hs * 0.31], fill=f),
             (34, 28, 25), 104)
        both(lambda d, f, ex=ex: d.rectangle([ws * ex - ws * 0.06, hs * 0.205,
                                              ws * ex + ws * 0.06, hs * 0.235], fill=f),
             (196, 186, 166), 250)
    return Image.alpha_composite(base, sculpted(color, height, cx, y_base))


def stair(d, cx, y_top, y_bot, w_top, w_bot, steps=13):
    """Perspective flight descending toward the camera; treads lit, risers dark."""
    for i in range(steps):
        t0, t1 = i / steps, (i + 1) / steps
        y0 = y_top + (y_bot - y_top) * t0 ** 1.45
        y1 = y_top + (y_bot - y_top) * t1 ** 1.45
        w0 = w_top + (w_bot - w_top) * t0
        w1 = w_top + (w_bot - w_top) * t1
        tone = 132 - int(52 * t0)
        d.polygon([(cx - w0, y0), (cx + w0, y0), (cx + w1, y1), (cx - w1, y1)],
                  fill=(tone, tone - 12, tone - 22))
        d.line([(cx - w1, y1), (cx + w1, y1)], fill=(58, 50, 44),
               width=max(1, int(px(1.2))))
    for sx in (-1, 1):
        d.line([(cx + sx * w_top, y_top), (cx + sx * w_bot, y_bot)],
               fill=(150, 134, 112), width=max(2, int(px(2))))


def skull_layer(cx, top, w, h):
    """Return (skull, neon rim) layers for the gate.

    The skull goes on after the vignette: it is lit by its own neon, and running
    it through the frame's edge darkening turned it into a glass outline.
    """
    ws, hs = int(w), int(h)
    color = Image.new("RGB", (ws, hs), (0, 0, 0))
    height = Image.new("L", (ws, hs), 0)
    dc, dh = ImageDraw.Draw(color), ImageDraw.Draw(height)
    bone = (200, 194, 178)

    # cranium, then the zygomatic arches narrowing into the maxilla
    dc.ellipse([0, 0, ws, hs * 0.72], fill=bone)
    dh.ellipse([0, 0, ws, hs * 0.72], fill=226)
    jaw = [(ws * 0.05, hs * 0.36), (ws * 0.16, hs * 0.90), (ws * 0.84, hs * 0.90),
           (ws * 0.95, hs * 0.36)]
    dc.polygon(jaw, fill=bone)
    dh.polygon(jaw, fill=198)
    # brow ridges standing proud of the sockets
    for sx in (-1, 1):
        pts = [(ws * (0.5 + sx * 0.43), hs * 0.31), (ws * (0.5 + sx * 0.11), hs * 0.20),
               (ws * (0.5 + sx * 0.02), hs * 0.27), (ws * (0.5 + sx * 0.07), hs * 0.38),
               (ws * (0.5 + sx * 0.41), hs * 0.39)]
        dc.polygon(pts, fill=(220, 214, 196))
        dh.polygon(pts, fill=244)
    # eye sockets, sunk deep, with a cold glow low inside
    for sx in (-1, 1):
        ex = ws * (0.5 + sx * 0.205)
        for lo, hi, shade in ((0.150, 0.60, (12, 10, 11)), (0.112, 0.575, (5, 5, 6))):
            box = [ex - ws * lo, hs * 0.40, ex + ws * lo, hs * hi]
            dc.ellipse(box, fill=shade)
            dh.ellipse(box, fill=64)
        dc.ellipse([ex - ws * 0.038, hs * 0.525, ex + ws * 0.038, hs * 0.585],
                   fill=(38, 128, 82))
        dc.ellipse([ex - ws * 0.018, hs * 0.545, ex + ws * 0.018, hs * 0.575],
                   fill=(118, 212, 150))
    # nasal aperture
    nose = [(ws * 0.50, hs * 0.49), (ws * 0.435, hs * 0.665), (ws * 0.474, hs * 0.695),
            (ws * 0.50, hs * 0.66), (ws * 0.526, hs * 0.695), (ws * 0.565, hs * 0.665)]
    dc.polygon(nose, fill=(9, 8, 9))
    dh.polygon(nose, fill=58)
    # open mouth: recessed void, tooth row, then four fangs over the gate
    mouth = [(ws * 0.285, hs * 0.745), (ws * 0.715, hs * 0.745),
             (ws * 0.635, hs * 0.985), (ws * 0.365, hs * 0.985)]
    dc.polygon(mouth, fill=(10, 8, 9))
    dh.polygon(mouth, fill=52)
    dc.rectangle([ws * 0.30, hs * 0.708, ws * 0.70, hs * 0.772], fill=(214, 208, 190))
    dh.rectangle([ws * 0.30, hs * 0.708, ws * 0.70, hs * 0.772], fill=250)
    for i in range(1, 7):
        tx = ws * (0.30 + 0.40 * i / 7)
        dc.line([(tx, hs * 0.708), (tx, hs * 0.772)], fill=(138, 131, 116),
                width=max(1, int(ws * 0.011)))
        dh.line([(tx, hs * 0.708), (tx, hs * 0.772)], fill=228,
                width=max(1, int(ws * 0.011)))
    for off, fw, ft in ((-0.132, 0.030, 0.950), (-0.046, 0.024, 0.890),
                        (0.046, 0.024, 0.890), (0.132, 0.030, 0.950)):
        bx = ws * (0.5 + off)
        fang = [(bx - ws * fw, hs * 0.760), (bx + ws * fw, hs * 0.760),
                (bx + ws * fw * 0.30, hs * ft), (bx - ws * fw * 0.30, hs * ft)]
        dc.polygon(fang, fill=(226, 220, 202))
        dh.polygon(fang, fill=252)
    # carved cracks across the dome
    for x0, y0, x1, y1 in ((0.30, 0.12, 0.35, 0.24), (0.68, 0.16, 0.63, 0.28),
                           (0.47, 0.06, 0.44, 0.16)):
        dc.line([(ws * x0, hs * y0), (ws * x1, hs * y1)], fill=(126, 120, 108),
                width=max(1, int(ws * 0.012)))
        dh.line([(ws * x0, hs * y0), (ws * x1, hs * y1)], fill=210,
                width=max(1, int(ws * 0.012)))

    layer = sculpted(color, height, cx, top + hs)
    alpha = height.point(lambda v: 255 if v > 28 else 0).filter(ImageFilter.GaussianBlur(1))
    rim = art.outline(alpha, (54, 202, 128),
                      thickness=max(2, int(ws * 0.020)), expand=1)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow.alpha_composite(rim, (int(cx - ws / 2), int(top)))
    return layer, glow


def plaza(d, y_top):
    """Tiled floor in one-point perspective with an engraved inlay ring."""
    d.rectangle([0, y_top, W, H], fill=(58, 45, 43))
    y, gap = y_top, px(3)
    while y < H:
        y2 = min(H, y + gap)
        lift = int(14 * (y - y_top) / max(1, H - y_top))
        d.rectangle([0, y, W, y2], fill=(66 + lift, 52 + lift, 48 + lift))
        d.line([(0, y), (W, y)], fill=(34, 26, 26), width=max(1, int(px(0.7))))
        y = y2
        gap *= 1.30
    for k in range(-30, 31):
        x_top = CX + k * px(22)
        d.line([(x_top, y_top), (CX + (x_top - CX) * 3.4, H)],
               fill=(36, 28, 28), width=max(1, int(px(0.7))))
    for rx, ry, col, wdt in ((px(320), px(134), (112, 94, 78), px(1.8)),
                             (px(308), px(128), (40, 32, 31), px(1.4)),
                             (px(148), px(72), (106, 88, 72), px(1.4))):
        d.arc([CX - rx, y_top - ry + px(10), CX + rx, y_top + ry + px(10)],
              16, 164, fill=col, width=max(1, int(wdt)))


# ------------------------------------------------------------------ the arena
def paint():
    base = hd.blank([
        (0, (16, 9, 10)), (40, (58, 26, 22)), (78, (74, 35, 26)),
        (130, (46, 25, 20)), (170, (34, 21, 20)), (200, (20, 13, 14)),
        (240, (8, 7, 9)),
    ])
    d = ImageDraw.Draw(base)

    # hall masonry, then the upper wall above the ring, kept in shadow
    hd.stone(d, 0, 0, W, FLOOR_Y, (54, 39, 35), (31, 22, 21), rows=58, seed=12,
             jitter=0.5)
    upper = [(W, 0)] + [(x, ring_y(x)) for x in range(W, -1, -px(8))] + [(0, 0)]
    d.polygon(upper, fill=(26, 15, 15))
    for x in range(0, W, px(46)):
        d.rectangle([x + px(3), px(1), x + px(40), px(11)], fill=(21, 12, 12))

    # mezzanine: neon niches, balustrade, then the neon strips along the curve
    for i in range(-8, 9):
        if i == 0:
            continue
        x = CX + i * BAY
        if not (-BAY < x < W + BAY):
            continue
        y0 = ring_y(x)
        hd.arch(d, x, y0 + px(37), BAY * 0.66, px(37), (98, 82, 68))
        hd.arch(d, x, y0 + px(33), BAY * 0.52, px(33), (17, 11, 12))
        hd.glyph(d, x - BAY * 0.12, y0 + px(7), BAY * 0.24, (255, 56, 40),
                 seed=i + 4, width=px(1.6))
        # parapet: dark rail, lit coping, slim balusters
        d.rectangle([x - BAY / 2, y0 + px(37), x + BAY / 2, y0 + px(45)],
                    fill=(48, 36, 31))
        for k in range(-4, 5):
            pxx = x + k * BAY * 0.105
            d.rectangle([pxx - px(1.3), y0 + px(38), pxx + px(1.3), y0 + px(45)],
                        fill=(98, 85, 70))
        d.line([(x - BAY / 2, y0 + px(37)), (x + BAY / 2, y0 + px(37))],
               fill=(152, 134, 112), width=px(1.6))
    ring_line(d, px(33), (52, 212, 240), px(2))
    ring_line(d, px(35.5), (240, 54, 44), px(1.5))

    # lower arcade: tall arches into lit corridors, a sconce in every third bay
    for i in range(-8, 9):
        if i == 0:
            continue
        x = CX + i * BAY
        if not (-BAY < x < W + BAY):
            continue
        y0 = ring_y(x)
        top, bottom = y0 + px(58), FLOOR_Y - px(10)
        if bottom - top < px(30):
            continue
        hd.arch(d, x, bottom, BAY * 0.86, bottom - top, (78, 64, 52))
        hd.arch(d, x, bottom - px(7), BAY * 0.70, bottom - top - px(11), (30, 17, 16))
        iw = BAY * 0.30
        d.rectangle([x - iw, top + px(8), x + iw, bottom - px(8)], fill=(40, 20, 17))
        d.rectangle([x - iw, bottom - px(15), x + iw, bottom - px(8)], fill=(74, 46, 31))
        d.line([(x - iw, bottom - px(15)), (x + iw, bottom - px(15))],
               fill=(104, 68, 44), width=px(1))
        if i % 3 == 0:
            torch(d, x + (iw * 0.74 if i % 2 else -iw * 0.74), bottom - px(18))

    # gate tower, its stepped shoulders, then the staircase onto the plaza
    gw = px(44)
    d.rectangle([CX - gw, px(56), CX + gw, px(134)], fill=(106, 92, 78))
    d.rectangle([CX - gw, px(56), CX + gw, px(67)], fill=(126, 110, 92))
    for yy in range(px(74), px(130), px(18)):
        d.rectangle([CX - gw + px(7), yy, CX + gw - px(7), yy + px(13)],
                    fill=(64, 54, 45))
        d.line([(CX - gw + px(7), yy), (CX + gw - px(7), yy)],
               fill=(146, 128, 106), width=px(1.4))
        d.line([(CX - gw + px(7), yy + px(13)), (CX + gw - px(7), yy + px(13))],
               fill=(44, 37, 31), width=px(1.4))
    for sx in (-1, 1):
        x0, x1 = sorted((CX + sx * gw, CX + sx * (gw + px(9))))
        d.rectangle([x0, px(64), x1, px(134)], fill=(88, 76, 64))
    stair(d, CX, px(134), FLOOR_Y, px(30), px(64))
    for sx in (-1, 1):
        d.polygon([(CX + sx * px(30), px(134)), (CX + sx * px(38), px(134)),
                   (CX + sx * px(74), FLOOR_Y), (CX + sx * px(64), FLOOR_Y)],
                  fill=(114, 100, 84))
        d.line([(CX + sx * px(38), px(134)), (CX + sx * px(74), FLOOR_Y)],
               fill=(140, 124, 104), width=px(2))

    # guardians and fire bowls at the foot of the stairs, then the plaza
    for sx in (-1, 1):
        base = guardian(base, CX + sx * px(94), FLOOR_Y, px(40))
    d = ImageDraw.Draw(base)
    for sx in (-1, 1):
        brazier(d, CX + sx * px(150), FLOOR_Y, px(34))
    plaza(d, FLOOR_Y)

    base = hd.shade(base, [
        (hd.light(CX, px(150), px(300), (86, 46, 32), 52), px(14), 1.0),      # haze
        (hd.light(CX, px(26), px(76), (38, 190, 112), 46), px(6), 1.0),       # skull
        (hd.light(CX, FLOOR_Y + px(6), px(120), (40, 190, 114), 78), px(9), 1.2),
        (hd.light(CX - px(150), FLOOR_Y - px(36), px(78), (246, 162, 86), 150), px(8), 1.3),
        (hd.light(CX + px(150), FLOOR_Y - px(36), px(78), (246, 162, 86), 150), px(8), 1.3),
        (hd.light(CX - px(66), px(150), px(84), (236, 58, 44), 54), px(9), 1.1),
        (hd.light(CX + px(66), px(150), px(84), (236, 58, 44), 54), px(9), 1.1),
    ])

    # foreground: dark lip of the plaza across the bottom edge
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    fd.rectangle([0, H - px(10), W, H], fill=(7, 6, 9))
    for x in range(px(8), W, px(60)):
        fd.rectangle([x, H - px(26), x + px(3), H - px(4)], fill=(10, 9, 12))

    painted = hd.finish(base, 5, 3, 0.34, FLOOR_Y)
    skull, rim = skull_layer(CX, -px(3), px(78), px(92))
    painted = art.screen(Image.alpha_composite(painted, skull), rim,
                         glow_radius=px(2), gain=0.55, passes=2)
    return [("bg", 0, 0, painted, 0),
            ("fg", 3, 0, fg, 1)]


def main():
    hd.STAGES["lopans_throne"] = ("Lo Pan's Throne", paint)
    hd.build("lopans_throne")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
