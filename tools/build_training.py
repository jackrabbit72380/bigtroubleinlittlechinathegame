"""Paint the training room at the game's native 1920x1080.

The room was Elecbyte's stock stage: localcoord 320x240, a 50px-wide strip of
floor tiled across the screen and a 35x57 crate. The engine stretches that to
fill a 1080p display, so it was a six-times-blown-up arcade picture with a
visible tile seam down the middle - "not showing right size", and past saving by
scaling, because the source art is 50 pixels wide.

This paints the room at the size the rest of the game is drawn at and writes it
out as stages/stage0.sff + stage0.def: localcoord 1920x1080, a 2440-wide
backdrop (one screen plus the camera's travel each way), floor at row 900, and
the select screen's 1215x398 preview as 9000,1 like every other stage.

Run:  python3 tools/build_training.py
"""

from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGE = os.path.join(ROOT, "stages", "stage0")

SCREEN = (1920, 1080)
TRAVEL = 260                       # camera travel each way
W = SCREEN[0] + 2 * TRAVEL         # 2440: the painted backdrop
START_X = -TRAVEL
FLOOR_Y = 900                      # zoffset
PREVIEW = (1215, 398)              # the card art every stage bakes

GOLD = (206, 168, 86)
GOLD_DIM = (120, 96, 46)
INK = (10, 12, 13)


def backdrop():
    """Concrete hall, timber floor, a grid chalked down the middle."""
    img = art.vgrad((W, SCREEN[1]),
                    [(0, (10, 12, 14)), (240, (20, 23, 25)),
                     (FLOOR_Y - 40, (16, 18, 19)), (FLOOR_Y, (13, 14, 15)),
                     (SCREEN[1], (7, 8, 9))]).convert("RGBA")
    img = Image.alpha_composite(
        img, art.radial_light((W, SCREEN[1]), (W // 2, 210), 900,
                              (74, 96, 92), peak=80))

    d = ImageDraw.Draw(img)

    # --- wall: panelled concrete, one seam every 305px -------------------
    for x in range(-40, W, 305):
        d.rectangle([x, 0, x + 303, FLOOR_Y], outline=(34, 38, 40), width=3)
        d.line([(x + 3, 0), (x + 3, FLOOR_Y)], fill=(24, 27, 29), width=2)
    # a darker skirting band where the wall meets the floor
    d.rectangle([0, FLOOR_Y - 46, W, FLOOR_Y], fill=(15, 16, 17, 190))
    d.line([(0, FLOOR_Y - 46), (W, FLOOR_Y - 46)], fill=(46, 44, 38), width=3)
    d.rectangle([0, FLOOR_Y - 10, W, FLOOR_Y - 4], fill=GOLD_DIM + (255,))

    # --- floor: boards running to the vanishing point ---------------------
    vp = (W // 2, FLOOR_Y - 140)
    for i in range(-16, 17):
        x = W // 2 + i * 190
        d.line([vp, (x, SCREEN[1])], fill=(30, 30, 29), width=3)
    # cross boards, spaced tighter towards the horizon
    y = float(FLOOR_Y + 6)
    step = 10.0
    while y < SCREEN[1]:
        d.line([(0, y), (W, y)], fill=(26, 26, 25), width=2)
        y += step
        step *= 1.28

    # --- banner across the back wall --------------------------------------
    f = art.font(96)
    text = "TRAINING ROOM"
    tw = d.textlength(text, font=f)
    d.text(((W - tw) / 2.0, 120), text, font=f, fill=GOLD + (255,),
           stroke_width=6, stroke_fill=INK + (255,))
    d.line([(W // 2 - 420, 250), (W // 2 + 420, 250)], fill=GOLD_DIM + (255,), width=4)

    # --- two work lights on the wall --------------------------------------
    for x in (W // 2 - 470, W // 2 + 470):
        d.rectangle([x - 46, 40, x + 46, 88], fill=(22, 24, 24),
                    outline=(58, 54, 44), width=3)
        d.ellipse([x - 34, 62, x + 34, 118], fill=(255, 226, 158, 210))
        img = Image.alpha_composite(img, art.radial_light(
            (W, SCREEN[1]), (x, 110), 330, (255, 210, 130), peak=64))

    # chalk centre line the fighters square up on
    cx = W // 2
    for k in range(0, SCREEN[1] - FLOOR_Y, 22):
        d.line([(cx, FLOOR_Y + k), (cx, FLOOR_Y + k + 12)],
               fill=(180, 180, 172, 90), width=4)

    img = art.vignette(img, strength=0.5)
    return art.grain(img, amount=4, seed=11)


def preview(img):
    """The card art: the on-screen window, cropped to the card's 3:1 strip."""
    view = img.crop((TRAVEL, 0, TRAVEL + SCREEN[0], SCREEN[1]))
    top = FLOOR_Y - 500
    band = view.crop((0, top, SCREEN[0], top + int(SCREEN[0] * PREVIEW[1] / PREVIEW[0])))
    return band.resize(PREVIEW, Image.LANCZOS)


DEF = """;---------------------------------------------------------------------------
; Training Room
; Part of Big Trouble in Little China: The Game (Ikemen GO)
; Painted at 1920x1080 by tools/build_training.py.
;---------------------------------------------------------------------------
[Info]
name = "Training Room"
displayname = "Training Room"
versiondate = 11,05,2026
mugenversion = 1.0
author = "Big Trouble in Little China: The Game"

[Camera]
startx = 0
starty = 0
boundleft = -{travel}
boundright = {travel}
boundhigh = -112
boundlow = 0
verticalfollow = .2
floortension = 0
tension = 60
overdrawhigh = 0
overdrawlow = 0
cuthigh = 0
cutlow = 126
zoomout = 1
zoomin = 1

[PlayerInfo]
p1startx = -170
p1starty = 0
p1facing = 1
p2startx = 170
p2starty = 0
p2facing = -1
leftbound = -{travel}
rightbound = {travel}

[Bound]
screenleft = 15
screenright = 15

[StageInfo]
zoffset = {floor}
autoturn = 1
resetBG = 1
localcoord = 1920, 1080
xscale = 1
yscale = 1

[Shadow]
intensity = 0
color = 0,0,0
yscale = -.1
fade.range = -400,-100

[Reflection]
intensity = 0

[Music]
bgmusic =
bgmvolume = 100

[BGdef]
spr = stage0.sff
debugbg = 0

; IKEMEN GO select-screen preview
[Begin Action 9000]
9000,1, 0,0, -1

; the room: one painted plate, camera travel included in the art
[BG room]
type = normal
spriteno = 0,0
layerno = 0
start = {start},0
delta = 1,1
trans = none
mask = 1
tile = 0,0
"""


def main():
    img = backdrop()
    sprites = [
        {"group": 0, "number": 0, "image": img, "axis": (0, 0)},
        {"group": 9000, "number": 1, "image": preview(img), "axis": (0, 0)},
    ]
    with open(STAGE + ".sff", "wb") as f:
        f.write(sff.write_sff(sprites))
    with open(STAGE + ".def", "w", encoding="utf-8", newline="\n") as f:
        f.write(DEF.format(travel=TRAVEL, floor=FLOOR_Y, start=START_X))

    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    img.save(os.path.join(ROOT, "artifacts", "training_room.png"))
    print("  training room: %dx%d backdrop, preview %dx%d, localcoord 1920x1080"
          % (img.width, img.height, PREVIEW[0], PREVIEW[1]))


if __name__ == "__main__":
    main()
