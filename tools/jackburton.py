"""Jack Burton: his own costume palette plus pistol and knife special moves.

The roster is built from the shared Kung Fu Man base, so the body is KFM's.
What makes Jack Jack is the palette table below (white tank top, blue jeans,
brown hair, tanned skin, leather boots) and the two weapon moves, which bring
their own sprites, animations and state definitions.

Kung Fu Man's 32-colour table is laid out in ramps, and the ramps map onto
body regions consistently across every frame of his animation set:

    16-20  trousers          -> denim
    21     top highlight     -> white
    22-24  vest / headband   -> white tank top
    25-29  skin              -> tanned skin
    30     hair              -> brown
    31     outline / shadow  -> warm dark

Rebuilding the ramps instead of hue-shifting the whole table is what stops
Jack from coming out as a teal Kung Fu Man.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFilter

# --------------------------------------------------------------------- palette
# 32 RGBA entries, index 0 transparent, written straight into every palette
# slot of jackburton.sff.
COSTUME = [
    (0, 0, 0, 0),          # 0  transparent
    (22, 16, 12, 255),     # 1  outline
    (22, 16, 12, 255),     # 2
    (22, 16, 12, 255),     # 3
    (22, 16, 12, 255),     # 4
    (22, 16, 12, 255),     # 5
    (22, 16, 12, 255),     # 6
    (22, 16, 12, 255),     # 7
    (22, 16, 12, 255),     # 8
    (22, 16, 12, 255),     # 9
    (22, 16, 12, 255),     # 10
    (22, 16, 12, 255),     # 11
    (22, 16, 12, 255),     # 12
    (22, 16, 12, 255),     # 13
    (22, 16, 12, 255),     # 14
    (22, 16, 12, 255),     # 15
    (150, 175, 205, 255),  # 16 denim highlight
    (112, 140, 172, 255),  # 17 denim light
    (82, 108, 138, 255),   # 18 denim mid
    (58, 80, 106, 255),    # 19 denim shadow
    (38, 56, 78, 255),     # 20 denim deep shadow
    (255, 255, 255, 255),  # 21 tank highlight
    (255, 255, 255, 255),  # 22 tank body
    (232, 234, 238, 255),  # 23 tank shade
    (198, 202, 210, 255),  # 24 tank deep shade
    (243, 197, 166, 255),  # 25 skin highlight
    (233, 181, 146, 255),  # 26 skin light
    (215, 160, 124, 255),  # 27 skin mid
    (170, 115, 82, 255),   # 28 skin shadow
    (116, 71, 48, 255),    # 29 skin deep shadow
    (88, 58, 34, 255),     # 30 hair / leather brown
    (40, 28, 20, 255),     # 31 outline, warm
]


def palette_bytes() -> bytes:
    out = bytearray()
    for r, g, b, a in COSTUME:
        out += bytes((r, g, b, a))
    return bytes(out)


def palettes(base_palettes, grade, spec):
    """Palette 1 is the costume; the rest are graded alternates of it."""
    costume = palette_bytes()
    out = [costume]
    for _ in base_palettes[1:]:
        out.append(grade(costume, spec))
    return out


# ---------------------------------------------------------------------- sprite
STEEL = ((238, 243, 248), (176, 187, 198), (120, 132, 145))
LEATHER = ((92, 62, 38), (62, 40, 24))
FLAME = ((255, 255, 255), (255, 226, 150), (255, 160, 60))


def _blank(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def _blur_layer(img, radius):
    return img.filter(ImageFilter.GaussianBlur(radius))


def bullet():
    """Pistol round: hot core with a short trail, drawn pointing forward."""
    w, h = 26, 8
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    for i in range(14):                       # tapering trail
        t = i / 13.0
        a = int(150 * (1 - t) ** 1.6)
        x0 = 1 + i
        d.line([(x0, 4 - t * 1.6), (x0, 4 + t * 1.6)],
               fill=(255, 196, 96, a))
    glow = _blank(w, h)
    ImageDraw.Draw(glow).ellipse([12, 0, 25, 7], fill=(255, 214, 130, 190))
    img = Image.alpha_composite(img, _blur_layer(glow, 2))
    d = ImageDraw.Draw(img)
    d.ellipse([16, 1, 25, 6], fill=FLAME[0] + (255,))   # core
    d.ellipse([19, 2, 24, 5], fill=(255, 250, 232, 255))
    d.line([(14, 3), (18, 3)], fill=FLAME[1] + (255,))
    return img


def muzzle_flash(step):
    """Three-frame star flash coming out of the barrel."""
    w, h = 38, 26
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    scale = (1.0, 0.72, 0.42)[step]
    alpha = (235, 205, 150)[step]
    cx, cy = 9, 13
    reach = 16 * scale

    star = []
    for i in range(16):
        ang = math.pi * 2 * i / 16
        r = reach * (1.0 if i % 2 == 0 else 0.45)
        star.append((cx + math.cos(ang) * r * 1.5, cy + math.sin(ang) * r))
    d.polygon(star, fill=FLAME[2] + (alpha,))
    d.ellipse([cx - 7 * scale, cy - 7 * scale, cx + 7 * scale, cy + 7 * scale],
              fill=FLAME[1] + (alpha,))
    d.ellipse([cx - 4 * scale, cy - 4 * scale, cx + 4 * scale, cy + 4 * scale],
              fill=FLAME[0] + (alpha,))
    d.line([(cx, cy), (cx + 22 * scale, cy)], fill=(255, 246, 220, int(alpha * 0.8)),
           width=max(1, int(4 * scale)))
    halo = _blur_layer(img, 3)
    return Image.alpha_composite(halo, img)


def impact(step):
    """Bullet / knife hit: white spark with hot fragments."""
    w, h = 30, 30
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    scale = (1.0, 0.8, 0.5)[step]
    for i in range(10):
        ang = math.pi * 2 * i / 10 + step * 0.3
        r0, r1 = 3, 13 * scale * (1.0 if i % 2 == 0 else 0.6)
        d.line([(15 + math.cos(ang) * r0, 15 + math.sin(ang) * r0),
                (15 + math.cos(ang) * r1, 15 + math.sin(ang) * r1)],
               fill=FLAME[1] + (220,), width=2)
    d.ellipse([15 - 6 * scale, 15 - 6 * scale, 15 + 6 * scale, 15 + 6 * scale],
              fill=FLAME[0] + (235,))
    return Image.alpha_composite(_blur_layer(img, 2), img)


def _knife_rest():
    """Knife lying horizontal, blade forward, on a transparent square."""
    w, h = 46, 46
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    cy = h // 2
    # handle
    d.rounded_rectangle([6, cy - 3, 18, cy + 3], radius=2, fill=LEATHER[0] + (255,))
    for x in (8, 11, 14, 17):
        d.line([(x, cy - 2), (x, cy + 2)], fill=LEATHER[1] + (255,))
    # guard
    d.rectangle([18, cy - 6, 21, cy + 6], fill=(70, 78, 88, 255))
    # blade: long taper to a point
    d.polygon([(21, cy - 4), (40, cy - 3), (44, cy), (40, cy + 2),
               (21, cy + 4)], fill=STEEL[1] + (255,))
    d.polygon([(21, cy - 4), (40, cy - 3), (44, cy), (36, cy - 1),
               (21, cy - 1)], fill=STEEL[0] + (255,))
    d.line([(22, cy + 3), (40, cy + 2)], fill=STEEL[2] + (255,), width=1)
    return img


def thrown_knife(step):
    """Four-frame spin of the thrown blade."""
    base = _knife_rest()
    img = base.rotate(-step * 45, resample=Image.BICUBIC, expand=False)
    return img


def sprites():
    """Extra sprite records for Jack's SFF."""
    out = []
    out.append({"group": 7000, "number": 0, "image": bullet(), "axis": (4, 4)})
    for i in range(3):
        out.append({"group": 7001, "number": i,
                    "image": muzzle_flash(i), "axis": (8, 13)})
    for i in range(3):
        out.append({"group": 7002, "number": i,
                    "image": impact(i), "axis": (15, 15)})
    for i in range(4):
        out.append({"group": 7010, "number": i,
                    "image": thrown_knife(i), "axis": (23, 23)})
    return out


