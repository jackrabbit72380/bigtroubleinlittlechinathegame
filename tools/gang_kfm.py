"""Gang fighters built from the real Kung Fu Man art instead of drawn parts.

The base sprites in chars/kfm are indexed art, 47x106 for the idle frame. Every
gang member is that same art, recoloured by rewriting the palette roles (gi
cloth, trousers, headband and belt, hair, skin) and then upscaled to the
roster's 318px height. That keeps Kung Fu Man's real anatomy and shading while
still giving each member his own cloth tone, headband colour and weapon.

Every member is the same height: identity comes from what he carries and what
is on his face and head - a moustache, a beard, long hair, a bandolier of brass
bullets, a staff, a machete, a hatchet or two gold pistols - not from scale.

Props are painted onto the real frames: the hands are found by their skin
colour and the face by the top of the silhouette, so the weapon stays in the
fist and the moustache stays on the face in all 279 frames.

Run:  python3 tools/gang_kfm.py --sheet
"""

from __future__ import annotations

import colorsys
import math
import os
import re
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "chars", "kfm")
SCALE = 3                      # 106px base -> 318px, the roster height
PAD_X, PAD_Y = 96, 60          # room around the figure for staff and machete

# Every colour Kung Fu Man uses in palette 0, with the role it plays. The base
# wears a white gi, pale baggy trousers, a blue headband/belt/shoes and black
# hair; recolouring by role keeps each shading ramp intact, so highlights stay
# highlights and the figure keeps its volume.
ROLE = {
    (0x00, 0x00, 0x00): "outline",
    (0x31, 0x31, 0x31): "hair",
    (0x5a, 0x5a, 0x63): "hair_h",
    (0x42, 0x63, 0xa5): "trim_d",
    (0x80, 0x94, 0xc4): "trim",
    (0xa5, 0xb5, 0xde): "trim_l",
    (0x84, 0x42, 0x31): "skin_d2",
    (0x84, 0x6b, 0x5a): "skin_d",
    (0xa5, 0x90, 0x7d): "wrap_d",
    (0xbd, 0x73, 0x5a): "skin_2",
    (0xce, 0xb5, 0xa5): "wrap",
    (0xd4, 0x83, 0x63): "skin_3",
    (0xe7, 0x94, 0x73): "skin_4",
    (0xe7, 0xd6, 0xc6): "gi_s",
    (0xef, 0xbd, 0x9c): "skin_h",
    (0xf7, 0xef, 0xe7): "gi",
    (0xf7, 0xf7, 0xf7): "gi_h",
}

SKIN = {
    "skin_d2": (0x84, 0x42, 0x31),
    "skin_d": (0x84, 0x6b, 0x5a),
    "skin_2": (0xbd, 0x73, 0x5a),
    "skin_3": (0xd4, 0x83, 0x63),
    "skin_4": (0xe7, 0x94, 0x73),
    "skin_h": (0xef, 0xbd, 0x9c),
}

# Chang Sing: tan gi and trousers over black underclothes, black sash, gold band.
CHANG = {
    "gi_s": (0x8e, 0x78, 0x50), "gi": (0xc2, 0xa9, 0x7c), "gi_h": (0xdc, 0xc6, 0x99),
    "wrap_d": (0x6d, 0x5c, 0x3d), "wrap": (0x99, 0x83, 0x5b),
    "hair": (0x14, 0x12, 0x10), "hair_h": (0x2c, 0x28, 0x24),
    "outline": (0x08, 0x07, 0x06),
    "trim_d": (0x7a, 0x5a, 0x14), "trim": (0xc8, 0x95, 0x2f), "trim_l": (0xe6, 0xbb, 0x5c),
}

# Wing Kong: black gi and trousers, red trim and band.
WING = {
    "gi_s": (0x12, 0x12, 0x17), "gi": (0x22, 0x22, 0x2b), "gi_h": (0x31, 0x31, 0x3c),
    "wrap_d": (0x0e, 0x0e, 0x12), "wrap": (0x1b, 0x1b, 0x22),
    "hair": (0x0d, 0x0d, 0x10), "hair_h": (0x22, 0x22, 0x28),
    "outline": (0x06, 0x06, 0x08),
    "trim_d": (0x6d, 0x16, 0x1b), "trim": (0xa8, 0x22, 0x28), "trim_l": (0xcf, 0x38, 0x3c),
}

