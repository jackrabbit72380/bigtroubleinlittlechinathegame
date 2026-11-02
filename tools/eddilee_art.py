"""Eddie Lee: a street-smart Chinatown scrapper, painted in code.

He is the roster's fast, light counter-fighter: a young man in a lightweight
jacket worn open over a rolled-sleeve shirt, fingerless gloves and flexible
street shoes, with the Chang Sing's red-and-gold knot worked into his collar
and his cuff. No hat and no weapon - his silhouette is the jacket and the
gloves, so those are the two things the art spends its detail on.

The rig contract is Wang Chi's, because his stance is the closest to what
Eddie needs (arms cut hanging, one bent piece per arm, a wide base):

    art_src/chars/eddilee/parts/*.png
    art_src/chars/eddilee/parts/rig.json

Run:  python3 tools/eddilee_art.py [--sheet]
"""

from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import char_rig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "art_src", "chars", "eddilee", "parts")

SKIN = (222, 176, 140)
SKIN_LIT = (246, 208, 174)
SKIN_DK = (168, 118, 88)
SKIN_DEEP = (108, 70, 52)

HAIR = (28, 24, 28)
HAIR_LIT = (62, 54, 60)
HAIR_DK = (12, 10, 14)

# The jacket: a charcoal-indigo lightweight shell, so it reads as a jacket
# without going black, with a lighter lining flashing at the opening.
JACKET = (62, 68, 92)
JACKET_LIT = (96, 104, 132)
JACKET_DK = (36, 40, 58)
JACKET_DEEP = (22, 25, 38)
LINING = (126, 92, 76)

# The shirt under it: pale, fine-striped, sleeves rolled to the elbow.
SHIRT = (206, 204, 196)
SHIRT_LIT = (238, 236, 228)
SHIRT_DK = (152, 152, 146)
STRIPE = (150, 132, 128)

GLOVE = (44, 40, 48)
GLOVE_LIT = (78, 72, 84)
GLOVE_DK = (24, 22, 28)

JEANS = (72, 78, 96)
JEANS_LIT = (106, 114, 134)
JEANS_DK = (42, 46, 60)

SHOE = (52, 50, 56)
SHOE_LIT = (88, 86, 92)
SHOE_SOLE = (216, 212, 200)

# Chang Sing red and gold: the collar tab and the cuff band.
SASH = (176, 52, 44)
SASH_LIT = (214, 88, 72)
SASH_DK = (112, 28, 26)
GOLD = (212, 172, 92)
GOLD_DK = (140, 106, 46)


