"""The six-armed guardian of Lo Pan's ceremony hall, painted from the still.

In the film this is a stone statue: warm grey-brown, lit from below by the hall,
small snarling head under a tiara of skulls, a chest and belly carrying most of
the mass, six thick arms ending in hands with real fingers, a necklace and
pendant of skulls, gold bangles, a cloth sash across the lap, crossed legs.

So the figure is built the way a figure is drawn: smooth curved outlines and
tapered limbs on a 3x supersampled canvas, warm stone with mottling, lit once as
a whole - key from the upper left, cool bounce low, occlusion at the bottom - so
the arms, belly and lap belong to one body, and then the neon tube is laid on,
traced twice: once round the finished silhouette and once round each part, each
trace clipped to what is actually visible. The green stays on the tube and in a
faint bleed onto the stone beside it; the stone itself is grey.

Coordinates are units of the shared 4.5 canvas px: u is horizontal from the stage
centre, v is vertical from the top of the crown, v = 96 is the plinth top.

Used by tools/stage_ceremony.py.  Run: python3 tools/stage_ceremony.py
"""

from __future__ import annotations

import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter

SS = 3                                  # supersample: 3x, then LANCZOS down
BOX = (-80.0, -14.0, 80.0, 96.5)

STONE = (128, 118, 106)                 # warm grey stone, as in the still
STONE_LT = (198, 186, 170)
STONE_DK = (44, 38, 34)
FACE = (150, 140, 127)
GOLD = (204, 164, 82)
GOLD_DK = (88, 58, 24)
CLOTH = (104, 98, 88)
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
    """Points, unit tangents down a quadratic limb."""
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


def _taper(a, ctrl, b, w0, w1, n=30, swell=0.16, seed=0.0):
    """A limb: a quadratic spine whose width swells at the bicep.

    Returns the closed outline - two offset sides plus a semicircular cap at
    each end - so an arm reads as a heavy tube ending in a joint.
    """
    left, right = [], []
    for i, (x, y, tx, ty) in enumerate(_spine(a, ctrl, b, n)):
        t = i / n
        s = t * t * (3.0 - 2.0 * t)
        w = (w0 + (w1 - w0) * s) * (1.0 + swell * math.sin(math.pi * t) * math.sin(seed + 1.6))
        left.append((x - ty * w, y + tx * w))
        right.append((x + ty * w, y - tx * w))

    def cap(c, t_out, nrm, wid):
        tx, ty = t_out
        nx, ny = nrm
        return [(c[0] + (math.cos(ph) * nx + math.sin(ph) * tx) * wid,
                 c[1] + (math.cos(ph) * ny + math.sin(ph) * ty) * wid)
                for ph in (math.pi * k / 12 for k in range(13))]

    sp = _spine(a, ctrl, b, n)
    t0 = (sp[0][2], sp[0][3])
    t1 = (sp[-1][2], sp[-1][3])
    return (left + cap(b, t1, (-t1[1], t1[0]), w1)
            + right[::-1] + cap(a, (-t0[0], -t0[1]), (t0[1], -t0[0]), w0))


def _capsule(d, a, b, w0, w1, fill, edge=None, ew=0.0):
    """Straight tapered capsule - a finger, a toe, a fold - with an optional
    dark rim, so fingers separate from the palm behind them."""
    pts = _taper(a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b, w0, w1,
                 n=10, swell=0.0)
    if edge:
        d.line(pts + [pts[0]], fill=edge, width=max(1, ew), joint="curve")
    d.polygon(pts, fill=fill)
    return pts