# Hair presets. "shaved" borrows the skin ramp, so the scalp is bare.
HAIR = {
    "black": ((0x14, 0x12, 0x10), (0x2c, 0x28, 0x24)),
    "brown": ((0x2b, 0x1c, 0x12), (0x46, 0x30, 0x20)),
    "grey": ((0x5d, 0x5b, 0x57), (0x84, 0x82, 0x7c)),
    "shaved": (SKIN["skin_d"], SKIN["skin_2"]),
}

STAFF = dict(wood=(0x6b, 0x4a, 0x2a), wood_hi=(0x9c, 0x72, 0x44),
             cap=(0xc8, 0x95, 0x2f), edge=(0x2b, 0x1d, 0x10))
BLADE = dict(steel=(0x8d, 0x97, 0xa6), steel_mid=(0x6d, 0x77, 0x86),
             steel_hi=(0xe8, 0xee, 0xf6), spine=(0x25, 0x29, 0x31),
             grip=(0x3a, 0x24, 0x18), guard=(0xc8, 0x95, 0x2f),
             edge=(0x4a, 0x51, 0x5d))
GOLD = dict(dark=(0x6b, 0x48, 0x12), mid=(0xc9, 0x96, 0x2f), lit=(0xf4, 0xd8, 0x78))
LEATHER = dict(dark=(0x33, 0x24, 0x1a), mid=(0x5d, 0x43, 0x2e), lit=(0x8a, 0x66, 0x46))
BRASS = GOLD

# One entry per fighter. Everything is the same height; no build scale.
#   cloth / skin / band : tone multipliers on the gang palette
#   hair   : preset name          face : "", "moustache", "beard", "full"
#   gear   : "", "bandolier"      weapon: staff, machete, hatchet, pistols
MEMBERS = [
    dict(id="changsing_bo", gang="chang", cloth=1.02, skin=1.00, band=1.00,
         hair="black", face="moustache", gear="", weapon="staff", length=216),
    dict(id="changsing_lin", gang="chang", cloth=0.90, skin=1.06, band=0.72,
         hair="brown", face="", gear="", weapon="staff", length=200),
    dict(id="changsing_shi", gang="chang", cloth=1.12, skin=0.94, band=1.00,
         hair="black", face="beard", gear="", weapon="staff", length=210),
    dict(id="changsing_han", gang="chang", cloth=0.82, skin=0.88, band=0.55,
         hair="grey", face="full", gear="", weapon="staff", length=228),
    dict(id="changsing_wei", gang="chang", cloth=1.16, skin=1.02, band=1.20,
         hair="black", face="", gear="", weapon="staff", length=192),
    dict(id="changsing_tam", gang="chang", cloth=0.95, skin=0.98, band=0.40,
         hair="black", face="moustache", gear="", weapon="staff", length=222),
    dict(id="wingkong_gou", gang="wing", cloth=1.00, skin=1.00, band=1.00,
         hair="black", face="moustache", gear="", weapon="machete", length=124),
    dict(id="wingkong_ma", gang="wing", cloth=0.88, skin=1.06, band=1.15,
         hair="black", face="", gear="", weapon="machete", length=116),
    dict(id="wingkong_zhao", gang="wing", cloth=1.12, skin=0.92, band=0.70,
         hair="black", face="beard", gear="", weapon="machete", length=132),
    dict(id="wingkong_lu", gang="wing", cloth=0.80, skin=1.00, band=0.50,
         hair="brown", face="", gear="", weapon="machete", length=110),
    # Gold Gun Gerald: bandoliers of brass bullets and a gold pistol in each
    # hand. No blade of any kind.
    dict(id="wingkong_gerald", gang="wing", cloth=0.94, skin=0.96, band=1.10,
         hair="brown", face="full", gear="bandolier", weapon="pistols", length=44),
    # Wing Kong Hatchet Man: bald with long hair down the back, heavy
    # moustache, hatchet in the lead fist.
    dict(id="wingkong_hatchet", gang="wing", cloth=1.06, skin=1.04, band=0.85,
         hair="brown", face="moustache", gear="", weapon="hatchet", length=104),
]


