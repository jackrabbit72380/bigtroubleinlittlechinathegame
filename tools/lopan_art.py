"""Lo Pan: the sorcerer himself, painted in code.

Every other Storm or gang fighter is a body with a weapon. Lo Pan is a costume
and a piece of architecture: the towering headdress with its fan of panels and
the long pin through it, the floor-length imperial robe with the phoenix
embroidered across it, the sleeves that hang past his hands, and the beard.

He carries nothing. His hands are the weapon - claws, raised, fingers spread -
so where Rain grips a rake and Thunder a crescent blade, Lo Pan's arms end in
an open hand with long nails and a green light behind it. The sorcery itself
lives in ``tools/lopan.py``: sigils and spectral fire, never a bolt or a wave
of water.

Output is exactly what ``char_rig`` expects:

    art_src/chars/lopan/parts/*.png
    art_src/chars/lopan/parts/rig.json

Run:  python3 tools/lopan_art.py
"""

from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import char_rig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "art_src", "chars", "lopan", "parts")

# --------------------------------------------------------------------- palette
# Imperial navy: the robe in the concept is a deep blue-black, and it has to
# stay darker than the gold or the whole figure turns into one bright shape.
ROBE = (38, 46, 86)
ROBE_LIT = (62, 74, 124)
ROBE_DK = (22, 26, 52)

# Gold: the headdress band, the trim and the phoenix's highlights.
GOLD = (196, 158, 74)
GOLD_LIT = (240, 210, 132)
GOLD_DK = (124, 92, 34)

# Vermilion and jade, the two colours embroidered over the robe. The phoenix is
# painted in both: orange body, green wings, exactly as the costume reads.
VERMILION = (188, 74, 40)
VERMILION_LIT = (232, 120, 70)
JADE = (58, 132, 92)
JADE_LIT = (108, 194, 138)
JADE_DK = (28, 74, 52)

SKIN = (204, 178, 166)
SKIN_LIT = (232, 210, 198)
SKIN_DK = (146, 120, 112)
SKIN_DEEP = (96, 86, 88)

HAIR = (18, 16, 20)
HAIR_LIT = (52, 48, 58)

# His magic: a sickly green, the colour of the light under the throne.
SORCERY = (96, 226, 158)
SORCERY_LIT = (186, 255, 214)


