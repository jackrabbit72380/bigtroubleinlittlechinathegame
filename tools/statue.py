"""The six-armed guardian of Lo Pan's ceremony hall, painted from the still.

The statue in the film is one heavy seated figure, not a pile of parts: a small
snarling head under a tiara of skulls, a chest and belly carrying almost all the
mass, six arms as thick as the head ending in huge fists, a necklace of skulls,
gold bangles, a sash slung across the lap - and over all of it a green neon tube
that follows every contour, the inner ones as much as the outer.

So the figure is built the way a figure is drawn: smooth outlines (Catmull-Rom
blobs, quadratic tapered limbs) on a 3x supersampled canvas, lit once as a whole
so the arms, belly and lap belong to one body, and then traced twice - once
around the finished silhouette, and once around each part, because the tube in
the film separates the arms from the torso instead of ringing the whole statue.
That second pass is what makes six arms read as six arms.

Coordinates are in units of the shared 4.5 canvas px: u is horizontal from the
stage centre, v is vertical from the top of the crown, and v = 96 is the top of
the plinth the figure sits on.

Used by tools/stage_ceremony.py.  Run: python3 tools/stage_ceremony.py
"""

from __future__ import annotations

import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter

SS = 3                                  # supersample: 3x, then LANCZOS down
BOX = (-80.0, -14.0, 80.0, 96.5)        # unit-space box the figure is drawn in

STONE = (126, 140, 122)                 # weathered stone, gone green with damp
STONE_DK = (58, 68, 58)
FACE = (164, 174, 150)
GOLD = (206, 166, 86)
GOLD_DK = (92, 62, 26)
NEON = (78, 252, 166)
EYE = (255, 78, 34)

HEAD = (0.0, 27.0)
HEAD_RX, HEAD_RY = 12.8, 13.6


