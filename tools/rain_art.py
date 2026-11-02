"""Rain: the third Storm, painted in code like his brother Lightning.

Lightning has no turnaround to cut, so ``lightning_art.py`` draws his parts.
Rain is built the same way and shares the two pieces that make a Storm read as
a Storm: the wide low straw hat, taken from the same HD render through
``hat_cut.hat()`` so both men wear the identical prop, and the floor-length
cloak with its lining turned out. Everything under them is Rain's own: pale
grey cloth instead of black, a slate sash, and a steel claw rake gripped in
each fist - the two-pronged rakes from the concept sketch, shafts nearly as
tall as he is, four hooked prongs at the head.

Output is exactly what ``char_rig`` expects:

    art_src/chars/rain/parts/*.png
    art_src/chars/rain/parts/rig.json

Run:  python3 tools/rain_art.py
"""

from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import char_rig
import hat_cut

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "art_src", "chars", "rain", "parts")

# --------------------------------------------------------------------- palette
# Pale grey cloth, a shade lighter than the concept's sketch so the figure
# separates from the dark halls he fights in; slate trim and sash.
CLOTH = (186, 190, 198)
CLOTH_LIT = (218, 222, 228)
CLOTH_DK = (132, 136, 146)
CLOTH_TRIM = (96, 102, 114)

SASH = (58, 96, 108)
SASH_LIT = (84, 132, 146)
SASH_DK = (30, 58, 68)

SKIN = (216, 172, 142)
SKIN_LIT = (238, 198, 170)
SKIN_DK = (156, 112, 84)
SKIN_DEEP = (98, 68, 52)

# The cloak is the same garment Lightning wears - charcoal wool, oxblood
# lining - because it is the Storm uniform; only the cloth under it changes.
CAPE = (34, 32, 34)
CAPE_LIT = (62, 58, 60)
CAPE_DK = (15, 13, 14)
CAPE_LINING = (58, 22, 34)
CAPE_LINING_LIT = (92, 34, 48)

# Trousers are a full step darker than the robe: at the same value the skirt
# and the legs fused into one white apron in the pose sheet.
TROUSER = (118, 124, 136)
TROUSER_LIT = (148, 154, 166)
TROUSER_DK = (78, 82, 94)

BOOT = (44, 46, 54)
BOOT_LIT = (74, 78, 90)
BOOT_DK = (20, 21, 26)

# The rake is dark steel on a dark shaft. Pale steel was the same tone as the
# grey cloth, so the weapon and the sleeve merged into one pale slab.
SHAFT = (52, 38, 26)
SHAFT_LIT = (92, 70, 46)
STEEL = (118, 132, 154)
STEEL_LIT = (198, 212, 232)
STEEL_DK = (52, 58, 70)

STRAW = (206, 184, 140)


def _blank(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _shape(size, pts):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    return mask


def _limb(size, pts, base, lit, dark):
    return char_rig._shade(_shape(size, pts), base, lit, dark)


# ---------------------------------------------------------------------- torso
def torso():
    """Grey robe over a slate panel, a teal sash, folds down the front."""
    W, H = 132, 130
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(24, 20), (108, 20), (102, 64), (96, 106), (94, 130),
               (38, 130), (36, 106), (30, 64)], fill=255)
    # shoulder caps, sized to the joints at +-48 like Lightning's
    d.ellipse([16, 4, 60, 58], fill=255)
    d.ellipse([72, 4, 116, 58], fill=255)
    img = char_rig._shade(mask, CLOTH, CLOTH_LIT, CLOTH_DK)
    d = ImageDraw.Draw(img)

    # --- slate chest panel, hanging to the sash -----------------------------
    panel = Image.new("L", (W, H), 0)
    pd = ImageDraw.Draw(panel)
    pd.polygon([(30, 24), (102, 24), (97, 88), (35, 88)], fill=255)
    img.alpha_composite(char_rig._shade(panel, (120, 126, 138),
                                        (156, 162, 174), (84, 88, 98)))
    # No pleats and no fold lines: at sprite size any regular vertical pattern
    # reads as a grille, which is exactly what it looked like. The panel is one
    # toned sheet with a lit left edge and a hemmed bottom instead.
    d.line([(32, 26), (32, 86)], fill=(100, 106, 118, 160), width=2)
    d.line([(100, 26), (100, 86)], fill=(72, 78, 90, 170), width=2)
    d.line([(35, 85), (97, 85)], fill=(66, 72, 84, 210), width=3)

    # --- collar: two plain lapels meeting at a V ---------------------------
    d.polygon([(52, 20), (66, 40), (80, 20), (74, 17), (66, 31), (58, 17)],
              fill=(70, 76, 86, 255))

    # --- teal sash and buckle ----------------------------------------------
    d.polygon([(34, 88), (66, 100), (98, 88), (98, 100), (66, 112), (34, 100)],
              fill=SASH + (255,))
    d.line([(34, 88), (66, 100), (98, 88)], fill=SASH_LIT + (235,), width=3)
    d.line([(35, 99), (66, 111), (97, 99)], fill=SASH_DK + (235,), width=3)
    d.rectangle([33, 108, 99, 120], fill=(28, 30, 36, 255))
    d.ellipse([57, 104, 75, 122], fill=STEEL + (255,))
    d.ellipse([61, 108, 71, 118], fill=STEEL_DK + (255,))
    # a single water bead hanging from the buckle
    d.polygon([(66, 118), (70, 126), (66, 130), (62, 126)],
              fill=(150, 214, 238, 245))

    # --- folds --------------------------------------------------------------
    for x, y1 in ((40, 112), (52, 100), (80, 100), (92, 112)):
        d.line([(x, 56), (x + (2 if x < 66 else -2), y1)],
               fill=CLOTH_DK + (140,), width=2)
    for x in (36, 96):
        d.line([(x, 34), (x - 1, 100)], fill=CLOTH_LIT + (90,), width=2)
    return img.resize((114, H), Image.LANCZOS)


