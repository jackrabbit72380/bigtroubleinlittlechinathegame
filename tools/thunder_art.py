"""Thunder: the third Storm, painted in code like his brothers.

He wears the same broad straw hat and floor-length cloak as Lightning and Rain,
because that is the Storm uniform. Everything under it is his own, and it is
built to read as the big one of the three: a wide quilted ochre robe studded
with iron bosses, dark leather pauldrons over both shoulders, a deep red cloak
with the lining turned out, and a **crescent blade in each fist** - two curved
blades, not Rain's rakes and not Lightning's empty hands.

The blades are the reason this painter exists. Thunder's weapon is not a staff,
a rake or a lightning bolt: it is a pair of crescent knives, held one in each
hand in the crossed guard the statue shows.

Output is exactly what ``char_rig`` expects:

    art_src/chars/thunder/parts/*.png
    art_src/chars/thunder/parts/rig.json

Run:  python3 tools/thunder_art.py
"""

from __future__ import annotations

import json
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import char_rig
import hat_cut

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "art_src", "chars", "thunder", "parts")

# --------------------------------------------------------------------- palette
# Quilted ochre robe: the warm brown-gold of the film costume, a full step
# lighter than the leather so the studs and the straps still separate.
ROBE = (146, 108, 66)
ROBE_LIT = (194, 152, 102)
ROBE_DK = (94, 66, 38)
ROBE_TRIM = (70, 48, 30)
STUD = (52, 46, 42)
STUD_LIT = (132, 126, 118)

# Iron-studded leather over both shoulders. Darker and cooler than the robe:
# at the robe's own value the pauldrons vanished into the chest.
PAULD = (76, 48, 46)
PAULD_LIT = (116, 78, 70)
PAULD_DK = (40, 24, 24)

# The cloak is oxblood, the same wool the other two Storms wear, with the
# lining a shade deeper so the turned-out edge reads at sprite size.
CAPE = (104, 30, 36)
CAPE_LIT = (150, 50, 56)
CAPE_DK = (54, 13, 17)
CAPE_LINING = (62, 18, 22)
CAPE_LINING_LIT = (98, 34, 38)

SASH = (86, 26, 30)
SASH_LIT = (124, 46, 48)
SASH_DK = (46, 12, 14)

SKIN = (206, 158, 118)
SKIN_LIT = (234, 192, 154)
SKIN_DK = (146, 102, 72)
SKIN_DEEP = (86, 56, 40)

TROUSER = (78, 66, 58)
TROUSER_LIT = (106, 92, 82)
TROUSER_DK = (46, 38, 32)

BOOT = (34, 30, 28)
BOOT_LIT = (64, 58, 54)
BOOT_DK = (15, 13, 12)

# Blades: pale steel against the dark robe. They are the brightest thing on
# the figure after the hat, which is what makes them read as weapons.
STEEL = (150, 160, 176)
STEEL_LIT = (218, 228, 242)
STEEL_DK = (64, 72, 84)

STRAW = (206, 184, 140)


