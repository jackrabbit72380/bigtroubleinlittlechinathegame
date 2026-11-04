"""Build the top strip: one dragon per side, its body split into the two bars.

There is a single dragon each side, not a bar with a dragon drawn around it. The
animal's own body is the HUD:

    y  2..26   the top of the body  -> the big health bar   ([Lifebar])
    y 30..50   the underside/belly  -> the audacity bar     ([Powerbar])
    y  0..52   the head, turned in towards a glowing green/red yin-yang with the
               round timer counting down on it            ([Time])

So the health bar fills along the dragon's back and the audacity bar fills along
its belly - the bars are parts of the dragon, not rectangles laid over it. No
legs and no arms: back, belly, head, horns, mane and tail only.

Everything sits in the top ~52 pixels of the 1280x720 fight screen.

Sprites written into data/fight.sff:

    10,0 11,0 12,0 13,0..3   the dragon's back = the health bar
    40,0 41,0 43,0 44,0      the dragon's belly = the audacity bar
    20,0 / 20,1              the two bodies and tails, one per player
    30,0                     both heads + the yin-yang, drawn over the middle

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
HALF, H = 640, 60           # one half of the strip, anchored at the screen corner
SS = 4                      # supersample factor
SCREEN = 640                # screen centre

LIFE_Y = 2                  # top of the health bar = top of the dragon's back
LIFE_H = 24                 # height of the health band
BAR_Y = 30                  # top of the belly band
BAND = 20                   # height of the belly band
TIME_Y = 26                 # yin-yang centre
METER_W = 202               # fillable length of the audacity bar
BAR_X1 = 568                # p1.pos.x: inner end of the audacity bar

P2_TINT = "-150, 90, -10"   # player two is the green dragon

RED = {
    "ink": (24, 5, 4), "dark": (78, 12, 9), "mid": (146, 32, 20),
    "skin": (186, 54, 32), "light": (214, 88, 54), "rim": (250, 158, 112),
    "belly": (222, 168, 118), "belly_lit": (248, 208, 158),
    "horn": (244, 228, 188), "eye": (255, 216, 78), "mouth": (44, 6, 4),
    "glow": (255, 84, 48), "whisker": (255, 212, 156),
    "back_top": (60, 11, 8), "back_low": (38, 7, 5),
}
GREEN = {
    "ink": (10, 18, 6), "dark": (30, 52, 20), "mid": (88, 124, 36),
    "skin": (124, 160, 52), "light": (158, 192, 74), "rim": (214, 242, 148),
    "belly": (204, 196, 130), "belly_lit": (240, 236, 180),
    "horn": (238, 232, 194), "eye": (255, 216, 78), "mouth": (16, 24, 10),
    "glow": (96, 255, 120), "whisker": (232, 250, 186),
    "back_top": (38, 58, 22), "back_low": (24, 38, 14),
}


def _mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[c] + (b[c] - a[c]) * t) for c in range(3))


def _curve(ctrl, n=14):
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


# ------------------------------------------------------------- the body art
# the dragon's back runs along the top band and its tail sweeps off to the side
SPINE = ((594, 26), (560, 26), (500, 25), (440, 25), (380, 26), (330, 27),
         (290, 26), (250, 22), (200, 15), (150, 10), (118, 9))
SPINE_R = (24.0, 24.0, 23.0, 22.0, 21.0, 19.0, 15.0, 11.0, 7.0, 3.5, 1.5)


def paint_body_half(pal, flip):
    """The dragon behind the bars: back, belly line, tail. No legs, no head."""
    w, h = HALF * SS, H * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    line = []
    n = 12
    for i in range(len(SPINE) - 1):
        (x0, y0), (x1, y1) = SPINE[i], SPINE[i + 1]
        r0, r1 = SPINE_R[i], SPINE_R[i + 1]
        for k in range(n):
            t = k / float(n)
            line.append(((x0 + (x1 - x0) * t) * SS, (y0 + (y1 - y0) * t) * SS,
                         (r0 + (r1 - r0) * t) * SS))
    top = [(x, y - r) for x, y, r in line]
    bot = [(x, y + r) for x, y, r in reversed(line)]
    d.polygon(top + bot, fill=pal["ink"])
    inset = 1.6 * SS
    d.polygon([(x, y - r + inset) for x, y, r in line]
              + [(x, y + r - inset) for x, y, r in reversed(line)],
              fill=pal["skin"])
    # underside, lighter, split from the back along the middle of the body
    d.polygon([(x, y + r * 0.30) for x, y, r in line]
              + [(x, y + r - inset) for x, y, r in reversed(line)],
              fill=pal["belly"])
    _taper(d, [(x, y + r * 0.34) for x, y, r in line], 2.4 * SS, 1.2 * SS,
           pal["belly_lit"])
    # scales down the back, and the dorsal fin along the top edge
    for i in range(4, len(line) - 4, 3):
        x, y, r = line[i]
        d.line([(x, y - r + inset), (x + 5 * SS, y - r * 0.2)],
               fill=pal["ink"] + (60,))
    for fx in (0.30, 0.42, 0.55):
        i = int(fx * (len(line) - 1))
        x, y, r = line[i]
        d.polygon([(x - r * 0.5, y - r + inset), (x, y - r - 5 * SS),
                   (x + r * 0.5, y - r + inset)], fill=pal["mid"])
    if flip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img.resize((HALF, H), Image.LANCZOS)


# ------------------------------------------------- the bars, as body parts
def _band(w, h, pal, kind, lit, label=None):
    """One bar sprite shaped as part of the dragon's body."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(h):
        k = y / float(h - 1)
        if kind == "back":
            if lit:
                col = _mix(pal["rim"], pal["light"], k * 0.7)
                if k > 0.65:
                    col = _mix(col, pal["skin"], (k - 0.65) / 0.35)
            else:
                col = _mix(pal["back_top"], pal["back_low"], k)
                if k > 0.6:
                    col = _mix(col, pal["mid"], (k - 0.6) / 0.4 * 0.5)
        else:
            if lit:
                col = _mix(pal["belly_lit"], pal["belly"], k)
            else:
                col = _mix(pal["belly"], pal["dark"], k)
        d.line([(0, y), (w - 1, y)], fill=col + (255,))
    # shape: the top of the body is round, the belly of the body is round
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    if kind == "back":
        md.rounded_rectangle([0, 0, w - 1, h * 2 - 1], radius=h, fill=255)
    else:
        md.rounded_rectangle([0, -h + 1, w - 1, h - 1], radius=h, fill=255)
    # taper the outer end into the tail
    if kind == "back":
        fade = max(1, int(w * 0.14))
        px = mask.load()
        for x in range(fade):
            f = x / float(fade)
            for y in range(h):
                px[x, y] = int(px[x, y] * f ** 0.7)
    img.putalpha(mask)
    d = ImageDraw.Draw(img)
    if kind == "back":
        for x in range(int(w * 0.16), w - 6, 15):
            d.line([(x, 3), (x + 6, h * 0.55)], fill=pal["ink"] + (55,))
        d.line([(0, 1), (w, 1)], fill=pal["ink"] + (170,), width=1)
    else:
        d.line([(0, h - 2), (w, h - 2)], fill=pal["ink"] + (150,), width=1)
    if label:
        font = ImageFont.truetype(FONT, int(h * 0.46))
        box = d.textbbox((0, 0), label, font=font)
        d.text(((w - (box[2] - box[0])) / 2, h * 0.52 - box[1]), label,
               font=font, fill=(18, 24, 14, 235))
    return img


