"""Rain: thrown water instead of fists.

The third Storm fights at range, like Lightning, but with water: a three-dart
volley, a single heavy cloudburst, and a step that turns him into falling rain
and puts him down on the far side of his opponent. The plumbing is the same
slot Jack's pistol occupies (states 1500/1600, animations 7000-7030, commands
on kicks), so ``bake_char`` swaps the pose and every trigger still lines up.

The art is PNG32 written alongside the indexed base sprites, the same way
Jack's and Lightning's effects are.

Run:  imported by tools/build_chars.py
"""

from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw, ImageFilter

DROP = (146, 208, 238)
DROP_LIT = (214, 240, 250)
CORE = (250, 254, 255)
DEEP = (40, 96, 132)


def _blank(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def _glow(img, radius):
    return img.filter(ImageFilter.GaussianBlur(radius))


def dart():
    """The travelling projectile: a bead of water with its tail streaming."""
    w = h = 34
    img = _blank(w, h)
    halo = _blank(w, h)
    ImageDraw.Draw(halo).ellipse([3, 3, 30, 30], fill=DROP + (140,))
    img = Image.alpha_composite(img, _glow(halo, 5))
    d = ImageDraw.Draw(img)
    # teardrop: nose to the right, tail streaming back to the left
    d.polygon([(5, 17), (19, 6), (30, 17), (19, 28)], fill=DROP + (205,))
    d.ellipse([12, 9, 28, 25], fill=DROP_LIT + (235,))
    d.ellipse([16, 12, 24, 20], fill=CORE + (255,))
    d.line([(6, 17), (18, 10)], fill=DROP_LIT + (190,), width=2)
    for i in range(4):
        d.point([(3 + i * 2, 25 + i)], fill=DROP_LIT + (200,))
    return img


def splash(step):
    """Three-frame burst of water off the hand as the dart leaves."""
    w = h = 52
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    scale = (1.0, 1.32, 0.72)[step]
    for k, r in enumerate((6, 12, 19)):
        rr = r * scale
        d.arc([26 - rr, 26 - rr * 0.62, 26 + rr, 26 + rr * 0.62], 196, 344,
              fill=(DROP if k % 2 else DROP_LIT) + (215,), width=3)
    d.ellipse([26 - 7 * scale, 26 - 7 * scale, 26 + 7 * scale, 26 + 7 * scale],
              fill=DROP_LIT + (235,))
    d.ellipse([26 - 3 * scale, 26 - 3 * scale, 26 + 3 * scale, 26 + 3 * scale],
              fill=CORE + (255,))
    for i in range(6):
        a = math.pi * 2 * i / 6 + step * 0.5
        r0, r1 = 8, 16 * scale
        d.ellipse([26 + math.cos(a) * r1 - 2, 26 + math.sin(a) * r1 - 2,
                   26 + math.cos(a) * r1 + 2, 26 + math.sin(a) * r1 + 2],
                  fill=DROP_LIT + (220,))
        d.point([(26 + math.cos(a) * r0, 26 + math.sin(a) * r0)],
                fill=DROP + (200,))
    return Image.alpha_composite(_glow(img, 3), img)


def impact(step):
    """Water hit spark: droplets thrown out and falling, frame by frame."""
    w = h = 34
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    scale = (1.0, 0.8, 0.52)[step]
    d.ellipse([17 - 8 * scale, 17 - 7 * scale, 17 + 8 * scale, 17 + 7 * scale],
              fill=DROP_LIT + (225,))
    d.ellipse([17 - 4 * scale, 17 - 3 * scale, 17 + 4 * scale, 17 + 3 * scale],
              fill=CORE + (250,))
    rnd = random.Random(step * 11 + 7)
    for i in range(9):
        a = math.pi * 2 * i / 9 + step * 0.4
        r1 = (13 if i % 2 == 0 else 9) * scale
        x, y = 17 + math.cos(a) * r1, 17 + math.sin(a) * r1 + step * 2
        r = rnd.uniform(1.2, 2.6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=DROP_LIT + (220,))
    return Image.alpha_composite(_glow(img, 2), img)


def wave(step):
    """Four-frame wall of water, its crest rolling as it travels."""
    w, h = 78, 46
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    crest = []
    for i in range(9):
        t = i / 8.0
        crest.append((4 + 68 * t,
                      30 - math.sin(t * math.pi) * (13 + step * 1.6)
                      + math.sin(i * 2.1 + step * 1.4) * 3))
    body = [(4, 44), (74, 44)] + list(reversed(crest))
    d.polygon(body, fill=DROP + (185,))
    d.line(crest, fill=DROP_LIT + (230,), width=3, joint="curve")
    for i in (2, 4, 6):
        x, y = crest[i]
        d.ellipse([x - 3.5, y - 4.5, x + 3.5, y + 1], fill=CORE + (225,))
    for i in range(5):
        d.point([(10 + i * 14, 40 - (i % 2) * 3)], fill=DROP_LIT + (190,))
    return Image.alpha_composite(_glow(img, 3), img)


def rain_column(step):
    """The curtain of falling rain he becomes on the way across the screen."""
    w, h = 48, 210
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    for i in range(5):
        x0 = 7 + i * 8
        pts = [(x0 + math.sin(k * 1.35 + step * 1.6) * 2.6, 2 + k * 13.6)
               for k in range(16)]
        d.line(pts, fill=DROP + (145,), width=7, joint="curve")
        d.line(pts, fill=DROP_LIT + (195,), width=3, joint="curve")
    for i in range(10):
        x = 6 + (i * 7 + step * 5) % 36
        y = (i * 23 + step * 17) % 196 + 8
        d.line([(x, y), (x + 1, y + 8)], fill=CORE + (200,), width=2)
    return Image.alpha_composite(_glow(img, 4), img)


def hand_mist(step):
    """Droplets hanging and circling at his hands - an overlay, never the body.

    Same trick as Lightning's current: drawn as its own animation and spawned
    over him, so the arms and the rakes stay clean in every frame.
    """
    w, h = 70, 50
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    rnd = random.Random(step * 7 + 3)
    for cx in (18, 52):
        for k in range(6):
            a = step * 1.05 + k * 1.15
            x = cx + math.cos(a) * rnd.uniform(6, 13)
            y = 25 + math.sin(a) * rnd.uniform(4, 10)
            r = rnd.uniform(1.6, 3.4)
            d.ellipse([x - r, y - r, x + r, y + r], fill=DROP_LIT + (220,))
            d.ellipse([x - r * 0.4, y - r * 0.5, x + r * 0.4, y + r * 0.3],
                      fill=CORE + (245,))
    return Image.alpha_composite(_glow(img, 2), img)


def sprites():
    """Extra sprite records for Rain's SFF."""
    out = [{"group": 7000, "number": 0, "image": dart(), "axis": (17, 17)}]
    for i in range(3):
        out.append({"group": 7001, "number": i,
                    "image": splash(i), "axis": (26, 26)})
    for i in range(3):
        out.append({"group": 7002, "number": i,
                    "image": impact(i), "axis": (17, 17)})
    for i in range(4):
        out.append({"group": 7010, "number": i,
                    "image": wave(i), "axis": (39, 23)})
    for i in range(3):
        out.append({"group": 7020, "number": i,
                    "image": rain_column(i), "axis": (24, 208)})
    for i in range(4):
        out.append({"group": 7030, "number": i,
                    "image": hand_mist(i), "axis": (35, 25)})
    return out


def palettes(base_palettes, grade, spec):
    """No costume override: the roster's grading colours the body."""
    return [grade(p["rgba"], spec) for p in base_palettes]


# ------------------------------------------------------------------ animations
AIR = """
;---------------------------------------------------------------------------
; Rain - water animation set (added by tools/rain.py)
; The 7000-series frames carry the AIR blend flag A, so the dart, the splash
; and the curtain composite additively wherever they are drawn. Projectiles
; take no trans parameter in Ikemen, so this is the only way to make water
; read as light on a dark stage.
;---------------------------------------------------------------------------
; Water dart (projectile)
[Begin Action 7000]
Clsn1: 1
 Clsn1[0] = -10,-10, 10,10
7000,0, 0,0, -1, , A

; Splash at the hand
[Begin Action 7001]
7001,0, 0,0, 2, , A
7001,1, 0,0, 2, , A
7001,2, 0,0, -1, , A

; Impact splash
[Begin Action 7002]
7002,0, 0,0, 3, , A
7002,1, 0,0, 3, , A
7002,2, 0,0, -1, , A

; Cloudburst wave, rolling out
[Begin Action 7010]
Clsn1: 1
 Clsn1[0] = -30,-14, 30,14
7010,0, 0,0, 3, , A
7010,1, 0,0, 3, , A
7010,2, 0,0, 3, , A
7010,3, 0,0, 3, , A

; Curtain of rain, left standing where the step began
[Begin Action 7020]
7020,0, 0,0, 4, , A
7020,1, 0,0, 4, , A
7020,2, 0,0, -1, , A

; Water at his hands - an effect laid over the body, never in it
[Begin Action 7030]
7030,0, 0,0, 3, , A
7030,1, 0,0, 3, , A
7030,2, 0,0, 3, , A
7030,3, 0,0, -1, , A
"""


# ---------------------------------------------------------------------- command
CMD_COMMANDS = """
;-| Rain - storm motions |------------------------------------------------
[Command]
name = "drizzle_a"
command = ~D, DB, B, a

[Command]
name = "drizzle_b"
command = ~D, DB, B, b

[Command]
name = "downpour_a"
command = ~F, DF, D, DB, B, a

[Command]
name = "downpour_b"
command = ~F, DF, D, DB, B, b

; Rain Step: down, then up, with no button - the step is a movement
[Command]
name = "rain_step"
command = ~D, U

"""

CMD_STATES = """
;---------------------------------------------------------------------------
; Rain - water specials
;---------------------------------------------------------------------------
;Rain Dart (three darts)
[State -1, Rain Dart]
type = ChangeState
value = 1500
triggerall = command = "drizzle_a" || command = "drizzle_b"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = movecontact
trigger2 = stateno != [1500,1600)

;Cloudburst (single heavy wave)
[State -1, Cloudburst]
type = ChangeState
value = 1600
triggerall = command = "downpour_a" || command = "downpour_b"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = movecontact
trigger2 = stateno != [1500,1600)

;Rain Step (dash through the downpour)
; Numbered triggers are OR'ed, so everything that must hold goes in triggerall:
; written as trigger1..trigger3 the stateno test alone fired the step on the
; first frame of the round.
[State -1, Rain Step]
type = ChangeState
value = 1700
triggerall = command = "rain_step"
triggerall = statetype != A
triggerall = ctrl
trigger1 = stateno != [1700,1703)
"""


# ------------------------------------------------------------------------ state
CNS = """
;---------------------------------------------------------------------------
; Rain - water specials
; The dart volley is three darts on consecutive thrusts, each lighter than the
; last, so the whole volley lands about as hard as one solid strike. The
; Cloudburst is a single rolling wave that carries across the screen.
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

[State 1500, charged]
type = AfterImage
trigger1 = Time = 0
time = 12
length = 12
timegap = 1
framegap = 2
trans = add
paladd = 8, 30, 52
palmul = 1.0, 1.03, 1.14

[State 1500, sound]
type = PlaySnd
trigger1 = AnimElem = 3
value = 0, 3

[State 1500, splash 1]
type = Explod
trigger1 = AnimElem = 4
anim = 7001
id = 1501
pos = 40,-70
postype = p1
sprpriority = 4
removetime = -2
trans = add

[State 1500, splash 2]
type = Explod
trigger1 = AnimElem = 6
anim = 7001
id = 1501
pos = 40,-70
postype = p1
sprpriority = 4
removetime = -2
trans = add

[State 1500, splash 3]
type = Explod
trigger1 = AnimElem = 8
anim = 7001
id = 1501
pos = 40,-70
postype = p1
sprpriority = 4
removetime = -2
trans = add

[State 1500, dart 1]
type = Projectile
trigger1 = AnimElem = 4
projanim = 7000
projhitanim = 7002
velocity = 14, 0
removetime = -1
projshadow = -1
damage = 37
attr = S, SP
guardflag = MA
pausetime = 4, 10
sparkno = 1
sparkxy = -10,-58
hitsound = 5,3
guardsound = 6,0
animtype = Hard
ground.type = High
ground.slidetime = 8
ground.hittime = 12
ground.velocity = -3
air.velocity = -3,-2.5

[State 1500, dart 2]
type = Projectile
trigger1 = AnimElem = 6
projanim = 7000
projhitanim = 7002
velocity = 14, 0
removetime = -1
projshadow = -1
damage = 33
attr = S, SP
guardflag = MA
pausetime = 4, 10
sparkno = 1
sparkxy = -10,-58
hitsound = 5,3
guardsound = 6,0
animtype = Hard
ground.type = High
ground.slidetime = 8
ground.hittime = 12
ground.velocity = -3
air.velocity = -3,-2.5

[State 1500, dart 3]
type = Projectile
trigger1 = AnimElem = 8
projanim = 7000
projhitanim = 7002
velocity = 14, 0
removetime = -1
projshadow = -1
damage = 30
attr = S, SP
guardflag = MA
pausetime = 4, 10
sparkno = 1
sparkxy = -10,-58
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

[State 1600, charged]
type = AfterImage
trigger1 = Time = 0
time = 16
length = 14
timegap = 1
framegap = 2
trans = add
paladd = 8, 30, 52
palmul = 1.0, 1.03, 1.14

[State 1600, sound]
type = PlaySnd
trigger1 = AnimElem = 3
value = 0, 3

[State 1600, cloudburst]
type = Projectile
trigger1 = AnimElem = 4
projanim = 7010
projhitanim = 7002
velocity = 10, 0
removetime = -1
projshadow = -1
damage = 86
attr = S, SP
guardflag = MA
pausetime = 8, 14
sparkno = 1
sparkxy = -10,-62
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

;---------------------------------------------------------------------------
; Rain Step - he comes down out of his own downpour.
; Down, then up: rain closes over him where he stood, and he lands on the far
; side of the opponent with the water still falling around him, and it hits.
;---------------------------------------------------------------------------
[Statedef 1700]
type    = S
movetype= A
physics = N
anim = 40
ctrl = 0
velset = 0,0
sprpriority = 2

[State 1700, thunder]
type = PlaySnd
trigger1 = time = 0
value = 0, 3

; the curtain he turns into, standing where he was
[State 1700, column]
type = Explod
trigger1 = time = 0
anim = 7020
id = 1720
postype = p1
pos = 0,0
sprpriority = 3
removetime = 30
trans = add
ownpal = 1

[State 1700, splash]
type = Explod
trigger1 = time = 2
anim = 7001
id = 1721
postype = p1
pos = 0,-186
sprpriority = 4
removetime = -2
trans = add
ownpal = 1

; he IS the rain while he travels - nothing of the body shows
[State 1700, gone]
type = AssertSpecial
trigger1 = time >= 4 && time < 26
flag = invisible

[State 1700, trail]
type = AfterImage
trigger1 = time = 4
time = 20
length = 8
timegap = 1
framegap = 1
trans = add
paladd = 8, 30, 52
palmul = 1.0, 1.03, 1.14

[State 1700, rise]
type = VelSet
trigger1 = time = 4
y = -40

; at the top, cross to the far side of the opponent
[State 1700, cross]
type = PosSet
trigger1 = time = 20
x = enemy, pos x + ifelse(facing = 1, 78, -78)

[State 1700, apex]
type = PosSet
trigger1 = time = 20
y = -540

[State 1700, drop]
type = VelSet
trigger1 = time = 20
y = 46

[State 1700, land]
type = ChangeState
trigger1 = time > 20 && pos y >= 0
value = 1702

;---------------------------------------------------------------------------
[Statedef 1702]
type    = S
movetype= A
physics = N
juggle  = 4
anim = 1700
ctrl = 0
velset = 0,0
sprpriority = 2

; he came down behind the opponent, so turn and hit him
[State 1702, turn]
type = Turn
trigger1 = time = 0
trigger1 = p2bodydist X < 0

[State 1702, column]
type = Explod
trigger1 = time = 0
anim = 7020
id = 1722
postype = p1
pos = 0,0
sprpriority = 3
removetime = 16
trans = add
ownpal = 1

[State 1702, shake]
type = EnvShake
trigger1 = time = 0
time = 8
freq = 90
ampl = -12

[State 1702, thunder]
type = PlaySnd
trigger1 = time = 0
value = 0, 4

[State 1702, strike]
type = HitDef
trigger1 = time = 1
attr = S, HA
damage = 104
guardflag = MA
hitflag = MAF
pausetime = 10, 14
sparkno = 1
sparkxy = -30,-174
hitsound = 5,4
guardsound = 6,0
animtype = Hard
ground.type = High
ground.slidetime = 10
ground.hittime = 18
ground.velocity = -5,-5
air.velocity = -4,-6
fall = 1

[State 1702, end]
type = ChangeState
trigger1 = AnimTime = 0
value = 0
ctrl = 1

;---------------------------------------------------------------------------
; The water is not part of him: it is laid over the sprite, so the rakes and
; the cloak stay clean in every frame and the whole effect is one block here
; that can be switched off.
;---------------------------------------------------------------------------
[Statedef -2]
type = Explod
trigger1 = !(time % 10)
anim = 7030
id = 7300
postype = p1
pos = 0,-186
sprpriority = 4
removetime = 14
trans = add
ownpal = 1
"""

EXTRA_SPECIALS = """Rain Dart\t\t\t\t\t\t\t_QDB^K
Cloudburst\t\t\t\t\t\t\t_QDBF^K
Rain Step\t\t\t\t\t\t\t_D_U
"""