# ------------------------------------------------------------------ animations
AIR = """
;---------------------------------------------------------------------------
; Jack Burton - weapon animation set (added by tools/jackburton.py)
;---------------------------------------------------------------------------
; Pistol round (projectile)
[Begin Action 7000]
Clsn1: 1
 Clsn1[0] = -8,-4, 8,4
7000,0, 0,0, -1

; Muzzle flash
[Begin Action 7001]
7001,0, 0,0, 2
7001,1, 0,0, 2
7001,2, 0,0, -1

; Impact spark
[Begin Action 7002]
7002,0, 0,0, 3
7002,1, 0,0, 3
7002,2, 0,0, -1

; Thrown knife, spinning
[Begin Action 7010]
Clsn1: 1
 Clsn1[0] = -14,-9, 14,9
7010,0, 0,0, 3
7010,1, 0,0, 3
7010,2, 0,0, 3
7010,3, 0,0, 3
"""


# ---------------------------------------------------------------------- command
CMD_COMMANDS = """
;-| Jack Burton - weapon motions |-----------------------------------------
[Command]
name = "gun_a"
command = ~D, DB, B, a

[Command]
name = "gun_b"
command = ~D, DB, B, b

[Command]
name = "knife_a"
command = ~F, DF, D, DB, B, a

[Command]
name = "knife_b"
command = ~F, DF, D, DB, B, b

"""

