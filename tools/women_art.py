"""Gracie Law and Maio Yin: the roster's two women, painted in code.

The other fighters either cut their parts out of a photographic turnaround
(Jack) or paint a male body in code (Lightning, the gangs). These two have no
turnaround, so like Lightning they are drawn here, at rig scale, from the
costume in the reference stills: vermilion silk robes figured in gold, a wide
sash of gold plaques, jade at the throat, and a ceremonial crown.

Maio Yin wears the tall gold sunburst with the teal feather crest and the long
gold pendants. Gracie wears the silver filigree crown with its bead fringe and
a cream lining turned out down the front - the two crowns are what tells them
apart at fighting distance, since both wear the same wedding red.

Output is what ``char_rig`` and ``bake_char`` expect:

    art_src/chars/gracielaw/parts/*.png
    art_src/chars/gracielaw/parts/rig.json
    art_src/chars/jade/parts/*.png
    art_src/chars/jade/parts/rig.json

Run:  python3 tools/women_art.py [--sheet]
"""

from __future__ import annotations

import json
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import char_rig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "art_src", "chars")

# --------------------------------------------------------------------- palette
# Sampled from the reference stills: the robe is a warm vermilion, not a flag
# red, and the gold is old and slightly green rather than bright yellow.
SKIN = (236, 200, 178)
SKIN_LIT = (250, 224, 206)
SKIN_DK = (188, 140, 116)
SKIN_DEEP = (128, 88, 74)

HAIR = (22, 16, 16)
HAIR_LIT = (52, 40, 40)

GOLD = (198, 158, 74)
GOLD_LIT = (233, 200, 118)
GOLD_DK = (128, 96, 38)

SILVER = (196, 202, 210)
SILVER_LIT = (232, 238, 244)
SILVER_DK = (124, 132, 142)

JADE = (58, 140, 116)
JADE_LIT = (104, 184, 156)
JADE_DK = (28, 88, 72)

TEAL = (38, 122, 110)
TEAL_LIT = (74, 166, 148)
TEAL_DK = (16, 68, 62)

LIP = (168, 44, 52)
LASH = (30, 18, 18)

# The two costumes. Everything the painter needs to tell them apart lives here.
THEMES = {
    "gracielaw": dict(
        robe=(178, 40, 44), robe_lit=(214, 74, 72), robe_dk=(112, 18, 26),
        # Antique gold piping, not cream. A wide pale panel down the front of
        # the robe is what made her read as a red coat with a white apron.
        trim=(198, 160, 92),
        trim_lit=(232, 202, 138),
        trim_dk=(124, 92, 40),
        metal=SILVER,
        metal_lit=SILVER_LIT,
        metal_dk=SILVER_DK,
        crown="filigree",
        pattern="floral",
        pendant=JADE,
        pendant_lit=JADE_LIT,
        sash=(150, 30, 36),
    ),
    "jade": dict(
        robe=(186, 34, 38), robe_lit=(222, 68, 64), robe_dk=(116, 14, 22),
        trim=(206, 168, 84),             # gold-brocade edge, not cream
        trim_lit=(240, 208, 128),
        trim_dk=(132, 100, 40),
        metal=GOLD,
        metal_lit=GOLD_LIT,
        metal_dk=GOLD_DK,
        crown="sunburst",
        pattern="medallion",
        pendant=JADE,
        pendant_lit=JADE_LIT,
        sash=(160, 34, 34),
    ),
}


