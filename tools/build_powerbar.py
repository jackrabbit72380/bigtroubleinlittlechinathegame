"""Paint the top power meters as the dragon from the concept art.

Ikemen draws the power bar at the top of the screen from data/fight.sff: the
trough (40,0), a frame (41,0), the filled front (43,0) and a frontMax sprite
(44,0) that only appears at full power.

The reference is the gold dragon lying along the roof: head low at the LEFT,
neck rising into one big arch, the body falling into a trough in the middle,
then rising again into a curled tail that ends in a flared fin at the RIGHT. The
whole animal is covered in big overlapping plates.

This is a single serpent drawn on that path. Nothing else is added: no ring, no
spikes, no second body.

Run:  python3 tools/build_powerbar.py
"""

from __future__ import annotations

import math
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGHT_SFF = os.path.join(ROOT, "data", "fight.sff")
FIGHT_DEF = os.path.join(ROOT, "data", "fight.def")

W, H = 460, 76            # matches the meter range the def already uses
AXIS = (W, 0)

TROUGH = (40, 0, W, H, AXIS)
FRAME = (41, 0, W, H, AXIS)
FRONT = (43, 0, W, H, AXIS)
FRONT_MAX = (44, 0, W, H, AXIS)

SS = 5

CREVICE = (86, 60, 20)
BRONZE = (144, 104, 32)
GOLD = (198, 164, 58)
GOLD_LO = (228, 202, 98)
GOLD_HI = (251, 241, 180)
GREEN = (124, 136, 60)
RED = (188, 44, 30)
MOUTH = (82, 22, 16)
INK = (26, 20, 8)

# The concept's silhouette, traced left to right as fractions of the sprite.
# Head end at the left, the arch over the left half, the trough in the middle,
# the tail rising and curling at the right.
PATH = ((0.020, 0.700), (0.075, 0.640), (0.140, 0.470), (0.215, 0.300),
        (0.300, 0.245), (0.385, 0.250), (0.455, 0.380), (0.520, 0.610),
        (0.585, 0.735), (0.650, 0.700), (0.715, 0.520), (0.775, 0.350),
        (0.830, 0.265), (0.880, 0.300), (0.905, 0.400), (0.935, 0.360),
        (0.950, 0.280))

HEAD_AT = 0.0      # index into the path where the head sits (the left end)
TAIL_FIN_AT = -1   # the right end


def _curve(ctrl, n=16):
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


def _spine(w, h):
    # The path fractions are the concept's, but the head reaches ~38px past its
    # first point and the fin ~30px past its last, so the path is inset: that
    # keeps the snout and the fin inside the sprite instead of clipping them.
    def inset(fx):
        return 0.10 + (fx - PATH[0][0]) * 0.86

    line = _curve([(inset(fx) * w, fy * h) for fx, fy in PATH])
    out = []
    for i, (x, y) in enumerate(line):
        t = i / float(len(line) - 1)
        # thickest through the arch and the trough, tapering to the tail
        half = h * (0.100 + 0.045 * math.sin(math.pi * min(1.0, t * 0.85))
                    - 0.045 * max(0.0, t - 0.75) / 0.25)
        out.append((x, y, max(h * 0.035, half)))
    return out