def _blank(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _shape(size, pts):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    return mask


def _limb(size, pts, base, lit, dark):
    return char_rig._shade(_shape(size, pts), base, lit, dark)


# ---------------------------------------------------------------- crescent blade
def _crescent_mask(size=140, outer=52, inner=36, off=17):
    """A lune: the big disc with a smaller one bitten out of it.

    Where the two circles cross is the pair of horns, and those are the grip in
    the fist and the point of the blade. Drawing it as a polygon of sampled
    arcs left visible faceting at sprite size; the boolean edge is clean.
    """
    m = Image.new("L", (size, size), 0)
    cx = cy = size // 2
    ImageDraw.Draw(m).ellipse([cx - outer, cy - outer, cx + outer, cy + outer],
                              fill=255)
    bite = Image.new("L", (size, size), 0)
    ImageDraw.Draw(bite).ellipse([cx - inner + off, cy - inner,
                                  cx + inner + off, cy + inner], fill=255)
    return ImageChops.subtract(m, bite)


def _horn_offset(outer=52, inner=36, off=17):
    """Vector from the crescent's centre to its upper horn (grip end)."""
    d = float(off)
    a = (d * d + outer * outer - inner * inner) / (2 * d)
    h = math.sqrt(max(1.0, outer * outer - a * a))
    return a, -h


def _crescent(img, hx, hy, tilt=-58.0, scale=1.0, tassel=True):
    """Draw one crescent blade into ``img``, grip horn sitting on the fist."""
    outer, inner, off = 52 * scale, 36 * scale, 17 * scale
    size = int(math.ceil(outer * 2.4))
    mask = _crescent_mask(size, outer, inner, off)
    blade = char_rig._shade(mask, STEEL, STEEL_LIT, STEEL_DK)

    # A darker spine down the back of the blade, so the crescent is not one
    # flat sheet of pale metal at sprite size.
    d = ImageDraw.Draw(blade)
    cx = cy = size // 2
    d.arc([cx - outer + 5, cy - outer + 5, cx + outer - 5, cy + outer - 5],
          120, 250, fill=STEEL_DK + (170,), width=max(2, int(3 * scale)))
    d.arc([cx - outer + 9, cy - outer + 9, cx + outer - 9, cy + outer - 9],
          140, 230, fill=STEEL_LIT + (150,), width=max(1, int(2 * scale)))

    rotated = blade.rotate(tilt, resample=Image.BICUBIC, center=(cx, cy))

    # Where the grip horn ends up after the rotation, so the blade hangs off
    # the fist instead of floating near it.
    hx_local, hy_local = _horn_offset(outer, inner, off)
    a = math.radians(tilt)
    rx = hx_local * math.cos(a) - hy_local * math.sin(a)
    ry = hx_local * math.sin(a) + hy_local * math.cos(a)
    img.alpha_composite(rotated, (int(round(hx - cx - rx)),
                                  int(round(hy - cy - ry))))

    d = ImageDraw.Draw(img)
    # guard and a wrapped grip across the horn, so the fist holds something
    gx, gy = hx, hy
    d.line([(gx - 11 * scale, gy + 3 * scale), (gx + 9 * scale, gy - 5 * scale)],
           fill=STEEL_DK + (255,), width=max(3, int(5 * scale)))
    d.line([(gx - 9 * scale, gy + 2 * scale), (gx + 7 * scale, gy - 4 * scale)],
           fill=STEEL_LIT + (190,), width=max(1, int(2 * scale)))
    if tassel:
        d.line([(gx + 6 * scale, gy - 2 * scale), (gx + 11 * scale, gy + 9 * scale)],
               fill=(150, 30, 34, 235), width=max(1, int(2 * scale)))
        d.point([(gx + 11 * scale, gy + 10 * scale)], fill=(186, 52, 52, 235))
    return img


# ----------------------------------------------------------------------- torso
def torso():
    """Wide quilted ochre robe, iron-studded, with leather pauldrons."""
    W, H = 132, 130
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    # broader through the chest than Rain's, and squarer at the waist: he is
    # the heavyweight of the three and the silhouette has to say so
    d.polygon([(16, 18), (116, 18), (110, 66), (104, 108), (102, 130),
               (30, 130), (28, 108), (22, 66)], fill=255)
    d.ellipse([6, 0, 66, 60], fill=255)
    d.ellipse([66, 0, 126, 60], fill=255)
    img = char_rig._shade(mask, ROBE, ROBE_LIT, ROBE_DK)
    d = ImageDraw.Draw(img)

    # --- quilted rows: shallow diamonds, not a grid of lines -----------------
    quilt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    qd = ImageDraw.Draw(quilt)
    for row in range(6):
        y = 30 + row * 15
        for col in range(5):
            x = 24 + col * 21 + (10 if row % 2 else 0)
            qd.line([(x - 9, y), (x, y - 5)], fill=ROBE_DK + (110,), width=2)
            qd.line([(x, y - 5), (x + 9, y)], fill=ROBE_LIT + (80,), width=2)
            qd.line([(x - 9, y), (x, y + 5)], fill=ROBE_LIT + (60,), width=2)
            qd.line([(x, y + 5), (x + 9, y)], fill=ROBE_DK + (95,), width=2)
    quilt.putalpha(ImageChops.multiply(quilt.split()[3], mask))
    img.alpha_composite(quilt)

    # --- studs down the chest, the ones that read at sprite size --------------
    for row in range(4):
        y = 34 + row * 22
        xs = (34, 66, 98) if row % 2 == 0 else (50, 82)
        for x in xs:
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=STUD + (255,))
            d.point([(x - 1, y - 1)], fill=STUD_LIT + (220,))

    # --- leather chest strap -------------------------------------------------
    d.polygon([(24, 26), (40, 22), (110, 96), (108, 108), (96, 110), (20, 40)],
              fill=PAULD_DK + (255,))
    d.line([(28, 28), (104, 100)], fill=PAULD_LIT + (150,), width=2)

    # --- pauldrons -----------------------------------------------------------
    for sx in (0, 1):
        cx = 34 if sx == 0 else 98
        plate = Image.new("L", (W, H), 0)
        pd = ImageDraw.Draw(plate)
        pd.chord([cx - 34, 0, cx + 34, 58], 0, 180, fill=255)
        pd.rectangle([cx - 34, 26, cx + 34, 44], fill=255)
        img.alpha_composite(char_rig._shade(plate, PAULD, PAULD_LIT, PAULD_DK))
        d.line([(cx - 30, 12), (cx + 30, 12)], fill=PAULD_LIT + (120,), width=2)
        for k in range(3):
            bx = cx - 20 + k * 20
            d.ellipse([bx - 2, 20, bx + 2, 24], fill=STUD_LIT + (230,))

    # --- collar: a high dark band, open at the throat ------------------------
    d.polygon([(52, 18), (66, 38), (80, 18), (74, 14), (66, 27), (58, 14)],
              fill=PAULD_DK + (255,))

    # --- sash and belt -------------------------------------------------------
    d.polygon([(28, 96), (66, 108), (104, 96), (104, 110), (66, 122), (28, 110)],
              fill=SASH + (255,))
    d.line([(28, 96), (66, 108), (104, 96)], fill=SASH_LIT + (235,), width=3)
    d.line([(29, 109), (66, 121), (103, 109)], fill=SASH_DK + (235,), width=3)
    d.rectangle([27, 110, 105, 122], fill=(30, 22, 20, 255))
    d.ellipse([56, 106, 76, 126], fill=STEEL + (255,))
    d.ellipse([61, 111, 71, 121], fill=STEEL_DK + (255,))

    for x, y1 in ((36, 108), (52, 96), (80, 96), (96, 108)):
        d.line([(x, 54), (x + (2 if x < 66 else -2), y1)],
               fill=ROBE_DK + (140,), width=2)
    return img.resize((114, H), Image.LANCZOS)


