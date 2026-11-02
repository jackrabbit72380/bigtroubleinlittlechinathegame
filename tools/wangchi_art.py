"""Wang Chi: the fourth fighter painted in code, from the drawing and the still.

The watercolour puts him at a table in a brown fedora, a striped scarf and a
dark shirt with a tie; the film still shows the same hat over a light shirt.
The statue has him stripped to a white shirt in a wide two-sword stance.

So: the fedora and the scarf - the two things that make him Wang Chi at a
glance - over the light grey shirt from the still, with a dark tie in the
collar opening and charcoal trousers. The swords stay out of the rig: the
statue is a display pose, and the character sheet's states use his hands.

Output is what ``char_rig`` and ``bake_char`` expect:

    art_src/chars/wangchi/parts/*.png
    art_src/chars/wangchi/parts/rig.json

Run:  python3 tools/wangchi_art.py [--sheet]
"""

from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import char_rig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "art_src", "chars", "wangchi", "parts")

SKIN = (226, 182, 150)
SKIN_LIT = (248, 214, 184)
SKIN_DK = (172, 124, 94)
SKIN_DEEP = (114, 76, 56)

HAIR = (36, 30, 32)
HAIR_LIT = (74, 64, 66)
HAIR_DK = (16, 14, 18)

HAT = (138, 108, 72)
HAT_LIT = (178, 146, 104)
HAT_DK = (84, 62, 40)
HAT_BAND = (66, 48, 32)

SHIRT = (196, 200, 202)
SHIRT_LIT = (232, 236, 238)
SHIRT_DK = (140, 146, 152)

SCARF_A = (92, 116, 146)
SCARF_A_LIT = (132, 158, 184)
SCARF_A_DK = (52, 70, 94)
SCARF_B = (168, 154, 120)

TROUSER = (64, 66, 76)
TROUSER_LIT = (98, 102, 114)
TROUSER_DK = (34, 36, 44)

TIE = (58, 54, 62)
TIE_LIT = (92, 86, 94)

SHOE = (30, 30, 34)
SHOE_LIT = (58, 58, 64)


def _blank(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _limb(size, pts, base, lit, dark):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    return char_rig._shade(mask, base, lit, dark)


def torso():
    """112 x 132 shirt: open collar, tie, and the scarf draped over it."""
    W, H = 112, 132
    cx = W // 2
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(cx - 26, 12), (cx + 26, 12), (cx + 30, 52), (cx + 26, 80),
               (cx + 30, 100), (cx + 31, 132), (cx - 31, 132), (cx - 30, 100),
               (cx - 26, 80), (cx - 30, 52)], fill=255)
    d.ellipse([cx - 34, 6, cx - 6, 40], fill=255)
    d.ellipse([cx + 6, 6, cx + 34, 40], fill=255)
    d.ellipse([cx - 25, 44, cx + 25, 76], fill=255)          # chest
    img = char_rig._shade(mask, SHIRT, SHIRT_LIT, SHIRT_DK)
    d = ImageDraw.Draw(img)

    # collar opening, with the tie hanging in it
    d.polygon([(cx - 13, 8), (cx + 13, 8), (cx + 5, 42), (cx - 5, 42)],
              fill=SKIN_DK + (215,))
    d.polygon([(cx - 4, 14), (cx + 4, 14), (cx + 6, 30), (cx, 38), (cx - 6, 30)],
              fill=TIE + (255,))
    d.line([(cx - 2, 16), (cx + 2, 16)], fill=TIE_LIT + (170,), width=1)
    # collar points
    d.polygon([(cx - 26, 8), (cx - 9, 10), (cx - 5, 30), (cx - 18, 16)],
              fill=SHIRT_LIT + (245,))
    d.polygon([(cx + 26, 8), (cx + 9, 10), (cx + 5, 30), (cx + 18, 16)],
              fill=SHIRT_DK + (225,))

    # the scarf: a band around the neck and two striped tails down the chest
    scarf = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(scarf)
    sd.polygon([(cx - 18, 8), (cx + 18, 8), (cx + 23, 24), (cx + 10, 30),
                (cx - 10, 30), (cx - 23, 24)], fill=255)
    sd.polygon([(cx - 19, 20), (cx - 8, 26), (cx - 6, 96), (cx - 17, 102),
                (cx - 22, 26)], fill=255)
    sd.polygon([(cx + 6, 26), (cx + 17, 20), (cx + 18, 80), (cx + 7, 88)],
               fill=255)
    img.alpha_composite(char_rig._shade(scarf, SCARF_A, SCARF_A_LIT, SCARF_A_DK))

    # stripes, clipped to the scarf so they follow its shape
    stripes = _blank((W, H))
    st = ImageDraw.Draw(stripes)
    for i in range(-2, 10):
        x = cx - 24 + i * 11
        st.polygon([(x, 0), (x + 6, 0), (x + 3, H), (x - 3, H)],
                   fill=SCARF_B + (238,))
    stripes.putalpha(ImageChops.multiply(stripes.getchannel("A"), scarf))
    img.alpha_composite(stripes)

    # scarf fringe at the hems
    for tail_x, hem in ((cx - 17, 96), (cx + 7, 80)):
        for i in range(3):
            d.line([(tail_x + i * 4, hem), (tail_x + i * 4, hem + 6)],
                   fill=SCARF_A_DK + (220,), width=2)

    # shirt: buttons, pocket, folds
    for y in (52, 68, 84, 100, 116):
        d.ellipse([cx - 2, y, cx + 3, y + 5], fill=SHIRT_DK + (235,))
        d.ellipse([cx - 1, y + 1, cx + 1, y + 3], fill=SHIRT_LIT + (150,))
    d.line([(cx + 14, 56), (cx + 14, 74)], fill=SHIRT_DK + (170,), width=1)
    d.line([(cx + 6, 58), (cx + 22, 58)], fill=SHIRT_DK + (170,), width=1)
    for x0, x1 in ((cx - 24, cx - 20), (cx + 24, cx + 20)):
        d.line([(x0, 46), (x1, 128)], fill=SHIRT_DK + (110,), width=2)
    d.line([(cx - 26, 74), (cx - 12, 78)], fill=SHIRT_DK + (90,), width=2)
    d.line([(cx + 12, 84), (cx + 26, 80)], fill=SHIRT_LIT + (110,), width=2)
    return img


