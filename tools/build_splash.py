"""Build the splash screen that plays before the title.

Ikemen draws it from data/ikemen1/logo.def (system.def points at it with
``logo.storyboard = logo.def``), and the storyboard's layers come from
data/ikemen1/system.sff. Both ship with the engine data and are restored on
every build, so the splash is generated here rather than committed by hand.

If art_src/ui/splash.png (or concept_art/ui/splash.png) exists it becomes the
splash, cover-cropped to 1280x720. With no plate, a card is painted from the
game's own wordmark over a night sky, so the splash exists before painted art
is supplied.

Run:  python3 tools/build_splash.py
"""

from __future__ import annotations

import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYSTEM_SFF = os.path.join(ROOT, "data", "ikemen1", "system.sff")
LOGO_DEF = os.path.join(ROOT, "data", "ikemen1", "logo.def")

# The splash is a full 1280x720 frame, drawn with the axis at its centre.
CANVAS = (1280, 720)
AXIS = (640, 360)
# Group 220 is not used by the engine's own system.sff (0, 98, 100-102,
# 110-113, 150-192, 200-204, 400-403, 500, 600, 610, 700, 800, 810, 921-923,
# 1000), so the poster cannot collide with screenpack art.
SPRITE = (220, 0)

SECONDS = 4.0
FADE_IN = 30
FADE_OUT = 45

PLATES = (os.path.join(ROOT, "art_src", "ui", "splash.png"),
          os.path.join(ROOT, "concept_art", "ui", "splash.png"))


def cover(img, size):
    """Scale to fill ``size`` and crop the overflow, keeping the centre."""
    k = max(size[0] / float(img.width), size[1] / float(img.height))
    img = img.resize((max(1, int(round(img.width * k))),
                      max(1, int(round(img.height * k)))), Image.LANCZOS)
    left = (img.width - size[0]) // 2
    top = (img.height - size[1]) // 2
    return img.crop((left, top, left + size[0], top + size[1]))


def night_sky():
    """Deep navy to violet, with a scatter of stars and a soft vignette."""
    sky = art.vgrad(CANVAS, [(0, (10, 14, 40)), (0.45, (26, 24, 78)),
                             (1, (48, 18, 62))])
    rnd = random.Random(7)
    stars = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    d = ImageDraw.Draw(stars)
    for _ in range(260):
        x, y = rnd.randrange(CANVAS[0]), rnd.randrange(CANVAS[1])
        r = rnd.choice((1, 1, 1, 2))
        a = rnd.randint(60, 210)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 250, 235, a))
    sky.alpha_composite(stars.filter(ImageFilter.GaussianBlur(0.4)))

    # a warm pool of light where the logo will sit
    halo = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([CANVAS[0] * 0.18, CANVAS[1] * 0.10,
                                  CANVAS[0] * 0.82, CANVAS[1] * 0.86],
                                 fill=(120, 90, 255, 46))
    sky.alpha_composite(halo.filter(ImageFilter.GaussianBlur(90)))

    # darken the corners so the poster-sized frame does not look flat
    vign = Image.new("L", CANVAS, 0)
    ImageDraw.Draw(vign).ellipse([-CANVAS[0] * 0.25, -CANVAS[1] * 0.35,
                                  CANVAS[0] * 1.25, CANVAS[1] * 1.35], fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(120))
    shade = Image.new("RGBA", CANVAS, (0, 0, 0, 255))
    shade.putalpha(vign.point(lambda v: int((255 - v) * 0.55)))
    sky.alpha_composite(shade)
    return sky


def fallback_card():
    """The painted splash: the game's wordmark on a night sky."""
    card = night_sky()
    try:
        import build_title
        logo, box = build_title.wordmark()
    except Exception as exc:                      # pragma: no cover - defensive
        print(f"  (no wordmark for the splash: {exc})")
        return card

    logo = logo.crop(box)
    k = (CANVAS[0] * 0.56) / float(logo.width)
    logo = logo.resize((max(1, int(round(logo.width * k))),
                        max(1, int(round(logo.height * k)))), Image.LANCZOS)

    glow = logo.filter(ImageFilter.GaussianBlur(16))
    glow.putalpha(glow.getchannel("A").point(lambda v: int(v * 0.55)))
    x = (CANVAS[0] - logo.width) // 2
    y = int(CANVAS[1] * 0.46) - logo.height // 2
    card.alpha_composite(glow, (x, y))
    card.alpha_composite(logo, (x, y))
    return card