def _blank(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _shape(size, pts):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    return mask


def _limb(size, pts, base, lit, dark):
    return char_rig._shade(_shape(size, pts), base, lit, dark)


def _phoenix(d, cx, cy, scale=1.0):
    """The bird embroidered on his chest: body, spread wings, tail down."""
    s = scale
    # tail: two long plumes falling to the hem
    for dx in (-7, 7):
        d.line([(cx + dx * s, cy + 6 * s), (cx + dx * 1.6 * s, cy + 52 * s)],
               fill=VERMILION + (235,), width=max(2, int(4 * s)))
        d.line([(cx + dx * s, cy + 6 * s), (cx + dx * 1.6 * s, cy + 52 * s)],
               fill=GOLD + (120,), width=max(1, int(2 * s)))
    # body
    d.ellipse([cx - 9 * s, cy - 10 * s, cx + 9 * s, cy + 14 * s],
              fill=VERMILION + (245,))
    d.ellipse([cx - 5 * s, cy - 7 * s, cx + 3 * s, cy + 6 * s],
              fill=VERMILION_LIT + (200,))
    # wings, swept up and out
    for sx in (-1, 1):
        d.polygon([(cx + sx * 7 * s, cy - 6 * s),
                   (cx + sx * 34 * s, cy - 26 * s),
                   (cx + sx * 30 * s, cy - 4 * s),
                   (cx + sx * 12 * s, cy + 8 * s)],
                  fill=JADE + (235,))
        d.line([(cx + sx * 9 * s, cy - 5 * s), (cx + sx * 31 * s, cy - 22 * s)],
               fill=JADE_LIT + (160,), width=max(1, int(2 * s)))
        for k in range(3):
            d.line([(cx + sx * (13 + k * 6) * s, cy - (10 + k * 4) * s),
                    (cx + sx * (12 + k * 6) * s, cy + (2 + k * 2) * s)],
                   fill=JADE_DK + (150,), width=1)
    # head and crest
    d.ellipse([cx - 4 * s, cy - 17 * s, cx + 4 * s, cy - 9 * s],
              fill=VERMILION_LIT + (250,))
    d.line([(cx, cy - 17 * s), (cx - 3 * s, cy - 27 * s)],
           fill=GOLD + (230,), width=max(1, int(2 * s)))
    d.line([(cx, cy - 17 * s), (cx + 4 * s, cy - 25 * s)],
           fill=GOLD + (230,), width=max(1, int(2 * s)))
    d.point([(cx - 2 * s, cy - 14 * s)], fill=(20, 16, 16, 255))


# ----------------------------------------------------------------------- torso
def torso():
    """Navy imperial robe, phoenix on the chest, gold-edged lapels."""
    W, H = 126, 132
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(28, 16), (98, 16), (94, 60), (92, 104), (90, 132),
               (36, 132), (34, 104), (32, 60)], fill=255)
    d.ellipse([16, 2, 60, 52], fill=255)
    d.ellipse([66, 2, 110, 52], fill=255)
    img = char_rig._shade(mask, ROBE, ROBE_LIT, ROBE_DK)
    d = ImageDraw.Draw(img)

    # --- the robe's own panel, a shade lighter than the sleeves -------------
    panel = Image.new("L", (W, H), 0)
    ImageDraw.Draw(panel).polygon([(40, 20), (86, 20), (84, 92), (42, 92)],
                                  fill=255)
    img.alpha_composite(char_rig._shade(panel, (46, 54, 98), (74, 86, 138),
                                        (26, 30, 58)))

    # --- phoenix -------------------------------------------------------------
    _phoenix(d, 63, 58, 1.10)

    # --- lapels: gold-edged, crossing left over right ------------------------
    d.polygon([(40, 16), (63, 40), (86, 16), (86, 24), (63, 50), (40, 24)],
              fill=GOLD + (255,))
    d.polygon([(41, 20), (63, 42), (85, 20), (85, 23), (63, 46), (41, 23)],
              fill=GOLD_DK + (200,))
    d.line([(40, 16), (63, 41), (86, 16)], fill=GOLD_LIT + (200,), width=2)

    # --- collar, standing up behind the beard -------------------------------
    d.polygon([(40, 12), (63, 26), (86, 12), (84, 4), (63, 18), (42, 4)],
              fill=JADE + (255,))
    d.line([(42, 5), (63, 19), (84, 5)], fill=JADE_LIT + (180,), width=2)

    # --- embroidered bands at the shoulders ---------------------------------
    for x0, x1 in ((30, 42), (84, 96)):
        d.line([(x0, 24), (x1, 24)], fill=VERMILION + (210,), width=3)
        d.line([(x0, 30), (x1, 30)], fill=JADE + (180,), width=2)

    for x, y1 in ((46, 104), (58, 96), (74, 96), (84, 104)):
        d.line([(x, 52), (x + (1 if x < 63 else -1), y1)],
               fill=ROBE_DK + (120,), width=2)
    return img.resize((110, H), Image.LANCZOS)


# ---------------------------------------------------------------------- pelvis
def pelvis():
    """Floor-length skirt, gold hem, the phoenix's tail running down it."""
    W, H = 96, 84
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(28, 4), (68, 4), (88, 56), (78, 82), (18, 82), (8, 56)], fill=255)
    d.ellipse([8, 50, 88, 86], fill=255)
    img = char_rig._shade(mask, ROBE, ROBE_LIT, ROBE_DK)
    d = ImageDraw.Draw(img)
    # sash
    d.rectangle([26, 2, 70, 14], fill=JADE + (255,))
    d.rectangle([26, 8, 70, 12], fill=GOLD + (230,))
    # the tail plumes continue below the sash
    for dx in (-7, 7):
        d.line([(48 + dx, 14), (48 + dx * 1.7, 60)],
               fill=VERMILION + (200,), width=3)
    for x in (26, 40, 56, 70):
        d.line([(x, 16), (x + (2 if x < 48 else -2), 76)],
               fill=ROBE_DK + (110,), width=2)
    # hem
    d.line([(14, 74), (82, 74)], fill=GOLD + (255,), width=3)
    d.line([(16, 79), (80, 79)], fill=GOLD_DK + (200,), width=2)
    return img.resize((76, H), Image.LANCZOS)


