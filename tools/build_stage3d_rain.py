#!/usr/bin/env python3
"""Paint and anchor the select-screen cards of the three floating-world stages.

The upstream Third Heights pack (SuperFromND, MIT) ships one island in two
renders, so there is no third scene to license. Rain's stage is the same model
framed differently; this tool paints its card from stage3d's own preview - the
same shot graded cold with rain streaked across it.

All three sheets carry the pack's 240x100 portrait, and that is the right art at
the right size: a 1280x720 stage's portrait draws 1.5x larger than a 1920x1080
one, and the stage's own portraitscale takes it to 1215 wide, the width every
other card in this roster uses. What was wrong was the anchor. The pack puts the
portrait's axis on its top-left corner, and the motif places a card's axis point
in the middle of the frame, so the screen drew the bottom-right quarter of the
picture inside the card and left the rest of it empty. The cards are anchored at
their centre here, the way every other stage's 1215x398 card already is.

Both indices are written, so a motif asking for 9000,0 or 9000,1 gets the card.

Run:  python3 tools/build_stage3d_rain.py
"""
import os
import random

from PIL import Image, ImageDraw, ImageEnhance

import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGES = os.path.join(ROOT, "stages")
BASE = os.path.join(STAGES, "stage3d.sff")
SIZE = (240, 100)
# every sheet whose portrait this tool owns: rain's painted card, and the two
# pack cards whose anchor it corrects
CARDS = ("stage3d", "stage3d_outline", "stage3d_rain")


def preview(path):
    """The sheet's 9000,1 picture, decoded, with its record."""
    data, sprites, palettes = sff.read_sff(path)
    for sp in sprites:
        if (sp["group"], sp["number"]) == (9000, 1):
            return sff.decode_sprite(data, sp, palettes).convert("RGBA"), sp
    raise SystemExit("%s has no 9000,1 preview to use" % os.path.basename(path))


def center_axis(sp):
    """The anchor a card is drawn from: the middle of its picture."""
    return (sp["w"] // 2, sp["h"] // 2)


def write_card(path, picture, axis):
    with open(path, "wb") as handle:
        handle.write(sff.write_sff([
            {"group": 9000, "number": 1, "image": picture, "axis": axis},
            {"group": 9000, "number": 0, "image": picture, "axis": axis},
        ]))


def rain_card(pic):
    big = pic.resize((SIZE[0] * 2, SIZE[1] * 2), Image.LANCZOS)
    r, g, b, a = big.split()
    # cold grade: pull the reds down, push the blue up - dusk turning to rain
    r = r.point(lambda v: int(v * 0.62))
    g = g.point(lambda v: int(v * 0.82))
    b = b.point(lambda v: min(255, int(v * 1.18)))
    graded = ImageEnhance.Brightness(Image.merge("RGBA", (r, g, b, a))).enhance(0.82)

    rain = Image.new("RGBA", graded.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(rain)
    rng = random.Random(20261107)
    for _ in range(150):
        x = rng.uniform(-30, graded.size[0] + 10)
        y = rng.uniform(-40, graded.size[1])
        length = rng.uniform(16, 44)
        slant = rng.uniform(5, 11)
        draw.line([(x, y), (x + slant, y + length)],
                  fill=(205, 226, 244, rng.randint(40, 110)), width=1)

    return Image.alpha_composite(graded, rain).resize(SIZE, Image.LANCZOS)


def main():
    base_pic, _base_sp = preview(BASE)
    for name in CARDS:
        path = os.path.join(STAGES, name + ".sff")
        picture, sp = preview(path)
        if name == "stage3d_rain":
            picture = rain_card(base_pic)
        axis = center_axis(sp)
        write_card(path, picture, axis)
        print("  stages/%s.sff: %dx%d card anchored at %d,%d"
              % (name, picture.width, picture.height, axis[0], axis[1]))


if __name__ == "__main__":
    main()
