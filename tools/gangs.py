"""The Chang Sing and the Wing Kong: twelve gang fighters for the rig.

The two gangs dress like Kung Fu Man, so each member is the same puppet body
painted in his gang's colours, with his own head, headwear and weapon:

  Chang Sing   tan gi over black underclothes, black sash, gold headband.
               Weapon: an extendable staff, held across the body.
  Wing Kong    black gi with red trim and a red sash. Weapon: a big machete.

Every member carries his weapon in his near fist for every frame, which is what
the gangs do, and it is painted into the hand part so it swings with the arm
without any per-frame attachment work.

Output is what ``char_rig`` and ``bake_char`` expect:

    art_src/chars/<id>/parts/*.png        (front set: portraits, win pose)
    art_src/chars/<id>/parts*/rig.json
    art_src/chars/<id>/parts_side/*.png   (profile set: every fight pose)

Run:  python3 tools/gangs.py [--sheet]
"""

from __future__ import annotations

import json
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import char_rig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "art_src", "chars")

SKIN = (208, 162, 126)
SKIN_LIT = (238, 198, 162)
SKIN_DK = (146, 104, 76)

# gang -> cloth, underlayer, sash, trim, band
GANG = {
    "changsing": dict(
        cloth=(186, 162, 120), cloth_lit=(216, 196, 156), cloth_dk=(120, 100, 68),
        under=(36, 34, 32), under_lit=(62, 58, 54), under_dk=(18, 16, 16),
        sash=(42, 38, 34), sash_lit=(78, 70, 60), trim=(70, 62, 50),
        band=(196, 160, 62), band_lit=(232, 202, 108), band_dk=(120, 94, 30),
    ),
    "wingkong": dict(
        cloth=(40, 40, 46), cloth_lit=(66, 66, 76), cloth_dk=(16, 16, 20),
        under=(28, 26, 30), under_lit=(50, 46, 52), under_dk=(10, 10, 12),
        sash=(146, 30, 34), sash_lit=(190, 54, 56), trim=(150, 34, 38),
        band=(150, 32, 36), band_lit=(196, 58, 58), band_dk=(84, 14, 18),
    ),
}

# id suffix, display name, head style, weapon, build (torso/limb scale)
MEMBERS = [
    ("changsing", [
        ("bo", "Bo the Doorman", "flat", "staff", 1.00),
        ("lin", "Lin the Runner", "ponytail", "staff", 1.00),
        ("shi", "Shi the Brawler", "spike", "staff", 1.00),
        ("han", "Han the Elder", "topknot", "staff", 1.00),
        ("wei", "Wei the Quiet", "long", "staff", 1.00),
        ("tam", "Tam Longarm", "bandana", "staff", 1.00),
    ]),
    ("wingkong", [
        ("gou", "Gou the Enforcer", "shaved", "machete", 1.00),
        ("ma", "Ma Redhand", "bandana", "machete", 1.00),
        ("zhao", "Zhao the Butcher", "bald", "machete", 1.00),
        ("lu", "Lu the Wire", "topknot", "machete", 1.00),
        ("gerald", "Gold Gun Gerald", "shaved", "pistols", 1.00),
        ("hatchet", "Hatchet Man", "long", "hatchet", 1.00),
        ("bai", "Bai the Lookout", "bandana", "machete", 1.00),
        ("shen", "Shen the Bruiser", "topknot", "staff", 1.00),
    ]),
]


# ------------------------------------------------------------------ primitives
def _mask(size, pts):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


def _body(size, mask, base, lit, dark):
    return char_rig._shade(mask, base, lit, dark)


def _tinted(g, k):
    """The gang's palette, lightened or darkened for one member.

    Gang colours are the uniform, but six men in identical cloth look like one
    man copied five times. A few percent either way - one man's gi sun-bleached,
    the next one's muddy - reads as six members without breaking either gang's
    colour.
    """
    if abs(k - 1.0) < 1e-6:
        return g
    return {key: tuple(max(0, min(255, int(round(c * k)))) for c in val)
            for key, val in g.items()}


