"""Paint the game's own title logo into the screenpack SFF.

The title screen draws its logo from system.sff sprites 0,0-0,3: a bright layer
plus an additive shadow layer for each of two elements. Those slots are
replaced here with the project's wordmark - heavy arched brush capitals reading
BIG TROUBLE, with "in Little China" set small beneath - so the screenpack's
positioning, bobbing and fades keep working untouched.

Run:  python3 tools/build_title.py
"""

from __future__ import annotations

import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYSTEM_SFF = os.path.join(ROOT, "data", "ikemen1", "system.sff")

# The four logo slots are all this size with the axis at their centre; keeping
# it means nothing in system.def has to change.
CANVAS = (699, 257)

RED = (178, 32, 28)
RED_DEEP = (104, 12, 12)
RED_HI = (222, 74, 54)
RED_SH = (128, 16, 14)


def cap_height(size):
    font = art.font(size)
    box = font.getbbox("H")
    return box[3] - box[1]


def glyph_mask(ch, size, weight=0.10):
    """One capital, white on transparent, fattened to brush weight.

    The display face on its own is a thin sans; the reference lettering is
    blocky, so every glyph is drawn with a heavy stroke to thicken its stems
    until the counters close up the way painted caps do.
    """
    font = art.font(size)
    stroke = max(1, int(round(size * weight)))
    box = font.getbbox(ch, stroke_width=stroke)
    pad = stroke + max(4, size // 10)
    img = Image.new("L", (box[2] - box[0] + pad * 2, box[3] - box[1] + pad * 2), 0)
    ImageDraw.Draw(img).text((pad - box[0], pad - box[1]), ch, font=font, fill=255,
                             stroke_width=stroke, stroke_fill=255)
    return img


def arc_line(text, size, cx, apex_y, radius, seed, jitter=1.0, tracking=0.95,
             weight=0.10):
    """Letters along an arc whose tops sit on ``apex_y`` at the centre.

    The arc's centre is directly below the apex, so a point at angle ``a`` is at
    (cx + R sin a, apex_y + R (1 - cos a)): the ends of the line drop by the
    sagitta, which is what gives the word its bow.
    """
    mask = Image.new("L", CANVAS, 0)
    rnd = random.Random(seed)
    font = art.font(size)
    chap = cap_height(size)
    widths = [max(1.0, font.getlength(c)) * tracking for c in text]
    total = sum(widths)
    # the string has to fit the arc without letters colliding, so the half
    # angle follows from the string's own width: arc length is 2 R theta
    half = (total * 1.02 / 2.0) / radius
    pos = 0.0
    for ch, adv in zip(text, widths):
        if ch != " ":
            frac = (pos + adv * 0.5) / total
            a = -half + 2.0 * half * frac
            gx = cx + radius * math.sin(a)
            gy = apex_y + radius * (1.0 - math.cos(a)) + chap * 0.5
            g = glyph_mask(ch, size, weight)
            ang = -math.degrees(a) + rnd.uniform(-2.5, 2.5) * jitter
            g = g.rotate(ang, resample=Image.BICUBIC, expand=True)
            gx += rnd.uniform(-1.5, 1.5) * jitter
            gy += rnd.uniform(-1.5, 1.5) * jitter
            mask.paste(g, (int(round(gx - g.width / 2)),
                           int(round(gy - g.height / 2))), g)
        pos += adv
    return mask


def flat_line(text, size, cx, cy, seed=0, jitter=0.0, tracking=1.0, weight=0.06):
    """A straight line of type, centred on (cx, cy)."""
    mask = Image.new("L", CANVAS, 0)
    rnd = random.Random(seed)
    font = art.font(size)
    stroke = max(1, int(round(size * weight)))
    widths = [max(1.0, font.getlength(c)) * tracking for c in text]
    total = sum(widths)
    pos = cx - total / 2.0
    for ch, adv in zip(text, widths):
        if ch != " ":
            box = font.getbbox(ch, stroke_width=stroke)
            g = Image.new("L", (box[2] - box[0] + 10, box[3] - box[1] + 10), 0)
            ImageDraw.Draw(g).text((5 - box[0], 5 - box[1]), ch, font=font, fill=255,
                                   stroke_width=stroke, stroke_fill=255)
            if jitter:
                g = g.rotate(rnd.uniform(-1.2, 1.2) * jitter,
                             resample=Image.BICUBIC, expand=True)
            mask.paste(g, (int(round(pos + box[0] - 5 + (adv - (box[2] - box[0])) / 2)),
                           int(round(cy - g.height / 2
                                     + rnd.uniform(-1.0, 1.0) * jitter))), g)
        pos += adv
    return mask


def brush(mask, seed=11):
    """Soften the type into paint: blended edges plus a little spatter.

    Earlier versions multiplied the mask by hard noise, which punched holes
    through thin strokes and left them looking like outlines. The edges are
    eased here instead, and only stray dots are added outside the letterform.
    """
    rnd = random.Random(seed)
    eased = mask.filter(ImageFilter.GaussianBlur(1.1)).point(
        lambda v: 255 if v > 96 else v)
    layer = Image.new("L", CANVAS, 0)
    d = ImageDraw.Draw(layer)
    edge = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(9)), mask)
    for _ in range(180):
        x, y = rnd.randrange(CANVAS[0]), rnd.randrange(CANVAS[1])
        if edge.getpixel((x, y)) > 80:
            r = rnd.choice((1, 1, 2))
            d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    return ImageChops.lighter(eased, layer)


