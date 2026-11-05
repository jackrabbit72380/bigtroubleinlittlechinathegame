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

SCREEN = (1920, 1080)
# 10x5 = 50 cells: the forty-eight fighters in data/select.def plus the random
# box, which is the whole cast on one page.
#
# The roster outgrew nine across when the rest of the film's cast joined it, so
# the grid gained a column. The cells are 80px now - the size the reference
# screen uses - and the 8px gutters between them came down to 2px to pay for it:
# 10 * 80 + 9 * 2 = 818, so the wall spans x=231 to x=1049 and the two standing
# fighters keep their own column either side of it.
CELL, CELL_H = 128, 160
GAP = 2
COLS, ROWS = 10, 5
GRID = ((SCREEN[0] - (COLS * CELL + (COLS - 1) * GAP)) // 2, 40)
GRID_W = COLS * CELL + (COLS - 1) * GAP
GRID_H = ROWS * CELL_H + (ROWS - 1) * GAP

BG_SPR = (220, 0)
CELL_SPR = (222, 0)
CURSOR = ((223, 0), (223, 1), (223, 2), (223, 3))
AXIS = (0, 0)
# Big side portraits: the panel window the 9000,2 art is clipped to, left/right.
# The grid's frame padding ends at x=221 and x=1059, so each window stops there.
# build_portraits.py paints the art 214x600 and it is drawn at x=2 and x=1278,
# so the window is wider and taller than the art and no part of the fighter is
# cut off by the screen edge.
FACE2_WIN_P1 = "0,180,311,1080"
FACE2_WIN_P2 = "1609,180,1920,1080"

GOLD = (206, 168, 86)
GOLD_DIM = (126, 96, 42)
GOLD_LIT = (244, 216, 120)
INK = (9, 12, 12)
ARENA_Y = 604

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
    img = art.vgrad(SCREEN, [(0, (5, 9, 10)), (390, (11, 20, 18)),
                             (750, (7, 12, 12)), (1080, (3, 6, 7))]).convert("RGBA")
    img = Image.alpha_composite(img, art.radial_light(SCREEN, (960, 375), 840,
                                                      (32, 96, 78), peak=105))

    # Slow marble smoke: soft ellipses at low alpha, each one blurred hard.
    rng = random.Random(11)
    for _ in range(22):
        cx, cy = rng.randrange(0, SCREEN[0]), rng.randrange(0, SCREEN[1])
        rx, ry = rng.randrange(210, 630), rng.randrange(105, 345)
        layer = Image.new("RGBA", SCREEN, (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                                      fill=(96, 150, 128, rng.randrange(5, 13)))
        img = Image.alpha_composite(img, layer.filter(
            ImageFilter.GaussianBlur(rng.randrange(51, 111))))

    d = ImageDraw.Draw(img)

    # The frame the grid sits in: a plate, a double gold rule, corner diamonds.
    pad = 15
    box = [GRID[0] - pad, GRID[1] - pad,
           GRID[0] + GRID_W + pad, GRID[1] + GRID_H + pad]
    d.rectangle(box, fill=(6, 9, 9, 176), outline=GOLD_DIM + (255,), width=3)
    d.rectangle([box[0] + 4, box[1] + 4, box[2] - 4, box[3] - 4],
                outline=GOLD + (232,), width=3)
    d.rectangle([box[0] + 8, box[1] + 8, box[2] - 8, box[3] - 8],
                outline=GOLD_DIM + (190,), width=2)
    for cx, cy in ((box[0], box[1]), (box[2], box[1]),
                   (box[0], box[3]), (box[2], box[3])):
        d.polygon([(cx, cy - 13), (cx + 13, cy), (cx, cy + 13), (cx - 13, cy)],
                  fill=GOLD + (255,), outline=(40, 32, 14, 255))

    # Side columns: rules marking where the two fighters stand, labelled on top.
    # The labels sit on the screen's top edge and are set at the same size as
    # the stage caption the engine draws under the arena thumbnail (font 11 =
    # the 13px Body face), so PLAYER 1, PLAYER 2 and VERSUS all read as one
    # caption line across the top instead of three unrelated sizes.
    LABEL_Y = 3
    LABEL_FONT = art.font(22)
    for x in (30, SCREEN[0] - 31):
        d.rectangle([x, LABEL_Y + 30, x + 3, SCREEN[1] - 69], fill=GOLD_DIM + (200,))
        d.rectangle([x + 1, LABEL_Y + 30, x + 1, SCREEN[1] - 69], fill=GOLD + (110,))
    cx1, cx2 = GRID[0] // 2, SCREEN[0] - GRID[0] // 2
    for cx, label in ((cx1, "PLAYER 1"), (cx2, "PLAYER 2")):
        tracked(d, (cx, LABEL_Y), label, LABEL_FONT, GOLD + (238,), tracking=2,
                anchor="ma")
        rule(d, cx - 87, cx + 87, LABEL_Y + 26, GOLD_DIM + (220,))

    # No painted "ARENA" caption: the engine draws the selected stage's own
    # name under the thumbnail, and the caption used to sit on top of the
    # preview box with nothing beneath it.

    img = art.vignette(img, strength=0.55)
    return art.grain(img, amount=5, seed=5)


def _plate(accent, dim):
    """One portrait plate: a tall coin shape with a double rule in ``accent``.

    The cells are 128x160, not squares: the grid reads as columns of figures
    rather than a wall of buttons, and the extra 32px is head room for the bust.
    The empty cell and both player cursors are this same plate, only recoloured,
    so a selection reads as the cell lighting up instead of a second, glowier
    shape pasted on top of it.
    """
    w, h = CELL, CELL_H
    r = min(w, h) // 8
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=INK + (238,),
                        outline=accent + (255,), width=4)
    d.rounded_rectangle([4, 4, w - 5, h - 5], radius=max(2, r - 2),
                        outline=(26, 24, 20, 255), width=4)
    d.rounded_rectangle([9, 9, w - 10, h - 10], radius=max(2, r - 5),
                        outline=dim + (215,), width=3)

    shade = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for y in range(7, 45):
        sd.line([(7, y), (w - 8, y)], fill=(0, 0, 0, int(74 * (1 - (y - 7) / 37.0))))
    img.alpha_composite(shade)
    return img


def cell_frame():
    """The empty portrait cell, in the screenpack's gold."""
    return _plate(GOLD, GOLD_DIM)


def cursor_frame(colour):
    """A player's selection: the cell plate in that player's colour."""
    return _plate(colour, tuple(int(c * 0.62) for c in colour))


# The random slot: a grey stone card with a question mark, drawn at the cell's
# size and, separately, at the size of the big side panels. The stock slot drew
# a recoloured 62px glyph blown up 4.8x in the panels, which is why the random
# portrait read as blank next to the painted ones.
RANDOM_CELL = (151, 0)
RANDOM_CARD = (128, 160)
RANDOM_PORTRAIT = (151, 10)
# The big panels clip to their portrait rect (8,150-308,670 on the left,
# 966,150-1266,670 on the right), so the random card is cut to fit that
# exactly - the validator refuses anything that would show around the art.
RANDOM_PANEL = (310, 900)


def random_card(size):
    """A grey plate with a big question mark: the stand-in for a random pick."""
    w, h = size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    radius = max(4, min(w, h) // 12)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius,
                        fill=(78, 82, 88, 255), outline=(18, 20, 22, 255),
                        width=2)
    inset = max(3, min(w, h) // 16)
    d.rounded_rectangle([inset, inset, w - 1 - inset, h - 1 - inset],
                        radius=max(3, radius - 2), outline=(146, 152, 160, 255),
                        width=1)
    wash = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    for y in range(inset + 1, h - inset - 1):
        k = (y - inset) / float(max(1, h - 2 * inset))
        wd.line([(inset + 1, y), (w - inset - 2, y)],
                fill=(0, 0, 0, int(58 * (1.0 - k))))
    img.alpha_composite(wash)
    font = art.font(int(min(w, h) * 0.58))
    text = "?"
    tw = d.textlength(text, font=font)
    box = d.textbbox((0, 0), text, font=font)
    th = box[3] - box[1]
    d.text(((w - tw) / 2.0, (h - th) / 2.0 - box[1]), text, font=font,
           fill=(238, 240, 244, 255), stroke_width=max(1, min(w, h) // 48),
           stroke_fill=(26, 28, 30, 255))
    return img


def repaint_random_mark():
    """Paint the random slot at cell size and at side-panel size.

    151,0 sits at (-22,-18) and the select layout compensates for it, so the
    like-for-like replacement keeps the axis it had. 151,10 is new and is what
    the big panels draw: panel-sized art at 1:1 with a zero axis.
    """
    d, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    wanted = {RANDOM_CELL: random_card(RANDOM_CARD),
              RANDOM_PORTRAIT: random_card(RANDOM_PANEL)}
    out, done = [], set()
    for sp in sprites:
        key = (sp["group"], sp["number"])
        if key in wanted:
            out.append({"group": key[0], "number": key[1],
                        "image": wanted[key], "axis": sp["axis"]})
            done.add(key)
            continue
        out.append({"group": sp["group"], "number": sp["number"],
                    "raw": sp["raw"], "format": sp["format"],
                    "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                    "axis": sp["axis"], "pal": sp["pal"], "link": sp["link"]})
    for key, image in wanted.items():
        if key not in done:
            out.append({"group": key[0], "number": key[1], "image": image,
                        "axis": (0, 0)})
    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    with open(SYSTEM_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(SYSTEM_SFF + ".tmp", SYSTEM_SFF)
    return len(wanted)


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
    # No palette menu on the select screen: it opened a "Color" panel every time
    # a fighter was picked, and the colour is a costume decision that belongs in
    # the character, not a prompt in the middle of choosing one.
    ("paletteselect", "0"),
    ("rows", str(ROWS)),
    ("columns", str(COLS)),
    ("wrapping", "1"),
    ("pos", "%d,%d" % GRID),
    ("showemptyboxes", "0"),
    ("moveoveremptyboxes", "0"),
    ("cell.size", "%d,%d" % (CELL, CELL_H)),
    ("cell.spacing", str(GAP)),
    ("cell.bg.spr", "%d,%d" % CELL_SPR),
    ("cell.bg.scale", "1,1"),
    ("cell.bg.offset", "0,0"),
    ("cell.random.spr", "151,0"),
    ("cell.random.scale", "1,1"),
    ("portrait.spr", "9000,0"),
    # the portrait art is painted at the cell's own size (build_portraits.py
    # CELL) and the bust is inset inside it, so it sits at the cell's origin -
    # nudging it in again double-counted the inset and pushed the art 4px past
    # the frame on two sides
    ("portrait.offset", "0,0"),
    ("portrait.scale", "1,1"),
    # The stage card's position, scale, window and name band all belong to
    # tools/build_select_ui.py, which runs after this one; stage.pos is
    # deliberately not set here, because the card hangs from the band now and
    # a pos written here would put the name somewhere else entirely.
    ("stage.font", "11, 0, 0, 236, 200, 120"),
    ("stage.active.font", "11, 0, 0, 255, 228, 140"),
    # The arena thumbnail. It was commented out by an older build, which left
    # the preview box showing nothing but its own frame.
    ("stage.portrait.spr", "9000,1"),
    # VERSUS is drawn by the engine: same face as the stage caption (font 11),
    # on the top edge, so it matches PLAYER 1 / PLAYER 2 and the stage name.
    ("title.offset", "960, 3"),
    ("title.font", "11, 0, 0, 255, 228, 140"),
    ("title.scale", "1,1"),
    # The big side art is the uniform 9000,2 portrait, so the two columns match
    # each other no matter how tall the fighter is in play. The art is 214x600
    # (build_portraits.py SIDE) with its axis at the top-left, so the offset is
    # where that corner goes: 4px inside the frame rule, low enough that the
    # 600px of fighter ends above the bottom of the screen. The old -78,150 came
    # from 300px-wide art and pushed a quarter of each fighter off the edge.
    ("p1.face.window", "0,0,1,1"),
    ("p1.face2.spr", "9000,2"),
    ("p1.face2.offset", "0, 180"),
    ("p1.face2.scale", "1,1"),
    ("p1.face2.window", FACE2_WIN_P1),
    ("p2.face.window", "0,0,1,1"),
    ("p2.face2.spr", "9000,2"),
    ("p2.face2.offset", "1920, 180"),
    ("p2.face2.scale", "1,1"),
    ("p2.face2.window", FACE2_WIN_P2),
    # The fighter names under the panels are engine text and were still the
    # stock face at the stock size - the largest type on the screen, which is
    # backwards: the panel exists to show the portrait, and the name was set
    # bigger than the PLAYER 1 / VERSUS captions above it. They are font 11 now
    # like the rest of the captions, and 0.25 because name text is drawn in a
    # 320x240 space inside a 1280x720 motif (x4), so a quarter scale lands it at
    # the font's own size.
    ("p1.name.font", "11, 0, 0, 255, 228, 140"),
    ("p1.name.scale", "0.25, 0.25"),
    ("p1.name.offset", "75, 1035"),
    ("p1.name.layerno", "2"),
    ("p2.name.font", "11, 0, -1, 255, 170, 96"),
    ("p2.name.scale", "0.25, 0.25"),
    ("p2.name.offset", "1845, 1035"),
    ("p2.name.layerno", "2"),
    # The "?" and the loading art stand in for the portrait, so they are drawn
    # inside the same rect and clipped by the same window. Left at the stock
    # 5x scale and a 476px-wide window they spilled past the panel and showed
    # around the preview art. Offsets below compensate for each sprite's axis:
    # 151,0 sits at (-22,-18), 151,1 (mirrored) at (31,0), 1000,1 at (0,0).
    # The random card is painted at panel size, so it draws at 1:1 from the
    # panel's corner instead of a 62px glyph blown up 4.8x.
    ("p1.face2.random.spr", "151,10"),
    # 151,10 is still the old 300x520 card, so it is scaled to the 214px panel
    # instead of drawing into the grid.
    ("p1.face2.random.offset", "0, 180"),
    ("p1.face2.random.scale", "1, 1"),
    ("p1.face2.random.window", FACE2_WIN_P1),
    ("p1.face2.loading.offset", "0, 180"),
    ("p1.face2.loading.scale", "0.3333, 0.3333"),
    ("p1.face2.loading.window", FACE2_WIN_P1),
    ("p2.face2.random.spr", "151,10"),
    # p2 draws its panel art mirrored (facing = -1), so the offset is the
    # panel's right edge and the card lands on 1066-1276.
    ("p2.face2.random.offset", "1920, 180"),
    ("p2.face2.random.scale", "1, 1"),
    ("p2.face2.random.window", FACE2_WIN_P2),
    ("p2.face2.loading.offset", "1920, 180"),
    ("p2.face2.loading.scale", "0.3333, 0.3333"),
    ("p2.face2.loading.window", FACE2_WIN_P2),
    # The random box's "?" carries the same odd axis; at 1.6x it ran 20px into
    # the cells beside it.
    ("cell.random.offset", "0,0"),
    ("cell.random.scale", "1, 1"),
    # The stock screen re-rolls the random portrait every 4 ticks and plays
    # pX.random.move.snd on every roll, which stacked voices into a continuous
    # machine-gun tone while the "?" was highlighted. Half a second per roll,
    # and the cancel flag so a new roll stops the previous sound.
    ("cell.random.switchtime", "48"),
    ("random.move.snd.cancel", "1"),
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
# art on top of the new layout. stage.portrait.spr is deliberately NOT here:
# it is the arena thumbnail, and disabling it left the preview box empty.
DISABLE = re.compile(
    r"^\s*(p[1-4]\.cursor\.(active|done)\.anim|"
    r"p[12]\.face2\.(projection|yangle|focallength))\s*=", re.IGNORECASE)


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
    marks = repaint_random_mark()
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
    sheet = Image.new("RGBA", (CELL * 3 + 32, CELL_H + 16), (24, 24, 32, 255))
    sheet.alpha_composite(cell_frame(), (8, 8))
    sheet.alpha_composite(cursor_frame(PLAYER_COLOURS[0]), (CELL + 16, 8))
    sheet.alpha_composite(cursor_frame(PLAYER_COLOURS[1]), (CELL * 2 + 24, 8))
    sheet.convert("RGB").save(os.path.join(ROOT, "artifacts", "select_cells.png"))
    print(f"select screen: {COLS}x{ROWS} grid at {GRID[0]},{GRID[1]}, "
          f"cells {CELL}px, background layer {'added' if added else 'kept'}, "
          f"{marks} random card(s) painted")


if __name__ == "__main__":
    main()
