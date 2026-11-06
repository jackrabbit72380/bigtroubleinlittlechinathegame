"""Jack Burton, painted: white tank, denim jeans, boots and a grin.

Jack's parts used to be cut out of a photographic turnaround by
``jack_cut.py``. That pipeline could never hold together: a photo cut has a
hard straight edge through skin at the shoulder, the crop at the jaw left the
head with no neck at all, and the cut art was sized separately from the
skeleton it was posed on, so the shoulder - and the head hanging off it - sat
above the top of his own body. Every fix was another patch on a seam.

So he is drawn instead, the same way Lightning, Lo Pan and Gracie Law are: flat
sprite tones over a shaded mask, authored in the rig's own units. Part sizes
are derived from ``char_rig.METRICS`` - the torso is exactly ``torso_len``
tall, the head's neck is ``neck_len`` deep, the shin is exactly ``shin``
long - so art and skeleton cannot disagree, which is what broke the photo
version. The rig's figure is short-torsoed and small-headed by realistic
measure (92 of 317), so the head and hands are sized to those numbers too
rather than to a real man's proportions.

Output is exactly what ``char_rig`` expects:

    art_src/chars/jackburton/parts/*.png
    art_src/chars/jackburton/parts/rig.json

Run:  python3 tools/jack_parts.py
"""

from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import char_rig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "art_src", "chars", "jackburton", "parts")

M = char_rig.METRICS
TORSO_LEN = float(M["torso_len"])
NECK_LEN = float(M["neck_len"])
UARM = float(M["uarm"])
FARM = float(M["farm"])
HAND = float(M["hand"])
THIGH = float(M["thigh"])
SHIN = float(M["shin"])
SH_HALF = float(M["shoulder_half"])
HIP_HALF = float(M["hip_half"])

# --------------------------------------------------------------------- palette
SKIN = (222, 170, 136)
SKIN_LIT = (243, 198, 166)
SKIN_DK = (176, 122, 92)
SKIN_DEEP = (122, 78, 58)

TANK = (242, 242, 238)
TANK_LIT = (255, 255, 251)
TANK_DK = (186, 190, 196)

DENIM = (76, 102, 132)
DENIM_LIT = (108, 138, 170)
DENIM_DK = (46, 66, 90)

# Leather, sampled from the boot in jack_faceing_farward.png rather than
# picked by eye: the shaft there sits at rgb(66,39,27), the highlights at
# rgb(110,73,56) and the shadows round rgb(49,28,19). The boot reference art
# arrives as untextured clay, so it cannot supply these - tools/boot_paint.py
# colours that art with this same ramp.
BOOT = (66, 39, 27)
BOOT_LIT = (110, 73, 56)
BOOT_DK = (45, 26, 17)

HAIR = (96, 60, 32)
HAIR_LIT = (138, 94, 54)
HAIR_DK = (52, 32, 16)

BROW = (54, 34, 20)
LIP = (150, 88, 76)
BUCKLE = (198, 178, 120)

# The chest emblem is the real illustration, reduced, not a shape-by-shape
# redraw. It was drawn in code first: at the 20px the chest occupies in game
# that reduction collapsed into a pink arc with a blank face, so the painted
# version is gone and this path is used instead. Drop the transparent PNG here
# and the torso picks it up; with no file the chest stays plain, which is what
# this screenpack shipped before.
REF_EMBLEM = os.path.join(ROOT, "art_src", "chars", "jackburton", "ref", "emblem.png")