# ------------------------------------------------------------------------ head
def head():
    """The headdress, the pin, the hair and the beard - his whole silhouette.

    The canvas is much taller than the head: the fan of the headdress is nearly
    as tall again as the face, and at 112px it was drawn as a striped cap. The
    pivot is the bottom of the canvas, so the extra height grows upward and the
    neck stays where the rig expects it.
    """
    W, H = 176, 152
    cx = W // 2
    img = _blank((W, H))

    # --- hair behind everything ---------------------------------------------
    hair = Image.new("L", (W, H), 0)
    hd = ImageDraw.Draw(hair)
    hd.ellipse([cx - 42, 74, cx + 42, 150], fill=255)
    hd.rectangle([cx - 42, 104, cx - 24, 150], fill=255)
    hd.rectangle([cx + 24, 104, cx + 42, 150], fill=255)
    img.alpha_composite(char_rig._shade(hair, HAIR, HAIR_LIT, (8, 8, 10)))

    # --- face: long and narrow ----------------------------------------------
    neck = Image.new("L", (W, H), 0)
    ImageDraw.Draw(neck).rectangle([cx - 12, 128, cx + 12, H], fill=255)
    img.alpha_composite(char_rig._shade(neck, SKIN_DK, SKIN, SKIN_DEEP))

    face = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(face)
    fd.ellipse([cx - 27, 78, cx + 27, 144], fill=255)
    fd.rectangle([cx - 17, 106, cx + 17, 144], fill=255)
    img.alpha_composite(char_rig._shade(face, SKIN, SKIN_LIT, SKIN_DK))
    d = ImageDraw.Draw(img)

    # --- eyes: narrow, dark, hard under the band -----------------------------
    d.line([(cx - 21, 104), (cx - 5, 106)], fill=(36, 28, 30, 240), width=3)
    d.line([(cx + 5, 106), (cx + 21, 104)], fill=(36, 28, 30, 240), width=3)
    for sx in (-1, 1):
        d.ellipse([cx + sx * 12 - 4, 110, cx + sx * 12 + 4, 115],
                  fill=(246, 244, 242, 255))
        d.ellipse([cx + sx * 12 - 2, 110, cx + sx * 12 + 2, 115],
                  fill=(14, 12, 16, 255))
    d.line([(cx, 116), (cx - 3, 126)], fill=SKIN_DK + (200,), width=2)
    d.line([(cx - 6, 129), (cx + 6, 129)], fill=(58, 30, 30, 230), width=2)

    # --- moustache and beard -------------------------------------------------
    d.polygon([(cx - 17, 127), (cx, 125), (cx + 17, 127), (cx + 8, 135),
               (cx, 131), (cx - 8, 135)], fill=HAIR + (255,))
    beard = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(beard)
    bd.polygon([(cx - 22, 128), (cx + 22, 128), (cx + 16, 148), (cx + 4, 152),
                (cx - 9, 150), (cx - 19, 142)], fill=255)
    img.alpha_composite(char_rig._shade(beard, HAIR, HAIR_LIT, (8, 8, 10)))
    d = ImageDraw.Draw(img)
    for x in range(-15, 16, 5):
        d.line([(cx + x, 134), (cx + int(x * 0.7), 148)],
               fill=HAIR_LIT + (110,), width=1)

    # --- headdress: gold band at the brow, the fan towering above it ---------
    d.rectangle([cx - 32, 74, cx + 32, 92], fill=GOLD + (255,))
    d.rectangle([cx - 32, 74, cx + 32, 79], fill=GOLD_LIT + (235,))
    d.rectangle([cx - 32, 89, cx + 32, 92], fill=GOLD_DK + (235,))
    for k in range(3):
        bx = cx - 20 + k * 20
        d.ellipse([bx - 5, 79, bx + 5, 89], fill=GOLD_DK + (255,))
        d.ellipse([bx - 2, 82, bx + 2, 86], fill=GOLD_LIT + (255,))

    crown = Image.new("L", (W, H), 0)
    cd = ImageDraw.Draw(crown)
    for k in range(5):
        top = 8 + abs(k - 2) * 7
        x0 = cx - 40 + k * 16
        cd.polygon([(x0, 74), (x0 + 16, 74), (x0 + 13, top), (x0 + 3, top)],
                   fill=255)
    img.alpha_composite(char_rig._shade(crown, (40, 44, 78), (66, 72, 116),
                                        (20, 22, 44)))
    d = ImageDraw.Draw(img)
    for k in range(5):
        top = 8 + abs(k - 2) * 7
        x0 = cx - 40 + k * 16
        d.line([(x0 + 8, top + 3), (x0 + 8, 72)], fill=VERMILION + (235,),
               width=4)
        d.line([(x0 + 11, top + 6), (x0 + 11, 70)], fill=(226, 220, 214, 185),
               width=2)
        d.line([(x0 + 1, 72), (x0 + 14, 72)], fill=GOLD + (240,), width=2)

    # the pin, straight through the band and out both sides
    d.line([(cx - 46, 82), (cx + 46, 82)], fill=GOLD + (255,), width=3)
    d.line([(cx - 46, 81), (cx + 46, 81)], fill=GOLD_LIT + (200,), width=1)
    d.ellipse([cx - 51, 78, cx - 44, 86], fill=GOLD_LIT + (255,))
    d.ellipse([cx + 44, 78, cx + 51, 86], fill=GOLD_LIT + (255,))

    return img


