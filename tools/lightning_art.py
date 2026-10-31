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
# Colours are lifted from the painted concept (juan-ruiz-03.jpg) rather than
# guessed, so the sprites sit in the same light as the picture: a charcoal
# robe, steel-blue plate, and a cloak whose lining is oxblood, not red.
ROBE = (26, 26, 33)
ROBE_LIT = (44, 44, 55)
ROBE_DK = (13, 13, 18)
ROBE_TRIM = (86, 84, 92)

SKIN = (216, 172, 142)
SKIN_LIT = (238, 198, 170)
SKIN_DK = (156, 112, 84)
SKIN_DEEP = (98, 68, 52)

BEAD = (86, 102, 122)
BEAD_LIT = (128, 148, 172)
BEAD_DK = (46, 58, 76)

CAPE = (34, 30, 30)
CAPE_LIT = (60, 52, 50)
CAPE_DK = (16, 13, 14)
CAPE_LINING = (68, 14, 30)
CAPE_LINING_LIT = (96, 24, 42)

STRAW = (206, 184, 140)
STRAW_LIT = (238, 220, 180)
STRAW_DK = (146, 120, 80)
HATBAND = (58, 42, 28)

TROUSER = (34, 34, 43)
TROUSER_LIT = (47, 47, 57)
TROUSER_DK = (22, 22, 30)

