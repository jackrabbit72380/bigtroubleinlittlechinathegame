#!/usr/bin/env python3
"""Paint and anchor the three floating-world stages: cards, island and weather.

The upstream Third Heights pack (SuperFromND, MIT) ships one island in two
renders, so the three stages are told apart by what happens around the island
rather than by the mesh: this tool paints each stage's card, the island backdrop
its def draws and the weather the def puts over that.

  Third Heights        bright day, cloud haze drifting across the top, spray
                       rising off the water
  Third Heights        the same island at night in the outline render, under a
   Outline             violet wash with cold motes climbing through it and mist
                       crawling along the water
  Third Heights        the storm: two layers of painted rain, one behind the
   Rainfall            fighters and one in front, a slate wash and driving mist

The island itself is painted rather than drawn from the .glb. The models are
sound - core glTF, unlit intent baked into their emissive textures - but a stage
cannot depend on a renderer that may not draw them: on the machine these stages
are played on the model never appeared and the screen was a black field with the
weather over it. See [BG island] in the three defs.

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


# The stage card's own gold rule: the stage wall's boxes are plain pictures, and
# without a rule they read as loose screenshots. Baked into every 9000,1 card so
# the wall, the select screen's hint and the VS card all get it, no runtime frame.
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
# ----------------------------------------------------------------- the island --
# The 3D model is off in these stages' defs. Its glTF is sound and the engine has
# a model path, but on the machine these stages are played on the model never
# drew: the screen was a black field with the painted weather on top of it, twice.
# A stage cannot depend on something that is not drawn, so the island is painted
# here instead - sky, sea, the rock mass and its mist - at the stage's own
# localcoord (1280x720), which is where the 2D weather layers are painted too.

def lerp(a, b, t):
    return tuple(int(round(a[k] + (b[k] - a[k]) * t)) for k in range(len(a)))


def vgrad(stops):
    """A 1280x720 canvas whose colour depends on y only."""
    img = Image.new("RGBA", FRAME, (0, 0, 0, 255))
    px = img.load()
    for y in range(FRAME[1]):
        for i in range(len(stops) - 1):
            y0, c0 = stops[i]
            y1, c1 = stops[i + 1]
            if y0 <= y <= y1:
                col = lerp(c0, c1, (y - y0) / float(max(1, y1 - y0)))
                for x in range(FRAME[0]):
                    px[x, y] = col + (255,)
                break
    return img


def soft_clouds(count, colour, seed, y0, y1, alpha, wrap=True):
    img = Image.new("RGBA", FRAME, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rng = random.Random(seed)
    w, h = FRAME
    for _ in range(count):
        cx = rng.uniform(0, w)
        cy = rng.uniform(y0, y1)
        rw = rng.uniform(150, 360)
        rh = rng.uniform(12, 34)
        a = rng.randint(alpha[0], alpha[1])
        shifts = (-w, 0, w) if wrap else (0,)
        for dx in shifts:
            draw.ellipse([cx + dx - rw, cy - rh, cx + dx + rw, cy + rh], fill=colour + (a,))
    return img


def island_layer(mode):
    """The terrace the fight happens on, in the pack's three hours of the day.

    The play plane is the flat top of the rock, not the frame's bottom: these
    stages put their ground line at zoffset 660 of a 720-tall localcoord, so the
    terrace surface is painted at y=604 and the mass under it falls off the frame.
    A card drawn with the plateau high and the sea at the bottom put the fighters
    in the water below their own island.
    """
    if mode == "day":
        sky = [(0, (86, 150, 210)), (250, (142, 190, 228)), (448, (222, 222, 206)),
               (FRAME[1], (222, 222, 206))]
        sea_top, sea_bottom = (80, 122, 134), (16, 34, 48)
        rock, rock_dark = (94, 94, 98), (32, 34, 42)
        rim, foliage, mist = (248, 240, 212), (64, 90, 60), (214, 226, 228)
        orb, orb_xy = (255, 246, 214), (1010, 116)
    elif mode == "night":
        sky = [(0, (18, 10, 40)), (250, (40, 24, 72)), (448, (88, 60, 110)),
               (FRAME[1], (88, 60, 110))]
        sea_top, sea_bottom = (32, 20, 52), (6, 3, 14)
        rock, rock_dark = (46, 34, 68), (14, 9, 28)
        rim, foliage, mist = (208, 192, 255), (40, 32, 70), (116, 98, 164)
        orb, orb_xy = (216, 210, 255), (286, 108)
    else:
        sky = [(0, (42, 54, 76)), (250, (66, 80, 102)), (448, (110, 122, 136)),
               (FRAME[1], (110, 122, 136))]
        sea_top, sea_bottom = (38, 50, 62), (10, 15, 22)
        rock, rock_dark = (62, 66, 74), (22, 26, 34)
        rim, foliage, mist = (188, 204, 220), (52, 64, 58), (144, 158, 172)
        orb, orb_xy = (198, 214, 232), (950, 132)

    horizon, ground = 448, 604
    img = vgrad(sky)

    glow = Image.new("RGBA", FRAME, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for rad, a in ((230, 10), (160, 14), (100, 20), (54, 30), (26, 70)):
        gd.ellipse([orb_xy[0] - rad, orb_xy[1] - rad,
                    orb_xy[0] + rad, orb_xy[1] + rad], fill=orb + (a,))
    img = Image.alpha_composite(img, glow)

    img = Image.alpha_composite(img, soft_clouds(14, lerp(rim, (255, 255, 255), 0.3),
                                                 7711, 70, 300, (24, 58)))
    img = Image.alpha_composite(img, soft_clouds(8, rim, 7713, 300, 410, (16, 34)))

    draw = ImageDraw.Draw(img)
    for y in range(horizon, FRAME[1]):
        t = (y - horizon) / float(FRAME[1] - horizon)
        draw.line([(0, y), (FRAME[0], y)], fill=lerp(sea_top, sea_bottom, t) + (255,))
    rng = random.Random(7721)
    for _ in range(70):
        y = rng.uniform(horizon + 8, FRAME[1] - 2)
        x = rng.uniform(-40, FRAME[0])
        ln = rng.uniform(40, 210)
        a = int(30 * (1.0 - (y - horizon) / float(FRAME[1] - horizon)) + 10)
        draw.line([(x, y), (x + ln, y)], fill=rim + (a,), width=1)

    # the orb's reflection: one soft wedge down the water, not a stack of bars
    refl = Image.new("RGBA", FRAME, (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    rd.polygon([(orb_xy[0] - 30, horizon), (orb_xy[0] + 30, horizon),
                (orb_xy[0] + 96, FRAME[1]), (orb_xy[0] - 96, FRAME[1])], fill=orb + (26,))
    rd.polygon([(orb_xy[0] - 14, horizon), (orb_xy[0] + 14, horizon),
                (orb_xy[0] + 46, FRAME[1]), (orb_xy[0] - 46, FRAME[1])], fill=orb + (30,))
    img = Image.alpha_composite(img, refl)

    # far islets on the horizon, so the sea has distance in it
    rd = ImageDraw.Draw(img)
    for cx, cw, ch in ((118, 66, 22), (206, 34, 13), (1094, 54, 18), (1188, 28, 10)):
        rd.polygon([(cx - cw, horizon), (cx, horizon - ch), (cx + cw, horizon)],
                   fill=lerp(rock_dark, (0, 0, 0), 0.35) + (235,))

    # the terrace: a shelf across the whole span, its mass falling off the frame
    top = []
    x = -40
    while x <= FRAME[0] + 40:
        top.append((x, ground + rng.randint(-5, 4)))
        x += 32
    body = top + [(FRAME[0] + 40, FRAME[1] + 40), (-40, FRAME[1] + 40)]
    shelf = Image.new("RGBA", FRAME, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shelf)
    sd.polygon(body, fill=rock + (255,))
    shade = Image.new("RGBA", FRAME, (0, 0, 0, 0))
    shd = ImageDraw.Draw(shade)
    for y in range(ground - 10, FRAME[1] + 1):
        t = min(1.0, (y - (ground - 10)) / 180.0)
        shd.line([(0, y), (FRAME[0], y)], fill=lerp(rock, rock_dark, t) + (255,))
    shelf = Image.composite(shade, shelf, shelf.split()[3])

    sd = ImageDraw.Draw(shelf)
    # the worn surface: a lighter band along the top, then the stone's grain
    for i in range(10):
        y = ground - 9 + i * 3
        sd.line([(0, y), (FRAME[0], y)], fill=lerp(rock, rim, 0.10) + (90 - i * 7,))
    for i in range(26):
        x = rng.uniform(-20, FRAME[0] + 20)
        y0 = ground + 14 + rng.uniform(0, 40)
        sd.line([(x, y0), (x + rng.uniform(-18, 18), y0 + rng.uniform(30, 90))],
                fill=rock_dark + (60,), width=rng.choice((2, 3)))
    sd.line(top, fill=rim + (200,), width=3, joint="curve")

    # planting along the back of the terrace, and one roof for scale
    for i in range(20):
        cx = rng.uniform(-10, FRAME[0] + 10)
        cy = ground - rng.uniform(2, 12)
        rw = rng.uniform(9, 24)
        sd.ellipse([cx - rw, cy - rw * 0.8, cx + rw, cy + rw * 0.4], fill=foliage + (255,))
    sd.polygon([(956, ground - 8), (986, ground - 46), (1016, ground - 8)],
               fill=rock_dark + (255,))
    sd.line([(986, ground - 46), (986, ground - 6)], fill=rim + (150,), width=2)

    img = Image.alpha_composite(img, shelf)

    # mist lying along the terrace, and over the sea beyond its edge
    mist_img = Image.new("RGBA", FRAME, (0, 0, 0, 0))
    md = ImageDraw.Draw(mist_img)
    for y in range(ground - 26, ground + 18):
        t = 1.0 - abs(y - (ground - 4)) / 22.0
        md.line([(0, y), (FRAME[0], y)], fill=mist + (int(70 * max(0.0, t)),))
    img = Image.alpha_composite(img, mist_img)
    return img


def lip_layer(mode):
    """A dark foreground edge at the foot of the frame, drawn over the fighters.

    Painted stages in this roster carry a [BG lip] on layerno 1 so the arena has
    something solid between the play plane and the viewer. This is that edge: the
    near side of the rock, fading out before it reaches the fighters' feet.
    """
    alpha = {"day": 168, "night": 190, "storm": 182}[mode]
    colour = {"day": (26, 30, 34), "night": (6, 4, 12), "storm": (16, 20, 26)}[mode]
    img = Image.new("RGBA", FRAME, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for y in range(FRAME[1] - 64, FRAME[1]):
        t = (y - (FRAME[1] - 64)) / 64.0
        draw.line([(0, y), (FRAME[0], y)], fill=colour + (int(alpha * t * t),))
    return img


def island_sprite(name):
    """The backdrop sprite the stage's [BG sky] layer reads."""
    mode = {"stage3d": "day", "stage3d_outline": "night"}.get(name, "storm")
    return {"group": 3, "number": {"day": 0, "night": 1}.get(mode, 2),
            "image": island_layer(mode), "axis": (0, 0)}