# ------------------------------------------------------------------ outlines
def _catmull(pts, closed=True, n=14):
    """Catmull-Rom through the points: a drawn curve, not a faceted polygon."""
    p = list(pts)
    if closed:
        p = [p[-1]] + p + [p[0], p[1]]
    else:
        p = [p[0]] + p + [p[-1], p[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append((
                0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)))
    return out


def _spine(a, ctrl, b, n=30):
    """Points, tangents and widths down a quadratic limb."""
    out = []
    for i in range(n + 1):
        t = i / n
        it = 1.0 - t
        x = it * it * a[0] + 2 * it * t * ctrl[0] + t * t * b[0]
        y = it * it * a[1] + 2 * it * t * ctrl[1] + t * t * b[1]
        dx = 2 * it * (ctrl[0] - a[0]) + 2 * t * (b[0] - ctrl[0])
        dy = 2 * it * (ctrl[1] - a[1]) + 2 * t * (b[1] - ctrl[1])
        ln = math.hypot(dx, dy) or 1.0
        out.append((x, y, dx / ln, dy / ln))
    return out


def _taper(a, ctrl, b, w0, w1, n=30, swell=0.14):
    """A limb: a quadratic spine with a width that swells at the bicep.

    Returns the closed outline - two offset sides plus a rounded cap at each
    end - so an arm reads as a heavy tube ending in a joint, never a stick.
    """
    left, right = [], []
    for i, (x, y, tx, ty) in enumerate(_spine(a, ctrl, b, n)):
        t = i / n
        s = t * t * (3.0 - 2.0 * t)
        w = (w0 + (w1 - w0) * s) * (1.0 + swell * math.sin(math.pi * t))
        left.append((x - ty * w, y + tx * w))
        right.append((x + ty * w, y - tx * w))
    # caps, swept around the true tangent at each end, so the outline closes
    # into one continuous loop instead of jumping across the limb
    def cap(c, t_out, nrm, wid):
        tx, ty = t_out
        nx, ny = nrm
        return [(c[0] + (math.cos(ph) * nx + math.sin(ph) * tx) * wid,
                 c[1] + (math.cos(ph) * ny + math.sin(ph) * ty) * wid)
                for ph in (math.pi * k / 10 for k in range(11))]

    sp = _spine(a, ctrl, b, n)
    t0 = (sp[0][2], sp[0][3])
    t1 = (sp[-1][2], sp[-1][3])
    cap_b = cap(b, t1, (-t1[1], t1[0]), w1)          # left end of b, round front
    cap_a = cap(a, (-t0[0], -t0[1]), (t0[1], -t0[0]), w0)   # right end of a
    return left + cap_b + right[::-1] + cap_a


def _fist(d, c, r, ang, fill, seam):
    """A clenched fist: palm mass, four knuckles over it, thumb along the side.

    The knuckles are separate bumps so the contour breaks into fingers the way
    the film's tube does, instead of ringing one smooth ball.
    """
    ax, ay = math.cos(ang), math.sin(ang)          # along the forearm
    nx, ny = -ay, ax                               # across it
    cx, cy = c[0] - ax * r * 0.10, c[1] - ay * r * 0.10
    d.ellipse([cx - r * 1.04, cy - r * 0.96, cx + r * 1.04, cy + r * 0.96], fill=fill)
    for k in (-0.72, -0.25, 0.25, 0.72):
        kx = cx + ax * r * 0.58 + nx * k * r * 0.90
        ky = cy + ay * r * 0.58 + ny * k * r * 0.90
        d.ellipse([kx - r * 0.52, ky - r * 0.52, kx + r * 0.52, ky + r * 0.52], fill=fill)
        d.line([(kx + nx * r * 0.16, ky + ny * r * 0.16),
                (cx + ax * r * 0.06, cy + ay * r * 0.06)], fill=seam,
               width=max(1, int(r * 0.13)))
    d.ellipse([cx - ax * r * 0.85 - nx * r * 0.50 - r * 0.32,
               cy - ay * r * 0.85 - ny * r * 0.50 - r * 0.32,
               cx - ax * r * 0.85 - nx * r * 0.50 + r * 0.32,
               cy - ay * r * 0.85 - ny * r * 0.50 + r * 0.32], fill=fill)


def _hand(d, c, r, ang, fill, seam):
    """An open hand, fingers curled up: the lowest pair do not clench."""
    ax, ay = math.cos(ang), math.sin(ang)
    nx, ny = -ay, ax
    d.ellipse([c[0] - r, c[1] - r * 0.86, c[0] + r, c[1] + r * 0.86], fill=fill)
    for k in (-0.62, -0.21, 0.21, 0.62):
        bx = c[0] + ax * r * 0.58 + nx * k * r * 0.80
        by = c[1] + ay * r * 0.58 + ny * k * r * 0.80
        d.ellipse([bx - r * 0.27, by - r * 0.27, bx + r * 0.27, by + r * 0.27], fill=fill)
    d.ellipse([c[0] - ax * r * 0.40 - nx * r * 0.80 - r * 0.18,
               c[1] - ay * r * 0.40 - ny * r * 0.80 - r * 0.18,
               c[0] - ax * r * 0.40 - nx * r * 0.80 + r * 0.18,
               c[1] - ay * r * 0.40 - ny * r * 0.80 + r * 0.18], fill=fill)


# ------------------------------------------------------------------ lighting
def _vgrad(w, h, stops):
    """Vertical ramp, as an L image, from (position, gain) stops.

    Gains are multipliers on the stone: 1.0 leaves it alone, 0.62 darkens it to
    under two thirds, 1.34 lifts the crown - so they are scaled by 255 here
    rather than being written as byte values.
    """
    thin = Image.new("L", (1, h))
    p = thin.load()
    stops = sorted(stops)
    for y in range(h):
        t = y / max(1, h - 1)
        val = stops[-1][1]
        for i in range(len(stops) - 1):
            p0, v0 = stops[i]
            p1, v1 = stops[i + 1]
            if p0 <= t <= p1 and p1 > p0:
                val = v0 + (v1 - v0) * (t - p0) / (p1 - p0)
                break
        p[0, y] = int(max(0, min(255, val * 255.0)))
    return thin.resize((w, h))


def _radial(w, h, fx, fy, rx, ry, power=2.0):
    """Soft elliptical falloff, 1 at (fx, fy), 0 at the rim, as an L image."""
    n = 180
    small = Image.new("L", (n, n), 0)
    q = small.load()
    for y in range(n):
        for x in range(n):
            dx = (x / n - fx) / max(1e-6, rx)
            dy = (y / n - fy) / max(1e-6, ry)
            v = max(0.0, 1.0 - math.hypot(dx, dy))
            q[x, y] = int(255 * (v ** power))
    return small.resize((w, h), Image.BICUBIC)


# ------------------------------------------------------------------ the figure
def build(S, cx, top, w_full, h_full):
    """Paint the statue; returns (layer, neon rim, eye light) at stage size."""
    u0, v0, u1, v1 = BOX
    w = int(round((u1 - u0) * S * SS))
    h = int(round((v1 - v0) * S * SS))

    def X(u):
        return (u - u0) * S * SS

    def Y(v):
        return (v - v0) * S * SS

    def P(pts):
        return [(X(x), Y(y)) for x, y in pts]

    contours = []           # unit-space polygons the neon also traces

    def blob(d, pts, fill=STONE, outline=True, smooth=14):
        sm = _catmull(pts, True, smooth)
        d.polygon(P(sm), fill=fill)
        if outline:
            contours.append(sm)

    body = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    seam_w = max(1, int(0.30 * S * SS))

    # seated: thighs and shins crushed together across the drum, a low wide
    # mass with the knees breaking the outline either side of the belly
    blob(d, [(-54, 93), (-44, 86.5), (-30, 84), (-14, 88), (0, 92.5),
             (14, 88), (30, 84), (44, 86.5), (54, 93), (50, 96.5), (-50, 96.5)])
    for sx in (-1, 1):
        blob(d, [(sx * 24, 82), (sx * 37, 83.5), (sx * 43, 90), (sx * 35, 92.5),
                 (sx * 24, 89.5)])
    blob(d, [(-9, 89.5), (0, 88), (9, 89.5), (7, 94), (-7, 94)])     # ankles

    # torso: traps into a chest that gives way to the huge belly
    torso = [(-26, 45), (-29, 53), (-33, 62), (-35, 72), (-33.5, 81),
             (-27, 88), (-16, 91), (0, 92), (16, 91), (27, 88), (33.5, 81),
             (35, 72), (33, 62), (29, 53), (26, 45), (14, 40.5), (0, 39.5),
             (-14, 40.5)]
    blob(d, torso)
    # belly, a dome that hangs over the sash
    blob(d, [(-27, 74), (-19, 66), (0, 63.5), (19, 66), (27, 74), (25, 85),
             (12, 90), (-12, 90), (-25, 85)])
    for sx in (-1, 1):                                    # pectorals
        blob(d, [(sx * 3, 45.5), (sx * 12, 44), (sx * 22, 47.5), (sx * 20, 56),
                 (sx * 10, 58), (sx * 3, 54)], outline=False)

    # sash: a heavy cloth slung across the lap, falling off the left knee
    blob(d, [(-28, 76), (-16, 79.5), (-2, 81.5), (12, 83), (27, 86.5), (29, 95),
             (10, 92), (-8, 90), (-23, 87), (-29, 81)], (132, 138, 118))
    for k in (0, 1, 2):
        d.line(P([(-27 + k * 2.5, 79 + k * 1.8), (-6, 84.5 + k * 1.8),
                  (16, 87 + k * 1.8), (27, 90 + k * 1.8)]),
               fill=(66, 72, 58), width=seam_w)
    d.line(P([(-27, 79.5), (-6, 84.8), (16, 87.4), (27, 90.2)]),
           fill=(176, 180, 156), width=max(1, int(0.26 * S * SS)))

    # six arms in three tiers: fists above the head at the corners, fists
    # thrown wide at head height, and the lowest pair open over the knees
    tiers = [
        ((23, 47), (40, 36), (34, 15), 10.4, 8.0, 10.2, "fist"),
        ((25, 55), (50, 47), (52, 31), 10.8, 8.4, 9.6, "fist"),
        ((23, 62), (46, 73), (47, 85), 9.8, 7.2, 8.2, "hand"),
    ]
    bands = []
    for sx in (-1, 1):
        for (au, av), (cu, cv), (bu, bv), w0, w1, wr, kind in tiers:
            a = (sx * au, av)
            ctrl = (sx * cu, cv)
            b = (sx * bu, bv)
            d.ellipse([X(a[0] - w0 * 1.06), Y(a[1] - w0 * 1.06),
                       X(a[0] + w0 * 1.06), Y(a[1] + w0 * 1.06)], fill=STONE)
            limb = _taper(a, ctrl, b, w0, w1)
            d.polygon(P(limb), fill=STONE)
            contours.append(limb)
            ang = math.atan2(b[1] - ctrl[1], b[0] - ctrl[0])
            # the hand sits proud of the wrist, so the bangle above it reads as
            # a cuff and the knuckles break the outline instead of the forearm
            hc = (b[0] + math.cos(ang) * wr * 0.45, b[1] + math.sin(ang) * wr * 0.45)
            if kind == "fist":
                _fist(d, hc, wr * 1.24, ang, STONE, STONE_DK)
            else:
                _hand(d, hc, wr * 1.14, ang, STONE, STONE_DK)
            for frac, half, thick in ((0.92, w1 * 1.04, 1.3), (0.26, w0 * 0.98, 1.2)):
                pts = _spine(a, ctrl, b)
                i = int(round(frac * (len(pts) - 1)))
                bx, by, tx, ty = pts[i]
                nx, ny = -ty, tx
                bands.append((bx, by, nx, ny, tx, ty, half, thick))

    for bx, by, nx, ny, tx, ty, half, thick in bands:
        quad = [(bx + nx * half - tx * thick, by + ny * half - ty * thick),
                (bx - nx * half - tx * thick, by - ny * half - ty * thick),
                (bx - nx * half + tx * thick, by - ny * half + ty * thick),
                (bx + nx * half + tx * thick, by + ny * half + ty * thick)]
        d.polygon(P(quad), fill=GOLD)
        d.line(P([(bx + nx * half - tx * thick, by + ny * half - ty * thick),
                  (bx - nx * half - tx * thick, by - ny * half - ty * thick)]),
               fill=(244, 216, 142), width=max(1, int(0.22 * S * SS)))

    # head: a short thick neck, long bodhisattva ears, and a face that is all
    # brow and jaw with a small snarling mouth between them
    hx, hy = HEAD
    blob(d, [(-9.5, 39), (-6.5, 32), (6.5, 32), (9.5, 39), (0, 42)], STONE_DK,
         outline=False)
    for sx in (-1, 1):                       # traps heaped under the jaw
        blob(d, [(sx * 10, 41), (sx * 24, 44), (sx * 26, 49), (sx * 12, 45)],
             outline=False)
    for sx in (-1, 1):
        blob(d, [(sx * (HEAD_RX - 1.0), hy - 6.5), (sx * (HEAD_RX + 2.0), hy - 5.5),
                 (sx * (HEAD_RX + 1.6), hy + 7.5), (sx * (HEAD_RX - 2.4), hy + 6.5)])
    d.ellipse([X(hx - HEAD_RX), Y(hy - HEAD_RY), X(hx + HEAD_RX), Y(hy + HEAD_RY)],
              fill=FACE)
    blob(d, [(-9.5, hy + 6), (0, hy + 9.5), (9.5, hy + 6), (0, hy + 14)], FACE,
         outline=False)

    # brows: two heavy bars angled down into the nose bridge
    for sx in (-1, 1):
        blob(d, [(sx * 1.2, hy - 5.4), (sx * 9.8, hy - 7.0), (sx * 10.2, hy - 4.4),
                 (sx * 1.5, hy - 2.4)], (44, 52, 44), outline=False)
    # eye sockets, deep and wide, with a lit lower lid
    for sx in (-1, 1):
        ex = hx + sx * 5.1
        d.ellipse([X(ex - 3.7), Y(hy - 3.4), X(ex + 3.7), Y(hy + 1.7)],
                  fill=(16, 12, 12))
        d.line(P([(ex - sx * 3.5, hy - 1.1), (ex + sx * 3.4, hy - 2.1)]),
               fill=(126, 140, 114), width=max(1, int(0.30 * S * SS)))
    # nose: a broad wedge with flared nostrils
    blob(d, [(0, hy - 3.4), (2.6, hy - 0.2), (2.5, hy + 2.6), (1.3, hy + 3.4),
             (-1.3, hy + 3.4), (-2.5, hy + 2.6), (-2.6, hy - 0.2)],
         (158, 168, 144), outline=False)
    for sx in (-1, 1):
        d.ellipse([X(sx * 2.8 - 1.0), Y(hy + 2.8), X(sx * 2.8 + 1.0), Y(hy + 4.0)],
                  fill=(40, 46, 38))
    # mouth: wide, open, the top row seen and four fangs standing up off the jaw
    my = hy + 8.2
    d.polygon(P([(-7.0, my - 1.8), (-3.6, my - 0.4), (0, my + 0.3),
                 (3.6, my - 0.4), (7.0, my - 1.8),
                 (5.8, my + 2.4), (0, my + 3.2), (-5.8, my + 2.4)]),
              fill=(12, 9, 9))
    d.line(P([(-7.0, my - 1.8), (-3.6, my - 0.4), (0, my + 0.3),
              (3.6, my - 0.4), (7.0, my - 1.8)]),
           fill=(132, 144, 118), width=max(1, int(0.36 * S * SS)))
    for k in (-0.74, -0.45, -0.15, 0.15, 0.45, 0.74):
        tx = k * 6.0
        d.polygon(P([(tx - 0.58, my - 1.2), (tx + 0.58, my - 1.2), (tx, my + 0.5)]),
                  fill=(228, 224, 202))
    for k, size in ((-0.55, 1.0), (-0.19, 0.64), (0.19, 0.64), (0.55, 1.0)):
        tx = k * 8.8
        wdt, hgt = 0.80 * size, 2.7 * size
        d.polygon(P([(tx - wdt, my + 2.3), (tx + wdt, my + 2.3), (tx, my + 2.3 - hgt)]),
                  fill=(240, 236, 214))
    d.line(P([(-5.8, my + 2.4), (0, my + 3.3), (5.8, my + 2.4)]),
           fill=(60, 68, 58), width=max(1, int(0.42 * S * SS)))
    d.arc([X(-5.6), Y(my + 2.6), X(5.6), Y(hy + 13.6)], 15, 165,
          fill=(120, 132, 106), width=max(1, int(0.34 * S * SS)))   # chin

    # crown: a band of skulls with horns, not gold spikes
    d.polygon(P([(-HEAD_RX, hy - 12.6), (HEAD_RX, hy - 12.6),
                 (HEAD_RX, hy - 8.8), (-HEAD_RX, hy - 8.8)]), fill=GOLD)
    contours.append([(-HEAD_RX, hy - 12.6), (HEAD_RX, hy - 12.6),
                     (HEAD_RX, hy - 8.8), (-HEAD_RX, hy - 8.8)])
    for k in range(-2, 3):
        skx = k * 5.0
        sky = hy - 11.2
        d.ellipse([X(skx - 2.9), Y(sky - 3.0), X(skx + 2.9), Y(sky + 1.9)],
                  fill=(236, 232, 210))
        d.polygon(P([(skx - 2.2, sky + 1.2), (skx + 2.2, sky + 1.2),
                     (skx + 1.7, sky + 3.4), (skx - 1.7, sky + 3.4)]),
                  fill=(236, 232, 210))
        for sx in (-1, 1):
            d.ellipse([X(skx + sx * 1.45 - 0.65), Y(sky - 0.9),
                       X(skx + sx * 1.45 + 0.65), Y(sky + 0.7)], fill=(26, 30, 26))
    for sx in (-1, 1):
        d.polygon(P([(sx * 9.6, hy - 12.0), (sx * 14.2, hy - 18.0),
                     (sx * 12.8, hy - 9.8)]), fill=(184, 176, 152))

    # necklace: a strand of small skulls across the chest
    for k in range(-5, 6):
        t = k / 5.0
        bx = t * 14.0
        by = 45.5 + (1.0 - t * t) * 8.5
        d.ellipse([X(bx - 1.2), Y(by - 1.2), X(bx + 1.2), Y(by + 1.2)], fill=GOLD)
        if k % 2 == 0:
            d.ellipse([X(bx - 0.8), Y(by - 0.75), X(bx + 0.8), Y(by + 1.4)],
                      fill=(236, 230, 206))
            for sx in (-1, 1):
                d.ellipse([X(bx + sx * 0.45 - 0.34), Y(by - 0.2),
                           X(bx + sx * 0.45 + 0.34), Y(by + 0.42)],
                          fill=(24, 26, 22))
    d.ellipse([X(-2.8), Y(55.8), X(2.8), Y(60.8)], fill=(232, 226, 202))
    for sx in (-1, 1):
        d.ellipse([X(sx * 1.4 - 0.8), Y(57.6), X(sx * 1.4 - 0.1), Y(58.8)],
                  fill=(22, 24, 20))

    # seams: dark creases where the parts meet, so the forms read even without
    # the neon (arm roots, chest over belly, lap under the sash)
    for sx in (-1, 1):
        d.line(P([(sx * 20, 50), (sx * 26, 58), (sx * 24, 66)]),
               fill=STONE_DK, width=max(1, int(0.55 * S * SS)))
    d.line(P([(-24, 60), (0, 62.5), (24, 60)]), fill=STONE_DK,
           width=max(1, int(0.5 * S * SS)))

    # ---------------------------------------------------------- lighting
    rgb = body.convert("RGB")
    ramp = _vgrad(w, h, [(0.0, 1.34), (0.24, 1.16), (0.55, 1.0),
                         (0.78, 0.86), (0.92, 0.72), (1.0, 0.62)])
    rgb = ImageChops.multiply(rgb, Image.merge("RGB", (ramp, ramp, ramp)))
    key = _radial(w, h, 0.40, 0.12, 0.50, 0.44).point(lambda v: int(v * 0.88))
    key_rgb = ImageChops.multiply(Image.new("RGB", (w, h), (198, 208, 172)),
                                  Image.merge("RGB", (key, key, key)))
    rgb = ImageChops.screen(rgb, key_rgb)
    # cool bounce off the hall, low on the right, keeps the shadow side readable
    bounce = _radial(w, h, 0.72, 0.62, 0.44, 0.42).point(lambda v: int(v * 0.34))
    bounce_rgb = ImageChops.multiply(Image.new("RGB", (w, h), (86, 150, 120)),
                                     Image.merge("RGB", (bounce, bounce, bounce)))
    rgb = ImageChops.screen(rgb, bounce_rgb)
    lit = Image.merge("RGBA", (*rgb.split(), body.split()[3]))

    small = lit.resize((max(1, w // SS), max(1, h // SS)), Image.LANCZOS)
    layer = Image.new("RGBA", (w_full, h_full), (0, 0, 0, 0))
    ox = int(round(cx + u0 * S))
    oy = int(round(top + v0 * S))
    layer.alpha_composite(small, (ox, oy))

    # ---------------------------------------------------------- neon
    # outer line: the silhouette, so the tube runs unbroken round the figure
    alpha = small.split()[3]
    solid = alpha.point(lambda v: 255 if v > 96 else 0)
    line = ImageChops.subtract(solid, solid.filter(ImageFilter.MinFilter(3)))
    line = line.filter(ImageFilter.MaxFilter(3))
    # inner lines: every part traced, which is what separates six arms from a
    # torso - the film's tube runs along the arm roots and the bangle rims
    # ...but only where that part is still visible: a flat trace would draw the
    # torso's outline straight across the belly that covers it, which reads as
    # scribble. Walking the shapes from the top of the stack down lets each
    # contour be clipped by the shapes painted over it, so the tube follows
    # what the camera can actually see.
    lw = max(1, int(0.34 * S * SS))
    inner = Image.new("L", (w, h), 0)
    covered = Image.new("L", (w, h), 0)
    for pts in reversed(contours):
        poly = Image.new("L", (w, h), 0)
        ImageDraw.Draw(poly).polygon(P(pts), fill=255)
        scratch = Image.new("L", (w, h), 0)
        ImageDraw.Draw(scratch).line(P(pts) + [P(pts)[0]], fill=255,
                                     width=lw, joint="curve")
        near = covered.filter(ImageFilter.MaxFilter(3))
        inner = ImageChops.lighter(inner,
                                   ImageChops.subtract(scratch, near))
        covered = ImageChops.lighter(covered, poly)
    inner = inner.resize(small.size, Image.LANCZOS).point(lambda v: int(v * 0.92))
    mask = ImageChops.lighter(line, inner)
    mask = mask.filter(ImageFilter.GaussianBlur(max(0.35, 0.14 * S)))
    glow = mask.filter(ImageFilter.GaussianBlur(max(1.4, 1.0 * S)))
    rim_small = Image.new("RGBA", small.size, (0, 0, 0, 0))
    rim_small.paste(Image.new("RGBA", small.size, NEON + (255,)), (0, 0),
                    mask.point(lambda v: int(v * 0.92)))
    rim_small.paste(Image.new("RGBA", small.size, NEON + (255,)), (0, 0),
                    glow.point(lambda v: int(v * 0.40)))
    rim = Image.new("RGBA", (w_full, h_full), (0, 0, 0, 0))
    rim.alpha_composite(rim_small, (ox, oy))

    # eye light, its own layer so the stage lighting cannot dim it
    eyes = Image.new("RGBA", (w_full, h_full), (0, 0, 0, 0))
    ed = ImageDraw.Draw(eyes)
    for sx in (-1, 1):
        ex = cx + sx * 5.1 * S
        ey = top + (HEAD[1] - 1.0) * S
        for rad, a in ((2.9, 24), (2.0, 54), (1.25, 104), (0.72, 165)):
            r = rad * S
            ed.ellipse([ex - r, ey - r * 0.84, ex + r, ey + r * 0.84],
                       fill=EYE + (a,))
    eyes = eyes.filter(ImageFilter.GaussianBlur(max(0.6, 0.16 * S)))

    return layer, rim, eyes
