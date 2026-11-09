"""Paint the game's own title logo into the screenpack SFF.

The title screen draws its logo from system.sff sprites 0,0-0,3: a bright layer
plus an additive shadow layer for each of two elements. Those slots are
replaced here with the project's wordmark, so the screenpack's positioning,
bobbing and fades keep working untouched.

The wordmark is the gold-on-maroon lockup: BIG TROUBLE arched across the top,
then IN / LITTLE / CHINA stacked beneath it. The blue ribbon swooshes an
earlier version swept past the letters are gone: they crossed the wordmark and
read as stray blue streaks sitting behind the title. The lockup is composed on a tall scratch canvas and
then fitted to the sprite, because the stacked lines and the arch's descending
arms do not fit a short canvas at any font size - and art.font() falls back
through system faces to Pillow's own default, so the metrics are not constant
between machines.

If art_src/ui/title_logo.png (or concept_art/ui/title_logo.png) exists, that
picture is used as the logo instead, fitted to the slot - so the painted film
art can replace this rendition without touching the pipeline.

Run:  python3 tools/build_title.py
"""

from __future__ import annotations

import math
import os
import random
import re
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYSTEM_SFF = os.path.join(ROOT, "data", "ikemen1", "system.sff")

# The logo sprite. Sized for this lockup rather than the engine's 699x257 slot:
# the arch plus three stacked lines needs the height.
# The engine draws this layer 1:1 - it ignores the "scale" line background
# layers can carry - so the sprite's own size is the wordmark's size and its
# resolution on screen. The stock 900x420 slot put 884 px of ink across a 1920
# frame and read soft, so the slot is 1.3x that: about 1154x371 of ink, which
# still leaves clear air above the title menu's first row (menu.pos = 960,470).
GROW = 1.3
CANVAS = (int(round(900 * GROW)), int(round(420 * GROW)))
# Where the lockup is drawn before it is fitted into CANVAS. The lockup is
# composed at SS times the sprite's size so the fit into the slot is a
# downscale: composed at sprite size it was stretched from the scratch canvas,
# and the wordmark on screen carried that softness.
SS = 2
SUP = SS * GROW          # composition size relative to the stock 900-wide design
SCRATCH = (CANVAS[0] * SS, int(round(CANVAS[1] * 11 / 7)) * SS)
WORK = CANVAS

TOP_MARGIN = 30          # ink starts this far down the 1080-line screen
PAD = 8                  # clearance kept inside the sprite, for the glow
ARC_RADIUS = 760 * SUP   # bows the caps' ends well below the apex, as in the film

GOLD = [(0.00, (255, 228, 140)), (0.34, (246, 200, 110)),
        (0.68, (255, 197, 60)), (1.00, (236, 139, 24))]
MAROON = [(0.00, (152, 33, 45)), (0.55, (122, 20, 32)), (1.00, (82, 10, 20))]
CREAM = (255, 236, 180)
BLUE = (44, 70, 128)
BLUE_DEEP = (26, 44, 92)
WHITE = (255, 255, 255)

PLATES = (os.path.join(ROOT, "art_src", "ui", "title_logo.png"),
          os.path.join(ROOT, "art_src", "ui", "title_logo_logo.png"),
          os.path.join(ROOT, "concept_art", "ui", "title_logo.png"),
          os.path.join(ROOT, "concept_art", "ui", "title_logo_logo.png"))


# ------------------------------------------------------------------- type

# The main menu and the VS screen draw each other's backdrop: the title layers
# now show the art the VS screen used to own, and tools/build_select_ui.py points
# the VS layers at the title set, so the two screens have swapped backgrounds.
# Only the sprite numbers change - every layer keeps its own start, window, tile,
# velocity and trans, and both skies are baked at 1920x1080 with a zero axis, so
# nothing has to be reseated or rescaled.
BACKDROP_SWAP = (("titlebg background sky", 204, 0),
                 ("titlebg background clouds top", 102, 2),
                 ("titlebg background clouds bottom", 102, 3))


def swap_backdrop_layers():
    """Point this screen's backdrop layers at the other screen's art."""
    path = os.path.join(ROOT, "data", "ikemen1", "system.def")
    if not os.path.isfile(path):
        return 0
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    wanted = {name: (group, number) for name, group, number in BACKDROP_SWAP}
    out, section, changed = [], "", 0
    for line in lines:
        s = line.strip().lower()
        if s.startswith("["):
            section = s.strip("[]").strip()
        elif s.startswith("spriteno") and section in wanted:
            group, number = wanted[section]
            line = "spriteno = " + str(group) + "," + str(number)
            changed += 1
        out.append(line)
    if changed:
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
        os.replace(path + ".tmp", path)
    return changed