# --------------------------------------------------------------------- pelvis
def pelvis():
    """The robe's skirt, flaring from the sash."""
    W, H = 100, 76
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    # Narrower than Lightning's skirt: 95px across it read as an apron over
    # the boots rather than a robe on a figure.
    d.polygon([(31, 6), (69, 6), (88, 60), (70, 74), (30, 74), (12, 60)], fill=255)
    d.ellipse([12, 50, 88, 78], fill=255)
    img = char_rig._shade(mask, CLOTH, CLOTH_LIT, CLOTH_DK)
    d = ImageDraw.Draw(img)
    d.rectangle([28, 4, 72, 16], fill=(28, 30, 36, 255))
    d.rectangle([30, 6, 70, 12], fill=SASH + (240,))
    for x in (30, 42, 56, 70):
        d.line([(x, 20), (x + (3 if x < 50 else -3), 70)],
               fill=CLOTH_DK + (135,), width=2)
    d.line([(16, 60), (26, 70)], fill=CLOTH_LIT + (80,), width=2)
    return img.resize((78, H), Image.LANCZOS)


# ----------------------------------------------------------------------- head
def head():
    """The same hat as Lightning, and the same brim shadow under it.

    The face is not modelled: the brim is wide enough that the whole head is in
    its shade, so what ships is the hat and the V of grey collar beneath it.
    """
    W, H = 158, 96
    cx = W // 2
    img = _blank((W, H))

    neck = Image.new("L", (W, H), 0)
    ImageDraw.Draw(neck).rectangle([cx - 13, 72, cx + 13, H], fill=255)
    img.alpha_composite(char_rig._shade(neck, SKIN_DK, SKIN, SKIN_DEEP))

    face = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(face)
    fd.ellipse([cx - 31, 32, cx + 31, 94], fill=255)
    fd.rectangle([cx - 19, 60, cx + 19, 94], fill=255)
    img.alpha_composite(char_rig._shade(face, (150, 110, 86),
                                        (196, 150, 118), SKIN_DEEP))

    shade_layer = _blank((W, H))
    sd = ImageDraw.Draw(shade_layer)
    sd.ellipse([cx - 44, 20, cx + 44, 98], fill=(8, 9, 12, 255))
    sd.rectangle([cx - 44, 40, cx + 44, 98], fill=(8, 9, 12, 255))
    img.alpha_composite(shade_layer.filter(ImageFilter.GaussianBlur(2.2)))

    hat_img = hat_cut.hat(140, 74)
    img.alpha_composite(hat_img, (cx - hat_img.width // 2, 72 - hat_img.height))
    return img


# ---------------------------------------------------------------------- weapon
def _rake(img, hx, hy, dx, dy):
    """Draw a claw rake into ``img``: shaft out of the fist, four hooked prongs.

    The fist is at (hx, hy) and the head of the rake at (hx + dx, hy + dy), so
    the caller can tilt it without redrawing the head.
    """
    d = ImageDraw.Draw(img)
    tx, ty = hx + dx, hy + dy

    # shaft
    d.line([(hx, hy), (tx, ty)], fill=SHAFT + (255,), width=7)
    d.line([(hx + 1, hy), (tx + 1, ty)], fill=SHAFT_LIT + (185,), width=3)
    # binding at the grip and the ferrule under the head
    d.line([(hx - 4, hy - 6), (hx + 4, hy + 6)], fill=(48, 36, 26, 235), width=4)
    d.line([(tx - 5, ty + 12), (tx + 5, ty + 10)], fill=STEEL_DK + (255,), width=8)

    # the head: a steel bar with four claws hooked up off it. The hooks turn
    # outward at the tip - straight prongs read as a garden fork, not a claw.
    d.line([(tx - 19, ty + 4), (tx + 19, ty + 4)], fill=STEEL_DK + (255,), width=9)
    d.line([(tx - 19, ty + 2), (tx + 19, ty + 2)], fill=STEEL + (255,), width=5)
    d.line([(tx - 17, ty + 0), (tx + 17, ty + 0)], fill=STEEL_LIT + (200,), width=2)
    for i in range(4):
        x0 = tx - 16 + i * 10.6
        bow = (i - 1.5) * 1.8
        d.line([(x0, ty + 1), (x0 + bow * 0.5, ty - 14), (x0 + bow, ty - 27)],
               fill=STEEL_DK + (255,), width=6, joint="curve")
        d.line([(x0, ty + 1), (x0 + bow * 0.5, ty - 14), (x0 + bow, ty - 27)],
               fill=STEEL + (255,), width=4, joint="curve")
        # the hook: a short arc turning away from the middle of the head
        sgn = 1 if i >= 2 else -1
        d.line([(x0 + bow, ty - 27), (x0 + bow + sgn * 6, ty - 33),
                (x0 + bow + sgn * 9, ty - 30)],
               fill=STEEL + (255,), width=3, joint="curve")
        d.point([(x0 + bow + sgn * 9, ty - 30)], fill=STEEL_LIT + (255,))
    return img


# ------------------------------------------------------------------------ arm
def arm(near=True):
    """One bent arm in grey cloth, fist closed round a claw rake.

    The canvas is taller than Lightning's because the rake stands above the
    hand: the shoulder sits at (54, 110) rather than (54, 14), so the arm hangs
    in exactly the same place and only the part grew upward. ``rig.json``
    carries the matching pivot.
    """
    W, H = 148, 228
    img = _blank((W, H))
    base, lit, dark = (CLOTH, CLOTH_LIT, CLOTH_DK) if near else (
        (150, 154, 162), (186, 190, 198), (104, 108, 116))
    skin = (SKIN, SKIN_LIT, SKIN_DK) if near else (SKIN_DK, SKIN, SKIN_DEEP)

    sh = (54.0, 110.0)
    elbow = (58.0, 156.0) if near else (60.0, 160.0)
    wrist = (82.0, 178.0) if near else (80.0, 182.0)

    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(38, 108), (69, 108), (70, 150), (68, 160), (46, 162), (38, 124)], fill=255)
    d.ellipse([sh[0] - 18, sh[1] - 10, sh[0] + 18, sh[1] + 15], fill=255)
    d.ellipse([elbow[0] - 12, elbow[1] - 9, elbow[0] + 12, elbow[1] + 9], fill=255)
    img.alpha_composite(char_rig._shade(mask, base, lit, dark))

    fmask = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(fmask)
    fd.line([elbow, wrist], fill=255, width=17)
    fd.ellipse([elbow[0] - 9, elbow[1] - 9, elbow[0] + 9, elbow[1] + 9], fill=255)
    fd.ellipse([wrist[0] - 9, wrist[1] - 9, wrist[0] + 9, wrist[1] + 9], fill=255)
    img.alpha_composite(char_rig._shade(fmask, base, lit, dark))

    d = ImageDraw.Draw(img)
    d.line([(wrist[0] - 5, wrist[1] - 3), (wrist[0] + 5, wrist[1] + 3)],
           fill=CLOTH_TRIM + (255,), width=22)
    d.line([(wrist[0] - 3, wrist[1] - 2), (wrist[0] + 4, wrist[1] + 3)],
           fill=dark + (210,), width=15)

    # fist closed on the shaft
    hx, hy = (92, 184) if near else (90, 188)
    d.ellipse([hx - 11, hy - 10, hx + 11, hy + 10], fill=skin[0] + (255,))
    d.ellipse([hx - 8, hy - 8, hx + 6, hy + 3], fill=skin[1] + (205,))
    d.line([(hx - 4, hy + 5), (hx + 9, hy + 6)], fill=skin[2] + (185,), width=2)
    for i in range(3):
        d.line([(hx + 3, hy - 6 + i * 5), (hx + 12, hy - 5 + i * 5)],
               fill=skin[2] + (150,), width=2)

    d.line([(38, 124), (41, 148)], fill=dark + (130,), width=2)
    d.line([(66, 120), (65, 146)], fill=lit + (80,), width=2)
    d.line([(58, 156), (76, 156)], fill=dark + (100,), width=2)

    # the rake: nearly upright, head above the hat line, tilted a touch forward
    _rake(img, hx, hy, 6, -118)

    if not near:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img


