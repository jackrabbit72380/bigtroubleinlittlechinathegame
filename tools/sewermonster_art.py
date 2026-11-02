"""Sewer Monster: the half-mummified wild man that guards Lo Pan's drains.

The reference set is the comic's Chinese Wild Man - a gaunt, hunched thing with
a reddish mane, a desiccated face full of long teeth, long arms ending in
talons, and the remains of an old robe hanging off one shoulder - plus the resin
sculpture's low, animal crouch. He is painted in code like the rest of the
painted roster, with two differences: he is authored taller than everyone else
(see TARGET_BY_CHAR in tools/bake_char.py) and his stance is the only one on the
roster that is genuinely hunched.

Rig contract is Wang Chi's set - one bent piece per arm, thigh/shin/foot pairs,
a pelvis and a torso:

    art_src/chars/sewermonster/parts/*.png
    art_src/chars/sewermonster/parts/rig.json

Run:  python3 tools/sewermonster_art.py [--sheet]
"""

from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import char_rig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "art_src", "chars", "sewermonster", "parts")

# Desiccated flesh: grey-bone rather than pink, so the red mane and the eye are
# the only warm things on him and the eye is what you notice.
FLESH = (166, 162, 142)
FLESH_LIT = (206, 202, 180)
FLESH_DK = (118, 114, 98)
FLESH_DEEP = (72, 70, 58)

# Exposed muscle where the body has rotted through.
SINEW = (122, 66, 60)
SINEW_DK = (78, 38, 36)

# The mane and the patches of hair: dark red-brown, matted.
MANE = (104, 62, 44)
MANE_LIT = (146, 92, 64)
MANE_DK = (58, 32, 24)

# What is left of the robe: a sodden indigo that has been in the water for
# centuries, so it is closer to a stain than a colour.
ROBE = (56, 62, 84)
ROBE_LIT = (86, 92, 118)
ROBE_DK = (30, 34, 48)

BONE = (216, 208, 182)
BONE_DK = (138, 130, 108)
TEETH = (238, 232, 214)
EYE = (226, 196, 96)
EYE_DK = (128, 96, 30)
PUPIL = (28, 20, 14)
MOUTH = (60, 24, 26)


