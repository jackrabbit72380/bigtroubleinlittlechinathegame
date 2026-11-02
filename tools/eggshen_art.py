"""Egg Shen: the third fighter painted in code, from the statue and the drawing.

The references agree on the costume even though the drawing shows him in a
grey suit and the statue in his working clothes: baggy blue-grey jacket with a
twisted rope belt, a satchel slung across the chest, wide trousers gathered at
the ankle, black cloth shoes, long grey hair, moustache and a small beard.

The jacket and trousers win, because that is what he wears while he is doing
the thing he is in the game to do. The suit's paisley tie survives as the dark
under-shirt at the throat.

Output is what ``char_rig`` and ``bake_char`` expect:

    art_src/chars/eggshen/parts/*.png
    art_src/chars/eggshen/parts/rig.json

Run:  python3 tools/eggshen_art.py [--sheet]
"""

from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import char_rig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "art_src", "chars", "eggshen", "parts")

SKIN = (214, 176, 148)
SKIN_LIT = (236, 204, 176)
SKIN_DK = (160, 116, 90)
SKIN_DEEP = (108, 72, 56)

HAIR = (150, 150, 156)
HAIR_LIT = (186, 186, 192)
HAIR_DK = (94, 94, 102)

JACKET = (88, 100, 114)
JACKET_LIT = (124, 138, 154)
JACKET_DK = (48, 56, 68)

TROUSER = (74, 84, 96)
TROUSER_LIT = (104, 116, 130)
TROUSER_DK = (40, 48, 58)

ROPE = (176, 154, 108)
ROPE_LIT = (214, 194, 152)
ROPE_DK = (108, 90, 56)

SHIRT = (44, 42, 52)
SHOE = (38, 36, 42)
SHOE_LIT = (66, 64, 72)

SATCHEL = (98, 74, 52)
SATCHEL_LIT = (134, 104, 74)
SATCHEL_DK = (58, 42, 28)


def _blank(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _limb(size, pts, base, lit, dark):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    return char_rig._shade(mask, base, lit, dark)


def torso():
    """118 x 132 jacket: stocky, squared shoulders, rope belt, satchel."""
    W, H = 118, 132
    cx = W // 2
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(cx - 30, 12), (cx + 30, 12), (cx + 36, 50), (cx + 30, 78),
               (cx + 36, 100), (cx + 38, 132), (cx - 38, 132), (cx - 36, 100),
               (cx - 30, 78), (cx - 36, 50)], fill=255)
    d.ellipse([cx - 40, 4, cx - 4, 48], fill=255)
    d.ellipse([cx + 4, 4, cx + 40, 48], fill=255)
    d.ellipse([cx - 28, 40, cx + 28, 74], fill=255)          # belly
    img = char_rig._shade(mask, JACKET, JACKET_LIT, JACKET_DK)
    d = ImageDraw.Draw(img)

    # dark shirt in the V of the jacket, with the tie's knot
    d.polygon([(cx - 14, 10), (cx + 14, 10), (cx + 6, 44), (cx - 6, 44)],
              fill=SHIRT + (255,))
    d.polygon([(cx - 4, 42), (cx + 4, 42), (cx, 62)], fill=(62, 60, 74, 255))
    # jacket lapels over the shirt
    d.polygon([(cx - 30, 10), (cx - 12, 12), (cx - 4, 46), (cx - 22, 34)],
              fill=JACKET_LIT + (235,))
    d.polygon([(cx + 30, 10), (cx + 12, 12), (cx + 4, 46), (cx + 22, 34)],
              fill=JACKET_DK + (215,))

    # the satchel strap, shoulder to opposite hip
    d.line([(cx + 26, 16), (cx - 22, 84)], fill=SATCHEL_DK + (235,), width=9)
    d.line([(cx + 26, 16), (cx - 22, 84)], fill=SATCHEL + (235,), width=6)
    # the bag itself on the near hip
    d.password = None
    d.polygon([(cx - 40, 74), (cx - 16, 68), (cx - 12, 104), (cx - 38, 108)],
              fill=SATCHEL + (255,))
    d.line([(cx - 38, 80), (cx - 15, 75)], fill=SATCHEL_LIT + (200,), width=2)
    d.polygon([(cx - 32, 74), (cx - 18, 71), (cx - 18, 78), (cx - 32, 81)],
              fill=SATCHEL_DK + (255,))

    # twisted rope belt: two offset strands with a knot
    for y0 in (86, 92):
        for i in range(9):
            x = cx - 34 + i * 8
            d.line([(x, y0), (x + 4, y0 + 3), (x + 8, y0)],
                   fill=ROPE + (250,), width=3)
    d.line([(cx - 36, 88), (cx + 34, 88)], fill=ROPE_LIT + (170,), width=1)
    d.ellipse([cx - 6, 84, cx + 8, 98], fill=ROPE + (255,))
    d.ellipse([cx - 2, 87, cx + 4, 95], fill=ROPE_DK + (255,))
    d.line([(cx + 6, 96), (cx + 12, 116)], fill=ROPE + (240,), width=4)

    # folds and buttons
    for x0, x1 in ((cx - 28, cx - 24), (cx - 16, cx - 14), (cx + 16, cx + 14),
                   (cx + 28, cx + 24)):
        d.line([(x0, 48), (x1, 128)], fill=JACKET_DK + (105,), width=2)
    for y in (60, 74):
        d.ellipse([cx + 12, y, cx + 18, y + 6], fill=JACKET_DK + (230,))
    return img


