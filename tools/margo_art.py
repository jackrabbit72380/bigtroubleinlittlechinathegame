"""Margo: the reporter who will not take "naive" for an answer.

The comic panel gives the whole look: a mass of auburn curls, a blue denim
jacket open over a grey marl blouse with the sleeves pushed up, dark trousers,
and a camera flash gun in both hands. For a fighter the flash hangs off her
shoulder strap instead, so both hands stay free for the palm strikes and the
pen: a press badge on the lapel, a satchel at the hip, a wrist recorder with its
little red light, and boots with something solid under them.

Rig contract is the women's set (a hanging arm cut as one piece, like Gracie's):

    art_src/chars/margo/parts/*.png
    art_src/chars/margo/parts/rig.json

Run:  python3 tools/margo_art.py [--sheet]
"""

from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import char_rig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "art_src", "chars", "margo", "parts")

SKIN = (238, 198, 170)
SKIN_LIT = (252, 222, 198)
SKIN_DK = (190, 142, 118)
SKIN_DEEP = (128, 88, 72)

# Auburn curls: the one warm colour on her, so it carries the silhouette.
HAIR = (128, 74, 46)
HAIR_LIT = (172, 108, 66)
HAIR_DK = (74, 40, 26)

# Denim jacket, washed pale at the seams.
DENIM = (76, 98, 140)
DENIM_LIT = (112, 138, 180)
DENIM_DK = (44, 60, 92)

# Grey marl blouse.
BLOUSE = (170, 170, 174)
BLOUSE_LIT = (206, 206, 210)
BLOUSE_DK = (120, 120, 126)

PANTS = (60, 60, 70)
PANTS_LIT = (94, 94, 106)
PANTS_DK = (34, 34, 42)

BOOT = (52, 44, 40)
BOOT_LIT = (88, 74, 64)
BOOT_DK = (28, 24, 22)
SOLE = (36, 34, 36)

STRAP = (62, 44, 34)
STRAP_LIT = (98, 72, 54)
BAG = (78, 56, 42)
BAG_LIT = (112, 84, 62)

BADGE = (238, 236, 226)
BADGE_RED = (188, 52, 48)
LENS = (196, 206, 216)
LED = (216, 62, 52)


