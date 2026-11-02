"""Lo Pan: sorcery, green and slow.

Lo Pan does not throw anything. His magic is conjured: sigils drawn in the air
that hang for a beat and then fly, fire that burns green, and the claws of
spirits he calls up out of the floor. There is no bolt (that is Lightning), no
water (Rain) and no press of air (Thunder) - his effects are runes, ghost-fire
and a spectral hand, all of it in the sickly jade light that fills his throne
room.

He reuses the plumbing Jack's pistol occupies (states 1500/1600, animations
7000-7030, commands on kicks), so ``bake_char`` swaps the pose and every
trigger still lines up.

Run:  imported by tools/build_chars.py
"""

from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw, ImageFilter

# Sorcery green: the light under the throne. Never blue and never white-hot -
# it has to sit apart from Lightning's arcs and Thunder's pale air.
JADE = (104, 226, 158)
JADE_LIT = (186, 255, 214)
CORE = (240, 255, 246)
DEEP = (26, 92, 66)
GHOST = (150, 214, 190)


def _blank(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def _glow(img, radius):
    return img.filter(ImageFilter.GaussianBlur(radius))


def _rune(d, cx, cy, r, angle=0.0, points=5):
    """A star-rune: a pentacle of strokes with a ring round it."""
    d.ellipse([cx - r, cy - r * 0.86, cx + r, cy + r * 0.86],
              outline=JADE + (200,), width=2)
    pts = []
    for k in range(points):
        a = angle + math.pi * 2 * k / points
        pts.append((cx + math.cos(a) * r * 0.82, cy + math.sin(a) * r * 0.72))
    for k in range(points):
        a, b = pts[k], pts[(k + 2) % points]
        d.line([a, b], fill=JADE_LIT + (185,), width=2)


def sigil(step=0):
    """The travelling conjuration: a rune, turning as it flies."""
    w = h = 48
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    _rune(d, 24, 24, 15 - step * 0.5, angle=step * 0.4)
    d.ellipse([19, 19, 29, 29], fill=CORE + (215,))
    for k in range(6):
        a = step * 0.5 + math.pi * 2 * k / 6
        d.point([(24 + math.cos(a) * 19, 24 + math.sin(a) * 16)],
                fill=JADE_LIT + (220,))
    return Image.alpha_composite(_glow(img, 4), img)


def cast(step):
    """The conjuring at his hands: a rune opening in the air."""
    w = h = 66
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    scale = (0.75, 1.15, 1.0)[step]
    _rune(d, 33, 33, 17 * scale, angle=step * 0.55)
    d.ellipse([33 - 6 * scale, 33 - 5 * scale, 33 + 6 * scale, 33 + 5 * scale],
              fill=JADE_LIT + (240,))
    d.ellipse([33 - 3, 33 - 3, 33 + 3, 33 + 3], fill=CORE + (255,))
    rnd = random.Random(step * 19 + 4)
    for i in range(10):
        a = math.pi * 2 * i / 10 + step * 0.5
        r0, r1 = 20 * scale, 28 * scale
        d.line([(33 + math.cos(a) * r0, 33 + math.sin(a) * r0 * 0.8),
                (33 + math.cos(a) * r1, 33 + math.sin(a) * r1 * 0.8)],
               fill=JADE + (rnd.randint(120, 210),), width=2)
    return Image.alpha_composite(_glow(img, 3), img)


def impact(step):
    """Where the sigil lands: it breaks into spirits and green sparks."""
    w = h = 40
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    scale = (1.0, 0.8, 0.5)[step]
    d.ellipse([20 - 9 * scale, 20 - 8 * scale, 20 + 9 * scale, 20 + 8 * scale],
              fill=JADE_LIT + (220,))
    d.ellipse([20 - 4 * scale, 20 - 3 * scale, 20 + 4 * scale, 20 + 3 * scale],
              fill=CORE + (250,))
    rnd = random.Random(step * 23 + 7)
    for i in range(10):
        a = math.pi * 2 * i / 10 + step * 0.6
        r = (13 if i % 2 else 8) * scale
        x, y = 20 + math.cos(a) * r, 20 + math.sin(a) * r * 0.9 - step * 2
        rr = rnd.uniform(1.2, 2.6)
        d.ellipse([x - rr, y - rr, x + rr, y + rr],
                  fill=(JADE_LIT if i % 2 else GHOST) + (215,))
    return Image.alpha_composite(_glow(img, 2), img)


def fire(step):
    """Green fire, rolling: the crest climbs and leans as it travels."""
    w, h = 96, 62
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    crest = []
    for i in range(11):
        t = i / 10.0
        crest.append((4 + 88 * t,
                      38 - math.sin(t * math.pi) * (16 + step * 1.7)
                      + math.sin(i * 2.2 + step * 1.5) * 4))
    body = [(4, 58), (92, 58)] + list(reversed(crest))
    d.polygon(body, fill=DEEP + (170,))
    d.polygon([(x, y + 6) for x, y in crest] + [(92, 58), (4, 58)],
              fill=JADE + (150,))
    d.line(crest, fill=JADE_LIT + (225,), width=4, joint="curve")
    for i in (2, 5, 8):
        x, y = crest[i]
        d.line([(x, y), (x + (i - 5) * 1.5, y - 9 - step)], fill=JADE_LIT + (200,),
               width=2)
        d.point([(x + (i - 5) * 1.5, y - 10 - step)], fill=CORE + (255,))
    for i in range(9):
        x = 8 + i * 10
        y = 40 - (i % 3) * 3 + step
        d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=GHOST + (170,))
    return Image.alpha_composite(_glow(img, 4), img)


