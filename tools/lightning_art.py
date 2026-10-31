"""Lightning: the puppet rig's second fighter, painted from the concept sheet.

Jack's parts are cut out of a photographic turnaround by ``jack_cut.py``.
Lightning has no turnaround - the references are painted concepts, a statue
and a sprite - so his parts are drawn here instead: the wide low straw hat with
its dark band, the black robe under a plated silver bib, the black cloak with
its oxblood lining, the black leather trousers and tall boots, and the blue
lightning crawling over his hands and his hat brim.

Output is exactly what ``char_rig`` expects:

    art_src/chars/lightning/parts/*.png
    art_src/chars/lightning/parts/rig.json

Run:  python3 tools/lightning_art.py
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
PARTS = os.path.join(ROOT, "art_src", "chars", "lightning", "parts")

# --------------------------------------------------------------------- palette
ROBE = (30, 30, 36)
ROBE_LIT = (58, 58, 68)
ROBE_DK = (12, 12, 16)
ROBE_TRIM = (86, 84, 92)

SKIN = (206, 158, 124)
SKIN_LIT = (234, 192, 158)
SKIN_DK = (146, 104, 78)
SKIN_DEEP = (96, 68, 52)

BEAD = (188, 192, 202)
BEAD_LIT = (246, 248, 252)
BEAD_DK = (104, 108, 120)

CAPE = (26, 22, 26)
CAPE_LIT = (52, 44, 48)
CAPE_DK = (8, 6, 8)
CAPE_LINING = (98, 22, 28)
CAPE_LINING_LIT = (140, 36, 42)

STRAW = (206, 184, 140)
STRAW_LIT = (238, 220, 180)
STRAW_DK = (146, 120, 80)
HATBAND = (58, 42, 28)

TROUSER = (28, 28, 34)
TROUSER_LIT = (50, 50, 60)
TROUSER_DK = (10, 10, 14)

BOOT = (26, 26, 32)
BOOT_LIT = (62, 64, 74)
BOOT_DK = (10, 10, 14)

BOLT = (128, 200, 255)
BOLT_CORE = (242, 250, 255)


def _blank(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _shape(size, pts):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    return mask


def _limb(size, pts, base, lit, dark):
    return char_rig._shade(_shape(size, pts), base, lit, dark)


def _zig(x0, y0, x1, y1, steps=6, amp=7.0, phase=0.0):
    """A deterministic jagged path, i.e. a lightning stroke."""
    pts = [(x0, y0)]
    for i in range(1, steps):
        t = i / steps
        wobble = math.sin(i * 2.1 + phase) * amp
        pts.append((x0 + (x1 - x0) * t + wobble,
                    y0 + (y1 - y0) * t + math.sin(i * 1.3 + phase) * amp * 0.5))
    pts.append((x1, y1))
    return pts


def _stroke(img, pts, width=3, glow=True):
    """Blue lightning: a soft halo, a coloured line and a white-hot core."""
    if glow:
        halo = _blank(img.size)
        hd = ImageDraw.Draw(halo)
        hd.line(pts, fill=BOLT + (120,), width=width + 4, joint="curve")
        img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(2.4)))
    d = ImageDraw.Draw(img)
    d.line(pts, fill=BOLT + (225,), width=width, joint="curve")
    d.line(pts, fill=BOLT_CORE + (255,), width=max(1, width // 3), joint="curve")


# ----------------------------------------------------------------------- torso
def torso():
    """Slate robe, beaded demon-face apron, grey waist chevron."""
    W, H = 132, 130
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(14, 22), (118, 22), (108, 64), (99, 106), (97, 130),
               (35, 130), (33, 106), (24, 64)], fill=255)
    d.ellipse([2, 2, 64, 60], fill=255)          # shoulder caps
    d.ellipse([68, 2, 130, 60], fill=255)
    img = char_rig._shade(mask, ROBE, ROBE_LIT, ROBE_DK)
    d = ImageDraw.Draw(img)

    # --- silver bib, scalloped at the hem ----------------------------------
    # The concept wears a plated silver bib over the black robe rather than the
    # slate bead apron he started with; the hem hangs in points over the belly.
    pm = Image.new("L", (W, H), 0)
    pd = ImageDraw.Draw(pm)
    pd.polygon([(27, 24), (105, 24), (101, 76), (31, 76)], fill=255)
    for i in range(7):
        x = 30 + i * 10.4
        pd.polygon([(x, 74), (x + 10.4, 74), (x + 5.2, 92)], fill=255)
    img.alpha_composite(char_rig._shade(pm, BEAD, BEAD_LIT, BEAD_DK))

    beads = _blank((W, H))
    bd = ImageDraw.Draw(beads)
    for row in range(10):
        y = 28 + row * 6.2
        for col in range(12):
            x = 31 + col * 6.6 + (3.3 if row % 2 else 0.0)
            r = 2.7
            if not (pm.getpixel((min(W - 1, int(x)), min(H - 1, int(y)))) > 40):
                continue
            bd.ellipse([x - r, y - r, x + r, y + r], fill=BEAD + (255,))
            bd.arc([x - r, y - r, x + r, y + r], 200, 340,
                   fill=BEAD_LIT + (255,), width=1)
            bd.point([(x + 0.6, y + 0.7)], fill=BEAD_DK + (180,))
    beads.putalpha(ImageChops.multiply(beads.getchannel("A"), pm))
    img.alpha_composite(beads)

    # --- the demon face worked into the bib --------------------------------
    d.ellipse([48, 44, 86, 80], fill=(22, 22, 28, 235))
    d.arc([48, 44, 86, 80], 200, 340, fill=BEAD_LIT + (200,), width=2)
    for sx in (58, 72):
        d.ellipse([sx - 5, 50, sx + 5, 59], fill=(214, 52, 46, 255))
        d.ellipse([sx - 2.5, 52.5, sx + 2.5, 56.5], fill=(255, 176, 118, 255))
    for x in range(52, 86, 6):
        d.polygon([(x, 63), (x + 4, 63), (x + 2, 72)], fill=(238, 240, 246, 255))
    for x in range(54, 84, 10):
        d.polygon([(x, 79), (x + 4, 79), (x + 2, 72)], fill=(206, 212, 222, 255))
    # small horns curling off the mask
    for sgn, x in ((-1, 50), (1, 84)):
        d.line([(x, 50), (x + sgn * 7, 42), (x + sgn * 4, 35)],
               fill=BEAD_LIT + (235,), width=3)

    # --- grey waist chevron and belt --------------------------------------
    d.polygon([(44, 90), (66, 103), (88, 90), (88, 99), (66, 113), (44, 99)],
              fill=(126, 132, 142, 255))
    d.polygon([(44, 90), (66, 103), (66, 108), (44, 95)],
              fill=(158, 164, 174, 255))
    d.rectangle([33, 108, 99, 120], fill=(16, 14, 16, 255))
    d.rectangle([58, 106, 74, 122], fill=(178, 156, 106, 255))
    d.rectangle([62, 110, 70, 118], fill=(96, 78, 46, 255))

    # --- collar and folds --------------------------------------------------
    d.polygon([(52, 20), (66, 34), (80, 20), (74, 18), (66, 26), (58, 18)],
              fill=(22, 26, 36, 255))
    for x, y1 in ((40, 112), (52, 100), (80, 100), (92, 112)):
        d.line([(x, 56), (x + (2 if x < 66 else -2), y1)],
               fill=ROBE_DK + (150,), width=2)
    for x in (36, 96):
        d.line([(x, 34), (x - 1, 100)], fill=ROBE_LIT + (90,), width=2)
    return img


# ---------------------------------------------------------------------- pelvis
def pelvis():
    """The robe's skirt, flaring from a sash."""
    W, H = 100, 76
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(31, 6), (69, 6), (95, 62), (72, 74), (28, 74), (5, 62)], fill=255)
    d.ellipse([6, 50, 94, 78], fill=255)
    img = char_rig._shade(mask, ROBE, ROBE_LIT, ROBE_DK)
    d = ImageDraw.Draw(img)
    d.rectangle([28, 4, 72, 18], fill=(16, 14, 16, 255))
    d.rectangle([44, 2, 58, 20], fill=(178, 156, 106, 255))
    for x in (30, 42, 56, 70):
        d.line([(x, 22), (x + (3 if x < 50 else -3), 70)],
               fill=ROBE_DK + (130,), width=2)
    d.line([(12, 60), (24, 70)], fill=ROBE_LIT + (80,), width=2)
    return img


