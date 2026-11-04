"""Paint the top power meters as the gold dragon from the concept art.

Ikemen draws the power bar at the top of the screen from data/fight.sff: the
trough (40,0), a frame (41,0), the filled front (43,0) and a frontMax sprite
(44,0) that only appears at full power.

The reference is the gold dragon on the banner: a smooth serpent, no lizard
spikes, a raised maned head with curved horns, whiskers and an open jaw, and a
hide of large overlapping fish scales catching light along the top of every
plate. That is what is drawn here - tapered curves for the body, neck, horns,
mane and whiskers, and a two-tone scale pattern over the whole body, so the
texture is the reference's texture and not a gradient band.

The frame carries the whole animal so it reads at low power, the front is the lit
body (power climbs along the back towards the jaw), and the full bar blooms and
carries AUDACITY in solid gold with no outline.

Run:  python3 tools/build_powerbar.py
"""

from __future__ import annotations

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGHT_SFF = os.path.join(ROOT, "data", "fight.sff")

# Footprint in the fight screen's 1280x720 space. Tall enough for a raised head
# and wide enough for a maned neck plus a curling tail; the axis is the right
# edge, which is where data/fight.def anchors the bar.
W, H = 300, 44
AXIS = (W, 0)

TROUGH = (40, 0, W, H, AXIS)
FRAME = (41, 0, W, H, AXIS)
FRONT = (43, 0, W, H, AXIS)
FRONT_MAX = (44, 0, W, H, AXIS)

SS = 6  # supersample factor

# Gold as the banner uses it: red-brown in the crevices, honey on the plates,
# pale gold on the lit edge, with the eye and mouth in red.
CREVICE = (92, 44, 16)
BRONZE = (146, 86, 26)
GOLD = (204, 148, 46)
GOLD_LO = (236, 186, 78)
GOLD_HI = (253, 236, 170)
RED = (188, 40, 28)
MOUTH = (86, 20, 14)
INK = (30, 16, 7)

NECK = (0.845, 0.40)   # body ends here, as a fraction of W and H


def _taper(d, pts, w0, w1, fill, outline=None):
    """Stamp a tapered stroke through a polyline: horns, mane, whiskers, tail."""
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


def _curve_points(ctrl, n=18):
    """Catmull-Rom through the control points, for smooth serpentine curves."""
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
    """Centre line of the body from tail to shoulder, and its half-thickness."""
    ctrl = [(w * 0.03, h * 0.72), (w * 0.16, h * 0.78), (w * 0.33, h * 0.66),
            (w * 0.50, h * 0.62), (w * 0.66, h * 0.56), (w * 0.78, h * 0.48),
            (NECK[0] * w, NECK[1] * h)]
    line = _curve_points(ctrl)
    out = []
    for i, (x, y) in enumerate(line):
        t = i / float(len(line) - 1)
        half = h * (0.085 + 0.155 * min(1.0, (t + 0.10) ** 0.7))
        out.append((x, y, half))
    return out


def _body_polygon(line):
    top = [(x, y - half) for x, y, half in line]
    bot = [(x, y + half) for x, y, half in reversed(line)]
    return top + bot


def _scale_field(w, h, line, plates):
    """Two-tone overlapping scales over the body, drawn along its centre line.

    Each plate is a scallop with a dark underside and a pale lit edge, which is
    the texture the banner's dragon has; a plain gradient read as a plastic tube.
    """
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    n = len(line)
    rows = 3
    step = w / float(plates)
    for r in range(rows):
        k = (r + 0.5) / rows
        x = step * (0.5 if r % 2 else 0.0)
        while x < w * NECK[0]:
            idx = min(n - 1, max(0, int(round(x / float(w) * (n - 1)))))
            _x, cy, half = line[idx]
            yy = cy - half * 0.55 + 2 * half * 0.62 * k
            rr = step * 0.62
            d.arc([x - rr, yy - rr * 0.85, x + rr, yy + rr * 0.85],
                  190, 350, fill=CREVICE + (235,), width=int(max(2, step * 0.34)))
            d.arc([x - rr, yy - rr * 0.98, x + rr, yy + rr * 0.72],
                  196, 344, fill=GOLD_HI + (210,), width=int(max(1, step * 0.14)))
            x += step
    return layer