def _taper(d, pts, w0, w1, fill, outline=None):
    segs = max(1, len(pts) - 1)
    for i in range(segs):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        steps = max(4, int(math.hypot(x1 - x0, y1 - y0) * 1.5))
        for s in range(steps + 1):
            t = s / float(steps)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            k = (i + t) / segs
            r = (w0 + (w1 - w0) * k) / 2.0
            if outline:
                d.ellipse([x - r - 1, y - r - 1, x + r + 1, y + r + 1],
                          fill=outline)
        for s in range(steps + 1):
            t = s / float(steps)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            k = (i + t) / segs
            r = (w0 + (w1 - w0) * k) / 2.0
            d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def _scales(d, w, h, line):
    """Big overlapping plates across the whole animal, following its curve."""
    n = len(line)
    step = w / 44.0
    for r in range(3):
        x = step * (0.5 if r % 2 else 0.0)
        while x < w * 0.99:
            idx = min(n - 1, max(0, int(round(x / float(w) * (n - 1)))))
            _x, cy, half = line[idx]
            yy = cy + (-0.60 + 0.60 * r) * half
            rr = step * 0.72
            d.arc([x - rr, yy - rr * 0.95, x + rr, yy + rr * 0.95],
                  188, 352, fill=CREVICE + (238,), width=int(max(2, step * 0.30)))
            d.arc([x - rr, yy - rr * 1.06, x + rr, yy + rr * 0.84],
                  194, 346, fill=GOLD_HI + (200,), width=int(max(1, step * 0.11)))
            if int(x / step) % 6 == 2:
                d.arc([x - rr * 0.72, yy - rr * 0.55, x + rr * 0.72,
                       yy + rr * 0.62], 205, 335, fill=GREEN + (195,),
                      width=int(max(2, step * 0.20)))
            x += step


def _head(d, w, h, line, bright=False):
    """The head at the left end, facing left, as in the concept."""
    x0, y0, half = line[0]
    s = (h / 76.0) * 1.05
    body = GOLD_LO if bright else GOLD
    hi = GOLD_HI
    hx = x0 + 6 * s
    hy = y0 - 2 * s

    # neck into the skull
    _taper(d, [(hx + 26 * s, hy + 6 * s), (hx + 12 * s, hy + 1 * s),
               (hx - 2 * s, hy - 2 * s)], 24 * s, 20 * s, body, INK)
    # skull
    d.ellipse([hx - 16 * s, hy - 12 * s, hx + 10 * s, hy + 10 * s], fill=body,
              outline=INK, width=max(1, int(1.2 * s)))
    # snout and upper jaw, pointing left
    _taper(d, [(hx - 8 * s, hy - 6 * s), (hx - 24 * s, hy - 6 * s),
               (hx - 38 * s, hy - 2 * s)], 16 * s, 6 * s, hi, INK)
    # lower jaw, open
    _taper(d, [(hx - 8 * s, hy + 6 * s), (hx - 24 * s, hy + 10 * s),
               (hx - 34 * s, hy + 7 * s)], 12 * s, 5 * s, body, INK)
    d.polygon([(hx - 10 * s, hy - 1 * s), (hx - 36 * s, hy + 1 * s),
               (hx - 34 * s, hy + 8 * s), (hx - 10 * s, hy + 6 * s)], fill=MOUTH)
    for i in range(3):
        tx = hx - (14 + i * 6) * s
        d.polygon([(tx, hy + 1 * s), (tx - 3 * s, hy + 1 * s),
                   (tx - 1.5 * s, hy + 4.5 * s)], fill=hi)
    # horns sweeping back to the right, over the mane
    _taper(d, [(hx - 2 * s, hy - 10 * s, ), (hx + 16 * s, hy - 20 * s),
               (hx + 34 * s, hy - 18 * s), (hx + 46 * s, hy - 8 * s)],
           7.5 * s, 1.6 * s, hi, INK)
    _taper(d, [(hx + 6 * s, hy - 10 * s), (hx + 20 * s, hy - 16 * s),
               (hx + 32 * s, hy - 12 * s)], 4.5 * s, 1.3 * s, body, INK)
    # mane flowing back along the neck
    for i, (dy, ln, lift) in enumerate(((-8, 26, -12), (-1, 30, -4), (6, 24, 6))):
        base = (hx + 4 * s, hy + dy * s)
        pts = [base, (base[0] + ln * 0.4 * s, base[1] + lift * 0.6 * s),
               (base[0] + ln * 0.75 * s, base[1] + lift * 1.1 * s),
               (base[0] + ln * s, base[1] + (lift + 4) * s)]
        _taper(d, _curve(pts, 12), 5.5 * s, 1.2 * s,
               hi if i % 2 else GOLD_LO, INK)
    # eye, nostril, whiskers trailing back
    d.ellipse([hx - 12 * s, hy - 7 * s, hx - 4 * s, hy - 1 * s], fill=RED,
              outline=INK)
    d.ellipse([hx - 9 * s, hy - 5.4 * s, hx - 6.4 * s, hy - 2.6 * s], fill=INK)
    d.ellipse([hx - 34 * s, hy + 1 * s, hx - 31.5 * s, hy + 3 * s], fill=INK)
    for dy, dirn in ((-2, -1.0), (4, 1.0)):
        base = (hx - 36 * s, hy + dy * s)
        pts = [base, (base[0] + 8 * s, base[1] + dirn * 6 * s),
               (base[0] + 18 * s, base[1] + dirn * 2 * s),
               (base[0] + 24 * s, base[1] + dirn * 8 * s)]
        _taper(d, _curve(pts, 10), 1.8 * s, 0.8 * s, hi)


