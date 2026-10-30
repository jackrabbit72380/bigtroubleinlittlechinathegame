"""Repaint the character-select screen as an MKT HD style portrait grid.

The staged screenpack lays the roster out as a 10x8 wall of 24px cells seen in
perspective, which reads nothing like the arcade game this project chases. This
paints the arcade layout instead: five framed portraits on the top row, three
beneath them, the selected fighters standing large down the left and right
edges, and the arena name under the grid.

Every sprite is written into data/ikemen1/system.sff and every layout key into
the [Select Info] block of data/ikemen1/system.def, so a build-assets run from a
fresh checkout reproduces the screen. The engine sizes its own portraits as
cell-width art at scale .25 with the axis at the sprite's top-left corner
(9000,0 is 25x25 in a 24px cell), so the art here is painted at cell size and
drawn at scale 1 with the same zero axis.

Run:  python3 tools/build_select_grid.py
"""

from __future__ import annotations

import os
import random
import re
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYSTEM_SFF = os.path.join(ROOT, "data", "ikemen1", "system.sff")
SYSTEM_DEF = os.path.join(ROOT, "data", "ikemen1", "system.def")

SCREEN = (1280, 720)
CELL = 120
GAP = 8
COLS, ROWS = 5, 2
GRID = ((SCREEN[0] - (COLS * CELL + (COLS - 1) * GAP)) // 2, 100)
GRID_W = COLS * CELL + (COLS - 1) * GAP
GRID_H = ROWS * CELL + (ROWS - 1) * GAP

BG_SPR = (220, 0)
CELL_SPR = (222, 0)
CURSOR = ((223, 0), (223, 1), (223, 2), (223, 3))
AXIS = (0, 0)

GOLD = (206, 168, 86)
GOLD_DIM = (126, 96, 42)
INK = (9, 12, 12)
ARENA_Y = 604
STAGE_Y = 660

# The screenpack's own select background: sky, cloud band, bars and the two
# portrait gradients. The painted background below replaces all of it, so these
# are blanked (a 1x1 transparent sprite) instead of being deleted from the def,
# which keeps the engine's layer blocks valid.
BLANKED = ((101, 0), (101, 2), (101, 3), (100, 1), (102, 0), (102, 1))

# Cursor colour per player, in the order the grid draws players 1-4.
PLAYER_COLOURS = ((72, 232, 96), (240, 186, 64), (176, 132, 240), (96, 208, 232))


def tracked(draw, xy, text, font, fill, tracking=2, anchor="la"):
    """Draw letter-spaced caps, the way an arcade caption is set."""
    x, y = xy
    widths = [font.getlength(ch) for ch in text]
    total = sum(widths) + tracking * max(0, len(text) - 1)
    if anchor == "ma":
        x -= total / 2.0
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += w + tracking
    return total


def rule(draw, x0, x1, y, fill, width=1):
    draw.rectangle([min(x0, x1), y, max(x0, x1), y + width - 1], fill=fill)


def background():
    """1280x720 select backdrop: stone, jade haze, gold frame, captions."""
    img = art.vgrad(SCREEN, [(0, (5, 9, 10)), (260, (11, 20, 18)),
                             (500, (7, 12, 12)), (720, (3, 6, 7))]).convert("RGBA")
    img = Image.alpha_composite(img, art.radial_light(SCREEN, (640, 250), 560,
                                                      (32, 96, 78), peak=105))

    # Slow marble smoke: soft ellipses at low alpha, each one blurred hard.
    rng = random.Random(11)
    for _ in range(22):
        cx, cy = rng.randrange(0, SCREEN[0]), rng.randrange(0, SCREEN[1])
        rx, ry = rng.randrange(140, 420), rng.randrange(70, 230)
        layer = Image.new("RGBA", SCREEN, (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                                      fill=(96, 150, 128, rng.randrange(5, 13)))
        img = Image.alpha_composite(img, layer.filter(
            ImageFilter.GaussianBlur(rng.randrange(34, 74))))

    d = ImageDraw.Draw(img)

    # The frame the grid sits in: a plate, a double gold rule, corner diamonds.
    pad = 26
    box = [GRID[0] - pad, GRID[1] - pad,
           GRID[0] + GRID_W + pad, GRID[1] + GRID_H + pad]
    d.rectangle(box, fill=(6, 9, 9, 176), outline=GOLD_DIM + (255,), width=2)
    d.rectangle([box[0] + 4, box[1] + 4, box[2] - 4, box[3] - 4],
                outline=GOLD + (232,), width=2)
    d.rectangle([box[0] + 8, box[1] + 8, box[2] - 8, box[3] - 8],
                outline=GOLD_DIM + (190,), width=1)
    for cx, cy in ((box[0], box[1]), (box[2], box[1]),
                   (box[0], box[3]), (box[2], box[3])):
        d.polygon([(cx, cy - 9), (cx + 9, cy), (cx, cy + 9), (cx - 9, cy)],
                  fill=GOLD + (255,), outline=(40, 32, 14, 255))

    # Side columns: rules marking where the two fighters stand, labelled on top.
    for x, label in ((20, "PLAYER 1"), (SCREEN[0] - 21, "PLAYER 2")):
        d.rectangle([x, 58, x + 2, SCREEN[1] - 46], fill=GOLD_DIM + (200,))
        d.rectangle([x + 1, 58, x + 1, SCREEN[1] - 46], fill=GOLD + (110,))
    cx1, cx2 = GRID[0] // 2, SCREEN[0] - GRID[0] // 2
    for cx, label in ((cx1, "PLAYER 1"), (cx2, "PLAYER 2")):
        tracked(d, (cx, 66), label, art.font(19), GOLD + (238,), tracking=3,
                anchor="ma")
        rule(d, cx - 62, cx + 62, 92, GOLD_DIM + (220,))

    # Arena caption: the engine draws the stage's own name under this line.
    tracked(d, (640, ARENA_Y - 34), "ARENA", art.font(20), GOLD + (238,),
            tracking=8, anchor="ma")
    rule(d, 520, 600, ARENA_Y - 9, GOLD_DIM + (210,))
    rule(d, 680, 760, ARENA_Y - 9, GOLD_DIM + (210,))

    img = art.vignette(img, strength=0.55)
    return art.grain(img, amount=5, seed=5)


def cell_frame():
    """One empty portrait cell: dark stone plate with a gold bevel."""
    s = CELL
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, s - 1, s - 1], fill=INK + (238,))
    d.rectangle([0, 0, s - 1, s - 1], outline=GOLD + (255,), width=2)
    d.rectangle([2, 2, s - 3, s - 3], outline=(26, 24, 20, 255), width=2)
    d.rectangle([4, 4, s - 5, s - 5], outline=GOLD_DIM + (210,), width=1)

    shade = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for y in range(5, 30):
        sd.line([(5, y), (s - 6, y)], fill=(0, 0, 0, int(74 * (1 - (y - 5) / 25.0))))
    img.alpha_composite(shade)
    return img