# ------------------------------------------------------------------------ legs
def thigh():
    W, H = 54, 86
    return _limb((W, H), [(10, 2), (44, 2), (46, 46), (41, 84), (13, 84), (8, 46)],
                 TROUSER, TROUSER_LIT, TROUSER_DK)


def shin():
    W, H = 46, 77
    leg = _limb((W, H), [(9, 2), (37, 2), (39, 34), (35, 75), (11, 75), (7, 34)],
                TROUSER, TROUSER_LIT, TROUSER_DK)
    bootmask = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(bootmask)
    bd.polygon([(7, 30), (39, 30), (35, 75), (11, 75)], fill=255)
    boot = char_rig._shade(bootmask, BOOT, BOOT_LIT, BOOT_DK)
    img = Image.alpha_composite(leg, boot)
    d = ImageDraw.Draw(img)
    d.line([(5, 30), (41, 30)], fill=(110, 114, 124, 190), width=2)
    d.line([(10, 38), (34, 38)], fill=BOOT_LIT + (110,), width=2)
    return img


def foot():
    """Dark pointed boot, toe to the right; the pivot is the heel."""
    W, H = 52, 36
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(6, 8), (30, 5), (50, 17), (49, 33), (8, 34)], fill=255)
    d.ellipse([2, 6, 22, 34], fill=255)
    img = char_rig._shade(mask, BOOT, BOOT_LIT, BOOT_DK)
    d = ImageDraw.Draw(img)
    d.line([(7, 32), (48, 31)], fill=(110, 114, 124, 205), width=2)
    d.line([(9, 12), (27, 9)], fill=BOOT_LIT + (120,), width=2)
    return img