def pelvis():
    """100 x 104: baggy trousers with the jacket hem over them."""
    W, H = 100, 104
    cx = W // 2
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(cx - 30, 2), (cx + 30, 2), (cx + 34, 40), (cx + 30, 102),
               (cx + 6, 102), (cx + 2, 54), (cx - 2, 54), (cx - 6, 102),
               (cx - 30, 102), (cx - 34, 40)], fill=255)
    img = char_rig._shade(mask, TROUSER, TROUSER_LIT, TROUSER_DK)
    d = ImageDraw.Draw(img)
    # jacket hem hanging over the waist
    hem = _blank((W, H))
    hd = ImageDraw.Draw(hem)
    hd.polygon([(cx - 34, 0), (cx + 34, 0), (cx + 30, 22), (cx - 30, 22)], fill=255)
    hem.putalpha(ImageChops.multiply(hem.getchannel("A"), mask))
    img.alpha_composite(char_rig._shade(hem.getchannel("A"), JACKET, JACKET_LIT, JACKET_DK))
    d = ImageDraw.Draw(img)
    d.line([(cx - 30, 22), (cx + 30, 22)], fill=JACKET_DK + (215,), width=2)
    for x0, x1 in ((cx - 18, cx - 20), (cx + 18, cx + 20)):
        d.line([(x0, 26), (x1, 98)], fill=TROUSER_DK + (110,), width=2)
    return img


