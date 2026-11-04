"""Paint the top power meters as the gold dragon from the concept art.

Ikemen draws the power bar at the top of the screen from data/fight.sff: the
trough (40,0), a frame (41,0), the filled front (43,0) and a frontMax sprite
(44,0) that only appears at full power. The stock art is a grey metal rail with
a white "MAXIMUM!" banner on the end.

This draws an actual dragon instead: a scaled serpent body running the length of
the bar, a tail curling at the far end, a mane of spikes at the shoulder, and a
big horned head at the filled end with an open jaw, teeth, an eye and whiskers.
The frame carries the whole animal so it reads when the meter is empty; the
front is only the lit body, so power climbs along the dragon's back towards its
jaw; the full bar blooms and carries the word AUDACITY in solid gold, with no
outline at all.

Everything is drawn at four times the sprite's size and reduced with a Lanczos
filter, which is what keeps the curves smooth rather than stair-stepped.

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

# Footprint in the fight screen's 1280x720 space. Wider and taller than the
# stock 202x18 rail so the head, shoulder mane and tail all fit inside the
# silhouette instead of the head being a stamp on the end of a bar. The axis is
# still the right edge, which is where data/fight.def anchors it.
W, H = 244, 34
AXIS = (W, 0)
NECK_X = 178          # where the body ends and the neck starts

TROUGH = (40, 0, W, H, AXIS)
FRAME = (41, 0, W, H, AXIS)
FRONT = (43, 0, W, H, AXIS)
FRONT_MAX = (44, 0, W, H, AXIS)

SS = 4  # supersample factor

DEEP = (40, 22, 8)
BRONZE = (108, 64, 16)
GOLD = (198, 142, 40)
GOLD_LO = (230, 182, 76)
GOLD_HI = (252, 234, 160)
RED = (198, 44, 30)
MOUTH = (72, 18, 12)
INK = (26, 14, 6)

SCALE = 1.0  # multiplied by SS when drawing


def _body_outline(w, h):
    """Body polygon from tail to shoulder, plus the centre line it follows."""
    pts = []
    n = 200
    for i in range(n + 1):
        t = i / float(n)
        x = w * (0.02 + 0.72 * t)
        cy = h * (0.56 + 0.075 * math.sin(math.pi * 2.2 * t + 0.9)
                  + 0.035 * math.sin(math.pi * 4.4 * t))
        half = h * (0.10 + 0.20 * min(1.0, t ** 0.75))
        pts.append((x, cy, half))
    top = [(x, cy - half) for x, cy, half in pts]
    bot = [(x, cy + half) for x, cy, half in reversed(pts)]
    return top + bot, pts


def _head_geometry(w, h, neck_cy):
    """Polygons for the head, in sprite pixels before supersampling.

    The head is a third of the bar: skull and brow, a long snout with an open
    jaw, two horns swept back over the mane, and the mane spikes themselves. It
    is anchored on the neck's own centre line and its snout stops short of the
    sprite's right edge, so it joins the body and never gets clipped.
    """
    hx = w * 0.645          # back of the skull, overlapping the neck
    cy = neck_cy
    s = h / 34.0 * 0.84     # head is drawn for a 34px bar and scales with it

    def P(px, py):
        return (hx + px * s, cy + py * s)

    skull = [P(0, -7), P(9, -13), P(24, -13), P(38, -8), P(50, -3), P(58, 0),
             P(52, 3), P(40, 4), P(28, 5), P(12, 5), P(0, 4)]
    snout = [P(40, 4), P(58, 0), P(70, 2), P(72, 6), P(64, 8), P(50, 8)]
    jaw = [P(18, 8), P(38, 9), P(58, 8), P(70, 8), P(64, 14), P(48, 16),
           P(32, 16), P(18, 14)]
    mouth = [P(30, 6), P(66, 6), P(62, 10), P(34, 11)]
    horn_a = [P(10, -11), P(-13, -19), P(-2, -8), P(7, -10)]
    horn_b = [P(22, -11), P(3, -17), P(9, -7), P(17, -9)]
    # mane spikes behind the jaw
    mane = []
    for i in range(6):
        bx = -2 - i * 5
        top = -12 - (2 if i % 2 else 0)
        mane.append([P(bx, -4), P(bx - 7, top), P(bx - 3, -1)])
    eye = (P(36, -5), P(44, -1))
    nostril = (P(64, 2), P(68, 4))
    return {"skull": skull, "snout": snout, "jaw": jaw, "mouth": mouth,
            "horn_a": horn_a, "horn_b": horn_b, "mane": mane, "eye": eye,
            "nostril": nostril, "hx": hx, "cy": cy, "s": s}


def _scale_poly(pts, k):
    return [(x * k, y * k) for x, y in pts]


def _poly(d, pts, fill, outline=None, width=1):
    d.polygon([(round(x), round(y)) for x, y in pts], fill=fill,
              outline=outline)


def _scales(d, w, h, centre, colour, step, row_h, width):
    """Rows of overlapping plates along the body's own centre line."""
    n = len(centre)
    x = 6.0
    row = 0
    while x < NECK_X * 0.98:
        k = min(1.0, max(0.0, x / float(w)))
        idx = min(n - 1, int(round(k * (n - 1))))
        _x, cy, half = centre[idx]
        for r in range(3):
            yy = cy - half * 0.72 + row_h * r
            d.arc([x - step, yy - step * 0.55, x + step, yy + step * 0.55],
                  200, 340, fill=colour, width=width)
        x += step
        row += 1


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
        col = tuple(int(round(lo[1][c] + (hi[1][c] - lo[1][c]) * f)) for c in range(3))
        for x in range(w):
            px[x, y] = col
    return img


