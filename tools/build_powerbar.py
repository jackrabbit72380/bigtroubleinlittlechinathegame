"""Paint the top power meters as the dragon from the concept art.

Ikemen draws the power bar at the top of the screen from data/fight.sff: the
trough (40,0), a frame (41,0), the filled front (43,0) and a frontMax sprite
(44,0) that only appears at full power.

The reference is the gold dragon lying along the roof: head low at the LEFT,
neck rising into one big arch, the body falling into a trough in the middle,
then rising again into a curled tail that ends in a flared fin at the RIGHT. The
whole animal is covered in big overlapping plates.

Two ways to get the art:

1. Drop the concept picture in as ``concept_art/ui/powerbar.png`` (or .jpg /
   .webp). If that file exists it is cut to the meter's shape and used as-is, so
   the bar is literally the concept art. Nothing is painted over it.
2. Otherwise the dragon is painted here on the concept's own silhouette.

Either way the finished art is fitted into the 460x76 sprite, so nothing is ever
cut off at an edge.

Run:  python3 tools/build_powerbar.py
"""

from __future__ import annotations

import glob
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
CONCEPT_GLOB = os.path.join(ROOT, "concept_art", "ui", "powerbar.*")

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
    """Centre line and half-thickness, in the un-padded meter's coordinates."""
    line = _curve([(fx * w, fy * h) for fx, fy in PATH])
    out = []
    for i, (x, y) in enumerate(line):
        t = i / float(len(line) - 1)
        # thickest through the arch and the trough, tapering to the tail
        half = h * (0.180 + 0.045 * math.sin(math.pi * min(1.0, t * 0.85))
                    - 0.060 * max(0.0, t - 0.75) / 0.25)
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


def _scales(d, line):
    """Big overlapping plates across the animal, following its curve."""
    n = len(line)
    left, right = line[0][0], line[-1][0]
    step = (right - left) / 46.0
    for r in range(3):
        x = left + step * (0.5 if r % 2 else 0.0)
        while x < right:
            f = (x - left) / max(1.0, right - left)
            idx = min(n - 1, max(0, int(round(f * (n - 1)))))
            _x, cy, half = line[idx]
            yy = cy + (-0.60 + 0.60 * r) * half
            rr = step * 0.72
            d.arc([x - rr, yy - rr * 0.95, x + rr, yy + rr * 0.95],
                  188, 352, fill=CREVICE + (238,), width=int(max(2, step * 0.30)))
            d.arc([x - rr, yy - rr * 1.06, x + rr, yy + rr * 0.84],
                  194, 346, fill=GOLD_HI + (200,), width=int(max(1, step * 0.11)))
            if int((x - left) / step) % 6 == 2:
                d.arc([x - rr * 0.72, yy - rr * 0.55, x + rr * 0.72,
                       yy + rr * 0.62], 205, 335, fill=GREEN + (195,),
                      width=int(max(2, step * 0.20)))
            x += step


