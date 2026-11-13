"""Paint the training room at the game's native 1920x1080.

The room was Elecbyte's stock stage: localcoord 320x240, a 50px-wide strip of
floor tiled across the screen and a 35x57 crate. The engine stretches that to
fill a 1080p display, so it was a six-times-blown-up arcade picture with a
visible tile seam down the middle - "not showing right size", and past saving by
scaling, because the source art is 50 pixels wide.

This paints the room at the size the rest of the game is drawn at and writes it
out as stages/stage0.sff + stage0.def: localcoord 1920x1080, a 2440-wide
backdrop (one screen plus the camera's travel each way and a little slack),
floor at row 900, and
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
# 900, not 260. boundleft/boundright clamp the FIGHTERS as much as the camera:
# at +-260 the two of them start 170 apart and could walk 90 units before the
# bound stopped them, the camera never left the middle of a room that is a
# screen wide plus its travel, and the backdrop never scrolled. Half a screen
# of travel each way is what a stage this size wants.
TRAVEL = 900                       # camera travel each way ([Camera] bound)
# A BG element's start x is measured from the CENTRE of the screen, not from its
# left edge - tools/stages_hd.py relies on that when it parks its back wall at
# 960 - 2057 + 0.35 * 3136 = 0. This plate was 1920 + 2*260 wide and started at
# -260, so it was drawn from x = 960 - 260 = 700: the left third of the screen
# was black, and panning left turned the whole view black. It is now a screen
# wide, plus the camera's travel each side, plus the same overscan the HD stages
# carry, and centred, so the room fills the frame at every camera position.
OVERSCAN = 96
W = SCREEN[0] + 2 * (TRAVEL + OVERSCAN)   # 2632: the painted backdrop
START_X = -(W // 2)                       # -1316: centred on screen x = 960
FLOOR_Y = 900                      # zoffset
PREVIEW = (1215, 398)              # the card art every stage bakes

GOLD = (206, 168, 86)
GOLD_DIM = (120, 96, 46)
INK = (10, 12, 13)



# The stage card's own gold rule, the same one the HD stage painters bake, so the
# training room's card is not the one bare tile in the stage wall.
CARD_GOLD = (240, 196, 88, 255)
CARD_DARK = (10, 14, 22, 255)


def frame_card(img):
    """A gold rule around a stage card, with a dark line outside it."""
    out = img.convert("RGBA").copy()
    draw = ImageDraw.Draw(out)
    w, h = out.size
    draw.rectangle([0, 0, w - 1, h - 1], outline=CARD_DARK, width=2)
    draw.rectangle([2, 2, w - 3, h - 3], outline=CARD_GOLD, width=4)
    return out

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

    # --- nothing lettered on the wall -------------------------------------
    # There used to be a painted "TRAINING ROOM" sign here. A stage is scenery:
    # the mode, the stage name and the rest of the status are the engine's to
    # draw, in the fighter HUD and the motif, and baking a caption into the art
    # duplicates them and dates the room. The wall is left as panelled concrete.

    # --- two work lights on the wall --------------------------------------
    # Below the HUD too, so they light the wall instead of the health bars.
    light_y = 230
    for x in (W // 2 - 470, W // 2 + 470):
        img = Image.alpha_composite(img, art.radial_light(
            (W, SCREEN[1]), (x, light_y + 60), 330, (255, 210, 130), peak=64))
    # alpha_composite returns a new image, so the draw handle above is stale
    # from here on: the fixtures and the centre line have to go on the new one
    # or they are painted into a picture nothing reads
    d = ImageDraw.Draw(img)
    for x in (W // 2 - 470, W // 2 + 470):
        d.rectangle([x - 46, light_y, x + 46, light_y + 48], fill=(22, 24, 24),
                    outline=(58, 54, 44), width=3)
        d.ellipse([x - 34, light_y + 22, x + 34, light_y + 78],
                  fill=(255, 226, 158, 210))

    # chalk centre line the fighters square up on
    cx = W // 2
    for k in range(0, SCREEN[1] - FLOOR_Y, 22):
        d.line([(cx, FLOOR_Y + k), (cx, FLOOR_Y + k + 12)],
               fill=(180, 180, 172, 90), width=4)

    img = art.vignette(img, strength=0.5)
    return art.grain(img, amount=4, seed=11)


def preview(img):
    """The card art: the on-screen window, cropped to the card's 3:1 strip."""
    x0 = (W - SCREEN[0]) // 2
    view = img.crop((x0, 0, x0 + SCREEN[0], SCREEN[1]))
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
zoomout = 0.75
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
        {"group": 9000, "number": 1, "image": frame_card(preview(img)), "axis": (0, 0)},
    ]
    with open(STAGE + ".sff", "wb") as f:
        f.write(sff.write_sff(sprites))
    with open(STAGE + ".def", "w", encoding="utf-8", newline="\n") as f:
        f.write(DEF.format(travel=TRAVEL, floor=FLOOR_Y, start=START_X))

    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    img.save(os.path.join(ROOT, "artifacts", "training_room.png"))
    print("  training room: %dx%d backdrop, start %d, preview %dx%d, "
          "localcoord 1920x1080" % (img.width, img.height, START_X,
                                    PREVIEW[0], PREVIEW[1]))


if __name__ == "__main__":
    main()
