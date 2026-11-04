"""Build the top strip: the big bars on top, audacity below, dragons in it.

Everything lives in the first ~52 pixels of the 1280x720 fight screen:

    y  2..30   the big bars - health - painted as the dragon's scaled back,
               red for player one and green for player two
    y 30..50   the meter band, which is the dragon's own body:
                 top half    = skin   -> the power meter
                 bottom half = belly  -> the audacity (underbelly) meter
    y  0..48   the glowing green/red yin-yang at dead centre, timer inside it

So the bars are not laid over the dragon: the dragon's back is the big bar, and
the dragon's body is the power/audacity meter. Head, horns, mane and the tail
grow out of the body at either end, with no legs and no arms.

Sprites written into data/fight.sff:

    10,0 11,0 12,0 13,0..3   the big bar, as dragon skin
    40,0 41,0 43,0 44,0      the body band: skin over belly
    20,0 / 20,1              head + tail halves, one per player

    python3 tools/build_banner.py
"""

import math
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import sff  # noqa: E402

FIGHT_SFF = os.path.join(ROOT, "data", "fight.sff")
FIGHT_DEF = os.path.join(ROOT, "data", "fight.def")
FONT = os.path.join(ROOT, "data", "ikemen1", "fonts", "Display.ttf")

GROUP = 20
HALF, H = 640, 260          # one half of the 1280x720 fight screen
SS = 4                      # supersample factor
SCREEN = 640                # screen centre

LIFE_Y = 2                  # the big bars, right at the top
BAR_Y = 30                  # the body band (power over audacity)
TIME_Y = 24                 # yin-yang centre
BAND = 20                   # height of the body band
METER_W = 202               # fillable length of the metre
BAR_X1 = 568                # p1.pos.x: inner end of the metre

# player two's big bar is the green dragon: shift the red skin across to green
P2_TINT = "-150, 90, -10"

RED = {
    "ink": (24, 5, 4), "dark": (86, 14, 10), "mid": (152, 34, 22),
    "skin": (188, 56, 34), "light": (214, 88, 54), "rim": (248, 152, 108),
    "belly": (224, 172, 124), "belly_lit": (246, 206, 158),
    "horn": (242, 226, 186), "eye": (255, 216, 78), "mouth": (46, 6, 4),
    "glow": (255, 84, 48), "whisker": (255, 212, 156),
    "back_top": (64, 12, 9), "back_low": (40, 8, 6),
}
GREEN = {
    "ink": (10, 18, 6), "dark": (34, 58, 22), "mid": (92, 128, 38),
    "skin": (124, 160, 52), "light": (156, 190, 72), "rim": (212, 240, 146),
    "belly": (206, 198, 132), "belly_lit": (238, 234, 178),
    "horn": (238, 232, 194), "eye": (255, 216, 78), "mouth": (16, 24, 10),
    "glow": (96, 255, 120), "whisker": (232, 250, 186),
    "back_top": (40, 60, 24), "back_low": (26, 40, 16),
}

# centre line of the animal across the 640-wide half: snout at the inner end,
# back running outward, tail tapering off to the left
SPINE = ((566, 40), (540, 40), (500, 39), (460, 39), (420, 40), (380, 40),
         (350, 40), (320, 39), (290, 37), (262, 36), (242, 35))
SPINE_R = (10.0, 9.8, 9.6, 9.4, 9.2, 9.0, 8.2, 6.6, 4.4, 2.4, 1.0)


def _mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[c] + (b[c] - a[c]) * t) for c in range(3))


def _curve(ctrl, n=14):
    """Catmull-Rom through the control points."""
    pts = [ctrl[0]] + list(ctrl) + [ctrl[-1]]
    out = []
    for i in range(len(pts) - 3):
        p0, p1, p2, p3 = pts[i:i + 4]
        for s in range(n):
            t = s / float(n)
            t2, t3 = t * t, t * t * t
            out.append(tuple(
                0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * t
                       + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                       + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3)
                for c in (0, 1)))
    out.append(tuple(pts[-2]))
    return out