# ---------------------------------------------------------------------- pelvis
def pelvis():
    """The robe's skirt, flaring from the sash, studded at the hem."""
    W, H = 100, 76
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(28, 6), (72, 6), (92, 58), (74, 74), (26, 74), (8, 58)], fill=255)
    d.ellipse([8, 48, 92, 78], fill=255)
    img = char_rig._shade(mask, ROBE, ROBE_LIT, ROBE_DK)
    d = ImageDraw.Draw(img)
    d.rectangle([26, 4, 74, 16], fill=(30, 22, 20, 255))
    d.rectangle([28, 6, 72, 12], fill=SASH + (240,))
    for x in (28, 42, 58, 72):
        d.line([(x, 20), (x + (3 if x < 50 else -3), 68)],
               fill=ROBE_DK + (135,), width=2)
    # hem band and its studs
    d.line([(12, 58), (88, 58)], fill=ROBE_TRIM + (255,), width=3)
    for x in range(16, 88, 12):
        d.ellipse([x - 2, 62, x + 2, 66], fill=STUD + (255,))
    return img.resize((78, H), Image.LANCZOS)


# ------------------------------------------------------------------------ head
def head():
    """The same straw hat as his brothers, wider, and a heavy brow under it."""
    W, H = 176, 104
    cx = W // 2
    img = _blank((W, H))

    neck = Image.new("L", (W, H), 0)
    ImageDraw.Draw(neck).rectangle([cx - 15, 74, cx + 15, H], fill=255)
    img.alpha_composite(char_rig._shade(neck, SKIN_DK, SKIN, SKIN_DEEP))

    face = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(face)
    fd.ellipse([cx - 33, 28, cx + 33, 96], fill=255)
    fd.rectangle([cx - 21, 58, cx + 21, 96], fill=255)
    img.alpha_composite(char_rig._shade(face, SKIN, SKIN_LIT, SKIN_DK))
    d = ImageDraw.Draw(img)

    # jaw and cheek shadow: the same shade the brim lays on all three of them
    shade_layer = _blank((W, H))
    sd = ImageDraw.Draw(shade_layer)
    sd.ellipse([cx - 48, 14, cx + 48, 100], fill=(8, 9, 12, 255))
    sd.rectangle([cx - 48, 42, cx + 48, 100], fill=(8, 9, 12, 255))
    img.alpha_composite(shade_layer.filter(ImageFilter.GaussianBlur(2.4)))

    # brow, eyes and the set of the mouth: he is the one who scowls
    d.line([(cx - 22, 58), (cx - 6, 60)], fill=(40, 26, 20, 235), width=3)
    d.line([(cx + 6, 60), (cx + 22, 58)], fill=(40, 26, 20, 235), width=3)
    d.line([(cx - 15, 64), (cx - 5, 64)], fill=(24, 20, 20, 245), width=3)
    d.line([(cx + 5, 64), (cx + 15, 64)], fill=(24, 20, 20, 245), width=3)
    d.line([(cx - 9, 82), (cx + 9, 82)], fill=(70, 34, 30, 235), width=3)
    d.line([(cx - 12, 88), (cx + 12, 88)], fill=(48, 24, 22, 180), width=2)

    hat_img = hat_cut.hat(168, 88)
    img.alpha_composite(hat_img, (cx - hat_img.width // 2, 78 - hat_img.height))
    return img


# ------------------------------------------------------------------------- arm
def arm(near=True):
    """One bent arm in ochre cloth with a crescent blade gripped in the fist."""
    W, H = 210, 268
    img = _blank((W, H))
    base, lit, dark = (ROBE, ROBE_LIT, ROBE_DK) if near else (
        (118, 86, 52), (154, 118, 78), (80, 56, 32))
    skin = (SKIN, SKIN_LIT, SKIN_DK) if near else (SKIN_DK, SKIN, SKIN_DEEP)

    sh = (54.0, 116.0)
    elbow = (58.0, 162.0) if near else (60.0, 166.0)
    wrist = (82.0, 186.0) if near else (80.0, 190.0)

    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    # a thick upper arm: the sleeve is quilted armour, not a shirt
    d.polygon([(34, 112), (72, 112), (72, 156), (70, 166), (44, 168), (34, 128)], fill=255)
    d.ellipse([sh[0] - 21, sh[1] - 12, sh[0] + 21, sh[1] + 17], fill=255)
    d.ellipse([elbow[0] - 14, elbow[1] - 11, elbow[0] + 14, elbow[1] + 11],
              fill=255)
    img.alpha_composite(char_rig._shade(mask, base, lit, dark))

    fmask = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(fmask)
    fd.line([elbow, wrist], fill=255, width=20)
    fd.ellipse([elbow[0] - 10, elbow[1] - 10, elbow[0] + 10, elbow[1] + 10],
               fill=255)
    fd.ellipse([wrist[0] - 10, wrist[1] - 10, wrist[0] + 10, wrist[1] + 10],
               fill=255)
    img.alpha_composite(char_rig._shade(fmask, base, lit, dark))

    d = ImageDraw.Draw(img)
    # bracer: a steel cuff, so the forearm reads as armoured
    d.line([(wrist[0] - 5, wrist[1] - 3), (wrist[0] + 5, wrist[1] + 3)],
           fill=STEEL_DK + (255,), width=24)
    d.line([(wrist[0] - 3, wrist[1] - 2), (wrist[0] + 4, wrist[1] + 3)],
           fill=STEEL + (230,), width=16)
    d.line([(sh[0] - 8, sh[1] - 6), (sh[0] + 2, sh[1] + 8)],
           fill=dark + (120,), width=3)

    # fist
    hx, hy = (94, 192) if near else (92, 196)
    d.ellipse([hx - 12, hy - 11, hx + 12, hy + 11], fill=skin[0] + (255,))
    d.ellipse([hx - 9, hy - 9, hx + 6, hy + 3], fill=skin[1] + (205,))
    for i in range(3):
        d.line([(hx + 2, hy - 6 + i * 5), (hx + 12, hy - 5 + i * 5)],
               fill=skin[2] + (160,), width=2)

    # the blade, held up and turned in toward the centre line. At 0.94 of the
    # drawn size the crescents were as wide as his chest and swallowed the
    # robe; these are daggers, so they stay inside the shoulders.
    _crescent(img, hx + 2, hy - 2, tilt=-74.0 if near else -80.0,
              scale=0.70 if near else 0.66)

    if not near:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img


# ------------------------------------------------------------------------ legs
def thigh():
    W, H = 58, 86
    return _limb((W, H), [(9, 2), (48, 2), (50, 46), (44, 84), (12, 84), (6, 46)],
                 TROUSER, TROUSER_LIT, TROUSER_DK)


def shin():
    W, H = 48, 77
    leg = _limb((W, H), [(9, 2), (39, 2), (41, 34), (37, 75), (11, 75), (7, 34)],
                TROUSER, TROUSER_LIT, TROUSER_DK)
    bootmask = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(bootmask)
    bd.polygon([(7, 28), (41, 28), (37, 75), (11, 75)], fill=255)
    boot = char_rig._shade(bootmask, BOOT, BOOT_LIT, BOOT_DK)
    img = Image.alpha_composite(leg, boot)
    d = ImageDraw.Draw(img)
    d.line([(5, 28), (43, 28)], fill=(120, 112, 104, 190), width=2)
    d.line([(12, 20), (12, 27)], fill=ROBE_DK + (200,), width=2)
    d.line([(36, 20), (36, 27)], fill=ROBE_DK + (200,), width=2)
    return img


def foot():
    """Heavy boot, toe to the right; pivot at the heel."""
    W, H = 54, 38
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(6, 7), (32, 4), (52, 18), (51, 35), (8, 36)], fill=255)
    d.ellipse([2, 5, 24, 36], fill=255)
    img = char_rig._shade(mask, BOOT, BOOT_LIT, BOOT_DK)
    d = ImageDraw.Draw(img)
    d.line([(7, 34), (50, 33)], fill=(126, 118, 110, 205), width=2)
    d.line([(10, 11), (30, 8)], fill=BOOT_LIT + (120,), width=2)
    return img