CMD_STATES = """
;---------------------------------------------------------------------------
; Jack Burton - weapon specials
;---------------------------------------------------------------------------
;Six Shooter (pistol)
[State -1, Six Shooter]
type = ChangeState
value = 1500
triggerall = command = "gun_a" || command = "gun_b"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = movecontact
trigger2 = stateno != [1500,1600)

;Knife Toss
[State -1, Knife Toss]
type = ChangeState
value = 1600
triggerall = command = "knife_a" || command = "knife_b"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = movecontact
trigger2 = stateno != [1500,1600)
"""


# ------------------------------------------------------------------------ state
CNS = """
;---------------------------------------------------------------------------
; Jack Burton - gun and knife
; The pistol is a three-round burst: one Projectile per thrust, each weaker
; than the last, so the whole burst hurts about as much as one solid punch.
; The knife is a single heavy projectile that keeps spinning on the way out.
;---------------------------------------------------------------------------
[Statedef 1500]
type    = S
movetype= A
physics = S
juggle  = 4
poweradd= 45
velset = 0,0
anim = 1210
ctrl = 0
sprpriority = 2

[State 1500, sound]
type = PlaySnd
trigger1 = AnimElem = 3
value = 0, 3

[State 1500, flash 1]
type = Explod
trigger1 = AnimElem = 4
anim = 7001
id = 1501
pos = 34,-62
postype = p1
sprpriority = 4
removetime = -2

[State 1500, flash 2]
type = Explod
trigger1 = AnimElem = 6
anim = 7001
id = 1501
pos = 34,-62
postype = p1
sprpriority = 4
removetime = -2

[State 1500, flash 3]
type = Explod
trigger1 = AnimElem = 8
anim = 7001
id = 1501
pos = 34,-62
postype = p1
sprpriority = 4
removetime = -2

[State 1500, round 1]
type = Projectile
trigger1 = AnimElem = 4
projanim = 7000
projhitanim = 7002
velocity = 12, 0
removetime = -1
projshadow = -1
damage = 40
attr = S, SP
guardflag = MA
pausetime = 4, 10
sparkno = 1
sparkxy = -10,-50
hitsound = 5,3
guardsound = 6,0
animtype = Hard
ground.type = High
ground.slidetime = 8
ground.hittime = 12
ground.velocity = -3
air.velocity = -3,-2.5

[State 1500, round 2]
type = Projectile
trigger1 = AnimElem = 6
projanim = 7000
projhitanim = 7002
velocity = 12, 0
removetime = -1
projshadow = -1
damage = 35
attr = S, SP
guardflag = MA
pausetime = 4, 10
sparkno = 1
sparkxy = -10,-50
hitsound = 5,3
guardsound = 6,0
animtype = Hard
ground.type = High
ground.slidetime = 8
ground.hittime = 12
ground.velocity = -3
air.velocity = -3,-2.5

[State 1500, round 3]
type = Projectile
trigger1 = AnimElem = 8
projanim = 7000
projhitanim = 7002
velocity = 12, 0
removetime = -1
projshadow = -1
damage = 30
attr = S, SP
guardflag = MA
pausetime = 4, 10
sparkno = 1
sparkxy = -10,-50
hitsound = 5,3
guardsound = 6,0
animtype = Hard
ground.type = High
ground.slidetime = 8
ground.hittime = 12
ground.velocity = -3
air.velocity = -3,-2.5

[State 1500, end]
type = ChangeState
trigger1 = AnimTime = 0
value = 0
ctrl = 1

;---------------------------------------------------------------------------
[Statedef 1600]
type    = S
movetype= A
physics = S
juggle  = 5
poweradd= 55
velset = 0,0
anim = 1400
ctrl = 0
sprpriority = 2

[State 1600, sound]
type = PlaySnd
trigger1 = AnimElem = 3
value = 0, 3

[State 1600, throw]
type = Projectile
trigger1 = AnimElem = 4
projanim = 7010
projhitanim = 7002
velocity = 9, 0
removetime = -1
projshadow = -1
damage = 75
attr = S, SP
guardflag = MA
pausetime = 8, 14
sparkno = 1
sparkxy = -10,-55
hitsound = 5,4
guardsound = 6,0
animtype = Hard
ground.type = High
ground.slidetime = 10
ground.hittime = 16
ground.velocity = -4
air.velocity = -3.5,-3
fall = 0

[State 1600, end]
type = ChangeState
trigger1 = AnimTime = 0
value = 0
ctrl = 1
"""

EXTRA_SPECIALS = """Six Shooter\t\t\t\t\t\t\t_QDB^K
Knife Toss\t\t\t\t\t\t\t_QDBF^K
"""