def _shade(c, k):
    """Scale a colour's brightness, keeping it inside 0..255."""
    return tuple(max(0, min(255, int(v * k))) for v in c[:3])


def _warm(c, k):
    """Nudge a skin colour warm or cool without leaving the skin ramp."""
    r, g, b = c[:3]
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    h = (h + (k - 1.0) * 0.05) % 1.0
    s = max(0.0, min(1.0, s * (1.0 + (k - 1.0) * 0.6)))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return (int(r * 255), int(g * 255), int(b * 255))


def member(cid):
    return next(m for m in MEMBERS if m["id"] == cid)


def colour_map(gang, cloth=1.0, skin=1.0, band=1.0, hair="black"):
    """old RGB -> new RGB for one member."""
    base = CHANG if gang == "chang" else WING
    hair_d, hair_h = HAIR[hair]
    out = {}
    for rgb, role in ROLE.items():
        if role.startswith("skin"):
            out[rgb] = _warm(SKIN[role], skin)
        elif role.startswith("hair"):
            out[rgb] = hair_d if role == "hair" else hair_h
        elif role.startswith("trim"):
            out[rgb] = _shade(base[role], band)
        elif role.startswith("gi"):
            out[rgb] = _shade(base[role], cloth)
        else:
            out[rgb] = base.get(role, rgb)
    return out


def recolour(img, mapping):
    """Rewrite a decoded sprite's colours through ``mapping``."""
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a:
                c = mapping.get((r, g, b))
                if c:
                    px[x, y] = (c[0], c[1], c[2], a)
    return img


def upscale(img, scale=SCALE):
    """Take the 1990s sprite up to roster height, clean, then re-sharpen.

    The transparent pixels of the base art still carry a light colour, and a
    plain LANCZOS pass bleeds it onto every silhouette edge - that is what the
    white fringe was. Clearing the hidden colour first and dropping the faint
    half-pixels afterwards leaves an edge that reads as drawn, not cut out.
    """
    w, h = img.size
    empty = Image.new("RGBA", img.size, (0, 0, 0, 0))
    img = Image.composite(img, empty, img.split()[3])
    big = img.resize((w * scale, h * scale), Image.LANCZOS)
    big.putalpha(big.split()[3].point(lambda v: 255 if v >= 140 else 0))
    return big.filter(ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=3))


# --------------------------------------------------------------- finding things
def _opaque(img):
    return img.split()[3].point(lambda a: 255 if a else 0)


def hands(img, skin_rgb, limit=2):
    """Centre of each fist, most forward first, so a weapon has a grip."""
    w, h = img.size
    px = img.load()
    pts = [(x, y) for y in range(h) for x in range(w)
           if px[x, y][3] and (px[x, y][0], px[x, y][1], px[x, y][2]) in skin_rgb]
    out = []
    while pts and len(out) < limit:
        best = max(pts, key=lambda p: p[0] + p[1] * 0.15)
        near = [p for p in pts
                if abs(p[0] - best[0]) < 17 and abs(p[1] - best[1]) < 17]
        out.append((sum(p[0] for p in near) / len(near),
                    sum(p[1] for p in near) / len(near)))
        taken = set(near)
        pts = [p for p in pts if p not in taken]
    return out


def head_anchor(img):
    """Centre, height and half-width of the head, taken from the silhouette."""
    mask = _opaque(img)
    box = mask.getbbox()
    if not box:
        return None
    top = box[1]
    height = box[3] - top
    band = top + max(5, int(height * 0.17))
    px = mask.load()
    xs = [x for y in range(top, band) for x in range(box[0], box[2]) if px[x, y]]
    if not xs:
        return None
    lo, hi = min(xs), max(xs)
    hw = max(7.0, (hi - lo) / 2.0)
    return ((lo + hi) / 2.0, top + height * 0.075, hw)


def torso_band(img):
    """Left, top, right, bottom of the chest, for the bandolier."""
    mask = _opaque(img)
    box = mask.getbbox()
    if not box:
        return None
    top, height = box[1], box[3] - box[1]
    y0, y1 = int(top + height * 0.31), int(top + height * 0.50)
    px = mask.load()
    lefts, rights = [], []
    for y in range(y0, y1):
        row = [x for x in range(box[0], box[2]) if px[x, y]]
        if row:
            lefts.append(row[0])
            rights.append(row[-1])
    if not lefts:
        return None
    return (min(lefts), y0, max(rights), y1)