def _fist(d, c, r, ang, fill, seam, lit, dark):
    """A closed fist, the way the still's six hands are: all knuckles forward.

    Seen from the back of the hand - which is what faces the hall - the four
    fingers lie SIDE BY SIDE pointing away from the wrist, so the fingers and the
    grooves between them run along the arm, from the knuckle row at the far end
    back to the wrist. Rolling them across the hand instead (the old version)
    turned every fist into a bandaged barrel with the fingers pointing the wrong
    way. The knuckle row sits on the far edge, the fingertips curl out of sight
    over it, and the thumb lies across the outer side, its tip just short of the
    knuckles.
    """
    ax, ay = math.cos(ang), math.sin(ang)      # out along the arm, to the knuckles
    nx, ny = -ay, ax                           # across the back of the hand
    ew = max(2, int(r * 0.15))

    def at(fx, fy):
        return (c[0] + (ax * fx + nx * fy) * r, c[1] + (ay * fx + ny * fy) * r)

    def ell(fx, fy, rx, ry, col, outline=None, ow=0):
        pts = [at(fx + rx * math.cos(2 * math.pi * k / 30),
                  fy + ry * math.sin(2 * math.pi * k / 30)) for k in range(30)]
        d.polygon(pts, fill=col)
        if outline:
            d.line(pts + [pts[0]], fill=outline, width=ow)
        return pts

    # the hand: a block broader across than along the arm, clearly wider than
    # the wrist behind it
    ell(0.0, 0.0, 0.95, 1.02, fill)

    # four fingers abreast, running along the arm, dark grooves between them
    for fy in (-0.645, -0.215, 0.215, 0.645):
        _capsule(d, at(0.86, fy * 0.98), at(-0.66, fy),
                 r * 0.205, r * 0.215, fill, seam, ew)
        # the lit crown of each finger, so they read one at a time
        d.line([at(0.80, fy * 0.98 - 0.085), at(-0.56, fy - 0.085)],
               fill=lit, width=max(1, int(r * 0.055)))

    # the flexed joint crease across the fingers, just behind the knuckles
    d.line([at(0.56, -0.86), at(0.56, 0.86)], fill=seam,
           width=max(2, int(r * 0.095)))

    # the knuckle row on the far edge, and the shadow of the fingertips curling
    # out of sight past it
    ell(1.00, 0.0, 0.16, 0.92, dark)
    for fy in (-0.645, -0.215, 0.215, 0.645):
        ell(0.92, fy, 0.205, 0.19, fill, seam, max(1, int(r * 0.06)))
        ell(0.90, fy - 0.045, 0.135, 0.115, lit)

    # the wrist shadow, so the fist sits on the forearm rather than merging
    d.line([at(-0.84, -0.74), at(-0.84, 0.74)], fill=seam,
           width=max(2, int(r * 0.12)))

    # thumb across the outer side, tip short of the knuckles
    _capsule(d, at(-0.18, -0.98), at(0.58, -0.58),
             r * 0.255, r * 0.195, fill, seam, ew)
    ell(0.60, -0.56, 0.17, 0.155, fill, seam, max(1, int(r * 0.06)))
    d.line([at(0.10, -1.06), at(0.34, -0.80)], fill=lit,
           width=max(1, int(r * 0.05)))