def lip_sprite(name):
    mode = {"stage3d": "day", "stage3d_outline": "night"}.get(name, "storm")
    return {"group": 3, "number": 3, "image": lip_layer(mode), "axis": (0, 0)}


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
    out = [{"group": 9000, "number": 1, "image": frame_card(picture), "axis": axis},
           {"group": 9000, "number": 0, "image": frame_card(picture), "axis": axis}]
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
        # The card is painted from the island this stage draws, not carried over
        # from the sheet it is being written into: that 9000,1 was a placeholder -
        # a gradient with a play badge on it - and it is what the stage-select wall
        # showed for all three of these stages while the arenas themselves were
        # the painted terrace.
        mode = {"stage3d": "day", "stage3d_outline": "night"}.get(name, "storm")
        picture = island_layer(mode).resize(SIZE, Image.LANCZOS)
        axis = (SIZE[0] // 2, SIZE[1] // 2)
        weather = sprites_for(name) + [island_sprite(name), lip_sprite(name)]
        write_sheet(path, picture, axis, weather)
        print("  stages/%s.sff: %dx%d card at %d,%d + %d weather sprite(s)"
              % (name, picture.width, picture.height, axis[0], axis[1], len(weather)))


if __name__ == "__main__":
    main(sys.argv[1:])
