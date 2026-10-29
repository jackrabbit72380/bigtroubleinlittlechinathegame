"""Paint the game's own title logo into the screenpack SFF.

The title screen draws its logo from system.sff sprites 0,0-0,3: a bright layer
plus an additive shadow layer for each of two elements. Those slots are
replaced here with the project's wordmark - heavy arched brush capitals reading
BIG TROUBLE, with "in Little China" set small beneath - so the screenpack's
positioning, bobbing and fades keep working untouched.

Every size in here is measured from the loaded font rather than written down.
art.font() falls back through a list of system faces to Pillow's own default,
so a build machine and a dev machine can resolve different files with different
advance widths; a layout tuned by hand against one of them clipped the outer
caps on the other.

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
# it means the wordmark just has to sit on the same canvas.
CANVAS = (699, 257)

# Layout targets, as fractions of the canvas width. The caps span most of it,
# the small line is about half the caps' width and tucks inside their arc.
BIG_SPAN = 0.86
SMALL_SPAN = 0.56
TOP_MARGIN = 40          # artwork starts this far down the 720-line screen
ARC_RADIUS = 1300        # bows the ends ~31px below the apex, as in the reference

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


def width_of(img):
    box = img.getbbox()
    return 0 if box is None else box[2] - box[0]


def sized_to(target, build, guess=60.0, lo=10.0, hi=170.0, passes=5):
    """Build a line repeatedly until its ink is ``target`` pixels wide."""
    best, size, best_err = None, guess, None
    for _ in range(passes):
        img = build(int(round(size)))
        wide = width_of(img)
        if not wide:
            break
        err = abs(wide - target)
        if best_err is None or err < best_err:
            best, best_err = img, err
        if err <= 2:
            break
        size = max(lo, min(hi, size * target / float(wide)))
    return best


def touches(big, cand, box):
    """True if the candidate's ink lands on the big line's ink."""
    region = ImageChops.multiply(big.crop(box), cand.crop(box))
    return any(v > 40 for v in region.getdata())


def caps_line():
    """BIG TROUBLE, arch across the canvas at a measured width."""
    cx = CANVAS[0] / 2.0

    def build(size):
        # apex 30 keeps the ink clear of the canvas top: the additive glow layer
        # is a blur of this art, so ink running to within a few pixels of the
        # edge would be cut off square by the sprite boundary.
        return arc_line("BIG TROUBLE", size, cx, 30, ARC_RADIUS, seed=4,
                        jitter=1.0, tracking=1.02, weight=0.05)

    return sized_to(BIG_SPAN * CANVAS[0], build, guess=90.0, hi=150.0)


def subtitle(big):
    """in Little China, sized to the caps and tucked inside their arc."""
    cx = CANVAS[0] / 2.0
    box = big.getbbox()
    target = SMALL_SPAN * (box[2] - box[0])
    size = sized_to_size(target, lambda s: flat_line("in Little China", s, cx, 0,
                                                     seed=9, jitter=0.6,
                                                     weight=0.032), guess=60.0)

    # Walk down from the middle of the caps: the first spot that touches no
    # letter is the tightest one that stays inside the arc.
    for cy in range(box[1] + (box[3] - box[1]) // 3, box[3] + 16):
        cand = flat_line("in Little China", size, cx, cy, seed=9, jitter=0.6,
                         weight=0.032)
        cb = cand.getbbox()
        if cb is None or cb[0] < 8 or cb[2] > CANVAS[0] - 8:
            continue
        if not touches(big, cand, cb):
            return cand

    # Nothing fits between the outer caps on this face: shrink and sit under.
    while size > 12:
        size = int(size * 0.92)
        cand = flat_line("in Little China", size, cx, box[3] + 4, seed=9,
                         jitter=0.6, weight=0.032)
        cb = cand.getbbox()
        if cb and not touches(big, cand, cb):
            return cand
    return flat_line("in Little China", 24, cx, box[3] + 6, seed=9, jitter=0.6)


def sized_to_size(target, build, guess=60.0, lo=12.0, hi=120.0, passes=5):
    """Like sized_to, but returns the size rather than the rendered line."""
    size, best, best_err = guess, int(guess), None
    for _ in range(passes):
        wide = width_of(build(int(round(size))))
        if not wide:
            break
        err = abs(wide - target)
        if best_err is None or err < best_err:
            best, best_err = int(round(size)), err
        if err <= 2:
            break
        size = max(lo, min(hi, size * target / float(wide)))
    return best


def wobble(mask, amp=1.6, seed=7):
    """Displace the letterform edges through a smooth noise field.

    Painted letters never have a mathematically clean edge. A few pixels of
    low-frequency drift is what separates brush from type; without it the caps
    read as set text no matter how heavy the stroke is.
    """
    rnd = random.Random(seed)
    W, H = CANVAS
    small = (W // 14 + 2, H // 14 + 2)
    seed_img = Image.new("L", small)
    seed_img.putdata([rnd.randrange(256) for _ in range(small[0] * small[1])])

    fields = []
    for phase in (0, 1):
        f = Image.new("L", small)
        f.paste(seed_img, (0, 0))
        if phase:
            f = f.transpose(Image.FLIP_LEFT_RIGHT)
        f = f.resize(CANVAS, Image.BICUBIC).filter(ImageFilter.GaussianBlur(2.5))
        fields.append(list(f.getdata()))

    src = list(mask.getdata())
    out = [0] * (W * H)
    fx, fy = fields
    for y in range(H):
        row = y * W
        dy = int((fy[row] - 128) / 128.0 * amp)
        for x in range(W):
            sx = x + int((fx[row + x] - 128) / 128.0 * amp)
            sy = y + dy
            if 0 <= sx < W and 0 <= sy < H:
                out[row + x] = src[sy * W + sx]
    res = Image.new("L", CANVAS, 0)
    res.putdata(out)
    return res


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
    for _ in range(120):
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
    """The finished logo on the 699x257 screenpack canvas, and its ink box."""
    big = caps_line()
    small = subtitle(big)
    mask = wobble(ImageChops.lighter(big, small))
    mask = ImageChops.lighter(brush(mask, seed=4), brush(mask, seed=9))
    logo = paint(mask)
    box = logo.getchannel("A").getbbox()
    if box[0] < 4 or box[2] > CANVAS[0] - 4:
        raise SystemExit(f"title logo overflows its canvas: {box}")
    return logo, box


def place_def(start):
    """Move the four logo layers to where the reference art has the wordmark.

    system.def ships the engine's own logo at start = -250,155, which put this
    wordmark down and left of centre. The engine data is restored on every
    build, so the positions are re-applied here instead of being edited by hand.
    """
    path = os.path.join(ROOT, "data", "ikemen1", "system.def")
    if not os.path.isfile(path):
        return start
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    out, section, pending = [], "", False
    for line in lines:
        s = line.strip()
        if s.startswith("["):
            section, pending = s.lower(), False
        elif section.startswith("[titlebg title logo"):
            if s.replace(" ", "") in ("spriteno=0,0", "spriteno=0,1",
                                       "spriteno=0,2", "spriteno=0,3"):
                pending = True
            elif pending and s.replace(" ", "").startswith("start="):
                line = f"start = {start[0]},{start[1]}"
                pending = False
        out.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    return start


def build():
    if not os.path.isfile(SYSTEM_SFF):
        raise SystemExit("data/ikemen1/system.sff is missing - fetch the engine "
                         "data first")
    _d, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    slots = {(0, 0), (0, 1), (0, 2), (0, 3)}
    found = {(sp["group"], sp["number"]) for sp in sprites} & slots
    if found != slots:
        raise SystemExit(f"system.sff is missing logo slots: {slots - found}")

    logo, box = wordmark()
    glow = logo.filter(ImageFilter.GaussianBlur(3.2))
    blank = Image.new("RGBA", CANVAS, (0, 0, 0, 0))

    # 0,0 + 0,2 were a bright layer and its additive shadow; 0,1 + 0,3 were a
    # second element the engine drew on top of the first. The wordmark takes the
    # bright pair, a soft glow takes the shadows, and the second element is
    # cleared so no engine lettering survives on the screen.
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

    # Centre the inked box on the screen and hang it TOP_MARGIN down, measured
    # from where the ink actually landed rather than from the canvas edge.
    axis = next(sp["axis"] for sp in sprites
                if (sp["group"], sp["number"]) == (0, 0))
    start = (int(round(axis[0] - (box[0] + box[2]) / 2.0)),
             int(round(TOP_MARGIN + axis[1] - box[1])))
    place_def(start)

    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    logo.save(os.path.join(ROOT, "artifacts", "title_logo.png"))
    print(f"wrote the title logo into data/ikemen1/system.sff "
          f"({len(out)} sprites, slots 0,0-0,3 replaced)")
    print(f"logo ink box {box}, placed at start = {start[0]},{start[1]}")


if __name__ == "__main__":
    build()