def _torso(g):
    """104 x 110 gi jacket, hip at the bottom centre."""
    W, H = 104, 110
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.polygon([(12, 16), (92, 16), (86, 58), (78, 110), (26, 110), (18, 58)], fill=255)
    d.ellipse([0, 2, 58, 54], fill=255)
    d.ellipse([46, 2, 104, 54], fill=255)
    img = _body((W, H), m, g["cloth"], g["cloth_lit"], g["cloth_dk"])
    d = ImageDraw.Draw(img)

    # black underlayer showing at the neck opening
    d.polygon([(38, 4), (66, 4), (60, 30), (52, 40), (44, 30)], fill=g["under"] + (255,))
    # crossed lapels of the jacket
    d.polygon([(30, 8), (44, 6), (52, 42), (40, 30)], fill=g["cloth_lit"] + (235,))
    d.polygon([(74, 8), (60, 6), (52, 42), (64, 30)], fill=g["cloth_dk"] + (210,))
    d.line([(30, 10), (52, 46)], fill=g["trim"] + (200,), width=2)
    d.line([(74, 10), (52, 46)], fill=g["trim"] + (170,), width=2)
    # sash round the waist
    d.polygon([(20, 84), (84, 84), (82, 104), (22, 104)], fill=g["sash"] + (255,))
    d.line([(22, 86), (82, 86)], fill=g["sash_lit"] + (190,), width=2)
    d.line([(24, 100), (80, 100)], fill=g["sash_lit"] + (90,), width=1)
    for i in range(3):                       # cloth folds
        x = 34 + i * 18
        d.line([(x, 46), (x - 3, 82)], fill=g["cloth_dk"] + (70,), width=1)
    return img


def _pelvis(g):
    """62 x 38 trousers, hip line 25% down."""
    W, H = 62, 38
    m = _mask((W, H), [(3, 4), (59, 4), (55, 38), (34, 38), (31, 20), (28, 38), (7, 38)])
    img = _body((W, H), m, g["cloth"], g["cloth_lit"], g["cloth_dk"])
    d = ImageDraw.Draw(img)
    d.line([(5, 16), (57, 16)], fill=g["sash"] + (235,), width=4)
    # sash tail hanging at the left hip
    d.polygon([(4, 18), (13, 20), (11, 36), (3, 34)], fill=g["sash"] + (250,))
    d.line([(31, 18), (31, 34)], fill=g["cloth_dk"] + (200,), width=2)
    return img