def _dragon(kind):
    w, h = W * SS, H * SS
    body_poly, centre = _body_outline(w, h)
    head = _head_geometry(w, h, centre[-1][1])

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon([(round(x), round(y)) for x, y in body_poly],
                                 fill=255)

    if kind == "trough":
        body = _gradient(w, h, [(0.0, (16, 9, 3)), (0.5, (34, 20, 8)),
                                (0.78, (46, 26, 10)), (1.0, (14, 8, 3))])
        img.paste(body, (0, 0), mask)
        d = ImageDraw.Draw(img)
        _scales(d, w, h, centre, (58, 34, 12), 13 * SS, 4.5 * SS, int(1.6 * SS))
        for spike in _spines(w, h, centre):
            _poly(d, spike, (30, 18, 7))
        _vague_head(d, head, (46, 28, 12), (74, 20, 14))
        return img.resize((W, H), Image.LANCZOS)

    if kind == "frame":
        body = _gradient(w, h, [(0.0, BRONZE), (0.35, GOLD), (0.62, GOLD_LO),
                                (0.85, GOLD), (1.0, BRONZE)])
        img.paste(body, (0, 0), mask)
        d = ImageDraw.Draw(img)
        _scales(d, w, h, centre, (150, 96, 28), 13 * SS, 4.5 * SS, int(1.4 * SS))
        for spike in _spines(w, h, centre):
            _poly(d, spike, GOLD_LO)
        _detail_head(d, head)
        _tail(d, centre, h)
        return img.resize((W, H), Image.LANCZOS)

    # front / front_max: the lit body only, so power climbs towards the jaw
    body = _gradient(w, h, [(0.0, (150, 92, 24)), (0.28, GOLD),
                            (0.55, GOLD_LO), (0.82, GOLD_HI), (1.0, GOLD)])
    img.paste(body, (0, 0), mask)
    d = ImageDraw.Draw(img)
    _scales(d, w, h, centre, (120, 74, 22), 13 * SS, 4.5 * SS, int(1.8 * SS))
    _scales(d, w, h, centre, GOLD_HI, 13 * SS, 4.5 * SS, int(0.9 * SS))
    for spike in _spines(w, h, centre):
        _poly(d, spike, GOLD_HI)
    _tail(d, centre, h)

    if kind == "front_max":
        bloom = img.filter(ImageFilter.GaussianBlur(2.2 * SS))
        img = Image.alpha_composite(bloom, img)
        d = ImageDraw.Draw(img)
        _detail_head(d, head, bright=True)
        # AUDACITY in solid gold, sitting on the lit back: no stroke, no plate.
        text = "AUDACITY"
        font = art.font(int(h * 0.46))
        tw = d.textlength(text, font=font)
        box = d.textbbox((0, 0), text, font=font)
        tx = w * 0.34 - tw / 2.0
        ty = h * 0.52 - (box[3] - box[1]) / 2.0 - box[1]
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(glow).text((tx, ty), text, font=font, fill=GOLD_HI + (170,))
        img = Image.alpha_composite(img, glow.filter(
            ImageFilter.GaussianBlur(1.6 * SS)))
        d = ImageDraw.Draw(img)
        d.text((tx, ty), text, font=font, fill=(255, 246, 210, 255))
    return img.resize((W, H), Image.LANCZOS)