def _head(d, w, h, bright=False):
    """The head from the banner: maned, horned, whiskered, jaw open.

    Everything is a tapered stroke or a soft polygon - no triangles, which is
    what made the last version read as a lizard.
    """
    hx, hy = w * NECK[0], h * NECK[1]
    s = (h / 44.0) * 0.88
    body = GOLD_LO if bright else GOLD
    hi = GOLD_HI

    # neck swelling into the skull
    _taper(d, [(hx - 10 * s, hy + 2 * s), (hx + 2 * s, hy - 2 * s),
               (hx + 14 * s, hy - 4 * s)], 20 * s, 24 * s, body, INK)
    # skull and brow
    d.ellipse([hx + 2 * s, hy - 13 * s, hx + 30 * s, hy + 9 * s], fill=body,
              outline=INK, width=max(1, int(1.1 * s)))
    # upper jaw and snout, tapering to the nose
    _taper(d, [(hx + 20 * s, hy - 6 * s), (hx + 36 * s, hy - 5 * s),
               (hx + 48 * s, hy - 3 * s)], 15 * s, 7 * s, hi, INK)
    # lower jaw, dropped open
    _taper(d, [(hx + 20 * s, hy + 6 * s), (hx + 34 * s, hy + 9 * s),
               (hx + 44 * s, hy + 7 * s)], 11 * s, 5 * s, body, INK)
    # mouth gap and teeth
    d.polygon([(hx + 22 * s, hy + 1 * s), (hx + 45 * s, hy - 1 * s),
               (hx + 43 * s, hy + 7 * s), (hx + 22 * s, hy + 6 * s)],
              fill=MOUTH)
    for i in range(3):
        tx = hx + (25 + i * 6) * s
        d.polygon([(tx, hy + 1 * s), (tx + 3 * s, hy + 1 * s),
                   (tx + 1.5 * s, hy + 4.5 * s)], fill=hi)
    # curved horns sweeping back
    _taper(d, [(hx + 8 * s, hy - 11 * s), (hx - 8 * s, hy - 20 * s),
               (hx - 24 * s, hy - 21 * s), (hx - 34 * s, hy - 14 * s)],
           9 * s, 2 * s, hi, INK)
    _taper(d, [(hx + 14 * s, hy - 10 * s), (hx + 2 * s, hy - 17 * s),
               (hx - 10 * s, hy - 15 * s)], 5 * s, 1.2 * s, body, INK)
    # eye and nostril
    d.ellipse([hx + 16 * s, hy - 7 * s, hx + 22 * s, hy - 2 * s], fill=RED,
              outline=INK)
    d.ellipse([hx + 18.4 * s, hy - 5.6 * s, hx + 21 * s, hy - 3 * s], fill=INK)
    d.ellipse([hx + 43 * s, hy - 4 * s, hx + 45 * s, hy - 2 * s], fill=INK)
    # whiskers curling away from the snout
    for dy, dirn in ((-2, -1.0), (2, 1.0)):
        base = (hx + 46 * s, hy + dy * s)
        pts = [base, (base[0] - 10 * s, base[1] + dirn * 6 * s),
               (base[0] - 22 * s, base[1] + dirn * 2 * s),
               (base[0] - 30 * s, base[1] + dirn * 8 * s)]
        _taper(d, _curve_points(pts, 12), 1.8 * s, 0.8 * s, hi)


def _mane(d, w, h):
    """Strands flowing back off the skull, drawn behind the body."""
    hx, hy = w * NECK[0], h * NECK[1]
    s = (h / 44.0) * 0.88
    for i, (dy, ln, lift) in enumerate(((-9, 26, -14), (-4, 30, -8),
                                        (1, 28, 2), (6, 24, 9))):
        base = (hx + 3 * s, hy + dy * s)
        pts = [base,
               (base[0] - ln * 0.45 * s, base[1] + lift * 0.6 * s),
               (base[0] - ln * 0.8 * s, base[1] + lift * 1.1 * s),
               (base[0] - ln * s, base[1] + (lift + 4) * s)]
        _taper(d, _curve_points(pts, 12), 6.0 * s, 1.2 * s,
               GOLD_LO if i % 2 else GOLD, INK)