def _blank(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _shape(size, pts):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    return mask


def _limb(size, pts, base, lit, dark):
    return char_rig._shade(_shape(size, pts), base, lit, dark)


def _medallions(d, box, colour, count, r, rows=None):
    """Gold roundels scattered over the silk, the pattern on Maio Yin's robe."""
    x0, y0, x1, y1 = box
    rows = rows or 3
    for row in range(rows):
        y = y0 + (y1 - y0) * (row + 0.5) / rows
        for col in range(count):
            x = x0 + (x1 - x0) * (col + 0.5) / count + (6 if row % 2 else 0)
            d.ellipse([x - r, y - r, x + r, y + r], fill=colour + (255,))
            d.ellipse([x - r * 0.55, y - r * 0.55, x + r * 0.55, y + r * 0.55],
                      fill=colourX(colour, 1.25) + (255,))


def colourX(colour, k):
    """Lighten or darken a colour, clamped; used for motifs and shading."""
    return tuple(max(0, min(255, int(round(c * k)))) for c in colour)


def _floral(d, box, colour, count, r, rows=None):
    """Small five-petal flowers, the sprigs on Gracie's silk.

    Drawn as a bud with two diagonal leaves, the motif read as a wheat sheaf
    repeated down the bodice; petals stay inside a circle so the print reads as
    a flower even at fighting size.
    """
    x0, y0, x1, y1 = box
    rows = rows or 3
    for row in range(rows):
        y = y0 + (y1 - y0) * (row + 0.5) / rows
        for col in range(count):
            x = x0 + (x1 - x0) * (col + 0.5) / count + (7 if row % 2 else 0)
            for i in range(5):
                a = math.radians(i * 72 - 90)
                px = x + math.cos(a) * r * 0.55
                py = y + math.sin(a) * r * 0.55
                d.ellipse([px - r * 0.42, py - r * 0.42, px + r * 0.42, py + r * 0.42],
                          fill=colour + (215,))
            d.ellipse([x - r * 0.30, y - r * 0.30, x + r * 0.30, y + r * 0.30],
                      fill=colourX(colour, 0.8) + (235,))


# ----------------------------------------------------------------------- torso
def torso(t):
    """108 x 124 bodice: narrow shoulders, nipped waist, silk robe over all.

    The first pass put the shoulder caps on +-48 (the male rig's joints) on a
    104-wide body, so the arms grew out of the chest as two red balloons.
    """
    W, H = 108, 124
    cx = W // 2
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    # shoulders +-34, waist +-26, hips +-38: a figure, not a barrel
    d.polygon([(cx - 24, 14), (cx + 24, 14), (cx + 30, 50), (cx + 26, 76),
               (cx + 34, 96), (cx + 38, 124), (cx - 38, 124), (cx - 34, 96),
               (cx - 26, 76), (cx - 30, 50)], fill=255)
    # Shoulder caps at +-30, not +-36: at 34px across they read as two
    # puffed sleeves and the whole bodice as a coat rather than a dress.
    d.ellipse([cx - 30, 8, cx - 4, 38], fill=255)
    d.ellipse([cx + 4, 8, cx + 30, 38], fill=255)
    d.ellipse([cx - 22, 34, cx + 22, 60], fill=255)          # bust
    img = char_rig._shade(mask, t["robe"], t["robe_lit"], t["robe_dk"])
    d = ImageDraw.Draw(img)

    # silk figures, kept sparse: a fine all-over print reads as noise at
    # fighting size, so the motifs are few and large enough to see
    cloth = _blank((W, H))
    cd = ImageDraw.Draw(cloth)
    if t["pattern"] == "medallion":
        _medallions(cd, (cx - 26, 30, cx + 26, 78), GOLD, 2, 5.0, rows=3)
    else:
        _floral(cd, (cx - 26, 30, cx + 26, 78), t["trim_lit"], 2, 4.5, rows=3)
    cloth.putalpha(ImageChops.multiply(cloth.getchannel("A"), mask))
    img.alpha_composite(cloth)
    d = ImageDraw.Draw(img)

    # cross-over collar with the lining turned out down the middle
    # A narrow crossed collar, piped instead of filled: the wide pale band
    # this used to be is the "apron" half of the red-coat-and-apron read.
    d.polygon([(cx - 16, 12), (cx, 34), (cx + 16, 12), (cx + 11, 11),
               (cx, 28), (cx - 11, 11)], fill=t["trim"] + (245,))
    d.line([(cx - 16, 12), (cx, 36)], fill=t["metal"] + (225,), width=2)
    d.line([(cx + 16, 12), (cx, 36)], fill=t["metal"] + (190,), width=2)
    d.line([(cx - 1, 36), (cx - 1, 124)], fill=t["trim_dk"] + (120,), width=1)

    # mandarin collar standing at the throat: the qipao line, and the piece
    # that stops the bodice reading as an open coat with a lapel
    d.rectangle([cx - 13, 7, cx + 13, 15], fill=t["robe_dk"] + (255,))
    d.line([(cx - 13, 8), (cx + 13, 8)], fill=t["trim"] + (245,), width=2)
    d.line([(cx - 13, 14), (cx + 13, 14)], fill=t["robe_dk"] + (255,), width=1)

    # gold plaque sash at the waist
    d.rectangle([cx - 32, 86, cx + 32, 104], fill=t["sash"] + (255,))
    d.rectangle([cx - 32, 86, cx + 32, 90], fill=t["metal"] + (240,))
    d.rectangle([cx - 32, 100, cx + 32, 104], fill=t["metal"] + (205,))
    for i in range(4):
        x = cx - 22 + i * 15
        d.ellipse([x - 5, 91, x + 5, 100], fill=t["metal"] + (255,))
        d.ellipse([x - 2, 93, x + 2, 98], fill=t["metal_dk"] + (255,))

    # jade at the throat on a fine chain
    d.line([(cx - 12, 22), (cx - 6, 32), (cx + 6, 32), (cx + 12, 22)],
           fill=t["metal"] + (190,), width=1)
    d.ellipse([cx - 6, 30, cx + 6, 42], fill=t["pendant"] + (255,))
    d.ellipse([cx - 3, 32, cx + 3, 38], fill=t["pendant_lit"] + (255,))
    d.ellipse([cx - 6, 30, cx + 6, 42], outline=t["metal"] + (215,), width=1)

    for x0, x1 in ((cx - 30, cx - 26), (cx - 20, cx - 18), (cx + 20, cx + 18),
                   (cx + 30, cx + 26)):
        d.line([(x0, 46), (x1, 122)], fill=t["robe_dk"] + (105,), width=2)
    for x in (cx - 10, cx + 10):
        d.line([(x, 46), (x + (2 if x < cx else -2), 84)],
               fill=t["robe_lit"] + (85,), width=2)
    return img


# ---------------------------------------------------------------------- pelvis
def pelvis(t):
    """104 x 104 skirt: from the sash to a gold hem, wider than the torso."""
    W, H = 104, 104
    cx = W // 2
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(cx - 24, 2), (cx + 24, 2), (cx + 32, 34), (cx + 44, 100),
               (cx - 44, 100), (cx - 32, 34)], fill=255)
    d.ellipse([cx - 44, 86, cx + 44, 104], fill=255)
    img = char_rig._shade(mask, t["robe"], t["robe_lit"], t["robe_dk"])
    d = ImageDraw.Draw(img)

    cloth = _blank((W, H))
    cd = ImageDraw.Draw(cloth)
    if t["pattern"] == "medallion":
        _medallions(cd, (cx - 34, 28, cx + 34, 84), GOLD, 2, 5.5, rows=2)
    else:
        _floral(cd, (cx - 34, 28, cx + 34, 84), t["trim_lit"], 2, 5.0, rows=2)
    cloth.putalpha(ImageChops.multiply(cloth.getchannel("A"), mask))
    img.alpha_composite(cloth)
    d = ImageDraw.Draw(img)

    # The front of the skirt is silk, split by a narrow gold stripe. A wide
    # panel of pale trim here is what read as a white apron in game, so it is
    # a stripe now, with the slits of a qipao beside it.
    panel = _blank((W, H))
    pd = ImageDraw.Draw(panel)
    pd.polygon([(cx - 5, 4), (cx + 5, 4), (cx + 7, 100), (cx - 7, 100)],
               fill=t["trim"] + (255,))
    panel.putalpha(ImageChops.multiply(panel.getchannel("A"), mask))
    img.alpha_composite(panel)
    d = ImageDraw.Draw(img)
    d.line([(cx - 6, 6), (cx - 8, 98)], fill=t["trim_lit"] + (190,), width=1)
    d.line([(cx + 6, 6), (cx + 8, 98)], fill=t["trim_dk"] + (200,), width=2)
    for sx in (-1, 1):
        d.line([(cx + sx * 30, 40), (cx + sx * 34, 92)],
               fill=t["robe_dk"] + (170,), width=2)

    # No metal hem band: clipped and eroded it still read as a bright bar
    # across the ankles, so the skirt ends in silk and a single dark rule.
    d.line([(cx - 38, 96), (cx + 38, 96)], fill=t["robe_dk"] + (200,), width=2)

    # sash tails over the skirt
    d.polygon([(cx - 30, 6), (cx - 18, 8), (cx - 22, 40), (cx - 32, 34)],
              fill=t["sash"] + (255,))
    d.line([(cx - 28, 8), (cx - 30, 36)], fill=t["metal"] + (170,), width=2)
    for x0, x1 in ((cx - 36, cx - 30), (cx + 36, cx + 30)):
        d.line([(x0, 30), (x1, 96)], fill=t["robe_dk"] + (110,), width=2)
    return img