def cap_height(size):
    font = art.font(size)
    box = font.getbbox("H")
    return box[3] - box[1]


def glyph_mask(ch, size, weight=0.06):
    """One capital, white on transparent, fattened to display weight."""
    font = art.font(size)
    stroke = max(1, int(round(size * weight)))
    box = font.getbbox(ch, stroke_width=stroke)
    pad = stroke + max(4, size // 10)
    img = Image.new("L", (box[2] - box[0] + pad * 2, box[3] - box[1] + pad * 2), 0)
    ImageDraw.Draw(img).text((pad - box[0], pad - box[1]), ch, font=font, fill=255,
                             stroke_width=stroke, stroke_fill=255)
    return img


def arc_line(text, size, cx, apex_y, radius, seed, jitter=1.0, tracking=0.98,
             weight=0.06):
    """Letters along an arc whose tops sit on ``apex_y`` at the centre.

    The arc's centre is directly below the apex, so a point at angle ``a`` is at
    (cx + R sin a, apex_y + R (1 - cos a)): the ends of the line drop by the
    sagitta, which is what gives the word its bow.
    """
    mask = Image.new("L", WORK, 0)
    rnd = random.Random(seed)
    font = art.font(size)
    chap = cap_height(size)
    widths = [max(1.0, font.getlength(c)) * tracking for c in text]
    total = sum(widths)
    half = (total * 1.02 / 2.0) / radius
    pos = 0.0
    for ch, adv in zip(text, widths):
        if ch != " ":
            frac = (pos + adv * 0.5) / total
            a = -half + 2.0 * half * frac
            gx = cx + radius * math.sin(a)
            gy = apex_y + radius * (1.0 - math.cos(a)) + chap * 0.5
            g = glyph_mask(ch, size, weight)
            ang = -math.degrees(a) + rnd.uniform(-2.0, 2.0) * jitter
            g = g.rotate(ang, resample=Image.BICUBIC, expand=True)
            gx += rnd.uniform(-1.2, 1.2) * jitter
            gy += rnd.uniform(-1.2, 1.2) * jitter
            mask.paste(g, (int(round(gx - g.width / 2)),
                           int(round(gy - g.height / 2))), g)
        pos += adv
    return mask


def flat_line(text, size, cx, cy, seed=0, jitter=0.0, tracking=0.98, weight=0.06,
              tilt=0.0):
    """A straight line of type, centred on (cx, cy)."""
    mask = Image.new("L", WORK, 0)
    rnd = random.Random(seed)
    font = art.font(size)
    stroke = max(1, int(round(size * weight)))
    widths = [max(1.0, font.getlength(c)) * tracking for c in text]
    total = sum(widths)
    pos = cx - total / 2.0
    for i, (ch, adv) in enumerate(zip(text, widths)):
        if ch != " ":
            box = font.getbbox(ch, stroke_width=stroke)
            g = Image.new("L", (box[2] - box[0] + 10, box[3] - box[1] + 10), 0)
            ImageDraw.Draw(g).text((5 - box[0], 5 - box[1]), ch, font=font, fill=255,
                                   stroke_width=stroke, stroke_fill=255)
            ang = tilt * (i / max(1, len(text) - 1) - 0.5) * 2.0
            if jitter or ang:
                g = g.rotate(ang + rnd.uniform(-1.0, 1.0) * jitter,
                             resample=Image.BICUBIC, expand=True)
            mask.paste(g, (int(round(pos + box[0] - 5 + (adv - (box[2] - box[0])) / 2)),
                           int(round(cy - g.height / 2
                                     + rnd.uniform(-0.8, 0.8) * jitter))), g)
        pos += adv
    return mask


def width_of(img):
    box = img.getbbox()
    return 0 if box is None else box[2] - box[0]


def fit_size(target, build, guess=90.0, lo=10.0, hi=280.0, passes=6):
    """Return the size at which ``build`` draws ``target`` pixels of ink."""
    best, best_err = int(guess), None
    for _ in range(passes):
        wide = width_of(build(best))
        if not wide:
            break
        err = abs(wide - target)
        if best_err is not None and err >= best_err:
            break
        best_err = err
        if err <= 2:
            break
        best = int(max(lo, min(hi, best * target / float(wide))))
    return best


# ------------------------------------------------------------------- paint
def touches(a, b, box):
    """True if b's ink lands on a's ink (compared inside ``box``)."""
    region = ImageChops.multiply(a.crop(box), b.crop(box))
    return any(v > 40 for v in region.getdata())


def fill(mask, stops):
    """Vertical gradient clipped to a mask."""
    img = art.vgrad(WORK, [(int(t * (WORK[1] - 1)), c) for t, c in stops])
    img.putalpha(ImageChops.multiply(mask, img.getchannel("A")))
    return img


def shifted(mask, delta):
    out = Image.new("L", WORK, 0)
    out.paste(mask, delta)
    return out


def block(mask, depth):
    """The solid shape the letters are extruded into: the mask swept down-right."""
    dx, dy = depth
    out = mask
    steps = max(abs(dx), abs(dy))
    for i in range(1, steps + 1):
        out = ImageChops.lighter(out, shifted(mask, (dx * i // steps, dy * i // steps)))
    return out


def paint_line(mask, depth=(9, 10)):
    """Gold face, maroon extrusion, cream keyline, blue outer line."""
    solid = block(mask, depth)
    img = Image.new("RGBA", WORK, (0, 0, 0, 0))

    # outer blue keyline, then the cream one inside it
    img.alpha_composite(fill(solid.filter(ImageFilter.MaxFilter(5)), [(0, BLUE_DEEP)]))
    img.alpha_composite(fill(solid.filter(ImageFilter.MaxFilter(3)), [(0, CREAM)]))

    # the maroon block, darkened toward its foot so the extrusion reads as depth
    img.alpha_composite(fill(solid, MAROON))

    # the gold face, with a blush of white along its top edge
    img.alpha_composite(fill(mask, GOLD))
    lip = ImageChops.subtract(mask, shifted(mask, (0, 3)))
    img.alpha_composite(fill(lip, [(0, (255, 255, 245))]))

    # a soft inner shade at the foot of each letter, so the gold has weight
    foot = ImageChops.subtract(mask, shifted(mask, (0, -6)))
    shade = fill(foot, [(0, (200, 110, 20))])
    shade.putalpha(shade.getchannel("A").point(lambda v: int(v * 0.35)))
    img.alpha_composite(shade)
    return img.filter(ImageFilter.GaussianBlur(0.4))


# ------------------------------------------------------------------ ribbons
def catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return (0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                   + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                   + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
            0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                   + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                   + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3))


def spline(points, steps=240):
    """Sample a Catmull-Rom spline through ``points``."""
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    span = len(pts) - 3
    per = max(1, steps // span)
    for i in range(span):
        for s in range(per):
            out.append(catmull(pts[i], pts[i + 1], pts[i + 2], pts[i + 3],
                               s / float(per)))
    out.append(points[-1])
    return out


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ribbon(points, width=(30.0, 26.0), colors=(WHITE, BLUE_DEEP), seed=3):
    """A tapered brush ribbon along a spline, graded from white to blue."""
    rnd = random.Random(seed)
    path = spline(points)
    layer = Image.new("RGBA", WORK, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    n = len(path)
    for i, (x, y) in enumerate(path):
        t = i / float(n - 1)
        # fat through the middle, thinning at both ends
        shape = math.sin(math.pi * min(1.0, max(0.02, t))) ** 0.55
        r = (width[0] + (width[1] - width[0]) * t) * shape
        r *= 1.0 + rnd.uniform(-0.04, 0.04)
        col = lerp(colors[0], colors[1], min(1.0, t * 1.1))
        d.ellipse([x - r, y - r * 0.8, x + r, y + r * 0.8], fill=col + (255,))
    layer = layer.filter(ImageFilter.GaussianBlur(1.1))

    # a bright crest along the ribbon's upper edge
    crest = Image.new("RGBA", WORK, (0, 0, 0, 0))
    cd = ImageDraw.Draw(crest)
    for i, (x, y) in enumerate(path):
        t = i / float(n - 1)
        shape = math.sin(math.pi * min(1.0, max(0.02, t))) ** 0.55
        r = (width[0] + (width[1] - width[0]) * t) * shape * 0.32
        if r < 0.8:
            continue
        cd.ellipse([x - r, y - r * 0.85 - 3.0, x + r, y + r * 0.4 - 3.0],
                   fill=(255, 255, 255, 120))
    layer.alpha_composite(crest.filter(ImageFilter.GaussianBlur(2.2)))
    return layer


# ------------------------------------------------------------------- plate
# The title backdrop: full-screen art drawn over the animated clouds, under the
# logo (layerno 1) and the menu text (layerno 2). Groups already used by the
# engine screenpack: 0, 98, 100-102, 110-113, 150-192, 200-204, 220-223,
# 400-403, 500, 600, 610, 700, 800, 810, 921-923, 1000 - 205 is the first gap,
# so the backdrop cannot overwrite real screen art.
SCREEN = (1280, 720)
# The screen's localcoord. The title layers draw 1:1 in this space - the
# "scale = 1.5" written on them in the def has no effect - so the backdrop has
# to be painted at this size to fill the frame.
FRAME = (1920, 1080)
SKY_SLOT = (100, 0)
# [TitleBG Background Clouds Bottom] is the layer that reaches the floor of the
# screen, and it is 960 tall - the same 1280x720-era size the sky was. It stops
# 120px short of the bottom, so the last strip of the main menu was bare sky
# under the menu list with a hard line across it. It is baked to the frame's
# height here; the layer tiles horizontally, so its width is left alone.
CLOUD_BOTTOM = (100, 3)
OVERLAY = (205, 0)
SPLASHES = (os.path.join(ROOT, "art_src", "ui", "splash.png"),
            os.path.join(ROOT, "concept_art", "ui", "splash.png"))


def first_plate(paths):
    for path in paths:
        if os.path.isfile(path):
            return path
    return None


def flat_key(img, tol=20):
    """Turn a flat painted backdrop into transparency, then crop to the ink.

    Painted logos usually arrive flattened onto a light plate rather than with
    real alpha, so the corner colour is read as the backdrop and every pixel
    close to it is cleared. The picture is then cropped to what is left, since
    empty margin only shrinks the logo once it is fitted to the sprite. Art that
    already carries alpha, or that has no single corner colour, is only cropped.
    """
    img = img.convert("RGBA")
    alpha = img.getchannel("A")
    if alpha.getextrema()[0] < 250:
        box = alpha.getbbox()
        return img.crop(box) if box else img

    corners = [img.getpixel(p) for p in ((0, 0), (img.width - 1, 0),
                                         (0, img.height - 1),
                                         (img.width - 1, img.height - 1))]
    base = corners[0][:3]
    flat = all(max(abs(c[i] - base[i]) for i in range(3)) <= 12
               for c in corners[1:])
    if not flat:
        return img

    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if abs(r - base[0]) <= tol and abs(g - base[1]) <= tol \
                    and abs(b - base[2]) <= tol:
                px[x, y] = (r, g, b, 0)
    box = img.getchannel("A").getbbox()
    return img.crop(box) if box else img


def plate():
    """A painted title logo from art_src, if one has been supplied.

    Returns (image, path, aligned). ``aligned`` means the art is on the same
    canvas as the title backdrop, so the wordmark is already painted where it
    belongs: the art is packed at its own resolution with its canvas left alone,
    and the layers are given the backdrop's start and scalestart. That puts the
    engine's logo exactly on the painted wordmark.

    Keying and fitting it to a small sprite instead is what centred a second,
    smaller wordmark over the painting: cropping to the ink throws away the
    canvas position, and the sprite was then hung from TOP_MARGIN on its own.
    """
    path = first_plate(PLATES)
    if not path:
        return None, None, False
    img = Image.open(path).convert("RGBA")
    if img.width >= FRAME[0] * 2 and img.height >= FRAME[1] * 2:
        return opaque_off_black(img), path, True
    img = flat_key(Image.open(path))
    k = min(CANVAS[0] / float(img.width), CANVAS[1] / float(img.height))
    img = img.resize((max(1, int(round(img.width * k))),
                      max(1, int(round(img.height * k)))), Image.LANCZOS)
    out = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    out.alpha_composite(img, ((CANVAS[0] - img.width) // 2,
                              (CANVAS[1] - img.height) // 2))
    return out, path, False


def opaque_off_black(img):
    """Keep every visible pixel off pure black.

    ``mask = 1`` keys colour 0 out of a cut-out, so no visible pixel may sit on
    it: the night painting and the wordmark are both full of near-black, and
    punched holes would be worse than a shade. Clear pixels stay (0, 0, 0, 0) -
    they are the cut-out itself.
    """
    r, g, b, a = img.split()
    black = ImageChops.lighter(ImageChops.lighter(r, g), b).point(
        lambda v: 0 if v else 255)
    img.paste((1, 1, 1, 255),
              mask=ImageChops.multiply(black, a.point(lambda v: 255 if v else 0)))
    return img


def overlay():
    """The full-screen backdrop from art_src/ui/splash.png, cover-cropped.

    Transparency survives on purpose. This layer sits above the clouds, so an
    opaque poster hides the sky completely while a cut-out one lets it show
    through - and a flat plate colour is keyed out the same way the logo's is,
    so an export with a white or grey box does not paint a rectangle over the
    animated clouds.
    """
    path = first_plate(SPLASHES)
    if not path:
        return None, None
    img = flat_key(Image.open(path))
    # FRAME, not SCREEN: this layer is drawn in the title's 1920x1080 localcoord
    # (every [TitleBG] sprite in the screenpack is 1920x1080 with a zero axis),
    # so a 1280x720 plate would cover only two thirds of the title screen.
    #
    # A 16:9 source is only ever resized here, never cropped: cover-fitting an
    # image that is already the frame's shape scales both sides by the same
    # amount and crops nothing.
    #
    # Packed at the master's own resolution, never downsampled to the frame.
    # These system layers honour scalestart - the shipped screenpack scales its
    # own attract logo with scalestart = 1.5,1.5 - so a plate drawn at
    # 1/scale covers exactly the frame while keeping every pixel of an 8K master
    # for a render above localcoord. The "scale = 1.5" lines this build strips
    # were a different, invalid key: scalestart is the one the engine reads.
    wide = img.width >= FRAME[0] * 2 and img.height >= FRAME[1] * 2
    if wide:
        th = img.height
        tw = int(round(th * FRAME[0] / float(FRAME[1])))
        if tw > img.width:
            tw = img.width
            th = int(round(tw * FRAME[1] / float(FRAME[0])))
    else:
        tw, th = FRAME
    k = max(tw / float(img.width), th / float(img.height))
    img = img.resize((max(1, int(round(img.width * k))),
                      max(1, int(round(img.height * k)))), Image.LANCZOS)
    left = (img.width - tw) // 2
    top = (img.height - th) // 2
    img = img.crop((left, top, left + tw, top + th)).convert("RGBA")
    return opaque_off_black(img), path


def bg_start(section):
    """The ``start`` of one [TitleBG ...] layer, or None."""
    path = os.path.join(ROOT, "data", "ikemen1", "system.def")
    if not os.path.isfile(path):
        return None
    current = ""
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip().lower()
            if s.startswith("["):
                current = s
            elif current == "[" + section.lower() + "]" and s.startswith("start"):
                try:
                    x, y = s.split("=", 1)[1].split(",")
                    return int(x.strip()), int(y.strip())
                except ValueError:
                    return None
    return None


def place_overlay(start, scale=1):
    """Add the backdrop layer after the clouds and before the logo.

    ``scale`` is the plate's width over the frame's. A master with the pixels for
    more than the frame is packed at full resolution and drawn back down with
    ``scalestart``, which these system layers honour, so the frame gets every
    pixel of the art instead of a 1920-wide downsample.

    ``mask = 1`` is what makes the plate a cut-out. It is what every other
    transparent layer in this file uses - the engine's own wordmark at 0,0 is a
    32-bit cut-out drawn with it - and with ``mask = 0`` the clear pixels of a
    32-bit sprite are painted over the sky instead of letting it through, which
    is the black plate.

    Definition order is drawing order inside a layerno, so putting this section
    between the sky/cloud layers and [TitleBG Title Logo] is what makes the art
    cover the clouds yet stay under the wordmark and the menu. Idempotent: an
    existing overlay block is removed before the new one is written.
    """
    path = os.path.join(ROOT, "data", "ikemen1", "system.def")
    if not os.path.isfile(path):
        return False
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()

    out, skipping, placed = [], False, False
    for line in lines:
        s = line.strip().lower()
        if s.startswith("["):
            skipping = s.startswith("[titlebg title overlay")
        if skipping:
            continue
        if start is not None and s.startswith("[titlebg title logo") and not placed:
            if out and out[-1].strip():
                out.append("")
            block = ["[TitleBG Title Overlay]",
                     "type = normal",
                     "spriteno = %d, %d" % OVERLAY,
                     "layerno = 0",
                     "start = %d,%d" % start]
            if scale != 1:
                block.append("scalestart = %.6g, %.6g" % (scale, scale))
            block += ["mask = 1", ""]
            out.extend(block)
            placed = True
        out.append(line)

    text = "\n".join(out) + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    swap_backdrop_layers()
    return placed


# -------------------------------------------------------------------- logo
def lockup():
    """The lockup on the scratch canvas, before fitting."""
    cx = WORK[0] / 2.0

    caps_size = fit_size(0.84 * WORK[0],
                         lambda s: arc_line("BIG TROUBLE", s, cx, int(round(24 * SUP)),
                                            ARC_RADIUS, seed=4, jitter=1.0),
                         guess=int(110 * SUP), hi=int(280 * SUP))
    caps = arc_line("BIG TROUBLE", caps_size, cx, int(round(24 * SUP)), ARC_RADIUS, seed=4,
                    jitter=1.0)
    cbox = caps.getbbox()

    # The arch's arms dive well below the centre, so the stack is measured from
    # the middle of the caps - not from the bottom of the whole mask, which is
    # the tip of the outer letters.
    middle = caps.crop((int(cx) - 40, 0, int(cx) + 40, WORK[1])).getbbox()
    mid_bottom = middle[3]

    in_size = max(16, int(round(caps_size * 0.17)))
    in_mask = flat_line("IN", in_size, cx + 2, mid_bottom + in_size * 0.66,
                        seed=7, jitter=0.3, weight=0.06)
    ibox = in_mask.getbbox()

    # LITTLE and CHINA stack under it, narrow enough to sit in the opening
    # between the arms; if a font's metrics push one into an arm, it drops
    # until it clears rather than crossing it.
    # Sized by cap height, not by width: LITTLE has six letters to BIG TROUBLE's
    # eleven, so matching widths would make its capitals as tall as the arch.
    little_size = max(24, int(round(caps_size * 0.66)))
    little_y = ibox[3] + little_size * 0.62
    little = flat_line("LITTLE", little_size, cx - 30, little_y, seed=11,
                       jitter=0.4, weight=0.05, tilt=0.5)
    while little_y < WORK[1] - int(60 * SUP) and touches(caps, little, little.getbbox()):
        little_y += int(4 * SUP)
        little = flat_line("LITTLE", little_size, cx - 30, little_y, seed=11,
                           jitter=0.4, weight=0.05, tilt=0.5)
    lbox = little.getbbox()

    china_size = max(22, int(round(caps_size * 0.62)))
    china_y = lbox[3] + china_size * 0.60
    china = flat_line("CHINA", china_size, cx + 30, china_y, seed=13, jitter=0.4,
                      weight=0.05, tilt=-0.5)
    while china_y < WORK[1] - int(50 * SUP) and touches(caps, china, china.getbbox()):
        china_y += int(4 * SUP)
        china = flat_line("CHINA", china_size, cx + 30, china_y, seed=13,
                          jitter=0.4, weight=0.05, tilt=-0.5)
    hbox = china.getbbox()

    art_img = Image.new("RGBA", WORK, (0, 0, 0, 0))
    art_img.alpha_composite(paint_line(caps, depth=(int(12 * SUP), int(13 * SUP))))
    art_img.alpha_composite(paint_line(in_mask, depth=(int(5 * SUP), int(6 * SUP))))
    art_img.alpha_composite(paint_line(
        little, depth=(max(4, little_size // 10), max(5, little_size // 9))))
    art_img.alpha_composite(paint_line(
        china, depth=(max(4, china_size // 10), max(5, china_size // 9))))
    return art_img


def wordmark():
    """The lockup fitted into the sprite, with its ink box."""
    global WORK
    WORK = SCRATCH
    try:
        art_img = lockup()
    finally:
        WORK = CANVAS

    box = art_img.getbbox()
    art_img = art_img.crop(box)
    room = (CANVAS[0] - PAD * 2, CANVAS[1] - PAD * 2)
    # fill the slot: the lockup is drawn on a scratch canvas at working size,
    # so scaling it up into the sprite is how it gets its final resolution
    k = min(room[0] / float(art_img.width), room[1] / float(art_img.height))
    art_img = art_img.resize((max(1, int(round(art_img.width * k))),
                              max(1, int(round(art_img.height * k)))),
                             Image.LANCZOS)

    logo = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    logo.alpha_composite(art_img, ((CANVAS[0] - art_img.width) // 2,
                                   (CANVAS[1] - art_img.height) // 2))
    box = logo.getbbox()
    if box[0] < 1 or box[2] > CANVAS[0] - 1 or box[1] < 1 or box[3] > CANVAS[1] - 1:
        raise SystemExit(f"title logo overflows its canvas: {box}")
    return logo, box


def place_def(start, scale=1, static=False):
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
            bare = s.replace(" ", "").lower()
            if bare in ("spriteno=0,0", "spriteno=0,1",
                        "spriteno=0,2", "spriteno=0,3"):
                pending = True
            elif pending and bare.startswith("start="):
                out.append(f"start = {start[0]},{start[1]}")
                if scale != 1:
                    out.append("scalestart = %.6g, %.6g" % (scale, scale))
                pending = False
                continue
            elif bare.startswith("scalestart="):
                continue          # rewritten right after the start line
            elif static and (bare.startswith("sin.y") or bare.startswith("sin.x")):
                # the wordmark is painted into the backdrop, so a bobbing layer
                # would slide off it and show the doubled logo
                continue
        out.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    return start


def strip_menu_shade():
    """Drop the engine's black panel from behind the title menu.

    The stock motif draws [TitleBG Background Black Menu Bars]: a 785x348
    semi-transparent black plate at start = 640,282, which lands right where the
    menu column sits - so the whole list was read through a grey smear. The
    engine data is restored on every build, so the layer is removed here instead
    of by hand. Idempotent: a file without the block is left untouched.
    """
    path = os.path.join(ROOT, "data", "ikemen1", "system.def")
    if not os.path.isfile(path):
        return False
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    out, skipping = [], False
    for line in lines:
        s = line.strip().lower()
        if s.startswith("["):
            skipping = s.startswith("[titlebg background black menu bar")
        if not skipping:
            out.append(line)
    if len(out) == len(lines):
        return False
    while out and not out[-1].strip():
        out.pop()
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    return True


def full_frame_sky(stock):
    """Paint the stock sky at frame size.

    The screenpack ships a 1280x960 sky, sized for a 1280x720 motif, but this
    motif's title layers are drawn 1:1 in a 1920x1080 localcoord - the
    "scale = 1.5" on each [TitleBG] layer is never applied - so the art covered
    only the left two thirds of the frame and stopped 120px above the bottom.
    What showed through was bgclearcolor: a blue rectangle with a black band
    under the menu. Cover-cropping the sky here fills the frame while leaving
    every layer's start, layerno and the cloud offsets exactly as they were.
    Idempotent: a sky already at frame size is passed through untouched.
    """
    if tuple(stock.size) == FRAME:
        return stock.convert("RGBA")
    k = max(FRAME[0] / float(stock.width), FRAME[1] / float(stock.height))
    wide = stock.resize((max(FRAME[0], int(round(stock.width * k))),
                         max(FRAME[1], int(round(stock.height * k)))),
                        Image.LANCZOS)
    return wide.convert("RGBA").crop((0, 0, FRAME[0], FRAME[1]))


# Any background layer block: [TitleBG ...], [OptionBG ...], [HiscoreBG ...],
# [VictoryBG ...] and so on. [Hiscore Info] and the like are not layers.
BG_SECTION = re.compile(r"^\[[a-z0-9_]*bg(\s|def\])")


def strip_dead_scale():
    """Drop the "scale = 1.5" lines from every screen's background layers.

    They were there to blow 1280x720-era art up to this motif's frame, but the
    engine draws these layers 1:1 - a 1280-wide sky landed on the left two
    thirds of a 1920 frame with the line in place - so they did nothing on the
    title, and the same dead lines were still sitting on the option, ranking,
    victory, replay and attract backgrounds. Every floor bitmap is now painted
    at frame size, so all of them draw 1:1 and the lines go.
    Idempotent: a def without them is left untouched.
    """
    path = os.path.join(ROOT, "data", "ikemen1", "system.def")
    if not os.path.isfile(path):
        return 0
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    out, section, dropped = [], "", 0
    for line in lines:
        s = line.strip().lower()
        if s.startswith("["):
            section = s
        elif BG_SECTION.match(section) \
                and s.replace(" ", "").startswith("scale=1.5,1.5"):
            dropped += 1
            continue
        out.append(line)
    if not dropped:
        return 0
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    return dropped


def build():
    if not os.path.isfile(SYSTEM_SFF):
        raise SystemExit("data/ikemen1/system.sff is missing - fetch the engine "
                         "data first")
    d, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    slots = {(0, 0), (0, 1), (0, 2), (0, 3)}
    found = {(sp["group"], sp["number"]) for sp in sprites} & slots
    if found != slots:
        raise SystemExit(f"system.sff is missing logo slots: {slots - found}")

    painted, source, aligned = plate()
    if painted is None:
        logo, box = wordmark()
    elif aligned:
        logo, box = painted, painted.getbbox()
        print(f"using painted title plate {os.path.relpath(source, ROOT)} at "
              f"{logo.width}x{logo.height} on the backdrop's canvas")
    else:
        logo, box = painted, painted.getbbox()
        print(f"using painted title plate {os.path.relpath(source, ROOT)}")

    # the glow is measured in sprite pixels, so it scales with the plate
    grow = GROW * (logo.width / float(CANVAS[0])) if aligned else GROW
    glow = logo.filter(ImageFilter.GaussianBlur(3.2 * grow))
    blank = Image.new("RGBA", CANVAS, (0, 0, 0, 0))

    # 0,0 + 0,2 were a bright layer and its additive shadow; 0,1 + 0,3 were a
    # second element the engine drew on top of the first. The wordmark takes the
    # bright pair, a soft glow takes the shadows, and the second element is
    # cleared so no engine lettering survives on the screen.
    sky = next((sp for sp in sprites
                if (sp["group"], sp["number"]) == SKY_SLOT), None)
    if sky is None:
        raise SystemExit("system.sff has no sky sprite at 100,0")
    sky_img = full_frame_sky(sff.decode_sprite(d, sky, palettes))

    floor = next((sp for sp in sprites
                  if (sp["group"], sp["number"]) == CLOUD_BOTTOM), None)
    if floor is None:
        raise SystemExit("system.sff has no floor cloud sprite at 100,3")
    floor_img = sff.decode_sprite(d, floor, palettes)
    if floor_img.height != FRAME[1]:
        # a 12.5% vertical stretch of soft cloud: it puts the layer's last row
        # on the frame's last row, so the art runs off the bottom edge
        floor_img = floor_img.resize((floor_img.width, FRAME[1]), Image.LANCZOS)
    if floor_img.height != FRAME[1]:
        raise SystemExit("the floor cloud layer does not reach the frame's floor")

    sky_axis = next((sp["axis"] for sp in sprites
                     if (sp["group"], sp["number"]) == (100, 0)), (0, 0))
    replacement = {(0, 0): logo, (0, 2): glow, (0, 1): blank, (0, 3): blank,
                   SKY_SLOT: sky_img, CLOUD_BOTTOM: floor_img}

    out = []
    for sp in sprites:
        key = (sp["group"], sp["number"])
        if key in replacement:
            # on the backdrop's grid the logo shares the sky's axis, so the same
            # start and scalestart land it on the painted wordmark
            axis = sky_axis if aligned and key[0] == 0 else sp["axis"]
            out.append({"group": key[0], "number": key[1],
                        "image": replacement[key], "axis": axis})
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"],
                        "link": sp["link"]})

    # The backdrop goes in as its own sprite, sharing the sky's axis so it lands
    # exactly where the clouds do.
    over_img, over_src = overlay()
    out = [sp for sp in out if (sp["group"], sp["number"]) != OVERLAY]
    if over_img is not None:
        out.append({"group": OVERLAY[0], "number": OVERLAY[1],
                    "image": over_img, "axis": sky_axis})

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
    where = bg_start("titlebg background sky") or (-640, 0)
    factor = 1.0
    if over_img is not None:
        factor = over_img.width / float(FRAME[0])
    if aligned:
        # no fitting at all: the art carries the wordmark's place with it
        start = where
        place_def(start, 1.0 / factor, static=True)
        print(f"title logo on the backdrop's grid: start = {start[0]},{start[1]}, "
              f"scalestart {1.0 / factor:.6g}, no bob")
    else:
        axis = next(sp["axis"] for sp in sprites
                    if (sp["group"], sp["number"]) == (0, 0))
        start = (int(round(axis[0] - (box[0] + box[2]) / 2.0)),
                 int(round(TOP_MARGIN + axis[1] - box[1])))
        place_def(start)
    if strip_menu_shade():
        print("removed the black menu panel from the title background")
    dead = strip_dead_scale()
    if dead:
        print(f"removed {dead} dead scale = 1.5 line(s) from the background layers")
    print(f"sky painted at {sky_img.width}x{sky_img.height} to fill the "
          f"{FRAME[0]}x{FRAME[1]} frame")
    print(f"floor cloud layer at {floor_img.width}x{floor_img.height} - it now "
          f"reaches the bottom of the frame")
    # Called either way: with no plate the layer and its sprite are removed
    # again, so deleting art_src/ui/splash.png restores the plain clouds.
    if place_overlay(where if over_img is not None else None, 1.0 / factor):
        print(f"using painted title backdrop {os.path.relpath(over_src, ROOT)} "
              f"at {over_img.width}x{over_img.height} over the sky "
              f"(scalestart {1.0 / factor:.6g}, mask = 1)")
    elif over_img is None:
        print("no art_src/ui/splash.png - the title keeps its painted clouds")

    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    logo.save(os.path.join(ROOT, "artifacts", "title_logo.png"))
    print(f"wrote the title logo into data/ikemen1/system.sff "
          f"({len(out)} sprites, slots 0,0-0,3 replaced)")
    print(f"logo ink box {box}, placed at start = {start[0]},{start[1]}")


if __name__ == "__main__":
    build()