# --------------------------------------------------------------------- weapons
def draw_staff(d, grip, length=216.0, angle=-0.14):
    """A six-foot staff held out in front, butt behind the fist."""
    gx, gy = grip
    dx, dy = math.cos(angle), math.sin(angle)
    x0, y0 = gx - dx * length * 0.22, gy - dy * length * 0.22
    x1, y1 = gx + dx * length * 0.78, gy + dy * length * 0.78
    d.line([(x0, y0), (x1, y1)], fill=STAFF["edge"], width=11)
    d.line([(x0, y0), (x1, y1)], fill=STAFF["wood"], width=8)
    d.line([(x0 - dy * 2, y0 + dx * 2), (x1 - dy * 2, y1 + dx * 2)],
           fill=STAFF["wood_hi"], width=2)
    for t in (0.0, 1.0):
        cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=STAFF["cap"],
                  outline=STAFF["edge"])


def draw_machete(d, grip, length=120.0, angle=-0.10):
    """A long chopper: straight spine, deep belly, chamfered tip, wrapped grip.

    Coordinates run along the blade (t) and across it (u, positive = the side
    the edge hangs on), so the shape stays the same at any hand angle.
    """
    gx, gy = grip
    dx, dy = math.cos(angle), math.sin(angle)
    nx, ny = -dy, dx

    def P(t, u):
        return (gx + dx * t + nx * u, gy + dy * t + ny * u)

    # grip through the fist, brass guard where the blade starts
    d.line([P(-26, 3), P(6, 3)], fill=BLADE["spine"], width=15)
    d.line([P(-24, 3), P(5, 3)], fill=BLADE["grip"], width=10)
    for t in (-18, -12, -6):
        d.line([P(t, -2), P(t + 1, 8)], fill=LEATHER["mid"], width=2)
    d.line([P(6, -9), P(6, 15)], fill=BLADE["guard"], width=5)
    d.ellipse([*P(-27, -1), *P(-21, 5)], fill=BLADE["guard"])

    # Blade: straight spine, deep belly, and a tip cut away on the edge side
    # the way a chopper's is - a square end reads as a pipe, not a blade.
    outer = [P(6, -6), P(length * 0.72, -6), P(length * 0.95, 2),
             P(length, 14), P(length * 0.78, 21), P(6, 19)]
    d.polygon(outer, fill=BLADE["edge"])
    inner = [P(9, -4), P(length * 0.71, -4), P(length * 0.93, 3),
             P(length - 4, 13), P(length * 0.77, 18), P(9, 16)]
    d.polygon(inner, fill=BLADE["steel"])
    d.polygon([P(10, 10), P(length * 0.80, 11), P(length * 0.77, 18), P(10, 16)],
              fill=BLADE["steel_mid"])          # shadow side of the belly
    d.line([P(9, -4), P(length * 0.71, -4)], fill=BLADE["spine"], width=4)
    d.line([P(10, 16), P(length * 0.77, 18)], fill=BLADE["steel_hi"], width=3)


def draw_hatchet(d, grip, length=104.0, angle=-1.02):
    """Short haft with a wedge head, held up the way Hatchet Man holds it."""
    gx, gy = grip
    dx, dy = math.cos(angle), math.sin(angle)
    nx, ny = -dy, dx

    def P(t, u):
        return (gx + dx * t + nx * u, gy + dy * t + ny * u)

    d.line([P(-length * 0.34, 0), P(length * 0.62, 0)], fill=BLADE["spine"], width=12)
    d.line([P(-length * 0.32, 0), P(length * 0.60, 0)], fill=STAFF["wood"], width=7)
    d.line([P(-length * 0.30, -2), P(length * 0.58, -2)], fill=STAFF["wood_hi"], width=2)
    for t in (-length * 0.06, 0.02 * length, length * 0.10):
        d.line([P(t, -4), P(t, 4)], fill=LEATHER["mid"], width=2)

    # Axe head: narrow where it meets the haft, flaring out to a curved bit.
    head = [P(length * 0.56, -13), P(length * 0.62, 11), P(length * 0.82, 22),
            P(length * 1.00, 20), P(length * 1.04, 2), P(length * 0.92, -13),
            P(length * 0.74, -16)]
    d.polygon(head, fill=BLADE["edge"])
    inner = [P(length * 0.60, -10), P(length * 0.65, 9), P(length * 0.83, 18),
             P(length * 0.97, 17), P(length * 1.00, 2), P(length * 0.89, -10),
             P(length * 0.74, -13)]
    d.polygon(inner, fill=BLADE["steel"])
    d.polygon([P(length * 0.66, 2), P(length * 0.86, 12), P(length * 0.96, 15),
               P(length * 0.97, 6)], fill=BLADE["steel_mid"])
    # bright bit along the cutting curve, dark poll behind it
    d.line([P(length * 0.80, 20), P(length * 0.98, 18), P(length * 1.02, 3)],
           fill=BLADE["steel_hi"], width=3)
    d.line([P(length * 0.58, -12), P(length * 0.72, -15)], fill=BLADE["spine"], width=4)