# ------------------------------------------------------------------------ head
def head(t):
    """96 x 118 head with the ceremonial crown; neck at the bottom centre.

    The face is drawn first and the hair laid over it. Cutting the face back
    out of a shaded hair mass left a pale mask with a painted-on brow, which is
    what the first version looked like at sprite size.
    """
    W, H = 96, 118
    cx = W // 2
    img = _blank((W, H))

    neck = Image.new("L", (W, H), 0)
    ImageDraw.Draw(neck).rectangle([cx - 10, 96, cx + 10, H], fill=255)
    img.alpha_composite(char_rig._shade(neck, SKIN_DK, SKIN, SKIN_DEEP))

    # hair mass behind the head, so the silhouette has a bun and a nape
    back = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(back)
    bd.ellipse([cx - 27, 46, cx + 27, 100], fill=255)
    bd.ellipse([cx - 13, 100, cx + 13, 112], fill=255)
    bd.ellipse([cx - 15, 30, cx + 15, 58], fill=255)          # bun
    img.alpha_composite(char_rig._shade(back, HAIR, HAIR_LIT, (8, 6, 6)))

    # face: a narrow oval with a soft chin, no hard jaw corner
    face = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(face)
    fd.ellipse([cx - 20, 58, cx + 20, 102], fill=255)
    fd.polygon([(cx - 15, 88), (cx + 15, 88), (cx + 9, 106), (cx, 110),
                (cx - 9, 106)], fill=255)
    img.alpha_composite(char_rig._shade(face, SKIN, SKIN_LIT, SKIN_DK))
    d = ImageDraw.Draw(img)

    # fringe and the two locks in front of the ears
    hair = Image.new("L", (W, H), 0)
    hd = ImageDraw.Draw(hair)
    hd.ellipse([cx - 24, 56, cx + 24, 76], fill=255)
    hd.rectangle([cx - 24, 76, cx - 19, 92], fill=255)
    hd.rectangle([cx + 19, 76, cx + 24, 92], fill=255)
    img.alpha_composite(char_rig._shade(hair, HAIR, HAIR_LIT, (8, 6, 6)))
    d = ImageDraw.Draw(img)
    d.line([(cx, 58), (cx, 70)], fill=(64, 48, 48, 150), width=1)     # parting

    # --- face: kohl, a line of gold shadow, a small red mouth --------------
    for sx in (-1, 1):
        ex = cx + sx * 9
        d.line([(ex - 5, 80), (ex + 5, 79)], fill=LASH + (245,), width=2)   # lash
        d.line([(ex - 4, 82), (ex + 4, 82)], fill=(250, 246, 240, 255), width=2)
        d.ellipse([ex - 1.5, 81, ex + 1.5, 84], fill=(40, 26, 22, 255))
        d.line([(ex - 4, 77), (ex + 3, 76)], fill=t["metal"] + (130,), width=1)
    d.line([(cx - 1, 88), (cx + 1, 92)], fill=SKIN_DEEP + (120,), width=1)
    d.polygon([(cx - 5, 97), (cx, 95), (cx + 5, 97), (cx, 100)], fill=LIP + (255,))
    d.line([(cx - 5, 97), (cx + 5, 97)], fill=colourX(LIP, 0.65) + (255,), width=1)
    d.line([(cx - 6, 94), (cx + 6, 94)], fill=SKIN_DK + (90,), width=1)

    # --- crown --------------------------------------------------------------
    if t["crown"] == "sunburst":
        # Maio Yin: a teal feather crest, gold spokes fanned over it, long pendants.
        crest = Image.new("L", (W, H), 0)
        cd = ImageDraw.Draw(crest)
        cd.ellipse([cx - 24, 18, cx + 24, 56], fill=255)
        for i in range(9):                       # feather teeth
            x = cx - 20 + i * 5
            cd.polygon([(x - 2, 30), (x, 8 + (6 if i % 2 else 0)), (x + 3, 30)],
                       fill=255)
        crest = ImageChops.multiply(crest, Image.new("L", (W, H), 255))
        img.alpha_composite(char_rig._shade(crest, TEAL, TEAL_LIT, TEAL_DK))
        d = ImageDraw.Draw(img)
        for i in range(13):
            a = math.radians(200 + i * (140 / 12.0))
            r0 = 26
            r1 = 40 + (5 if i % 2 else 0)
            d.line([(cx + math.cos(a) * r0, 48 + math.sin(a) * r0),
                    (cx + math.cos(a) * r1, 48 + math.sin(a) * r1)],
                   fill=t["metal"] + (255,), width=2)
            d.ellipse([cx + math.cos(a) * r1 - 2, 48 + math.sin(a) * r1 - 2,
                       cx + math.cos(a) * r1 + 2, 48 + math.sin(a) * r1 + 2],
                      fill=t["metal_lit"] + (255,))
        d.arc([cx - 26, 36, cx + 26, 62], 198, 342, fill=t["metal"] + (255,), width=4)
        d.arc([cx - 26, 36, cx + 26, 62], 198, 342, fill=t["metal_lit"] + (160,), width=1)
        for sx in (-1, 1):
            px = cx + sx * 26
            d.line([(px, 58), (px, 62)], fill=t["metal"] + (235,), width=2)
            for k in range(3):
                y = 66 + k * 8
                d.ellipse([px - 3, y - 3, px + 3, y + 3], fill=t["metal"] + (255,))
                d.ellipse([px - 1.5, y - 1.5, px + 1.5, y + 1.5],
                          fill=t["metal_dk"] + (220,))
            d.line([(px, 88), (px + sx * 3, 100)], fill=t["metal"] + (220,), width=2)
    else:
        # Gracie: a silver band with short filigree spokes and a bead fringe.
        d.arc([cx - 25, 44, cx + 25, 78], 196, 344, fill=t["metal"] + (255,), width=4)
        d.arc([cx - 25, 44, cx + 25, 78], 196, 344, fill=t["metal_lit"] + (180,), width=1)
        for i in range(9):
            a = math.radians(202 + i * (136 / 8.0))
            d.line([(cx + math.cos(a) * 24, 60 + math.sin(a) * 24),
                    (cx + math.cos(a) * 32, 60 + math.sin(a) * 32)],
                   fill=t["metal"] + (235,), width=1)
            d.ellipse([cx + math.cos(a) * 33 - 2, 60 + math.sin(a) * 33 - 2,
                       cx + math.cos(a) * 33 + 2, 60 + math.sin(a) * 33 + 2],
                      fill=SILVER_LIT + (255,))
        for i in range(7):                       # bead fringe over the brow
            x = cx - 15 + i * 5
            d.line([(x, 56), (x, 60)], fill=t["metal"] + (200,), width=1)
            d.ellipse([x - 2, 59, x + 2, 63], fill=SILVER_LIT + (255,))
        d.polygon([(cx - 7, 50), (cx, 36), (cx + 7, 50)], fill=t["metal"] + (255,))
        d.polygon([(cx - 3, 48), (cx, 40), (cx + 3, 48)], fill=t["metal_lit"] + (255,))
        for sx in (-1, 1):                       # jade drops
            px = cx + sx * 25
            d.line([(px, 62), (px, 74)], fill=t["metal"] + (220,), width=1)
            d.ellipse([px - 4, 74, px + 4, 86], fill=t["pendant"] + (255,))
            d.ellipse([px - 2, 76, px + 1, 81], fill=t["pendant_lit"] + (255,))
    return img


