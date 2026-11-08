"""Paint the countdown's yin-yang and point [Time] at it.

The round timer used to draw bare digits between the health bars. This paints a
yin-yang - green left, red right, both halves glowing - into data/fight.sff as
sprite group 30, number 0, and gives [Time] that sprite as its background, so
the digits count down underneath it.

Run after tools/build_powerbar.py, which rewrites fight.sff:

    python3 tools/build_timer.py
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import sff  # noqa: E402

FIGHT_SFF = os.path.join(ROOT, "data", "fight.sff")
FIGHT_DEF = os.path.join(ROOT, "data", "fight.def")

GROUP, NUMBER = 30, 0      # unused group in fight.sff, so nothing is replaced

R = 52                     # disc radius, in fight pixels (1280x720 space)
GLOW = 20                  # halo radius
SS = 4                     # supersample factor

GREEN = (58, 255, 138)
RED = (255, 62, 52)
RIM = (255, 226, 160)


def paint():
    """Draw the disc, then its halo, and return the finished sprite + axis."""
    n = (R + GLOW) * 2
    big = n * SS
    c = big / 2.0
    r = R * SS
    half = r / 2.0
    dot = r / 8.0

    disc = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(disc)
    # red whole, green left half, then the two lobes that turn the divide into
    # an S, and the opposite-coloured dots inside them
    d.ellipse([c - r, c - r, c + r, c + r], fill=RED + (255,))
    d.pieslice([c - r, c - r, c + r, c + r], 90, 270, fill=GREEN + (255,))
    d.ellipse([c - half, c - r, c + half, c], fill=GREEN + (255,))
    d.ellipse([c - half, c, c + half, c + r], fill=RED + (255,))
    d.ellipse([c - dot, c - half - dot, c + dot, c - half + dot],
              fill=RED + (255,))
    d.ellipse([c - dot, c + half - dot, c + dot, c + half + dot],
              fill=GREEN + (255,))
    # a warm rim keeps it readable against the dark HUD
    d.ellipse([c - r, c - r, c + r, c + r], outline=RIM + (235,),
              width=max(1, round(1.6 * SS)))

    halo = disc.filter(ImageFilter.GaussianBlur(5.5 * SS))
    alpha = halo.split()[3].point(lambda v: min(255, round(v * 2.1)))
    halo.putalpha(alpha)

    out = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    out.alpha_composite(halo)
    out.alpha_composite(disc)
    out = out.resize((n, n), Image.LANCZOS)
    return out, (n // 2, n // 2)


def write_sprite(image, axis):
    raw, sprites, palettes = sff.read_sff(FIGHT_SFF)
    out, replaced = [], False
    for sp in sprites:
        if (sp["group"], sp["number"]) == (GROUP, NUMBER):
            out.append({"group": GROUP, "number": NUMBER,
                        "image": image, "axis": axis})
            replaced = True
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"],
                        "link": sp["link"]})
    if not replaced:
        out.append({"group": GROUP, "number": NUMBER,
                    "image": image, "axis": axis})
    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    with open(FIGHT_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(FIGHT_SFF + ".tmp", FIGHT_SFF)
    return replaced


def patch_time():
    """Give [Time] the sprite as its background, above the digits."""
    with open(FIGHT_DEF, encoding="utf-8", errors="surrogateescape",
              newline="") as f:
        lines = f.read().split("\n")
    try:
        start = next(i for i, ln in enumerate(lines)
                     if ln.strip().lower() == "[time]")
    except StopIteration:
        raise SystemExit("data/fight.def has no [Time] section")
    end = next((j for j in range(start + 1, len(lines))
                if lines[j].lstrip().startswith("[")), len(lines))
    body = lines[start:end]

    want = {
        "bg.spr": "%d,%d" % (GROUP, NUMBER),
        "bg.offset": "0,55",
        "bg.palfx.sinmul": "26, 26, 26, 24",
    }
    seen = set()
    for i, ln in enumerate(body):
        key = ln.split("=")[0].strip().lower()
        if key in want and not ln.lstrip().startswith(";"):
            body[i] = "%s = %s" % (key, want[key])
            seen.add(key)
        elif ln.strip().lower().startswith(";bg.spr"):
            body[i] = "\n".join("%s = %s" % (k, v) for k, v in want.items()
                                 if k not in seen)
            seen.update(want)
    for key, value in want.items():
        if key not in seen:
            body.append("%s = %s" % (key, value))
    if not want.keys() - seen and seen == set(want.keys()):
        pass
    lines[start:end] = body
    with open(FIGHT_DEF + ".tmp", "w", encoding="utf-8",
              errors="surrogateescape", newline="") as f:
        f.write("\n".join(lines))
    os.replace(FIGHT_DEF + ".tmp", FIGHT_DEF)
    return True


def main():
    # Retired. Sprite 30,0 is not the timer's own: build_banner.py paints BOTH
    # dragon heads and the yin-yang into it as one composite, and the heads are
    # the HUD's centrepiece. Running this tool wrote a bare disc over that
    # composite, which is why the heads disappeared and the yin-yang changed
    # size. It keeps its own painter for reference, behind the same escape hatch
    # build_powerbar.py uses, so nobody loses the disc but nobody gets it by
    # accident either.
    if not os.environ.get("TIMER_PAINT"):
        print("timer: sprite 30,0 belongs to build_banner.py (heads + yin-yang); "
              "set TIMER_PAINT=1 to paint the bare disc instead")
        return
    if not os.path.isfile(FIGHT_SFF):
        raise SystemExit("data/fight.sff is missing")
    image, axis = paint()
    replaced = write_sprite(image, axis)
    patched = patch_time()
    _d, check, _p = sff.read_sff(FIGHT_SFF)
    ok = any((s["group"], s["number"]) == (GROUP, NUMBER) for s in check)
    if not ok:
        raise SystemExit("sprite 30,0 did not land in fight.sff")
    size = (image.width, image.height)
    print("yin-yang %s at %d,%d (%s), axis %s, [Time] %s" % (
        size, GROUP, NUMBER, "replaced" if replaced else "added", axis,
        "patched" if patched else "already set"))


if __name__ == "__main__":
    main()
