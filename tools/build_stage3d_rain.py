#!/usr/bin/env python3
"""Paint and anchor the three floating-world stages: cards and weather.

The upstream Third Heights pack (SuperFromND, MIT) ships one island in two
renders, so the three stages are told apart by what happens around the island
rather than by the mesh: this tool paints each stage's card and the weather its
def then draws over the model.

  Third Heights        bright day, cloud haze drifting across the top, spray
                       rising off the water
  Third Heights        the same island at night in the outline render, under a
   Outline             violet wash with cold motes climbing through it and mist
                       crawling along the water
  Third Heights        the storm: two layers of painted rain, one behind the
   Rainfall            fighters and one in front, a slate wash and driving mist

Every sheet also carries the pack's 240x100 portrait, anchored on its centre.
That anchor is why these cards drew before as a quarter of a picture in the
corner: the pack puts the axis on the top-left, and the motif places a card's
axis point in the middle of the frame. The stage's own portraitscale lands the
240-wide portrait at 1215 wide, the width every other card in this roster uses.

Background sprites are painted at the stages' localcoord (1280x720), because a
stage BG layer is drawn in localcoord units, and each is seamless in whichever
direction its layer tiles.

Run:  python3 tools/build_stage3d_rain.py
"""
import os
import random
import sys

from PIL import Image, ImageDraw, ImageEnhance

import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGES = os.path.join(ROOT, "stages")
BASE = os.path.join(STAGES, "stage3d.sff")
SIZE = (240, 100)          # the pack's portrait
FRAME = (1280, 720)        # the stages' localcoord: BG sprites draw 1:1
CARDS = ("stage3d", "stage3d_outline", "stage3d_rain")


# ----------------------------------------------------------------- portraits --
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


def grade(pic, warm=False, night=False):
    """One island, three hours of the day."""
    r, g, b, a = pic.convert("RGBA").split()
    if night:
        r = r.point(lambda v: int(v * 0.42))
        g = g.point(lambda v: int(v * 0.38))
        b = b.point(lambda v: min(255, int(v * 0.92)))
        pic = ImageEnhance.Brightness(Image.merge("RGBA", (r, g, b, a))).enhance(0.9)
    elif warm:
        r = r.point(lambda v: min(255, int(v * 1.12)))
        g = g.point(lambda v: int(v * 1.02))
        b = b.point(lambda v: int(v * 0.86))
        pic = Image.merge("RGBA", (r, g, b, a))
        pic = ImageEnhance.Color(pic).enhance(1.22)
        pic = ImageEnhance.Brightness(pic).enhance(1.06)
    return pic


def rain_card(pic):
    big = pic.resize((SIZE[0] * 2, SIZE[1] * 2), Image.LANCZOS)
    r, g, b, a = big.split()
    # cold grade: pull the reds down, push the blue up - dusk turning to rain
    r = r.point(lambda v: int(v * 0.62))
    g = g.point(lambda v: int(v * 0.82))
    b = b.point(lambda v: min(255, int(v * 1.18)))
    graded = ImageEnhance.Brightness(Image.merge("RGBA", (r, g, b, a))).enhance(0.82)
    return draw_rain(graded, 150, (16, 44), (-11, -5), (205, 226, 244), (40, 110)).resize(
        SIZE, Image.LANCZOS)


# ------------------------------------------------------------------ weather --
def draw_rain(img, count, length, slant, colour, alpha, seed=20261107):
    """Streaks over a picture, wrapped so the sheet tiles without a seam.

    A negative slant leans a streak's foot to the left of its head, which is the way
    weather crosses this stage: the wind runs left along the terrace, so the drops
    and the sheets that carry them have to lean and travel the same way.
    """
    draw = ImageDraw.Draw(img)
    rng = random.Random(seed)
    w, h = img.size
    for _ in range(count):
        x = rng.uniform(-60, w + 20)
        y = rng.uniform(-80, h)
        ln = rng.uniform(*length)
        lean = rng.uniform(*slant)
        fill = tuple(colour) + (rng.randint(*alpha),)
        for dx in (-w, 0, w):
            for dy in (-h, 0, h):
                draw.line([(x + dx, y + dy), (x + dx + lean, y + dy + ln)],
                          fill=fill, width=1)
    return img


def rain_sheet(count, length, slant, colour, alpha, seed):
    img = Image.new("RGBA", FRAME, (0, 0, 0, 0))
    return draw_rain(img, count, length, slant, colour, alpha, seed)