def draw_pistol(d, grip, angle=-0.04, big=1.0):
    """A gold automatic, barrel forward, seen side on."""
    gx, gy = grip
    dx, dy = math.cos(angle), math.sin(angle)
    nx, ny = -dy, dx

    def P(t, u):
        return (gx + dx * t + nx * u, gy + dy * t + ny * u)

    s = big
    # grip running down-back out of the fist
    d.line([P(-8 * s, 4 * s), P(6 * s, 16 * s)], fill=BLADE["spine"], width=int(11 * s))
    d.line([P(-7 * s, 5 * s), P(5 * s, 15 * s)], fill=LEATHER["dark"],
           width=int(7 * s))
    # slide and frame
    d.polygon([P(-6 * s, -7 * s), P(30 * s, -7 * s), P(32 * s, 1 * s),
               P(6 * s, 3 * s), P(-6 * s, 2 * s)], fill=GOLD["mid"])
    d.line([P(-5 * s, -6 * s), P(29 * s, -6 * s)], fill=GOLD["lit"], width=int(3 * s))
    d.line([P(6 * s, 2 * s), P(32 * s, 0)], fill=GOLD["dark"], width=int(2 * s))
    # muzzle, hammer, trigger guard
    d.line([P(30 * s, -7 * s), P(33 * s, -6 * s)], fill=GOLD["dark"], width=int(4 * s))
    d.line([P(-6 * s, -6 * s), P(-9 * s, -2 * s)], fill=GOLD["dark"], width=int(3 * s))
    d.arc([*P(6 * s, 3 * s), *P(18 * s, 14 * s)], 300, 180, fill=GOLD["dark"],
          width=max(2, int(2 * s)))


def paint_weapons(img, m):
    """Draw what the member carries out of his fist (or fists)."""
    skin_rgb = {_warm(SKIN[r], m["skin"]) for r in SKIN}
    fists = hands(img, skin_rgb, limit=2 if m["weapon"] == "pistols" else 1)
    if not fists:
        return img
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    kind, length = m["weapon"], m["length"]
    if kind == "staff":
        draw_staff(d, fists[0], length)
    elif kind == "machete":
        draw_machete(d, fists[0], length)
    elif kind == "hatchet":
        draw_hatchet(d, fists[0], length)
    elif kind == "pistols":
        for i, grip in enumerate(fists):
            draw_pistol(d, (grip[0], grip[1] - 2), -0.04 if i == 0 else 0.12)
    return Image.alpha_composite(img, layer)