def _vgrad(w, h, stops):
    """Vertical ramp as an L image from (position, gain) stops, gain x255."""
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


    def blob(d, pts, fill=STONE, smooth=14):
        d.polygon(P(_catmull(pts, True, smooth)), fill=fill)

    body = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    seam = max(1, int(0.26 * S * SS))

    # ---- crossed legs on the drum: thighs, knees, shins, feet -------------
    blob(d, [(-55, 93), (-45, 86), (-30, 83.5), (-14, 87.5), (0, 92),
             (14, 87.5), (30, 83.5), (45, 86), (55, 93), (51, 96.5), (-51, 96.5)])
    for sx in (-1, 1):                       # thighs, heavy and separated
        blob(d, [(sx * 20, 84), (sx * 34, 82.5), (sx * 44, 86), (sx * 47, 91),
                 (sx * 38, 92.5), (sx * 24, 90.5)])
        blob(d, [(sx * 25, 84.5), (sx * 33, 84), (sx * 35, 87), (sx * 27, 88)],
             STONE_LT if sx > 0 else STONE)   # knee cap catches light
    blob(d, [(-12, 90), (0, 87.5), (12, 90), (10, 94.5), (-10, 94.5)])  # shins
    for sx in (-1, 1):                       # feet crossed at the centre
        blob(d, [(sx * 2, 93), (sx * 13, 92), (sx * 15, 95.5), (sx * 3, 96)],
             STONE)
        for k in range(3):
            d.line(P([(sx * (5 + k * 3), 94.2), (sx * (6 + k * 3), 95.8)]),
                   fill=STONE_DK, width=max(1, int(0.18 * S * SS)))

    # ---- torso: traps, chest, waist, belly -------------------------------
    torso = [(-27, 44), (-30, 52), (-31, 60), (-32, 67), (-34, 74), (-33, 82),
             (-27, 89), (-16, 92), (0, 93), (16, 92), (27, 89), (33, 82),
             (34, 74), (32, 67), (31, 60), (30, 52), (27, 44), (15, 40), (0, 39),
             (-15, 40)]
    blob(d, torso)
    blob(d, [(-28, 74), (-20, 66), (0, 63), (20, 66), (28, 74), (26, 86),
             (12, 91), (-12, 91), (-26, 86)])                     # belly
    for sx in (-1, 1):                                            # pectorals
        blob(d, [(sx * 2, 45), (sx * 12, 43.5), (sx * 23, 47), (sx * 21, 56),
                 (sx * 10, 58.5), (sx * 2, 54)])
    d.line(P([(0, 44), (0, 58)]), fill=STONE_DK, width=seam)      # sternum
    for vy in (66, 73, 80):                                       # belly folds
        d.arc([X(-16), Y(vy - 3), X(16), Y(vy + 3)], 20, 160, fill=STONE_DK,
              width=max(1, int(0.20 * S * SS)))
    d.ellipse([X(-1.8), Y(84.5), X(1.8), Y(88)], fill=STONE_DK)   # navel

    # ---- sash: cloth slung across the lap, with folds that hang ----------
    sash = [(-29, 75), (-17, 79), (-2, 81), (13, 82.5), (28, 86), (30, 95),
            (12, 92.5), (-8, 90.5), (-24, 87.5), (-30, 81)]
    blob(d, sash, CLOTH)
    for k in range(3):
        d.line(P([(-28 + k * 3, 78 + k * 2.0), (-6, 84 + k * 2.0),
                  (16, 86.5 + k * 2.0), (28, 90 + k * 2.0)]),
               fill=(58, 54, 48), width=seam)
        d.line(P([(-28 + k * 3, 78.6 + k * 2.0), (-6, 84.6 + k * 2.0),
                  (16, 87.1 + k * 2.0), (28, 90.6 + k * 2.0)]),
               fill=(150, 142, 126), width=max(1, int(0.16 * S * SS)))
    d.line(P([(-29, 75.4), (-17, 79.4), (-2, 81.4), (13, 82.9), (28, 86.4)]),
           fill=(168, 158, 140), width=max(1, int(0.24 * S * SS)))

    # ---- six arms: three pairs, every one bent hard at the elbow ---------
    # In the still the arms are not spokes off the shoulders: each turns a
    # corner, the upper pairs throwing the fists up above the head and the
    # lowest pair hanging open over the knees. Widths taper shoulder to wrist.
    arms = [
        # shoulder,     elbow,       wrist,       w0    w1    w2    w3   hand
        ((24, 56), (46, 62), (60, 59), 9.8, 8.2, 7.4, 6.2, 9.9),
        ((22, 48), (45, 37), (54, 24), 10.6, 8.8, 8.0, 6.4, 10.6),
        ((14, 43), (30, 29), (24, 15), 10.2, 8.6, 7.8, 6.2, 10.8),
    ]

    def ring(p, tx, ty, half, thick, fill=GOLD):
        nx_, ny_ = -ty, tx
        quad = [(p[0] + nx_ * half - tx * thick, p[1] + ny_ * half - ty * thick),
                (p[0] - nx_ * half - tx * thick, p[1] - ny_ * half - ty * thick),
                (p[0] - nx_ * half + tx * thick, p[1] - ny_ * half + ty * thick),
                (p[0] + nx_ * half + tx * thick, p[1] + ny_ * half + ty * thick)]
        d.polygon(P(quad), fill=fill)
        d.line(P([(p[0] + nx_ * half - tx * thick, p[1] + ny_ * half - ty * thick),
                  (p[0] - nx_ * half - tx * thick, p[1] - ny_ * half - ty * thick)]),
               fill=(248, 222, 152), width=max(1, int(0.14 * S * SS)))

    for sx in (-1, 1):
        for sh, el, wr, w0, w1, w2, w3, hr in arms:
            sh_p = (sx * sh[0], sh[1])
            el_p = (sx * el[0], el[1])
            wr_p = (sx * wr[0], wr[1])
            d.ellipse([X(sh_p[0] - w0 * 1.08), Y(sh_p[1] - w0 * 1.08),
                       X(sh_p[0] + w0 * 1.08), Y(sh_p[1] + w0 * 1.08)], fill=STONE)
            upper = _taper(sh_p, ((sh_p[0] + el_p[0]) / 2,
                                  (sh_p[1] + el_p[1]) / 2 + 1.4),
                           el_p, w0, w1)
            d.line(P(upper) + [P(upper)[0]], fill=STONE_DK,
                   width=max(2, int(1.1 * S * SS)), joint="curve")
            d.polygon(P(upper), fill=STONE)
            d.ellipse([X(el_p[0] - w1), Y(el_p[1] - w1),
                       X(el_p[0] + w1), Y(el_p[1] + w1)],
                      fill=STONE, outline=STONE_DK, width=max(1, int(0.6 * S * SS)))
            fore_ctrl = ((el_p[0] + wr_p[0]) / 2, (el_p[1] + wr_p[1]) / 2)
            fore = _taper(el_p, fore_ctrl, wr_p, w2 * 0.94, w3)
            d.line(P(fore) + [P(fore)[0]], fill=STONE_DK,
                   width=max(2, int(1.1 * S * SS)), joint="curve")
            d.polygon(P(fore), fill=STONE)
            ang = math.atan2(wr_p[1] - el_p[1], wr_p[0] - el_p[0])
            hc = (wr_p[0] + math.cos(ang) * hr * 0.86,
                  wr_p[1] + math.sin(ang) * hr * 0.86)
            # hands are drawn straight into canvas pixels, so the centre and the
            # radius have to be transformed. Passing unit-space values put every
            # fist a fifth of its size in the corner of the canvas, which is why no
            # hand ever appeared on the figure.
            hc_px = (X(hc[0]), Y(hc[1]))
            hr_px = hr * S * SS
            _fist(d, hc_px, hr_px, ang, STONE, STONE_DK, STONE_LT, (96, 88, 80))
            # bangles: the still's cuffs sit right at the wrist and inboard of
            # it, and their width follows the forearm they wrap - a ring cut to
            # the arm's width at the elbow floats off it
            sp = _spine(el_p, fore_ctrl, wr_p)
            for idx in (len(sp) - 1, len(sp) - 4):
                bx_, by_, tx, ty = sp[max(0, idx)]
                t = max(0, idx) / (len(sp) - 1)
                s_ = t * t * (3.0 - 2.0 * t)
                half_w = (w2 * 0.94 + (w3 - w2 * 0.94) * s_) * 1.10
                ring((bx_, by_), tx, ty, half_w, 1.05)

    # ---- head ------------------------------------------------------------
    hx, hy = HEAD
    blob(d, [(-9.5, 40), (-6.5, 32), (6.5, 32), (9.5, 40), (0, 43)], STONE_DK)
    for sx in (-1, 1):
        blob(d, [(sx * 10, 41), (sx * 24, 44), (sx * 26, 49), (sx * 12, 46)])                                     # trapezius
        blob(d, [(sx * (HEAD_RX - 1.0), hy - 6.5), (sx * (HEAD_RX + 2.2), hy - 5.0),
                 (sx * (HEAD_RX + 1.8), hy + 8.0), (sx * (HEAD_RX - 2.4), hy + 6.5)])
    d.ellipse([X(hx - HEAD_RX), Y(hy - HEAD_RY), X(hx + HEAD_RX), Y(hy + HEAD_RY)],
              fill=FACE)
    blob(d, [(-10, hy + 5), (0, hy + 9.5), (10, hy + 5), (0, hy + 14.5)], FACE)                                         # jaw
    # cheek planes and the shadow under the brow
    for sx in (-1, 1):
        d.ellipse([X(sx * 7.2 - 3.4), Y(hy + 0.5), X(sx * 7.2 + 3.4), Y(hy + 5.5)],
                  fill=(136, 126, 114))
    # brows: heavy bars angled down into the nose bridge
    for sx in (-1, 1):
        blob(d, [(sx * 1.0, hy - 5.6), (sx * 10.0, hy - 7.2), (sx * 10.4, hy - 4.2),
                 (sx * 1.4, hy - 2.2)], (52, 46, 42))
    # eye sockets, deep and wide
    for sx in (-1, 1):
        ex = hx + sx * 5.1
        d.ellipse([X(ex - 3.8), Y(hy - 3.6), X(ex + 3.8), Y(hy + 1.8)],
                  fill=(22, 18, 18))
        d.arc([X(ex - 3.6), Y(hy - 3.4), X(ex + 3.6), Y(hy + 1.6)], 200, 340,
              fill=(174, 162, 146), width=max(1, int(0.26 * S * SS)))
    # nose: bridge, bulb, flared nostrils
    blob(d, [(0, hy - 3.6), (2.8, hy - 0.2), (2.7, hy + 2.6), (1.4, hy + 3.6),
             (-1.4, hy + 3.6), (-2.7, hy + 2.6), (-2.8, hy - 0.2)],
         (162, 152, 138))
    for sx in (-1, 1):
        d.ellipse([X(sx * 2.9 - 1.0), Y(hy + 2.9), X(sx * 2.9 + 1.0), Y(hy + 4.2)],
                  fill=(44, 38, 34))
    # mouth: wide open snarl, upper row seen, four fangs standing off the jaw
    my = hy + 8.4
    d.polygon(P([(-7.2, my - 1.9), (-3.8, my - 0.4), (0, my + 0.3),
                 (3.8, my - 0.4), (7.2, my - 1.9),
                 (6.0, my + 2.5), (0, my + 3.4), (-6.0, my + 2.5)]),
              fill=(16, 12, 12))
    d.line(P([(-7.2, my - 1.9), (-3.8, my - 0.4), (0, my + 0.3),
              (3.8, my - 0.4), (7.2, my - 1.9)]),
           fill=(178, 166, 148), width=max(1, int(0.30 * S * SS)))
    for k in (-0.75, -0.45, -0.15, 0.15, 0.45, 0.75):
        tx = k * 6.2
        d.polygon(P([(tx - 0.60, my - 1.2), (tx + 0.60, my - 1.2), (tx, my + 0.6)]),
                  fill=(228, 222, 202))
    for k, size in ((-0.55, 1.0), (-0.19, 0.64), (0.19, 0.64), (0.55, 1.0)):
        tx = k * 8.8
        wdt, hgt = 0.82 * size, 2.8 * size
        d.polygon(P([(tx - wdt, my + 2.4), (tx + wdt, my + 2.4), (tx, my + 2.4 - hgt)]),
                  fill=(238, 232, 212))
    d.line(P([(-6.0, my + 2.5), (0, my + 3.5), (6.0, my + 2.5)]),
           fill=(70, 62, 56), width=max(1, int(0.38 * S * SS)))
    d.arc([X(-5.8), Y(my + 2.8), X(5.8), Y(hy + 14.2)], 15, 165,
          fill=(128, 118, 104), width=max(1, int(0.30 * S * SS)))   # chin

    # ---- crown: a band of skulls with horns ------------------------------
    d.polygon(P([(-HEAD_RX, hy - 13.0), (HEAD_RX, hy - 13.0),
                 (HEAD_RX, hy - 9.0), (-HEAD_RX, hy - 9.0)]), fill=GOLD)
    for k in range(-2, 3):
        skx = k * 5.0
        sky = hy - 11.6
        d.ellipse([X(skx - 3.0), Y(sky - 3.1), X(skx + 3.0), Y(sky + 2.0)],
                  fill=(228, 220, 200))
        d.polygon(P([(skx - 2.3, sky + 1.2), (skx + 2.3, sky + 1.2),
                     (skx + 1.8, sky + 3.6), (skx - 1.8, sky + 3.6)]),
                  fill=(228, 220, 200))
        for sx in (-1, 1):
            d.ellipse([X(skx + sx * 1.5 - 0.7), Y(sky - 1.0),
                       X(skx + sx * 1.5 + 0.7), Y(sky + 0.8)], fill=(28, 26, 24))
        d.line(P([(skx, sky + 1.0), (skx, sky + 2.8)]), fill=(120, 112, 96),
               width=max(1, int(0.16 * S * SS)))
    for sx in (-1, 1):
        d.polygon(P([(sx * 9.8, hy - 12.4), (sx * 14.6, hy - 18.6),
                     (sx * 13.0, hy - 10.0)]), fill=(186, 176, 156))

    # ---- necklace: a strand of skulls and a pendant ----------------------
    for k in range(-5, 6):
        t = k / 5.0
        bx, by = t * 14.5, 44.5 + (1.0 - t * t) * 9.0
        d.ellipse([X(bx - 1.2), Y(by - 1.2), X(bx + 1.2), Y(by + 1.2)], fill=GOLD)
        if k % 2 == 0:
            d.ellipse([X(bx - 0.85), Y(by - 0.8), X(bx + 0.85), Y(by + 1.5)],
                      fill=(230, 224, 202))
            for sx in (-1, 1):
                d.ellipse([X(bx + sx * 0.47 - 0.36), Y(by - 0.2),
                           X(bx + sx * 0.47 + 0.36), Y(by + 0.45)],
                          fill=(24, 22, 20))
    d.ellipse([X(-3.0), Y(55.6), X(3.0), Y(61.0)], fill=(228, 222, 200))
    for sx in (-1, 1):
        d.ellipse([X(sx * 1.5 - 0.85), Y(57.5), X(sx * 1.5 - 0.1), Y(58.8)],
                  fill=(22, 20, 18))

    # ---- stone mottling, then one light over the whole body --------------
    rgb = body.convert("RGB")
    noise = Image.effect_noise((max(2, w // 24), max(2, h // 24)), 34)
    noise = noise.filter(ImageFilter.GaussianBlur(2)).resize((w, h), Image.BICUBIC)
    noise = noise.point(lambda v: 128 + (v - 128) // 3)
    rgb = ImageChops.multiply(rgb, Image.merge("RGB", (noise, noise, noise)))
    rgb = rgb.point(lambda v: int(min(255, (v / 255.0) ** 0.92 * 255)))

    ramp = _vgrad(w, h, [(0.0, 1.24), (0.26, 1.10), (0.56, 0.98),
                         (0.80, 0.84), (0.93, 0.68), (1.0, 0.56)])
    rgb = ImageChops.multiply(rgb, Image.merge("RGB", (ramp, ramp, ramp)))
    key = _radial(w, h, 0.40, 0.12, 0.48, 0.42).point(lambda v: int(v * 0.80))
    key_rgb = ImageChops.multiply(Image.new("RGB", (w, h), (255, 234, 198)),
                                  Image.merge("RGB", (key, key, key)))
    rgb = ImageChops.screen(rgb, key_rgb)
    # the hall's neon bounces cool green up the shadow side
    bounce = _radial(w, h, 0.74, 0.60, 0.42, 0.40).point(lambda v: int(v * 0.30))
    bounce_rgb = ImageChops.multiply(Image.new("RGB", (w, h), (74, 170, 132)),
                                     Image.merge("RGB", (bounce, bounce, bounce)))
    rgb = ImageChops.screen(rgb, bounce_rgb)
    lit = Image.merge("RGBA", (*rgb.split(), body.split()[3]))

    small = lit.resize((max(1, w // SS), max(1, h // SS)), Image.LANCZOS)
    layer = Image.new("RGBA", (w_full, h_full), (0, 0, 0, 0))
    ox = int(round(cx + u0 * S))
    oy = int(round(top + v0 * S))
    layer.alpha_composite(small, (ox, oy))

    # ---- neon -----------------------------------------------------------
    alpha = small.split()[3]
    solid = alpha.point(lambda v: 255 if v > 96 else 0)
    outer = ImageChops.subtract(solid, solid.filter(ImageFilter.MinFilter(3)))
    outer = outer.filter(ImageFilter.MaxFilter(3))

    # The tube in the still is one line round the outside of the statue: no
    # lines across the belly, the arms or the cloth. So the neon is the
    # silhouette and nothing else.
    mask = outer.filter(ImageFilter.GaussianBlur(max(0.32, 0.13 * S)))

    # the tube bleeds a little green onto the stone right beside it, which is
    # what keeps the figure from looking like a cut-out
    bleed = mask.filter(ImageFilter.GaussianBlur(max(1.6, 1.5 * S))).point(
        lambda v: int(v * 0.42))
    bleed = ImageChops.multiply(bleed, small.split()[3])
    layer.paste(Image.new("RGB", small.size, (46, 190, 128)), (ox, oy), bleed)

    line = mask.point(lambda v: int(v * 0.95))
    glow = mask.filter(ImageFilter.GaussianBlur(max(1.4, 1.0 * S))).point(
        lambda v: int(v * 0.40))
    rim_small = Image.new("RGBA", small.size, (0, 0, 0, 0))
    rim_small.paste(Image.new("RGBA", small.size, NEON + (255,)), (0, 0), line)
    rim_small.paste(Image.new("RGBA", small.size, NEON + (255,)), (0, 0), glow)
    rim = Image.new("RGBA", (w_full, h_full), (0, 0, 0, 0))
    rim.alpha_composite(rim_small, (ox, oy))

    # ---- eye light, its own layer so the hall cannot dim it -------------
    eyes = Image.new("RGBA", (w_full, h_full), (0, 0, 0, 0))
    ed = ImageDraw.Draw(eyes)
    for sx in (-1, 1):
        ex = cx + sx * 5.1 * S
        ey = top + (HEAD[1] - 1.0) * S
        for rad, a in ((2.8, 22), (1.9, 52), (1.2, 104), (0.70, 168)):
            r = rad * S
            ed.ellipse([ex - r, ey - r * 0.82, ex + r, ey + r * 0.82],
                       fill=EYE + (a,))
    eyes = eyes.filter(ImageFilter.GaussianBlur(max(0.6, 0.15 * S)))

    return layer, rim, eyes