def build_bigbars(by_key):
    """Health bar sprites -> the dragon's back."""
    def meta(key, fallback):
        sp = by_key.get(key)
        return ((sp["w"], sp["h"]), sp["axis"]) if sp else (fallback, None)

    out = {}
    for key, lit, fallback in (((10, 0), False, (435, 24)),
                               ((12, 0), False, (435, 24))):
        (w, h), axis = meta(key, fallback)
        out[key] = (_band(w, h, RED, "back", lit), axis or (w, 0))
    (w, h), axis = meta((11, 0), (439, 28))
    frame = _band(w, h, RED, "back", False)
    ImageDraw.Draw(frame).rounded_rectangle(
        [0, 0, w - 1, h - 1], radius=h // 2 - 2,
        outline=RED["ink"] + (255,), width=2)
    out[(11, 0)] = (frame, axis or (w, 0))
    for i, lit in enumerate((True, True, True, True)):
        key = (13, i)
        (w, h), axis = meta(key, (435, 24))
        out[key] = (_band(w, h, RED, "back", True), axis or (w, 0))
    return out


def build_meters(by_key):
    """Audacity bar sprites -> the dragon's belly."""
    def axis(key, fallback):
        sp = by_key.get(key)
        return sp["axis"] if sp else fallback

    def size(key, fallback):
        sp = by_key.get(key)
        return (sp["w"], sp["h"]) if sp else fallback

    out = {}
    out[(40, 0)] = (_band(*size((40, 0), (METER_W + 4, BAND)), RED, "belly",
                          False), axis((40, 0), (METER_W + 4, 0)))
    out[(41, 0)] = (Image.new("RGBA", size((41, 0), (METER_W + 4, BAND)),
                              (0, 0, 0, 0)), axis((41, 0), (METER_W + 4, 0)))
    out[(43, 0)] = (_band(*size((43, 0), (METER_W, BAND)), RED, "belly", True),
                    axis((43, 0), (METER_W, 0)))
    out[(44, 0)] = (_band(*size((44, 0), (METER_W, BAND)), RED, "belly", True,
                          label="AUDACITY"),
                    axis((44, 0), (METER_W, 0)))
    return out


