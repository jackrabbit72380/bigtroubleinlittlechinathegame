"""The rest of the cast: guards, the Lords of Death, police and civilians.

``gangs.py`` paints the two tongs, who wear gis. The people around them do not:
the Wing Kong's female guards wear a fitted dark tunic, the Lords of Death are a
street gang in jackets and sunglasses with a knife, a pistol and a baton between
them, and the Chinatown police and the Wing Kong's own security wear a buttoned
uniform and a peaked cap. Uncle Chu and the old Guardian wear long coats.

Everything here is painted in code on the same puppet skeleton the gangs use,
so a fighter is still a rig bake like everyone else:

    art_src/chars/<id>/parts/*.png        (front set: portraits, win pose)
    art_src/chars/<id>/parts*/rig.json
    art_src/chars/<id>/parts_side/*.png   (profile set: every fight pose)

The garment is what tells these people apart at fighting distance, so each look
paints its own torso; heads, arms, legs and feet come from the gang primitives
with this member's palette, and the head gains sunglasses or a cap where the
character wears one.

Run:  python3 tools/street.py [--sheet]
"""

from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import char_rig
import gangs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "art_src", "chars")

SKIN = gangs.SKIN
SKIN_LIT = gangs.SKIN_LIT
SKIN_DK = gangs.SKIN_DK


# ------------------------------------------------------------------- palettes
def _clamp(c):
    return tuple(max(0, min(255, int(round(v)))) for v in c)


def _k(c, k):
    return _clamp(tuple(v * k for v in c))


def palette(cloth, under, accent, band=None):
    """One member's colours, in the shape the gang painters already expect."""
    band = band or accent
    return dict(
        cloth=cloth, cloth_lit=_k(cloth, 1.24), cloth_dk=_k(cloth, 0.56),
        under=under, under_lit=_k(under, 1.5), under_dk=_k(under, 0.62),
        sash=accent, sash_lit=_k(accent, 1.24), trim=_k(accent, 0.86),
        band=band, band_lit=_k(band, 1.3), band_dk=_k(band, 0.6),
    )


PALETTES = {
    # the Wing Kong's female guard detail: their black gi, cut as a tunic
    "wingkong_f": palette((38, 38, 44), (26, 24, 28), (150, 32, 36)),
    "jade_f": palette((52, 96, 88), (26, 30, 30), (196, 160, 62)),
    "crimson": palette((128, 30, 40), (30, 26, 30), (200, 166, 88)),
    "plum": palette((92, 50, 86), (30, 26, 34), (196, 160, 90)),
    "teal": palette((38, 92, 94), (26, 30, 32), (188, 168, 96)),
    # street clothes
    "denim": palette((48, 66, 102), (30, 30, 34), (168, 168, 176)),
    "olive": palette((74, 78, 52), (30, 30, 26), (140, 120, 60)),
    "brown": palette((88, 60, 40), (32, 28, 24), (156, 116, 64)),
    "grey": palette((70, 72, 78), (30, 30, 34), (122, 122, 130)),
    "sand": palette((176, 148, 104), (60, 52, 40), (120, 90, 50)),
    "green": palette((46, 84, 60), (28, 30, 26), (150, 130, 70)),
    # uniforms
    "police": palette((34, 44, 74), (18, 20, 26), (196, 168, 92)),
    "guard": palette((44, 46, 52), (22, 22, 26), (150, 32, 36)),
}


# -------------------------------------------------------------------- garments
def _torso_blank(w=104, h=110):
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    d.polygon([(12, 16), (92, 16), (86, 58), (78, h), (26, h), (18, 58)], fill=255)
    d.ellipse([0, 2, 58, 54], fill=255)
    d.ellipse([46, 2, 104, 54], fill=255)
    return m