def _blank(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _limb(size, pts, base, lit, dark):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    return char_rig._shade(mask, base, lit, dark)


def _matted(img, box, colour, lit, dark, seed=1):
    """Paint matted hair inside a box, clipped to whatever is already drawn."""
    x0, y0, x1, y1 = box
    lay = _blank(img.size)
    d = ImageDraw.Draw(lay)
    x = x0
    i = seed
    while x < x1:
        spread = 3 + (i * 7) % 5
        d.line([(x, y0 + (i * 11) % 9), (x + (i % 3) - 1, y1)],
               fill=colour + (232,), width=spread)
        x += 5 + (i * 3) % 4
        i += 1
    lay.putalpha(ImageChops.multiply(lay.getchannel("A"),
                                     img.getchannel("A")))
    out = img.copy()
    shaded = char_rig._shade(lay.getchannel("A"), colour, lit, dark)
    shaded.putalpha(ImageChops.multiply(shaded.getchannel("A"),
                                        lay.getchannel("A")))
    out.alpha_composite(shaded)
    return out


def torso():
    """120 x 140: sunken chest, ribs, a mane over the shoulders, robe rags."""
    W, H = 120, 140
    cx = W // 2
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    # broad at the shoulders, collapsed at the waist
    d.polygon([(cx - 34, 16), (cx + 34, 16), (cx + 30, 46), (cx + 22, 74),
               (cx + 20, 104), (cx + 24, 140), (cx - 24, 140), (cx - 20, 104),
               (cx - 22, 74), (cx - 30, 46)], fill=255)
    d.ellipse([cx - 40, 8, cx - 10, 38], fill=255)
    d.ellipse([cx + 10, 8, cx + 40, 38], fill=255)
    d.ellipse([cx - 22, 40, cx + 22, 74], fill=255)
    img = char_rig._shade(mask, FLESH, FLESH_LIT, FLESH_DK)
    d = ImageDraw.Draw(img)

    # the ribcage, and the torn side where the muscle shows
    for i, y in enumerate((52, 60, 68, 76)):
        d.arc([cx - 20, y - 6, cx + 20, y + 10], 200, 340,
              fill=FLESH_DEEP + (150,), width=2)
    d.polygon([(cx + 8, 48), (cx + 26, 54), (cx + 22, 88), (cx + 10, 80)],
              fill=SINEW + (210,))
    for y in range(54, 86, 6):
        d.line([(cx + 11, y), (cx + 23, y + 2)], fill=SINEW_DK + (220,), width=1)
    d.line([(cx - 2, 46), (cx - 4, 96)], fill=FLESH_DEEP + (170,), width=2)
    d.line([(cx - 14, 58), (cx - 8, 86)], fill=FLESH_LIT + (110,), width=2)

    # what is left of the robe: a sodden wrap from one shoulder
    robe = Image.new("L", (W, H), 0)
    rd = ImageDraw.Draw(robe)
    rd.polygon([(cx - 34, 18), (cx - 6, 12), (cx - 10, 52), (cx - 16, 92),
                (cx - 26, 132), (cx - 34, 138), (cx - 30, 60)], fill=255)
    rd.polygon([(cx + 20, 96), (cx + 30, 100), (cx + 26, 140), (cx + 14, 138)],
               fill=255)
    img.alpha_composite(char_rig._shade(robe, ROBE, ROBE_LIT, ROBE_DK))
    d = ImageDraw.Draw(img)
    for x0, y0, x1, y1 in ((cx - 30, 30, cx - 34, 90), (cx - 20, 66, cx - 26, 126)):
        d.line([(x0, y0), (x1, y1)], fill=ROBE_DK + (140,), width=2)
    # the ragged hem
    for i in range(5):
        x = cx - 34 + i * 4
        d.line([(x, 130), (x + 1, 140)], fill=ROBE_DK + (210,), width=2)
    # a rope belt end hanging from the wrap
    d.line([(cx - 26, 96), (cx - 22, 122)], fill=(96, 82, 52, 235), width=3)

    # the mane over both shoulders
    img = _matted(img, (cx - 40, 4, cx - 12, 42), MANE, MANE_LIT, MANE_DK, 2)
    img = _matted(img, (cx + 12, 4, cx + 40, 40), MANE, MANE_LIT, MANE_DK, 5)
    return img


def pelvis():
    """104 x 110: hips under a torn robe skirt, matted hair at the thighs."""
    W, H = 104, 110
    cx = W // 2
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(cx - 26, 2), (cx + 26, 2), (cx + 30, 36), (cx + 24, 78),
               (cx + 6, 78), (cx + 3, 48), (cx - 3, 48), (cx - 6, 78),
               (cx - 24, 78), (cx - 30, 36)], fill=255)
    img = char_rig._shade(mask, FLESH, FLESH_LIT, FLESH_DK)
    d = ImageDraw.Draw(img)

    # the robe skirt, ragged and uneven
    robe = Image.new("L", (W, H), 0)
    rd = ImageDraw.Draw(robe)
    rd.polygon([(cx - 30, 4), (cx + 30, 4), (cx + 28, 44), (cx + 20, 96),
                (cx + 8, 84), (cx + 2, 100), (cx - 6, 82), (cx - 14, 98),
                (cx - 22, 80), (cx - 28, 40)], fill=255)
    img.alpha_composite(char_rig._shade(robe, ROBE, ROBE_LIT, ROBE_DK))
    d = ImageDraw.Draw(img)
    d.line([(cx - 28, 22), (cx + 28, 20)], fill=(96, 82, 52, 240), width=4)
    for i in range(6):
        x = cx - 26 + i * 9
        d.line([(x, 26), (x + 2, 92)], fill=ROBE_DK + (130,), width=2)
    return img