def _head(style, g, side, skin=(SKIN, SKIN_LIT, SKIN_DK)):
    """62 x 48 head, neck at the bottom centre, facing +x when side."""
    W, H = 62, 48
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.ellipse([12, 2, 50, 34], fill=255)              # cranium
    d.polygon([(15, 18), (47, 18), (44, 38), (31, 46), (18, 38)], fill=255)  # jaw
    d.rectangle([27, 40, 35, 48], fill=255)            # neck
    img = _body((W, H), m, skin[0], skin[1], skin[2])
    d = ImageDraw.Draw(img)
    hair, hl, hd = g["cloth_dk"], g["cloth"], (12, 10, 10)

    # ---- hair and headwear
    if style in ("flat", "spike", "bandana", "shaved", "bald"):
        d.ellipse([10, 0, 52, 22], fill=(34, 26, 20, 255))
    if style == "ponytail":
        d.ellipse([10, 0, 52, 22], fill=(34, 26, 20, 255))
        d.polygon([(12, 8), (4, 22), (2, 40), (10, 30), (16, 14)], fill=(34, 26, 20, 255))
    if style == "long":
        d.ellipse([10, 0, 52, 22], fill=(34, 26, 20, 255))
        d.polygon([(12, 6), (3, 20), (2, 46), (12, 44), (16, 16)], fill=(34, 26, 20, 255))
    if style == "topknot":
        d.ellipse([10, 0, 52, 20], fill=(34, 26, 20, 255))
        d.ellipse([24, -6, 38, 8], fill=(34, 26, 20, 255))
    if style == "bald":
        d.ellipse([12, 2, 50, 18], fill=skin[1] + (255,))
    if style == "spike":
        for i in range(4):
            x = 16 + i * 8
            d.polygon([(x, 14), (x + 5, 0), (x + 8, 14)], fill=(34, 26, 20, 255))

    # ---- headband: the gang's colour, tied at the back
    d.rectangle([11, 12, 51, 19], fill=g["band"] + (255,))
    d.line([(12, 13), (50, 13)], fill=g["band_lit"] + (210,), width=1)
    d.polygon([(6, 13), (12, 11), (12, 20), (5, 21)], fill=g["band_dk"] + (255,))
    d.polygon([(4, 18), (11, 19), (7, 28)], fill=g["band_dk"] + (230,))   # tail

    # ---- face
    if side:
        d.line([(48, 20), (55, 24), (47, 27)], fill=skin[2] + (220,), width=2)  # nose
        d.line([(34, 22), (43, 22)], fill=(250, 246, 240, 255), width=3)
        d.ellipse([37, 20, 40, 24], fill=(44, 30, 22, 255))
        d.line([(32, 17), (43, 18)], fill=(34, 24, 18, 240), width=2)
        d.line([(36, 34), (44, 33)], fill=(110, 58, 46, 230), width=2)
    else:
        for ex in (23, 39):
            d.line([(ex - 4, 22), (ex + 4, 22)], fill=(250, 246, 240, 255), width=3)
            d.ellipse([ex - 1, 20, ex + 2, 24], fill=(44, 30, 22, 255))
            d.line([(ex - 6, 17), (ex + 6, 18)], fill=(34, 24, 18, 240), width=2)
        d.line([(31, 24), (29, 31)], fill=skin[2] + (160,), width=2)
        d.line([(24, 36), (38, 36)], fill=(110, 58, 46, 230), width=2)

    if style in ("bald", "shaved", "topknot"):
        d.arc([22, 30, 44, 46], 200, 340, fill=(40, 30, 24, 170), width=2)   # beard
    return img


def _uarm(g, sleeve, banded=False):
    """34 x 62 upper arm: short gi sleeve over a bare bicep."""
    W, H = 34, 62
    m = char_rig._profile_shape((W, H), [(0.0, 0.86), (0.2, 1.0), (0.62, 0.9), (1.0, 0.8)])
    img = _body((W, H), m, SKIN, SKIN_LIT, SKIN_DK)
    d = ImageDraw.Draw(img)
    sleeve_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sleeve_mask).rectangle([0, 0, W, 30], fill=255)
    sleeve_mask = Image.composite(sleeve_mask, Image.new("L", (W, H), 0), m)
    img.alpha_composite(_body((W, H), sleeve_mask, sleeve[0], sleeve[1], sleeve[2]))
    d = ImageDraw.Draw(img)
    d.line([(2, 30), (32, 30)], fill=g["trim"] + (200,), width=2)
    if banded:
        d.line([(3, 8), (30, 8)], fill=g["band"] + (150,), width=2)
    d.line([(14, 36), (17, 58)], fill=SKIN_DK + (90,), width=2)
    return img


def _farm(g):
    """28 x 52 forearm in the gang's underlayer, wrapped at the wrist."""
    W, H = 28, 52
    m = char_rig._profile_shape((W, H), [(0.0, 0.9), (0.2, 1.0), (0.7, 0.86), (1.0, 0.76)])
    img = _body((W, H), m, g["under"], g["under_lit"], g["under_dk"])
    d = ImageDraw.Draw(img)
    for i in range(3):
        y = 34 + i * 5
        d.line([(2, y), (26, y - 1)], fill=g["cloth"] + (150,), width=2)
    d.line([(2, 6), (26, 6)], fill=g["trim"] + (190,), width=2)
    return img