# ------------------------------------------------------------------------- arm
def arm(near=True):
    """A wide sleeve with an open clawed hand at the end of it."""
    W, H = 188, 246
    img = _blank((W, H))
    base, lit, dark = (ROBE, ROBE_LIT, ROBE_DK) if near else (
        (30, 36, 68), (52, 62, 104), (18, 22, 44))
    skin = (SKIN, SKIN_LIT, SKIN_DK) if near else (SKIN_DK, SKIN, SKIN_DEEP)

    sh = (54.0, 112.0)
    elbow = (58.0, 158.0) if near else (60.0, 162.0)
    wrist = (80.0, 182.0) if near else (78.0, 186.0)

    # upper arm inside the sleeve
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(37, 108), (71, 108), (70, 152), (68, 162), (42, 164), (37, 124)], fill=255)
    d.ellipse([sh[0] - 19, sh[1] - 11, sh[0] + 19, sh[1] + 16], fill=255)
    img.alpha_composite(char_rig._shade(mask, base, lit, dark))

    # the sleeve: a wide bell hanging from the elbow past the hand
    sleeve = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(sleeve)
    sd.polygon([(elbow[0] - 16, elbow[1] - 12), (elbow[0] + 16, elbow[1] - 12),
                (elbow[0] + 44, elbow[1] + 62), (elbow[0] + 18, elbow[1] + 84),
                (elbow[0] - 26, elbow[1] + 78), (elbow[0] - 22, elbow[1] + 26)],
               fill=255)
    img.alpha_composite(char_rig._shade(sleeve, base, lit, dark))
    d = ImageDraw.Draw(img)
    # gold band at the cuff and a jade stripe up the sleeve
    d.line([(elbow[0] - 22, elbow[1] + 58), (elbow[0] + 40, elbow[1] + 44)],
           fill=GOLD + (240,), width=3)
    d.line([(elbow[0] - 20, elbow[1] + 66), (elbow[0] + 38, elbow[1] + 52)],
           fill=JADE + (190,), width=2)

    # forearm emerging from the cuff
    fmask = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(fmask)
    fd.line([elbow, wrist], fill=255, width=15)
    img.alpha_composite(char_rig._shade(fmask, skin[0], skin[1], skin[2]))

    # open hand, fingers spread, long nails
    hx, hy = (92, 186) if near else (90, 190)
    d = ImageDraw.Draw(img)
    d.ellipse([hx - 10, hy - 8, hx + 10, hy + 10], fill=skin[0] + (255,))
    for k in range(4):
        a = -0.9 + k * 0.55
        fx = hx + 8 + 12 * (0.35 + 0.65 * (k % 2))
        fy = hy - 4 + (k - 1.5) * 8
        d.line([(hx + 4, hy + (k - 1.5) * 3), (fx, fy)],
               fill=skin[0] + (255,), width=5)
        d.line([(fx, fy), (fx + 4, fy - 2)], fill=JADE + (215,), width=2)
    d.line([(hx - 2, hy + 4), (hx + 8, hy + 14)], fill=skin[2] + (180,), width=2)

    if not near:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img