def _spine(s):
    pts = [SPINE[0]] + list(SPINE) + [SPINE[-1]]
    rad = [SPINE_R[0]] + list(SPINE_R) + [SPINE_R[-1]]
    out = []
    for i in range(len(pts) - 3):
        p0, p1, p2, p3 = pts[i:i + 4]
        r0, r1, r2, r3 = rad[i:i + 4]
        for k in range(14):
            t = k / 14.0
            t2, t3 = t * t, t * t * t

            def cr(a, b, c, d):
                return 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2
                              + (-a + 3 * b - 3 * c + d) * t3)
            out.append((cr(p0[0], p1[0], p2[0], p3[0]) * s,
                        cr(p0[1], p1[1], p2[1], p3[1]) * s,
                        max(0.6, cr(r0, r1, r2, r3)) * s))
    return out


def _taper(d, pts, w0, w1, fill, outline=None, ow=2):
    segs = max(1, len(pts) - 1)
    for pass_no in (0, 1):
        for i in range(segs):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            steps = max(4, int(math.hypot(x1 - x0, y1 - y0) * 0.9))
            for k in range(steps + 1):
                t = k / float(steps)
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                r = (w0 + (w1 - w0) * ((i + t) / segs)) / 2.0
                if pass_no == 0:
                    if not outline:
                        continue
                    r += ow
                d.ellipse([x - r, y - r, x + r, y + r],
                          fill=outline if pass_no == 0 else fill)