def _head(d, line, unit):
    """The head at the left end, facing left, as in the concept."""
    x0, y0, half = line[0]
    s = unit * 1.30
    hx = x0 + 8 * s
    hy = y0 - 2 * s

    # neck into the skull
    _taper(d, [(hx + 30 * s, hy + 8 * s), (hx + 14 * s, hy + 2 * s),
               (hx - 2 * s, hy - 2 * s)], 30 * s, 24 * s, GOLD_LO, INK)
    # skull
    d.ellipse([hx - 18 * s, hy - 14 * s, hx + 12 * s, hy + 12 * s], fill=GOLD_LO,
              outline=INK, width=max(1, int(1.2 * s)))
    # snout and upper jaw, pointing left
    _taper(d, [(hx - 8 * s, hy - 7 * s), (hx - 26 * s, hy - 7 * s),
               (hx - 40 * s, hy - 2 * s)], 18 * s, 7 * s, GOLD, INK)
    # lower jaw, open
    _taper(d, [(hx - 8 * s, hy + 7 * s), (hx - 26 * s, hy + 11 * s),
               (hx - 36 * s, hy + 7 * s)], 14 * s, 5 * s, GOLD_LO, INK)
    d.polygon([(hx - 10 * s, hy - 1 * s), (hx - 38 * s, hy + 1 * s),
               (hx - 36 * s, hy + 8 * s), (hx - 10 * s, hy + 6 * s)], fill=MOUTH)
    for i in range(3):
        tx = hx - (15 + i * 7) * s
        d.polygon([(tx, hy + 1 * s), (tx - 3 * s, hy + 1 * s),
                   (tx - 1.5 * s, hy + 5 * s)], fill=GOLD_HI)
    # horns sweeping back to the right, over the mane
    _taper(d, [(hx - 2 * s, hy - 12 * s), (hx + 16 * s, hy - 22 * s),
               (hx + 34 * s, hy - 20 * s), (hx + 46 * s, hy - 9 * s)],
           8 * s, 1.6 * s, GOLD_HI, INK)
    _taper(d, [(hx + 6 * s, hy - 12 * s), (hx + 20 * s, hy - 18 * s),
               (hx + 32 * s, hy - 13 * s)], 5 * s, 1.3 * s, GOLD_LO, INK)
    # mane flowing back along the neck
    for i, (dy, ln, lift) in enumerate(((-7, 34, -16), (3, 30, 8))):
        base = (hx + 4 * s, hy + dy * s)
        pts = [base, (base[0] + ln * 0.4 * s, base[1] + lift * 0.6 * s),
               (base[0] + ln * 0.75 * s, base[1] + lift * 1.1 * s),
               (base[0] + ln * s, base[1] + (lift + 4) * s)]
        _taper(d, _curve(pts, 12), 9 * s, 2.0 * s,
               GOLD_HI if i % 2 else GOLD, INK)
    # eye, nostril, whiskers trailing back
    d.ellipse([hx - 14 * s, hy - 9 * s, hx - 3 * s, hy + 1 * s], fill=RED,
              outline=INK)
    d.ellipse([hx - 10 * s, hy - 6.5 * s, hx - 6 * s, hy - 1.5 * s], fill=INK)
    d.ellipse([hx - 36 * s, hy + 1 * s, hx - 33 * s, hy + 3 * s], fill=INK)
    for dy, dirn in ((-6, -1.0), (9, 1.0)):
        base = (hx - 34 * s, hy + dy * s)
        pts = [base, (base[0] + 12 * s, base[1] + dirn * 4 * s),
               (base[0] + 26 * s, base[1] + dirn * 7 * s),
               (base[0] + 38 * s, base[1] + dirn * 5 * s)]
        _taper(d, _curve(pts, 12), 2.0 * s, 0.6 * s, GOLD_HI)


def _tail_fin(d, line):
    """The flared fin where the tail lifts at the right end."""
    x, y, half = line[-1]
    for dy, ln in ((-1.0, 22), (0.0, 26), (1.0, 20)):
        pts = [(x - half * 1.2, y + dy * half * 0.55),
               (x + ln * 0.5, y + dy * half * 1.1),
               (x + ln * 0.95, y + dy * half * 1.5),
               (x + ln * 1.25, y + dy * half * 1.15)]
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


def _dragon_raw(kind):
    """Paint one meter sprite on a canvas padded well past the sprite edges.

    The padding is what stops the craftsmanship being cut off: the head, the
    mane and the fin all reach outside the meter's 460x76 box, so they are drawn
    here and the finished art is fitted back into the box afterwards.
    """
    w, h = W * SS, H * SS
    pad_x, pad_y = int(w * 0.14), int(h * 0.55)
    cw, ch = w + 2 * pad_x, h + 2 * pad_y

    line = [(x + pad_x, y + pad_y, r) for x, y, r in _spine(w, h)]
    top = [(x, y - half) for x, y, half in line]
    bot = [(x, y + half) for x, y, half in reversed(line)]
    mask = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(mask).polygon([(round(x), round(y)) for x, y in top + bot],
                                 fill=255)

    img = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    if kind == "trough":
        img.paste(_gradient(cw, ch, [(0.0, (14, 10, 4)), (0.45, (42, 30, 10)),
                                     (0.75, (56, 40, 14)), (1.0, (12, 9, 3))]),
                  (0, 0), mask)
    elif kind == "frame":
        img.paste(_gradient(cw, ch, [(0.0, BRONZE), (0.30, GOLD),
                                     (0.55, GOLD_LO), (0.80, GOLD),
                                     (1.0, BRONZE)]), (0, 0), mask)
    else:
        img.paste(_gradient(cw, ch, [(0.0, (152, 120, 36)), (0.30, GOLD),
                                     (0.60, GOLD_LO), (0.86, GOLD_HI),
                                     (1.0, GOLD)]), (0, 0), mask)

    # the plates are painted on their own layer and clipped to the body, so no
    # piece of them can float in the empty corners
    sc = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    _scales(ImageDraw.Draw(sc), line)
    img = Image.alpha_composite(
        img, Image.composite(sc, Image.new("RGBA", (cw, ch), (0, 0, 0, 0)),
                             mask))

    d = ImageDraw.Draw(img)
    _head(d, line, (h / 76.0) * 1.0)
    _tail_fin(d, line)

    if kind == "trough":
        dim = Image.new("RGBA", (cw, ch), (0, 0, 0, 136))
        img = Image.alpha_composite(img, Image.composite(
            dim, Image.new("RGBA", (cw, ch), (0, 0, 0, 0)), mask))

    if kind == "front_max":
        img = Image.alpha_composite(img.filter(ImageFilter.GaussianBlur(2.0 * SS)),
                                    img)
    return img