def _jacket(g):
    """Open jacket over a tee, hem at the hip. Lords, minions, Junk."""
    W, H = 104, 110
    img = char_rig._shade(_torso_blank(W, H), g["cloth"], g["cloth_lit"], g["cloth_dk"])
    d = ImageDraw.Draw(img)
    # the shirt underneath, showing in the open front
    d.polygon([(40, 4), (64, 4), (60, 44), (52, 92), (44, 44)], fill=g["under"] + (255,))
    # jacket fronts, left panel over right
    d.polygon([(30, 8), (44, 4), (46, 92), (26, 100)], fill=g["cloth_lit"] + (235,))
    d.polygon([(74, 8), (60, 4), (58, 92), (78, 100)], fill=g["cloth_dk"] + (225,))
    d.line([(26, 12), (46, 20)], fill=g["trim"] + (200,), width=3)
    d.line([(78, 12), (58, 20)], fill=g["trim"] + (170,), width=3)
    # collar
    d.polygon([(44, 4), (52, 16), (60, 4), (52, 10)], fill=g["cloth_lit"] + (240,))
    # waistband and hem
    d.rectangle([18, 92, 86, 98], fill=g["cloth_dk"] + (255,))
    d.line([(20, 99), (84, 99)], fill=(12, 12, 14, 220), width=2)
    # pockets
    for x in (26, 64):
        d.line([(x, 66), (x + 14, 66)], fill=g["cloth_dk"] + (150,), width=2)
    for i in range(2):                       # seams
        x = 36 + i * 30
        d.line([(x, 22), (x - 2, 90)], fill=g["cloth_dk"] + (60,), width=1)
    return img


def _uniform(g):
    """Buttoned tunic, belt, badge and shoulder tabs. Police and security."""
    W, H = 104, 110
    img = char_rig._shade(_torso_blank(W, H), g["cloth"], g["cloth_lit"], g["cloth_dk"])
    d = ImageDraw.Draw(img)
    # collar of the shirt under the tunic
    d.polygon([(40, 4), (64, 4), (58, 22), (52, 30), (46, 22)], fill=g["under"] + (255,))
    d.polygon([(40, 4), (52, 14), (46, 22)], fill=g["under_lit"] + (240,))
    d.polygon([(64, 4), (52, 14), (58, 22)], fill=g["under_lit"] + (240,))
    # placket down the middle with its buttons
    d.line([(52, 16), (52, 96)], fill=g["cloth_dk"] + (220,), width=2)
    for i in range(4):
        y = 26 + i * 17
        d.ellipse([49, y - 3, 55, y + 3], fill=g["band_lit"] + (255,),
                  outline=g["cloth_dk"] + (255,))
    # shoulder tabs
    for x0 in (20, 66):
        d.polygon([(x0, 18), (x0 + 18, 22), (x0 + 18, 27), (x0, 24)],
                  fill=g["sash"] + (235,))
    # badge on the left breast
    d.polygon([(66, 40), (74, 42), (76, 52), (70, 56), (64, 50)],
              fill=(214, 186, 108, 255), outline=(96, 74, 28, 255))
    d.line([(70, 44), (70, 52)], fill=(120, 96, 40, 220), width=1)
    # belt with a buckle
    d.rectangle([18, 88, 86, 100], fill=g["under"] + (255,))
    d.rectangle([46, 86, 58, 102], fill=g["band"] + (255,), outline=(24, 24, 26, 255))
    for i in range(2):
        x = 30 + i * 42
        d.line([(x, 20), (x - 2, 86)], fill=g["cloth_dk"] + (70,), width=1)
    return img


def _dress(g):
    """Fitted tunic flaring to the hip, sash, slit skirt. The female guards."""
    W, H = 104, 110
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.polygon([(16, 16), (88, 16), (82, 52), (96, H), (8, H), (22, 52)], fill=255)
    d.ellipse([4, 4, 54, 50], fill=255)
    d.ellipse([50, 4, 100, 50], fill=255)
    img = char_rig._shade(m, g["cloth"], g["cloth_lit"], g["cloth_dk"])
    d = ImageDraw.Draw(img)
    # high collar and a keyhole of skin below it
    d.polygon([(40, 2), (64, 2), (58, 20), (52, 28), (46, 20)], fill=g["under"] + (255,))
    d.ellipse([48, 4, 56, 14], fill=SKIN + (255,))
    # wrap front, the left panel crossing over
    d.polygon([(44, 10), (58, 22), (54, 58), (40, 40)], fill=g["cloth_lit"] + (225,))
    d.line([(44, 12), (56, 24)], fill=g["trim"] + (190,), width=2)
    # sash, wide, tied at the waist
    d.polygon([(20, 62), (84, 62), (82, 78), (22, 78)], fill=g["sash"] + (255,))
    d.line([(22, 64), (82, 64)], fill=g["sash_lit"] + (200,), width=2)
    d.polygon([(22, 70), (34, 72), (30, 92), (20, 88)], fill=g["sash"] + (250,))
    # the slit, and the skirt folds
    d.line([(52, 80), (54, 108)], fill=g["cloth_dk"] + (210,), width=2)
    for i in range(3):
        x = 32 + i * 20
        d.line([(x, 82), (x - 3, 108)], fill=g["cloth_dk"] + (70,), width=1)
    return img