def head():
    """100 x 120: a desiccated face, one eye lit, long teeth, a full mane."""
    W, H = 100, 120
    cx = W // 2
    img = _blank((W, H))

    neck = Image.new("L", (W, H), 0)
    ImageDraw.Draw(neck).polygon([(cx - 13, 96), (cx + 13, 96),
                                  (cx + 15, H), (cx - 15, H)], fill=255)
    img.alpha_composite(char_rig._shade(neck, FLESH_DK, FLESH, FLESH_DEEP))

    # skull: tall cranium, heavy brow, jaw that is mostly teeth
    face = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(face)
    fd.ellipse([cx - 21, 26, cx + 21, 74], fill=255)
    fd.polygon([(cx - 20, 44), (cx - 18, 78), (cx - 10, 92), (cx + 10, 92),
                (cx + 18, 78), (cx + 20, 44)], fill=255)
    fd.polygon([(cx - 12, 70), (cx + 12, 70), (cx + 9, 96), (cx - 9, 96)],
               fill=255)
    img.alpha_composite(char_rig._shade(face, FLESH, FLESH_LIT, FLESH_DK))

    img = _matted(img, (cx - 34, 2, cx + 34, 34), MANE, MANE_LIT, MANE_DK, 1)
    img = _matted(img, (cx - 42, 12, cx - 22, 74), MANE, MANE_LIT, MANE_DK, 4)
    img = _matted(img, (cx + 22, 12, cx + 42, 74), MANE, MANE_LIT, MANE_DK, 7)
    d = ImageDraw.Draw(img)

    # brow ridge, then the sockets
    d.line([(cx - 18, 44), (cx - 4, 40)], fill=FLESH_DEEP + (215,), width=4)
    d.line([(cx + 18, 44), (cx + 4, 40)], fill=FLESH_DEEP + (215,), width=4)
    d.ellipse([cx - 17, 44, cx - 3, 56], fill=FLESH_DEEP + (235,))
    d.ellipse([cx + 3, 44, cx + 17, 56], fill=FLESH_DEEP + (235,))
    # one eye burns, the other socket is dead
    d.ellipse([cx + 5, 47, cx + 15, 55], fill=EYE + (255,))
    d.ellipse([cx + 9, 48, cx + 13, 53], fill=PUPIL + (255,))
    d.arc([cx + 4, 46, cx + 16, 56], 190, 350, fill=EYE_DK + (220,), width=1)
    d.line([(cx - 14, 50), (cx - 6, 51)], fill=FLESH_DK + (170,), width=1)

    # nose: two slits
    d.polygon([(cx - 4, 58), (cx + 4, 58), (cx + 2, 68), (cx - 2, 68)],
              fill=FLESH_DEEP + (200,))
    d.line([(cx - 6, 68), (cx - 3, 67)], fill=SINEW_DK + (170,), width=1)
    d.line([(cx + 6, 68), (cx + 3, 67)], fill=SINEW_DK + (170,), width=1)

    # the mouth: wide, dark, with the long teeth the reference gives him
    d.polygon([(cx - 13, 74), (cx + 13, 74), (cx + 9, 88), (cx - 9, 88)],
              fill=MOUTH + (245,))
    for i, x in enumerate((cx - 11, cx - 6, cx - 1, cx + 4, cx + 9)):
        drop = 8 + (i % 2) * 3
        d.polygon([(x - 2, 74), (x + 2, 74), (x, 74 + drop)],
                  fill=TEETH + (250,))
    for i, x in enumerate((cx - 8, cx - 3, cx + 2, cx + 7)):
        d.polygon([(x - 2, 88), (x + 2, 88), (x, 86 - 2 - (i % 2) * 2)],
                  fill=BONE + (245,))
    # jaw, cheekbone, and the dried muscle at the temple
    d.line([(cx - 16, 80), (cx - 8, 92)], fill=FLESH_DK + (200,), width=2)
    d.line([(cx + 16, 80), (cx + 8, 92)], fill=FLESH_DK + (200,), width=2)
    d.line([(cx - 19, 62), (cx - 13, 68)], fill=SINEW + (160,), width=2)
    d.line([(cx + 19, 62), (cx + 13, 68)], fill=SINEW + (160,), width=2)
    # an ear, pointed, where a man's would be
    d.polygon([(cx + 21, 50), (cx + 30, 44), (cx + 28, 60), (cx + 21, 62)],
              fill=FLESH_DK + (245,))
    return img


def arm(near=True):
    """168 x 150: a long sinewy arm, matted hair, three talons at the hand."""
    W, H = 168, 150
    img = _blank((W, H))
    flesh = (FLESH, FLESH_LIT, FLESH_DK) if near else (FLESH_DK, FLESH, FLESH_DEEP)
    sh = (62.0, 14.0)
    elbow = (66.0, 78.0) if near else (70.0, 80.0)
    wrist = (92.0, 108.0) if near else (88.0, 110.0)
    hand = (100.0, 118.0) if near else (96.0, 120.0)

    bare = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(bare)
    bd.ellipse([sh[0] - 20, sh[1] - 14, sh[0] + 20, sh[1] + 22], fill=255)
    bd.line([sh, elbow], fill=255, width=18)
    bd.ellipse([elbow[0] - 11, elbow[1] - 11, elbow[0] + 11, elbow[1] + 11],
               fill=255)
    bd.line([elbow, wrist], fill=255, width=14)
    bd.ellipse([wrist[0] - 8, wrist[1] - 8, wrist[0] + 8, wrist[1] + 8], fill=255)
    bd.ellipse([hand[0] - 10, hand[1] - 9, hand[0] + 10, hand[1] + 10], fill=255)
    img.alpha_composite(char_rig._shade(bare, *flesh))
    d = ImageDraw.Draw(img)

    # stringy muscle down the forearm
    d.line([(elbow[0] + 4, elbow[1] + 6), (wrist[0] - 2, wrist[1] - 6)],
           fill=FLESH_DEEP + (135,), width=2)
    d.line([(sh[0] + 6, sh[1] + 20), (elbow[0] + 6, elbow[1] - 8)],
           fill=FLESH_LIT + (110,), width=3)

    # matted hair over the upper arm
    img = _matted(img, (int(sh[0] - 22), int(sh[1] + 4),
                        int(elbow[0] + 2), int(elbow[1] - 10)),
                  MANE, MANE_LIT, MANE_DK, 3 if near else 6)
    d = ImageDraw.Draw(img)

    # talons: three long claws off the hand, curving down and forward
    for dx, dy, length in ((-7, 2, 16), (-1, 4, 21), (6, 3, 18)):
        bx, by = hand[0] + dx, hand[1] + dy
        tip = (bx + 4, by + length)
        d.polygon([(bx - 3, by), (bx + 3, by), (tip[0] + 1, tip[1]),
                   (tip[0] - 1, tip[1] - 2)], fill=BONE + (250,))
        d.line([(bx, by + 2), (tip[0], tip[1] - 2)], fill=BONE_DK + (200,),
               width=1)
    # a thumb claw, set back
    d.polygon([(hand[0] - 8, hand[1] - 2), (hand[0] - 12, hand[1] - 8),
               (hand[0] - 4, hand[1] + 2)], fill=BONE + (245,))

    if not near:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img


