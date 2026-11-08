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

# The aperture, in skull-layer coordinates: wide under the brow, waisted at the
# cheeks, and open at the bottom so the fog has somewhere to come from.
# The aperture runs off the bottom of the layer on purpose: the staircase comes
# up through the floor of the mouth and the fog plays in the gap, so there is
# bone only on the sides of it, never across it.
MOUTH_PTS = [(0.176, 0.606), (0.500, 0.580), (0.824, 0.606), (0.800, 0.780),
             (0.706, 1.005), (0.294, 1.005), (0.200, 0.780)]

# The jaw, as the gate is built in the reference: two curved tusks either side
# of the doorway. Each one is thick at the angle of the jaw below the cheek,
# sweeps up along the edge of the mouth and hooks inward to a point level with
# the fangs - which is why a pair of straight struts never looked right. They
# stand in the opening; nothing crosses its floor.
JAW_SPINE = [(0.238, 1.060), (0.186, 0.960), (0.206, 0.866), (0.330, 0.784)]


def _bezier(p0, p1, p2, p3, t):
    """A point on a cubic, for the spine the tusk is swept along."""
    mt = 1.0 - t
    a, b, c, d = mt ** 3, 3 * mt * mt * t, 3 * mt * t * t, t ** 3
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
            a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


def jaw_side_pts(mirror=False, n=24):
    """One jaw tusk: a blade swept along the spine, tapering into the hook."""
    p0, p1, p2, p3 = JAW_SPINE
    spine = [_bezier(p0, p1, p2, p3, i / float(n - 1)) for i in range(n)]
    edge_a, edge_b = [], []
    for i, (x, y) in enumerate(spine):
        xa, ya = spine[max(0, i - 1)]
        xb, yb = spine[min(n - 1, i + 1)]
        dx, dy = xb - xa, yb - ya
        ln = max(1e-6, (dx * dx + dy * dy) ** 0.5)
        nx, ny = -dy / ln, dx / ln
        t = i / float(n - 1)
        # thick at the angle of the jaw, thinning into the point
        w = 0.074 * (1.0 - t) ** 0.85 + 0.002
        edge_a.append((x + nx * w, y + ny * w))
        edge_b.append((x - nx * w, y - ny * w))
    pts = edge_a + edge_b[::-1]
    return [((1.0 - u) if mirror else u, v) for u, v in pts]


def jaw_mask(blur=None):
    """Silhouette of both jaw bones, for passes that must not tint them."""
    m = Image.new("L", (SKULL_W, SKULL_H), 0)
    d = ImageDraw.Draw(m)
    for mirror in (False, True):
        d.polygon([(u * SKULL_W, v * SKULL_H) for u, v in jaw_side_pts(mirror)],
                  fill=255)
    return m.filter(ImageFilter.GaussianBlur(SKULL_W * 0.008 if blur is None else blur))


def mouth_canvas():
    """The aperture mapped onto the stage canvas, where the skull is pasted."""
    ox, oy = CX - int(SKULL_W / 2), int(SKULL_TOP)
    return [(ox + u * SKULL_W, oy + v * SKULL_H) for u, v in MOUTH_PTS]

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