def _label(img, cw, ch, w, h, pad_x, pad_y):
    """AUDACITY, sitting on the body with no outline."""
    d = ImageDraw.Draw(img)
    text = "AUDACITY"
    font = art.font(int(h * 0.21))
    tw = d.textlength(text, font=font)
    box = d.textbbox((0, 0), text, font=font)
    tx = pad_x + w * 0.52 - tw / 2.0
    ty = pad_y + h * 0.52 - (box[3] - box[1]) / 2.0 - box[1]
    glow = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(glow).text((tx, ty), text, font=font, fill=GOLD_HI + (140,))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(1.5 * SS)))
    ImageDraw.Draw(img).text((tx, ty), text, font=font, fill=(255, 246, 206, 255))


def _fit(raws):
    """Crop the painted canvases to their shared artwork and size to the sprite.

    One box for all four, so the trough, frame and fill stay line for line in
    step with each other.
    """
    boxes = [img.split()[3].getbbox() for img in raws]
    boxes = [b for b in boxes if b]
    left = min(b[0] for b in boxes)
    top = min(b[1] for b in boxes)
    right = max(b[2] for b in boxes)
    bottom = max(b[3] for b in boxes)
    w, h = raws[0].size
    # a hair of breathing room so nothing lands hard on the sprite edge
    px = max(1, int((right - left) * 0.012))
    py = max(1, int((bottom - top) * 0.030))
    box = (max(0, left - px), max(0, top - py),
           min(w, right + px), min(h, bottom + py))
    return [img.crop(box).resize((W, H), Image.LANCZOS) for img in raws], box


def _concept_path():
    for ext in ("png", "PNG", "jpg", "JPG", "jpeg", "JPEG", "webp", "WEBP"):
        p = os.path.join(ROOT, "concept_art", "ui", "powerbar." + ext)
        if os.path.isfile(p):
            return p
    hits = sorted(h for h in glob.glob(CONCEPT_GLOB) if os.path.isfile(h))
    return hits[0] if hits else None


