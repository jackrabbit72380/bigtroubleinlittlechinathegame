"""Turn high-resolution backdrop art into native 1920x1080 (HD) Ikemen stages.

The procedural painters in tools/build_stages.py draw at arcade resolution
(localcoord 320x240), which the engine has to stretch to fill a 1080p window.
This script is the HD path: give it real backdrop art and it writes a stage that
is authored at 1920x1080, so a 1080p display shows real pixels instead of an
upscaled 240-line image.

Layout - one folder per stage under art_src/:

    art_src/
      lopans_throne/
        backdrop.png      required, 8192x1080 is ideal, anything from 1920x1080 up
        foreground.png    optional, same size, drawn in front of the fighters
        stage.txt         optional, "name = Lo Pan's Throne"

The backdrop is cover-fitted to the stage canvas: scaled to fill without
distorting, then centre-cropped, so 16:9 art drops in untouched and taller art
loses a little top and bottom.

Geometry is imported from tools/stages_hd.py rather than copied, so art that
comes in this way lands in exactly the arena the shipped stages use:

    stage canvas      8192 x 1080  (two 4096-wide halves)
    camera            boundleft/right +/-3136
    players           leftbound/rightbound +/-4028, 68 px inside the edge
    floor             zoffset 900  (the art's floor line sits at row 900)
    localcoord        1920, 1080

It used to carry its own smaller set of numbers (5600 x 1080, camera +/-1788,
players +/-2368), which meant dropping art in here quietly produced a narrower
arena than the procedural stages - and a 5600-wide sprite, past the 4096 texture
limit that makes the renderer drop the device.

The localcoord height has to equal the canvas height. Ikemen derives the
vertical framing from it (src/camera.go):

    cutlow = (localcoord[1] - zoffset) - localcoord[1] * 0.05

With localcoord 720 and zoffset 900 that resolves negative, the floor lands
past the bottom of the coordinate space and the backdrop is framed wrong.

Wide layers are cut into columns of at most MAX_TEX pixels, one sprite and one
[BG] block each, for the same reason stages_hd.py does it: an 8192-wide texture
is refused by the driver.

tools/build_stages.py skips any stage that has an art_src/ folder, so an HD
backdrop replaces the procedural one without editing code.

Run:  python3 tools/build_hd_stage.py        (also part of tools/build_all.py)
"""

from __future__ import annotations

import os
import sys

from PIL import Image, ImageChops, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sff
import stages_hd as hd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART_SRC = os.path.join(ROOT, "art_src")

# HD geometry, owned by the painter that produces the shipped stages.
SCROLL = hd.SCROLL                            # 3136: camera travel
LOCAL_W, LOCAL_H = hd.LOCAL_W, hd.LOCAL_H     # 1920 x 1080
H = hd.H                                      # 1080 painted height
W = hd.W                                      # 8192: full stage canvas
CX = hd.CX                                    # 4096: canvas centre
START_X = hd.START_X                          # -4096: canvas left edge in stage x
ZOFFSET = hd.FLOOR_Y                          # 900: ground line
PLAYER_BOUND = hd.PLAYER_BOUND                # 4028
SCREEN_MARGIN = hd.SCREEN_MARGIN              # 68
MAX_TEX = hd.MAX_TEX                          # 4096: widest single sprite
split_wide = hd.split_wide
PREVIEW_W, PREVIEW_H = hd.PREVIEW_W, hd.PREVIEW_H

# Depth layers. The painted canvas is 8192 wide for a 3136-travel camera, so a
# parallax plate only has to be LOCAL_W + delta*2*SCROLL across, and the floor
# lip only needs the strip the fighters stand in.
SKY_DELTA = 0.35
SKY_W = int(LOCAL_W + SKY_DELTA * 2 * SCROLL)   # 4115 px, 4096 + 19 once split
LIP_TOP = ZOFFSET                                # the lip starts at the ground line
# Cutting the lip 40px above the ground line pasted the wall/floor junction
# (luma 8-21) in front of the fighters' feet, which stand on a lit floor
# plate: their feet vanished into a dark strip and they read as floating.
LIP_H = H - LIP_TOP                             # 180 px
LIP_FADE = 70                                   # soft edge, so no hard cut
# Layers are written at full size and drawn 1:1. They used to be painted at
# half size and blown back up with `scale = 2,2` in the .def, but that
# scale is not applied to BG sprites: the floor lip went down at 2800px
# wide from x=-2800, so it covered only the LEFT half of the stage and the
# floor beyond it was drawn bare - the hard black step seen on every map.
HALF = 1