# ------------------------------------------------------------------------ arms
def arm(t, near=True):
    """One arm: sleeve, forearm, gold cuff and hand, drawn HANGING.

    Same correction as Lightning's: the part was a raised "L", the idle pose
    swings it down 30 degrees, and the result pinned the elbow against the
    waist with the forearm jutting out sideways. Hanging from the shoulder, the
    same swing carries the forearm forward and keeps the elbow clear of the
    ribs. Still one mask with one gradient across it, so no pale seam appears
    part-way down the arm.
    """
    W, H = 148, 132
    img = _blank((W, H))
    base, lit, dark = ((t["robe"], t["robe_lit"], t["robe_dk"]) if near
                       else (colourX(t["robe"], 0.72), colourX(t["robe"], 0.9),
                             colourX(t["robe_dk"], 0.7)))
    skin = (SKIN, SKIN_LIT, SKIN_DK) if near else (SKIN_DK, SKIN, SKIN_DEEP)

    sh = (54.0, 14.0)
    elbow = (60.0, 60.0)
    wrist = (80.0, 82.0)

    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(sh[0] - 17, sh[1] - 6), (sh[0] + 16, sh[1] - 6),
               (elbow[0] + 10, elbow[1]), (elbow[0] - 10, elbow[1])], fill=255)
    d.ellipse([sh[0] - 17, sh[1] - 13, sh[0] + 17, sh[1] + 14], fill=255)
    d.ellipse([elbow[0] - 10, elbow[1] - 9, elbow[0] + 10, elbow[1] + 9], fill=255)
    fmask = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(fmask)
    fd.line([elbow, wrist], fill=255, width=13)
    fd.line([elbow, wrist], fill=255, width=13)
    fd.ellipse([wrist[0] - 7, wrist[1] - 7, wrist[0] + 7, wrist[1] + 7], fill=255)
    mask = ImageChops.lighter(mask, fmask)
    img.alpha_composite(char_rig._shade(mask, base, lit, dark))
    d = ImageDraw.Draw(img)

    # folds, drawn along the arm so the eye reads one piece of cloth
    d.line([(sh[0] - 5, sh[1] + 8), (sh[0] - 2, elbow[1] - 6)],
           fill=dark + (140,), width=2)
    d.line([(sh[0] + 7, sh[1] + 8), (elbow[0] + 5, elbow[1] - 5)],
           fill=lit + (95,), width=2)
    d.line([(sh[0] - 8, sh[1] + 22), (sh[0] + 9, sh[1] + 24)],
           fill=t["metal"] + (110,), width=2)

    # gold cuff, square to the forearm, then the hand
    d.line([(wrist[0] - 8, wrist[1] + 3), (wrist[0] + 3, wrist[1] - 8)],
           fill=t["metal"] + (255,), width=14)
    d.line([(wrist[0] - 5, wrist[1] + 2), (wrist[0] + 2, wrist[1] - 5)],
           fill=t["metal_dk"] + (200,), width=9)
    hx, hy = 90, 92
    d.ellipse([hx - 9, hy - 7, hx + 9, hy + 9], fill=skin[0] + (255,))
    d.ellipse([hx - 7, hy - 5, hx + 4, hy + 3], fill=skin[1] + (200,))
    for i in range(3):
        d.line([(hx + 2, hy + 1 + i * 4), (hx + 10, hy + 4 + i * 4)],
               fill=skin[2] + (150,), width=2)
        d.point([(hx + 10, hy + 4 + i * 4)], fill=LIP + (230,))
    d.line([(hx - 6, hy + 1), (hx + 4, hy + 3)], fill=skin[1] + (170,), width=2)

    if not near:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img