def _fist():
    W, H = 30, 30
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.ellipse([1, 1, 29, 27], fill=255)
    d.rectangle([1, 12, 29, 28], fill=255)
    return _body((W, H), m, SKIN, SKIN_LIT, SKIN_DK)


ARM_CANVAS = (370, 270)
SHOULDER = (46, 30)


def _rot(cx, cy, ang, dist):
    """Point ``dist`` along a limb angle: 0 hangs down, 90 points forward.

    Same convention as ``char_rig._seg``: screen y grows downward, so a 0-degree
    limb adds to y. With the sign inverted the elbow landed above the shoulder
    and the whole forearm and weapon were painted off the top of the canvas.
    """
    a = math.radians(ang)
    return (cx + math.sin(a) * dist, cy + math.cos(a) * dist)


def _arm(g, sleeve, banded, weapon):
    """One bent arm in the guard the rig draws: sleeve, forearm, fist, weapon.

    The rig poses an arm as a single piece cut in its guard, so the three
    segments and the weapon are composed here into that one piece. The weapon
    is painted in, which means every frame holds it, as the gangs do.
    """
    W, H = ARM_CANVAS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    up_a, fore_a = 12.0, 112.0
    shoulder = SHOULDER
    elbow = _rot(shoulder[0], shoulder[1], up_a, 62.0)
    wrist = _rot(elbow[0], elbow[1], fore_a, 52.0)

    char_rig._place(img, dict(image=_uarm(g, sleeve, banded),
                              pivot=(17.0, 0.0), base=0.0), up_a, shoulder)
    char_rig._place(img, dict(image=_farm(g), pivot=(14.0, 0.0), base=0.0),
                    fore_a, elbow)
    fist = _fist()
    img.alpha_composite(fist, (round(wrist[0] - 15), round(wrist[1] - 15)))

    d = ImageDraw.Draw(img)
    if weapon == "staff":
        back = _rot(wrist[0], wrist[1], fore_a, -70)
        tip = _rot(wrist[0], wrist[1], fore_a, 150)
        d.line([back, tip], fill=(44, 30, 18, 255), width=12)
        d.line([back, tip], fill=(92, 68, 40, 255), width=8)
        d.line([back, tip], fill=(140, 108, 68, 200), width=3)
        for f in (0.18, 0.46, 0.74):
            p = _rot(wrist[0], wrist[1], fore_a, -80 + 245 * f)
            d.ellipse([p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5],
                      fill=(206, 184, 132, 240), outline=(58, 44, 30, 255))
        for p in (back, tip):
            d.ellipse([p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7],
                      fill=(66, 50, 34, 255), outline=(40, 28, 18, 255))
    elif weapon == "machete":
        grip = _rot(wrist[0], wrist[1], fore_a, -34)
        heel = _rot(wrist[0], wrist[1], fore_a, 6)
        tip = _rot(wrist[0], wrist[1], fore_a, 112)
        a = math.radians(fore_a)
        nx, ny = math.cos(a), math.sin(a)

        def off(p, wdt):
            return (p[0] + nx * wdt, p[1] + ny * wdt)

        d.line([grip, heel], fill=(58, 40, 30, 255), width=9)
        d.line([_rot(wrist[0], wrist[1], fore_a, 0),
                _rot(wrist[0], wrist[1], fore_a, 12)],
               fill=(150, 32, 36, 255), width=6)
        d.polygon([off(heel, -7), off(tip, -10), off(tip, 10), off(heel, 7)],
                  fill=(198, 204, 210, 255))
        d.line([off(heel, -7), off(tip, -10)], fill=(242, 246, 250, 245), width=2)
        d.line([off(heel, 7), off(tip, 10)], fill=(120, 128, 136, 220), width=2)
        d.line([off(heel, 0), off(tip, 0)], fill=(160, 168, 176, 90), width=1)
    return img


