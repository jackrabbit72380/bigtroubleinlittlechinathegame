"""Frame each HUD corner portrait in the select screen's own gold cell.

The select screen draws a fighter in a 128x160 cell: the character's 9000,0 art
inside the gold cell frame (system.sff 222,0). The fight HUD framed the same art
in its own small blue-grey boxes, 100x100 and 108x108, and cropped the portrait
with a 92x92 window, so the corner showed a cut-down sliver of a fighter in a box
that matched nothing else in the game.

Both corners now show the select cell itself: 222,0 is copied into fight.sff (the
HUD's sprite file, group 222 number 0, which was unused there), drawn at the
cell's proportions over the full 9000,0 art with the window gone. 0.667 is
1280/1920, so the box is exactly the size it is on the select screen once the HUD
is scaled up to the screen.

Run after the tools that rewrite fight.sff:

    python3 tools/build_face_boxes.py
"""

from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import sff  # noqa: E402

SYSTEM_SFF = os.path.join(ROOT, "data", "ikemen1", "system.sff")
FIGHT_SFF = os.path.join(ROOT, "data", "fight.sff")
FIGHT_DEF = os.path.join(ROOT, "data", "fight.def")

CELL = (222, 0)                 # the gold cell frame on the select screen
CELL_SIZE = (128, 160)          # as authored, in select-screen pixels
SCALE = 1280.0 / 1920.0         # fight.def's coordinate space
POS = {"p1": (20, 20), "p2": (1260, 20)}

SECTIONS = ("Face", "Simul Face", "Tag Face", "Turns Face")


def copy_cell_sprite():
    """Put the gold frame into fight.sff as 222,0, keeping the rest intact."""
    sd, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    src = next((s for s in sprites if (s["group"], s["number"]) == CELL), None)
    if src is None:
        raise SystemExit("system.sff has no %d,%d cell frame" % CELL)
    if (src["w"], src["h"]) != CELL_SIZE:
        raise SystemExit("cell frame %d,%d is %dx%d, expected %dx%d"
                         % ((CELL[0], CELL[1], src["w"], src["h"]) + CELL_SIZE))
    image = sff.decode_sprite(sd, src, palettes, src["pal"]).convert("RGBA")

    d, sprites, palettes = sff.read_sff(FIGHT_SFF)
    out, done = [], False
    for sp in sprites:
        if (sp["group"], sp["number"]) == CELL:
            out.append({"group": CELL[0], "number": CELL[1],
                        "image": image, "axis": src["axis"]})
            done = True
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"], "link": sp["link"]})
    if not done:
        out.append({"group": CELL[0], "number": CELL[1],
                    "image": image, "axis": src["axis"]})
    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    with open(FIGHT_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(FIGHT_SFF + ".tmp", FIGHT_SFF)
    return image.size + (src["axis"], done)


def cell_keys(side):
    """The keys that turn one corner into the select screen's cell."""
    facing = "1" if side == "p1" else "-1"
    scale = "%.3f, %.3f" % (SCALE, SCALE)
    return [
        ("%s.bg0.spr" % side, "-1"),
        ("%s.bg1.spr" % side, "%d,%d" % CELL),
        ("%s.bg1.offset" % side, "0, 0"),
        ("%s.bg1.scale" % side, scale),
        ("%s.bg1.facing" % side, facing),
        ("%s.bg1.layerno" % side, "2"),
        ("%s.face.spr" % side, "9000,0"),
        ("%s.face.offset" % side, "0, 0"),
        ("%s.face.scale" % side, scale),
        ("%s.face.facing" % side, facing),
        ("%s.face.layerno" % side, "1"),
    ]


def patch_def():
    with open(FIGHT_DEF, encoding="utf-8", errors="surrogateescape",
              newline="") as f:
        text = f.read()
    changed = []
    for name in SECTIONS:
        start = text.find("[%s]" % name)
        if start < 0:
            continue
        nxt = re.compile(r"^\[", re.M).search(text, start + len(name) + 2)
        end = nxt.start() if nxt else len(text)
        head, body, tail = text[:start], text[start:end], text[end:]
        for side in ("p1", "p2"):
            for key, value in cell_keys(side):
                pattern = re.compile(r"^(;?[ \t]*" + re.escape(key) + r"[ \t]*=[^;\r\n]*)", re.M)
                line = "%s = %s" % (key, value)
                if pattern.search(body):
                    body = pattern.sub(line, body, count=1)
                else:
                    body = body.rstrip("\r\n") + "\n" + line + "\n"
                changed.append("%s/%s" % (name, key))
            # the window cropped the portrait; the cell art is already the box
            body = re.sub(r"(?m)^([ \t]*)(%s\.face\.window[ \t]*=[^\r\n]*)$"
                          % side, r"\1;\2", body)
        text = head + body + tail
    with open(FIGHT_DEF + ".tmp", "w", encoding="utf-8",
              errors="surrogateescape", newline="") as f:
        f.write(text)
    os.replace(FIGHT_DEF + ".tmp", FIGHT_DEF)
    return changed


def main():
    width, height, axis, replaced = copy_cell_sprite()
    changed = patch_def()
    d, sprites, palettes = sff.read_sff(FIGHT_SFF)
    got = next((s for s in sprites if (s["group"], s["number"]) == CELL), None)
    if got is None or (got["w"], got["h"]) != CELL_SIZE:
        raise SystemExit("cell frame did not land in fight.sff")
    print("cell frame %dx%d axis %s %s fight.sff as %d,%d; %d def key(s) set in %d section(s)"
          % (width, height, axis, "replaced" if replaced else "added",
             CELL[0], CELL[1], len(changed), len(SECTIONS)))


if __name__ == "__main__":
    main()