def pelvis():
    """100 x 104: trousers, belt with a plain buckle."""
    W, H = 100, 104
    cx = W // 2
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(cx - 24, 2), (cx + 24, 2), (cx + 26, 34), (cx + 24, 72),
               (cx + 6, 72), (cx + 3, 46), (cx - 3, 46), (cx - 6, 72),
               (cx - 24, 72), (cx - 26, 34)], fill=255)
    img = char_rig._shade(mask, TROUSER, TROUSER_LIT, TROUSER_DK)
    d = ImageDraw.Draw(img)
    # belt
    d.rectangle([cx - 30, 6, cx + 30, 20], fill=(52, 40, 30, 255))
    d.rectangle([cx - 30, 8, cx + 30, 10], fill=(96, 76, 54, 210))
    d.rectangle([cx - 7, 6, cx + 7, 20], outline=(168, 146, 96, 245), width=2)
    d.rectangle([cx - 2, 10, cx + 2, 16], fill=(168, 146, 96, 220))
    # creases
    for x0, x1 in ((cx - 15, cx - 17), (cx + 15, cx + 17)):
        d.line([(x0, 22), (x1, 70)], fill=TROUSER_DK + (120,), width=2)
    d.line([(cx - 22, 44), (cx - 9, 48)], fill=TROUSER_LIT + (90,), width=2)
    d.line([(cx + 9, 56), (cx + 22, 52)], fill=TROUSER_DK + (90,), width=2)
    return img


