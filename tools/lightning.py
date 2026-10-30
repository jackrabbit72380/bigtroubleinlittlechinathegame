"""Lightning: thrown electricity instead of fists.

Lightning is the Three Storms' fastest, so his two specials are projectiles
rather than weapon moves: a three-bolt volley and a single heavier bolt. They
reuse the same slot Jack's pistol and knife occupy (states 1500 and 1600,
animations 7000/7001/7002/7010, commands on kicks), which is what lets
``bake_char`` swap the pose and keep all the plumbing.

The art is PNG32 written alongside the indexed base sprites, like Jack's.

Run:  imported by tools/build_chars.py
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFilter

BOLT = (128, 200, 255)
BOLT_LIT = (206, 236, 255)
CORE = (248, 253, 255)
DEEP = (48, 96, 168)


def _blank(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def _glow(img, radius):
    return img.filter(ImageFilter.GaussianBlur(radius))


def bolt_orb():
    """The travelling projectile: a hot core wrapped in crackling arcs."""
    w = h = 34
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    halo = _blank(w, h)
    hd = ImageDraw.Draw(halo)
    hd.ellipse([2, 2, 31, 31], fill=BOLT + (150,))
    img = Image.alpha_composite(img, _glow(halo, 5))
    d = ImageDraw.Draw(img)
    d.ellipse([6, 6, 27, 27], fill=BOLT + (200,))
    d.ellipse([10, 10, 23, 23], fill=BOLT_LIT + (255,))
    d.ellipse([13, 13, 20, 20], fill=CORE + (255,))
    # arcs spitting off the ball
    for i in range(6):
        a = math.pi * 2 * i / 6 + 0.4
        x0 = 17 + math.cos(a) * 9
        y0 = 17 + math.sin(a) * 9
        x1 = 17 + math.cos(a) * 16
        y1 = 17 + math.sin(a) * 16
        mx = (x0 + x1) / 2 + math.cos(a + 1.2) * 3
        my = (y0 + y1) / 2 + math.sin(a + 1.2) * 3
        d.line([(x0, y0), (mx, my), (x1, y1)], fill=BOLT_LIT + (230,), width=2)
    return img


def discharge(step):
    """Three-frame burst of current at the hand as the bolt leaves."""
    w = h = 52
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    scale = (1.0, 1.35, 0.7)[step]
    for i in range(9):
        a = math.pi * 2 * i / 9 + step * 0.5
        r0, r1 = 4, (9 if i % 2 else 20) * scale
        d.line([(26 + math.cos(a) * r0, 26 + math.sin(a) * r0),
                (26 + math.cos(a) * r1, 26 + math.sin(a) * r1)],
               fill=(BOLT if i % 2 else BOLT_LIT) + (220,), width=3)
    d.ellipse([26 - 8 * scale, 26 - 8 * scale, 26 + 8 * scale, 26 + 8 * scale],
              fill=BOLT_LIT + (235,))
    d.ellipse([26 - 4 * scale, 26 - 4 * scale, 26 + 4 * scale, 26 + 4 * scale],
              fill=CORE + (255,))
    return Image.alpha_composite(_glow(img, 3), img)


def impact(step):
    """Electric hit spark: radial spikes collapsing frame by frame."""
    w = h = 34
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    scale = (1.0, 0.78, 0.5)[step]
    for i in range(8):
        a = math.pi * 2 * i / 8 + step * 0.35
        r0 = 2
        r1 = (14 if i % 2 == 0 else 9) * scale
        mx = 17 + math.cos(a + 0.4) * r1 * 0.6
        my = 17 + math.sin(a + 0.4) * r1 * 0.6
        d.line([(17 + math.cos(a) * r0, 17 + math.sin(a) * r0), (mx, my),
                (17 + math.cos(a) * r1, 17 + math.sin(a) * r1)],
               fill=(BOLT_LIT if i % 2 else BOLT) + (235,), width=2)
    d.ellipse([17 - 6 * scale, 17 - 6 * scale, 17 + 6 * scale, 17 + 6 * scale],
              fill=CORE + (240,))
    return Image.alpha_composite(_glow(img, 2), img)


def arc_bolt(step):
    """Four-frame spear of lightning, re-jagged each frame so it crackles."""
    w, h = 78, 46
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    pts = [(3, 23)]
    for i in range(1, 9):
        t = i / 9.0
        pts.append((3 + 68 * t, 23 + math.sin(i * 2.3 + step * 1.7) * 12))
    pts.append((73, 23))
    d.line(pts, fill=BOLT + (200,), width=7, joint="curve")
    d.line(pts, fill=BOLT_LIT + (235,), width=4, joint="curve")
    d.line(pts, fill=CORE + (255,), width=2, joint="curve")
    # a couple of branches
    for i in (3, 6):
        x, y = pts[i]
        d.line([(x, y), (x + 9, y + (9 if i % 2 else -9))],
               fill=BOLT_LIT + (200,), width=2)
    return Image.alpha_composite(_glow(img, 3), img)


def sprites():
    """Extra sprite records for Lightning's SFF."""
    out = [{"group": 7000, "number": 0, "image": bolt_orb(), "axis": (17, 17)}]
    for i in range(3):
        out.append({"group": 7001, "number": i,
                    "image": discharge(i), "axis": (26, 26)})
    for i in range(3):
        out.append({"group": 7002, "number": i,
                    "image": impact(i), "axis": (17, 17)})
    for i in range(4):
        out.append({"group": 7010, "number": i,
                    "image": arc_bolt(i), "axis": (39, 23)})
    return out