# ------------------------------------------------------------------------ legs
def thigh(t):
    W, H = 50, 86
    img = _limb((W, H), [(13, 2), (37, 2), (39, 46), (35, 84), (15, 84), (11, 46)],
                t["robe"], t["robe_lit"], t["robe_dk"])
    d = ImageDraw.Draw(img)
    for x0, x1 in ((18, 20), (33, 31)):
        d.line([(x0, 8), (x1, 80)], fill=t["robe_dk"] + (100,), width=2)
    d.line([(12, 60), (38, 60)], fill=t["robe_dk"] + (90,), width=2)   # knee crease
    if t["pattern"] == "medallion":
        d.ellipse([20, 26, 29, 35], fill=GOLD + (215,))
    else:
        d.line([(20, 30), (29, 27)], fill=t["trim_lit"] + (200,), width=2)
    return img


def shin(t):
    """Silk trouser above a gold anklet; the slipper is the foot part."""
    W, H = 44, 77
    leg = _limb((W, H), [(10, 2), (34, 2), (35, 34), (31, 74), (13, 74), (9, 34)],
                t["robe"], t["robe_lit"], t["robe_dk"])
    d = ImageDraw.Draw(leg)
    for x0, x1 in ((17, 19), (28, 26)):
        d.line([(x0, 8), (x1, 64)], fill=t["robe_dk"] + (100,), width=2)
    d.line([(12, 56), (32, 56)], fill=t["robe_dk"] + (150,), width=2)
    d.line([(11, 66), (33, 66)], fill=t["metal"] + (255,), width=4)
    d.line([(12, 63), (32, 63)], fill=t["metal_lit"] + (170,), width=1)
    return leg


