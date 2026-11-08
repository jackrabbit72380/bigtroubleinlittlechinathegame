"""Build the splash screen that plays before the title.

Ikemen draws it from data/ikemen1/logo.def (system.def points at it with
``logo.storyboard = logo.def``), and the storyboard's layers come from
data/ikemen1/system.sff. Both ship with the engine data and are restored on
every build, so the splash is generated here rather than committed by hand.

If art_src/ui/splash.png (or concept_art/ui/splash.png) exists it becomes the
splash, cover-cropped to 1280x720 over a night sky - the supplied art is a
cut-out, and the sky keeps its clear areas from fading up on black. With no
plate, a card is painted from the game's own wordmark over that same sky, so the
splash exists before painted art is supplied.

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
# The poster needs a slot of its own. 220,0 and 225,0 both belong to the
# char-select screen (the portrait wall and the painted backdrop, painted by
# tools/build_select_grid.py), so a poster written to either is overwritten by
# it or overwrites it. 206 is free: 200-205, 220-225, 400-403, 500, 600, 610,
# 700, 800, 810, 921-923 and 1000 are taken.
SPRITE = (206, 0)
# The night sky is a sprite of its own and the storyboard draws it behind the
# poster, so the poster keeps every pixel of transparency the art came with.
SKY_SPRITE = (207, 0)

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


def night_sky(halo=True):
    """Deep navy to violet, with a scatter of stars and a soft vignette.

    ``halo`` is the violet pool the fallback card puts behind its painted
    wordmark. Painted art brings its own composition, so it is left out there -
    it landed as a purple blob in the one clear part of the art.
    """
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

    if halo:
        # a warm pool of light where the fallback card's wordmark sits
        pool = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        ImageDraw.Draw(pool).ellipse([CANVAS[0] * 0.18, CANVAS[1] * 0.10,
                                      CANVAS[0] * 0.82, CANVAS[1] * 0.86],
                                     fill=(120, 90, 255, 46))
        sky.alpha_composite(pool.filter(ImageFilter.GaussianBlur(90)))

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


def card_wordmark():
    """The title's wordmark, placed where the title screen will draw it.

    The card is 1280x720 and the title is 1920x1080, and both are stretched to
    the window, so holding the same fraction of each frame is what makes the
    logo stay put when the card fades into the title.
    """
    try:
        import build_title
    except Exception as exc:                      # pragma: no cover - defensive
        print(f"  (no wordmark for the splash card: {exc})")
        return None
    logo, box = build_title.wordmark()
    k = CANVAS[1] / float(build_title.FRAME[1])
    logo = logo.resize((max(1, int(round(logo.width * k))),
                        max(1, int(round(logo.height * k)))), Image.LANCZOS)
    left, right = int(round(box[0] * k)), int(round(box[2] * k))
    top = int(round(box[1] * k))
    x = (CANVAS[0] - (right - left)) // 2 - left
    y = int(round(build_title.TOP_MARGIN * k)) - top
    return logo, (x, y)


def poster():
    """The splash artwork: a painted plate if supplied, else the fallback."""
    for path in PLATES:
        if os.path.isfile(path):
            img = Image.open(path).convert("RGBA")
            if abs(img.width / float(img.height) - 16 / 9.0) > 0.06:
                print(f"  warning: {os.path.relpath(path, ROOT)} is "
                      f"{img.width}x{img.height}, not 16:9; it will be cropped")
            # Nothing is baked behind the plate: the sky is drawn under it by
            # the storyboard, so the poster stays a cut-out.
            card = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
            card.alpha_composite(cover(img, CANVAS))
            mark = card_wordmark()
            if mark is not None:
                card.alpha_composite(mark[0], mark[1])
            return card, path
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
        "[Splash Sky]\n"
        "type = normal\n"
        f"spriteno = {SKY_SPRITE[0]}, {SKY_SPRITE[1]}\n"
        "start = 0, 0\n"
        "mask = 0\n"
        "\n"
        "[Splash Poster]\n"
        "type = normal\n"
        f"spriteno = {SPRITE[0]}, {SPRITE[1]}\n"
        "start = 0, 0\n"
        "mask = 0\n"
    )


def write_system_sprites(images, axis=AXIS):
    """Put each ``images`` slot into system.sff, replacing what is there."""
    if not os.path.isfile(SYSTEM_SFF):
        raise SystemExit("data/ikemen1/system.sff is missing - fetch the engine "
                         "data first")
    _d, sprites, palettes = sff.read_sff(SYSTEM_SFF)

    out, replaced = [], set()
    for sp in sprites:
        key = (sp["group"], sp["number"])
        if key in images:
            out.append({"group": key[0], "number": key[1],
                        "image": images[key], "axis": axis})
            replaced.add(key)
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"],
                        "link": sp["link"]})
    for key in sorted(set(images) - replaced):
        out.append({"group": key[0], "number": key[1],
                    "image": images[key], "axis": axis})

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

    sky_img = night_sky(halo=False)
    total, replaced = write_system_sprites({SKY_SPRITE: sky_img, SPRITE: art_img})

    with open(LOGO_DEF + ".tmp", "w", encoding="utf-8") as f:
        f.write(storyboard())
    os.replace(LOGO_DEF + ".tmp", LOGO_DEF)

    # Read both back: a splash that does not resolve is a black screen at
    # startup, and the engine cannot be asked about it here.
    _d, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    have = {(sp["group"], sp["number"]) for sp in sprites}
    for slot in (SPRITE, SKY_SPRITE):
        if slot not in have:
            raise SystemExit(f"splash sprite {slot} did not make it into system.sff")
    with open(LOGO_DEF, encoding="utf-8") as f:
        text = f.read()
    for slot in (SKY_SPRITE, SPRITE):
        if f"spriteno = {slot[0]}, {slot[1]}" not in text:
            raise SystemExit(f"logo.def does not draw sprite {slot}")
    if text.index("spriteno = %d" % SKY_SPRITE[0]) > text.index("spriteno = %d" % SPRITE[0]):
        raise SystemExit("logo.def draws the sky after the poster")

    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    preview = sky_img.copy()
    preview.alpha_composite(art_img)
    preview.save(os.path.join(ROOT, "artifacts", "splash.png"))
    print(f"wrote the splash into data/ikemen1/system.sff ({total} sprites, sky "
          f"{SKY_SPRITE[0]},{SKY_SPRITE[1]}, poster {SPRITE[0]},{SPRITE[1]}, "
          f"{replaced} replaced) and data/ikemen1/logo.def ({SECONDS:.0f}s)")


if __name__ == "__main__":
    build()