def sky_layer(bg):
    """Far parallax plate: softened, dimmed centre crop of the backdrop.

    It is blurred and pushed toward blue so it reads as distance rather than as
    a second copy of the wall the fighters are standing against.
    """
    x0 = (W - SKY_W) // 2
    sky = bg.crop((x0, 0, x0 + SKY_W, H))
    sky = sky.resize((max(1, SKY_W // HALF), max(1, H // HALF)), Image.BILINEAR)
    sky = sky.filter(ImageFilter.GaussianBlur(1.5))
    r, g, b, a = sky.split()
    r = r.point(lambda v: int(v * 0.68))
    g = g.point(lambda v: int(v * 0.72))
    b = b.point(lambda v: int(v * 0.80))
    return Image.merge("RGBA", (r, g, b, a))


def lip_layer(bg):
    """The floor's front lip, redrawn in front of the fighters.

    Same pixels as the backdrop, at the same place, but on layerno 1 with a
    gradient top edge: the feet sink into the floor instead of being pasted on
    top of it, which is the depth cue the arcade stages rely on.
    """
    lip = bg.crop((0, LIP_TOP, W, H)).convert("RGBA")
    lip = lip.resize((max(1, W // HALF), max(1, LIP_H // HALF)), Image.BILINEAR)
    w, h = lip.size
    grad = Image.new("L", (w, h), 255)
    fade = max(1, int(round((LIP_FADE * h) / float(LIP_H))))
    for y in range(fade):
        grad.paste(int(255 * (y + 1) / float(fade)), (0, y, w, y + 1))
    lip.putalpha(ImageChops.multiply(lip.getchannel("A"), grad))
    return lip


BG_BLOCK = """
[BG {name}]
type = normal
spriteno = {group},{number}
layerno = {layerno}
start = {start},{y}
delta = {delta}
scale = 1,1
trans = none
mask = {mask}
tile = 0,0
"""


def columns(sprites, group, img):
    """Cut `img` at MAX_TEX, one sprite per column, and return the offsets.

    A sprite wider than the driver's texture limit is not drawn at all - the
    device is dropped mid-match - so no layer here is ever one big image.
    """
    offsets = []
    for number, (offset, piece) in enumerate(split_wide(img)):
        sprites.append({"group": group, "number": number,
                        "image": piece, "axis": (0, 0)})
        offsets.append(offset)
    return offsets


def blocks(layer, group, offsets, start_x, y, delta, layerno, mask):
    """One [BG] block per column, extra columns labelled layer 1, layer 2."""
    out = []
    for number, offset in enumerate(offsets):
        name = layer if number == 0 else f"{layer} {number}"
        out.append(BG_BLOCK.format(
            name=name, group=group, number=number,
            start=start_x + offset, y=y, delta=delta,
            layerno=layerno, mask=mask))
    return "".join(out)


DEF_TEMPLATE = """;---------------------------------------------------------------------------
; {name}
; Part of Big Trouble in Little China: The Game (Ikemen GO)
; HD stage: authored at 1920x1080 from art_src/{sid}/.
; Generated by tools/build_hd_stage.py.
;---------------------------------------------------------------------------
[Info]
name = "{name}"
displayname = "{display}"
versiondate = 10,28,2026
mugenversion = 1.0
author = "Big Trouble in Little China: The Game"

[Camera]
startx = 0
starty = 0
boundleft = -{scroll}
boundright = {scroll}
boundhigh = {boundhigh}
boundlow = 0
verticalfollow = .2
floortension = 0
tension = 60
overdrawhigh = 0
overdrawlow = 0
cuthigh = {cuthigh}
cutlow = {cutlow}
zoomout = 1
zoomin = 1

[PlayerInfo]
p1startx = {startx}
p1starty = 0
p1facing = 1
p2startx = {p2startx}
p2starty = 0
p2facing = -1
leftbound = -{playerbound}
rightbound = {playerbound}

[Bound]
screenleft = {margin}
screenright = {margin}

[StageInfo]
zoffset = {zoffset}
autoturn = 1
resetBG = 1
localcoord = {localw}, {localh}
xscale = 1
yscale = 1

[Shadow]
intensity = 96
color = 0,0,0
yscale = -.1
fade.range = -400,-100

[Reflection]
intensity = 0

[Music]
bgmusic =
bgmvolume = 100

[BGdef]
spr = {sid}.sff
debugbg = 0

; IKEMEN GO select-screen preview
[Begin Action 9000]
9000,1, 0,0, -1

; far parallax: a softened crop of the backdrop, travelling at 0.35 speed
{sky_blocks}
; the backdrop itself, one block per column of the split
{bg_blocks}
; your foreground.png, in front of the fighters
{fg_blocks}
; foreground floor lip: the bottom of the backdrop drawn in FRONT of the
; fighters, so their feet sit in the floor rather than on top of it
{lip_blocks}"""


def cover_fit(path, size):
    """Scale to fill `size` without distortion, then centre-crop."""
    img = Image.open(path).convert("RGBA")
    tw, th = size
    ratio = max(tw / img.width, th / img.height)
    new = (max(tw, int(round(img.width * ratio))),
           max(th, int(round(img.height * ratio))))
    img = img.resize(new, Image.LANCZOS)
    left = (img.width - tw) // 2
    top = (img.height - th) // 2
    return img.crop((left, top, left + tw, top + th))


def build_stage(sid):
    src = os.path.join(ART_SRC, sid)
    backdrop = os.path.join(src, "backdrop.png")
    if not os.path.isfile(backdrop):
        print(f"  {sid}: no backdrop.png, skipped")
        return None

    src_w, src_h = Image.open(backdrop).size
    print(f"  {sid}: source {src_w}x{src_h} -> {W}x{H} stage canvas")
    bg = cover_fit(backdrop, (W, H))

    fg_path = os.path.join(src, "foreground.png")
    if os.path.isfile(fg_path):
        fg = cover_fit(fg_path, (W, H))
    else:
        fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # select / VS card: 1215x398 of art lands on the 324x106 window at the
    # motif's stage.portrait.scale of .4 (see tools/stages_hd.py build() for
    # the .4 * 1280/1920 arithmetic). A 320x240 thumb sat letterboxed in it.
    preview = bg.crop((CX - PREVIEW_W // 2, H // 2 - PREVIEW_H // 2,
                       CX + PREVIEW_W // 2, H // 2 + PREVIEW_H // 2))

    sprites = []
    bg_offsets = columns(sprites, 0, bg)
    fg_offsets = columns(sprites, 3, fg)
    sky_offsets = columns(sprites, 10, sky_layer(bg))
    lip_offsets = columns(sprites, 11, lip_layer(bg))
    sprites.append({"group": 9000, "number": 1, "image": preview,
                    "axis": (PREVIEW_W // 2, PREVIEW_H // 2)})

    data = sff.write_sff(sprites)
    sff_path = os.path.join(ROOT, "stages", f"{sid}.sff")
    with open(sff_path, "wb") as fh:
        fh.write(data)

    name = sid.replace("_", " ").title()
    display = name
    meta = os.path.join(src, "stage.txt")
    if os.path.isfile(meta):
        for line in open(meta, encoding="utf-8"):
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == "name":
                    name = display = v.strip()

    def_path = os.path.join(ROOT, "stages", f"{sid}.def")
    with open(def_path, "w", encoding="utf-8") as fh:
        fh.write(DEF_TEMPLATE.format(
            sid=sid, name=name, display=display,
            scroll=SCROLL, playerbound=PLAYER_BOUND, margin=SCREEN_MARGIN,
            zoffset=ZOFFSET, localw=LOCAL_W, localh=LOCAL_H,
            boundhigh=int(-25 * hd.SCALE), cuthigh=int(35 * hd.SCALE),
            cutlow=int(25 * hd.SCALE), startx=int(-70 * hd.SCALE),
            p2startx=int(70 * hd.SCALE),
            sky_blocks=blocks("sky", 10, sky_offsets, -(SKY_W // 2), 0,
                              f"{SKY_DELTA},1", 0, 1),
            bg_blocks=blocks("bg", 0, bg_offsets, START_X, 0, "1,1", 0, 0),
            fg_blocks=blocks("fg", 3, fg_offsets, START_X, 0, "1,1", 1, 1),
            lip_blocks=blocks("lip", 11, lip_offsets, START_X, LIP_TOP,
                              "1,1", 1, 1),
        ))
    print(f"  {sid}: wrote stages/{sid}.sff ({len(data) / 1024:.0f} KiB) and .def")
    return True


def hd_stages():
    if not os.path.isdir(ART_SRC):
        return []
    out = []
    for sid in sorted(os.listdir(ART_SRC)):
        if os.path.isfile(os.path.join(ART_SRC, sid, "backdrop.png")):
            out.append(sid)
    return out


def main():
    stages = hd_stages()
    if not stages:
        print("No HD backdrops found (art_src/<stage>/backdrop.png); "
              "the procedural stages are used for every arena")
        return 0
    print("Building HD stages")
    for sid in stages:
        build_stage(sid)
    print(f"{len(stages)} HD stage(s) built at localcoord {LOCAL_W}x{LOCAL_H}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