def _thigh(g):
    W, H = 42, 74
    m = char_rig._profile_shape((W, H), [(0.0, 0.86), (0.22, 1.0), (0.7, 0.9), (1.0, 0.82)])
    img = _body((W, H), m, g["cloth"], g["cloth_lit"], g["cloth_dk"])
    d = ImageDraw.Draw(img)
    d.line([(16, 12), (18, 68)], fill=g["cloth_dk"] + (80,), width=2)
    return img


def _shin(g):
    W, H = 34, 77
    m = char_rig._profile_shape((W, H), [(0.0, 0.9), (0.24, 1.0), (0.75, 0.88), (1.0, 0.8)])
    img = _body((W, H), m, g["cloth"], g["cloth_lit"], g["cloth_dk"])
    d = ImageDraw.Draw(img)
    # wrapped ankle and a low black slipper cuff
    for i in range(4):
        y = 44 + i * 6
        d.line([(2, y), (32, y)], fill=g["under"] + (170,), width=3)
    d.rectangle([1, 66, 33, 77], fill=g["under"] + (255,))
    return img


def _foot(g):
    """Toe pointing +x, sole flat: 44 x 36, heel near the left."""
    W, H = 44, 36
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.polygon([(4, 6), (26, 4), (42, 18), (41, 27), (5, 30)], fill=255)
    d.ellipse([2, 4, 22, 32], fill=255)
    img = _body((W, H), m, g["under"], g["under_lit"], g["under_dk"])
    d = ImageDraw.Draw(img)
    d.rectangle([3, 27, 44, 33], fill=(196, 192, 184, 255))
    d.line([(4, 8), (40, 18)], fill=(70, 66, 60, 150), width=2)
    return img


# ------------------------------------------------------------------ one fighter
def parts_for(gang, style, weapon, side, tint=1.0):
    g = _tinted(GANG[gang], tint)
    banded = gang == "changsing"
    if banded:
        sleeve = (g["under"], g["under_lit"], g["under_dk"])
    else:
        sleeve = (g["cloth"], g["cloth_lit"], g["cloth_dk"])
    skin = (SKIN, SKIN_LIT, SKIN_DK)
    if style == "topknot":
        skin = (196, 148, 112), (226, 186, 148), (136, 96, 70)
    out = {
        "torso": _torso(g),
        "pelvis": _pelvis(g),
        "head": _head(style, g, side, skin),
        "arm_n": _arm(g, sleeve, banded, weapon),
        "arm_f": _arm(g, sleeve, banded, ""),
        "thigh_n": _thigh(g), "thigh_f": _thigh(g),
        "shin_n": _shin(g), "shin_f": _shin(g),
        "foot_n": _foot(g), "foot_f": _foot(g),
    }
    return out


def rig_json():
    return {
        "scale": 1.0,
        "canvas": [360, 400],
        "axis": [180, 372],
        "pivots": {
            "pelvis": [31, 9],
            "foot_n": [10, 22],
            "foot_f": [10, 22],
            "arm_n": [46, 30],
            "arm_f": [46, 30],
        },
    }


def write_member(gang, slug, name, style, weapon, build, tint=1.0):
    cid = f"{gang}_{slug}"
    for sub, side in (("parts", False), ("parts_side", True)):
        folder = os.path.join(PARTS, cid, sub)
        os.makedirs(folder, exist_ok=True)
        for pname, img in parts_for(gang, style, weapon, side, tint).items():
            if build != 1.0 and pname in ("thigh_n", "thigh_f", "shin_n", "shin_f"):
                k = build
                img = img.resize((max(1, round(img.width * k)),
                                  max(1, round(img.height * k))), Image.LANCZOS)
            img.save(os.path.join(folder, f"{pname}.png"))
        with open(os.path.join(folder, "rig.json"), "w", encoding="utf-8") as f:
            json.dump(rig_json(), f, indent=2)
    return cid