def _blank(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _capsule(draw, p0, p1, r0, r1, fill=255):
    """A tapered limb between two joints, as a mask on ``draw``."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    span = (dx * dx + dy * dy) ** 0.5 or 1.0
    nx, ny = -dy / span, dx / span
    draw.polygon([(p0[0] + nx * r0, p0[1] + ny * r0),
                  (p1[0] + nx * r1, p1[1] + ny * r1),
                  (p1[0] - nx * r1, p1[1] - ny * r1),
                  (p0[0] - nx * r0, p0[1] - ny * r0)], fill=fill)
    draw.ellipse([p0[0] - r0, p0[1] - r0, p0[0] + r0, p0[1] + r0], fill=fill)
    draw.ellipse([p1[0] - r1, p1[1] - r1, p1[0] + r1, p1[1] + r1], fill=fill)


def _emblem_ref(width):
    """The chest graphic from the reference art, resampled onto the chest.

    Two things matter at this size. The art is cropped to its own pixels first,
    so the illustration's own white margin does not shrink the mark, and the
    resize runs on premultiplied alpha: a straight RGBA downscale pulls the ink
    outline into the pale face and greys the whole mark out.
    """
    if not os.path.isfile(REF_EMBLEM):
        return None
    art = Image.open(REF_EMBLEM).convert("RGBA")
    box = art.getchannel("A").getbbox()
    if box:
        art = art.crop(box)
    height = max(6, int(round(width * art.height / max(1, art.width))))
    small = art.convert("RGBa").resize((width, height), Image.LANCZOS).convert("RGBA")
    # The flat art already has the ink and the colour; the only thing the drop to
    # 48px costs is edge definition, so it is sharpened and nothing else. (The
    # saturation and quantise that used to be here were for keying the print off
    # a tank-top mock-up, where the fabric shading greyed it out.)
    rgb = small.convert("RGB").filter(
        ImageFilter.UnsharpMask(radius=0.9, percent=70, threshold=0))
    out = rgb.convert("RGBA")
    out.putalpha(small.getchannel("A"))
    return out


# ------------------------------------------------------------------------ torso
def torso():
    """Bare shoulders, a white tank with a scooped neck, and his belt.

    The art is exactly ``torso_len`` tall with its pivot at the hip, so the
    shoulder joint - and everything hung off it - sits on the top edge.
    """
    W = int(SH_HALF * 2 + 14)
    H = int(TORSO_LEN)
    cx = W // 2
    body = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(body)
    d.polygon([(cx - SH_HALF - 2, 8), (cx - SH_HALF + 10, 0),
               (cx + SH_HALF - 10, 0), (cx + SH_HALF + 2, 8),
               (cx + HIP_HALF + 8, int(H * 0.74)),
               (cx + HIP_HALF, H - 1), (cx - HIP_HALF, H - 1),
               (cx - HIP_HALF - 8, int(H * 0.74))], fill=255)
    d.ellipse([cx - SH_HALF + 2, 0, cx + SH_HALF - 2, 17], fill=255)
    # a torso this short is nearly all ribcage: keep the waist narrow
    d.polygon([(cx - HIP_HALF - 6, int(H * 0.55)), (cx + HIP_HALF + 6, int(H * 0.55)),
               (cx + HIP_HALF, H - 1), (cx - HIP_HALF, H - 1)], fill=255)
    img = char_rig._shade(body, SKIN, SKIN_LIT, SKIN_DEEP)

    tank = Image.new("L", (W, H), 0)
    td = ImageDraw.Draw(tank)
    # The neckline must CLOSE: left unclosed, the two strap edges ran parallel
    # down to the belt and left a bare strip of skin down his whole chest.
    td.polygon([(cx - SH_HALF + 5, 5), (cx - SH_HALF + 15, 2),
                (cx - 11, 22), (cx - 7, 34), (cx + 7, 34), (cx + 11, 22),
                (cx + SH_HALF - 15, 2), (cx + SH_HALF - 5, 5),
                (cx + HIP_HALF + 6, int(H * 0.80)),
                (cx - HIP_HALF - 6, int(H * 0.80))], fill=255)
    img.alpha_composite(char_rig._shade(tank, TANK, TANK_LIT, TANK_DK))
    d = ImageDraw.Draw(img)

    # --- the chest emblem -------------------------------------------------
    # Width comes off the shoulders, so it stays on the chest if the rig's
    # metrics are ever re-measured. Height follows the art's own aspect.
    emblem = _emblem_ref(max(10, int(SH_HALF * 1.20)))
    if emblem is not None:
        img.alpha_composite(emblem, (cx - emblem.width // 2, int(H * 0.24)))

    for sx in (-1, 1):
        # one soft fold under each pectoral, nothing drawn across the chest
        d.arc([cx + sx * 5 - 12, 40, cx + sx * 5 + 12, 56], 200, 340,
              fill=TANK_DK + (120,), width=1)
        d.line([(cx + sx * 9, 8), (cx + sx * 26, 10)], fill=SKIN_LIT + (130,), width=1)
    d.line([(cx - 14, int(H * 0.66)), (cx + 14, int(H * 0.66))],
           fill=TANK_DK + (80,), width=1)

    d.rectangle([cx - HIP_HALF - 4, int(H * 0.82), cx + HIP_HALF + 4, H - 1],
                fill=BOOT_DK + (255,))
    d.rectangle([cx - 7, int(H * 0.82) + 2, cx + 7, H - 3], fill=BUCKLE + (255,))
    d.rectangle([cx - 3, int(H * 0.82) + 5, cx + 3, H - 6], fill=BOOT_DK + (255,))
    return img


# ------------------------------------------------------------------------ pelvis
def pelvis():
    W = int(HIP_HALF * 2 + 18)
    H = 32
    cx = W // 2
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(cx - HIP_HALF - 4, 4), (cx + HIP_HALF + 4, 4),
               (cx + HIP_HALF, H - 1), (cx - HIP_HALF, H - 1)], fill=255)
    img = char_rig._shade(mask, DENIM, DENIM_LIT, DENIM_DK)
    d = ImageDraw.Draw(img)
    d.line([(cx, 8), (cx, H - 2)], fill=DENIM_DK + (150,), width=1)
    d.line([(cx - HIP_HALF - 2, 6), (cx + HIP_HALF + 2, 6)],
           fill=BOOT_DK + (255,), width=2)
    return img


# -------------------------------------------------------------------------- head
def head():
    """Long-haired, stubbled, smirking - and with an actual neck.

    The head is sized to the rig's own head bone rather than to a real man's
    proportions: the default figure is 317 units tall with a 42-unit head, so
    a correctly proportioned human head here would be a bobblehead. The neck
    is painted into this part, ``neck_len`` plus a margin deep, so the jaw can
    never end on air above the collar the way the photo cut did.
    """
    fw, fh = 34, 46
    depth = int(NECK_LEN + 2)
    W, H = fw + 24, fh + depth
    cx = W // 2
    img = _blank((W, H))

    back = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(back)
    bd.ellipse([cx - 17, 1, cx + 17, 44], fill=255)
    bd.polygon([(cx - 17, 18), (cx - 15, fh + 12), (cx - 6, fh + 8),
                (cx - 4, 40), (cx + 4, 40), (cx + 6, fh + 8),
                (cx + 15, fh + 12), (cx + 17, 18)], fill=255)
    img.alpha_composite(char_rig._shade(back, HAIR, HAIR_LIT, HAIR_DK))

    neck = Image.new("L", (W, H), 0)
    nd = ImageDraw.Draw(neck)
    nd.polygon([(cx - 7, fh - 8), (cx + 7, fh - 8),
                (cx + 9, H - 2), (cx - 9, H - 2)], fill=255)
    neck = neck.filter(ImageFilter.GaussianBlur(0.8))
    skin_neck = char_rig._shade(neck, SKIN_DK, SKIN, SKIN_DEEP)
    jawshade = Image.new("L", (W, H), 0)
    jd = ImageDraw.Draw(jawshade)
    for i in range(8):
        jd.line([(0, fh - 9 + i), (W, fh - 9 + i)], fill=int(130 * (1 - i / 8.0)))
    dark = Image.new("RGBA", (W, H), SKIN_DEEP + (0,))
    dark.putalpha(ImageChops.multiply(
        jawshade.filter(ImageFilter.GaussianBlur(1.6)), neck))
    skin_neck = Image.alpha_composite(skin_neck, dark)
    fade = Image.new("L", (W, H), 255)
    fd = ImageDraw.Draw(fade)
    for i in range(7):
        fd.line([(0, H - 7 + i), (W, H - 7 + i)], fill=int(255 * (1 - i / 6.0)))
    skin_neck.putalpha(ImageChops.multiply(skin_neck.getchannel("A"), fade))
    img.alpha_composite(skin_neck)

    face = Image.new("L", (W, H), 0)
    fdw = ImageDraw.Draw(face)
    fdw.ellipse([cx - 13, 6, cx + 13, 40], fill=255)
    fdw.polygon([(cx - 12, 24), (cx - 6, 44), (cx + 6, 44), (cx + 12, 24)],
                fill=255)
    img.alpha_composite(char_rig._shade(face, SKIN, SKIN_LIT, SKIN_DK))
    d = ImageDraw.Draw(img)

    stub = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(stub)
    sd.polygon([(cx - 11, 28), (cx - 7, 44), (cx + 7, 44), (cx + 11, 28)],
               fill=105)
    img.alpha_composite(Image.merge("RGBA", (
        Image.new("L", (W, H), 124), Image.new("L", (W, H), 90),
        Image.new("L", (W, H), 66),
        stub.filter(ImageFilter.GaussianBlur(1.4)))))

    for sx in (-1, 1):
        ex = cx + sx * 6
        d.line([(ex - 5, 19 + (1 if sx > 0 else 0)), (ex + 4, 17)],
               fill=BROW + (235,), width=1)
        d.ellipse([ex - 4, 20, ex + 4, 26], fill=(238, 236, 232, 255))
        d.ellipse([ex - 2, 21, ex + 2, 25], fill=(96, 128, 150, 255))
        d.point([(ex, 22)], fill=(20, 16, 14, 255))
        d.line([(ex - 4, 21), (ex + 4, 21)], fill=SKIN_DEEP + (140,), width=1)
    d.line([(cx + 1, 25), (cx, 32), (cx + 2, 33)], fill=SKIN_DK + (170,), width=1)
    d.line([(cx - 6, 37), (cx, 36), (cx + 5, 34)], fill=LIP + (230,), width=1)
    d.line([(cx - 5, 38), (cx + 4, 36)], fill=SKIN_DEEP + (130,), width=1)

    front = Image.new("L", (W, H), 0)
    frd = ImageDraw.Draw(front)
    frd.polygon([(cx - 15, 14), (cx - 7, 4), (cx + 4, 3), (cx + 13, 8),
                 (cx + 15, 18), (cx + 11, 15), (cx + 5, 9), (cx - 4, 10),
                 (cx - 9, 16), (cx - 12, 32), (cx - 15, 27)], fill=255)
    frd.polygon([(cx - 13, 16), (cx - 10, 16), (cx - 9, 34), (cx - 13, 35)],
                fill=255)
    frd.polygon([(cx + 11, 15), (cx + 14, 17), (cx + 12, 33), (cx + 9, 32)],
                fill=255)
    img.alpha_composite(char_rig._shade(front, HAIR, HAIR_LIT, HAIR_DK))
    d = ImageDraw.Draw(img)
    d.line([(cx - 12, 11), (cx + 8, 7)], fill=HAIR_LIT + (110,), width=1)
    return img


# -------------------------------------------------------------------------- arms
def arm(near=True):
    """One bare arm hanging from the shoulder, elbow just outboard of it.

    Drawn hanging rather than in a guard, because the idle pose swings each arm
    down about the shoulder; an L-shaped arm rotated down drives its own elbow
    into the ribs.
    """
    sx, sy = 22.0, 12.0
    ex, ey = sx + 5.0, sy + UARM
    wx, wy = ex + 6.0, ey + FARM
    W = int(max(ex, wx) + 16)
    H = int(wy + HAND + 4)
    img = _blank((W, H))
    base, lit, dark = (SKIN, SKIN_LIT, SKIN_DK) if near else (
        (SKIN_DK, SKIN, SKIN_DEEP))

    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    _capsule(md, (sx, sy), (ex, ey), 11.0, 9.0)
    img.alpha_composite(char_rig._shade(mask, base, lit, dark))

    fmask = Image.new("L", (W, H), 0)
    fmd = ImageDraw.Draw(fmask)
    _capsule(fmd, (ex, ey), (wx, wy), 9.0, 7.0)
    img.alpha_composite(char_rig._shade(fmask, base, lit, dark))
    d = ImageDraw.Draw(img)

    d.arc([sx - 10, sy - 1, sx + 9, sy + 19], 200, 340, fill=lit + (150,), width=2)
    d.line([(sx - 7, sy + 16), (ex - 5, ey - 3)], fill=dark + (110,), width=1)

    # watch on the wrist, band and face
    d.line([(wx - 8, wy - 9), (wx + 6, wy - 10)], fill=BOOT_DK + (255,), width=4)
    d.ellipse([wx - 4, wy - 15, wx + 4, wy - 7], fill=BOOT_DK + (255,))
    d.ellipse([wx - 2, wy - 13, wx + 2, wy - 9], fill=(214, 214, 200, 255))

    # fist
    d.ellipse([wx - 8, wy - 3, wx + 8, wy + HAND], fill=base + (255,))
    d.ellipse([wx - 6, wy - 1, wx + 2, wy + 6], fill=lit + (190,))
    for i in range(3):
        d.line([(wx - 6, wy + 5 + i * 4), (wx + 7, wy + 6 + i * 4)],
               fill=dark + (140,), width=1)

    if not near:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img


# -------------------------------------------------------------------------- legs
def thigh():
    W, H = 38, int(THIGH)
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(7, 1), (31, 1), (33, int(H * 0.6)), (29, H - 1),
               (9, H - 1), (5, int(H * 0.6))], fill=255)
    img = char_rig._shade(mask, DENIM, DENIM_LIT, DENIM_DK)
    d = ImageDraw.Draw(img)
    d.line([(11, 4), (9, H - 4)], fill=DENIM_DK + (110,), width=1)
    d.line([(26, 5), (28, H - 6)], fill=DENIM_LIT + (90,), width=1)
    d.line([(7, int(H * 0.2)), (31, int(H * 0.2))], fill=DENIM_DK + (110,), width=1)
    return img


def shin():
    """Denim to the knee, then the tall boot; art is exactly shin tall."""
    W, H = 34, int(SHIN)
    leg = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(leg)
    d.polygon([(6, 1), (28, 1), (29, int(H * 0.42)), (26, H - 4),
               (8, H - 4), (5, int(H * 0.42))], fill=255)
    img = char_rig._shade(leg, DENIM, DENIM_LIT, DENIM_DK)

    bootmask = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(bootmask)
    bd.polygon([(5, int(H * 0.34)), (29, int(H * 0.34)),
                (26, H - 3), (7, H - 3)], fill=255)
    bd.rectangle([6, H - 6, 27, H - 1], fill=255)
    img.alpha_composite(char_rig._shade(bootmask, BOOT, BOOT_LIT, BOOT_DK))
    d = ImageDraw.Draw(img)
    # The reference boot, in the order its shapes read at sprite size: a stiff
    # cuff, a seam running down the outer side, a row of buttons on the outer
    # edge, and a treaded sole. The button row is what identifies the boot when
    # the whole man is 106px tall, so it gets the contrast; seams stay faint.
    top = int(H * 0.34)
    d.line([(4, top), (30, top)], fill=BOOT_LIT + (210,), width=1)
    d.line([(5, top + 3), (29, top + 3)], fill=BOOT_DK + (150,), width=1)
    d.line([(25, top + 5), (24, H - 6)], fill=BOOT_LIT + (120,), width=1)
    for i in range(8):
        by = top + 6 + i * max(2, (H - 14 - top) // 8)
        if by > H - 8:
            break
        d.ellipse([27, by, 29, by + 2], fill=BOOT_LIT + (235,))
        d.point([(28, by + 1)], fill=BOOT_DK + (235,))
    d.rectangle([6, H - 4, 27, H - 2], fill=BOOT_DK + (255,))
    for x in range(7, 27, 3):
        d.point([(x, H - 3)], fill=BOOT_LIT + (120,))
    return img


def foot():
    """Boot toe to the right; the pivot is the ankle, above the sole."""
    W, H = 40, 26
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(5, 3), (20, 1), (38, 12), (37, H - 2), (6, H - 2)], fill=255)
    d.ellipse([1, 1, 16, H - 1], fill=255)
    img = char_rig._shade(mask, BOOT, BOOT_LIT, BOOT_DK)
    d = ImageDraw.Draw(img)
    d.line([(5, H - 4), (37, H - 5)], fill=BOOT_DK + (255,), width=2)
    # tread notches on the sole edge and the toe-cap seam from the reference
    for x in range(7, 36, 3):
        d.point([(x, H - 3)], fill=BOOT_LIT + (120,))
    d.arc([16, 2, 34, H - 3], 300, 40, fill=BOOT_LIT + (120,), width=1)
    d.line([(7, 7), (20, 5)], fill=BOOT_LIT + (140,), width=1)
    return img


# -------------------------------------------------------------------------- main
def main():
    os.makedirs(PARTS, exist_ok=True)
    parts = dict(
        torso=torso(), pelvis=pelvis(), head=head(),
        arm_n=arm(near=True), arm_f=arm(near=False),
        thigh_n=thigh(), thigh_f=thigh(),
        shin_n=shin(), shin_f=shin(),
        foot_n=foot(), foot_f=foot(),
    )
    for name, img in parts.items():
        img.save(os.path.join(PARTS, f"{name}.png"))

    # Pivots are stated here, in the part's own pixels, and every one of them
    # is a joint the rig poses around: the hip for the torso, the neck for the
    # head, the shoulder for an arm, the knee for a shin, the ankle for a foot.
    pivots = {
        "torso": [parts["torso"].width // 2, parts["torso"].height - 1],
        "pelvis": [parts["pelvis"].width // 2, 12],
        "head": [parts["head"].width // 2, 46],
        "arm_n": [22, 12],
        "arm_f": [parts["arm_f"].width - 22, 12],
        "thigh_n": [19, 4],
        "thigh_f": [19, 4],
        "shin_n": [17, 3],
        "shin_f": [17, 3],
        "foot_n": [10, 12],
        "foot_f": [10, 12],
    }
    rig = dict(
        scale=1.0,
        pivots=pivots,
        angles={name: 0.0 for name in ("head", "torso", "pelvis")},
    )
    with open(os.path.join(PARTS, "rig.json"), "w", encoding="utf-8") as f:
        json.dump(rig, f, indent=2)
        f.write("\n")

    for name in sorted(parts):
        w, h = parts[name].size
        print(f"  {name:10} {w:3}x{h:<4} pivot {pivots[name]}")
    print(f"wrote {len(parts)} painted parts -> art_src/chars/jackburton/parts/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