BOOT = (34, 34, 42)
BOOT_LIT = (60, 62, 74)
BOOT_DK = (16, 16, 22)

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
    d.polygon([(24, 20), (108, 20), (102, 64), (96, 106), (94, 130),
               (38, 130), (36, 106), (30, 64)], fill=255)
    # Shoulder caps sized to the joints at +-48, not to the canvas: at 62px
    # across they were half the figure's width and he read as a barrel next to
    # the concept's narrow shoulders.
    d.ellipse([16, 4, 60, 58], fill=255)
    d.ellipse([72, 4, 116, 58], fill=255)
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
        pd.polygon([(x, 74), (x + 10.4, 74), (x + 5.2, 96)], fill=255)
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
    # A mask the size of the wearer's own face read as a second head stuck to
    # his chest; on the concept it is a small motif stamped on the plate.
    d.ellipse([55, 46, 77, 74], fill=(22, 22, 28, 235))
    d.arc([55, 46, 77, 74], 200, 340, fill=BEAD_LIT + (200,), width=2)
    for sx in (61, 71):
        d.ellipse([sx - 3.5, 51, sx + 3.5, 58], fill=(214, 52, 46, 255))
        d.ellipse([sx - 1.8, 53, sx + 1.8, 56], fill=(255, 176, 118, 255))
    for x in range(58, 76, 4):
        d.polygon([(x, 61), (x + 3, 61), (x + 1.5, 67)], fill=(238, 240, 246, 255))
    for x in range(59, 75, 7):
        d.polygon([(x, 73), (x + 3, 73), (x + 1.5, 67)], fill=(206, 212, 222, 255))
    # small horns curling off the mask
    for sgn, x in ((-1, 57), (1, 75)):
        d.line([(x, 52), (x + sgn * 5, 46), (x + sgn * 3, 41)],
               fill=BEAD_LIT + (235,), width=2)

    # --- grey waist chevron and belt --------------------------------------
    d.polygon([(44, 90), (66, 103), (88, 90), (88, 99), (66, 113), (44, 99)],
              fill=(78, 82, 94, 255))
    d.polygon([(44, 90), (66, 103), (66, 108), (44, 95)],
              fill=(104, 110, 124, 255))
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
    # trim the over-wide canvas so the part is as wide as the shoulders it has
    return img.resize((114, H), Image.LANCZOS)


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
    return img.resize((86, H), Image.LANCZOS)


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
    W, H = 158, 96
    cx = W // 2
    img = _blank((W, H))

    # --- neck, so the head meets the shoulders instead of hovering ----------
    neck = Image.new("L", (W, H), 0)
    ImageDraw.Draw(neck).rectangle([cx - 13, 72, cx + 13, H], fill=255)
    img.alpha_composite(char_rig._shade(neck, SKIN_DK, SKIN, SKIN_DEEP))

    # --- skull, nearly all of it lost in the brim's shadow ------------------
    face = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(face)
    fd.ellipse([cx - 31, 32, cx + 31, 94], fill=255)
    fd.rectangle([cx - 19, 60, cx + 19, 94], fill=255)
    img.alpha_composite(char_rig._shade(face, (150, 110, 86),
                                      (196, 150, 118), SKIN_DEEP))
    d = ImageDraw.Draw(img)
    # The brim shadow was opaque enough to erase the jaw, which left a black
    # band with nothing in it but eyes; softened, its hard elliptical edge
    # instead read as a white mask with slits painted on. A shadow layer of its
    # own, blurred, lands between the two: dark under the brim, falling off
    # towards the chin so the face still has a bottom.
    shade_layer = _blank((W, H))
    sd = ImageDraw.Draw(shade_layer)
    sd.ellipse([cx - 40, 50, cx + 40, 96], fill=(10, 10, 15, 178))
    sd.ellipse([cx - 34, 70, cx + 34, 94], fill=(6, 6, 9, 86))
    img.alpha_composite(shade_layer.filter(ImageFilter.GaussianBlur(2.6)))
    d = ImageDraw.Draw(img)
    d.line([(cx - 12, 88), (cx + 12, 87)], fill=(120, 66, 58, 150), width=2)
    d.line([(cx - 9, 93), (cx + 9, 92)], fill=(150, 104, 84, 90), width=2)  # chin

    # --- the hat, straight out of the render -------------------------------
    # The concept's brim is a little under half the figure's width; the body is
    # slimmed to suit it rather than the hat shrunk to fit the body.
    hat_img = hat_cut.hat(140, 74)
    img.alpha_composite(hat_img, (cx - hat_img.width // 2,
                                  72 - hat_img.height))

    # --- the only lit thing under it ---------------------------------------
    for ex in (cx - 17, cx + 17):
        glow = _blank((W, H))
        ImageDraw.Draw(glow).ellipse([ex - 11, 71, ex + 11, 83],
                                     fill=BOLT + (105,))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(3)))
    d = ImageDraw.Draw(img)
    for ex, sgn in ((cx - 17, -1), (cx + 17, 1)):
        d.line([(ex - 7, 77), (ex + 7, 75)], fill=(12, 22, 46, 255), width=4)
        d.line([(ex - 6, 76), (ex + 6, 75)], fill=BOLT + (255,), width=2)
        d.point([(ex - 1, 76)], fill=BOLT_CORE + (255,))
        d.point([(ex + sgn * 5, 75)], fill=(255, 255, 255, 255))
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
    d.polygon([(43, 14), (67, 14), (70, 54), (39, 57)], fill=255)
    d.ellipse([sh[0] - 13, sh[1] - 8, sh[0] + 13, sh[1] + 13], fill=255)
    d.ellipse([elbow[0] - 15, elbow[1] - 12, elbow[0] + 15, elbow[1] + 10], fill=255)
    img.alpha_composite(char_rig._shade(mask, base, lit, dark))

    # forearm sleeve, angled out towards the enemy
    fmask = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(fmask)
    fd.line([elbow, wrist], fill=255, width=17)
    fd.ellipse([elbow[0] - 9, elbow[1] - 9, elbow[0] + 9, elbow[1] + 9], fill=255)
    fd.ellipse([wrist[0] - 9, wrist[1] - 9, wrist[0] + 9, wrist[1] + 9], fill=255)
    img.alpha_composite(char_rig._shade(fmask, base, lit, dark))

    d = ImageDraw.Draw(img)
    # flared cuff at the wrist
    d.line([(93, 81), (103, 87)], fill=(104, 108, 120, 255), width=22)
    d.line([(95, 82), (102, 87)], fill=dark + (210,), width=15)

    # hand: wrist, palm, four fingers
    hx, hy = 116, 96
    d.ellipse([hx - 11, hy - 10, hx + 11, hy + 10], fill=skin[0] + (255,))
    d.ellipse([hx - 8, hy - 8, hx + 6, hy + 3], fill=skin[1] + (205,))
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
    # The far arm was the near arm again, so its hand reached across his own
    # chest and vanished behind the torso, leaving one floating glove. A
    # mirrored part bends the other way and puts the hand on its own side.
    if not near:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img


# ------------------------------------------------------------------------ legs
def thigh():
    W, H = 54, 86
    return _limb((W, H), [(10, 2), (44, 2), (46, 46), (41, 84), (13, 84), (8, 46)],
                 TROUSER, TROUSER_LIT, TROUSER_DK)