def cursor_frame(colour):
    """Selection frame: a bright box with a soft outward glow."""
    s = CELL
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, s - 3, s - 3], outline=colour + (255,), width=4)
    d.rectangle([6, 6, s - 7, s - 7], outline=(255, 255, 255, 150), width=1)
    d.rectangle([0, 0, s - 1, s - 1], outline=colour + (120,), width=1)
    glow = img.filter(ImageFilter.GaussianBlur(7))
    out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    out.alpha_composite(glow)
    out.alpha_composite(img)
    return out


def rewrite_system_sff(images):
    """Replace or append sprites in system.sff, leaving the rest byte-exact."""
    d, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    blank = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    out, done = [], set()
    for sp in sprites:
        key = (sp["group"], sp["number"])
        if key in images:
            out.append({"group": key[0], "number": key[1],
                        "image": images[key], "axis": AXIS})
            done.add(key)
        elif key in BLANKED:
            out.append({"group": key[0], "number": key[1],
                        "image": blank, "axis": AXIS})
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"], "link": sp["link"]})
    for key, image in images.items():
        if key not in done:
            out.append({"group": key[0], "number": key[1], "image": image,
                        "axis": AXIS})

    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: built system.sff has no signature")
    with open(SYSTEM_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(SYSTEM_SFF + ".tmp", SYSTEM_SFF)
    return len(out)


KEYS = (
    ("rows", str(ROWS)),
    ("columns", str(COLS)),
    ("wrapping", "1"),
    ("pos", "%d,%d" % GRID),
    ("showemptyboxes", "0"),
    ("moveoveremptyboxes", "0"),
    ("cell.size", "%d,%d" % (CELL, CELL)),
    ("cell.spacing", str(GAP)),
    ("cell.bg.spr", "%d,%d" % CELL_SPR),
    ("cell.bg.scale", "1,1"),
    ("cell.bg.offset", "0,0"),
    ("cell.random.spr", "151,0"),
    ("cell.random.scale", "1.6,1.6"),
    ("portrait.spr", "9000,0"),
    ("portrait.offset", "0,0"),
    ("portrait.scale", "1,1"),
    ("stage.pos", "640,%d" % STAGE_Y),
    ("title.offset", "640,30"),
    # The big side art is the uniform 9000,2 portrait, so the two columns match
    # each other no matter how tall the fighter is in play.
    ("p1.face.window", "0,0,1,1"),
    ("p1.face2.spr", "9000,2"),
    ("p1.face2.offset", "8,150"),
    ("p1.face2.scale", "1,1"),
    ("p1.face2.window", "0,86,320,712"),
    ("p2.face.window", "0,0,1,1"),
    ("p2.face2.spr", "9000,2"),
    ("p2.face2.offset", "1266,150"),
    ("p2.face2.scale", "1,1"),
    ("p2.face2.window", "962,86,1276,712"),
)
for i, spr in enumerate(CURSOR, start=1):
    KEYS += ((f"p{i}.cursor.active.spr", "%d,%d" % spr),
             (f"p{i}.cursor.active.scale", "1,1"),
             (f"p{i}.cursor.active.offset", "0,0"),
             (f"p{i}.cursor.done.spr", "%d,%d" % spr),
             (f"p{i}.cursor.done.scale", "1,1"),
             (f"p{i}.cursor.done.offset", "0,0"))

# Keys that belong to the wall-of-cells layout and would fight the grid.
DROP = re.compile(r"^\s*cell\.\*-\d+\.", re.IGNORECASE)
# Anim-based overrides that would draw the old cursor or the perspective face2
# art on top of the new layout.
DISABLE = re.compile(
    r"^\s*(p[1-4]\.cursor\.(active|done)\.anim|"
    r"p[12]\.face2\.(projection|yangle|focallength)\s*|"
    r"stage\.portrait\.spr)\s*=", re.IGNORECASE)


def patch_select_info():
    with open(SYSTEM_DEF, encoding="utf-8", errors="replace") as f:
        text = f.read()
    head, sep, rest = text.partition("[Select Info]")
    if not sep:
        raise SystemExit("system.def has no [Select Info] block")

    body, tail = rest, ""
    lines = rest.splitlines(True)
    for i, line in enumerate(lines):
        if line.startswith("["):
            body, tail = "".join(lines[:i]), "".join(lines[i:])
            break
    else:
        tail = ""

    kept = []
    for line in body.splitlines(True):
        if DROP.match(line):
            continue
        if DISABLE.match(line):
            kept.append(";" + line.lstrip())
            continue
        kept.append(line)
    body = "".join(kept)

    for key, value in KEYS:
        pattern = re.compile(r"^\s*;?\s*" + re.escape(key) + r"\s*=", re.IGNORECASE)
        new_line = "%s = %s\n" % (key, value)
        lines = body.splitlines(True)
        for i, line in enumerate(lines):
            if pattern.match(line):
                lines[i] = new_line
                break
        else:
            lines.append(new_line)
        body = "".join(lines)

    text = head + sep + body + tail
    with open(SYSTEM_DEF + ".tmp", "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(SYSTEM_DEF + ".tmp", SYSTEM_DEF)


def layer_block():
    return (
        "\n;------------------------------------\n"
        "; Select-screen background, painted by tools/build_select_grid.py\n"
        "[SelectBG Portrait Grid]\n"
        "type = normal\n"
        "spriteno = %d, %d\n" % BG_SPR +
        "start = -640, 0\n"
        "layerno = 0\n"
        "mask = 1\n"
    )


def patch_bg_layer():
    with open(SYSTEM_DEF, encoding="utf-8", errors="replace") as f:
        text = f.read()
    if "spriteno = %d, %d" % BG_SPR in text:
        return False
    marker = "\n[VS Screen]"
    if marker not in text:
        raise SystemExit("system.def has no [VS Screen]; cannot place the background")
    text = text.replace(marker, layer_block() + marker, 1)
    with open(SYSTEM_DEF + ".tmp", "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(SYSTEM_DEF + ".tmp", SYSTEM_DEF)
    return True


def main():
    if not os.path.isfile(SYSTEM_SFF) or not os.path.isfile(SYSTEM_DEF):
        raise SystemExit("data/ikemen1 is missing - fetch the engine data first")

    images = {BG_SPR: background(), CELL_SPR: cell_frame()}
    for spr, colour in zip(CURSOR, PLAYER_COLOURS):
        images[spr] = cursor_frame(colour)

    rewrite_system_sff(images)
    patch_select_info()
    added = patch_bg_layer()

    # Read back: a screen nobody can see is worse than the old one.
    _d, sprites, _p = sff.read_sff(SYSTEM_SFF)
    have = {(sp["group"], sp["number"]): sp for sp in sprites}
    for key in images:
        if key not in have:
            raise SystemExit(f"select-screen sprite {key} did not make it into system.sff")
        sp = have[key]
        if sp["group"] == BG_SPR[0] and (sp["w"], sp["h"]) != SCREEN:
            raise SystemExit(f"select background is {sp['w']}x{sp['h']}, expected {SCREEN}")
    with open(SYSTEM_DEF, encoding="utf-8", errors="replace") as f:
        text = f.read()
    if "portrait.spr = 9000,0" not in text or "rows = %d" % ROWS not in text:
        raise SystemExit("system.def does not carry the new select layout")

    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    background().convert("RGB").save(os.path.join(ROOT, "artifacts", "select_bg.png"))
    sheet = Image.new("RGBA", (CELL * 3 + 32, CELL + 16), (24, 24, 32, 255))
    sheet.alpha_composite(cell_frame(), (8, 8))
    sheet.alpha_composite(cursor_frame(PLAYER_COLOURS[0]), (CELL + 16, 8))
    sheet.alpha_composite(cursor_frame(PLAYER_COLOURS[1]), (CELL * 2 + 24, 8))
    sheet.convert("RGB").save(os.path.join(ROOT, "artifacts", "select_cells.png"))
    print(f"select screen: {COLS}x{ROWS} grid at {GRID[0]},{GRID[1]}, "
          f"cells {CELL}px, background layer {'added' if added else 'kept'}")


if __name__ == "__main__":
    main()