def head():
    """92 x 108: brown fedora, short black hair, young face."""
    W, H = 92, 108
    cx = W // 2
    img = _blank((W, H))

    neck = Image.new("L", (W, H), 0)
    ImageDraw.Draw(neck).rectangle([cx - 11, 88, cx + 11, H], fill=255)
    img.alpha_composite(char_rig._shade(neck, SKIN_DK, SKIN, SKIN_DEEP))

    # short black hair as the mass the hat sits on
    hair = Image.new("L", (W, H), 0)
    hd = ImageDraw.Draw(hair)
    hd.ellipse([cx - 22, 22, cx + 22, 70], fill=255)
    hd.polygon([(cx - 22, 40), (cx - 24, 60), (cx - 18, 58), (cx - 18, 44)], fill=255)
    hd.polygon([(cx + 22, 40), (cx + 24, 60), (cx + 18, 58), (cx + 18, 44)], fill=255)
    img.alpha_composite(char_rig._shade(hair, HAIR, HAIR_LIT, HAIR_DK))

    face = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(face)
    fd.ellipse([cx - 18, 34, cx + 18, 84], fill=255)
    fd.polygon([(cx - 15, 62), (cx + 15, 62), (cx + 10, 88), (cx, 94),
                (cx - 10, 88)], fill=255)
    img.alpha_composite(char_rig._shade(face, SKIN, SKIN_LIT, SKIN_DK))

    # ears
    for sx in (-1, 1):
        ex = cx + sx * 19
        e = Image.new("L", (W, H), 0)
        ImageDraw.Draw(e).ellipse([ex - 4, 50, ex + 4, 66], fill=255)
        img.alpha_composite(char_rig._shade(e, SKIN, SKIN_LIT, SKIN_DK))
    d = ImageDraw.Draw(img)

    # face
    for sx in (-1, 1):
        ex = cx + sx * 10
        d.line([(ex - 7, 50), (ex + 6, 49)], fill=(48, 36, 30, 245), width=3)
        d.ellipse([ex - 6, 54, ex + 6, 62], fill=(246, 242, 236, 255))
        d.ellipse([ex - 2, 55, ex + 2, 61], fill=(38, 26, 20, 255))
        d.arc([ex - 6, 52, ex + 6, 62], 200, 340, fill=(60, 44, 36, 200), width=1)
        d.line([(ex - 2, 64), (ex - 6, 68)], fill=SKIN_DK + (150,), width=1)
    d.polygon([(cx - 4, 62), (cx + 4, 62), (cx + 2, 74), (cx - 2, 74)],
              fill=SKIN_DK + (130,))
    d.line([(cx + 1, 66), (cx + 4, 72)], fill=SKIN_DEEP + (130,), width=2)
    # a grin: he is the one who is enjoying this
    d.line([(cx - 9, 80), (cx + 9, 79)], fill=(120, 62, 56, 235), width=2)
    d.arc([cx - 9, 75, cx + 9, 87], 15, 165, fill=(120, 62, 56, 200), width=2)
    d.line([(cx - 6, 86), (cx + 6, 85)], fill=SKIN_DK + (120,), width=1)
    # cheekbones
    d.line([(cx - 15, 70), (cx - 11, 76)], fill=SKIN_DK + (90,), width=2)
    d.line([(cx + 15, 70), (cx + 11, 76)], fill=SKIN_DK + (90,), width=2)

    # fedora: brim, then crown with its front dent, then the band
    brim = Image.new("L", (W, H), 0)
    ImageDraw.Draw(brim).ellipse([0, 24, W - 1, 46], fill=255)
    img.alpha_composite(char_rig._shade(brim, HAT, HAT_LIT, HAT_DK))

    crown = Image.new("L", (W, H), 0)
    cd = ImageDraw.Draw(crown)
    cd.polygon([(cx - 21, 4), (cx + 21, 4), (cx + 24, 30), (cx - 24, 30)], fill=255)
    cd.ellipse([cx - 21, 0, cx + 21, 16], fill=255)
    img.alpha_composite(char_rig._shade(crown, HAT, HAT_LIT, HAT_DK))
    d = ImageDraw.Draw(img)
    d.line([(cx - 16, 6), (cx - 4, 10)], fill=HAT_DK + (150,), width=3)
    d.line([(cx + 16, 6), (cx + 4, 10)], fill=HAT_DK + (150,), width=3)
    d.rectangle([cx - 24, 20, cx + 24, 30], fill=HAT_BAND + (255,))
    d.line([(cx - 24, 21), (cx + 24, 21)], fill=(112, 88, 62, 210), width=1)
    # shadow the brim throws across the brow
    shade = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shade).rectangle([cx - 20, 30, cx + 20, 40], fill=140)
    shadow = Image.new("RGBA", (W, H), (40, 26, 18, 0))
    shadow.putalpha(shade)
    img.alpha_composite(shadow)
    return img