def _tail(d, line):
    x, y, half = line[0]
    pts = [(x + half * 0.4, y), (x - half * 1.6, y - half * 1.1),
           (x - half * 2.9, y + half * 0.2), (x - half * 2.2, y + half * 1.3),
           (x - half * 0.9, y + half * 0.9)]
    _taper(d, _curve_points(pts, 14), half * 1.5, half * 0.5, GOLD, INK)


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

    if kind == "trough":
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).polygon([(round(x), round(y)) for x, y in poly],
                                     fill=255)
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        img.paste(_gradient(w, h, [(0.0, (16, 9, 4)), (0.4, (40, 23, 10)),
                                   (0.7, (54, 30, 12)), (1.0, (14, 8, 3))]),
                  (0, 0), mask)
        d = ImageDraw.Draw(img)
        plates = _scale_field(w, h, line, plates=26)
        dark = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dark)
        dd.polygon([(round(x), round(y)) for x, y in poly], fill=(0, 0, 0, 150))
        img = Image.alpha_composite(img, Image.composite(
            plates, Image.new("RGBA", (w, h), (0, 0, 0, 0)),
            mask).point(lambda v: v))
        _tail(d, line)
        _head(d, w, h, bright=False)
        img = Image.composite(img, Image.new("RGBA", (w, h), (0, 0, 0, 0)), mask)
        return img.resize((W, H), Image.LANCZOS)

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon([(round(x), round(y)) for x, y in poly],
                                 fill=255)
    back = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(back)
    _mane(bd, w, h)
    _tail(bd, line)
    img = Image.alpha_composite(back, img)

    if kind == "frame":
        img = Image.alpha_composite(img, Image.new("RGBA", (w, h), (0, 0, 0, 0)))
        img.paste(_gradient(w, h, [(0.0, BRONZE), (0.35, GOLD),
                                   (0.62, GOLD_LO), (0.85, GOLD), (1.0, BRONZE)]),
                  (0, 0), mask)
    else:
        img.paste(_gradient(w, h, [(0.0, (150, 92, 26)), (0.3, GOLD),
                                   (0.6, GOLD_LO), (0.88, GOLD_HI),
                                   (1.0, GOLD)]), (0, 0), mask)
    img = Image.alpha_composite(img, Image.composite(
        _scale_field(w, h, line, plates=26), Image.new("RGBA", (w, h),
                                                      (0, 0, 0, 0)), mask))
    d = ImageDraw.Draw(img)
    _head(d, w, h, bright=(kind == "front_max"))

    if kind == "front_max":
        img = Image.alpha_composite(img.filter(ImageFilter.GaussianBlur(2.4 * SS)),
                                    img)
        d = ImageDraw.Draw(img)
        text = "AUDACITY"
        font = art.font(int(h * 0.40))
        tw = d.textlength(text, font=font)
        box = d.textbbox((0, 0), text, font=font)
        tx = w * 0.34 - tw / 2.0
        ty = h * 0.52 - (box[3] - box[1]) / 2.0 - box[1]
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(glow).text((tx, ty), text, font=font, fill=GOLD_HI + (150,))
        img = Image.alpha_composite(img, glow.filter(
            ImageFilter.GaussianBlur(1.8 * SS)))
        ImageDraw.Draw(img).text((tx, ty), text, font=font,
                                 fill=(255, 248, 214, 255))
    return img.resize((W, H), Image.LANCZOS)


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

    _d, check, _p = sff.read_sff(FIGHT_SFF)
    have = {(s["group"], s["number"]): s for s in check}
    for group, number, w, h, _axis in (TROUGH, FRAME, FRONT, FRONT_MAX):
        s = have.get((group, number))
        if s is None:
            raise SystemExit(f"power bar sprite {group},{number} went missing")
        if (s["w"], s["h"]) != (w, h):
            raise SystemExit(f"power bar sprite {group},{number} is "
                             f"{s['w']}x{s['h']}, expected {w}x{h}")

    scale = 5
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
    print(f"power bar: {W}x{H}, {SS}x supersampled, serpent body with fish "
          f"scales, maned horned head, AUDACITY in gold with no outline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