def head():
    """92 x 108: grey hair with a receding hairline, moustache, goatee.

    The first version painted a bald dome in skin over the hair and a moustache
    in light grey, which at sprite size read as a white bird sitting on his
    face. Hair is drawn as a cap that covers the crown and the beard stays small.
    """
    W, H = 92, 108
    cx = W // 2
    img = _blank((W, H))

    neck = Image.new("L", (W, H), 0)
    ImageDraw.Draw(neck).rectangle([cx - 12, 92, cx + 12, H], fill=255)
    img.alpha_composite(char_rig._shade(neck, SKIN_DK, SKIN, SKIN_DEEP))

    # long grey hair down the back and sides
    back = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(back)
    bd.ellipse([cx - 27, 12, cx + 27, 74], fill=255)
    bd.polygon([(cx - 26, 38), (cx - 33, 94), (cx - 18, 90), (cx - 16, 50)], fill=255)
    bd.polygon([(cx + 26, 38), (cx + 33, 94), (cx + 18, 90), (cx + 16, 50)], fill=255)
    img.alpha_composite(char_rig._shade(back, HAIR, HAIR_LIT, HAIR_DK))

    face = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(face)
    fd.ellipse([cx - 21, 28, cx + 21, 84], fill=255)
    fd.polygon([(cx - 17, 64), (cx + 17, 64), (cx + 12, 90), (cx, 96),
                (cx - 12, 90)], fill=255)
    img.alpha_composite(char_rig._shade(face, SKIN, SKIN_LIT, SKIN_DK))

    # hair as a cap over the crown, with the forehead cut back into it so the
    # hairline is receding rather than painted on
    cap = Image.new("L", (W, H), 0)
    cd = ImageDraw.Draw(cap)
    cd.ellipse([cx - 23, 16, cx + 23, 62], fill=255)
    cd.polygon([(cx - 23, 40), (cx - 23, 74), (cx - 28, 70), (cx - 28, 36)], fill=255)
    cd.polygon([(cx + 23, 40), (cx + 23, 74), (cx + 28, 70), (cx + 28, 36)], fill=255)
    forehead = Image.new("L", (W, H), 0)
    ImageDraw.Draw(forehead).ellipse([cx - 16, 30, cx + 16, 58], fill=255)
    cap = ImageChops.subtract(cap, forehead)
    cap = ImageChops.multiply(cap, Image.new("L", (W, H), 255))
    img.alpha_composite(char_rig._shade(cap, HAIR, HAIR_LIT, HAIR_DK))
    d = ImageDraw.Draw(img)

    # face
    for sx in (-1, 1):
        ex = cx + sx * 11
        d.line([(ex - 8, 50), (ex + 7, 48)], fill=(64, 58, 56, 240), width=3)
        d.ellipse([ex - 6, 52, ex + 6, 60], fill=(244, 238, 230, 255))
        d.ellipse([ex - 2, 53, ex + 2, 59], fill=(52, 36, 28, 255))
        d.line([(ex - 3, 63), (ex - 8, 67)], fill=SKIN_DK + (160,), width=1)
        d.line([(ex - 7, 42), (ex + 7, 41)], fill=SKIN_DK + (110,), width=1)
    d.polygon([(cx - 5, 62), (cx + 5, 62), (cx + 3, 74), (cx - 3, 74)],
              fill=SKIN_DK + (150,))
    d.line([(cx + 2, 66), (cx + 5, 72)], fill=SKIN_DEEP + (140,), width=2)
    d.line([(cx - 7, 84), (cx + 7, 84)], fill=(96, 62, 56, 235), width=2)

    # a thin moustache and a small goatee, not a white mask
    d.polygon([(cx - 9, 78), (cx, 76), (cx + 9, 78), (cx, 82)], fill=HAIR_DK + (255,))
    d.polygon([(cx - 5, 88), (cx + 5, 88), (cx + 3, 100), (cx - 3, 100)],
              fill=HAIR_DK + (250,))
    d.line([(cx - 8, 90), (cx - 5, 98)], fill=HAIR + (200,), width=2)
    d.line([(cx + 8, 90), (cx + 5, 98)], fill=HAIR + (200,), width=2)
    return img