# ------------------------------------------------------------------------ cape
def cape():
    """The Storm cloak, to the floor, hanging open with the lining turned out.

    Same silhouette and same wool as Lightning's, because it is the same
    garment; only the light on it is a shade cooler.
    """
    W, H = 190, 240
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(62, 6), (128, 6), (170, 156), (184, 216), (158, 202),
               (138, 228), (112, 206), (92, 230), (66, 208), (40, 228),
               (16, 204), (6, 156), (24, 118)], fill=255)
    d.ellipse([52, 0, 138, 30], fill=255)
    img = char_rig._shade(mask, CAPE, CAPE_LIT, CAPE_DK)
    d = ImageDraw.Draw(img)

    lining = Image.new("L", (W, H), 0)
    ld = ImageDraw.Draw(lining)
    ld.polygon([(60, 10), (92, 10), (86, 128), (66, 196), (30, 210),
                (14, 172), (34, 104)], fill=255)
    ld.polygon([(126, 12), (140, 12), (150, 150), (140, 196), (126, 152)],
               fill=255)
    img.alpha_composite(char_rig._shade(lining, CAPE_LINING,
                                        CAPE_LINING_LIT, CAPE_DK))

    for x0, x1 in ((30, 14), (52, 40), (70, 60), (96, 108), (118, 148),
                   (142, 172)):
        d.line([(x0, 34), (x1, 210)], fill=CAPE_DK + (120,), width=3)
    for x0, x1 in ((44, 36), (84, 92), (106, 122)):
        d.line([(x0, 44), (x1, 160)], fill=CAPE_LIT + (70,), width=3)
    for x0, x1 in ((46, 26), (72, 56)):
        d.line([(x0, 30), (x1, 196)], fill=CAPE_LINING_LIT + (110,), width=2)
    d.line([(134, 24), (146, 170)], fill=CAPE_LINING_LIT + (90,), width=2)

    d.line([(58, 12), (128, 12)], fill=(122, 126, 136, 255), width=6)
    d.ellipse([85, 6, 101, 22], fill=STEEL + (255,))
    return img


# ------------------------------------------------------------------------ main
RIG_JSON = {
    "pivots": {
        "pelvis": [39, 16],
        # shoulder is at y=110 in the taller arm part, so the pivot moved down
        # with it: at 14 the whole arm and its rake hung 96px too high.
        "arm_n": [54, 110],
        "arm_f": [93, 110],
        "foot_n": [14, 25],
        "foot_f": [14, 25],
        "cape": [95, 12],
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
    print(f"wrote {len(parts)} parts -> art_src/chars/rain/parts/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