def _coat(g):
    """Long coat over a shirt: Uncle Chu and the Guardian."""
    W, H = 104, 110
    img = char_rig._shade(_torso_blank(W, H), g["cloth"], g["cloth_lit"], g["cloth_dk"])
    d = ImageDraw.Draw(img)
    d.polygon([(40, 4), (64, 4), (60, 46), (52, 100), (44, 46)], fill=g["under"] + (255,))
    # wide lapels turned back
    d.polygon([(26, 8), (44, 4), (48, 40), (30, 54), (22, 22)], fill=g["cloth_lit"] + (240,))
    d.polygon([(78, 8), (60, 4), (56, 40), (74, 54), (82, 22)], fill=g["cloth_dk"] + (235,))
    d.line([(24, 22), (44, 10)], fill=g["trim"] + (180,), width=2)
    d.line([(80, 22), (60, 10)], fill=g["trim"] + (150,), width=2)
    # rope belt with its knot
    d.rectangle([18, 74, 86, 84], fill=g["sash"] + (255,))
    d.ellipse([46, 72, 58, 86], fill=g["sash_lit"] + (255,))
    d.line([(50, 86), (46, 104)], fill=g["sash"] + (240,), width=4)
    d.line([(54, 86), (60, 104)], fill=g["sash"] + (240,), width=4)
    for i in range(2):
        x = 34 + i * 34
        d.line([(x, 30), (x - 3, 104)], fill=g["cloth_dk"] + (70,), width=1)
    return img


TORSO = {"street": _jacket, "uniform": _uniform, "dress": _dress, "coat": _coat}


def _pelvis(g, look):
    W, H = 62, 38
    m = gangs._mask((W, H), [(3, 4), (59, 4), (55, 38), (34, 38), (31, 20),
                             (28, 38), (7, 38)])
    img = char_rig._shade(m, g["cloth"], g["cloth_lit"], g["cloth_dk"])
    d = ImageDraw.Draw(img)
    if look == "uniform":
        d.line([(4, 12), (58, 12)], fill=g["under"] + (255,), width=5)
    elif look == "dress":
        d.line([(4, 10), (58, 10)], fill=g["sash"] + (235,), width=4)
    else:
        d.line([(4, 12), (58, 12)], fill=g["cloth_dk"] + (230,), width=4)
    d.line([(31, 18), (31, 34)], fill=g["cloth_dk"] + (200,), width=2)
    return img


# ----------------------------------------------------------------------- heads
def _head(m, side):
    """The gang head, plus this member's sunglasses or peaked cap."""
    g = m["_g"]
    img = gangs._head(m["style"], g, side, beard=not m.get("female"))
    d = ImageDraw.Draw(img)
    if m.get("glasses"):
        # a dark wrap across the eyes, glinting on the near lens
        d.polygon([(14, 18), (48, 17), (50, 25), (14, 27)], fill=(20, 22, 26, 245))
        d.line([(16, 20), (46, 19)], fill=(226, 232, 236, 170), width=1)
        d.line([(14, 27), (48, 26)], fill=(10, 10, 12, 200), width=1)
        if side:
            d.line([(44, 18), (52, 20)], fill=(20, 22, 26, 245), width=3)
    if m["style"] == "cap":
        # peaked cap: a dark crown sitting on the brow, visor forward
        d.ellipse([8, 0, 54, 20], fill=g["under"] + (255,))
        d.ellipse([12, 2, 50, 16], fill=g["cloth_dk"] + (255,))
        d.rectangle([10, 14, 52, 19], fill=g["cloth"] + (255,))
        d.polygon([(44, 14), (62, 18), (62, 24), (44, 21)], fill=(16, 16, 20, 255))
        if not side:
            d.polygon([(2, 16), (20, 15), (20, 21), (2, 22)], fill=(16, 16, 20, 255))
        d.line([(12, 15), (50, 15)], fill=g["band"] + (200,), width=2)
    return img