# ------------------------------------------------------------------------ legs
def thigh():
    W, H = 54, 86
    return _limb((W, H), [(11, 2), (43, 2), (45, 46), (40, 84), (14, 84), (9, 46)],
                 ROBE_DK, (44, 52, 92), (16, 18, 34))


def shin():
    W, H = 46, 78
    leg = _limb((W, H), [(9, 2), (37, 2), (39, 34), (35, 76), (11, 76), (7, 34)],
                ROBE_DK, (44, 52, 92), (16, 18, 34))
    bootmask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(bootmask).polygon([(7, 26), (39, 26), (35, 76), (11, 76)],
                                     fill=255)
    boot = char_rig._shade(bootmask, (22, 20, 26), (54, 50, 60), (10, 9, 12))
    img = Image.alpha_composite(leg, boot)
    d = ImageDraw.Draw(img)
    d.line([(5, 26), (41, 26)], fill=GOLD + (200,), width=2)
    return img


def foot():
    W, H = 54, 34
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(6, 6), (30, 4), (52, 14), (51, 31), (8, 32)], fill=255)
    d.ellipse([2, 4, 22, 32], fill=255)
    img = char_rig._shade(mask, (22, 20, 26), (54, 50, 60), (10, 9, 12))
    d = ImageDraw.Draw(img)
    d.line([(8, 30), (50, 29)], fill=GOLD + (170,), width=2)
    return img


# ------------------------------------------------------------------------ robe
def train():
    """The robe's train behind him - the 'cape' slot, worn as imperial silk."""
    W, H = 184, 232
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(58, 4), (126, 4), (172, 148), (180, 208), (150, 196),
               (128, 224), (100, 198), (74, 226), (52, 196), (22, 214),
               (12, 146), (30, 110)], fill=255)
    d.ellipse([50, -4, 134, 26], fill=255)
    img = char_rig._shade(mask, (32, 38, 74), (56, 66, 112), (18, 20, 40))
    d = ImageDraw.Draw(img)
    # gold border down both edges, as the costume has
    d.line([(20, 130), (16, 200), (40, 190)], fill=GOLD + (230,), width=3)
    d.line([(166, 140), (172, 200), (150, 192)], fill=GOLD + (230,), width=3)
    for x0, x1 in ((34, 20), (56, 44), (76, 66), (100, 110), (124, 150),
                   (148, 172)):
        d.line([(x0, 30), (x1, 210)], fill=(18, 20, 40, 130), width=3)
    return img


# ------------------------------------------------------------------------ main
RIG_JSON = {
    "pivots": {
        "pelvis": [38, 14],
        # the sleeve makes the arm part wider than Rain's, so the far arm's
        # pivot mirrors to 188-56
        "arm_n": [54, 112],
        "arm_f": [133, 112],
        "foot_n": [14, 24],
        "foot_f": [14, 24],
        "cape": [92, 10],
    },
}


def main():
    os.makedirs(PARTS, exist_ok=True)
    parts = {
        "cape": train(),
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
    print(f"wrote {len(parts)} parts -> art_src/chars/lopan/parts/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