def paint(mask):
    """Give a letterform mask the painted-red look, with a dark rim."""
    img = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    img.alpha_composite(art.outline(mask, RED_DEEP, thickness=2))

    body = Image.new("RGBA", CANVAS, RED + (255,))
    body.putalpha(mask)
    img.alpha_composite(body)

    # a few darker brush streaks inside the strokes, clipped to the letterform
    rnd = random.Random(21)
    streaks = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    sd = ImageDraw.Draw(streaks)
    for _ in range(90):
        x, y = rnd.randrange(CANVAS[0]), rnd.randrange(CANVAS[1])
        if mask.getpixel((x, y)) < 128:
            continue
        ln = rnd.randint(6, 26)
        ang = rnd.uniform(-0.5, 0.5)
        sd.line([(x, y), (x + math.cos(ang) * ln, y + math.sin(ang) * ln)],
                fill=RED_SH + (rnd.randint(30, 80),), width=rnd.randint(1, 2))
    img.alpha_composite(streaks)

    # a warm highlight riding the upper edge of each stroke
    hi = ImageChops.subtract(mask, ImageChops.offset(mask, 1, 4))
    hi_layer = Image.new("RGBA", CANVAS, RED_HI + (255,))
    hi_layer.putalpha(ImageChops.multiply(hi, mask).point(lambda v: int(v * 0.5)))
    img.alpha_composite(hi_layer)

    # slight vertical shading so the paint has weight
    grad = art.vgrad(CANVAS, [(0, (40, 0, 0)), (CANVAS[1], (0, 0, 0))])
    shade = grad.copy()
    shade.putalpha(mask.point(lambda v: int(v * 0.18)))
    img.alpha_composite(shade)
    return img.filter(ImageFilter.GaussianBlur(0.5))


def wordmark():
    """The finished logo on the 699x257 screenpack canvas."""
    W, _H = CANVAS
    cx = W / 2.0
    big = arc_line("BIG TROUBLE", 84, cx, 26, 500, seed=4, jitter=1.0,
                   tracking=1.0, weight=0.045)
    small = flat_line("in Little China", 40, cx, 206, seed=9, jitter=0.5,
                      tracking=1.02, weight=0.03)
    mask = ImageChops.lighter(brush(big, seed=4), brush(small, seed=9))
    return paint(mask)


def build():
    if not os.path.isfile(SYSTEM_SFF):
        raise SystemExit("data/ikemen1/system.sff is missing - fetch the engine "
                         "data first")
    _d, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    slots = {(0, 0), (0, 1), (0, 2), (0, 3)}
    found = {(sp["group"], sp["number"]) for sp in sprites} & slots
    if found != slots:
        raise SystemExit(f"system.sff is missing logo slots: {slots - found}")

    logo = wordmark()
    glow = logo.filter(ImageFilter.GaussianBlur(3.2))
    blank = Image.new("RGBA", CANVAS, (0, 0, 0, 0))

    # 0,0 + 0,2 were a bright layer and its additive shadow; 0,1 + 0,3 were a
    # second element the engine drew bottom-right. The wordmark takes the bright
    # pair, a soft glow takes the shadows, and the second element is cleared so
    # no engine lettering survives on the screen.
    replacement = {(0, 0): logo, (0, 2): glow, (0, 1): blank, (0, 3): blank}

    out = []
    for sp in sprites:
        key = (sp["group"], sp["number"])
        if key in replacement:
            out.append({"group": key[0], "number": key[1],
                        "image": replacement[key], "axis": sp["axis"]})
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"],
                        "link": sp["link"]})

    # Build the whole file in memory and swap it in: opening the real path for
    # writing first would truncate a 9 MB engine asset if anything raised.
    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: built file has no SFF signature")
    with open(SYSTEM_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(SYSTEM_SFF + ".tmp", SYSTEM_SFF)

    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    logo.save(os.path.join(ROOT, "artifacts", "title_logo.png"))
    print(f"wrote the title logo into data/ikemen1/system.sff "
          f"({len(out)} sprites, slots 0,0-0,3 replaced)")


if __name__ == "__main__":
    build()
