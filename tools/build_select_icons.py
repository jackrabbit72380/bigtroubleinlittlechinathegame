"""Repaint the select screen's team markers in the game's own palette.

Four sprites decide whether the team-mode screen reads at a glance, and all four
shipped as stock screenpack art in blues that fight the gold UI:

  180,0  the cursor beside the mode list - a royal-blue triangle
  181,0  a team-slot marker, filled (P1 side); 182,0 the same slot empty
  191,0  the P2 side's filled marker; 192,0 its empty one

The filled and empty markers were the same silhouette in two brightnesses of
blue, so a four-slot row read as four blobs of the same colour, and the sizes
were the only thing telling the two apart. They are one person silhouette here,
in the palette's gold: solid for a slot in use, hollowed out with a dim rim for
one that is not, both with a dark edge so they hold up over portrait art. P2
keeps its own colour - amber, the same one the right-hand menu text uses - so
the sides stay apart while the shapes match.

Run:  python3 tools/build_select_icons.py
"""

from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYSTEM_SFF = os.path.join(ROOT, "data", "ikemen1", "system.sff")

GOLD = (240, 196, 88)
BRIGHT = (255, 228, 140)
AMBER = (236, 158, 74)
AMBER_BRIGHT = (255, 196, 120)
DIM = (198, 162, 96)
INK = (16, 12, 10)

PERSON = (30, 48)
ARROW = (22, 38)
SS = 6                                  # supersample factor


def _mask(grow=0, size=PERSON):
    """The person: a head over a rounded bust, grown by ``grow`` px."""
    w, h = size[0] * SS, size[1] * SS
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    g = grow * SS
    d.ellipse([9 * SS - g, 3 * SS - g, 21 * SS + g, 15 * SS + g], fill=255)
    d.rounded_rectangle([5 * SS - g, 17 * SS - g, 25 * SS + g, 45 * SS + g],
                        radius=6 * SS + g, fill=255)
    return m


def _gradient(size, top, bottom):
    w, h = size[0] * SS, size[1] * SS
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        col = (round(top[0] + (bottom[0] - top[0]) * t),
               round(top[1] + (bottom[1] - top[1]) * t),
               round(top[2] + (bottom[2] - top[2]) * t), 255)
        d.line([(0, y), (w, y)], fill=col)
    return img


def person(top, bottom, hollow=False):
    """The marker at its finished size (30x48), edges included."""
    w, h = PERSON[0] * SS, PERSON[1] * SS
    ink = Image.new("RGBA", (w, h), INK + (255,))
    ink.putalpha(_mask(grow=1))
    if hollow:
        img = ink
        img.paste((0, 0, 0, 0), mask=_mask(grow=-2))
        tin = Image.new("RGBA", (w, h), (0, 0, 0, 140))
        img = Image.composite(tin, img, _mask(grow=-2))
        rim = Image.new("RGBA", (w, h), DIM + (255,))
        rim.putalpha(_mask(grow=-1))
        rim.paste((0, 0, 0, 0), mask=_mask(grow=-3))
        img = Image.alpha_composite(rim, img)
    else:
        body = _gradient(PERSON, top, bottom)
        body.putalpha(_mask(grow=0))
        img = Image.alpha_composite(ink, body)
    return img.resize(PERSON, Image.LANCZOS)


def arrow():
    """The mode cursor at its finished size (22x38), pointing right."""
    w, h = ARROW[0] * SS, ARROW[1] * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(4 * SS, 3 * SS), (4 * SS, 35 * SS), (20 * SS, 19 * SS)],
              fill=INK + (255,))
    d.polygon([(6 * SS, 8 * SS), (6 * SS, 30 * SS), (17 * SS, 19 * SS)],
              fill=BRIGHT + (255,))
    d.polygon([(6 * SS, 19 * SS), (6 * SS, 30 * SS), (14 * SS, 23 * SS)],
              fill=GOLD + (255,))
    return img.resize(ARROW, Image.LANCZOS)


def art():
    """Every sprite this tool owns, keyed by (group, number), with its axis."""
    return {
        (180, 0): (arrow(), (21, 35)),
        (181, 0): (person(BRIGHT, GOLD), (14, 45)),
        (182, 0): (person(DIM, DIM, hollow=True), (14, 45)),
        (191, 0): (person(AMBER_BRIGHT, AMBER), (14, 45)),
        (192, 0): (person(DIM, DIM, hollow=True), (14, 45)),
    }


def write_sprites(images):
    d, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    out, seen = [], set()
    for sp in sprites:
        key = (sp["group"], sp["number"])
        if key in images:
            img, axis = images[key]
            out.append({"group": key[0], "number": key[1], "image": img, "axis": axis})
            seen.add(key)
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"], "link": sp["link"]})
    for key, (img, axis) in images.items():
        if key not in seen:
            out.append({"group": key[0], "number": key[1], "image": img, "axis": axis})
    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: built file has no SFF signature")
    with open(SYSTEM_SFF + ".tmp", "wb") as fh:
        fh.write(blob)
    os.replace(SYSTEM_SFF + ".tmp", SYSTEM_SFF)
    return len(out)


def verify():
    """Re-read what was written: sizes, and no blue left in the markers."""
    d, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    problems = []
    for key, want in (((180, 0), ARROW), ((181, 0), PERSON), ((182, 0), PERSON),
                      ((191, 0), PERSON), ((192, 0), PERSON)):
        sp = next((s for s in sprites if (s["group"], s["number"]) == key), None)
        if sp is None:
            problems.append("%d,%d is missing from system.sff" % key)
            continue
        if (sp["w"], sp["h"]) != want:
            problems.append("%d,%d is %dx%d, expected %dx%d"
                            % (key[0], key[1], sp["w"], sp["h"], want[0], want[1]))
            continue
        img = sff.decode_sprite(d, sp, palettes).convert("RGBA")
        px = [p for p in img.convert("RGBA").getdata() if p[3] > 128]
        if not px:
            problems.append("%d,%d is blank" % key)
            continue
        r = sum(p[0] for p in px) / len(px)
        b = sum(p[2] for p in px) / len(px)
        if b > r:
            problems.append("%d,%d still reads blue (r=%.0f b=%.0f)" % (key[0], key[1], r, b))
        elif key[0] in (180, 181, 191) and r < 150:
            problems.append("%d,%d is too dark to read over a portrait (r=%.0f)"
                            % (key[0], key[1], r))
        if sp["axis"] != {180: (21, 35)}.get(key[0], (14, 45)):
            problems.append("%d,%d moved its axis" % key)
    return problems


def main():
    images = art()
    count = write_sprites(images)
    problems = verify()
    for line in problems:
        print("  FAIL " + line)
    if problems:
        return 1
    print("select icons: %d sprite(s) in system.sff, %d total" % (len(images), count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
