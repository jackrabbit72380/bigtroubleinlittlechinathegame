"""Restore the VS dragon and make its own body carry the two bars.

The dragon geometry here - the body curve, the crest plates, the dorsal fins and
the head with its horns, mane, teeth and whiskers - is the version that was
approved earlier, carried over from tools/build_banner.py at 92d7ff0. The only
changes are the ones asked for: the legs and claws are gone, the body is slimmer,
and the back is flattened so the dragon lies along the top of the screen.

One dragon per side, and its body IS the HUD:

    y  2..26   top of the body      -> big health bar        ([Lifebar])
    y 30..50   underside / belly    -> audacity bar          ([Powerbar])
    y  0..52   head at dead centre, turned in to the glowing green/red
               yin-yang with the round timer on it          ([Time])

The head is drawn on the [Time] layer so it sits over the bar ends rather than
being hidden behind them, and the tail sweeps out towards the screen edge.

Sprites written into data/fight.sff:

    10,0 11,0 12,0 13,0..3   the back   = health bar
    40,0 41,0 43,0 44,0      the belly  = audacity bar
    20,0 / 20,1              the body and tail, one per player
    30,0                     both heads + the yin-yang

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
TIMER_GROUP = 30
HALF, H = 640, 60           # one half of the strip, anchored at the screen corner
SS = 4                      # supersample factor
SCREEN = 640                # screen centre

LIFE_Y = 2                  # top of the health bar = top of the dragon's back
BAR_Y = 30                  # top of the audacity bar = the underside
BAND = 20                   # height of the audacity band
TIME_Y = 34                 # yin-yang centre
METER_W = 202               # fillable length of the audacity bar
BAR_X1 = 568                # p1.pos.x: inner end of the audacity bar

SPINE_Y = 25                # the dragon's centre line
BODY_R = 23                 # its half-thickness

P2_TINT = "-150, 90, -10"   # player two is the green dragon

RED = {
    "ink": (24, 5, 4), "dark": (78, 12, 9), "mid": (146, 32, 20),
    "skin": (186, 54, 32), "light": (214, 88, 54), "rim": (250, 158, 112),
    "belly": (222, 168, 118), "belly_lit": (248, 208, 158),
    "plate": (252, 240, 216),
    "horn": (244, 228, 188), "eye": (255, 216, 78), "mouth": (44, 6, 4),
    "glow": (255, 84, 48), "whisker": (255, 212, 156),
    "back_top": (60, 11, 8), "back_low": (38, 7, 5),
}
GREEN = {
    "ink": (10, 18, 6), "dark": (30, 52, 20), "mid": (88, 124, 36),
    "skin": (124, 160, 52), "light": (158, 192, 74), "rim": (214, 242, 148),
    "belly": (204, 196, 130), "belly_lit": (240, 236, 180),
    "plate": (246, 242, 214),
    "horn": (238, 232, 194), "eye": (255, 216, 78), "mouth": (16, 24, 10),
    "glow": (96, 255, 120), "whisker": (232, 250, 186),
    "back_top": (38, 58, 22), "back_low": (24, 38, 14),
}

# the approved body curve: tail at the outer end, a lazy rise and fall along the
# back, neck at the inner end where the head takes over
PATH = ((139, 30), (180, 33), (232, 29), (300, 24), (380, 22), (460, 24),
        (520, 28), (570, 26), (598, 25))
PATH_R = (1.5, 5.0, 11.0, 18.0, 22.0, 23.0, 21.0, 16.0, 9.0)

HEAD_JOINT = (480, 26)      # where the neck meets the skull


def _mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[c] + (b[c] - a[c]) * t) for c in range(3))


def _curve(ctrl, n=26):
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
    """Approved centre line and thickness profile, in device pixels."""
    pts, rad = PATH, PATH_R
    pad_p, pad_r = [pts[0]] + list(pts) + [pts[-1]], \
        [rad[0]] + list(rad) + [rad[-1]]
    out = []
    for i in range(len(pad_p) - 3):
        p0, p1, p2, p3 = pad_p[i:i + 4]
        r0, r1, r2, r3 = pad_r[i:i + 4]
        for k in range(26):
            t = k / 26.0
            t2, t3 = t * t, t * t * t

            def cr(a, b, c, d):
                return 0.5 * (2 * b + (-a + c) * t
                              + (2 * a - 5 * b + 4 * c - d) * t2
                              + (-a + 3 * b - 3 * c + d) * t3)
            out.append((cr(p0[0], p1[0], p2[0], p3[0]) * s,
                        cr(p0[1], p1[1], p2[1], p3[1]) * s,
                        max(0.8, cr(r0, r1, r2, r3)) * s))
    return out


def _taper(d, pts, w0, w1, fill, outline=None):
    """Stroke a tapered limb along a polyline."""
    for i in range(max(1, len(pts) - 1)):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        steps = max(4, int(math.hypot(x1 - x0, y1 - y0) * 0.8))
        for pass_no in (0, 1):
            for s in range(steps + 1):
                t = s / float(steps)
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                r = (w0 + (w1 - w0) * ((i + t) / max(1, len(pts) - 1))) / 2.0
                if pass_no == 0:
                    if not outline:
                        continue
                    d.ellipse([x - r - 1, y - r - 1, x + r + 1, y + r + 1],
                              fill=outline)
                elif not (outline and r <= 1):
                    d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def _body(img, line, pal):
    """The approved shaded body: dark underside, belly band, lit spine ridge."""
    d = ImageDraw.Draw(img)
    for x, y, r in line:
        d.ellipse([x - r, y - r, x + r, y + r], fill=pal["dark"])
    for x, y, r in line:
        d.ellipse([x - r * 0.95, y - r * 0.93 + r * 0.06,
                   x + r * 0.95, y + r * 0.93 + r * 0.06], fill=pal["mid"])
    for x, y, r in line:
        d.ellipse([x - r * 0.70, y + r * 0.10, x + r * 0.70, y + r * 0.94],
                  fill=pal["belly"])
    _taper(d, [(x, y - r * 0.68) for x, y, r in line], 5 * SS, 2 * SS,
           pal["rim"])


def _plates(img, line, pal):
    """The approved crest plates, sunk into the back of the body."""
    d = ImageDraw.Draw(img)
    n = len(line)
    step = max(4, n // 16)
    for i in range(4, n - 6, step):
        x, y, r = line[i]
        rr = r * 0.42
        cy = y - r * 0.18
        d.ellipse([x - rr, cy - rr, x + rr, cy + rr],
                  fill=pal["dark"] + (90,), outline=pal["plate"] + (170,),
                  width=int(max(1, 1.3 * SS)))
        d.arc([x - rr * 0.55, cy - rr * 0.55, x + rr * 0.55, cy + rr * 0.55],
              210, 330, fill=pal["rim"] + (140,), width=int(max(1, 0.9 * SS)))


def _spikes(img, line, pal, clip_top=0):
    """The approved dorsal fins, only where they are on screen."""
    d = ImageDraw.Draw(img)
    n = len(line)
    for i in range(5, n - 8, max(4, n // 14)):
        x, y, r = line[i]
        tip = y - r * 1.34
        if tip / SS < clip_top:
            continue
        d.polygon([(x - r * 0.40, y - r * 0.86), (x - r * 0.04, tip),
                   (x + r * 0.44, y - r * 0.86)],
                  fill=pal["mid"], outline=pal["ink"])


def _head(d, jx, jy, jr, pal):
    """The approved head, facing right so it looks in towards the timer."""
    s = SS

    _taper(d, [(jx - 46 * s, jy + 8 * s), (jx - 8 * s, jy + 2 * s)],
           jr * 1.9, jr * 1.7, pal["mid"], pal["ink"])

    def P(dx, dy):
        return (jx + dx * s, jy + dy * s)

    _taper(d, [P(-40, 16), P(-14, 6), P(4, 2)], 40 * s, 44 * s, pal["mid"],
           pal["ink"])
    d.ellipse([P(-6, -32)[0], P(-6, -32)[1], P(60, 30)[0], P(60, 30)[1]],
              fill=pal["light"], outline=pal["ink"], width=int(1.8 * s))
    d.polygon([P(4, -30), P(58, -24), P(52, -6), P(2, -12)],
              fill=pal["mid"], outline=pal["ink"])
    _taper(d, [P(44, -8), P(88, -6), P(116, 4)], 26 * s, 14 * s, pal["mid"],
           pal["ink"])
    _taper(d, [P(42, 14), P(84, 30), P(110, 22)], 20 * s, 10 * s,
           pal["light"], pal["ink"])
    d.polygon([P(46, 2), P(114, 6), P(106, 22), P(46, 16)], fill=pal["mouth"])
    for i in range(4):
        tx = 54 + i * 15
        d.polygon([P(tx, 2), P(tx + 8, 2), P(tx + 4, 13)], fill=pal["horn"])
    d.ellipse([P(12, -26)[0], P(12, -26)[1], P(34, -2)[0], P(34, -2)[1]],
              fill=pal["eye"], outline=pal["ink"], width=int(1.3 * s))
    d.ellipse([P(21, -19)[0], P(21, -19)[1], P(32, -7)[0], P(32, -7)[1]],
              fill=pal["ink"])
    _taper(d, _curve([P(10, -30), P(-26, -64), P(-62, -60), P(-84, -38)], 16),
           9 * s, 1.6 * s, pal["horn"], pal["ink"])
    _taper(d, _curve([P(2, -20), P(-30, -46), P(-58, -38)], 16),
           6 * s, 1.2 * s, pal["horn"], pal["ink"])
    for dy, ln, lift in ((-24, 62, -22), (-4, 58, 6), (16, 46, 20), (30, 34, 28)):
        base = P(-2, dy)
        pts = [base, (base[0] - ln * 0.45 * s, base[1] + lift * 0.55 * s),
               (base[0] - ln * 0.78 * s, base[1] + lift * 1.05 * s),
               (base[0] - ln * s, base[1] + (lift + 6) * s)]
        _taper(d, _curve(pts, 14), 13 * s, 2 * s, pal["light"], pal["ink"])
    d.ellipse([P(98, 0)[0], P(98, 0)[1], P(106, 8)[0], P(106, 8)[1]],
              fill=pal["ink"])
    _taper(d, _curve([P(80, 24), P(68, 48), P(42, 58)], 14), 10 * s, 1.6 * s,
           pal["light"], pal["ink"])
    for dy, dirn in ((-10, -1.0), (14, 1.0)):
        base = P(112, dy)
        pts = [base, (base[0] - 34 * s, base[1] + dirn * 12 * s),
               (base[0] - 70 * s, base[1] + dirn * 22 * s),
               (base[0] - 104 * s, base[1] + dirn * 16 * s)]
        _taper(d, _curve(pts, 16), 3.4 * s, 0.8 * s, pal["whisker"])


# --------------------------------------------------- the two halves and heads
def paint_body_half(pal, flip):
    """The dragon behind the bars: back, belly, plates, fins, tail."""
    w, h = HALF * SS, H * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    line = _spine(SS)
    _body(img, line, pal)
    _plates(img, line, pal)
    _spikes(img, line, pal, clip_top=0)
    if flip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img.resize((HALF, H), Image.LANCZOS)


def _disc(r, s):
    """The green/red yin-yang, glowing."""
    n = int(r * 2.6 * s)
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c, rr = n / 2.0, r * s
    half, dot = rr / 2.0, rr / 8.0
    green, red = (58, 255, 138, 255), (255, 62, 52, 255)
    d.ellipse([c - rr, c - rr, c + rr, c + rr], fill=red)
    d.pieslice([c - rr, c - rr, c + rr, c + rr], 90, 270, fill=green)
    d.ellipse([c - half, c - rr, c + half, c], fill=green)
    d.ellipse([c - half, c, c + half, c + rr], fill=red)
    d.ellipse([c - dot, c - half - dot, c + dot, c - half + dot], fill=red)
    d.ellipse([c - dot, c + half - dot, c + dot, c + half + dot], fill=green)
    d.ellipse([c - rr, c - rr, c + rr, c + rr],
              outline=(255, 226, 160, 235), width=max(1, round(1.4 * s)))
    halo = img.filter(ImageFilter.GaussianBlur(4.0 * s))
    alpha = halo.split()[3].point(lambda v: min(255, round(v * 2.0)))
    halo.putalpha(alpha)
    out = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    out.alpha_composite(halo)
    out.alpha_composite(img)
    return out


def paint_timer():
    """Both approved heads, scaled to the body, facing the yin-yang."""
    w, h = 400, 160
    JOINT = (105, 80)               # local anchor of the left head
    HALF_SCALE = 0.62               # the heads are drawn at twice this size
    big_w, big_h = 240, 140
    joint_big = (120, 70)

    def head_layer(pal, flip):
        layer = Image.new("RGBA", (big_w * SS, big_h * SS), (0, 0, 0, 0))
        _head(ImageDraw.Draw(layer), joint_big[0] * SS, joint_big[1] * SS,
              9 * SS, pal)
        layer = layer.resize((int(big_w * HALF_SCALE * SS),
                              int(big_h * HALF_SCALE * SS)), Image.LANCZOS)
        if flip:
            layer = layer.transpose(Image.FLIP_LEFT_RIGHT)
        return layer

    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    scale = (w * SS) / float(w)
    for pal, flip, jx in ((RED, False, JOINT[0]), (GREEN, True, 400 - JOINT[0])):
        layer = head_layer(pal, flip)
        img.alpha_composite(layer, (int(jx * SS - layer.width / 2),
                                    int(JOINT[1] * SS - layer.height / 2)))
    disc = _disc(28, SS)
    img.alpha_composite(disc, (int(200 * SS - disc.width / 2),
                               int(JOINT[1] * SS - disc.height / 2)))
    return img.resize((w, h), Image.LANCZOS), (200, JOINT[1])


# ------------------------------------------------------- the bars as body parts
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
            col = _mix(pal["belly_lit"], pal["belly"], k) if lit else \
                _mix(pal["belly"], pal["dark"], k)
        d.line([(0, y), (w - 1, y)], fill=col + (255,))
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    if kind == "back":
        md.rounded_rectangle([0, 0, w - 1, h * 2 - 1], radius=h, fill=255)
    else:
        md.rounded_rectangle([0, -h + 1, w - 1, h - 1], radius=h, fill=255)
    if kind == "back":
        fade = max(1, int(w * 0.14))
        px = mask.load()
        for x in range(fade):
            f = (x / float(fade)) ** 0.7
            for y in range(h):
                px[x, y] = int(px[x, y] * f)
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
    def meta(key, fallback):
        sp = by_key.get(key)
        return ((sp["w"], sp["h"]), sp["axis"]) if sp else (fallback, None)

    out = {}
    for key, fallback in (((10, 0), (435, 24)), ((12, 0), (435, 24))):
        (w, h), axis = meta(key, fallback)
        out[key] = (_band(w, h, RED, "back", False), axis or (w, 0))
    (w, h), axis = meta((11, 0), (439, 28))
    frame = _band(w, h, RED, "back", False)
    ImageDraw.Draw(frame).rounded_rectangle(
        [0, 0, w - 1, h - 1], radius=max(2, h // 2 - 2),
        outline=RED["ink"] + (255,), width=2)
    out[(11, 0)] = (frame, axis or (w, 0))
    for i in range(4):
        key = (13, i)
        (w, h), axis = meta(key, (435, 24))
        out[key] = (_band(w, h, RED, "back", True), axis or (w, 0))
    return out


def build_meters(by_key):
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
                          label="AUDACITY"), axis((44, 0), (METER_W, 0)))
    return out


# ------------------------------------------------------------------- sprite I/O
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
            body = _set(body, "%s.%s.xshear" % (side, name), "0")
        if side == "p2":
            for name in ("bg0", "top", "mid", "front100", "front50",
                         "front25", "front"):
                body = _set(body, "%s.%s.palfx.add" % (side, name), P2_TINT)
    lines[s:e] = body.split("\n")

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

    s, e = _section(lines, "Time")
    body = "\n".join(lines[s:e])
    body = re.sub(r"(?m)^(\s*pos\s*=\s*).*$",
                  lambda m: "%s%d,%d" % (m.group(1), SCREEN, TIME_Y), body)
    body = _set(body, "bg.spr", "%d,%d" % (TIMER_GROUP, 0))
    body = _set(body, "bg.offset", "0,0")
    body = re.sub(r"(?m)^(\s*counter\w*\.offset\s*=\s*)(-?\d+),\s*-?\d+\s*$",
                  lambda m: "%s%s,%d" % (m.group(1), m.group(2), -4), body)
    body = re.sub(r"(?m)^(\s*counter\w*\.scale\s*=\s*)\d+(\.\d+)?\s*,\s*\d+(\.\d+)?\s*$",
                  lambda m: "%s0.55, 0.55" % m.group(1), body)
    lines[s:e] = body.split("\n")

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
    timer, axis = paint_timer()
    painted[(TIMER_GROUP, 0)] = (timer, axis)
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
    strip.alpha_composite(timer.crop((150, 0, 250, 64)), (590, 0))
    strip.convert("RGB").save(os.path.join(ROOT, "artifacts", "vs_banner.png"))
    print("strip: sprites %s, back y %d, belly y %d, heads/timer y %d" % (
        written, LIFE_Y, BAR_Y, TIME_Y))


if __name__ == "__main__":
    main()