def _blank(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _limb(size, pts, base, lit, dark):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    return char_rig._shade(mask, base, lit, dark)


def torso():
    """112 x 132: open jacket over a striped shirt, Chang Sing tab and knot."""
    W, H = 112, 132
    cx = W // 2

    # the shirt body first: the jacket is drawn over its edges
    shirt = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shirt)
    sd.polygon([(cx - 26, 10), (cx + 26, 10), (cx + 28, 60),
                (cx + 26, 132), (cx - 26, 132), (cx - 28, 60)], fill=255)
    sd.ellipse([cx - 33, 6, cx - 5, 40], fill=255)
    sd.ellipse([cx + 5, 6, cx + 33, 40], fill=255)
    img = char_rig._shade(shirt, SHIRT, SHIRT_LIT, SHIRT_DK)

    stripes = _blank((W, H))
    st = ImageDraw.Draw(stripes)
    for i in range(-4, 12):
        x = cx - 28 + i * 9
        st.line([(x, 0), (x, H)], fill=STRIPE + (120,), width=2)
    stripes.putalpha(ImageChops.multiply(stripes.getchannel("A"), shirt))
    img.alpha_composite(stripes)

    # the open jacket: two front panels with a lining edge, plus the collar
    jacket = Image.new("L", (W, H), 0)
    jd = ImageDraw.Draw(jacket)
    jd.polygon([(cx - 26, 8), (cx - 8, 12), (cx - 10, 60), (cx - 12, 132),
                (cx - 32, 132), (cx - 33, 60), (cx - 30, 40)], fill=255)
    jd.polygon([(cx + 26, 8), (cx + 8, 12), (cx + 10, 60), (cx + 12, 132),
                (cx + 32, 132), (cx + 33, 60), (cx + 30, 40)], fill=255)
    jd.ellipse([cx - 34, 4, cx - 6, 34], fill=255)
    jd.ellipse([cx + 6, 4, cx + 34, 34], fill=255)
    jd.polygon([(cx - 30, 6), (cx - 12, 10), (cx - 18, 30), (cx - 26, 22)],
               fill=255)
    jd.polygon([(cx + 30, 6), (cx + 12, 10), (cx + 18, 30), (cx + 26, 22)],
               fill=255)
    img.alpha_composite(char_rig._shade(jacket, JACKET, JACKET_LIT, JACKET_DK))
    d = ImageDraw.Draw(img)

    # lining flashing inside the opening, then the collar points
    d.line([(cx - 9, 14), (cx - 11, 130)], fill=LINING + (215,), width=3)
    d.line([(cx + 9, 14), (cx + 11, 130)], fill=LINING + (235,), width=3)
    d.line([(cx - 10, 16), (cx - 12, 128)], fill=JACKET_DEEP + (200,), width=1)
    d.line([(cx + 10, 16), (cx + 12, 128)], fill=JACKET_DEEP + (200,), width=1)
    d.polygon([(cx - 27, 8), (cx - 11, 12), (cx - 16, 32), (cx - 24, 20)],
              fill=JACKET_LIT + (240,))
    d.polygon([(cx + 27, 8), (cx + 11, 12), (cx + 16, 32), (cx + 24, 20)],
              fill=JACKET_DK + (225,))

    # the Chang Sing colours: a red tab on the near collar with a gold bar
    d.polygon([(cx + 12, 12), (cx + 20, 15), (cx + 17, 40), (cx + 11, 34)],
              fill=SASH + (255,))
    d.line([(cx + 13, 18), (cx + 19, 21)], fill=GOLD + (240,), width=2)
    d.line([(cx + 12, 26), (cx + 18, 29)], fill=GOLD + (210,), width=2)

    # the knot on the chest: a gold diamond ringed in red
    kx, ky = cx - 18, 62
    d.polygon([(kx, ky - 9), (kx + 8, ky), (kx, ky + 9), (kx - 8, ky)],
              outline=SASH + (245,), width=2)
    d.polygon([(kx, ky - 5), (kx + 4, ky), (kx, ky + 5), (kx - 4, ky)],
              fill=GOLD + (245,))
    d.line([(kx - 12, ky), (kx - 8, ky)], fill=GOLD_DK + (220,), width=2)
    d.line([(kx + 8, ky), (kx + 12, ky)], fill=GOLD_DK + (220,), width=2)

    # pocket flap, zip pull, and the folds that give the shell some weight
    d.line([(cx - 30, 92), (cx - 14, 94)], fill=JACKET_DEEP + (190,), width=2)
    d.line([(cx - 30, 96), (cx - 14, 98)], fill=JACKET_LIT + (120,), width=1)
    d.line([(cx + 30, 70), (cx + 16, 74)], fill=JACKET_LIT + (110,), width=2)
    d.line([(cx - 6, 40), (cx - 4, 66)], fill=SHIRT_DK + (110,), width=1)
    for y in (48, 62, 76, 90, 104, 118):
        d.line([(cx - 3, y), (cx + 3, y)], fill=SHIRT_DK + (150,), width=1)
    return img


def pelvis():
    """100 x 104: jeans, a webbing belt, and the coin pouch on the hip."""
    W, H = 100, 104
    cx = W // 2
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(cx - 24, 2), (cx + 24, 2), (cx + 26, 34), (cx + 24, 72),
               (cx + 6, 72), (cx + 3, 46), (cx - 3, 46), (cx - 6, 72),
               (cx - 24, 72), (cx - 26, 34)], fill=255)
    img = char_rig._shade(mask, JEANS, JEANS_LIT, JEANS_DK)
    d = ImageDraw.Draw(img)

    # belt: dark webbing with a plain square buckle
    d.rectangle([cx - 30, 6, cx + 30, 19], fill=(38, 34, 40, 255))
    d.rectangle([cx - 30, 8, cx + 30, 10], fill=(74, 68, 78, 210))
    d.rectangle([cx - 7, 5, cx + 7, 20], outline=(168, 156, 132, 250), width=2)
    d.rectangle([cx - 2, 9, cx + 2, 16], fill=(168, 156, 132, 220))

    # the coin pouch: the prop his Lucky Coin Flick comes out of
    d.rounded_rectangle([cx + 14, 22, cx + 26, 40], radius=3,
                        fill=(58, 46, 36, 255), outline=GOLD_DK + (220,), width=1)
    d.line([(cx + 16, 28), (cx + 24, 28)], fill=GOLD + (190,), width=1)

    for x0, x1 in ((cx - 15, cx - 17), (cx + 15, cx + 17)):
        d.line([(x0, 22), (x1, 70)], fill=JEANS_DK + (120,), width=2)
    d.line([(cx - 22, 44), (cx - 9, 48)], fill=JEANS_LIT + (90,), width=2)
    d.line([(cx + 9, 56), (cx + 22, 52)], fill=JEANS_DK + (90,), width=2)
    return img