def thigh():
    W, H = 50, 84
    img = _limb((W, H), [(10, 2), (38, 2), (40, 44), (34, 82), (12, 82),
                         (8, 44)], FLESH, FLESH_LIT, FLESH_DK)
    img = _matted(img, (8, 4, 40, 40), MANE, MANE_LIT, MANE_DK, 4)
    d = ImageDraw.Draw(img)
    d.line([(16, 50), (20, 78)], fill=FLESH_DEEP + (130,), width=2)
    d.line([(30, 52), (27, 76)], fill=SINEW + (120,), width=2)
    return img


def shin():
    W, H = 46, 76
    leg = _limb((W, H), [(9, 2), (37, 2), (34, 40), (28, 72), (13, 72),
                         (8, 40)], FLESH, FLESH_LIT, FLESH_DK)
    d = ImageDraw.Draw(leg)
    for x0, x1 in ((16, 18), (30, 28)):
        d.line([(x0, 8), (x1, 62)], fill=FLESH_DEEP + (120,), width=2)
    # the ankle bone, sharp under the skin
    d.ellipse([14, 58, 22, 68], outline=FLESH_DK + (200,), width=2)
    d.ellipse([25, 60, 32, 69], outline=FLESH_DK + (170,), width=2)
    return leg


def foot():
    """58 x 32: a splayed clawed foot, toes gripping the stone."""
    W, H = 58, 32
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(6, 10), (30, 6), (46, 12), (48, 26), (8, 28)], fill=255)
    d.ellipse([2, 8, 24, 28], fill=255)
    img = char_rig._shade(mask, FLESH, FLESH_LIT, FLESH_DK)
    d = ImageDraw.Draw(img)
    # three toes with claws, and a heel spur
    for i, x in enumerate((32, 40, 48)):
        d.ellipse([x - 4, 16, x + 4, 26], fill=FLESH_DK + (235,))
        d.polygon([(x - 3, 16), (x + 3, 16), (x + 6, 27 - i * 2), (x + 2, 26)],
                  fill=BONE + (248,))
    d.polygon([(6, 12), (10, 4), (14, 14)], fill=BONE + (235,))
    d.line([(10, 24), (46, 23)], fill=FLESH_DEEP + (170,), width=2)
    d.line([(12, 12), (28, 9)], fill=FLESH_LIT + (150,), width=2)
    return img


RIG_JSON = {
    "pivots": {
        "pelvis": [52, 18],
        "arm_n": [62, 14],
        "arm_f": [106, 14],
        "foot_n": [16, 20],
        "foot_f": [16, 20],
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
    print(f"  sewermonster: {len(made)} parts -> art_src/chars/sewermonster/parts/")
    return made


def main(argv):
    write()
    if "--sheet" in argv:
        rig = char_rig.load_rig("sewermonster")
        poses = ["stance", "breath", "walk_a", "jab", "boot", "hit", "win"]
        cw, ch = 400, 440
        sheet = Image.new("RGBA", (cw * len(poses), ch), (18, 24, 22, 255))
        table = char_rig.poses_for("sewermonster")
        for i, p in enumerate(poses):
            img = char_rig.render(rig, table[p])
            sheet.alpha_composite(
                img, (i * cw + (cw - img.width) // 2, ch - img.height))
        os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
        path = os.path.join(ROOT, "artifacts", "sewermonster_poses.png")
        sheet.convert("RGB").save(path)
        print(f"  wrote {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