def motes(count, colour, seed):
    """Cold lights that climb through the outline stage, seamless both ways."""
    img = Image.new("RGBA", FRAME, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rng = random.Random(seed)
    w, h = img.size
    for _ in range(count):
        x = rng.uniform(0, w)
        y = rng.uniform(0, h)
        rad = rng.uniform(1.4, 3.4)
        peak = rng.randint(70, 180)
        for dx in (-w, 0, w):
            for dy in (-h, 0, h):
                for step, a in ((rad * 2.6, peak // 6), (rad * 1.5, peak // 3),
                                (rad, peak)):
                    draw.ellipse([x + dx - step, y + dy - step,
                                  x + dx + step, y + dy + step],
                                 fill=tuple(colour) + (a,))
    return img


def band(y0, y1, colour, peak, wobble=0):
    """A soft horizontal band: alpha depends on y only, so it tiles sideways."""
    img = Image.new("RGBA", FRAME, (0, 0, 0, 0))
    px = img.load()
    h = FRAME[1]
    for y in range(h):
        if y < y0 or y > y1:
            continue
        # a raised-cosine ramp across the band, so no edge is a hard line
        span = max(1.0, (y1 - y0) / 2.0)
        mid = (y0 + y1) / 2.0
        t = abs(y - mid) / span
        a = int(peak * max(0.0, 1.0 - t * t))
        if wobble:
            a = int(a * (0.75 + 0.25 * ((y * wobble) % 7) / 7.0))
        for x in range(FRAME[0]):
            px[x, y] = tuple(colour) + (a,)
    return img


def blank():
    return Image.new("RGBA", FRAME, (0, 0, 0, 0))


def flash(strength, bolt_seed=None):
    """A flash across the sky, with a bolt tearing down out of it when asked.

    Drawn with trans = add, so the sky lifts rather than being painted over.
    """
    img = Image.new("RGBA", FRAME, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for y in range(FRAME[1]):
        t = y / float(FRAME[1])
        a = int(strength * max(0.0, 1.0 - t ** 1.5))
        if a:
            draw.line([(0, y), (FRAME[0], y)], fill=(206, 224, 255, a))
    if bolt_seed is not None:
        rng = random.Random(bolt_seed)
        x, y = rng.uniform(300, 980), -20.0
        path = [(x, y)]
        while y < FRAME[1] * 0.7:
            y += rng.uniform(45, 95)
            x += rng.uniform(-50, 50)
            path.append((x, y))
        for width, alpha in ((16, 26), (7, 70), (2, 235)):
            draw.line(path, fill=(228, 238, 255, alpha), width=width, joint="curve")
        for _ in range(2):                       # short forks off the channel
            bx, by = path[rng.randrange(1, max(2, len(path) - 2))]
            fork = [(bx, by)]
            for _step in range(3):
                bx += rng.uniform(-90, 90)
                by += rng.uniform(30, 70)
                fork.append((bx, by))
            draw.line(fork, fill=(214, 228, 255, 120), width=2)
    return img


def wash(colour, alpha):
    return Image.new("RGBA", FRAME, tuple(colour) + (alpha,))


def storm_sky(seed=4403):
    """A storm sky that is drawn *over* the 3D model with trans = add.

    On a machine where the engine cannot render the model - the model path is
    skipped outright when the renderer has no model support, which is what some
    older and AMD drivers do - a 3D stage draws as a black field under its
    painted weather. This sprite is the answer to that: additive, so a black
    frame is lifted to a slate storm sky with cloud banks and a hazy moon, while
    an island that *does* render is brightened by the same amount instead of
    being covered up. Nothing opaque can be used here, because a zero-layer BG
    is drawn after the model and would hide it.
    """
    img = Image.new("RGBA", FRAME, (0, 0, 0, 0))
    px = img.load()
    h = FRAME[1]
    # what the sky adds to a black frame at each height: brighter overhead,
    # dimmer at the waterline so the island keeps its contrast
    stops = ((0, (78, 104, 148), 150), (300, (64, 86, 126), 132),
             (520, (48, 64, 96), 104), (h - 1, (30, 40, 62), 70))
    for y in range(h):
        for i in range(len(stops) - 1):
            y0, c0, a0 = stops[i]
            y1, c1, a1 = stops[i + 1]
            if y0 <= y <= y1:
                t = (y - y0) / float(max(1, y1 - y0))
                col = tuple(int(c0[k] + (c1[k] - c0[k]) * t) for k in range(3))
                alpha = int(a0 + (a1 - a0) * t)
                for x in range(FRAME[0]):
                    px[x, y] = col + (alpha,)
                break

    rng = random.Random(seed)
    w, hh = FRAME
    # moon glow, high and behind the cloud line
    glow = Image.new("RGBA", FRAME, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    mx, my = 940, 132
    for rad, a in ((190, 10), (120, 14), (70, 20), (34, 34), (16, 60)):
        for dx in (-w, 0, w):
            gd.ellipse([mx + dx - rad, my - rad, mx + dx + rad, my + rad],
                       fill=(176, 190, 222, a))
    # cloud banks: flat, soft, wrapped sideways so the layer tiles without a seam
    clouds = Image.new("RGBA", FRAME, (0, 0, 0, 0))
    cd = ImageDraw.Draw(clouds)
    for band in ((40, 150, 70), (120, 240, 54), (210, 330, 40)):
        y0, y1, peak = band
        for _ in range(9):
            cx = rng.uniform(0, w)
            cy = rng.uniform(y0, y1)
            rw = rng.uniform(120, 320)
            rh = rng.uniform(18, 46)
            for dx in (-w, 0, w):
                cd.ellipse([cx + dx - rw, cy - rh, cx + dx + rw, cy + rh],
                           fill=(126, 146, 178, rng.randint(peak // 2, peak)))
    img = Image.alpha_composite(img, clouds)
    img = Image.alpha_composite(img, glow)
    return img


# --------------------------------------------------------------------- build --
def sprites_for(name):
    """The weather layers a stage's def asks for, by sprite number."""
    if name == "stage3d":
        return [
            {"group": 1, "number": 0, "image": band(0, 300, (255, 252, 246), 46),
             "axis": (0, 0)},
            {"group": 1, "number": 1, "image": band(430, 700, (238, 248, 255), 60),
             "axis": (0, 0)},
        ]
    if name == "stage3d_outline":
        return [
            {"group": 1, "number": 0, "image": motes(150, (196, 176, 255), 7101),
             "axis": (0, 0)},
            {"group": 1, "number": 1, "image": band(380, 690, (150, 120, 220), 70),
             "axis": (0, 0)},
            {"group": 1, "number": 2, "image": wash((34, 18, 62), 92), "axis": (0, 0)},
        ]
    return [
        {"group": 1, "number": 0,
         "image": rain_sheet(420, (26, 60), (-5, -2), (176, 202, 232), (28, 70), 4401),
         "axis": (0, 0)},
        {"group": 1, "number": 1,
         "image": rain_sheet(180, (44, 96), (-9, -4), (214, 232, 250), (60, 130), 4402),
         "axis": (0, 0)},
        {"group": 1, "number": 2, "image": wash((24, 32, 52), 64), "axis": (0, 0)},
        {"group": 1, "number": 3, "image": band(420, 700, (172, 196, 220), 66),
         "axis": (0, 0)},
        # the sky under the storm, drawn additively over the 3D model
        {"group": 1, "number": 4, "image": storm_sky(), "axis": (0, 0)},
        # the lightning sheet: a clear frame, the strike, and its afterglow
        {"group": 2, "number": 0, "image": blank(), "axis": (0, 0)},
        {"group": 2, "number": 1, "image": flash(88, 8801), "axis": (0, 0)},
        {"group": 2, "number": 2, "image": flash(30), "axis": (0, 0)},
    ]


def write_sheet(path, picture, axis, weather=()):
    out = [{"group": 9000, "number": 1, "image": picture, "axis": axis},
           {"group": 9000, "number": 0, "image": picture, "axis": axis}]
    out.extend(weather)
    with open(path, "wb") as handle:
        handle.write(sff.write_sff(out))


def main(argv=()):
    base_pic, _base_sp = preview(BASE)
    # optional filter, so one stage's sheet can be repainted without re-grading
    # the other two cards (grading is applied to the card already in the file)
    only = set(argv)
    for name in CARDS:
        if only and name not in only:
            continue
        path = os.path.join(STAGES, name + ".sff")
        # The card already in the sheet is the approved one: re-grading it on
        # every run would drift the colour a little each time. Grading only
        # happens when the sheet is new, or when REGRADE=1 asks for it.
        if os.path.isfile(path) and not os.environ.get("REGRADE"):
            picture, sp = preview(path)
        else:
            picture, sp = preview(BASE)
            if name == "stage3d":
                picture = grade(picture, warm=True)
            elif name == "stage3d_outline":
                picture = grade(picture, night=True)
            else:
                picture = rain_card(picture)
        axis = center_axis(sp)
        weather = sprites_for(name)
        write_sheet(path, picture, axis, weather)
        print("  stages/%s.sff: %dx%d card at %d,%d + %d weather sprite(s)"
              % (name, picture.width, picture.height, axis[0], axis[1], len(weather)))


if __name__ == "__main__":
    main(sys.argv[1:])