def head():
    """92 x 108: short black crop, alert eyes, the grin of a man with a plan."""
    W, H = 92, 108
    cx = W // 2
    img = _blank((W, H))

    neck = Image.new("L", (W, H), 0)
    ImageDraw.Draw(neck).rectangle([cx - 11, 88, cx + 11, H], fill=255)
    img.alpha_composite(char_rig._shade(neck, SKIN_DK, SKIN, SKIN_DEEP))

    # short hair, cut close at the sides and fuller on top with a side part
    hair = Image.new("L", (W, H), 0)
    hd = ImageDraw.Draw(hair)
    hd.ellipse([cx - 22, 20, cx + 22, 66], fill=255)
    hd.polygon([(cx - 22, 36), (cx - 25, 56), (cx - 19, 58), (cx - 18, 42)],
               fill=255)
    hd.polygon([(cx + 22, 36), (cx + 25, 56), (cx + 19, 58), (cx + 18, 42)],
               fill=255)
    hd.polygon([(cx - 18, 24), (cx + 14, 20), (cx + 20, 30), (cx - 16, 32)],
               fill=255)
    img.alpha_composite(char_rig._shade(hair, HAIR, HAIR_LIT, HAIR_DK))

    face = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(face)
    fd.ellipse([cx - 18, 34, cx + 18, 84], fill=255)
    fd.polygon([(cx - 15, 62), (cx + 15, 62), (cx + 10, 88), (cx, 94),
                (cx - 10, 88)], fill=255)
    img.alpha_composite(char_rig._shade(face, SKIN, SKIN_LIT, SKIN_DK))

    for sx in (-1, 1):
        ex = cx + sx * 19
        e = Image.new("L", (W, H), 0)
        ImageDraw.Draw(e).ellipse([ex - 4, 50, ex + 4, 66], fill=255)
        img.alpha_composite(char_rig._shade(e, SKIN, SKIN_LIT, SKIN_DK))
    d = ImageDraw.Draw(img)

    # hairline over the brow, and the part
    d.arc([cx - 20, 26, cx + 20, 56], 200, 340, fill=HAIR_DK + (235,), width=6)
    d.line([(cx - 4, 28), (cx + 6, 44)], fill=HAIR + (230,), width=2)

    # eyes: level, wide awake, calculating
    for sx in (-1, 1):
        ex = cx + sx * 10
        d.line([(ex - 7, 49), (ex + 6, 48)], fill=(40, 30, 26, 245), width=3)
        d.ellipse([ex - 6, 53, ex + 6, 62], fill=(246, 242, 236, 255))
        d.ellipse([ex - 2, 54, ex + 2, 61], fill=(34, 24, 18, 255))
        d.arc([ex - 6, 51, ex + 6, 62], 200, 340, fill=(52, 38, 32, 210), width=1)
        d.line([(ex - 2, 64), (ex - 6, 68)], fill=SKIN_DK + (150,), width=1)

    d.polygon([(cx - 4, 62), (cx + 4, 62), (cx + 2, 74), (cx - 2, 74)],
              fill=SKIN_DK + (130,))
    d.line([(cx + 1, 66), (cx + 4, 72)], fill=SKIN_DEEP + (130,), width=2)

    # the grin: one corner up. He is enjoying this more than he should.
    d.line([(cx - 9, 80), (cx + 10, 77)], fill=(118, 58, 52, 235), width=2)
    d.arc([cx - 9, 74, cx + 10, 86], 10, 150, fill=(118, 58, 52, 205), width=2)
    d.line([(cx - 6, 86), (cx + 7, 83)], fill=SKIN_DK + (120,), width=1)
    d.line([(cx - 15, 70), (cx - 11, 76)], fill=SKIN_DK + (95,), width=2)
    d.line([(cx + 15, 70), (cx + 11, 76)], fill=SKIN_DK + (95,), width=2)
    # a small chin scar: the street left a mark
    d.line([(cx + 5, 88), (cx + 8, 92)], fill=SKIN_DEEP + (170,), width=1)
    return img