def poster():
    """The splash artwork: a painted plate if supplied, else the fallback."""
    for path in PLATES:
        if os.path.isfile(path):
            img = Image.open(path).convert("RGBA")
            if abs(img.width / float(img.height) - 16 / 9.0) > 0.06:
                print(f"  warning: {os.path.relpath(path, ROOT)} is "
                      f"{img.width}x{img.height}, not 16:9; it will be cropped")
            return cover(img, CANVAS), path
    return fallback_card(), None


def storyboard():
    """The logo.def that plays the poster once, then hands over to the title."""
    end = int(round(SECONDS * 60))
    return (
        "[Info]\n"
        "localcoord = 1280,720\n"
        "\n"
        ";------------------------------------\n"
        "[Scene 0]\n"
        "; Splash card: fades up from black, holds, then fades to the title.\n"
        "bg.name = Splash\n"
        f"fadein.time = {FADE_IN}\n"
        f"fadeout.time = {FADE_OUT}\n"
        f"end.time = {end}\n"
        "\n"
        "[Splash Poster]\n"
        "type = normal\n"
        f"spriteno = {SPRITE[0]}, {SPRITE[1]}\n"
        "start = 0, 0\n"
        "mask = 0\n"
    )


def write_system_sprite(image, axis=AXIS):
    """Put ``image`` into system.sff at SPRITE, replacing it if it is there."""
    if not os.path.isfile(SYSTEM_SFF):
        raise SystemExit("data/ikemen1/system.sff is missing - fetch the engine "
                         "data first")
    _d, sprites, palettes = sff.read_sff(SYSTEM_SFF)

    out, replaced = [], False
    for sp in sprites:
        if (sp["group"], sp["number"]) == SPRITE:
            out.append({"group": SPRITE[0], "number": SPRITE[1],
                        "image": image, "axis": axis})
            replaced = True
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"],
                        "link": sp["link"]})
    if not replaced:
        out.append({"group": SPRITE[0], "number": SPRITE[1],
                    "image": image, "axis": axis})

    # Build in memory and swap in: opening the real path first would truncate a
    # 9 MB engine asset if anything below raised.
    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: built file has no SFF signature")
    with open(SYSTEM_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(SYSTEM_SFF + ".tmp", SYSTEM_SFF)
    return len(out), replaced


def build():
    if not os.path.isfile(LOGO_DEF):
        raise SystemExit("data/ikemen1/logo.def is missing - fetch the engine "
                         "data first")

    art_img, source = poster()
    if source:
        print(f"using painted splash {os.path.relpath(source, ROOT)}")
    else:
        print("no art_src/ui/splash.png - painting the fallback splash card")

    total, replaced = write_system_sprite(art_img)

    with open(LOGO_DEF + ".tmp", "w", encoding="utf-8") as f:
        f.write(storyboard())
    os.replace(LOGO_DEF + ".tmp", LOGO_DEF)

    # Read both back: a splash that does not resolve is a black screen at
    # startup, and the engine cannot be asked about it here.
    _d, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    have = {(sp["group"], sp["number"]) for sp in sprites}
    if SPRITE not in have:
        raise SystemExit(f"splash sprite {SPRITE} did not make it into system.sff")
    with open(LOGO_DEF, encoding="utf-8") as f:
        text = f.read()
    if f"spriteno = {SPRITE[0]}, {SPRITE[1]}" not in text:
        raise SystemExit("logo.def does not reference the splash sprite")

    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    art_img.save(os.path.join(ROOT, "artifacts", "splash.png"))
    print(f"wrote the splash into data/ikemen1/system.sff "
          f"({total} sprites, {SPRITE[0]},{SPRITE[1]} "
          f"{'replaced' if replaced else 'added'}) and data/ikemen1/logo.def "
          f"({SECONDS:.0f}s)")


if __name__ == "__main__":
    build()