# ---------------------------------------------------- heads + yin-yang timer
HEAD_W, HEAD_H = 88, 56


def _head_layer(pal, s):
    """A dragon head facing right, on its own layer."""
    img = Image.new("RGBA", (int(HEAD_W * s), int(HEAD_H * s)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def P(x, y):
        return (x * s, y * s)

    # neck stub, then skull and snout
    d.polygon([P(0, 12), P(22, 8), P(26, 46), P(0, 44)], fill=pal["skin"])
    d.polygon([P(18, 6), P(58, 4), P(70, 12), P(74, 24), P(64, 46), P(18, 46)],
              fill=pal["skin"], outline=pal["ink"], width=int(1.3 * s))
    d.polygon([P(62, 14), P(86, 20), P(86, 30), P(62, 34)], fill=pal["light"],
              outline=pal["ink"])
    # brow and eye
    d.polygon([P(18, 7), P(56, 5), P(58, 18), P(18, 19)], fill=pal["mid"])
    d.ellipse([P(34, 16)[0], P(34, 16)[1], P(50, 30)[0], P(50, 30)[1]],
              fill=pal["eye"], outline=pal["ink"])
    d.ellipse([P(41, 19)[0], P(41, 19)[1], P(49, 27)[0], P(49, 27)[1]],
              fill=pal["ink"])
    # open mouth, teeth, lower jaw
    d.polygon([P(20, 32), P(84, 28), P(74, 44), P(20, 44)], fill=pal["mouth"])
    for x in (26, 38, 50, 62):
        d.polygon([P(x, 32), P(x + 8, 31), P(x + 4, 41)], fill=pal["horn"])
    d.polygon([P(16, 40), P(76, 38), P(66, 50), P(16, 50)],
              fill=pal["belly"], outline=pal["ink"])
    # nostril
    d.ellipse([P(78, 20)[0], P(78, 20)[1], P(83, 25)[0], P(83, 25)[1]],
              fill=pal["ink"])
    # horns swept back over the neck
    _taper(d, _curve([P(30, 6), P(14, -4), P(0, -2), P(-6, 6)], 12),
           5 * s, 1.2 * s, pal["horn"], pal["ink"])
    _taper(d, _curve([P(44, 4), P(28, -6), P(12, -3)], 12),
           3.2 * s, 0.9 * s, pal["horn"], pal["ink"])
    # mane
    for dy, ln, lift in ((10, 26, -2), (22, 30, 2), (34, 24, 5)):
        base = P(16, dy)
        pts = [base, (base[0] - ln * 0.5 * s, base[1] + lift * 0.7 * s),
               (base[0] - ln * s, base[1] + lift * 1.5 * s)]
        _taper(d, _curve(pts, 10), 5 * s, 1 * s, pal["light"], pal["ink"])
    # whisker
    _taper(d, _curve([P(86, 26), P(70, 34), P(52, 38)], 10),
           1.8 * s, 0.5 * s, pal["whisker"])
    return img


def _disc(pal, r, s):
    """The green/red yin-yang, glowing."""
    n = int(r * 2.8 * s)
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = n / 2.0
    rr = r * s
    half, dot = rr / 2.0, rr / 8.0
    green, red = (58, 255, 138), (255, 62, 52)
    d.ellipse([c - rr, c - rr, c + rr, c + rr], fill=red + (255,))
    d.pieslice([c - rr, c - rr, c + rr, c + rr], 90, 270, fill=green + (255,))
    d.ellipse([c - half, c - rr, c + half, c], fill=green + (255,))
    d.ellipse([c - half, c, c + half, c + rr], fill=red + (255,))
    d.ellipse([c - dot, c - half - dot, c + dot, c - half + dot],
              fill=red + (255,))
    d.ellipse([c - dot, c + half - dot, c + dot, c + half + dot],
              fill=green + (255,))
    d.ellipse([c - rr, c - rr, c + rr, c + rr],
              outline=(255, 226, 160, 235), width=max(1, round(1.4 * s)))
    halo = img.filter(ImageFilter.GaussianBlur(4.0 * s))
    alpha = halo.split()[3].point(lambda v: min(255, round(v * 2.0)))
    halo.putalpha(alpha)
    out = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    out.alpha_composite(halo)
    out.alpha_composite(img)
    return out


def build_timer():
    """Both heads facing in, with the yin-yang between them, drawn over the HUD.

    A 320x100 sprite: heads sit outside the bars' inner ends so they are not
    hidden behind the health bar, and the disc is dead centre.
    """
    w, h = 320, 100
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    s = SS
    head = _head_layer(RED, s)
    img.alpha_composite(head, (int(56 * s), int(0 * s)))
    green = _head_layer(GREEN, s).transpose(Image.FLIP_LEFT_RIGHT)
    img.alpha_composite(green, (int((188) * s), int(0 * s)))
    disc = _disc(RED, 28, s)
    dw = disc.width // s
    img.alpha_composite(disc, (int((160 - dw / 2) * s), int((52 - dw / 2) * s)))
    return img.resize((w, h), Image.LANCZOS), (160, 50)


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

    # --- the health bar is the top of the dragon, anchored at the screen's top
    s, e = _section(lines, "Lifebar")
    body = "\n".join(lines[s:e])
    for side, x in (("p1", 595), ("p2", 684)):
        body = _set(body, "%s.pos" % side, "%d,%d" % (x, LIFE_Y))
        body = _set(body, "%s.bg1.spr" % side,
                    "%d,%d" % (GROUP, 0 if side == "p1" else 1))
        body = _set(body, "%s.bg1.offset" % side,
                    "%d,%d" % ((0 if side == "p1" else HALF) - x, -LIFE_Y))
        for name in ("bg1", "bg0", "top", "mid", "front100", "front50",
                     "front25", "front"):
            if name != "bg1.spr" and name != "bg1.offset":
                body = _set(body, "%s.%s.xshear" % (side, name), "0")
        if side == "p2":
            for name in ("bg0", "top", "mid", "front100", "front50",
                         "front25", "front"):
                body = _set(body, "%s.%s.palfx.add" % (side, name), P2_TINT)
    lines[s:e] = body.split("\n")

    # --- the audacity bar is the underside, right beneath it
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
        if side == "p2":
            for name in ("bg0", "front500", "front1000", "front2000",
                         "front3000", "front4000", "front5000", "front6000",
                         "front7000", "front8000", "front9000", "front10000",
                         "frontMax"):
                body = _set(body, "%s.%s.palfx.add" % (side, name), P2_TINT)
    body = re.sub(r"(?m)^(\s*p[12]\.counter\w*\.offset\s*=\s*)(-?\d+),\s*-?\d+\s*$",
                  lambda m: "%s%s,%d" % (m.group(1), m.group(2), BAND + 1), body)
    lines[s:e] = body.split("\n")

    # --- the heads and the disc sit on [Time], above the bars
    s, e = _section(lines, "Time")
    body = "\n".join(lines[s:e])
    body = re.sub(r"(?m)^(\s*pos\s*=\s*).*$",
                  lambda m: "%s%d,%d" % (m.group(1), SCREEN, TIME_Y), body)
    body = _set(body, "bg.spr", "30,0")
    body = _set(body, "bg.offset", "0,0")
    body = re.sub(r"(?m)^(\s*counter\w*\.offset\s*=\s*)(-?\d+),\s*-?\d+\s*$",
                  lambda m: "%s%s,%d" % (m.group(1), m.group(2), -4), body)
    body = re.sub(r"(?m)^(\s*counter\w*\.scale\s*=\s*)\d+(\.\d+)?\s*,\s*\d+(\.\d+)?\s*$",
                  lambda m: "%s0.55, 0.55" % m.group(1), body)
    lines[s:e] = body.split("\n")

    # --- the score readout clears the strip
    s, e = _section(lines, "Score")
    body = "\n".join(lines[s:e])
    body = _set(body, "p1.pos", "586,%d" % (BAR_Y + BAND + 10))
    body = _set(body, "p2.pos", "696,%d" % (BAR_Y + BAND + 10))
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


def main():
    if not os.path.isfile(FIGHT_SFF):
        raise SystemExit("data/fight.sff is missing")

    _d, before, _p = sff.read_sff(FIGHT_SFF)
    by_key = {(s["group"], s["number"]): s for s in before}

    painted = {(GROUP, 0): (paint_body_half(RED, False), (0, 0)),
               (GROUP, 1): (paint_body_half(GREEN, True), (0, 0))}
    painted.update(build_bigbars(by_key))
    painted.update(build_meters(by_key))
    timer, axis = build_timer()
    painted[(30, 0)] = (timer, axis)
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
    strip = Image.new("RGBA", (HALF * 2, 64), (0, 0, 0, 0))
    for key, x in (((GROUP, 0), 0), ((GROUP, 1), HALF)):
        strip.alpha_composite(painted[key][0].crop((0, 0, HALF, 64)), (x, 0))
    strip.convert("RGB").save(os.path.join(ROOT, "artifacts", "vs_banner.png"))
    print("strip: sprites %s, back y %d, belly y %d, heads/timer y %d" % (
        written, LIFE_Y, BAR_Y, TIME_Y))


if __name__ == "__main__":
    main()
