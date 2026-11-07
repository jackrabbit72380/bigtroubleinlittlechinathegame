#!/usr/bin/env python3
"""Paint rain's select-screen card for the third floating-world stage.

The upstream Third Heights pack (SuperFromND, MIT) ships one island in two
renders, so there is no third scene to license. Rain's stage is the same model
framed differently; this tool paints its card from stage3d's own preview - the
same shot graded cold with rain streaked across it - at the 240x100 size a
1280x720 stage's card draws at.
"""
import os
import random

from PIL import Image, ImageDraw, ImageEnhance

import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "stages", "stage3d.sff")
OUT = os.path.join(ROOT, "stages", "stage3d_rain.sff")
SIZE = (240, 100)


def base_picture():
    data, sprites, palettes = sff.read_sff(BASE)
    for sp in sprites:
        if (sp["group"], sp["number"]) == (9000, 1):
            return sff.decode_sprite(data, sp, palettes).convert("RGBA")
    raise SystemExit("stage3d.sff has no 9000,1 preview to paint from")


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
    card = rain_card(base_picture())
    with open(OUT, "wb") as f:
        f.write(sff.write_sff([{"group": 9000, "number": 1, "image": card,
                                "axis": (0, 0)}]))
    print("  stages/stage3d_rain.sff: rain's %dx%d card" % SIZE)


if __name__ == "__main__":
    main()