# ------------------------------------------------------------------- identity
def paint_identity(img, m):
    """Long hair, moustache, beard and the bandolier of brass bullets."""
    head = head_anchor(img)
    hair_d, hair_h = HAIR[m["hair"]]
    if head:
        cx, cy, hw = head
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        if m["id"] == "wingkong_hatchet":
            # long hair falling down the back, behind the shoulders
            d.polygon([(cx + hw * 0.50, cy - hw * 0.30),
                       (cx - hw * 0.25, cy - hw * 0.95),
                       (cx - hw * 0.95, cy - hw * 0.15),
                       (cx - hw * 0.88, cy + hw * 1.20),
                       (cx - hw * 0.55, cy + hw * 1.00),
                       (cx - hw * 0.38, cy + hw * 0.25),
                       (cx + hw * 0.05, cy + hw * 0.10)],
                      fill=hair_d + (255,))
            d.line([(cx - hw * 0.55, cy - hw * 0.45),
                    (cx - hw * 0.62, cy + hw * 0.95)], fill=hair_h + (200,), width=3)
        if m["face"] in ("moustache", "full"):
            d.polygon([(cx + hw * 0.10, cy + hw * 0.16),
                       (cx + hw * 0.66, cy + hw * 0.26),
                       (cx + hw * 0.52, cy + hw * 0.70),
                       (cx + hw * 0.18, cy + hw * 0.42)],
                      fill=hair_d + (255,))
        if m["face"] in ("beard", "full"):
            d.polygon([(cx - hw * 0.16, cy + hw * 0.52),
                       (cx + hw * 0.60, cy + hw * 0.48),
                       (cx + hw * 0.40, cy + hw * 1.12),
                       (cx + hw * 0.02, cy + hw * 1.02)],
                      fill=hair_d + (255,))
        img = Image.alpha_composite(img, layer)

    if m["gear"] == "bandolier":
        band = torso_band(img)
        if band:
            x0, y0, x1, y1 = band
            layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            for flip in (False, True):
                ax = x1 - 8 if flip else x0 + 8
                bx = x0 + 8 if flip else x1 - 8
                d.line([(ax, y0), (bx, y1)], fill=LEATHER["dark"] + (255,), width=10)
                d.line([(ax, y0), (bx, y1)], fill=LEATHER["mid"] + (255,), width=7)
                n = max(5, int(abs(bx - ax) / 11))
                for i in range(n):
                    t = (i + 0.5) / n
                    cx, cy = ax + (bx - ax) * t, y0 + (y1 - y0) * t
                    d.rectangle([cx - 3, cy - 5, cx + 3, cy + 5],
                                fill=BRASS["mid"], outline=BRASS["dark"])
                    d.rectangle([cx - 2, cy - 4, cx + 2, cy - 1],
                                fill=BRASS["lit"])
            # buckle at the belt line
            d.rectangle([(x0 + x1) / 2 - 7, y1 - 4, (x0 + x1) / 2 + 7, y1 + 8],
                        fill=BRASS["mid"], outline=BRASS["dark"])
            # keep it on the body: clip to the silhouette
            layer.putalpha(ImageChops.multiply(layer.getchannel("A"), _opaque(img)))
            img = Image.alpha_composite(img, layer)
    return img


def member_sprite(cid, group=0, number=0, weapon=True):
    m = member(cid)
    raw, sprites, pal = sff.read_sff(os.path.join(BASE, "kfm.sff"))
    sp = next(s for s in sprites if s["group"] == group and s["number"] == number)
    img = sff.decode_sprite(raw, sp, pal, 0)
    img = upscale(recolour(img, colour_map(m["gang"], m["cloth"], m["skin"],
                                           m["band"], m["hair"])))
    img = ImageOps.expand(img, (PAD_X, PAD_Y, PAD_X, PAD_Y), fill=(0, 0, 0, 0))
    img = paint_identity(img, m)
    if weapon:
        img = paint_weapons(img, m)
    return img


# ----------------------------------------------------------------------- build
def prop_colours():
    out = []
    for group in (STAFF, BLADE, GOLD, LEATHER):
        out.extend(group.values())
    return out


def member_palette(m):
    """One 256-colour palette for a member: index 0 transparent, then his art."""
    colours = []
    for rgb in list(colour_map(m["gang"], m["cloth"], m["skin"], m["band"],
                               m["hair"]).values()) + prop_colours():
        rgb = tuple(rgb[:3])
        if rgb not in colours:
            colours.append(rgb)
    flat = [255, 0, 255]                    # index 0: the SFF's transparent entry
    for rgb in colours[:255]:
        flat.extend(rgb)
    flat += [0] * (768 - len(flat))

    pal_bytes = bytearray()
    for i in range(256):
        r, g, b = flat[i * 3:i * 3 + 3]
        pal_bytes += bytes((r, g, b, 0 if i == 0 else 255))
    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette(flat)
    return bytes(pal_bytes), pal_img