# ------------------------------------------------------------------------ cape
def cape():
    """The Storm cloak, heavier than Rain's, hem torn by the stairs of the hall."""
    W, H = 196, 246
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(62, 6), (134, 6), (178, 154), (192, 218), (164, 202),
               (140, 232), (112, 208), (90, 234), (62, 208), (36, 232),
               (12, 204), (4, 152), (24, 116)], fill=255)
    # high collar, turned up behind the hat
    d.ellipse([54, -6, 142, 34], fill=255)
    img = char_rig._shade(mask, CAPE, CAPE_LIT, CAPE_DK)
    d = ImageDraw.Draw(img)

    lining = Image.new("L", (W, H), 0)
    ld = ImageDraw.Draw(lining)
    ld.polygon([(60, 10), (92, 10), (86, 130), (66, 200), (28, 212),
                (12, 174), (34, 104)], fill=255)
    ld.polygon([(130, 12), (146, 12), (156, 152), (144, 200), (128, 154)],
               fill=255)
    img.alpha_composite(char_rig._shade(lining, CAPE_LINING,
                                        CAPE_LINING_LIT, CAPE_DK))

    for x0, x1 in ((28, 12), (50, 38), (72, 62), (98, 106), (122, 152),
                   (146, 176)):
        d.line([(x0, 34), (x1, 214)], fill=CAPE_DK + (125,), width=3)
    for x0, x1 in ((42, 34), (86, 94), (108, 124)):
        d.line([(x0, 44), (x1, 164)], fill=CAPE_LIT + (70,), width=3)

    # collar band and the clasp
    d.line([(58, 12), (134, 12)], fill=(132, 130, 132, 255), width=7)
    d.ellipse([87, 5, 105, 23], fill=STEEL + (255,))
    d.ellipse([92, 10, 100, 18], fill=STEEL_DK + (255,))
    return img


# ------------------------------------------------------------------------ main
RIG_JSON = {
    "pivots": {
        "pelvis": [39, 16],
        # the arm parts are taller than Rain's - the blade needs the room - so
        # the shoulder sits lower and the pivot follows it
        "arm_n": [54, 116],
        "arm_f": [155, 116],
        "foot_n": [14, 26],
        "foot_f": [14, 26],
        "cape": [98, 12],
    },
}


def main():
    os.makedirs(PARTS, exist_ok=True)
    parts = {
        "cape": cape(),
        "torso": torso(),
        "pelvis": pelvis(),
        "head": head(),
        "arm_n": arm(near=True),
        "arm_f": arm(near=False),
        "thigh_n": thigh(),
        "thigh_f": thigh(),
        "shin_n": shin(),
        "shin_f": shin(),
        "foot_n": foot(),
        "foot_f": foot(),
    }
    for name, img in parts.items():
        img.save(os.path.join(PARTS, f"{name}.png"))
    with open(os.path.join(PARTS, "rig.json"), "w", encoding="utf-8") as f:
        json.dump(RIG_JSON, f, indent=2)
        f.write("\n")
    print(f"wrote {len(parts)} parts -> art_src/chars/thunder/parts/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