def names():
    out = {}
    for gang, members in MEMBERS:
        for slug, name, _s, _w, _b in members:
            out[f"{gang}_{slug}"] = name
    return out


def ids():
    return [f"{gang}_{slug}" for gang, members in MEMBERS for slug, *_ in members]


# --------------------------------------------------------- roster definitions
PAL = {"changsing": (38, 0.92, 1.02), "wingkong": (0, 0.6, 0.58)}

MOVES = {
    "changsing": dict(throw="Staff Sweep", palm="Pole Palm", upper="Rising Staff",
                      blow="Long Reach Blow", zankou="Staff Butt",
                      knee="Chang Sing Kick", super1="Extend and Strike",
                      super2="Six Staffs"),
    "wingkong": dict(throw="Machete Toss", palm="Cleaver Palm",
                     upper="Rising Blade", blow="Red Hand Blow",
                     zankou="Machete Chop", knee="Alley Kick",
                     super1="Wing Kong Rush", super2="Red Alley Justice"),
}

QUOTES = {
    "changsing": [
        "The Chang Sing do not run.",
        "Six of us. Six staves. One alley.",
        "You picked the wrong night, friend.",
        "We were here before your boss was born.",
        "The staff is longer than your reach.",
        "Chinatown remembers who stood.",
        "Egg Shen sends his regards.",
    ],
    "wingkong": [
        "The Wing Kong own this street.",
        "Red means last warning.",
        "The blade is heavy. You will not enjoy it.",
        "Lo Pan pays. We collect.",
        "You should have stayed in your truck.",
        "Nobody walks out of our alley.",
        "Say hello to the boys in the back.",
    ],
}

BLURB = {
    "changsing": "Chang Sing. Tan gi, black underclothes, and a staff that never runs short.",
    "wingkong": "Wing Kong. Black gi, red trim, and a machete the size of your arm.",
}

ROSTER_SPECS = []
for _gang, _members in MEMBERS:
    for _i, (_slug, _name, _style, _weapon, _build) in enumerate(_members):
        ROSTER_SPECS.append(dict(
            id=f"{_gang}_{_slug}", name=_name, display=_name,
            pal=PAL[_gang], life=880 + _i * 35, attack=96 + _i * 3,
            defence=94 + _i * 2, xscale=_build, yscale=_build,
            order=1 if _gang == "changsing" else 2,
            blurb=BLURB[_gang], moves=dict(MOVES[_gang]),
            quotes=QUOTES[_gang],
        ))


def main(argv):
    made = []
    for gang, members in MEMBERS:
        for i, (slug, name, style, weapon, build) in enumerate(members):
            cid = f"{gang}_{slug}"
            write_member(gang, slug, name, style, weapon, build,
                         tint=1.0 + (i - 2.5) * 0.07)
            made.append(cid)
    print(f"painted {len(made)} gang members: {', '.join(made)}")
    if "--sheet" in argv:
        import char_rig as cr
        roster = []
        for cid in made[:6]:
            rig = cr.load_rig(cid)
            roster.append((cid, cr.render(rig, cr.POSES["stance"])))
        for cid in made[6:]:
            rig = cr.load_rig(cid)
            roster.append((cid, cr.render(rig, cr.POSES["stance"])))
        cell = (360, 400)
        sheet = Image.new("RGBA", (cell[0] * 6, cell[1] * 2), (28, 30, 38, 255))
        for i, (cid, img) in enumerate(roster):
            sheet.alpha_composite(img, ((i % 6) * cell[0], (i // 6) * cell[1]))
        os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
        path = os.path.join(ROOT, "artifacts", "gangs_roster.png")
        sheet.convert("RGB").save(path)
        print("wrote artifacts/gangs_roster.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