# ------------------------------------------------------------------------ head
def head():
    """The hat hides the face; only two blue eyes burn out of its shade.

    The hat is not drawn here. It is cut from the HD render in
    ``concept_art/fighters/lightning`` by ``tools/hat_cut.py``, because the
    render is the real prop and its banded weave and straw fan survive the
    reduction better than a redrawing did. Everything else - the skull, the
    shadow the brim throws over it, the eyes - is flat sprite tones drawn here,
    since those have to sit on the character's palette. The brim comes down to
    the eye line, so at fighting distance he is a hat with two lit slits.
    """
    W, H = 150, 94
    img = _blank((W, H))

    # --- neck, so the head meets the shoulders instead of hovering ----------
    neck = Image.new("L", (W, H), 0)
    ImageDraw.Draw(neck).rectangle([62, 70, 88, 94], fill=255)
    img.alpha_composite(char_rig._shade(neck, SKIN_DK, SKIN, SKIN_DEEP))

    # --- skull, nearly all of it lost in the brim's shadow ------------------
    face = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(face)
    fd.ellipse([44, 30, 106, 92], fill=255)
    fd.rectangle([56, 58, 94, 92], fill=255)
    img.alpha_composite(char_rig._shade(face, (150, 110, 86),
                                       (196, 150, 118), SKIN_DEEP))
    d = ImageDraw.Draw(img)
    d.ellipse([34, 52, 116, 92], fill=(10, 10, 15, 212))        # brim shadow
    d.ellipse([40, 68, 110, 90], fill=(6, 6, 9, 92))            # deepest, at the jaw
    d.line([(63, 86), (87, 85)], fill=(96, 50, 44, 175), width=2)    # mouth

    # --- the hat, straight out of the render -------------------------------
    hat_img = hat_cut.hat(134, 68)
    img.alpha_composite(hat_img, ((W - hat_img.width) // 2,
                                  70 - hat_img.height))

    # --- the only lit thing under it ---------------------------------------
    for cx in (62, 88):
        glow = _blank((W, H))
        ImageDraw.Draw(glow).ellipse([cx - 11, 69, cx + 11, 81],
                                     fill=BOLT + (105,))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(3)))
    d = ImageDraw.Draw(img)
    for cx, sgn in ((62, -1), (88, 1)):
        d.line([(cx - 7, 75), (cx + 7, 73)], fill=(12, 22, 46, 255), width=4)
        d.line([(cx - 6, 74), (cx + 6, 73)], fill=BOLT + (255,), width=2)
        d.point([(cx - 1, 74)], fill=BOLT_CORE + (255,))
        d.point([(cx + sgn * 5, 73)], fill=(255, 255, 255, 255))
    return img


