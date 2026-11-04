"""Paint the top power meters as the coiled dragon from the concept art.

Ikemen draws the power bar at the top of the screen from data/fight.sff: the
trough (40,0), a frame (41,0), the filled front (43,0) and a frontMax sprite
(44,0) that only appears at full power.

The reference is the dragon running along the roof tiles: it does not run in a
straight line. The body comes off the head, dips, rises into a high arch over
the middle, falls into a trough, then coils once and ends in a flared tail fin,
with big overlapping scales all over it. This draws that path - the arch, the
trough, the coil and the fin - rather than a straight rail, because the shape is
the thing that makes it that dragon.

The bar is anchored at its right edge and fills leftwards, so the drawing is the
reference mirrored: the head sits at the right, at the filled end, and the tail
fin at the left, so power climbs along the coil into the jaw.

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

# Footprint in the fight screen's 1280x720 space. W matches the meter range the
# def already uses (p1.range.x = 15,-460), so the bar keeps its exact width on
# screen; H is much taller than the stock 202x18 rail because the arch and coil
# have to fit inside it.
W, H = 460, 76
AXIS = (W, 0)

TROUGH = (40, 0, W, H, AXIS)
FRAME = (41, 0, W, H, AXIS)
FRONT = (43, 0, W, H, AXIS)
FRONT_MAX = (44, 0, W, H, AXIS)

SS = 5  # supersample factor

CREVICE = (88, 62, 22)
BRONZE = (146, 106, 34)
GOLD = (196, 162, 58)
GOLD_LO = (226, 200, 96)
GOLD_HI = (250, 240, 178)
GREEN = (126, 138, 62)
RED = (186, 42, 30)
MOUTH = (84, 22, 16)
INK = (26, 20, 8)

HEAD_AT = (0.925, 0.50)     # neck joint, as a fraction of W and H
TAIL_AT = (0.030, 0.62)


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


def _taper(d, pts, w0, w1, fill, outline=None):
    """A tapered stroke: horns, mane, whiskers, tail fin lobes."""
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


def _spine(w, h):
    """The reference's silhouette: dip, arch, trough, coil, neck.

    Read left to right this is the tail end, the coil, the trough under the
    arch, the high arch itself, and the neck dropping to the head.
    """
    ctrl = [(TAIL_AT[0] * w, TAIL_AT[1] * h),
            (0.10 * w, 0.640 * h),
            (0.17 * w, 0.440 * h),
            (0.22 * w, 0.260 * h),
            (0.27 * w, 0.440 * h),
            (0.34 * w, 0.640 * h),
            (0.45 * w, 0.740 * h),
            (0.55 * w, 0.600 * h),
            (0.64 * w, 0.300 * h),
            (0.71 * w, 0.180 * h),
            (0.78 * w, 0.300 * h),
            (0.86 * w, 0.460 * h),
            (HEAD_AT[0] * w, HEAD_AT[1] * h)]
    line = _curve(ctrl, 16)
    out = []
    for i, (x, y) in enumerate(line):
        t = i / float(len(line) - 1)
        # thin at the tail, fullest through the arch and the neck
        half = h * (0.050 + 0.062 * math.sin(math.pi * min(1.0, t * 0.92)) ** 0.6
                    + 0.024 * t)
        out.append((x, y, half))
    return out


def _body_polygon(line):
    top = [(x, y - half) for x, y, half in line]
    bot = [(x, y + half) for x, y, half in reversed(line)]
    return top + bot


def _scale_field(w, h, line, plates):
    """Big overlapping plates: dark crease under each, lit edge on top."""
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    n = len(line)
    step = w / float(plates)
    for r in range(2):
        x = step * (0.5 if r % 2 else 0.0)
        while x < HEAD_AT[0] * w:
            idx = min(n - 1, max(0, int(round(x / float(w) * (n - 1)))))
            _x, cy, half = line[idx]
            yy = cy + (-0.35 + 0.7 * r) * half
            rr = step * (0.62 - 0.06 * r)
            d.arc([x - rr, yy - rr * 0.9, x + rr, yy + rr * 0.9],
                  190, 350, fill=CREVICE + (240,), width=int(max(2, step * 0.30)))
            d.arc([x - rr, yy - rr * 1.02, x + rr, yy + rr * 0.78],
                  196, 344, fill=GOLD_HI + (205,), width=int(max(1, step * 0.12)))
            # a few plates mottled green, the way the reference's hide is
            if (int(x / step) + r) % 7 == 3:
                d.arc([x - rr * 0.7, yy - rr * 0.5, x + rr * 0.7, yy + rr * 0.6],
                      205, 335, fill=GREEN + (200,), width=int(max(2, step * 0.22)))
            x += step
    return layer


def _tail_fin(d, w, h, line):
    """The flared fin at the tail end, as in the reference."""
    x, y, half = line[0]
    for dy, ln in ((-1.5, 34), (-0.4, 40), (0.7, 32)):
        pts = [(x + half * 0.6, y + dy * half * 0.5),
               (x - ln * 0.35, y + dy * half),
               (x - ln * 0.8, y + dy * half * 1.25),
               (x - ln, y + dy * half * 0.9)]
        _taper(d, _curve(pts, 10), half * 1.3, half * 0.5, GOLD_LO, INK)


def _coil(d, w, h, line):
    """The single coil where the body loops, drawn as a ring the body passes."""
    idx = int(len(line) * 0.21)
    x, y, half = line[idx]
    r = half * 1.5
    d.ellipse([x - r, y - r, x + r, y + r], outline=GOLD, width=int(max(2, half * 0.55)))
    d.ellipse([x - r, y - r, x + r, y + r], outline=INK,
              width=int(max(1, half * 0.18)))


def _head(d, w, h):
    """Maned head at the neck joint, facing right into the filled end."""
    hx, hy = w * HEAD_AT[0], h * HEAD_AT[1]
    s = (h / 76.0) * 0.82
    body, hi = GOLD, GOLD_HI

    _taper(d, [(hx - 16 * s, hy + 2 * s), (hx - 4 * s, hy - 4 * s),
               (hx + 8 * s, hy - 6 * s)], 14 * s, 18 * s, body, INK)
    d.ellipse([hx - 4 * s, hy - 14 * s, hx + 20 * s, hy + 8 * s], fill=body,
              outline=INK, width=max(1, int(s)))
    _taper(d, [(hx + 12 * s, hy - 8 * s), (hx + 26 * s, hy - 7 * s),
               (hx + 38 * s, hy - 4 * s)], 12 * s, 5 * s, hi, INK)
    _taper(d, [(hx + 12 * s, hy + 4 * s), (hx + 26 * s, hy + 8 * s),
               (hx + 35 * s, hy + 6 * s)], 9 * s, 4 * s, body, INK)
    d.polygon([(hx + 14 * s, hy - 1 * s), (hx + 36 * s, hy - 3 * s),
               (hx + 34 * s, hy + 5 * s), (hx + 14 * s, hy + 4 * s)], fill=MOUTH)
    for i in range(3):
        tx = hx + (17 + i * 5) * s
        d.polygon([(tx, hy - 1 * s), (tx + 2.5 * s, hy - 1 * s),
                   (tx + 1.2 * s, hy + 2.5 * s)], fill=hi)
    # horns sweeping back over the mane
    _taper(d, [(hx + 2 * s, hy - 12 * s), (hx - 14 * s, hy - 22 * s),
               (hx - 30 * s, hy - 20 * s), (hx - 40 * s, hy - 12 * s)],
           8 * s, 1.8 * s, hi, INK)
    _taper(d, [(hx + 8 * s, hy - 11 * s), (hx - 4 * s, hy - 18 * s),
               (hx - 16 * s, hy - 15 * s)], 5 * s, 1.4 * s, body, INK)
    # mane strands behind the neck
    for i, (dy, ln, lift) in enumerate(((-10, 30, -12), (-4, 34, -6),
                                        (2, 30, 4), (8, 26, 10))):
        base = (hx - 2 * s, hy + dy * s)
        pts = [base, (base[0] - ln * 0.45 * s, base[1] + lift * 0.6 * s),
               (base[0] - ln * 0.8 * s, base[1] + lift * 1.1 * s),
               (base[0] - ln * s, base[1] + (lift + 4) * s)]
        _taper(d, _curve(pts, 12), 5.5 * s, 1.2 * s,
               hi if i % 2 else GOLD_LO, INK)
    # eye, nostril, whiskers
    d.ellipse([hx + 6 * s, hy - 8 * s, hx + 13 * s, hy - 2 * s], fill=RED,
              outline=INK)
    d.ellipse([hx + 9 * s, hy - 6.4 * s, hx + 11.6 * s, hy - 3.6 * s], fill=INK)
    d.ellipse([hx + 34 * s, hy - 5 * s, hx + 36.5 * s, hy - 3 * s], fill=INK)
    for dy, dirn in ((-3, -1.0), (3, 1.0)):
        base = (hx + 36 * s, hy + dy * s)
        pts = [base, (base[0] - 8 * s, base[1] + dirn * 7 * s),
               (base[0] - 20 * s, base[1] + dirn * 3 * s),
               (base[0] - 28 * s, base[1] + dirn * 10 * s)]
        _taper(d, _curve(pts, 12), 2.0 * s, 0.9 * s, hi)


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
    poly = _body_polygon(line)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon([(round(x), round(y)) for x, y in poly], fill=255)

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if kind == "trough":
        img.paste(_gradient(w, h, [(0.0, (14, 10, 4)), (0.45, (38, 28, 10)),
                                   (0.75, (52, 38, 14)), (1.0, (12, 9, 3))]),
                  (0, 0), mask)
        img = Image.alpha_composite(img, Image.composite(
            _scale_field(w, h, line, plates=22),
            Image.new("RGBA", (w, h), (0, 0, 0, 0)), mask))
        d = ImageDraw.Draw(img)
        _coil(d, w, h, line)
        _head(d, w, h)
        dim = Image.new("RGBA", (w, h), (0, 0, 0, 128))
        img = Image.alpha_composite(img, Image.composite(
            dim, Image.new("RGBA", (w, h), (0, 0, 0, 0)), mask))
    else:
        if kind == "frame":
            img.paste(_gradient(w, h, [(0.0, BRONZE), (0.3, GOLD),
                                       (0.55, GOLD_LO), (0.8, GOLD),
                                       (1.0, BRONZE)]), (0, 0), mask)
        else:
            img.paste(_gradient(w, h, [(0.0, (150, 118, 36)), (0.3, GOLD),
                                       (0.6, GOLD_LO), (0.86, GOLD_HI),
                                       (1.0, GOLD)]), (0, 0), mask)
        img = Image.alpha_composite(img, Image.composite(
            _scale_field(w, h, line, plates=22),
            Image.new("RGBA", (w, h), (0, 0, 0, 0)), mask))
        d = ImageDraw.Draw(img)
        _coil(d, w, h, line)
        _head(d, w, h)

        if kind == "front_max":
            img = Image.alpha_composite(
                img.filter(ImageFilter.GaussianBlur(2.0 * SS)), img)
            d = ImageDraw.Draw(img)
            text = "AUDACITY"
            font = art.font(int(h * 0.26))
            tw = d.textlength(text, font=font)
            box = d.textbbox((0, 0), text, font=font)
            tx = w * 0.40 - tw / 2.0
            ty = h * 0.86 - (box[3] - box[1]) / 2.0 - box[1]
            glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(glow).text((tx, ty), text, font=font,
                                      fill=GOLD_HI + (150,))
            img = Image.alpha_composite(img, glow.filter(
                ImageFilter.GaussianBlur(1.5 * SS)))
            ImageDraw.Draw(img).text((tx, ty), text, font=font,
                                     fill=(255, 246, 206, 255))

    fin = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    _tail_fin(ImageDraw.Draw(fin), w, h, line)
    img = Image.alpha_composite(fin, img)
    return img.resize((W, H), Image.LANCZOS)


def patch_fight_def():
    """Widen the fill range to the new sprite width, so the whole coil fills.

    The def's range.x is how far the front sprite travels as power climbs; left
    at the stock -206 the fill would only ever cover the right half of a 400px
    dragon.
    """
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

    ranged = patch_fight_def()

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
    for key in ((40, 0), (41, 0), (43, 0), (44, 0)):
        image, _axis = painted[key]
        sheet.alpha_composite(image.resize((W * scale, H * scale), Image.LANCZOS),
                              (12, y))
        y += H * scale + 12
    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    sheet.convert("RGB").save(os.path.join(ROOT, "artifacts", "powerbar.png"))
    print(f"power bar: {W}x{H} coiled dragon (arch, trough, coil, fin), "
          f"{SS}x supersampled, fill range {'widened' if ranged else 'already set'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
