"""Size every stage's preview so the VS screen draws it at the roster's card size.

The VS screen does not draw the wall's baked card. It draws each stage's own
9000,1 straight out of the stage's sheet, and the engine multiplies that by
motif/localcoord and by the stage's ``portraitscale`` before ``stage.portrait.scale``
ever applies. A stage whose sheet holds a picture of another shape therefore
lands at another size: the three Third Heights stages hold the pack's 240x100
preview, which at 3.375 lands 1215x506 - too tall for the screen's 1034x335
window, so it is cropped top and bottom - and the 3-D Lab holds a 1280x960
render that lands 1920x1440, three times the frame's width.

So the picture each of those stages carries is refitted to the size that lands
exactly on the roster's 1215x398 card in its own def's units: scaled to cover
that shape and centre-cropped, the same treatment tools/build_stage_wall.py
gives it when it bakes the wall's card from the same sprite. Stages that are
already right are left untouched, byte for byte.

Run: python3 tools/fit_stage_previews.py && python3 tools/build_stage_wall.py
"""

from __future__ import annotations

import os
import re
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SELECT_DEF = os.path.join(ROOT, "data", "select.def")
CARD = (1215, 398)          # the preview every stage shows, in motif units
MOTIF_W = 1920              # [Info] localcoord of the screenpack
PREVIEW = (9000, 1)


def pool():
    """The stage pool, in the order [ExtraStages] lists it."""
    text = open(SELECT_DEF, encoding="utf-8", errors="replace").read()
    block = text.split("[ExtraStages]", 1)[1].split("[", 1)[0]
    refs = []
    for line in block.splitlines():
        line = line.split(";", 1)[0].strip()
        if line.lower().endswith(".def"):
            refs.append(line)
    return refs


def setting(text, key, default):
    found = re.search(r"^\s*" + key + r"\s*=\s*([^;\r\n]+)", text, re.M | re.I)
    return found.group(1).strip() if found else default


def drawn_size(def_path):
    """The on-screen size of a stage's 9000,1, and the sprite size that lands on CARD."""
    text = open(def_path, encoding="utf-8", errors="replace").read()
    try:
        localcoord = float(setting(text, "localcoord", "1280,720").split(",")[0])
    except ValueError:
        localcoord = 1280.0
    try:
        portraitscale = float(setting(text, "portraitscale", "1"))
    except ValueError:
        portraitscale = 1.0
    factor = MOTIF_W / localcoord * portraitscale
    want = (max(1, int(round(CARD[0] / factor))),
            max(1, int(round(CARD[1] / factor))))
    return factor, want


def cover(image, size, anchor="center"):
    """Scale to cover ``size`` and crop - no distortion, no letterbox.

    ``anchor`` is where the crop sits: "center" keeps the middle of the picture,
    "bottom" keeps its foot. A stage layer is painted at the stage's own frame
    (1280x720 for the 3D arenas) and the card is 3:1, so the band has to be
    chosen: squashing the frame into the card is what made those three previews
    read flat, and a centred crop would cut the ground off them.
    """
    width, height = image.size
    scale = max(size[0] / float(width), size[1] / float(height))
    scaled = image.resize((max(1, int(round(width * scale))),
                           max(1, int(round(height * scale)))), Image.LANCZOS)
    left = (scaled.size[0] - size[0]) // 2
    top = (scaled.size[1] - size[1]) if anchor == "bottom" \
        else (scaled.size[1] - size[1]) // 2
    return scaled.crop((left, top, left + size[0], top + size[1]))


def main():
    changed = 0
    for ref in pool():
        def_path = os.path.join(ROOT, ref.replace("/", os.sep))
        if not os.path.isfile(def_path):
            print("  missing def: " + ref)
            continue
        sff_path = def_path[:-4] + ".sff"
        if not os.path.isfile(sff_path):
            print("  missing sheet: " + ref)
            continue
        factor, want = drawn_size(def_path)
        data, sprites, pals = sff.read_sff(sff_path)
        hit = next((sp for sp in sprites
                    if (sp["group"], sp["number"]) == PREVIEW), None)
        if hit is None:
            print("  no 9000,1 in %s" % os.path.basename(sff_path))
            continue
        drawn = (hit["w"] * factor, hit["h"] * factor)
        if (abs(drawn[0] - CARD[0]) < 2 and abs(drawn[1] - CARD[1]) < 2):
            continue
        try:
            image = sff.decode_sprite(data, hit, pals, hit["pal"])
        except Exception as exc:            # format 1 and friends: leave it be
            print("  %-22s cannot be decoded (%s), left alone"
                  % (os.path.basename(sff_path), exc))
            continue
        fitted = cover(image, want)
        out = []
        for sp in sprites:
            if (sp["group"], sp["number"]) == PREVIEW:
                out.append({"group": sp["group"], "number": sp["number"],
                            "image": fitted, "axis": sp.get("axis"),
                            "link": sp.get("link", 0)})
            else:
                out.append(sp)
        # read_sff hands back palette records; write_sff wants the bytes
        pal_bytes = [p["rgba"] if isinstance(p, dict) else p for p in pals]
        blob = sff.write_sff(out, pal_bytes)
        # write beside the sheet and move it into place: a failure here must not
        # be able to leave a truncated sprite sheet behind, which is what an
        # earlier version of this tool did to stages/lab3d.sff
        temp = sff_path + ".new"
        with open(temp, "wb") as handle:
            handle.write(blob)
        os.replace(temp, sff_path)
        changed += 1
        print("  %-22s %dx%d drew %dx%d -> %dx%d draws %dx%d"
              % (os.path.basename(sff_path), hit["w"], hit["h"],
                 drawn[0], drawn[1], want[0], want[1], CARD[0], CARD[1]))
    print("stage previews: %d refitted, %d stage(s) in the pool" % (changed, len(pool())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
