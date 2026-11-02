"""Thunder: pressure, not lightning.

Thunder is the heavy one of the Three Storms, and his power is the clap - a
wall of compressed air that rings out of both fists and shakes the room. There
is no electricity anywhere in this module: Lightning owns that, and the two
brothers must not read as the same fighter. What he throws is a pale gold
pressure ring; what it hits with is the air behind it, with the dust of the
floor coming up under the wave.

He reuses the plumbing Jack's pistol occupies (states 1500/1600, animations
7000-7030, commands on kicks), so ``bake_char`` swaps the pose and every
trigger still lines up.

Run:  imported by tools/build_chars.py
"""

from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw, ImageFilter

# Compressed air: pale gold-white, never blue. The blue in this game belongs to
# Lightning's bolts and Rain's water, and a third blue effect read as one of
# them.
RING = (246, 232, 196)
RING_LIT = (255, 250, 232)
CORE = (255, 255, 252)
DUST = (138, 110, 78)
DUST_LIT = (178, 148, 108)
DEEP = (96, 74, 48)


def _blank(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def _glow(img, radius):
    return img.filter(ImageFilter.GaussianBlur(radius))


def ring(step=0):
    """The travelling clap: one compressed ring of air, sawing outward."""
    w = h = 46
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    rx, ry = 15.0 + step * 1.5, 12.0 + step * 1.2
    for k, (a, wid) in enumerate(((150, 6), (220, 4), (255, 2))):
        rr = 1.0 - k * 0.22
        d.ellipse([23 - rx * rr, 23 - ry * rr, 23 + rx * rr, 23 + ry * rr],
                  outline=RING + (a,), width=wid)
    d.ellipse([23 - 6, 23 - 5, 23 + 6, 23 + 5], fill=CORE + (235,))
    # the air behind the ring is displaced sideways, so the ring is not round
    for i in range(8):
        a = math.pi * 2 * i / 8 + 0.2
        x, y = 23 + math.cos(a) * (rx + 4), 23 + math.sin(a) * (ry + 3)
        d.line([(x, y), (x + math.cos(a) * 4, y + math.sin(a) * 4)],
               fill=RING_LIT + (150,), width=2)
    return Image.alpha_composite(_glow(img, 4), img)


def clap(step):
    """Both fists driven together: the burst off the hands."""
    w = h = 64
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    scale = (1.0, 1.35, 0.7)[step]
    for k, (r, a) in enumerate(((10, 235), (19, 200), (29, 150))):
        rr = r * scale
        d.ellipse([32 - rr, 32 - rr * 0.86, 32 + rr, 32 + rr * 0.86],
                  outline=RING + (a,), width=4 - k)
    d.ellipse([32 - 7 * scale, 32 - 6 * scale, 32 + 7 * scale, 32 + 6 * scale],
              fill=RING_LIT + (240,))
    d.ellipse([32 - 3, 32 - 3, 32 + 3, 32 + 3], fill=CORE + (255,))
    rnd = random.Random(step * 13 + 5)
    for i in range(7):
        a = math.pi * 2 * i / 7 + step * 0.35
        r0, r1 = 12 * scale, 22 * scale
        d.line([(32 + math.cos(a) * r0, 32 + math.sin(a) * r0 * 0.86),
                (32 + math.cos(a) * r1, 32 + math.sin(a) * r1 * 0.86)],
               fill=RING_LIT + (rnd.randint(140, 220),), width=2)
    return Image.alpha_composite(_glow(img, 3), img)


def impact(step):
    """Where it lands: the ring collapses and the floor dust jumps."""
    w = h = 38
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    scale = (1.0, 0.78, 0.5)[step]
    d.ellipse([19 - 9 * scale, 19 - 8 * scale, 19 + 9 * scale, 19 + 8 * scale],
              fill=RING_LIT + (225,))
    d.ellipse([19 - 4 * scale, 19 - 4 * scale, 19 + 4 * scale, 19 + 4 * scale],
              fill=CORE + (250,))
    rnd = random.Random(step * 17 + 3)
    for i in range(9):
        a = math.pi * 2 * i / 9 + step * 0.5
        r1 = (14 if i % 2 else 10) * scale
        x, y = 19 + math.cos(a) * r1, 19 + math.sin(a) * r1
        r = rnd.uniform(1.2, 2.8)
        d.ellipse([x - r, y - r, x + r, y + r],
                  fill=(DUST_LIT if i % 3 else RING_LIT) + (215,))
    return Image.alpha_composite(_glow(img, 2), img)


def wave(step):
    """Earthshaker: the pressure wall, rolling, with the floor coming up."""
    w, h = 104, 64
    img = _blank(w, h)
    d = ImageDraw.Draw(img)

    # the wall itself: a broad crescent of displaced air
    crest = []
    for i in range(11):
        t = i / 10.0
        crest.append((4 + 96 * t,
                      34 - math.sin(t * math.pi) * (17 + step * 1.8)
                      + math.sin(i * 1.9 + step * 1.3) * 3))
    body = [(4, 54), (100, 54)] + list(reversed(crest))
    d.polygon(body, fill=RING + (120,))
    d.line(crest, fill=RING + (200,), width=5, joint="curve")
    d.line([(x, y - 3) for x, y in crest], fill=RING_LIT + (235,), width=2,
           joint="curve")

    # grit lifted off the ground under it
    rnd = random.Random(step * 9 + 1)
    for i in range(14):
        x = 6 + rnd.uniform(0, 92)
        y = 46 + rnd.uniform(-8, 6) - step * 1.2
        r = rnd.uniform(1.4, 3.6)
        d.ellipse([x - r, y - r, x + r, y + r],
                  fill=(DUST if i % 2 else DUST_LIT) + (rnd.randint(110, 200),))
    return Image.alpha_composite(_glow(img, 4), img)


def column(step):
    """The air standing where he brought his fists down."""
    w, h = 56, 230
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    for i in range(5):
        x0 = 10 + i * 9
        pts = [(x0 + math.sin(k * 1.2 + step * 1.5) * 3.2, 6 + k * 15.0)
               for k in range(15)]
        d.line(pts, fill=RING + (105,), width=9, joint="curve")
        d.line(pts, fill=RING_LIT + (150,), width=4, joint="curve")
    for i in range(12):
        x = 8 + (i * 9 + step * 7) % 40
        y = (i * 29 + step * 21) % 214 + 8
        d.line([(x, y), (x + 2, y + 9)], fill=CORE + (170,), width=2)
    return Image.alpha_composite(_glow(img, 5), img)


def fists(step):
    """Air shimmering round both fists - an overlay, never part of the body."""
    w, h = 78, 54
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    rnd = random.Random(step * 5 + 9)
    for cx in (20, 58):
        for k in range(5):
            a = step * 0.9 + k * 1.25
            r = rnd.uniform(5, 12)
            x = cx + math.cos(a) * r
            y = 27 + math.sin(a) * r * 0.7
            rr = rnd.uniform(1.4, 2.8)
            d.ellipse([x - rr, y - rr, x + rr, y + rr],
                      fill=RING_LIT + (215,))
        d.arc([cx - 13, 14, cx + 13, 40], 200, 340,
              fill=RING + (170,), width=2)
    return Image.alpha_composite(_glow(img, 3), img)


def sprites():
    """Extra sprite records for Thunder's SFF."""
    out = [{"group": 7000, "number": 0, "image": ring(0), "axis": (23, 23)}]
    for i in range(3):
        out.append({"group": 7001, "number": i,
                    "image": clap(i), "axis": (32, 32)})
    for i in range(3):
        out.append({"group": 7002, "number": i,
                    "image": impact(i), "axis": (19, 19)})
    for i in range(4):
        out.append({"group": 7010, "number": i,
                    "image": wave(i), "axis": (52, 32)})
    for i in range(3):
        out.append({"group": 7020, "number": i,
                    "image": column(i), "axis": (28, 226)})
    for i in range(4):
        out.append({"group": 7030, "number": i,
                    "image": fists(i), "axis": (39, 27)})
    return out


def palettes(base_palettes, grade, spec):
    """No costume override: the roster's grading colours the body."""
    return [grade(p["rgba"], spec) for p in base_palettes]


# ------------------------------------------------------------------ animations
AIR = """
;---------------------------------------------------------------------------
; Thunder - air pressure animation set (added by tools/thunder.py)
; The 7000-series frames carry the AIR blend flag A, so the ring, the burst
; and the dust composite additively wherever they are drawn.
;---------------------------------------------------------------------------
; Pressure ring (projectile)
[Begin Action 7000]
Clsn1: 1
 Clsn1[0] = -12,-12, 12,12
7000,0, 0,0, -1, , A

; Clap burst at the hands
[Begin Action 7001]
7001,0, 0,0, 2, , A
7001,1, 0,0, 2, , A
7001,2, 0,0, -1, , A

; Impact ring
[Begin Action 7002]
7002,0, 0,0, 3, , A
7002,1, 0,0, 3, , A
7002,2, 0,0, -1, , A

; Earthshaker wall, rolling out
[Begin Action 7010]
Clsn1: 1
 Clsn1[0] = -40,-20, 40,20
7010,0, 0,0, 3, , A
7010,1, 0,0, 3, , A
7010,2, 0,0, 3, , A
7010,3, 0,0, 3, , A

; Standing column of displaced air
[Begin Action 7020]
7020,0, 0,0, 4, , A
7020,1, 0,0, 4, , A
7020,2, 0,0, -1, , A

; Air round the fists - an effect laid over the body, never in it
[Begin Action 7030]
7030,0, 0,0, 3, , A
7030,1, 0,0, 3, , A
7030,2, 0,0, 3, , A
7030,3, 0,0, -1, , A
"""


# ---------------------------------------------------------------------- command
CMD_COMMANDS = """
;-| Thunder - storm motions |---------------------------------------------
[Command]
name = "clap_a"
command = ~D, DB, B, a

[Command]
name = "clap_b"
command = ~D, DB, B, b

[Command]
name = "quake_a"
command = ~F, DF, D, DB, B, a

[Command]
name = "quake_b"
command = ~F, DF, D, DB, B, b

"""

CMD_STATES = """
;---------------------------------------------------------------------------
; Thunder - pressure specials
;---------------------------------------------------------------------------
;Thunder Clap (three rings)
[State -1, Thunder Clap]
type = ChangeState
value = 1500
triggerall = command = "clap_a" || command = "clap_b"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = movecontact
trigger2 = stateno != [1500,1600)

;Earthshaker (single heavy wall)
[State -1, Earthshaker]
type = ChangeState
value = 1600
triggerall = command = "quake_a" || command = "quake_b"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = movecontact
trigger2 = stateno != [1500,1600)
"""


# ------------------------------------------------------------------------ state
CNS = """
;---------------------------------------------------------------------------
; Thunder - pressure specials
; The clap is three rings on consecutive beats, each lighter than the last, so
; the volley lands about as hard as one solid strike. The Earthshaker is a
; single rolling wall of compressed air that carries across the screen and
; brings the floor up with it.
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
paladd = 26, 20, 4
palmul = 1.06, 1.03, 0.98

[State 1500, sound]
type = PlaySnd
trigger1 = AnimElem = 3
value = 0, 3

[State 1500, burst 1]
type = Explod
trigger1 = AnimElem = 4
anim = 7001
id = 1501
pos = 40,-70
postype = p1
sprpriority = 4
removetime = -2
trans = add

[State 1500, burst 2]
type = Explod
trigger1 = AnimElem = 6
anim = 7001
id = 1501
pos = 40,-70
postype = p1
sprpriority = 4
removetime = -2
trans = add

[State 1500, burst 3]
type = Explod
trigger1 = AnimElem = 8
anim = 7001
id = 1501
pos = 40,-70
postype = p1
sprpriority = 4
removetime = -2
trans = add

[State 1500, ring 1]
type = Projectile
trigger1 = AnimElem = 4
projanim = 7000
projhitanim = 7002
velocity = 13, 0
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
ground.velocity = -4
air.velocity = -3,-2.5

[State 1500, ring 2]
type = Projectile
trigger1 = AnimElem = 6
projanim = 7000
projhitanim = 7002
velocity = 13, 0
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
ground.velocity = -4
air.velocity = -3,-2.5

[State 1500, ring 3]
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

[State 1600, charged]
type = AfterImage
trigger1 = Time = 0
time = 16
length = 14
timegap = 1
framegap = 2
trans = add
paladd = 26, 20, 4
palmul = 1.06, 1.03, 0.98

[State 1600, sound]
type = PlaySnd
trigger1 = AnimElem = 3
value = 0, 3

[State 1600, shake]
type = EnvShake
trigger1 = AnimElem = 4
time = 10
freq = 70
ampl = -8

[State 1600, earthshaker]
type = Projectile
trigger1 = AnimElem = 4
projanim = 7010
projhitanim = 7002
velocity = 9, 0
removetime = -1
projshadow = -1
damage = 92
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
; The pressure is not part of him: it is laid over the sprite, so the blades
; and the cloak stay clean in every frame.
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
"""

EXTRA_SPECIALS = """Thunder Clap\t\t\t\t\t\t\t_QDB^K
Earthshaker\t\t\t\t\t\t\t_QDBF^K
"""