def arm(near=True):
    """Wide sleeve, rope cuff, open hand. One mask, so the joints stay smooth."""
    W, H = 148, 132
    img = _blank((W, H))
    base, lit, dark = (JACKET, JACKET_LIT, JACKET_DK) if near else (
        (62, 70, 80), (92, 102, 114), (34, 40, 48))
    skin = (SKIN, SKIN_LIT, SKIN_DK) if near else (SKIN_DK, SKIN, SKIN_DEEP)
    sh = (54.0, 12.0)
    elbow = (60.0, 60.0) if near else (62.0, 62.0)
    wrist = (80.0, 82.0) if near else (78.0, 84.0)

    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    # a wide, square sleeve: the statue's sleeve is nearly a rectangle
    d.polygon([(37, 4), (71, 4), (72, 56), (70, 62), (50, 64), (37, 20)], fill=255)
    d.ellipse([sh[0] - 19, sh[1] - 13, sh[0] + 19, sh[1] + 18], fill=255)
    d.line([elbow, wrist], fill=255, width=16)
    d.ellipse([elbow[0] - 10, elbow[1] - 10, elbow[0] + 10, elbow[1] + 10], fill=255)
    d.ellipse([wrist[0] - 9, wrist[1] - 9, wrist[0] + 9, wrist[1] + 9], fill=255)
    img.alpha_composite(char_rig._shade(mask, base, lit, dark))
    d = ImageDraw.Draw(img)

    # sleeve folds
    d.line([(45, 20), (44, 60)], fill=dark + (135,), width=2)
    d.line([(65, 18), (66, 58)], fill=lit + (95,), width=2)
    d.line([(46, 40), (64, 42)], fill=dark + (90,), width=2)

    # the sleeve is gathered into a rope cuff, like the belt
    for i in range(3):
        d.line([(wrist[0] - 8, wrist[1] - 4 + i * 3), (wrist[0] + 6, wrist[1] - 1 + i * 3)],
               fill=ROPE + (245,), width=3)
    d.line([(wrist[0] - 8, wrist[1] - 6), (wrist[0] + 6, wrist[1] - 3)],
           fill=ROPE_LIT + (170,), width=1)

    # open hand, fingers spread a little the way the statue holds them
    hx, hy = (90, 92) if near else (88, 94)
    d.ellipse([hx - 10, hy - 9, hx + 10, hy + 9], fill=skin[0] + (255,))
    d.ellipse([hx - 8, hy - 6, hx + 5, hy + 4], fill=skin[1] + (200,))
    for i in range(4):
        d.line([(hx + 3, hy - 7 + i * 4), (hx + 13, hy - 8 + i * 4)],
               fill=skin[2] + (170,), width=2)
    d.line([(hx - 4, hy + 6), (hx + 8, hy + 7)], fill=skin[2] + (160,), width=2)

    if not near:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img


def thigh():
    W, H = 54, 86
    img = _limb((W, H), [(12, 2), (42, 2), (44, 46), (40, 84), (14, 84), (9, 46)],
                TROUSER, TROUSER_LIT, TROUSER_DK)
    d = ImageDraw.Draw(img)
    for x0, x1 in ((18, 20), (36, 34)):
        d.line([(x0, 8), (x1, 80)], fill=TROUSER_DK + (110,), width=2)
    d.line([(12, 56), (42, 56)], fill=TROUSER_DK + (90,), width=2)
    return img


def shin():
    W, H = 46, 77
    leg = _limb((W, H), [(9, 2), (37, 2), (38, 40), (32, 74), (14, 74), (8, 40)],
                TROUSER, TROUSER_LIT, TROUSER_DK)
    d = ImageDraw.Draw(leg)
    for x0, x1 in ((16, 18), (31, 29)):
        d.line([(x0, 8), (x1, 64)], fill=TROUSER_DK + (105,), width=2)
    # the trousers are gathered and bound at the ankle
    for i in range(3):
        d.line([(9, 60 + i * 4), (36, 60 + i * 4)], fill=ROPE + (225,), width=3)
    return leg


def foot():
    W, H = 48, 30
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(5, 10), (26, 7), (45, 15), (44, 28), (7, 29)], fill=255)
    d.ellipse([1, 8, 20, 29], fill=255)
    img = char_rig._shade(mask, SHOE, SHOE_LIT, (20, 18, 22))
    d = ImageDraw.Draw(img)
    d.line([(6, 28), (44, 27)], fill=(16, 14, 16, 255), width=2)
    d.line([(9, 12), (26, 9)], fill=SHOE_LIT + (150,), width=2)
    return img


RIG_JSON = {
    "pivots": {
        "pelvis": [50, 16],
        "arm_n": [54, 12],
        "arm_f": [93, 12],
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
    print(f"  eggshen: {len(made)} parts -> art_src/chars/eggshen/parts/")
    return made


def main(argv):
    write()
    if "--sheet" in argv:
        rig = char_rig.load_rig("eggshen")
        poses = ["stance", "breath", "walk_a", "jab", "boot", "hit", "win"]
        cw, ch = 380, 420
        sheet = Image.new("RGBA", (cw * len(poses), ch), (24, 26, 32, 255))
        for i, p in enumerate(poses):
            img = char_rig.render(rig, char_rig.poses_for("eggshen")[p])
            sheet.alpha_composite(img, (i * cw + (cw - img.width) // 2, ch - img.height))
        os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
        path = os.path.join(ROOT, "artifacts", "eggshen_poses.png")
        sheet.convert("RGB").save(path)
        print(f"  wrote {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