def _blank(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _limb(size, pts, base, lit, dark):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    return char_rig._shade(mask, base, lit, dark)


def _curls(img, box, colour, lit, dark, seed=1, clip=True):
    """A mass of curls: overlapping volumes in one mask, shaded once.

    Drawing a curl at a time left the pale body showing between them, which read
    as stripes; the mass is one shape here and the curls are only its outline.
    """
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([x0 + w * 0.1, y0, x1 - w * 0.1, y0 + h * 0.75], fill=255)
    i = seed
    step = max(7, w // 5)
    x = x0
    while x <= x1:
        r = max(5, int(min(w, h) * (0.16 + 0.10 * ((i * 7) % 4) / 3.0)))
        y = y0 + h * 0.35 + (i * 13) % max(1, int(h * 0.4))
        md.ellipse([x - r, y - r, x + r, y + r], fill=255)
        x += step
        i += 1
    # the ends, hanging past the shoulders
    for sx in (x0, x1):
        r = max(6, int(min(w, h) * 0.18))
        md.ellipse([sx - r, y1 - r * 1.6, sx + r, y1 + r * 0.4], fill=255)
    if clip:
        mask = ImageChops.multiply(mask, img.getchannel("A"))
    out = img.copy()
    shaded = char_rig._shade(mask, colour, lit, dark)
    shaded.putalpha(ImageChops.multiply(shaded.getchannel("A"), mask))
    out.alpha_composite(shaded)
    d = ImageDraw.Draw(out)
    # curl separations, so the mass reads as hair and not as a helmet
    i = seed
    x = x0 + 4
    while x < x1 - 3:
        d.arc([x - 6, y0 + h * 0.25, x + 8, y0 + h * 0.75],
              200, 340, fill=dark + (150,), width=2)
        d.arc([x - 4, y0 + h * 0.45, x + 10, y0 + h * 0.95],
              10, 150, fill=lit + (120,), width=1)
        x += max(8, step)
        i += 1
    return out


def torso():
    """112 x 132: marl blouse, open denim jacket, badge, strap, flash unit."""
    W, H = 112, 132
    cx = W // 2

    blouse = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(blouse)
    bd.polygon([(cx - 25, 10), (cx + 25, 10), (cx + 27, 58),
                (cx + 25, 132), (cx - 25, 132), (cx - 27, 58)], fill=255)
    bd.ellipse([cx - 32, 6, cx - 5, 38], fill=255)
    bd.ellipse([cx + 5, 6, cx + 32, 38], fill=255)
    img = char_rig._shade(blouse, BLOUSE, BLOUSE_LIT, BLOUSE_DK)

    marl = _blank((W, H))
    md = ImageDraw.Draw(marl)
    for i in range(-3, 12):
        x = cx - 26 + i * 8
        md.line([(x, 0), (x + 3, H)], fill=BLOUSE_DK + (110,), width=1)
    marl.putalpha(ImageChops.multiply(marl.getchannel("A"), blouse))
    img.alpha_composite(marl)

    jacket = Image.new("L", (W, H), 0)
    jd = ImageDraw.Draw(jacket)
    jd.polygon([(cx - 26, 8), (cx - 9, 12), (cx - 11, 62), (cx - 13, 132),
                (cx - 31, 132), (cx - 32, 60), (cx - 29, 38)], fill=255)
    jd.polygon([(cx + 26, 8), (cx + 9, 12), (cx + 11, 62), (cx + 13, 132),
                (cx + 31, 132), (cx + 32, 60), (cx + 29, 38)], fill=255)
    jd.ellipse([cx - 33, 4, cx - 6, 32], fill=255)
    jd.ellipse([cx + 6, 4, cx + 33, 32], fill=255)
    jd.polygon([(cx - 29, 6), (cx - 12, 10), (cx - 17, 34), (cx - 25, 24)],
               fill=255)
    jd.polygon([(cx + 29, 6), (cx + 12, 10), (cx + 17, 34), (cx + 25, 24)],
               fill=255)
    img.alpha_composite(char_rig._shade(jacket, DENIM, DENIM_LIT, DENIM_DK))
    d = ImageDraw.Draw(img)

    # jacket edges, stitched, and the pale felled seams of denim
    d.line([(cx - 10, 14), (cx - 12, 130)], fill=DENIM_DK + (220,), width=2)
    d.line([(cx + 10, 14), (cx + 12, 130)], fill=DENIM_LIT + (215,), width=2)
    for y in range(20, 128, 16):
        d.line([(cx - 30, y), (cx - 14, y + 1)], fill=DENIM_LIT + (90,), width=1)
        d.line([(cx + 14, y + 2), (cx + 30, y + 1)], fill=DENIM_DK + (90,), width=1)

    # the press badge, clipped to the near lapel
    bx, by = cx + 17, 44
    d.rectangle([bx - 5, by - 7, bx + 6, by + 7], fill=STRAP + (250,))
    d.rectangle([bx - 4, by - 6, bx + 5, by + 6], fill=BADGE + (255,))
    d.rectangle([bx - 4, by - 6, bx + 5, by - 3], fill=BADGE_RED + (255,))
    d.line([(bx - 2, by + 1), (bx + 3, by + 1)], fill=(120, 118, 110, 220), width=1)
    d.line([(bx - 2, by + 3), (bx + 3, by + 3)], fill=(120, 118, 110, 220), width=1)

    # the strap across the chest, and the flash unit riding on it
    strap = Image.new("L", (W, H), 0)
    ImageDraw.Draw(strap).polygon([(cx - 24, 10), (cx - 15, 8), (cx + 22, 96),
                                   (cx + 14, 100)], fill=255)
    img.alpha_composite(char_rig._shade(strap, STRAP, STRAP_LIT, (30, 22, 18)))
    d = ImageDraw.Draw(img)
    fx, fy = cx - 20, 62
    d.rounded_rectangle([fx - 8, fy - 7, fx + 8, fy + 7], radius=2,
                        fill=(44, 44, 50, 255), outline=(22, 22, 26, 255))
    d.ellipse([fx - 5, fy - 4, fx + 5, fy + 4], fill=LENS + (250,))
    d.ellipse([fx - 2, fy - 2, fx + 2, fy + 1], fill=(240, 246, 252, 235))
    d.line([(fx - 6, fy + 5), (fx + 6, fy + 5)], fill=(120, 60, 40, 220), width=1)

    # collar points turned up, because she is that kind of reporter
    d.polygon([(cx - 26, 8), (cx - 12, 12), (cx - 16, 30), (cx - 23, 18)],
              fill=DENIM_LIT + (240,))
    d.polygon([(cx + 26, 8), (cx + 12, 12), (cx + 16, 30), (cx + 23, 18)],
              fill=DENIM_DK + (225,))
    # blouse placket and a couple of buttons showing where the jacket is open
    d.line([(cx - 1, 30), (cx - 1, 128)], fill=BLOUSE_DK + (170,), width=1)
    for y in (44, 66, 88, 110):
        d.ellipse([cx - 3, y, cx + 1, y + 4], fill=BLOUSE_DK + (220,))
    return img


def pelvis():
    """100 x 104: slim trousers, a belt, and the satchel on the hip."""
    W, H = 100, 104
    cx = W // 2
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(cx - 23, 2), (cx + 23, 2), (cx + 25, 34), (cx + 23, 72),
               (cx + 6, 72), (cx + 3, 46), (cx - 3, 46), (cx - 6, 72),
               (cx - 23, 72), (cx - 25, 34)], fill=255)
    img = char_rig._shade(mask, PANTS, PANTS_LIT, PANTS_DK)
    d = ImageDraw.Draw(img)

    d.rectangle([cx - 28, 6, cx + 28, 18], fill=(44, 36, 32, 255))
    d.rectangle([cx - 28, 8, cx + 28, 10], fill=(96, 78, 62, 200))
    d.rectangle([cx - 6, 5, cx + 6, 19], outline=(178, 152, 116, 245), width=2)

    # the satchel, hanging at her far hip
    d.rounded_rectangle([cx + 12, 26, cx + 30, 50], radius=3,
                        fill=BAG + (255,), outline=BAG_LIT + (200,), width=1)
    d.line([(cx + 14, 34), (cx + 28, 34)], fill=BAG_LIT + (220,), width=2)
    d.rectangle([cx + 19, 32, cx + 23, 36], fill=(196, 172, 108, 235))

    for x0, x1 in ((cx - 14, cx - 16), (cx + 14, cx + 16)):
        d.line([(x0, 20), (x1, 70)], fill=PANTS_DK + (120,), width=2)
    d.line([(cx - 20, 44), (cx - 8, 48)], fill=PANTS_LIT + (85,), width=2)
    return img