def _spines(w, h, centre):
    """Dorsal spines along the ridge."""
    out = []
    for i in range(8, len(centre) - 12, 7):
        x, cy, half = centre[i]
        hgt = half * (0.55 if i % 2 else 0.85)
        out.append([(x - half * 0.7, cy - half + 1),
                    (x + half * 0.1, cy - half - hgt),
                    (x + half * 0.8, cy - half + 1)])
    return out


def _tail(d, centre, h):
    x, cy, half = centre[0]
    rr = half * 1.5
    d.ellipse([x - rr, cy - rr, x + rr, cy + rr], fill=GOLD, outline=INK)
    d.ellipse([x - rr * 0.45, cy - rr * 0.45, x + rr * 0.5, cy + rr * 0.5],
              fill=(90, 52, 14))


def _vague_head(d, head, body_col, eye_col):
    """The head shape, unlit: enough to see the animal when the meter is empty."""
    for key in ("horn_a", "horn_b", "skull", "snout", "jaw"):
        _poly(d, head[key], body_col, INK)
    _poly(d, head["mouth"], MOUTH)
    ex0, ey0 = head["eye"][0]
    ex1, ey1 = head["eye"][1]
    d.ellipse([ex0, ey0, ex1, ey1], fill=eye_col)


def _detail_head(d, head, bright=False):
    """The lit head: mane, horns, skull, snout, open jaw, teeth, eye, nostril."""
    body = GOLD_LO if bright else GOLD
    hi = GOLD_HI
    for spike in head["mane"]:
        _poly(d, spike, body, INK)
    _poly(d, head["horn_a"], hi, INK)
    _poly(d, head["horn_b"], body, INK)
    _poly(d, head["skull"], body, INK)
    _poly(d, head["snout"], hi, INK)
    _poly(d, head["mouth"], MOUTH)
    _poly(d, head["jaw"], body, INK)
    # teeth: three from the upper jaw, two from the lower
    hx, s = head["hx"], head["s"]
    cy = head["cy"]
    for i, tx in enumerate((44, 53, 62)):
        base = cy + 6 * s
        d.polygon([(hx + tx * s, base), (hx + (tx + 3) * s, base),
                   (hx + (tx + 1.5) * s, base + 3.2 * s)], fill=hi)
    for tx in (40, 52):
        base = cy + 12 * s
        d.polygon([(hx + tx * s, base), (hx + (tx + 3) * s, base),
                   (hx + (tx + 1.5) * s, base - 2.6 * s)], fill=hi)
    ex0, ey0 = head["eye"][0]
    ex1, ey1 = head["eye"][1]
    d.ellipse([ex0, ey0, ex1, ey1], fill=RED, outline=INK)
    d.ellipse([ex0 + (ex1 - ex0) * 0.45, ey0 + (ey1 - ey0) * 0.35,
               ex0 + (ex1 - ex0) * 0.95, ey0 + (ey1 - ey0) * 0.85], fill=INK)
    nx0, ny0 = head["nostril"][0]
    nx1, ny1 = head["nostril"][1]
    d.ellipse([nx0, ny0, nx1, ny1], fill=INK)
    # whiskers: two long curls trailing back from the snout
    for y0, dy, length in ((2.0, -1.0, 26), (5.0, 1.0, 22)):
        prev = (hx + 66 * s, cy + y0 * s)
        for i in range(1, 6):
            k = i / 5.0
            nxt = (prev[0] - length * k * s * 0.9,
                   cy + (y0 + dy * 3.2 * k * k) * s)
            d.line([prev, nxt], fill=hi, width=max(1, int(0.9 * s * SS)))
            prev = nxt


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
    print(f"power bar: {W}x{H} dragon, {SS}x supersampled, AUDACITY in gold "
          f"with no outline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