# ------------------------------------------------------------------------ arms
def arm(near=True):
    """One bent arm: robe sleeve, cuff, and a hand with current crawling on it."""
    W, H = 148, 132
    img = _blank((W, H))
    base, lit, dark = (ROBE, ROBE_LIT, ROBE_DK) if near else (
        (18, 18, 22), (36, 36, 44), (8, 8, 10))
    skin = (SKIN, SKIN_LIT, SKIN_DK) if near else (SKIN_DK, SKIN, SKIN_DEEP)
    sh = (54.0, 14.0)
    elbow = (56.0, 62.0)
    wrist = (98.0, 84.0)

    # upper sleeve, hanging from the shoulder
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(37, 14), (73, 14), (78, 54), (33, 58)], fill=255)
    d.ellipse([sh[0] - 20, sh[1] - 10, sh[0] + 20, sh[1] + 18], fill=255)
    d.ellipse([elbow[0] - 22, elbow[1] - 16, elbow[0] + 22, elbow[1] + 14], fill=255)
    img.alpha_composite(char_rig._shade(mask, base, lit, dark))

    # forearm sleeve, angled out towards the enemy
    fmask = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(fmask)
    fd.line([elbow, wrist], fill=255, width=24)
    fd.ellipse([elbow[0] - 13, elbow[1] - 13, elbow[0] + 13, elbow[1] + 13], fill=255)
    fd.ellipse([wrist[0] - 13, wrist[1] - 13, wrist[0] + 13, wrist[1] + 13], fill=255)
    img.alpha_composite(char_rig._shade(fmask, base, lit, dark))

    d = ImageDraw.Draw(img)
    # flared cuff at the wrist
    d.line([(92, 80), (104, 88)], fill=(132, 134, 144, 255), width=30)
    d.line([(95, 82), (102, 87)], fill=dark + (210,), width=22)

    # hand: wrist, palm, four fingers
    hx, hy = 116, 96
    d.ellipse([hx - 14, hy - 13, hx + 14, hy + 13], fill=skin[0] + (255,))
    d.ellipse([hx - 10, hy - 10, hx + 8, hy + 4], fill=skin[1] + (205,))
    d.line([(hx - 4, hy + 5), (hx + 9, hy + 6)], fill=skin[2] + (185,), width=2)
    for i in range(3):
        d.line([(hx + 3, hy - 6 + i * 5), (hx + 13, hy - 5 + i * 5)],
               fill=skin[2] + (150,), width=2)
    d.line([(hx + 2, hy - 9), (hx + 9, hy - 9)], fill=skin[1] + (180,), width=2)

    # folds in the sleeve
    d.line([(40, 28), (43, 54)], fill=dark + (130,), width=2)
    d.line([(69, 26), (71, 52)], fill=lit + (80,), width=2)
    d.line([(64, 66), (82, 74)], fill=dark + (100,), width=2)

    # current: short arcs off the hand, not a fork
    _stroke(img, _zig(hx + 6, hy - 8, hx + 20, hy - 20, 4, 4, 0.7), width=2)
    _stroke(img, _zig(hx - 8, hy + 6, hx - 18, hy + 17, 3, 3, 2.1), width=2)
    return img