# --------------------------------------------------------------- big bars
def paint_back(w, h, pal, frame=False):
    """The big bar as the dragon's scaled back: gradient, ink rim, belly band."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(h):
        k = y / float(h - 1)
        if frame:
            col = _mix(pal["ink"], (12, 6, 8), k)
        else:
            col = _mix(pal["back_top"], pal["back_low"], k)
            if k > 0.62:                       # underbelly peeking out
                col = _mix(col, pal["mid"], (k - 0.62) / 0.38 * 0.55)
        d.line([(0, y), (w - 1, y)], fill=col + (255,))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1],
                                           radius=h // 2, fill=255)
    img.putalpha(mask)
    # scales along the back
    if not frame:
        for x in range(8, w - 8, 13):
            d.line([(x, 2), (x + 5, h * 0.34)], fill=pal["ink"] + (70,))
            d.line([(x + 5, h * 0.34), (x + 10, 2)], fill=pal["rim"] + (40,))
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2,
                        outline=pal["ink"] + (255,), width=2)
    return img


def paint_fill(w, h, pal, level):
    """Health fill: bright skin at full health down to dull scale when low."""
    hi = [pal["rim"], pal["light"], pal["skin"], pal["mid"]][level]
    lo = [pal["light"], pal["skin"], pal["mid"], pal["dark"]][level]
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(h):
        k = y / float(h - 1)
        col = _mix(hi, lo, k * 0.85)
        if k > 0.70:
            col = _mix(col, pal["belly"], (k - 0.70) / 0.30 * 0.85)
        d.line([(0, y), (w - 1, y)], fill=col + (255,))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1],
                                           radius=h // 2, fill=255)
    img.putalpha(mask)
    for x in range(6, w - 6, 15):
        d.line([(x, 2), (x + 6, h * 0.45)], fill=pal["ink"] + (55,))
    d.line([(0, 1), (w, 1)], fill=pal["rim"] + (150,), width=1)
    return img


def build_bigbars(by_key):
    """Repaint the big bar sprites, keeping the sizes and axes the engine uses."""
    def meta(key, fallback):
        sp = by_key.get(key)
        return ((sp["w"], sp["h"]), sp["axis"]) if sp else (fallback, None)

    out = {}
    for key, frame, fallback in (((10, 0), False, (435, 24)),
                                 ((11, 0), True, (439, 28)),
                                 ((12, 0), False, (435, 24))):
        (w, h), axis = meta(key, fallback)
        out[key] = (paint_back(w, h, RED, frame=frame), axis or (w, 0))
    for i, level in enumerate((0, 1, 2, 3)):
        key = (13, i)
        (w, h), axis = meta(key, (435, 24))
        out[key] = (paint_fill(w, h, RED, level), axis or (w, 0))
    return out


# ------------------------------------------------------------- body band
def paint_meter(pal, lit, label=None):
    """One metre sprite: skin on the top half, belly on the bottom half."""
    w, h = METER_W + 4, BAND
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(h):
        k = y / float(h - 1)
        if k < 0.5:
            t = k / 0.5
            a = pal["rim"] if lit else pal["mid"]
            b = pal["light"] if lit else pal["skin"]
            col = _mix(a, b, t)
        else:
            t = (k - 0.5) / 0.5
            a = pal["belly_lit"] if lit else pal["belly"]
            b = pal["belly"] if lit else pal["dark"]
            col = _mix(a, b, t)
        d.line([(0, y), (w - 1, y)], fill=col + (255,))
    d.rectangle([0, 0, w - 1, h - 1], outline=pal["ink"] + (255,), width=1)
    d.line([(0, h // 2), (w - 1, h // 2)],
           fill=(pal["ink"] + (150,)) if not lit else (pal["ink"] + (90,)))
    if label:
        font = ImageFont.truetype(FONT, int(h * 0.46))
        box = d.textbbox((0, 0), label, font=font)
        d.text(((w - (box[2] - box[0])) / 2, h * 0.56 - box[1]), label,
               font=font, fill=(16, 22, 12, 235))
    return img


def build_meters(by_key):
    """The four body-band sprites, all BAND pixels tall, axes preserved."""
    def axis(key, fallback):
        sp = by_key.get(key)
        return sp["axis"] if sp else fallback

    out = {}
    out[(40, 0)] = (paint_meter(RED, lit=False), axis((40, 0), (METER_W + 4, 0)))
    out[(41, 0)] = (Image.new("RGBA", (METER_W + 4, BAND), (0, 0, 0, 0)),
                    axis((41, 0), (METER_W + 4, 0)))
    out[(43, 0)] = (paint_meter(RED, lit=True), axis((43, 0), (METER_W, 0)))
    out[(44, 0)] = (paint_meter(RED, lit=True, label="AUDACITY"),
                    axis((44, 0), (METER_W, 0)))
    return out


# ----------------------------------------------------------------- head
def _head(img, pal, s):
    """A bold little profile head at the inner end, looking at the timer."""
    d = ImageDraw.Draw(img)

    def P(x, y):
        return (x * s, y * s)

    d.polygon([P(540, 30), P(566, 30), P(566, 52), P(540, 52)],
              fill=pal["skin"])
    d.polygon([P(558, 32), P(592, 31), P(604, 35), P(610, 41), P(602, 52),
               P(558, 52)], fill=pal["skin"], outline=pal["ink"],
              width=int(1.4 * s))
    d.polygon([P(596, 35), P(613, 39), P(613, 45), P(596, 47)],
              fill=pal["light"], outline=pal["ink"])
    d.polygon([P(558, 33), P(590, 32), P(592, 38), P(558, 39)], fill=pal["mid"])
    d.polygon([P(558, 45), P(610, 43), P(602, 51), P(558, 51)],
              fill=pal["mouth"])
    for x in (562, 572, 582, 592):
        d.polygon([P(x, 45), P(x + 7, 44.5), P(x + 3.5, 51)],
                  fill=pal["horn"])
    d.polygon([P(556, 49), P(602, 49), P(594, 54), P(556, 54)],
              fill=pal["belly"], outline=pal["ink"])
    d.ellipse([P(570, 35)[0], P(570, 35)[1], P(583, 44)[0], P(583, 44)[1]],
              fill=pal["eye"], outline=pal["ink"])
    d.ellipse([P(575, 37)[0], P(575, 37)[1], P(581, 42)[0], P(581, 42)[1]],
              fill=pal["ink"])
    d.ellipse([P(605, 40)[0], P(605, 40)[1], P(609, 43)[0], P(609, 43)[1]],
              fill=pal["ink"])
    _taper(d, _curve([P(566, 32), P(550, 29), P(534, 31), P(524, 35)], 10),
           4.2 * s, 1.0 * s, pal["horn"], pal["ink"])
    _taper(d, _curve([P(576, 31.5), P(560, 28.5), P(546, 31)], 10),
           2.6 * s, 0.8 * s, pal["horn"], pal["ink"])
    for dy, ln, lift in ((32, 20, -1.5), (37, 22, 1.0), (43, 18, 2.5)):
        base = P(556, dy)
        pts = [base, (base[0] - ln * 0.5 * s, base[1] + lift * 0.7 * s),
               (base[0] - ln * s, base[1] + lift * 1.4 * s)]
        _taper(d, _curve(pts, 10), 4.4 * s, 0.9 * s, pal["light"], pal["ink"])
    _taper(d, _curve([P(613, 42), P(600, 47), P(586, 50)], 10),
           1.6 * s, 0.4 * s, pal["whisker"])


def _body(img, pal, s):
    line = _spine(s)
    d = ImageDraw.Draw(img)
    top = [(x, y - r) for x, y, r in line]
    bot = [(x, y + r) for x, y, r in reversed(line)]
    poly = top + bot
    d.polygon(poly, fill=pal["ink"])
    inner = [(x, y - r + 1.6 * s) for x, y, r in line]
    inner += [(x, y + r - 1.6 * s) for x, y, r in reversed(line)]
    d.polygon(inner, fill=pal["skin"])
    split = [(x, y + r * 0.06) for x, y, r in line]
    belly = [(x, y + r - 1.6 * s) for x, y, r in reversed(line)]
    d.polygon(split + belly, fill=pal["belly"])
    _taper(d, [(x, y + r * 0.08) for x, y, r in line], 2.6 * s, 1.4 * s,
           pal["belly_lit"])
    for fx, height in ((0.42, 4.2), (0.30, 3.6), (0.20, 2.8)):
        i = int(fx * (len(line) - 1))
        x, y, r = line[i]
        d.polygon([(x - r * 0.9, y - r + 1.5 * s),
                   (x - r * 0.1, y - r - height * s),
                   (x + r * 0.9, y - r + 1.5 * s)], fill=pal["mid"])


def _backdrop(img, pal, s):
    d = ImageDraw.Draw(img)
    for y in range(int(56 * s)):
        k = y / (56.0 * s)
        alpha = int(210 * (1.0 - k) ** 1.6)
        d.rectangle([0, y, img.width, y], fill=(6, 8, 20, alpha))
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([(SCREEN - 150) * s, -30 * s, (SCREEN + 150) * s, 52 * s],
               fill=pal["glow"] + (40,))
    glow = glow.filter(ImageFilter.GaussianBlur(9 * s))
    img.alpha_composite(glow)


def paint_half(pal, flip):
    w, h = HALF * SS, H * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    _backdrop(img, pal, SS)
    _body(img, pal, SS)
    _head(img, pal, SS)
    if flip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img.resize((HALF, H), Image.LANCZOS)


# ------------------------------------------------------------------ defs
def _write_sprites(painted):
    raw, sprites, palettes = sff.read_sff(FIGHT_SFF)
    out, done = [], set()
    for sp in sprites:
        key = (sp["group"], sp["number"])
        if key in painted:
            image, axis = painted[key]
            out.append({"group": key[0], "number": key[1], "image": image,
                        "axis": axis})
            done.add(key)
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"],
                        "link": sp["link"]})
    for key, (image, axis) in painted.items():
        if key not in done:
            out.append({"group": key[0], "number": key[1], "image": image,
                        "axis": axis})
            done.add(key)
    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: built fight.sff has no signature")
    with open(FIGHT_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(FIGHT_SFF + ".tmp", FIGHT_SFF)
    return sorted(done)


def _section(lines, name):
    start = next((i for i, ln in enumerate(lines)
                  if ln.strip().lower() == "[" + name.lower() + "]"), None)
    if start is None:
        raise SystemExit("data/fight.def has no [%s] section" % name)
    end = next((j for j in range(start + 1, len(lines))
                if lines[j].lstrip().startswith("[")), len(lines))
    return start, end


def _set(body, key, value):
    pat = re.compile(r"(?m)^(\s*)%s\s*=.*$" % re.escape(key))
    if pat.search(body):
        return pat.sub(lambda m: "%s%s = %s" % (m.group(1), key, value), body)
    return body.rstrip("\n") + "\n%s = %s" % (key, value)


def patch_def():
    with open(FIGHT_DEF, encoding="utf-8", errors="surrogateescape",
              newline="") as f:
        lines = f.read().split("\n")

    # --- big bars on top, banner halves anchored at the screen's top corners --
    s, e = _section(lines, "Lifebar")
    body = "\n".join(lines[s:e])
    for side, x in (("p1", 595), ("p2", 684)):
        body = _set(body, "%s.pos" % side, "%d,%d" % (x, LIFE_Y))
        body = _set(body, "%s.bg1.spr" % side,
                    "%d,%d" % (GROUP, 0 if side == "p1" else 1))
        body = _set(body, "%s.bg1.offset" % side,
                    "%d,%d" % ((0 if side == "p1" else 640) - x, -LIFE_Y))
        body = _set(body, "%s.bg1.xshear" % side, "0")
        body = _set(body, "%s.bg0.xshear" % side, "0")
        body = _set(body, "%s.top.xshear" % side, "0")
        body = _set(body, "%s.mid.xshear" % side, "0")
        for name in ("front100", "front50", "front25", "front"):
            body = _set(body, "%s.%s.xshear" % (side, name), "0")
        if side == "p2":
            # player two is the green dragon
            for name in ("bg0", "top", "mid", "front100", "front50",
                         "front25", "front"):
                body = _set(body, "%s.%s.palfx.add" % (side, name), P2_TINT)
    lines[s:e] = body.split("\n")

    # --- the body band: skin over belly, right under the big bars ---
    s, e = _section(lines, "Powerbar")
    body = "\n".join(lines[s:e])
    for side, x in (("p1", BAR_X1), ("p2", 712)):
        body = _set(body, "%s.pos" % side, "%d,%d" % (x, BAR_Y))
        body = _set(body, "%s.bg0.offset" % side, "0,0")
        body = _set(body, "%s.bg1.offset" % side, "0,0")
        for name in ("front", "front500", "front1000", "front2000", "front3000",
                     "front4000", "front5000", "front6000", "front7000",
                     "front8000", "front9000", "front10000"):
            body = _set(body, "%s.%s.offset" % (side, name),
                        "%d,0" % (4 if side == "p2" else -4))
        body = _set(body, "%s.frontMax.offset" % side,
                    "%d,0" % (208 if side == "p2" else -4))
    body = re.sub(r"(?m)^(\s*p[12]\.counter\w*\.offset\s*=\s*)(-?\d+),\s*-?\d+\s*$",
                  lambda m: "%s%s,%d" % (m.group(1), m.group(2), BAND + 1), body)
    lines[s:e] = body.split("\n")

    # --- yin-yang and digits, small, at dead centre ---
    s, e = _section(lines, "Time")
    body = "\n".join(lines[s:e])
    body = re.sub(r"(?m)^(\s*pos\s*=\s*).*$",
                  lambda m: "%s%d,%d" % (m.group(1), SCREEN, TIME_Y), body)
    body = _set(body, "bg.offset", "0,0")
    body = re.sub(r"(?m)^(\s*counter\w*\.offset\s*=\s*)(-?\d+),\s*-?\d+\s*$",
                  lambda m: "%s%s,%d" % (m.group(1), m.group(2), -4), body)
    body = re.sub(r"(?m)^(\s*counter\w*\.scale\s*=\s*)\d+(\.\d+)?\s*,\s*\d+(\.\d+)?\s*$",
                  lambda m: "%s0.55, 0.55" % m.group(1), body)
    lines[s:e] = body.split("\n")

    # --- the score readout clears the bars ---
    s, e = _section(lines, "Score")
    body = "\n".join(lines[s:e])
    body = _set(body, "p1.pos", "586,%d" % (LIFE_Y + BAND + 12))
    body = _set(body, "p2.pos", "696,%d" % (LIFE_Y + BAND + 12))
    lines[s:e] = body.split("\n")

    with open(FIGHT_DEF + ".tmp", "w", encoding="utf-8",
              errors="surrogateescape", newline="") as f:
        f.write("\n".join(lines))
    os.replace(FIGHT_DEF + ".tmp", FIGHT_DEF)


def _concept_path():
    base = os.path.join(ROOT, "concept_art", "ui")
    for name in ("banner", "vs_banner", "hud_banner"):
        for ext in ("png", "PNG", "jpg", "JPG", "jpeg", "JPEG", "webp",
                    "WEBP"):
            p = os.path.join(base, name + "." + ext)
            if os.path.isfile(p):
                return p
    return None


def _from_concept(path):
    src = Image.open(path).convert("RGBA")
    box = src.split()[3].getbbox() or (0, 0, src.width, src.height)
    art_img = src.crop(box).resize((HALF * 2, H), Image.LANCZOS)
    print("banner cut from %s" % os.path.relpath(path, ROOT))
    return (art_img.crop((0, 0, HALF, H)),
            art_img.crop((HALF, 0, HALF * 2, H)))


def main():
    if not os.path.isfile(FIGHT_SFF):
        raise SystemExit("data/fight.sff is missing")

    _d, before, _p = sff.read_sff(FIGHT_SFF)
    by_key = {(s["group"], s["number"]): s for s in before}

    concept = _concept_path()
    if concept:
        left, right = _from_concept(concept)
    else:
        left = paint_half(RED, flip=False)
        right = paint_half(GREEN, flip=True)

    painted = {(GROUP, 0): (left, (0, 0)), (GROUP, 1): (right, (0, 0))}
    painted.update(build_bigbars(by_key))
    painted.update(build_meters(by_key))
    written = _write_sprites(painted)
    patch_def()

    _d2, after, _p2 = sff.read_sff(FIGHT_SFF)
    have = {(s["group"], s["number"]): s for s in after}
    for key, (img, _axis) in painted.items():
        sp = have.get(key)
        if sp is None:
            raise SystemExit("sprite %d,%d went missing" % key)
        if (sp["w"], sp["h"]) != (img.width, img.height):
            raise SystemExit("sprite %d,%d is %dx%d, expected %dx%d" % (
                key[0], key[1], sp["w"], sp["h"], img.width, img.height))

    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    strip = Image.new("RGBA", (HALF * 2, 84), (0, 0, 0, 0))
    strip.alpha_composite(left.crop((0, 0, HALF, 84)), (0, 0))
    strip.alpha_composite(right.crop((0, 0, HALF, 84)), (HALF, 0))
    strip.convert("RGB").save(os.path.join(ROOT, "artifacts", "vs_banner.png"))
    print("top strip: sprites %s, bars y %d, band y %d, timer y %d" % (
        written, LIFE_Y, BAR_Y, TIME_Y))


if __name__ == "__main__":
    main()