def head():
    """92 x 108: a mass of auburn curls over a face that is already annoyed."""
    W, H = 92, 108
    cx = W // 2
    img = _blank((W, H))

    neck = Image.new("L", (W, H), 0)
    ImageDraw.Draw(neck).rectangle([cx - 10, 86, cx + 10, H], fill=255)
    img.alpha_composite(char_rig._shade(neck, SKIN_DK, SKIN, SKIN_DEEP))

    # the curls sit behind the face, so they frame it rather than cap it
    img = _curls(img, (cx - 32, 8, cx + 32, 92), HAIR, HAIR_LIT, HAIR_DK,
                 1, clip=False)

    face = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(face)
    fd.ellipse([cx - 17, 30, cx + 17, 80], fill=255)
    fd.polygon([(cx - 14, 58), (cx + 14, 58), (cx + 10, 86), (cx, 92),
                (cx - 10, 86)], fill=255)
    img.alpha_composite(char_rig._shade(face, SKIN, SKIN_LIT, SKIN_DK))
    d = ImageDraw.Draw(img)

    # a fringe of curls over the brow
    for i, (fx, fy, r) in enumerate(((cx - 16, 26, 10), (cx - 4, 22, 11),
                                     (cx + 9, 25, 10), (cx + 18, 32, 8))):
        d.ellipse([fx - r, fy - r, fx + r, fy + r], fill=HAIR + (250,))
        d.arc([fx - r, fy - r, fx + r, fy + r], 200, 350,
              fill=HAIR_LIT + (180,), width=2)

    # brows, level and sceptical
    for sx in (-1, 1):
        ex = cx + sx * 9
        d.line([(ex - 6, 44), (ex + 6, 42)], fill=HAIR_DK + (240,), width=3)
        d.ellipse([ex - 5, 48, ex + 5, 57], fill=(250, 248, 244, 255))
        d.ellipse([ex - 2, 49, ex + 2, 56], fill=(46, 32, 24, 255))
        d.arc([ex - 5, 46, ex + 5, 57], 190, 350, fill=(58, 40, 32, 210), width=1)
        d.line([(ex - 6, 42), (ex - 3, 40)], fill=HAIR_DK + (200,), width=1)

    d.polygon([(cx - 3, 58), (cx + 3, 58), (cx + 1, 68), (cx - 1, 68)],
              fill=SKIN_DK + (130,))
    # mouth: a wry half-smile with lipstick
    d.line([(cx - 8, 76), (cx + 9, 73)], fill=(150, 62, 68, 240), width=3)
    d.arc([cx - 8, 70, cx + 9, 82], 15, 150, fill=(150, 62, 68, 200), width=2)
    d.line([(cx + 6, 74), (cx + 9, 72)], fill=(122, 46, 52, 220), width=1)
    d.line([(cx - 14, 66), (cx - 10, 72)], fill=SKIN_DK + (95,), width=2)
    d.line([(cx + 14, 66), (cx + 10, 72)], fill=SKIN_DK + (95,), width=2)
    # a small scratch on the cheek: she has been getting into trouble
    d.line([(cx + 6, 60), (cx + 10, 64)], fill=(178, 96, 88, 190), width=1)
    # earring
    d.ellipse([cx - 20, 62, cx - 16, 68], outline=(222, 196, 108, 230), width=1)
    return img


