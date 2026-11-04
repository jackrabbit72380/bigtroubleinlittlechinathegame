"""Paint the VS banner: two dragons across the top of the screen.

The VS lifebars in data/fight.def get a background layer of dragon art - red on
the left, green on the right - with their heads turned in towards the green and
red yin-yang and the round timer in the middle.

It is drawn as two halves, one per player, anchored on the screen centre:

    20,0   left half, 640x260, axis on its bottom right corner  -> p1.bg1
    20,1   right half, green, axis on its bottom left corner    -> p2.bg1

Two halves rather than one wide sprite keeps each half under its own lifebar, so
neither can end up covering the other player's bars whatever order the engine
draws them in. Only [Lifebar] is touched, so VS gets the dragons and the simul,
tag and turns HUDs are left exactly as they were.

Run:  python3 tools/build_banner.py
"""

import math
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import sff  # noqa: E402

FIGHT_SFF = os.path.join(ROOT, "data", "fight.sff")
FIGHT_DEF = os.path.join(ROOT, "data", "fight.def")

GROUP = 20
HALF, H = 640, 260          # one half of the 1280x720 fight screen
SS = 3                      # supersample factor
SCREEN = 640                # screen centre: where the two halves meet

RED = {
    "dark": (64, 10, 8), "mid": (146, 30, 20), "light": (198, 66, 40),
    "rim": (244, 138, 96), "belly": (222, 162, 112),
    "plate": (250, 236, 210), "horn": (240, 224, 182), "eye": (255, 214, 74),
    "mouth": (52, 8, 6), "ink": (26, 5, 4), "glow": (255, 84, 48),
    "whisker": (255, 208, 148),
}
GREEN = {
    "dark": (20, 38, 14), "mid": (84, 118, 36), "light": (144, 178, 64),
    "rim": (204, 234, 136), "belly": (204, 196, 128),
    "plate": (246, 242, 214), "horn": (236, 230, 192), "eye": (255, 214, 74),
    "mouth": (18, 26, 10), "ink": (12, 20, 6), "glow": (96, 255, 120),
    "whisker": (230, 248, 180),
}

# centre line of the animal: tail at the outer edge, one hump, a trough, then the
# neck rising towards the middle of the screen where the head takes over
PATH = ((0.020, 0.560), (0.052, 0.650), (0.108, 0.622), (0.168, 0.508),
        (0.242, 0.408), (0.322, 0.398), (0.406, 0.472), (0.488, 0.542),
        (0.566, 0.506), (0.628, 0.418), (0.670, 0.356))

HEAD_JOINT = (0.670, 0.356)     # where the neck meets the skull


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


def _spine(w, h):
    """Centre line plus half-thickness: heavy body, thick shoulder, thin tail."""
    line = _curve([(fx * w, fy * h) for fx, fy in PATH])
    out = []
    for i, (x, y) in enumerate(line):
        t = i / float(len(line) - 1)
        base = 0.030 + 0.066 * math.sin(math.pi * min(1.0, t * 1.04)) ** 0.5
        shoulder = 1.0 + 0.30 * math.exp(-((t - 0.88) / 0.14) ** 2)
        half = h * base * shoulder
        out.append((x, y, max(h * 0.014, half)))
    return out