def _tail_fin(d, w, h, line):
    """The flared fin where the tail lifts at the right end."""
    x, y, half = line[-1]
    s = (h / 76.0) * 1.0
    for dy, ln in ((-1.0, 20), (0.0, 24), (1.0, 18)):
        pts = [(x - half * 0.4, y + dy * half * 0.55),
               (x + ln * 0.5 * s, y + dy * half * 1.1),
               (x + ln * 0.95 * s, y + dy * half * 1.5),
               (x + ln * 1.25 * s, y + dy * half * 1.15)]
        _taper(d, _curve(pts, 10), half * 1.2, half * 0.45, GOLD_LO, INK)


def _gradient(w, h, stops):
    img = Image.new("RGB", (w, h))
    px = img.load()
    stops = sorted(stops)
    for y in range(h):
        k = y / float(max(1, h - 1))
        lo, hi = stops[0], stops[-1]
        for i in range(len(stops) - 1):
            if stops[i][0] <= k <= stops[i + 1][0]:
                lo, hi = stops[i], stops[i + 1]
                break
        span = max(1e-6, hi[0] - lo[0])
        f = min(1.0, max(0.0, (k - lo[0]) / span))
        col = tuple(int(round(lo[1][c] + (hi[1][c] - lo[1][c]) * f))
                    for c in range(3))
        for x in range(w):
            px[x, y] = col
    return img


def _dragon(kind):
    w, h = W * SS, H * SS
    line = _spine(w, h)
    top = [(x, y - half) for x, y, half in line]
    bot = [(x, y + half) for x, y, half in reversed(line)]
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon([(round(x), round(y)) for x, y in top + bot],
                                 fill=255)

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if kind == "trough":
        img.paste(_gradient(w, h, [(0.0, (14, 10, 4)), (0.45, (42, 30, 10)),
                                   (0.75, (56, 40, 14)), (1.0, (12, 9, 3))]),
                  (0, 0), mask)
    elif kind == "frame":
        img.paste(_gradient(w, h, [(0.0, BRONZE), (0.30, GOLD), (0.55, GOLD_LO),
                                   (0.80, GOLD), (1.0, BRONZE)]), (0, 0), mask)
    else:
        img.paste(_gradient(w, h, [(0.0, (152, 120, 36)), (0.30, GOLD),
                                   (0.60, GOLD_LO), (0.86, GOLD_HI),
                                   (1.0, GOLD)]), (0, 0), mask)

    d = ImageDraw.Draw(img)
    _scales(d, w, h, line)
    _head(d, w, h, line, bright=(kind == "front_max"))
    _tail_fin(d, w, h, line)

    if kind == "trough":
        dim = Image.new("RGBA", (w, h), (0, 0, 0, 136))
        img = Image.alpha_composite(img, Image.composite(
            dim, Image.new("RGBA", (w, h), (0, 0, 0, 0)), mask))

    if kind == "front_max":
        img = Image.alpha_composite(img.filter(ImageFilter.GaussianBlur(2.0 * SS)),
                                    img)
        d = ImageDraw.Draw(img)
        text = "AUDACITY"
        font = art.font(int(h * 0.20))
        tw = d.textlength(text, font=font)
        box = d.textbbox((0, 0), text, font=font)
        tx = w * 0.46 - tw / 2.0
        ty = h * 0.80 - (box[3] - box[1]) / 2.0 - box[1]
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(glow).text((tx, ty), text, font=font, fill=GOLD_HI + (140,))
        img = Image.alpha_composite(img, glow.filter(
            ImageFilter.GaussianBlur(1.5 * SS)))
        ImageDraw.Draw(img).text((tx, ty), text, font=font,
                                 fill=(255, 246, 206, 255))

    return img.resize((W, H), Image.LANCZOS)