def shin():
    """Baggy trouser above, tall black boot below.

    The part is drawn only as long as the shin metric (77px), because the rig
    hangs it from the knee and the ankle is exactly one shin-length below: art
    longer than that pokes through the floor in every frame, and the foot is
    what should be standing on it.
    """
    W, H = 46, 77
    leg = _limb((W, H), [(9, 2), (37, 2), (39, 34), (35, 75), (11, 75), (7, 34)],
                TROUSER, TROUSER_LIT, TROUSER_DK)
    bootmask = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(bootmask)
    bd.polygon([(7, 30), (39, 30), (35, 75), (11, 75)], fill=255)
    boot = char_rig._shade(bootmask, BOOT, BOOT_LIT, BOOT_DK)
    img = Image.alpha_composite(leg, boot)
    d = ImageDraw.Draw(img)
    d.line([(5, 30), (41, 30)], fill=(104, 108, 118, 190), width=2)   # cuff
    d.line([(10, 38), (34, 38)], fill=BOOT_LIT + (110,), width=2)
    return img


def foot():
    """Black pointed shoe, toe to the right; the pivot is the heel."""
    W, H = 52, 36
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    # The sole is the bottom of the part, because the pivot sits on the ankle
    # and the ankle is 14px off the floor: a shoe that stopped short of its own
    # canvas hung the whole character in the air.
    d.polygon([(6, 8), (30, 5), (50, 17), (49, 33), (8, 34)], fill=255)
    d.ellipse([2, 6, 22, 34], fill=255)
    img = char_rig._shade(mask, BOOT, BOOT_LIT, BOOT_DK)
    d = ImageDraw.Draw(img)
    d.line([(7, 32), (48, 31)], fill=(104, 108, 118, 205), width=2)
    d.line([(9, 12), (27, 9)], fill=BOOT_LIT + (120,), width=2)
    return img


# ------------------------------------------------------------------------ cape
def cape():
    """Wool cloak to the floor, hanging open with its lining turned out.

    The concept wears it that way: the left front swung clear of the body so a
    long wedge of oxblood lining faces the camera, the wool gathering in deep
    folds down the right, and the hem ragged along the ground. It reads as one
    mass at fighting size, which is what a cape should do.
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

    # the lining, swung round to the front on the left, and a sliver of it
    # showing on the right where that edge turns away
    lining = Image.new("L", (W, H), 0)
    ld = ImageDraw.Draw(lining)
    ld.polygon([(60, 10), (92, 10), (86, 128), (66, 196), (30, 210),
                (14, 172), (34, 104)], fill=255)
    ld.polygon([(126, 12), (140, 12), (150, 150), (140, 196), (126, 152)],
               fill=255)
    img.alpha_composite(char_rig._shade(lining, CAPE_LINING,
                                        CAPE_LINING_LIT, CAPE_DK))

    # folds: shadow creases down both sides, lit ridges on the wool
    for x0, x1 in ((30, 14), (52, 40), (70, 60), (96, 108), (118, 148),
                   (142, 172)):
        d.line([(x0, 34), (x1, 210)], fill=CAPE_DK + (120,), width=3)
    for x0, x1 in ((44, 36), (84, 92), (106, 122)):
        d.line([(x0, 44), (x1, 160)], fill=CAPE_LIT + (70,), width=3)
    for x0, x1 in ((46, 26), (72, 56)):
        d.line([(x0, 30), (x1, 196)], fill=CAPE_LINING_LIT + (110,), width=2)
    d.line([(134, 24), (146, 170)], fill=CAPE_LINING_LIT + (90,), width=2)

    # clasp across the shoulders
    d.line([(58, 12), (128, 12)], fill=(122, 126, 136, 255), width=6)
    d.ellipse([85, 6, 101, 22], fill=(168, 146, 98, 255))
    return img


# ------------------------------------------------------------------------ main
RIG_JSON = {
    "pivots": {
        # pelvis art is 86 wide now, so the centre is 43, not the 50 the
        # 100-wide original used: a stale pivot drew the whole skirt 7px left.
        "pelvis": [43, 16],
        "arm_n": [56, 14],
        "arm_f": [92, 14],          # mirrored art, pivot mirrored too
        # ankle joint sits 14px above the ground, so the pivot is placed 14px
        # up from the sole (part height 36 - 14 = 20)
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
    print(f"wrote {len(parts)} parts -> art_src/chars/lightning/parts/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
