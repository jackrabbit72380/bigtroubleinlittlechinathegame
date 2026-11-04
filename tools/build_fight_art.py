"""Repaint the fight announcements in the game's own lettering.

Three sets of words are still the stock arcade art:

* ``TIME`` / ``UP!``  (fight.sff 525,0 and 525,1) - blue chrome
* ``WINNER!`` / ``YOU WIN!`` / ``YOU LOSE!`` (530,0-2) - silver chrome
* ``ROUND`` (500,0) - silver chrome

Every caption in this game is set in the wordmark's face, cream on top shading
to gold and red, with a maroon extrusion - the menus, the round timer, the hit
and combo counters (tools/build_fonts.py) and the VS logo. Those three are the
last pieces of art that still read as a different game, so they are repainted
here with the same glyph painter build_fonts.py uses, which keeps the exact
shading and the extrusion of the menu text.

The VS screen's ``NEXT MATCH`` banner (system.sff 202,0) is repainted the same
way: the engine's silver chrome banner beside the painted wordmark was the one
thing on that screen that did not belong.

Each sprite keeps its own size and axis, so every animation offset in
data/fight.def and data/ikemen1/system.def still points at the right place.

Run:  python3 tools/build_fight_art.py
"""

from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import build_fonts as fonts
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGHT_SFF = os.path.join(ROOT, "data", "fight.sff")
SYSTEM_SFF = os.path.join(ROOT, "data", "ikemen1", "system.sff")
TTF = os.path.join(ROOT, "data", "ikemen1", "fonts", "Display.ttf")

# (group, number) -> the words the stock sprite draws. The text is what the
# engine's own art says, so the announcement reads the same as before.
FIGHT_WORDS = {
    (525, 0): "TIME",
    (525, 1): "UP!",
    (530, 0): "WINNER!",
    (530, 1): "YOU WIN!",
    (530, 2): "YOU LOSE!",
    (500, 0): "ROUND",
}
SYSTEM_WORDS = {
    (202, 0): "NEXT MATCH",
}

# The maroon extrusion of the menu face, in pixels. The stock art is 100-110px
# tall, so a proportional depth keeps the same weight as the smaller captions.
DEPTH = 4


def face_text(text, px, depth=DEPTH):
    """The whole string in the wordmark face, as one RGBA plate."""
    font = ImageFont.truetype(TTF, px)
    cells = [fonts.glyph(ch, font, cell_h=px + depth + 12, depth=depth)
             for ch in text]
    width = sum(c.width for c in cells)
    height = max(c.height for c in cells)
    out = Image.new("RGBA", (max(1, width), max(1, height)), (0, 0, 0, 0))
    x = 0
    for cell in cells:
        out.alpha_composite(cell, (x, 0))
        x += cell.width
    return out


def fit(img, size):
    """Scale to fill `size` as far as the aspect allows, then centre.

    The stock sprites have their own slanted proportions; the words are set to
    the same box so an animation that slides or scales one still lands right.
    """
    tw, th = size
    ratio = min(tw / float(img.width), th / float(img.height))
    new = (max(1, int(round(img.width * ratio))),
           max(1, int(round(img.height * ratio))))
    img = img.resize(new, Image.LANCZOS)
    out = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    out.alpha_composite(img, ((tw - new[0]) // 2, (th - new[1]) // 2))
    return out


def repaint(path, words):
    """Replace each listed sprite's art, leaving the rest byte-exact."""
    raw, sprites, palettes = sff.read_sff(path)
    have = {(sp["group"], sp["number"]): sp for sp in sprites}
    missing = [key for key in words if key not in have]
    if missing:
        raise SystemExit("%s has no sprite %s" % (os.path.basename(path), missing))

    out, done = [], 0
    for sp in sprites:
        key = (sp["group"], sp["number"])
        if key in words:
            art = fit(face_text(words[key], 96), (sp["w"], sp["h"]))
            out.append({"group": sp["group"], "number": sp["number"],
                        "image": art, "axis": sp["axis"]})
            done += 1
            continue
        out.append({"group": sp["group"], "number": sp["number"],
                    "raw": sp["raw"], "format": sp["format"],
                    "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                    "axis": sp["axis"], "pal": sp["pal"], "link": sp["link"]})

    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: %s has no signature"
                         % os.path.basename(path))
    with open(path + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(path + ".tmp", path)
    return done


def build():
    for path in (FIGHT_SFF, SYSTEM_SFF, TTF):
        if not os.path.isfile(path):
            raise SystemExit("%s is missing - run the asset build first"
                             % os.path.relpath(path, ROOT))

    fight = repaint(FIGHT_SFF, FIGHT_WORDS)
    system = repaint(SYSTEM_SFF, SYSTEM_WORDS)

    # Read back: the words have to be in the sheets, at their old size.
    for path, words in ((FIGHT_SFF, FIGHT_WORDS), (SYSTEM_SFF, SYSTEM_WORDS)):
        _d, sprites, _p = sff.read_sff(path)
        have = {(sp["group"], sp["number"]) for sp in sprites}
        for key in words:
            if key not in have:
                raise SystemExit("sprite %d,%d did not survive the repaint"
                                 % key)

    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    sheet = Image.new("RGBA", (1800, 470), (26, 24, 26, 255))
    y = 10
    for key, word in list(FIGHT_WORDS.items()) + list(SYSTEM_WORDS.items()):
        plate = fit(face_text(word, 96), (520, 96)) if word != "NEXT MATCH" \
            else fit(face_text(word, 66), (516, 44))
        sheet.alpha_composite(plate, (20, y))
        y += plate.height + 8
    sheet.convert("RGB").save(os.path.join(ROOT, "artifacts", "fight_art.png"))
    print("fight art: %d fight sprite(s) and %d VS sprite repainted"
          % (fight, system))


if __name__ == "__main__":
    build()