def patch_fight_def():
    if not os.path.isfile(FIGHT_DEF):
        return False
    with open(FIGHT_DEF, encoding="utf-8", errors="surrogateescape",
              newline="") as f:
        text = f.read()
    orig = text
    text = re.sub(r"(?m)^(\s*p1\.range\.x\s*=\s*)-?\d+\s*,\s*-?\d+\s*$",
                  r"\g<1>-4, -%d" % (W - 4), text)
    text = re.sub(r"(?m)^(\s*p2\.range\.x\s*=\s*)-?\d+\s*,\s*-?\d+\s*$",
                  r"\g<1>4, %d" % (W - 4), text)
    if text != orig:
        with open(FIGHT_DEF + ".tmp", "w", encoding="utf-8",
                  errors="surrogateescape", newline="") as f:
            f.write(text)
        os.replace(FIGHT_DEF + ".tmp", FIGHT_DEF)
    return text != orig


def main():
    if not os.path.isfile(FIGHT_SFF):
        raise SystemExit("data/fight.sff is missing - fetch the engine data first")

    painted = {}
    for (group, number, w, h, axis), kind in (
            (TROUGH, "trough"), (FRAME, "frame"), (FRONT, "front"),
            (FRONT_MAX, "front_max")):
        painted[(group, number)] = (_dragon(kind), axis)

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
                        "axis": sp["axis"], "pal": sp["pal"], "link": sp["link"]})
    for key, (image, axis) in painted.items():
        if key not in done:
            out.append({"group": key[0], "number": key[1], "image": image,
                        "axis": axis})

    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: built fight.sff has no signature")
    with open(FIGHT_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(FIGHT_SFF + ".tmp", FIGHT_SFF)

    patch_fight_def()

    _d, check, _p = sff.read_sff(FIGHT_SFF)
    have = {(s["group"], s["number"]): s for s in check}
    for group, number, w, h, _axis in (TROUGH, FRAME, FRONT, FRONT_MAX):
        s = have.get((group, number))
        if s is None:
            raise SystemExit(f"power bar sprite {group},{number} went missing")
        if (s["w"], s["h"]) != (w, h):
            raise SystemExit(f"power bar sprite {group},{number} is "
                             f"{s['w']}x{s['h']}, expected {w}x{h}")

    scale = 4
    sheet = Image.new("RGBA", (W * scale + 24, (H * scale + 12) * 4 + 8),
                      (13, 15, 20, 255))
    y = 4
    for key in ((41, 0), (43, 0), (44, 0), (40, 0)):
        image, _axis = painted[key]
        sheet.alpha_composite(image.resize((W * scale, H * scale), Image.LANCZOS),
                              (12, y))
        y += H * scale + 12
    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    sheet.convert("RGB").save(os.path.join(ROOT, "artifacts", "powerbar.png"))
    print(f"power bar: {W}x{H}, one serpent on the concept's path "
          f"(head left, arch, trough, curled tail and fin right), {SS}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
