"""Frame each HUD corner portrait in the select screen's own gold cell.

The select screen draws a fighter in a 112x140 cell: the character's 9000,0 art
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
CELL_SIZE = (112, 140)          # as authored, in select-screen pixels
SCALE = 1280.0 / 1920.0         # fight.def's coordinate space
# The portrait is drawn as large as the frame's opening allows. It used to take
# the frame's own 0.667 - the scale of the 128x160 cell against the 1280-wide
# fight space - which is fine for the ring but too big for the picture drawn
# inside it, so art the size of a cell hung out of every corner. Nor is the
# select screen's 0.5 the answer: that is 0.5 of a 1920-wide space, larger in
# fight units than the opening, which is why the same art fitted there and not
# here. Sizing to the opening is the only figure that holds for both.
_CELL_IMAGE = None


def cell_image():
    global _CELL_IMAGE
    if _CELL_IMAGE is None:
        sd, sprites, palettes = sff.read_sff(SYSTEM_SFF)
        src = next(s for s in sprites if (s["group"], s["number"]) == CELL)
        _CELL_IMAGE = sff.decode_sprite(sd, src, palettes, src["pal"]).convert("RGBA")
    return _CELL_IMAGE


def portrait_scale():
    """The largest scale at which a cell-sized art stays inside the opening.

    The opening is measured in the cell art's own pixels, so the fit comes out in
    those pixels; face.scale is in fight units, which are SCALE of them, so that
    is applied last. Without it the picture is drawn 1/SCALE too large - which is
    exactly the bug this replaces, one layer down.
    """
    ox1, oy1, ox2, oy2 = cell_opening(cell_image())
    return min((ox2 - ox1) / float(CELL_SIZE[0]),
               (oy2 - oy1) / float(CELL_SIZE[1])) * SCALE
POS = {"p1": (20, 20), "p2": (1260, 20)}

SECTIONS = ("Face", "Simul Face", "Tag Face", "Turns Face")


def cell_opening(image):
    """The frame's opening, in the cell's own pixels.

    The gold cell is a painted ring, and its rounded corners are transparent, so
    a plain bounding box of the transparent pixels is the whole sprite and a scan
    inward from one edge runs straight past the border. What the portrait has to
    fit through is the gap *between* the painted left and right edges on each
    row; the rect below is the widest rectangle that sits inside all of them.
    """
    w, h = image.size
    px = image.load()
    rows = []
    for y in range(h):
        painted = [x for x in range(w) if px[x, y][3] > 8]
        if len(painted) < 2:
            continue
        gap = [x for x in range(painted[0], painted[-1] + 1) if px[x, y][3] <= 8]
        if not gap:
            continue
        rows.append((y, gap[0], gap[-1] + 1))
    if not rows:
        return 0, 0, w, h
    x1 = max(r[1] for r in rows)
    x2 = min(r[2] for r in rows)
    if x2 <= x1:
        return 0, 0, w, h
    return x1, rows[0][0], x2, rows[-1][0] + 1


def cell_window(side, image=None):
    """The frame's opening as a face.window rect, in fight.def units.

    The cell is drawn from POS at SCALE with its axis at the top-left, so the
    opening lands at pos + opening * SCALE; player two's cell is mirrored, so its
    opening is mirrored too. This is the box the portrait is held inside, and it
    is the same 112x140 cell the select screen uses, scaled for the fight space.
    """
    if image is None:
        image = cell_image()
    ox1, oy1, ox2, oy2 = cell_opening(image)
    x, y = POS[side]
    if side == "p1":
        x1, x2 = x + ox1 * SCALE, x + ox2 * SCALE
    else:
        x1, x2 = x - ox2 * SCALE, x - ox1 * SCALE
    return (int(round(x1)), int(round(y + oy1 * SCALE)),
            int(round(x2)), int(round(y + oy2 * SCALE)))


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


def cell_offset():
    """Where the portrait starts, so the art sits centred in the opening."""
    ox1, oy1, ox2, oy2 = cell_opening(cell_image())
    scale = portrait_scale()
    drawn = (CELL_SIZE[0] * scale, CELL_SIZE[1] * scale)
    return (int(round(ox1 * SCALE + ((ox2 - ox1) * SCALE - drawn[0]) / 2.0)),
            int(round(oy1 * SCALE + ((oy2 - oy1) * SCALE - drawn[1]) / 2.0)))


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
        ("%s.face.offset" % side, "%d, %d" % cell_offset()),
        ("%s.face.scale" % side, "%.3f, %.3f" % (portrait_scale(), portrait_scale())),
        ("%s.face.facing" % side, facing),
        ("%s.face.layerno" % side, "1"),
        # The corner art is the fighter's own 9000,0, and its size varies by
        # character, so without this the taller ones spilled past the frame and
        # read as cut off. The window is the cell's opening, at the cell's scale,
        # so the picture is framed by the box instead of hanging out of it.
        ("%s.face.window" % side,
         "%d, %d, %d, %d" % cell_window(side)),
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