def foot(t):
    """Embroidered slipper, toe to the right, sole on the bottom of the part."""
    W, H = 46, 28
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(5, 9), (24, 6), (43, 14), (42, 26), (7, 27)], fill=255)
    d.ellipse([1, 7, 18, 27], fill=255)
    img = char_rig._shade(mask, t["robe"], t["robe_lit"], t["robe_dk"])
    d = ImageDraw.Draw(img)
    d.line([(6, 26), (42, 25)], fill=(52, 34, 32, 255), width=2)
    d.line([(8, 10), (23, 8)], fill=t["trim_lit"] + (140,), width=2)
    d.polygon([(36, 12), (43, 14), (42, 25), (36, 24)], fill=t["metal"] + (240,))
    d.line([(37, 15), (41, 16)], fill=t["metal_lit"] + (200,), width=1)
    return img


# ---------------------------------------------------------------------- assembly
RIG_JSON = {
    "pivots": {
        "pelvis": [52, 16],
        "arm_n": [54, 14],
        "arm_f": [93, 14],
        "foot_n": [14, 25],
        "foot_f": [14, 25],
    },
}


def parts(t):
    return {
        "torso": torso(t),
        "pelvis": pelvis(t),
        "head": head(t),
        "arm_n": arm(t, near=True),
        "arm_f": arm(t, near=False),
        "thigh_n": thigh(t),
        "thigh_f": thigh(t),
        "shin_n": shin(t),
        "shin_f": shin(t),
        "foot_n": foot(t),
        "foot_f": foot(t),
    }