def arm(near=True):
    """148 x 132: denim sleeve rolled up, bare forearm, wrist recorder, hand."""
    W, H = 148, 132
    img = _blank((W, H))
    skin = (SKIN, SKIN_LIT, SKIN_DK) if near else (SKIN_DK, SKIN, SKIN_DEEP)
    denim = (DENIM, DENIM_LIT, DENIM_DK) if near else (
        (58, 76, 112), (88, 110, 148), (34, 46, 74))
    sh = (56.0, 12.0)
    elbow = (62.0, 60.0) if near else (64.0, 62.0)
    wrist = (82.0, 82.0) if near else (80.0, 84.0)
    hand = (90.0, 90.0) if near else (88.0, 92.0)

    bare = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(bare)
    bd.ellipse([sh[0] - 15, sh[1] - 11, sh[0] + 15, sh[1] + 17], fill=255)
    bd.line([sh, elbow], fill=255, width=14)
    bd.line([elbow, wrist], fill=255, width=11)
    bd.ellipse([elbow[0] - 7, elbow[1] - 7, elbow[0] + 7, elbow[1] + 7], fill=255)
    bd.ellipse([wrist[0] - 6, wrist[1] - 6, wrist[0] + 6, wrist[1] + 6], fill=255)
    img.alpha_composite(char_rig._shade(bare, *skin))

    cuff = (elbow[0] - 1, elbow[1] - 10)
    sleeve = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(sleeve)
    sd.polygon([(41, 3), (69, 3), (70, 42), (52, 48), (41, 21)], fill=255)
    sd.ellipse([sh[0] - 16, sh[1] - 12, sh[0] + 16, sh[1] + 19], fill=255)
    sd.line([sh, cuff], fill=255, width=16)
    img.alpha_composite(char_rig._shade(sleeve, *denim))
    d = ImageDraw.Draw(img)

    d.line([(46, 18), (45, 42)], fill=DENIM_DK + (130,), width=2)
    d.line([(64, 16), (65, 38)], fill=DENIM_LIT + (105,), width=2)
    # the rolled cuff: two thick folds
    d.ellipse([cuff[0] - 10, cuff[1] - 7, cuff[0] + 10, cuff[1] + 8],
              fill=DENIM_DK + (250,))
    d.arc([cuff[0] - 10, cuff[1] - 8, cuff[0] + 10, cuff[1] + 7], 205, 345,
          fill=DENIM_LIT + (220,), width=2)
    d.line([(cuff[0] - 9, cuff[1] + 1), (cuff[0] + 9, cuff[1] + 3)],
           fill=DENIM_DK + (200,), width=2)

    # the wrist recorder: a flat band with its little red light
    d.ellipse([wrist[0] - 7, wrist[1] - 7, wrist[0] + 7, wrist[1] + 7],
              fill=(40, 40, 46, 255))
    d.rectangle([wrist[0] - 5, wrist[1] - 4, wrist[0] + 4, wrist[1] + 2],
                fill=(66, 66, 74, 250))
    d.ellipse([wrist[0] + 1, wrist[1] - 3, wrist[0] + 4, wrist[1]],
              fill=LED + (255,))

    # hand, fingers open
    d.ellipse([hand[0] - 9, hand[1] - 8, hand[0] + 8, hand[1] + 8],
              fill=skin[0] + (255,))
    d.ellipse([hand[0] - 7, hand[1] - 5, hand[0] + 3, hand[1] + 3],
              fill=skin[1] + (185,))
    for i in range(4):
        d.line([(hand[0] + 2, hand[1] - 6 + i * 4), (hand[0] + 12, hand[1] - 7 + i * 4)],
               fill=skin[2] + (175,), width=2)
    d.line([(hand[0] - 4, hand[1] + 5), (hand[0] + 7, hand[1] + 6)],
           fill=skin[2] + (160,), width=2)

    if not near:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img