# ------------------------------------------------------------------ props
# Local copies: tools/stages_hd.py upstream does not carry these, and
# this module must rebuild from a plain checkout.
def hillshade(height, strength=5.0):
    """Emboss a height map into a shade multiplier, lit from the upper left.

    ImageChops.subtract clamps at zero, so each direction needs both a
    'falling towards the light' and a 'falling away' term to stay signed.
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
    """Composite a colour + height pair onto the full canvas at (cx, y_base)."""
    shade = hillshade(height)
    rgb = ImageChops.multiply(color, Image.merge("RGB", (shade, shade, shade)))
    rgba = rgb.convert("RGBA")
    alpha = height.point(lambda v: 255 if v > 28 else 0).filter(ImageFilter.GaussianBlur(1))
    rgba.putalpha(alpha)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.alpha_composite(rgba, (int(cx - color.size[0] / 2), int(y_base - color.size[1])))
    return layer


def torch(d, cx, cy, h=None):
    """Wall sconce: bracket, cup, and three flame tongues. cy is the bracket foot."""
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

    # plinth
    both(lambda d, f: d.rectangle([ws * 0.04, hs * 0.90, ws * 0.96, hs], fill=f),
         (146, 137, 120), 152)
    # haunches, then the chest slab
    both(lambda d, f: d.ellipse([ws * 0.08, hs * 0.56, ws * 0.92, hs * 0.94], fill=f),
         body, 208)
    both(lambda d, f: d.polygon([(ws * 0.26, hs * 0.42), (ws * 0.74, hs * 0.42),
                                 (ws * 0.86, hs * 0.90), (ws * 0.14, hs * 0.90)], fill=f),
         body, 226)
    # forelegs with paws
    for lx in (0.27, 0.63):
        both(lambda d, f: d.rectangle([ws * lx, hs * 0.60, ws * (lx + 0.10), hs * 0.92],
                                      fill=f), body, 238)
        both(lambda d, f: d.ellipse([ws * lx - ws * 0.02, hs * 0.86,
                                     ws * (lx + 0.12), hs * 0.96], fill=f),
             (156, 147, 130), 244)
    # mane disc behind the head
    both(lambda d, f: d.ellipse([ws * 0.16, hs * 0.02, ws * 0.84, hs * 0.60], fill=f),
         dark, 204)
    for k in range(12):
        a = 2 * math.pi * k / 12
        mx, my = ws * 0.5 + math.cos(a) * ws * 0.32, hs * 0.30 + math.sin(a) * ws * 0.28
        both(lambda d, f, mx=mx, my=my: d.ellipse(
            [mx - ws * 0.055, my - ws * 0.055, mx + ws * 0.055, my + ws * 0.055],
            fill=f), (158, 149, 132), 216)
    # head, muzzle, open jaw
    both(lambda d, f: d.ellipse([ws * 0.33, hs * 0.16, ws * 0.67, hs * 0.50], fill=f),
         body, 252)
    both(lambda d, f: d.rounded_rectangle([ws * 0.40, hs * 0.28, ws * 0.60, hs * 0.42],
                                          radius=hs * 0.05, fill=f),
         (182, 172, 154), 255)
    both(lambda d, f: d.ellipse([ws * 0.40, hs * 0.38, ws * 0.60, hs * 0.50], fill=f),
         (104, 96, 84), 206)
    # ears
    for ex, sgn in ((0.35, -1), (0.65, 1)):
        both(lambda d, f, ex=ex, sgn=sgn: d.polygon(
            [(ws * ex, hs * 0.18), (ws * (ex + sgn * 0.09), hs * 0.16),
             (ws * (ex + sgn * 0.03), hs * 0.05)], fill=f), (156, 147, 130), 240)
    # brows and sunken eyes
    for ex in (0.42, 0.58):
        both(lambda d, f, ex=ex: d.ellipse([ws * ex - ws * 0.045, hs * 0.24,
                                            ws * ex + ws * 0.045, hs * 0.31], fill=f),
             (34, 28, 25), 104)
        both(lambda d, f, ex=ex: d.rectangle([ws * ex - ws * 0.06, hs * 0.205,
                                              ws * ex + ws * 0.06, hs * 0.235], fill=f),
             (196, 186, 166), 250)
    return Image.alpha_composite(base, sculpted(color, height, cx, y_base))


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
        # cheek: the zygomatic mass is the widest part of the face below the
        # dome, so it has to flare past the muzzle rather than sit flush
        ell(rbox(ws * 0.5 + sx * ws * 0.104, hs * 0.488,
                 ws * 0.5 + sx * ws * 0.322, hs * 0.600), bone, 196)
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

    # --- mouth: an open aperture, cleared out of the layer ------------------
    poly([(u * ws, v * hs) for u, v in MOUTH_PTS], (0, 0, 0), 0)

    # --- jaw tusks, standing in the opening ---------------------------------
    # Painted after the aperture is cut. Drawn before it, the cut ate the hook
    # and left a stub standing at the edge, which is why it never matched.
    for mirror in (False, True):
        poly([(u * ws, v * hs) for u, v in jaw_side_pts(mirror)], (198, 190, 170), 208)

    # --- teeth --------------------------------------------------------------
    teeth_all = []
    def tooth(bx, y0, half, tip, lean=0.0):
        # The base is a shallow cup rather than a flat slab: the corners tuck
        # up under the gum, so a tooth that is painted brighter than the jaw
        # does not sit on it like a paper tab.
        pts = [(bx - half, y0 - half * 0.30),
               (bx - half * 0.55, y0),
               (bx + half * 0.58, y0),
               (bx + half, y0 - half * 0.30),
               (bx + half * 0.70 + lean * 0.55, y0 + (tip - y0) * 0.46),
               (bx + lean, tip),
               (bx - half * 0.62 + lean * 0.72, y0 + (tip - y0) * 0.52)]
        poly(pts, (232, 226, 206), 250)
        teeth_all.append(pts)
        dc.line([(bx - half * 0.30, y0 + px(1)), (bx + lean * 0.7, tip - px(2))],
                fill=(196, 188, 166), width=max(1, int(ws * 0.005)))

    # Upper jaw: the row across the lip, then the two corner fangs a side.
    # This is the layout the gate has always had; the bottom of the mouth is
    # where the extra teeth belong, not here.
    row_y = hs * 0.586
    for k in range(-2, 3):
        bx = ws * 0.5 + k * ws * 0.066
        tooth(bx, row_y, ws * 0.025, row_y + hs * (0.070 if abs(k) < 2 else 0.080))
    for sx in (-1, 1):
        tooth(ws * 0.5 + sx * ws * 0.232, hs * 0.592, ws * 0.037,
              hs * 0.790, lean=sx * ws * 0.012)
        tooth(ws * 0.5 + sx * ws * 0.322, hs * 0.588, ws * 0.030,
              hs * 0.706, lean=sx * ws * 0.007)
    # Lower jaw: three teeth a side standing up out of the floor of the mouth,
    # one behind the other - the corner tooth the gate always had, plus two
    # more stepped back into the throat. Each one behind is shorter, narrower
    # and set higher, because the floor of the mouth recedes upward.
    lower = [(0.163, 0.952, 0.029, 0.874),     # deepest in the throat
             (0.207, 0.956, 0.042, 0.858),     # middle
             (0.250, 0.964, 0.056, 0.840)]     # nearest, out at the corner
    for sx in (-1, 1):
        for u, y0, half, tip in lower:
            tooth(ws * 0.5 + sx * ws * u, hs * y0, ws * half, hs * tip,
                  lean=sx * ws * 0.010)

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
    shade = hillshade(height, 4.6)
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

    # --- teeth are bone, not shadowed stone --------------------------------
    # The vertical falloff that darkens the jaw toward the floor of the mouth
    # darkened the teeth with it: measured on the layer they came out around
    # (120, 112, 92), which reads as a void against the black of the open
    # mouth. The reference has them bright white, so each tooth is repainted
    # here, after the shading, as its own little vertical gradient - a shadow
    # under the gum, bone through the body, brightest at the tip.
    kt = SKULL_W / float(ws)
    for pts in teeth_all:
        sp = [(x * kt, y * kt) for x, y in pts]
        x0, x1 = min(p[0] for p in sp), max(p[0] for p in sp)
        y0, y1 = min(p[1] for p in sp), max(p[1] for p in sp)
        tw, th = max(1, int(x1 - x0) + 2), max(1, int(y1 - y0) + 2)
        tile = art.vgrad((tw, th), [(0, (148, 140, 122)),
                                    (int(th * 0.22), (226, 220, 202)),
                                    (int(th * 0.70), (246, 242, 228)),
                                    (th, (255, 254, 246))]).convert("RGBA")
        cut = Image.new("L", (tw, th), 0)
        ImageDraw.Draw(cut).polygon([(px - x0 + 1, py - y0 + 1) for px, py in sp],
                                    fill=255)
        cut = cut.filter(ImageFilter.GaussianBlur(0.5))
        sheet = Image.new("RGBA", (SKULL_W, SKULL_H), (0, 0, 0, 0))
        sheet.paste(tile, (int(x0) - 1, int(y0) - 1), cut)
        # A soft dark rim, so two fangs that overlap still read as two: without
        # it the nearer blade and the one behind it merge into one bright slab,
        # because they are painted the same bone.
        edge = Image.new("RGBA", (SKULL_W, SKULL_H), (0, 0, 0, 0))
        ImageDraw.Draw(edge).line(sp + [sp[0]], fill=(112, 100, 82, 200),
                                  width=max(1, int(SKULL_W * 0.005)),
                                  joint="curve")
        edge = edge.filter(ImageFilter.GaussianBlur(0.6))
        sheet = Image.alpha_composite(sheet, edge)
        layer = Image.alpha_composite(layer, sheet)

    # Gum: a soft maroon band over the roots. The teeth are brighter than the
    # jaw, so without it every one of them ends on a visible cut edge and the
    # fangs sit proud of the bone like tabs.
    # It stops at the ridge line: carried any lower it covered the shadowed
    # roots of the top row and flattened every one of those teeth into a tab,
    # which is the layer effect the bottom row kept and the top row lost.
    gum = Image.new("RGBA", (SKULL_W, SKULL_H), (0, 0, 0, 0))
    ImageDraw.Draw(gum).polygon([(SKULL_W * 0.150, SKULL_H * 0.546),
                                 (SKULL_W * 0.850, SKULL_H * 0.546),
                                 (SKULL_W * 0.836, SKULL_H * 0.600),
                                 (SKULL_W * 0.164, SKULL_H * 0.600)],
                                fill=(70, 40, 34, 186))
    gum = gum.filter(ImageFilter.GaussianBlur(SKULL_W * 0.012))
    gum.putalpha(ImageChops.multiply(gum.split()[3], alpha))
    layer = Image.alpha_composite(layer, gum)

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
    # Bone in front of the light stays bone. The underlight was tinting the
    # lower teeth mint, because they stand in the brightest part of it.
    k = SKULL_W / float(ws)
    tb = Image.new("L", (SKULL_W, SKULL_H), 0)
    td = ImageDraw.Draw(tb)
    for pts in teeth_all:
        td.polygon([(x * k, y * k) for x, y in pts], fill=255)
    under.putalpha(ImageChops.multiply(under.split()[3],
                                       ImageChops.invert(tb)))
    # The jaw is bone, not mouth: without this the green spill that lights the
    # inside of the mouth screened the whole mandible sage green.
    jaw = jaw_mask()
    under.putalpha(ImageChops.multiply(under.split()[3], ImageChops.invert(jaw)))
    layer = art.screen(layer, under, glow_radius=SKULL_W * 0.02, gain=1.0)
    layer.putalpha(alpha)          # screen() returns an opaque alpha channel

    # --- the jaw is bone, and it goes on last -------------------------------
    # The mouthlight kept screening the mandible sage through its mask, so the
    # bone is laid back over the top the way the teeth are, keeping most of the
    # modelling underneath it.
    jmask = jaw_mask(0.9)
    jbone = art.vgrad((SKULL_W, SKULL_H), [(int(SKULL_H * 0.90), (228, 220, 200)),
                                           (int(SKULL_H * 0.96), (200, 192, 172)),
                                           (SKULL_H, (154, 146, 130))]).convert("RGBA")
    jlit = Image.blend(layer.convert("RGB"), jbone.convert("RGB"), 0.62).convert("RGBA")
    jlit.putalpha(layer.getchannel("A"))
    layer = Image.composite(jlit, layer, jmask)

    # --- the tusks are the brightest bone on the gate ----------------------
    # The mouthlight throws up onto them, so they stay pale while the rest of
    # the jaw falls away. Left to the shading above they came out dark and the
    # pair read as two thin shadows of a jaw rather than bone standing in the
    # opening.
    tusk = Image.new("L", (SKULL_W, SKULL_H), 0)
    tdraw = ImageDraw.Draw(tusk)
    for mirror in (False, True):
        tdraw.polygon([(u * SKULL_W, v * SKULL_H) for u, v in jaw_side_pts(mirror)],
                      fill=255)
    tgrad = art.vgrad((SKULL_W, SKULL_H), [(int(SKULL_H * 0.68), (252, 248, 236)),
                                           (int(SKULL_H * 0.84), (236, 230, 212)),
                                           (SKULL_H, (198, 190, 170))]).convert("RGBA")
    tbright = Image.blend(layer.convert("RGB"), tgrad.convert("RGB"), 0.86).convert("RGBA")
    tbright.putalpha(layer.getchannel("A"))
    layer = Image.composite(tbright, layer, tusk.filter(ImageFilter.GaussianBlur(0.9)))

    # a crease down each blade, so the tusk has a grain instead of a flat fill
    crease = Image.new("RGBA", (SKULL_W, SKULL_H), (0, 0, 0, 0))
    cdw = ImageDraw.Draw(crease)
    jp0, jp1, jp2, jp3 = JAW_SPINE
    for mirror in (False, True):
        pts = []
        for i in range(10):
            t = 0.18 + 0.66 * i / 9.0
            u, v = _bezier(jp0, jp1, jp2, jp3, t)
            u = u + (0.074 * (1.0 - t) ** 0.85 + 0.002) * 0.34
            pts.append(((1.0 - u) if mirror else u, v))
        cdw.line([(u * SKULL_W, v * SKULL_H) for u, v in pts],
                 fill=(160, 152, 132, 130), width=max(1, int(SKULL_W * 0.006)),
                 joint="curve")
    crease = crease.filter(ImageFilter.GaussianBlur(0.7))
    crease.putalpha(ImageChops.multiply(crease.split()[3], tusk))
    layer = Image.alpha_composite(layer, crease)

    # --- neon rim -----------------------------------------------------------
    # The silhouette is the alpha on its own. It used to need a filled block
    # over the jaw, because the mouth ran off the bottom of the layer and there
    # was no jaw there to trace - and that block is what drew the straight green
    # lines down either side of the mouth, through open air.
    sil = alpha.copy()
    rim = art.outline(sil, (46, 208, 128), thickness=max(2, int(SKULL_W * 0.009)),
                      expand=1)
    hot = art.outline(sil, (150, 246, 196), thickness=max(1, int(SKULL_W * 0.003)),
                      expand=2)
    neon = Image.alpha_composite(rim, hot)

    # The bottom row gets no pass of its own. It used to have one - a green
    # ring drawn round every lower tooth - and that is what tinted the row mint
    # and what bled its lines across the teeth standing in front: the rings
    # were painted per tooth, in the same order the teeth were drawn, so a
    # nearer tooth never covered the edge of the one behind it. The rim above is
    # traced once, round the finished aperture, so every tooth - top row and
    # bottom row alike - gets the same neon edge, and overlapping bone simply
    # covers the edge underneath it.

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
            torch(d, x + BAY * 0.33, base_y - px(52))

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
        base = guardian(base, CX + sx * px(126), FLOOR_Y, px(30))
    d = ImageDraw.Draw(base)
    for sx in (-1, 1):
        brazier(d, CX + sx * px(88), FLOOR_Y, px(26))
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
    # The mouth is a real hole in the hall. The fog video is the last background
    # in the stack, so the only way it can be seen is if the backdrop is open
    # where the mouth is. The teeth belong to the skull layer and stay opaque,
    # so they are subtracted back out of the hole: they read as hanging in
    # front of the fog, not painted on the wall.
    mouth = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mouth).polygon(mouth_canvas(), fill=255)
    teeth = skull.getchannel("A").point(lambda v: 255 if v > 110 else 0)
    aperture = ImageChops.subtract(mouth, teeth)
    # Feathered, so the fog fades out into the stair throat at the bottom
    # of the jaw instead of stopping on a cut line.
    aperture = aperture.filter(ImageFilter.GaussianBlur(px(2.2)))
    painted = Image.alpha_composite(painted, skull)
    painted = art.screen(painted, rim, glow_radius=px(1.5), gain=0.26, passes=2)
    # art.screen() comes back with an opaque alpha channel, so the aperture is
    # punched last: it has to survive every layer drawn after it.
    painted.putalpha(ImageChops.subtract(painted.split()[3], aperture))
    # The fog is the fog.webm clip itself, drawn behind the hall, so the
    # aperture is the only place it can be seen. Its layer is FOG_BG below, and
    # that is empty unless video/fog.webm is really there: the clip is not part
    # of the game, and a layer pointing at a missing file does not leave the
    # mouth clear, it leaves it black.
    if FOG_BG:
        hd.EXTRA_BG["lopans_throne"] = FOG_BG
    return [("bg", 0, 0, painted, 0),
            ("fg", 3, 0, fg, 1)]


# ------------------------------------------------------------------ fog
# The mouth is a hole into the throat, and the fog in it is the fog.webm film,
# drawn as a video background. Two things about that layer are not obvious, and
# both were wrong in the first version:
#
#   * start = 0,0 puts the clip's left edge in the MIDDLE of the screen. Ikemen
#     draws a stage video with a render origin of gameWidth/2 to the right of
#     start (src/stage.go: "Choose render origin: top-left for motif/storyboard
#     videos, center for everything else"), which is why only the right half of
#     the mouth ever had fog in it. The clip is 3840x2160 for a 1920x1080 stage,
#     so start = -1920,0 centres it and covers the view twice over.
#   * video does not repeat unless `loop = 1` is set (is.ReadBool("loop", ...)
#     in the video branch of BG parsing). Without it the clip ran its fifteen
#     seconds and the mouth went dark for good.
_FOG_CLIP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "video", "fog.webm")

FOG_BG = ("""
; the mouth is a hole into the throat: the fog film sits at the bottom of the
; stack, so the aperture is the only place it can be seen. It covers the whole
; view, so the fog keeps running in the mouth as the camera pans.
[BG fog]
type = video
path = video/fog.webm
loop = 1
layerno = 0
start = -%d,0
delta = 0,0
""" % (hd.LOCAL_W,)) if os.path.exists(_FOG_CLIP) else ""


def main():
    hd.STAGES["lopans_throne"] = ("Lo Pan's Throne", paint)
    hd.build("lopans_throne")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