def palettes(base_palettes, grade, spec):
    """No costume override: the roster's grading colours the body."""
    return [grade(p["rgba"], spec) for p in base_palettes]


# ------------------------------------------------------------------ animations
AIR = """
;---------------------------------------------------------------------------
; Lightning - projectile animation set (added by tools/lightning.py)
;---------------------------------------------------------------------------
; Bolt (projectile)
[Begin Action 7000]
Clsn1: 1
 Clsn1[0] = -10,-10, 10,10
7000,0, 0,0, -1

; Discharge at the hand
[Begin Action 7001]
7001,0, 0,0, 2
7001,1, 0,0, 2
7001,2, 0,0, -1

; Impact spark
[Begin Action 7002]
7002,0, 0,0, 3
7002,1, 0,0, 3
7002,2, 0,0, -1

; Thunderbolt, crackling on its way out
[Begin Action 7010]
Clsn1: 1
 Clsn1[0] = -30,-14, 30,14
7010,0, 0,0, 3
7010,1, 0,0, 3
7010,2, 0,0, 3
7010,3, 0,0, 3
"""


# ---------------------------------------------------------------------- command
CMD_COMMANDS = """
;-| Lightning - storm motions |-------------------------------------------
[Command]
name = "volt_a"
command = ~D, DB, B, a

[Command]
name = "volt_b"
command = ~D, DB, B, b

[Command]
name = "thunder_a"
command = ~F, DF, D, DB, B, a

[Command]
name = "thunder_b"
command = ~F, DF, D, DB, B, b

"""

CMD_STATES = """
;---------------------------------------------------------------------------
; Lightning - storm specials
;---------------------------------------------------------------------------
;Volt Volley (three bolts)
[State -1, Volt Volley]
type = ChangeState
value = 1500
triggerall = command = "volt_a" || command = "volt_b"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = movecontact
trigger2 = stateno != [1500,1600)

;Thunderbolt (single heavy bolt)
[State -1, Thunderbolt]
type = ChangeState
value = 1600
triggerall = command = "thunder_a" || command = "thunder_b"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = movecontact
trigger2 = stateno != [1500,1600)
"""


# ------------------------------------------------------------------------ state
CNS = """
;---------------------------------------------------------------------------
; Lightning - storm specials
; The volley is three bolts on consecutive thrusts, each weaker than the last,
; so the whole volley hurts about as much as one solid strike. The Thunderbolt
; is a single heavy shot that keeps crackling all the way across the screen.
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

[State 1500, discharge 1]
type = Explod
trigger1 = AnimElem = 4
anim = 7001
id = 1501
pos = 40,-70
postype = p1
sprpriority = 4
removetime = -2

[State 1500, discharge 2]
type = Explod
trigger1 = AnimElem = 6
anim = 7001
id = 1501
pos = 40,-70
postype = p1
sprpriority = 4
removetime = -2

[State 1500, discharge 3]
type = Explod
trigger1 = AnimElem = 8
anim = 7001
id = 1501
pos = 40,-70
postype = p1
sprpriority = 4
removetime = -2

[State 1500, bolt 1]
type = Projectile
trigger1 = AnimElem = 4
projanim = 7000
projhitanim = 7002
velocity = 13, 0
removetime = -1
projshadow = -1
damage = 38
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

[State 1500, bolt 2]
type = Projectile
trigger1 = AnimElem = 6
projanim = 7000
projhitanim = 7002
velocity = 13, 0
removetime = -1
projshadow = -1
damage = 34
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

[State 1500, bolt 3]
type = Projectile
trigger1 = AnimElem = 8
projanim = 7000
projhitanim = 7002
velocity = 13, 0
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

[State 1600, sound]
type = PlaySnd
trigger1 = AnimElem = 3
value = 0, 3

[State 1600, thunderbolt]
type = Projectile
trigger1 = AnimElem = 4
projanim = 7010
projhitanim = 7002
velocity = 11, 0
removetime = -1
projshadow = -1
damage = 82
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
"""

EXTRA_SPECIALS = """Volt Volley\\t\\t\\t\\t\\t\\t\\t_QDB^K
Thunderbolt\\t\\t\\t\\t\\t\\t\\t_QDBF^K
"""