# ------------------------------------------------------------------------ arms
def _arm(g, sleeve, banded, weapon):
    if weapon in ("knife", "baton", "none", ""):
        return _plain_arm(g, sleeve, banded, weapon)
    return gangs._arm(g, sleeve, banded, weapon)


def _plain_arm(g, sleeve, banded, weapon):
    import math

    W, H = gangs.ARM_CANVAS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    up_a, fore_a = 12.0, 112.0
    shoulder = gangs.SHOULDER
    elbow = gangs._rot(shoulder[0], shoulder[1], up_a, 62.0)
    wrist = gangs._rot(elbow[0], elbow[1], fore_a, 52.0)

    char_rig._place(img, dict(image=gangs._uarm(g, sleeve, banded),
                              pivot=(17.0, 0.0), base=0.0), up_a, shoulder)
    char_rig._place(img, dict(image=gangs._farm(g), pivot=(14.0, 0.0), base=0.0),
                    fore_a, elbow)
    img.alpha_composite(gangs._fist(), (round(wrist[0] - 15), round(wrist[1] - 15)))

    if weapon in ("knife", "baton", "none", ""):
        d = ImageDraw.Draw(img)
        if weapon == "knife":
            grip = gangs._rot(wrist[0], wrist[1], fore_a, -18)
            heel = gangs._rot(wrist[0], wrist[1], fore_a, 6)
            tip = gangs._rot(wrist[0], wrist[1], fore_a, 58)
            d.line([grip, heel], fill=(48, 34, 26, 255), width=8)
            d.line([(heel[0] - 6, heel[1]), (heel[0] + 6, heel[1] - 4)],
                   fill=(150, 140, 120, 255), width=3)      # guard
            a = math.radians(fore_a)
            nx, ny = math.cos(a), math.sin(a)

            def off(p, w):
                return (p[0] + nx * w, p[1] + ny * w)

            d.polygon([off(heel, -4), off(tip, -2), off(tip, 2), off(heel, 4)],
                      fill=(216, 222, 228, 255))
            d.line([off(heel, -4), off(tip, -2)], fill=(248, 250, 252, 240), width=1)
        elif weapon == "baton":
            grip = gangs._rot(wrist[0], wrist[1], fore_a, -22)
            tip = gangs._rot(wrist[0], wrist[1], fore_a, 74)
            d.line([grip, tip], fill=(28, 28, 32, 255), width=9)
            d.line([grip, tip], fill=(58, 58, 66, 255), width=6)
            d.line([(grip[0] - 4, grip[1]), (tip[0] - 4, tip[1])],
                   fill=(120, 124, 132, 170), width=2)
    return img


# ---------------------------------------------------------------------- member
def parts_for(m, side):
    g = m["_g"]
    look = m["look"]
    sleeve = (g["cloth"], g["cloth_lit"], g["cloth_dk"])
    if look == "uniform":
        sleeve = (g["cloth"], g["cloth_lit"], g["cloth_dk"])
    torso = TORSO[look](g)
    if m.get("female"):
        # the guard detail is slighter than the tongs: narrow the torso and
        # pelvis rather than shrink the whole figure, which keeps the head
        # reading at the same size as everyone else's
        torso = torso.resize((round(torso.width * 0.88), torso.height), Image.LANCZOS)
        torso = torso.crop((0, 0, torso.width, torso.height))
    out = {
        "torso": torso,
        "pelvis": _pelvis(g, look),
        "head": _head(m, side),
        "arm_n": _arm(g, sleeve, False, m["weapon"]),
        "arm_f": _arm(g, sleeve, False, ""),
        "thigh_n": gangs._thigh(g), "thigh_f": gangs._thigh(g),
        "shin_n": gangs._shin(g), "shin_f": gangs._shin(g),
        "foot_n": gangs._foot(g), "foot_f": gangs._foot(g),
    }
    if look == "coat":
        out["cape"] = _coat_tail(g)
    return out