# ------------------------------------------------------------------------ legs
def thigh():
    W, H = 54, 86
    return _limb((W, H), [(7, 2), (47, 2), (49, 46), (44, 84), (10, 84), (5, 46)],
                 TROUSER, TROUSER_LIT, TROUSER_DK)


def shin():
    """Baggy trouser above, tall black boot below."""
    W, H = 46, 86
    leg = _limb((W, H), [(6, 2), (40, 2), (42, 38), (38, 84), (8, 84), (4, 38)],
                TROUSER, TROUSER_LIT, TROUSER_DK)
    bootmask = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(bootmask)
    bd.polygon([(4, 34), (42, 34), (38, 84), (8, 84)], fill=255)
    boot = char_rig._shade(bootmask, BOOT, BOOT_LIT, BOOT_DK)
    img = Image.alpha_composite(leg, boot)
    d = ImageDraw.Draw(img)
    d.line([(5, 34), (41, 34)], fill=(140, 144, 154, 210), width=2)   # cuff
    d.line([(10, 42), (34, 42)], fill=BOOT_LIT + (110,), width=2)
    return img


def foot():
    """Black pointed shoe, toe to the right; the pivot is the heel."""
    W, H = 52, 36
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(6, 8), (30, 5), (50, 18), (48, 30), (8, 30)], fill=255)
    d.ellipse([2, 6, 22, 30], fill=255)
    img = char_rig._shade(mask, BOOT, BOOT_LIT, BOOT_DK)
    d = ImageDraw.Draw(img)
    d.line([(7, 29), (49, 27)], fill=(138, 142, 152, 220), width=2)
    d.line([(9, 12), (27, 9)], fill=BOOT_LIT + (150,), width=2)
    return img


# ------------------------------------------------------------------------ cape
def cape():
    """Crimson cloak from the shoulders to below the knee."""
    W, H = 172, 226
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(58, 6), (114, 6), (162, 178), (146, 206), (118, 192),
               (96, 214), (70, 196), (40, 212), (16, 182), (26, 120)],
              fill=255)
    d.ellipse([50, 0, 122, 26], fill=255)
    img = char_rig._shade(mask, CAPE, CAPE_LIT, CAPE_DK)
    d = ImageDraw.Draw(img)
    # oxblood lining showing down the inside edge, then deep folds in the wool
    d.polygon([(58, 10), (86, 10), (74, 120), (48, 96)],
              fill=CAPE_LINING + (190,))
    d.polygon([(30, 120), (40, 96), (56, 150), (34, 176)],
              fill=CAPE_LINING + (170,))
    d.polygon([(140, 120), (130, 96), (116, 152), (136, 178)],
              fill=CAPE_LINING + (150,))
    for x0, x1 in ((46, 26), (68, 54), (92, 104), (116, 148), (134, 162)):
        d.line([(x0, 30), (x1, 196)], fill=CAPE_DK + (120,), width=3)
    for x0, x1 in ((56, 44), (80, 84), (104, 118)):
        d.line([(x0, 40), (x1, 150)], fill=CAPE_LIT + (70,), width=3)
    d.line([(60, 24), (44, 150)], fill=CAPE_LINING_LIT + (90,), width=2)
    # clasp across the shoulders
    d.line([(54, 14), (118, 14)], fill=(122, 126, 136, 255), width=6)
    d.ellipse([80, 8, 96, 24], fill=(168, 146, 98, 255))
    return img


# ------------------------------------------------------------------------ main
RIG_JSON = {
    "pivots": {
        "pelvis": [50, 16],
        "arm_n": [56, 14],
        "arm_f": [56, 14],
        "foot_n": [14, 32],
        "foot_f": [14, 32],
        "cape": [86, 12],
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
    print(f"wrote {len(parts)} parts -> art_src/chars/lightning/parts/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
