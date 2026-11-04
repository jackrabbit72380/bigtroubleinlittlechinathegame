"""Build the top strip: dragons that *are* the power meter, and the timer.

Everything lives in the first ~60 pixels of the 1280x720 fight screen:

    y  0..20   the dragon's back and head - this band is the metre itself
               top half   = skin   -> the power meter ([Powerbar])
               bottom half = belly -> the audacity (underbelly) meter
    y 30..58   the health bars, moved up under the dragons
    y  0..52   the glowing green/red yin-yang at dead centre, timer on top

The dragon bodies are painted straight into [Powerbar]'s own sprites, so the
meter is not laid over the dragon - the meter *is* the dragon's midsection. The
head, tail and backdrop are one background sprite per player, anchored under
that player's lifebar and covering only the top sliver of the screen:

    20,0   left half, 640x260, axis top-left -> p1.bg1
    20,1   right half, green, mirror of the left -> p2.bg1

No legs, no arms: just back, head, horns, mane and tail.

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

BAND = 20                   # the metre band, and the dragon's body, tall
BAR_Y = 0                   # [Powerbar] sits right at the top
LIFE_Y = 30                 # health bars tuck in underneath
TIME_Y = 26                 # yin-yang centre
METER_W = 202               # fillable length of the metre ([Powerbar] range)
BAR_X1 = 568                # p1.pos.x: the metre's inner end
METER_X0 = BAR_X1 - METER_W - 4     # outer end of the metre (range -4..-206)

RED = {
    "ink": (24, 5, 4), "dark": (86, 14, 10), "mid": (152, 34, 22),
    "skin": (188, 56, 34), "light": (214, 88, 54), "rim": (248, 152, 108),
    "belly": (224, 172, 124), "belly_lit": (246, 206, 158),
    "horn": (242, 226, 186), "eye": (255, 216, 78), "mouth": (46, 6, 4),
    "glow": (255, 84, 48), "whisker": (255, 212, 156),
}
GREEN = {
    "ink": (10, 18, 6), "dark": (34, 58, 22), "mid": (92, 128, 38),
    "skin": (124, 160, 52), "light": (156, 190, 72), "rim": (212, 240, 146),
    "belly": (206, 198, 132), "belly_lit": (238, 234, 178),
    "horn": (238, 232, 194), "eye": (255, 216, 78), "mouth": (16, 24, 10),
    "glow": (96, 255, 120), "whisker": (232, 250, 186),
}

# centre line of the animal across the 640-wide half: snout at the inner end,
# back running outward, tail tapering off to the left
SPINE = ((566, 10), (540, 10), (500, 9), (460, 9), (420, 10), (380, 10),
         (350, 10), (320, 9), (290, 7), (262, 6), (242, 5))
SPINE_R = (10.0, 9.8, 9.6, 9.4, 9.2, 9.0, 8.2, 6.6, 4.4, 2.4, 1.0)


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
    """Screen-space centre line with a half-thickness, scaled by s."""
    pts = [SPINE[0]] + list(SPINE) + [SPINE[-1]]
    rad = [SPINE_R[0]] + list(SPINE_R) + [SPINE_R[-1]]
    out = []
    for i in range(len(pts) - 3):
        p0, p1, p2, p3 = pts[i:i + 4]
        r0, r1, r2, r3 = rad[i:i + 4]
        for k in range(14):
            t = k / 14.0
            t2, t3 = t * t, t * t * t
            cr = lambda a, b, c, d: 0.5 * (2 * b + (-a + c) * t
                                           + (2 * a - 5 * b + 4 * c - d) * t2
                                           + (-a + 3 * b - 3 * c + d) * t3)
            out.append((cr(p0[0], p1[0], p2[0], p3[0]) * s,
                        cr(p0[1], p1[1], p2[1], p3[1]) * s,
                        max(0.6, cr(r0, r1, r2, r3)) * s))
    return out


def _taper(d, pts, w0, w1, fill, outline=None, ow=2):
    """Stroke a tapered limb along a polyline."""
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


def _body(img, pal, s):
    """Back of the dragon: ink outline, skin on top, belly underneath."""
    line = _spine(s)
    d = ImageDraw.Draw(img)
    top = [(x, y - r) for x, y, r in line]
    bot = [(x, y + r) for x, y, r in reversed(line)]
    poly = top + bot
    d.polygon(poly, fill=pal["ink"])
    d.line(poly + [poly[0]], fill=pal["ink"], width=int(1.5 * s), joint="curve")
    inner = [(x, y - r + 1.6 * s) for x, y, r in line]
    inner += [(x, y + r - 1.6 * s) for x, y, r in reversed(line)]
    d.polygon(inner, fill=pal["skin"])
    # belly: the whole lower half, lighter, with a lit edge along the split
    split = [(x, y + r * 0.06) for x, y, r in line]
    belly = [(x, y + r - 1.6 * s) for x, y, r in reversed(line)]
    d.polygon(split + belly, fill=pal["belly"])
    _taper(d, [(x, y + r * 0.08) for x, y, r in line], 2.6 * s, 1.4 * s,
           pal["belly_lit"])
    # dorsal spines, outside the metre so they never sit on the bar
    for fx, height in ((0.42, 4.2), (0.30, 3.6), (0.20, 2.8)):
        i = int(fx * (len(line) - 1))
        x, y, r = line[i]
        d.polygon([(x - r * 0.9, y - r + 1.5 * s),
                   (x - r * 0.1, y - r - height * s),
                   (x + r * 0.9, y - r + 1.5 * s)], fill=pal["mid"])


def _head(img, pal, s):
    """A bold little profile head at the inner end, looking at the timer."""
    d = ImageDraw.Draw(img)

    def P(x, y):
        return (x * s, y * s)

    # neck, so the head grows out of the back rather than sitting on it
    d.polygon([P(540, 0), P(566, 0), P(566, 24), P(540, 24)], fill=pal["skin"])
    # skull and snout
    d.polygon([P(558, 2), P(592, 1), P(604, 5), P(610, 10), P(602, 22),
               P(558, 22)], fill=pal["skin"], outline=pal["ink"],
              width=int(1.4 * s))
    d.polygon([P(596, 5), P(613, 9), P(613, 14), P(596, 16)],
              fill=pal["light"], outline=pal["ink"])
    # brow over the eye
    d.polygon([P(558, 3), P(590, 2), P(592, 8), P(558, 9)], fill=pal["mid"])
    # open mouth with a row of teeth
    d.polygon([P(558, 15), P(610, 13), P(602, 20), P(558, 20)],
              fill=pal["mouth"])
    for x in (562, 572, 582, 592):
        d.polygon([P(x, 15), P(x + 7, 14.5), P(x + 3.5, 20.5)],
                  fill=pal["horn"])
    # lower jaw
    d.polygon([P(556, 19), P(602, 19), P(594, 24), P(556, 24)],
              fill=pal["belly"], outline=pal["ink"])
    # eye
    d.ellipse([P(570, 5)[0], P(570, 5)[1], P(583, 14)[0], P(583, 14)[1]],
              fill=pal["eye"], outline=pal["ink"])
    d.ellipse([P(575, 7)[0], P(575, 7)[1], P(581, 12)[0], P(581, 12)[1]],
              fill=pal["ink"])
    # nostril
    d.ellipse([P(605, 10)[0], P(605, 10)[1], P(609, 13)[0], P(609, 13)[1]],
              fill=pal["ink"])
    # horns swept back along the top of the back
    _taper(d, _curve([P(566, 2), P(550, -1), P(534, 1), P(524, 5)], 10),
           4.2 * s, 1.0 * s, pal["horn"], pal["ink"])
    _taper(d, _curve([P(576, 1.5), P(560, -1.5), P(546, 1)], 10),
           2.6 * s, 0.8 * s, pal["horn"], pal["ink"])
    # mane
    for dy, ln, lift in ((2, 20, -1.5), (7, 22, 1.0), (13, 18, 2.5)):
        base = P(556, dy)
        pts = [base, (base[0] - ln * 0.5 * s, base[1] + lift * 0.7 * s),
               (base[0] - ln * s, base[1] + lift * 1.4 * s)]
        _taper(d, _curve(pts, 10), 4.4 * s, 0.9 * s, pal["light"], pal["ink"])
    # whisker trailing back over the body
    _taper(d, _curve([P(613, 12), P(600, 17), P(586, 20)], 10),
           1.6 * s, 0.4 * s, pal["whisker"])


def _backdrop(img, pal, s):
    """Dark wash behind the band only, so the strip cannot eat the screen."""
    d = ImageDraw.Draw(img)
    for y in range(int(26 * s)):
        k = y / (26.0 * s)
        alpha = int(232 * (1.0 - k) ** 1.4)
        d.rectangle([0, y, img.width, y], fill=(6, 8, 20, alpha))
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([(SCREEN - 150) * s, -30 * s, (SCREEN + 150) * s, 22 * s],
               fill=pal["glow"] + (46,))
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


def paint_meter(pal, lit, label=None):
    """One metre sprite: skin on the top half, belly on the bottom half."""
    w, h = METER_W + 4, BAND
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    top = 1 if lit else 0
    for y in range(h):
        k = y / float(h - 1)
        if k < 0.5:
            t = k / 0.5
            a = pal["rim"] if lit else pal["mid"]
            b = pal["light"] if lit else pal["skin"]
            col = tuple(int(a[c] + (b[c] - a[c]) * t) for c in range(3))
        else:
            t = (k - 0.5) / 0.5
            a = pal["belly_lit"] if lit else pal["belly"]
            b = pal["belly"] if lit else pal["dark"]
            col = tuple(int(a[c] + (b[c] - a[c]) * t) for c in range(3))
        d.rectangle([0, y, w - 1, y], fill=col + (255,))
    # ink rim, and the line where the skin meets the belly
    d.rectangle([0, 0, w - 1, h - 1], outline=pal["ink"] + (255,), width=top)
    d.rectangle([0, h // 2, w - 1, h // 2],
                fill=pal["ink"] + (150,) if not lit else pal["ink"] + (90,))
    if label:
        font = ImageFont.truetype(FONT, int(h * 0.44))
        box = d.textbbox((0, 0), label, font=font)
        d.text(((w - (box[2] - box[0])) / 2, h * 0.56 - box[1]), label,
               font=font, fill=(16, 22, 12, 235))
    return img


def build_meters():
    """The four [Powerbar] sprites, all BAND pixels tall."""
    out = {}
    out[(40, 0)] = (paint_meter(RED, lit=False), (METER_W + 4, 0))
    out[(41, 0)] = (Image.new("RGBA", (METER_W + 4, BAND), (0, 0, 0, 0)),
                    (METER_W + 4, 0))
    out[(43, 0)] = (paint_meter(RED, lit=True), (METER_W, 0))
    out[(44, 0)] = (paint_meter(RED, lit=True, label="AUDACITY"), (METER_W, 0))
    return out


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
    """Move the whole top strip up and hand the metres to the dragons."""
    with open(FIGHT_DEF, encoding="utf-8", errors="surrogateescape",
              newline="") as f:
        text = f.read()
    lines = text.split("\n")

    # --- health bars: up under the dragons, banner halves anchored at 0,0 ---
    s, e = _section(lines, "Lifebar")
    body = "\n".join(lines[s:e])
    for side, x in (("p1", 595), ("p2", 684)):
        body = _set(body, "%s.pos" % side, "%d,%d" % (x, LIFE_Y))
        body = _set(body, "%s.bg1.spr" % side, "%d,%d" % (GROUP, 0 if side == "p1" else 1))
        body = _set(body, "%s.bg1.offset" % side,
                    "%d,%d" % ((0 if side == "p1" else 640) - x, -LIFE_Y))
        body = _set(body, "%s.bg1.xshear" % side, "0")
    lines[s:e] = body.split("\n")

    # --- the metre band: no vertical offsets, everything on the same 0..20 ---
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
    # the level readout tucks under the metre instead of the health bar
    body = re.sub(r"(?m)^(\s*p[12]\.counter\w*\.offset\s*=\s*)(-?\d+),\s*-?\d+\s*$",
                  lambda m: "%s%s,%d" % (m.group(1), m.group(2), BAND + 1), body)
    lines[s:e] = body.split("\n")

    # --- yin-yang and digits, small, at dead centre ---
    s, e = _section(lines, "Time")
    body = "\n".join(lines[s:e])
    body = _set(body, "pos", "%d,%d" % (SCREEN, TIME_Y))
    body = re.sub(r"(?m)^(\s*pos\s*=\s*).*$", r"\g<1>%d,%d" % (SCREEN, TIME_Y), body)
    body = _set(body, "bg.offset", "0,0")
    body = re.sub(r"(?m)^(\s*counter\w*\.offset\s*=\s*)(-?\d+),\s*-?\d+\s*$",
                  lambda m: "%s%s,%d" % (m.group(1), m.group(2), -4), body)
    body = re.sub(r"(?m)^(\s*counter\w*\.scale\s*=\s*)\d+\s*,\s*\d+\s*$",
                  r"\g<1>0.55, 0.55", body)
    lines[s:e] = body.split("\n")

    # --- the score readout sat where the health bars now are ---
    s, e = _section(lines, "Score")
    body = "\n".join(lines[s:e])
    body = _set(body, "p1.pos", "586,%d" % (LIFE_Y + BAND + 10))
    body = _set(body, "p2.pos", "696,%d" % (LIFE_Y + BAND + 10))
    lines[s:e] = body.split("\n")

    with open(FIGHT_DEF + ".tmp", "w", encoding="utf-8",
              errors="surrogateescape", newline="") as f:
        f.write("\n".join(lines))
    os.replace(FIGHT_DEF + ".tmp", FIGHT_DEF)


def _concept_path():
    """A dropped-in concept banner wins over anything painted here."""
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

    concept = _concept_path()
    if concept:
        left, right = _from_concept(concept)
    else:
        left = paint_half(RED, flip=False)
        right = paint_half(GREEN, flip=True)

    painted = {(GROUP, 0): (left, (0, 0)), (GROUP, 1): (right, (0, 0))}
    painted.update(build_meters())
    written = _write_sprites(painted)
    patch_def()

    _d, check, _p = sff.read_sff(FIGHT_SFF)
    have = {(s["group"], s["number"]): s for s in check}
    for key, (img, _axis) in painted.items():
        sp = have.get(key)
        if sp is None:
            raise SystemExit("sprite %d,%d went missing" % key)
        if (sp["w"], sp["h"]) != (img.width, img.height):
            raise SystemExit("sprite %d,%d is %dx%d, expected %dx%d" % (
                key[0], key[1], sp["w"], sp["h"], img.width, img.height))

    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    strip = Image.new("RGBA", (HALF * 2, 64), (0, 0, 0, 0))
    strip.alpha_composite(left.crop((0, 0, HALF, 64)), (0, 0))
    strip.alpha_composite(right.crop((0, 0, HALF, 64)), (HALF, 0))
    strip.convert("RGB").save(os.path.join(ROOT, "artifacts", "vs_banner.png"))
    print("top strip: sprites %s, band %dpx, health y %d, timer y %d" % (
        written, BAND, LIFE_Y, TIME_Y))


if __name__ == "__main__":
    main()