def _from_concept(path):
    """Cut the dropped-in concept picture to the meter's shape, unchanged."""
    src = Image.open(path).convert("RGBA")
    box = src.split()[3].getbbox() or (0, 0, src.width, src.height)
    art_img = src.crop(box).resize((W, H), Image.LANCZOS)

    def shade(img, mul, alpha=255):
        r, g, b, a = img.split()
        return Image.merge("RGBA", (
            r.point(lambda v: min(255, int(v * mul))),
            g.point(lambda v: min(255, int(v * mul))),
            b.point(lambda v: min(255, int(v * mul))),
            a.point(lambda v: v * alpha // 255)))

    trough = shade(art_img, 0.42)
    frame = art_img
    front = shade(art_img, 1.06)
    front_max = front.copy()
    return {(40, 0): trough, (41, 0): frame, (43, 0): front,
            (44, 0): front_max}


def _patch_section(text, name, fn):
    """Run fn over one [Section] only, never over the rest of the file."""
    lines = text.split("\n")
    start = next((i for i, ln in enumerate(lines)
                  if ln.strip().lower() == "[" + name.lower() + "]"), None)
    if start is None:
        return text
    end = next((j for j in range(start + 1, len(lines))
                if lines[j].lstrip().startswith("[")), len(lines))
    body = "\n".join(lines[start:end])
    new = fn(body)
    if new == body:
        return text
    return "\n".join(lines[:start] + new.split("\n") + lines[end:])


def _patch_powerbar(body):
    # the meter is W wide, anchored on its right edge
    body = re.sub(r"(?m)^(\s*p1\.range\.x\s*=\s*)-?\d+\s*,\s*-?\d+\s*$",
                  r"\g<1>-4, -%d" % (W - 4), body)
    body = re.sub(r"(?m)^(\s*p2\.range\.x\s*=\s*)-?\d+\s*,\s*-?\d+\s*$",
                  r"\g<1>4, %d" % (W - 4), body)
    # AUDACITY replaces the maximum text ("M"), which sits under the bar
    body = re.sub(r"(?m)^(\s*p[12]\.counterMax\.text\s*=\s*).*$",
                  r"\g<1>AUDACITY", body)
    body = re.sub(r"(?m)^(\s*p[12]\.counterMax\.palfx\.mul\s*=\s*).*$",
                  r"\g<1>255, 214, 120", body)
    # the bar is H tall, so the counters sit below it, not buried in the art
    body = re.sub(
        r"(?m)^(\s*p[12]\.counter(?:Max|\d+)?\.offset\s*=\s*)(-?\d+)\s*,\s*-?\d+\s*$",
        lambda m: "%s%s,%d" % (m.group(1), m.group(2), H + 4), body)
    # A sine-modulated colour is the engine's blink. Every front and counter
    # level had one, so the meter strobed - fastest at full power, where
    # frontMax and counterMax pulsed on a 10-frame cycle. The tints stay, the
    # flashing goes.
    body = re.sub(r"(?m)^[ \t]*p[12]\.(?:front\w*|counter\w*)\.palfx\.sinmul"
                  r"[ \t]*=[^\r\n]*(?:\r?\n)?", "", body)
    return body


def patch_fight_def():
    if not os.path.isfile(FIGHT_DEF):
        return False
    with open(FIGHT_DEF, encoding="utf-8", errors="surrogateescape",
              newline="") as f:
        text = f.read()
    orig = text
    text = _patch_section(text, "Powerbar", _patch_powerbar)
    if text != orig:
        with open(FIGHT_DEF + ".tmp", "w", encoding="utf-8",
                  errors="surrogateescape", newline="") as f:
            f.write(text)
        os.replace(FIGHT_DEF + ".tmp", FIGHT_DEF)
    return text != orig


def main():
    # The dragon is the meter: its back is the health bar and its belly is the
    # audacity bar. It used to be opt-in, and the shipped def kept the stock
    # 206x18 range while the art grew, so the fill covered half the belly.

    if not os.path.isfile(FIGHT_SFF):
        raise SystemExit("data/fight.sff is missing - fetch the engine data first")

    mine = _concept_path()
    if mine:
        painted = {k: v.transpose(Image.FLIP_LEFT_RIGHT)
                   for k, v in _from_concept(mine).items()}
        note = "cut from " + os.path.relpath(mine, ROOT)
    else:
        raws = [_dragon_raw(kind) for kind in
                ("trough", "frame", "front", "front_max")]
        for kind, img in zip(("trough", "frame", "front", "front_max"), raws):
            bb = img.split()[3].getbbox()
            if bb and (bb[0] <= 0 or bb[1] <= 0
                       or bb[2] >= img.width or bb[3] >= img.height):
                raise SystemExit(f"{kind} art reaches the canvas edge - widen "
                                 f"the padding in _dragon_raw")
        fitted, box = _fit(raws)
        # the head belongs on the inside of the screen: p1's meter is on the
        # left and p2's is the same art mirrored, so both faces point at the
        # middle of the fight
        fitted = [img.transpose(Image.FLIP_LEFT_RIGHT) for img in fitted]
        painted = dict(zip(((40, 0), (41, 0), (43, 0), (44, 0)), fitted))
        note = (f"painted on the concept's path (head right, arch, trough, "
                f"curled tail right), crop {box[2] - box[0]}x{box[3] - box[1]}")

    raw, sprites, palettes = sff.read_sff(FIGHT_SFF)
    out, done = [], set()
    for sp in sprites:
        key = (sp["group"], sp["number"])
        if key in painted:
            out.append({"group": key[0], "number": key[1],
                        "image": painted[key], "axis": AXIS})
            done.add(key)
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"], "link": sp["link"]})
    for key, image in painted.items():
        if key not in done:
            out.append({"group": key[0], "number": key[1], "image": image,
                        "axis": AXIS})

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
        sheet.alpha_composite(
            painted[key].resize((W * scale, H * scale), Image.LANCZOS),
            (12, y))
        y += H * scale + 12
    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    sheet.convert("RGB").save(os.path.join(ROOT, "artifacts", "powerbar.png"))
    print(f"power bar: {W}x{H}, {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