def thigh():
    W, H = 46, 86
    img = _limb((W, H), [(11, 2), (35, 2), (36, 46), (32, 84), (13, 84),
                         (9, 46)], PANTS, PANTS_LIT, PANTS_DK)
    d = ImageDraw.Draw(img)
    for x0, x1 in ((17, 19), (30, 28)):
        d.line([(x0, 8), (x1, 80)], fill=PANTS_DK + (115,), width=2)
    d.line([(11, 54), (35, 54)], fill=PANTS_LIT + (80,), width=2)
    return img


def shin():
    W, H = 42, 77
    leg = _limb((W, H), [(9, 2), (33, 2), (33, 40), (27, 74), (14, 74),
                         (8, 40)], PANTS, PANTS_LIT, PANTS_DK)
    d = ImageDraw.Draw(leg)
    for x0, x1 in ((16, 18), (27, 25)):
        d.line([(x0, 8), (x1, 62)], fill=PANTS_DK + (110,), width=2)
    return leg


def foot():
    """48 x 30: a boot with a thick sole, laces and a heel."""
    W, H = 48, 30
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(4, 6), (22, 4), (42, 12), (44, 24), (6, 26)], fill=255)
    d.ellipse([1, 4, 18, 24], fill=255)
    img = char_rig._shade(mask, BOOT, BOOT_LIT, BOOT_DK)
    d = ImageDraw.Draw(img)
    d.rectangle([2, 21, 44, 27], fill=SOLE + (255,))
    d.line([(4, 21), (43, 20)], fill=BOOT_LIT + (170,), width=1)
    # laces up the instep and the ankle collar
    for i in range(3):
        y = 9 + i * 4
        d.line([(12 + i, y), (22 + i, y - 1)], fill=(196, 190, 176, 220), width=1)
    d.line([(19, 4), (24, 16)], fill=BOOT_DK + (200,), width=2)
    d.line([(8, 12), (20, 9)], fill=BOOT_LIT + (140,), width=2)
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
    print(f"  margo: {len(made)} parts -> art_src/chars/margo/parts/")
    return made


def main(argv):
    write()
    if "--sheet" in argv:
        rig = char_rig.load_rig("margo")
        poses = ["stance", "breath", "walk_a", "jab", "boot", "hit", "win"]
        cw, ch = 380, 420
        sheet = Image.new("RGBA", (cw * len(poses), ch), (24, 26, 32, 255))
        table = char_rig.poses_for("margo")
        for i, p in enumerate(poses):
            img = char_rig.render(rig, table[p])
            sheet.alpha_composite(
                img, (i * cw + (cw - img.width) // 2, ch - img.height))
        os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
        path = os.path.join(ROOT, "artifacts", "margo_poses.png")
        sheet.convert("RGB").save(path)
        print(f"  wrote {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