def scale_air(text, k):
    """Scale every frame offset and collision box in an AIR file."""
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.lower().startswith("clsn") and "=" in line:
            head, vals = line.split("=", 1)
            nums = re.findall(r"-?\d+", vals)
            if len(nums) == 4:
                out.append(head.strip() + " = " + ", ".join(
                    str(int(round(int(n) * k))) for n in nums))
                continue
        m = re.match(r"^(\d+)\s*,\s*(\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)$",
                     line)
        if m:
            g, n, x, y, t = (int(m.group(i)) for i in range(1, 6))
            out.append(f"{g},{n}, {int(round(x * k))},{int(round(y * k))}, {t}")
            continue
        out.append(raw.rstrip())
    return "\n".join(out) + "\n"


def build(cid):
    """Bake one gang member: recoloured, upscaled, dressed Kung Fu Man art."""
    m = member(cid)
    raw, sprites, pal = sff.read_sff(os.path.join(BASE, "kfm.sff"))
    cmap = colour_map(m["gang"], m["cloth"], m["skin"], m["band"], m["hair"])
    pal_bytes, pal_img = member_palette(m)

    out = []
    for sp in sprites:
        if sp["group"] >= 9000:
            continue          # portraits are rendered fresh by build_portraits
        img = sff.decode_sprite(raw, sp, pal, 0)
        img = upscale(recolour(img, cmap))
        img = ImageOps.expand(img, (PAD_X, PAD_Y, PAD_X, PAD_Y), fill=(0, 0, 0, 0))
        img = paint_identity(img, m)
        img = paint_weapons(img, m)

        # 8-bit on the member's own palette: same art, a tenth of the bytes.
        indexed = img.convert("RGB").quantize(palette=pal_img,
                                              dither=Image.Dither.NONE)
        flat_p = Image.new("P", img.size, 0)
        flat_p.putpalette(indexed.getpalette())
        flat_p.paste(indexed, (0, 0),
                     img.split()[3].point(lambda a: 255 if a > 0 else 0))

        ax, ay = sp["axis"]
        out.append({"group": sp["group"], "number": sp["number"],
                    "image": flat_p,
                    "axis": (round(ax * SCALE) + PAD_X, round(ay * SCALE) + PAD_Y)})

    d = os.path.join(ROOT, "chars", cid + "_rig")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, cid + ".sff"), "wb") as f:
        f.write(sff.write_sff(out, [pal_bytes]))

    air_src = open(os.path.join(BASE, "kfm.air"), encoding="utf-8-sig").read()
    with open(os.path.join(d, cid + ".air"), "w", encoding="utf-8") as f:
        f.write(scale_air(air_src, SCALE))

    def_path = os.path.join(d, cid + ".def")
    if os.path.isfile(def_path):
        with open(def_path, encoding="utf-8") as f:
            text = f.read().replace(' (rig)"', '"')
        with open(def_path, "w", encoding="utf-8") as f:
            f.write(text)
    print(f"{cid}: {len(out)} sprites -> chars/{cid}_rig")


def sheet(path="artifacts/kfm_gang_proto.png"):
    from PIL import ImageFont

    def font(size):
        try:
            return ImageFont.load_default(size=size)
        except Exception:
            return ImageFont.load_default()

    cw, ch = 300, 430
    rows = 2
    img_sheet = Image.new("RGB", (cw * 6, ch * rows), (24, 26, 33))
    d = ImageDraw.Draw(img_sheet)
    for i, m in enumerate(MEMBERS):
        img = member_sprite(m["id"])
        col, row = i % 6, i // 6
        x = col * cw + cw // 2 - img.width // 2
        y = row * ch + ch - 20 - img.height
        img_sheet.paste(img, (x, y), img)
        d.text((col * cw + 10, row * ch + 10), m["id"].split("_")[1].title(),
               font=font(15), fill=(226, 228, 238))
        d.line([(col * cw, row * ch), (col * cw, row * ch + ch)], fill=(44, 48, 58))
    img_sheet.save(path)
    print("wrote", path, img_sheet.size)


if __name__ == "__main__":
    if "--sheet" in sys.argv:
        sheet()
    elif "--build" in sys.argv:
        i = sys.argv.index("--build")
        ids = (sys.argv[i + 1].split(",") if len(sys.argv) > i + 1
               else [m["id"] for m in MEMBERS])
        for cid in ids:
            build(cid)
    else:
        print("usage: python3 tools/gang_kfm.py [--sheet | --build [id,id,...]]")