def arm(near=True):
    """Shirt sleeve to the cuff, then the hand. One mask, so no joint seam."""
    W, H = 148, 132
    img = _blank((W, H))
    base, lit, dark = (SHIRT, SHIRT_LIT, SHIRT_DK) if near else (
        (150, 154, 158), (184, 188, 192), (104, 110, 116))
    skin = (SKIN, SKIN_LIT, SKIN_DK) if near else (SKIN_DK, SKIN, SKIN_DEEP)
    sh = (56.0, 12.0)
    elbow = (62.0, 60.0) if near else (64.0, 62.0)
    wrist = (82.0, 82.0) if near else (80.0, 84.0)

    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(42, 4), (70, 4), (72, 54), (72, 62), (54, 64), (42, 20)], fill=255)
    d.ellipse([sh[0] - 17, sh[1] - 12, sh[0] + 17, sh[1] + 18], fill=255)
    d.line([elbow, wrist], fill=255, width=14)
    d.ellipse([elbow[0] - 9, elbow[1] - 9, elbow[0] + 9, elbow[1] + 9], fill=255)
    d.ellipse([wrist[0] - 8, wrist[1] - 8, wrist[0] + 8, wrist[1] + 8], fill=255)
    img.alpha_composite(char_rig._shade(mask, base, lit, dark))
    d = ImageDraw.Draw(img)

    # sleeve folds and a turned-back cuff at the wrist
    d.line([(47, 18), (46, 56)], fill=dark + (135,), width=2)
    d.line([(64, 16), (65, 54)], fill=lit + (95,), width=2)
    d.line([(47, 38), (63, 40)], fill=dark + (90,), width=2)
    d.line([(wrist[0] - 9, wrist[1] - 7), (wrist[0] + 6, wrist[1] - 1)],
           fill=dark + (215,), width=3)
    d.line([(wrist[0] - 10, wrist[1] - 9), (wrist[0] + 5, wrist[1] - 3)],
           fill=lit + (170,), width=1)
    d.ellipse([wrist[0] - 4, wrist[1] - 2, wrist[0] + 1, wrist[1] + 3],
              fill=dark + (235,))

    # hand, fingers a little spread
    hx, hy = (90, 90) if near else (88, 92)
    d.ellipse([hx - 9, hy - 9, hx + 9, hy + 9], fill=skin[0] + (255,))
    d.ellipse([hx - 7, hy - 6, hx + 4, hy + 4], fill=skin[1] + (190,))
    for i in range(4):
        d.line([(hx + 2, hy - 7 + i * 4), (hx + 12, hy - 8 + i * 4)],
               fill=skin[2] + (170,), width=2)
    d.line([(hx - 4, hy + 5), (hx + 7, hy + 6)], fill=skin[2] + (160,), width=2)

    if not near:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img


def thigh():
    W, H = 46, 86
    img = _limb((W, H), [(10, 2), (36, 2), (37, 46), (33, 84), (12, 84), (8, 46)],
                TROUSER, TROUSER_LIT, TROUSER_DK)
    d = ImageDraw.Draw(img)
    for x0, x1 in ((16, 18), (31, 29)):
        d.line([(x0, 8), (x1, 80)], fill=TROUSER_DK + (110,), width=2)
    d.line([(10, 54), (36, 54)], fill=TROUSER_LIT + (85,), width=2)
    return img


def shin():
    W, H = 42, 77
    leg = _limb((W, H), [(8, 2), (34, 2), (34, 40), (28, 74), (13, 74), (7, 40)],
                TROUSER, TROUSER_LIT, TROUSER_DK)
    d = ImageDraw.Draw(leg)
    for x0, x1 in ((15, 17), (28, 26)):
        d.line([(x0, 8), (x1, 64)], fill=TROUSER_DK + (105,), width=2)
    d.line([(8, 58), (34, 58)], fill=TROUSER_LIT + (70,), width=2)
    return leg


def foot():
    W, H = 48, 30
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(5, 11), (26, 8), (45, 15), (44, 27), (7, 28)], fill=255)
    d.ellipse([1, 9, 20, 28], fill=255)
    img = char_rig._shade(mask, SHOE, SHOE_LIT, (14, 14, 18))
    d = ImageDraw.Draw(img)
    d.line([(6, 27), (44, 26)], fill=(10, 10, 12, 255), width=2)
    d.line([(9, 13), (26, 10)], fill=SHOE_LIT + (160,), width=2)
    d.line([(30, 14), (42, 17)], fill=SHOE_LIT + (110,), width=2)
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
    print(f"  wangchi: {len(made)} parts -> art_src/chars/wangchi/parts/")
    return made


def main(argv):
    write()
    if "--sheet" in argv:
        rig = char_rig.load_rig("wangchi")
        poses = ["stance", "breath", "walk_a", "jab", "boot", "hit", "win"]
        cw, ch = 380, 420
        sheet = Image.new("RGBA", (cw * len(poses), ch), (24, 26, 32, 255))
        for i, p in enumerate(poses):
            img = char_rig.render(rig, char_rig.poses_for("wangchi")[p])
            sheet.alpha_composite(img, (i * cw + (cw - img.width) // 2, ch - img.height))
        os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
        path = os.path.join(ROOT, "artifacts", "wangchi_poses.png")
        sheet.convert("RGB").save(path)
        print(f"  wrote {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