def spirits(step):
    """The column of the dead he raises: faces in a shaft of green light."""
    w, h = 54, 220
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    for i in range(4):
        x0 = 14 + i * 9
        pts = [(x0 + math.sin(k * 1.1 + step * 1.4) * 3.4, 8 + k * 14.5)
               for k in range(15)]
        d.line(pts, fill=JADE + (95,), width=9, joint="curve")
        d.line(pts, fill=JADE_LIT + (135,), width=4, joint="curve")
    rnd = random.Random(step * 11 + 3)
    for i in range(4):
        y = 30 + i * 46 - (step * 6) % 46
        x = 27 + math.sin(step + i) * 9
        d.ellipse([x - 5, y - 6, x + 5, y + 5], fill=GHOST + (150,))
        d.point([(x - 2, y - 2)], fill=CORE + (200,))
        d.point([(x + 2, y - 2)], fill=CORE + (200,))
    return Image.alpha_composite(_glow(img, 5), img)


def hands(step):
    """Light gathered round his hands - an overlay, never part of the body."""
    w, h = 76, 52
    img = _blank(w, h)
    d = ImageDraw.Draw(img)
    rnd = random.Random(step * 3 + 11)
    for cx in (19, 57):
        for k in range(5):
            a = step * 0.85 + k * 1.3
            r = rnd.uniform(5, 11)
            x = cx + math.cos(a) * r
            y = 26 + math.sin(a) * r * 0.7
            rr = rnd.uniform(1.3, 2.6)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=JADE_LIT + (200,))
        d.arc([cx - 12, 14, cx + 12, 38], 195, 345, fill=JADE + (175,), width=2)
    return Image.alpha_composite(_glow(img, 3), img)


def sprites():
    """Extra sprite records for Lo Pan's SFF."""
    out = [{"group": 7000, "number": 0, "image": sigil(0), "axis": (24, 24)}]
    for i in range(3):
        out.append({"group": 7001, "number": i,
                    "image": cast(i), "axis": (33, 33)})
    for i in range(3):
        out.append({"group": 7002, "number": i,
                    "image": impact(i), "axis": (20, 20)})
    for i in range(4):
        out.append({"group": 7010, "number": i,
                    "image": fire(i), "axis": (48, 31)})
    for i in range(3):
        out.append({"group": 7020, "number": i,
                    "image": spirits(i), "axis": (27, 216)})
    for i in range(4):
        out.append({"group": 7030, "number": i,
                    "image": hands(i), "axis": (38, 26)})
    return out


def palettes(base_palettes, grade, spec):
    """No costume override: the roster's grading colours the body."""
    return [grade(p["rgba"], spec) for p in base_palettes]