def _taper(d, pts, w0, w1, fill, outline=None):
    """Stroke a tapered limb along a polyline."""
    segs = max(1, len(pts) - 1)
    for i in range(segs):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        steps = max(4, int(math.hypot(x1 - x0, y1 - y0) * 0.8))
        for s in range(steps + 1):
            t = s / float(steps)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            r = (w0 + (w1 - w0) * ((i + t) / segs)) / 2.0
            if outline:
                d.ellipse([x - r - 1, y - r - 1, x + r + 1, y + r + 1],
                          fill=outline)
        for s in range(steps + 1):
            t = s / float(steps)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            r = (w0 + (w1 - w0) * ((i + t) / segs)) / 2.0
            d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def _tangent(line, i):
    a = line[max(0, i - 2)]
    b = line[min(len(line) - 1, i + 2)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1.0
    return dx / n, dy / n


def _body(img, line, pal):
    """Heavy shaded tube: dark underside, belly band, lit spine ridge."""
    d = ImageDraw.Draw(img)
    for x, y, r in line:
        d.ellipse([x - r, y - r, x + r, y + r], fill=pal["dark"])
    for x, y, r in line:
        d.ellipse([x - r * 0.95, y - r * 0.93 + r * 0.06,
                   x + r * 0.95, y + r * 0.93 + r * 0.06], fill=pal["mid"])
    for x, y, r in line:
        d.ellipse([x - r * 0.70, y + r * 0.10, x + r * 0.70, y + r * 0.94],
                  fill=pal["belly"])
    ridge = [(x, y - r * 0.68) for x, y, r in line]
    _taper(d, ridge, 5 * SS, 2 * SS, pal["rim"])


def _plates(img, line, pal):
    """Outlined crest scales sunk into the back of the body."""
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


def _spikes(img, line, pal):
    """Small dorsal fins along the arch of the back."""
    d = ImageDraw.Draw(img)
    n = len(line)
    for i in range(5, n - 8, max(4, n // 14)):
        x, y, r = line[i]
        d.polygon([(x - r * 0.40, y - r * 0.86), (x - r * 0.04, y - r * 1.34),
                   (x + r * 0.44, y - r * 0.86)],
                  fill=pal["mid"], outline=pal["ink"])


def _leg(img, line, t, length, forward, pal):
    """One thick leg with a clawed foot, hanging off the body."""
    d = ImageDraw.Draw(img)
    i = int(t * (len(line) - 1))
    x, y, r = line[i]
    tx, ty = _tangent(line, i)
    nx, ny = -ty, tx
    if ny < 0:
        nx, ny = -nx, -ny
    hip = (x + nx * r * 0.50, y + ny * r * 0.30)
    knee = (hip[0] + nx * length * 0.52 + tx * forward * length * 0.34,
            hip[1] + ny * length * 0.52 + ty * forward * length * 0.34)
    foot = (knee[0] + nx * length * 0.44 - tx * forward * length * 0.26,
            knee[1] + ny * length * 0.44 - ty * forward * length * 0.26)
    _taper(d, [hip, knee], r * 1.05, r * 0.70, pal["mid"], pal["ink"])
    _taper(d, [knee, foot], r * 0.70, r * 0.46, pal["mid"], pal["ink"])
    for k in (-1, 0, 1):
        tip = (foot[0] + (nx + k * tx * 0.85) * length * 0.32,
               foot[1] + (ny + k * ty * 0.85) * length * 0.32)
        _taper(d, [foot, tip], r * 0.26, r * 0.08, pal["horn"], pal["ink"])


def _head(img, line, pal):
    """The head, drawn facing right so it looks in towards the timer."""
    s = SS
    jx, jy, jr = line[int(0.96 * (len(line) - 1))]
    d = ImageDraw.Draw(img)
    # a solid neck first, so the skull never reads as floating next to the body
    _taper(d, [(jx - 46 * s, jy + 8 * s), (jx - 8 * s, jy + 2 * s)],
           jr * 1.9, jr * 1.7, pal["mid"], pal["ink"])

    def P(dx, dy):
        return (jx + dx * s, jy + dy * s)

    # neck thickening under the skull
    _taper(d, [P(-40, 16), P(-14, 6), P(4, 2)], 40 * s, 44 * s, pal["mid"],
           pal["ink"])
    # skull
    d.ellipse([P(-6, -32)[0], P(-6, -32)[1], P(60, 30)[0], P(60, 30)[1]],
              fill=pal["light"], outline=pal["ink"], width=int(1.8 * s))
    # brow ridge
    d.polygon([P(4, -30), P(58, -24), P(52, -6), P(2, -12)],
              fill=pal["mid"], outline=pal["ink"])
    # muzzle and upper jaw
    _taper(d, [P(44, -8), P(88, -6), P(116, 4)], 26 * s, 14 * s, pal["mid"],
           pal["ink"])
    # lower jaw, open
    _taper(d, [P(42, 14), P(84, 30), P(110, 22)], 20 * s, 10 * s,
           pal["light"], pal["ink"])
    # mouth
    d.polygon([P(46, 2), P(114, 6), P(106, 22), P(46, 16)], fill=pal["mouth"])
    for i in range(4):
        tx = 54 + i * 15
        d.polygon([P(tx, 2), P(tx + 8, 2), P(tx + 4, 13)], fill=pal["horn"])
    # eye
    d.ellipse([P(12, -26)[0], P(12, -26)[1], P(34, -2)[0], P(34, -2)[1]],
              fill=pal["eye"], outline=pal["ink"], width=int(1.3 * s))
    d.ellipse([P(21, -19)[0], P(21, -19)[1], P(32, -7)[0], P(32, -7)[1]],
              fill=pal["ink"])
    # horns sweeping back over the mane
    _taper(d, _curve([P(10, -30), P(-26, -64), P(-62, -60), P(-84, -38)], 16),
           9 * s, 1.6 * s, pal["horn"], pal["ink"])
    _taper(d, _curve([P(2, -20), P(-30, -46), P(-58, -38)], 16),
           6 * s, 1.2 * s, pal["horn"], pal["ink"])
    # mane flowing back along the neck
    for dy, ln, lift in ((-24, 62, -22), (-4, 58, 6), (16, 46, 20), (30, 34, 28)):
        base = P(-2, dy)
        pts = [base, (base[0] - ln * 0.45 * s, base[1] + lift * 0.55 * s),
               (base[0] - ln * 0.78 * s, base[1] + lift * 1.05 * s),
               (base[0] - ln * s, base[1] + (lift + 6) * s)]
        _taper(d, _curve(pts, 14), 13 * s, 2 * s, pal["light"], pal["ink"])
    # nostril
    d.ellipse([P(98, 0)[0], P(98, 0)[1], P(106, 8)[0], P(106, 8)[1]],
              fill=pal["ink"])
    # beard
    _taper(d, _curve([P(80, 24), P(68, 48), P(42, 58)], 14), 10 * s, 1.6 * s,
           pal["light"], pal["ink"])
    # whiskers trailing back
    for dy, dirn in ((-10, -1.0), (14, 1.0)):
        base = P(112, dy)
        pts = [base, (base[0] - 34 * s, base[1] + dirn * 12 * s),
               (base[0] - 70 * s, base[1] + dirn * 22 * s),
               (base[0] - 104 * s, base[1] + dirn * 16 * s)]
        _taper(d, _curve(pts, 16), 3.4 * s, 0.8 * s, pal["whisker"])


def _backdrop(w, h, pal):
    """Storm-dark wash that fades out before the bottom of the banner."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for y in range(h):
        k = y / float(h - 1)
        alpha = int(226 * (1.0 - k) ** 1.5)
        col = (int(7 + 14 * k), int(9 + 18 * k), int(22 + 26 * k), alpha)
        for x in range(w):
            px[x, y] = col
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([w * 0.68, -h * 0.18, w * 1.12, h * 0.60],
               fill=pal["glow"] + (48,))
    glow = glow.filter(ImageFilter.GaussianBlur(w * 0.05))
    return Image.alpha_composite(img, glow)


def paint(pal, flip):
    w, h = HALF * SS, H * SS
    img = _backdrop(w, h, pal)
    line = _spine(w, h)
    _body(img, line, pal)
    _plates(img, line, pal)
    _spikes(img, line, pal)
    _leg(img, line, 0.34, h * 0.28, 1.0, pal)
    _leg(img, line, 0.62, h * 0.24, -1.0, pal)
    _leg(img, line, 0.86, h * 0.26, 1.0, pal)
    _head(img, line, pal)
    if flip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img.resize((HALF, H), Image.LANCZOS)


def _write_sprites(painted):
    """Put both halves into fight.sff, keeping every other sprite untouched."""
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


def _pos(body, side):
    m = re.search(r"(?m)^\s*%s\.pos\s*=\s*(-?\d+)\s*,\s*(-?\d+)" % side, body)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def patch_lifebar():
    """Give the VS lifebars the banner as a background layer."""
    with open(FIGHT_DEF, encoding="utf-8", errors="surrogateescape",
              newline="") as f:
        lines = f.read().split("\n")
    start, end = _section(lines, "Lifebar")
    body = "\n".join(lines[start:end])
    p1 = _pos(body, "p1")
    p2 = _pos(body, "p2")
    # each half's axis sits on the screen centre, one bar's height down
    want = {
        "p1.bg1.spr": "%d,0" % GROUP,
        "p1.bg1.offset": "%d,%d" % (SCREEN - p1[0], H - p1[1]),
        "p1.bg1.xshear": "0",
        "p2.bg1.spr": "%d,1" % GROUP,
        "p2.bg1.offset": "%d,%d" % (SCREEN - p2[0], H - p2[1]),
        "p2.bg1.xshear": "0",
    }
    kept = [ln for ln in lines[start:end]
            if ln.split("=")[0].strip().lower() not in want]
    out = []
    for ln in kept:
        out.append(ln)
        key = ln.split("=")[0].strip().lower()
        for side in ("p1", "p2"):
            if key == "%s.bg0.offset" % side:
                out.extend("%s.%s = %s" % (side, k, want["%s.%s" % (side, k)])
                           for k in ("bg1.spr", "bg1.offset", "bg1.xshear"))
    if not any("bg1.spr" in ln for ln in out):
        out.extend("%s = %s" % (k, v) for k, v in want.items())
    lines[start:end] = out
    with open(FIGHT_DEF + ".tmp", "w", encoding="utf-8",
              errors="surrogateescape", newline="") as f:
        f.write("\n".join(lines))
    os.replace(FIGHT_DEF + ".tmp", FIGHT_DEF)
    return want


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
    """Split the concept picture down the middle, unchanged."""
    src = Image.open(path).convert("RGBA")
    box = src.split()[3].getbbox() or (0, 0, src.width, src.height)
    art_img = src.crop(box).resize((HALF * 2, H), Image.LANCZOS)
    left = art_img.crop((0, 0, HALF, H))
    right = art_img.crop((HALF, 0, HALF * 2, H))
    print("banner cut from %s" % os.path.relpath(path, ROOT))
    return left, right


def main():
    if not os.path.isfile(FIGHT_SFF):
        raise SystemExit("data/fight.sff is missing")

    concept = _concept_path()
    if concept:
        left, right = _from_concept(concept)
    else:
        left = paint(RED, flip=False)
        right = paint(GREEN, flip=True)
    written = _write_sprites({(GROUP, 0): (left, (HALF, H)),
                              (GROUP, 1): (right, (0, H))})
    want = patch_lifebar()

    _d, check, _p = sff.read_sff(FIGHT_SFF)
    have = {(s["group"], s["number"]): s for s in check}
    for number in (0, 1):
        sp = have.get((GROUP, number))
        if sp is None:
            raise SystemExit("banner sprite %d,%d went missing" % (GROUP, number))
        if (sp["w"], sp["h"]) != (HALF, H):
            raise SystemExit("banner sprite %d,%d is %dx%d, expected %dx%d" % (
                GROUP, number, sp["w"], sp["h"], HALF, H))

    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    full = Image.new("RGBA", (HALF * 2, H), (0, 0, 0, 0))
    full.alpha_composite(left, (0, 0))
    full.alpha_composite(right, (HALF, 0))
    full.convert("RGB").save(os.path.join(ROOT, "artifacts", "vs_banner.png"))
    print("banner: %dx%d, sprites %s, [Lifebar] %s" % (
        HALF * 2, H, written, ", ".join("%s=%s" % kv for kv in want.items())))


if __name__ == "__main__":
    main()