def _coat_tail(g):
    """A long coat's skirt, behind the legs."""
    W, H = 96, 120
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.polygon([(14, 0), (82, 0), (92, H), (4, H)], fill=255)
    img = char_rig._shade(m, g["cloth"], g["cloth_lit"], g["cloth_dk"])
    d = ImageDraw.Draw(img)
    d.line([(48, 4), (48, H - 2)], fill=g["cloth_dk"] + (200,), width=2)
    return img


def rig_json():
    return gangs.rig_json()


def write_member(m):
    cid = m["id"]
    for sub, side in (("parts", False), ("parts_side", True)):
        folder = os.path.join(PARTS, cid, sub)
        os.makedirs(folder, exist_ok=True)
        for pname, img in parts_for(m, side).items():
            if m["build"] != 1.0 and pname in ("thigh_n", "thigh_f", "shin_n", "shin_f"):
                k = m["build"]
                img = img.resize((max(1, round(img.width * k)),
                                  max(1, round(img.height * k))), Image.LANCZOS)
            img.save(os.path.join(folder, f"{pname}.png"))
        with open(os.path.join(folder, "rig.json"), "w", encoding="utf-8") as f:
            json.dump(rig_json(), f, indent=2)
    return cid


# ------------------------------------------------------------------ the roster
# id, name, look, head style, weapon, build, palette, female, sunglasses
MEMBERS = [
    # --- the Wing Kong's female guard detail -------------------------------
    dict(id="dawn_vd", name="Dawn Of Death", look="dress", style="long",
         weapon="knife", build=0.96, pal="wingkong_f", female=True),
    dict(id="lotus", name="Iron Lotus Shinko", look="dress", style="topknot",
         weapon="knife", build=0.96, pal="jade_f", female=True),
    dict(id="viper_f", name="Red Viper", look="dress", style="ponytail",
         weapon="knife", build=0.96, pal="crimson", female=True),
    dict(id="silk", name="Shadow Silk Diana", look="dress", style="long",
         weapon="knife", build=0.96, pal="plum", female=True),
    # --- the Lords of Death: street clothes, sunglasses, blades and a baton
    dict(id="needles", name="Needles", look="street", style="bandana",
         weapon="knife", build=1.00, pal="denim", glasses=True),
    dict(id="joe_lucky", name="Joe Lucky", look="street", style="flat",
         weapon="pistols", build=1.00, pal="olive", glasses=True),
    dict(id="one_ear", name="One Ear", look="street", style="shaved",
         weapon="baton", build=1.02, pal="brown", glasses=True),
    # --- uniforms ----------------------------------------------------------
    dict(id="police", name="China Town Police", look="uniform", style="cap",
         weapon="baton", build=1.00, pal="police"),
    dict(id="minion1", name="Minion 1", look="street", style="shaved",
         weapon="knife", build=0.98, pal="grey", glasses=True),
    dict(id="minion2", name="Minion 2", look="street", style="flat",
         weapon="knife", build=1.02, pal="grey", glasses=True),
    dict(id="security1", name="Wing Kong Security Guard 1", look="uniform",
         style="cap", weapon="baton", build=1.00, pal="guard"),
    dict(id="security2", name="Wing Kong Security Guard 2", look="uniform",
         style="cap", weapon="baton", build=0.98, pal="guard"),
    # --- civilians ---------------------------------------------------------
    dict(id="junk", name="Junk", look="street", style="long",
         weapon="none", build=1.00, pal="denim"),
    dict(id="uncle_chu", name="Uncle Chu", look="coat", style="topknot",
         weapon="none", build=0.96, pal="sand"),
    dict(id="tara", name="Tara", look="dress", style="long",
         weapon="none", build=0.94, pal="teal", female=True),
    dict(id="otoole", name="Ms O'Toole", look="dress", style="ponytail",
         weapon="none", build=0.96, pal="plum", female=True),
    dict(id="guardian", name="The Guardian", look="coat", style="bald",
         weapon="staff", build=1.04, pal="green"),
]

for _m in MEMBERS:
    _m["_g"] = PALETTES[_m["pal"]]