def write(cid):
    folder = os.path.join(PARTS, cid, "parts")
    os.makedirs(folder, exist_ok=True)
    made = parts(THEMES[cid])
    for name, img in made.items():
        img.save(os.path.join(folder, f"{name}.png"))
    with open(os.path.join(folder, "rig.json"), "w", encoding="utf-8") as f:
        json.dump(RIG_JSON, f, indent=2)
        f.write("\n")
    print(f"  {cid}: {len(made)} parts -> art_src/chars/{cid}/parts/")
    return made


def sheet():
    """Standing render of both, side by side, for checking the painting."""
    rows = []
    for cid in THEMES:
        write(cid)
        rig = char_rig.load_rig(cid)
        rows.append((cid, char_rig.render(rig, char_rig.POSES["stance"])))
    cell = (380, 420)
    img = Image.new("RGBA", (cell[0] * len(rows), cell[1]), (26, 24, 28, 255))
    for i, (_cid, art) in enumerate(rows):
        img.alpha_composite(art, (i * cell[0] + (cell[0] - art.width) // 2,
                                  cell[1] - art.height))
    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    path = os.path.join(ROOT, "artifacts", "women_roster.png")
    img.convert("RGB").save(path)
    print(f"  wrote {os.path.relpath(path, ROOT)}")


def main(argv):
    if "--sheet" in argv:
        sheet()
        return 0
    for cid in THEMES:
        write(cid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