# ------------------------------------------------------------------ animations
AIR = """
;---------------------------------------------------------------------------
; Lo Pan - sorcery animation set (added by tools/lopan.py)
; The 7000-series frames carry the AIR blend flag A, so the runes and the
; green fire composite additively wherever they are drawn.
;---------------------------------------------------------------------------
; Conjured sigil (projectile)
[Begin Action 7000]
Clsn1: 1
 Clsn1[0] = -13,-13, 13,13
7000,0, 0,0, -1, , A

; Rune opening at the hands
[Begin Action 7001]
7001,0, 0,0, 2, , A
7001,1, 0,0, 2, , A
7001,2, 0,0, -1, , A

; Sigil breaking, spirits released
[Begin Action 7002]
7002,0, 0,0, 3, , A
7002,1, 0,0, 3, , A
7002,2, 0,0, -1, , A

; Green fire, rolling out
[Begin Action 7010]
Clsn1: 1
 Clsn1[0] = -38,-18, 38,18
7010,0, 0,0, 3, , A
7010,1, 0,0, 3, , A
7010,2, 0,0, 3, , A
7010,3, 0,0, 3, , A

; Column of spirits
[Begin Action 7020]
7020,0, 0,0, 4, , A
7020,1, 0,0, 4, , A
7020,2, 0,0, -1, , A

; Light at his hands - laid over the body, never in it
[Begin Action 7030]
7030,0, 0,0, 3, , A
7030,1, 0,0, 3, , A
7030,2, 0,0, 3, , A
7030,3, 0,0, -1, , A
"""


# ---------------------------------------------------------------------- command
CMD_COMMANDS = """
;-| Lo Pan - sorcerous motions |------------------------------------------
[Command]
name = "sigil_a"
command = ~D, DB, B, a

[Command]
name = "sigil_b"
command = ~D, DB, B, b

[Command]
name = "hellfire_a"
command = ~F, DF, D, DB, B, a

[Command]
name = "hellfire_b"
command = ~F, DF, D, DB, B, b

"""

CMD_STATES = """
;---------------------------------------------------------------------------
; Lo Pan - sorcery
;---------------------------------------------------------------------------
;Sigils of the Six (three conjured runes)
[State -1, Sigils of the Six]
type = ChangeState
value = 1500
triggerall = command = "sigil_a" || command = "sigil_b"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = movecontact
trigger2 = stateno != [1500,1600)

;Hell of Boiling Oil (single rolling wall of green fire)
[State -1, Hell of Boiling Oil]
type = ChangeState
value = 1600
triggerall = command = "hellfire_a" || command = "hellfire_b"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = movecontact
trigger2 = stateno != [1500,1600)
"""


# ------------------------------------------------------------------------ state
CNS = """
;---------------------------------------------------------------------------
; Lo Pan - sorcery
; Three sigils on consecutive beats, each weaker than the last, because they
; are drawn rather than thrown. The second is the fire he calls up out of the
; floor: one wall, slow, and it carries.
;---------------------------------------------------------------------------
[Statedef 1500]
type    = S
movetype= A
physics = S
juggle  = 4
poweradd= 50
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
paladd = 4, 26, 12
palmul = 1.0, 1.06, 1.0

[State 1500, sound]
type = PlaySnd
trigger1 = AnimElem = 3
value = 0, 3

[State 1500, rune 1]
type = Explod
trigger1 = AnimElem = 4
anim = 7001
id = 1501
pos = 40,-70
postype = p1
sprpriority = 4
removetime = -2
trans = add

[State 1500, rune 2]
type = Explod
trigger1 = AnimElem = 6
anim = 7001
id = 1501
pos = 40,-70
postype = p1
sprpriority = 4
removetime = -2
trans = add

[State 1500, rune 3]
type = Explod
trigger1 = AnimElem = 8
anim = 7001
id = 1501
pos = 40,-70
postype = p1
sprpriority = 4
removetime = -2
trans = add

[State 1500, sigil 1]
type = Projectile
trigger1 = AnimElem = 4
projanim = 7000
projhitanim = 7002
velocity = 12, 0
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

[State 1500, sigil 2]
type = Projectile
trigger1 = AnimElem = 6
projanim = 7000
projhitanim = 7002
velocity = 12, 0
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

[State 1500, sigil 3]
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
poweradd= 60
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
paladd = 4, 26, 12
palmul = 1.0, 1.06, 1.0

[State 1600, sound]
type = PlaySnd
trigger1 = AnimElem = 3
value = 0, 3

; the dead rise where he stands
[State 1600, spirits]
type = Explod
trigger1 = AnimElem = 4
anim = 7020
id = 1601
postype = p1
pos = 0,0
sprpriority = 3
removetime = 34
trans = add

[State 1600, fire]
type = Projectile
trigger1 = AnimElem = 4
projanim = 7010
projhitanim = 7002
velocity = 8, 0
removetime = -1
projshadow = -1
damage = 96
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
; The conjuring is laid over him rather than painted into him, so the robe and
; the headdress stay clean in every frame.
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

EXTRA_SPECIALS = """Sigils of the Six\t\t\t\t\t\t\t_QDB^K
Hell of Boiling Oil\t\t\t\t\t\t_QDBF^K
"""