def arm(near=True):
    """Jacket sleeve rolled at the elbow, bare forearm, fingerless glove."""
    W, H = 148, 132
    img = _blank((W, H))
    skin = (SKIN, SKIN_LIT, SKIN_DK) if near else (SKIN_DK, SKIN, SKIN_DEEP)
    shell = (JACKET, JACKET_LIT, JACKET_DK) if near else (
        (44, 48, 68), (74, 80, 102), (26, 28, 42))
    sh = (56.0, 12.0)
    elbow = (62.0, 60.0) if near else (64.0, 62.0)
    wrist = (82.0, 82.0) if near else (80.0, 84.0)
    hand = (90.0, 90.0) if near else (88.0, 92.0)

    # the bare arm: shoulder cap down to the wrist, one mask so no joint seam
    bare = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(bare)
    bd.ellipse([sh[0] - 16, sh[1] - 12, sh[0] + 16, sh[1] + 18], fill=255)
    bd.line([sh, elbow], fill=255, width=15)
    bd.line([elbow, wrist], fill=255, width=12)
    bd.ellipse([elbow[0] - 8, elbow[1] - 8, elbow[0] + 8, elbow[1] + 8], fill=255)
    bd.ellipse([wrist[0] - 7, wrist[1] - 7, wrist[0] + 7, wrist[1] + 7], fill=255)
    img.alpha_composite(char_rig._shade(bare, *skin))

    # the jacket sleeve, ending above the elbow where it is rolled back
    cuff = (elbow[0] - 2, elbow[1] - 9)
    sleeve = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(sleeve)
    sd.polygon([(40, 2), (70, 2), (71, 44), (52, 50), (40, 22)], fill=255)
    sd.ellipse([sh[0] - 17, sh[1] - 13, sh[0] + 17, sh[1] + 20], fill=255)
    sd.line([sh, cuff], fill=255, width=17)
    sd.ellipse([sh[0] - 10, sh[1] + 2, sh[0] + 10, sh[1] + 26], fill=255)
    img.alpha_composite(char_rig._shade(sleeve, *shell))
    d = ImageDraw.Draw(img)

    # sleeve folds
    d.line([(46, 18), (45, 44)], fill=JACKET_DEEP + (135,), width=2)
    d.line([(64, 16), (65, 40)], fill=JACKET_LIT + (95,), width=2)
    d.line([(47, 34), (62, 36)], fill=JACKET_DEEP + (90,), width=2)

    # the rolled cuff: a thick band, the Chang Sing stripe along it
    d.ellipse([cuff[0] - 11, cuff[1] - 8, cuff[0] + 11, cuff[1] + 9],
              fill=JACKET_DK + (250,))
    d.arc([cuff[0] - 11, cuff[1] - 8, cuff[0] + 11, cuff[1] + 9], 205, 345,
          fill=SASH + (240,), width=3)
    d.arc([cuff[0] - 11, cuff[1] - 10, cuff[0] + 11, cuff[1] + 7], 205, 345,
          fill=GOLD + (200,), width=1)

    # the glove: palm covered, fingers bare, strap across the back of the hand
    d.ellipse([hand[0] - 10, hand[1] - 9, hand[0] + 9, hand[1] + 9],
              fill=GLOVE + (255,))
    d.ellipse([hand[0] - 8, hand[1] - 7, hand[0] + 3, hand[1] + 4],
              fill=GLOVE_LIT + (150,))
    d.line([(hand[0] - 9, hand[1] + 3), (hand[0] + 5, hand[1] + 6)],
           fill=GLOVE_DK + (240,), width=3)
    d.line([(hand[0] - 9, hand[1] + 1), (hand[0] + 5, hand[1] + 4)],
           fill=SASH + (215,), width=1)
    # wrist strap of the glove
    d.line([(wrist[0] - 5, wrist[1] + 4), (wrist[0] + 4, wrist[1] + 8)],
           fill=GLOVE + (245,), width=4)
    for i in range(4):
        d.line([(hand[0] + 2, hand[1] - 7 + i * 4),
                (hand[0] + 13, hand[1] - 8 + i * 4)],
               fill=skin[2] + (185,), width=2)
    d.line([(hand[0] - 3, hand[1] + 6), (hand[0] + 8, hand[1] + 7)],
           fill=skin[2] + (165,), width=2)

    if not near:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img