MOVES = {
    "street": dict(throw="Alley Shove", palm="Switchblade Palm",
                   upper="Lucky Upper", blow="Sidewalk Blow",
                   zankou="Blackjack", knee="Knee in the Gutter",
                   super1="Lords of Death", super2="Three on One"),
    "uniform": dict(throw="Nightstick Toss", palm="Badge Palm",
                    upper="Riot Upper", blow="Beat Cop Blow",
                    zankou="Nightstick", knee="Patrol Kick",
                    super1="Curfew Sweep", super2="Call for Backup"),
    "dress": dict(throw="Silk Throw", palm="Fan Palm", upper="Guard Upper",
                  blow="Hidden Blade Blow", zankou="Sleeve Knife",
                  knee="Lotus Knee", super1="Iron Lotus", super2="Silk and Steel"),
    "coat": dict(throw="Old Man's Throw", palm="Ancient Palm",
                 upper="Rising Crane", blow="Long Sleeve Blow",
                 zankou="Bone Hand", knee="Staff Knee",
                 super1="The Old Ways", super2="Guardian's Gate"),
}

QUOTES = {
    "street": [
        "The Lords of Death run this block now.",
        "You want to talk to the boss? Talk to my knife.",
        "Lucky? The name is a promise.",
        "Three of us. One of you.",
        "Nobody walks out of the airport.",
        "We were told to bring the girl. You are in the way.",
    ],
    "uniform": [
        "Curfew is in ten minutes.",
        "Move along. Nothing to see.",
        "Chinatown is quiet tonight. Keep it that way.",
        "You are under arrest, friend.",
        "I have a nightstick and no patience.",
        "The Wing Kong pay the rent on this street.",
    ],
    "dress": [
        "The Wing Kong do not fight women. That is their mistake.",
        "I have carried a blade since I was a girl.",
        "You looked at the wrong guard.",
        "Lo Pan's house, Lo Pan's rules.",
        "Silk hides steel.",
        "Walk away while the offer stands.",
    ],
    "coat": [
        "I have seen three emperors come and go.",
        "Sit. Breathe. Then we talk.",
        "The old ways are not dead in this town.",
        "You are the storm's business, not mine.",
        "There is tea. Drink it.",
        "Chinatown keeps its own accounts.",
    ],
}

BLURB = {
    "street": "Lords of Death. Street clothes, dark glasses, and something edged in the pocket.",
    "uniform": "Chinatown patrol. Buttoned tunic, peaked cap, nightstick on the belt.",
    "dress": "Wing Kong guard detail. Fitted tunic, a knife in the sleeve, and no patience left.",
    "coat": "The old Chinatown. Long coat, rope belt, and hands that remember the forms.",
}

ORDERS = {"street": 2, "uniform": 2, "dress": 1, "coat": 3}

ROSTER_SPECS = []
for _i, _m in enumerate(MEMBERS):
    _fam = _m["look"]
    ROSTER_SPECS.append(dict(
        id=_m["id"], name=_m["name"], display=_m["name"],
        pal=(38, 1.0, 1.0), life=860 + _i * 18,
        attack=94 + (_i % 7) * 4, defence=92 + (_i % 5) * 3,
        xscale=_m["build"], yscale=_m["build"], order=ORDERS[_fam],
        blurb=BLURB[_fam], moves=dict(MOVES[_fam]),
        quotes=QUOTES[_fam],
    ))


def ids():
    return [m["id"] for m in MEMBERS]


def names():
    return {m["id"]: m["name"] for m in MEMBERS}


def main(argv):
    made = []
    for m in MEMBERS:
        made.append(write_member(m))
    print(f"painted {len(made)} street fighters: {', '.join(made)}")
    if "--sheet" in argv:
        sheet_cell = (360, 400)
        cols = 6
        rows = (len(made) + cols - 1) // cols
        sheet = Image.new("RGBA", (sheet_cell[0] * cols, sheet_cell[1] * rows),
                          (28, 30, 38, 255))
        for i, cid in enumerate(made):
            rig = char_rig.load_rig(cid)
            img = char_rig.render(rig, char_rig.POSES["stance"])
            sheet.alpha_composite(img, ((i % cols) * sheet_cell[0],
                                        (i // cols) * sheet_cell[1]))
        os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
        sheet.convert("RGB").save(os.path.join(ROOT, "artifacts", "street_roster.png"))
        print("wrote artifacts/street_roster.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