def thigh():
    W, H = 46, 86
    img = _limb((W, H), [(10, 2), (36, 2), (37, 46), (33, 84), (12, 84),
                         (8, 46)], JEANS, JEANS_LIT, JEANS_DK)
    d = ImageDraw.Draw(img)
    for x0, x1 in ((16, 18), (31, 29)):
        d.line([(x0, 8), (x1, 80)], fill=JEANS_DK + (110,), width=2)
    d.line([(10, 54), (36, 54)], fill=JEANS_LIT + (85,), width=2)
    # a worn patch at the knee
    d.line([(14, 62), (30, 60)], fill=JEANS_DK + (130,), width=3)
    return img


def shin():
    W, H = 42, 77
    leg = _limb((W, H), [(8, 2), (34, 2), (34, 40), (28, 74), (13, 74),
                         (7, 40)], JEANS, JEANS_LIT, JEANS_DK)
    d = ImageDraw.Draw(leg)
    for x0, x1 in ((15, 17), (28, 26)):
        d.line([(x0, 8), (x1, 64)], fill=JEANS_DK + (105,), width=2)
    # the hem is worn, so it sits above the shoe rather than over it
    d.line([(9, 70), (32, 69)], fill=JEANS_LIT + (150,), width=2)
    return leg


def foot():
    W, H = 48, 30
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(5, 9), (26, 6), (45, 13), (44, 26), (7, 27)], fill=255)
    d.ellipse([1, 7, 20, 26], fill=255)
    img = char_rig._shade(mask, SHOE, SHOE_LIT, (16, 16, 20))
    d = ImageDraw.Draw(img)
    # the pale sole of a canvas street shoe, and the toe cap
    d.rectangle([2, 22, 45, 28], fill=SHOE_SOLE + (250,))
    d.line([(3, 22), (44, 21)], fill=(150, 146, 136, 235), width=1)
    d.line([(9, 11), (27, 8)], fill=SHOE_LIT + (160,), width=2)
    d.line([(31, 12), (42, 15)], fill=SHOE_LIT + (110,), width=2)
    d.arc([26, 5, 46, 24], 300, 30, fill=(28, 26, 32, 230), width=2)
    d.line([(14, 15), (15, 21)], fill=SASH + (200,), width=2)
    return img


RIG_JSON = {
    "pivots": {
        "pelvis": [50, 16],
        "arm_n": [56, 12],
        "arm_f": [91, 12],
        "foot_n": [14, 21],
        "foot_f": [14, 21],
    },
}


def parts():
    return {
        "torso": torso(),
        "pelvis": pelvis(),
        "head": head(),
        "arm_n": arm(True),
        "arm_f": arm(False),
        "thigh_n": thigh(),
        "thigh_f": thigh(),
        "shin_n": shin(),
        "shin_f": shin(),
        "foot_n": foot(),
        "foot_f": foot(),
    }


def write():
    os.makedirs(PARTS, exist_ok=True)
    made = parts()
    for name, img in made.items():
        img.save(os.path.join(PARTS, f"{name}.png"))
    with open(os.path.join(PARTS, "rig.json"), "w", encoding="utf-8") as f:
        json.dump(RIG_JSON, f, indent=2)
        f.write("\n")
    print(f"  eddilee: {len(made)} parts -> art_src/chars/eddilee/parts/")
    return made


def main(argv):
    write()
    if "--sheet" in argv:
        rig = char_rig.load_rig("eddilee")
        poses = ["stance", "breath", "walk_a", "jab", "boot", "hit", "win"]
        cw, ch = 380, 420
        sheet = Image.new("RGBA", (cw * len(poses), ch), (24, 26, 32, 255))
        table = char_rig.poses_for("eddilee")
        for i, p in enumerate(poses):
            img = char_rig.render(rig, table[p])
            sheet.alpha_composite(
                img, (i * cw + (cw - img.width) // 2, ch - img.height))
        os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
        path = os.path.join(ROOT, "artifacts", "eddilee_poses.png")
        sheet.convert("RGB").save(path)
        print(f"  wrote {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
