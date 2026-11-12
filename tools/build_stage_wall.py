"""Paint the stage-screen cards: preview, gold frame and stage name, one sprite each.

The cards used to be assembled at runtime from each stage's own preview animation,
scaled through the motif's stage.portrait.scale, the stage's portraitscale, the
stage/motif localcoord ratio, the grid fit and a clip window. Those factors did not
agree: cards landed at half the box the grid reserved for them, and the picked
card's frame was drawn out in the gap beside the card.

So the picture is settled here, once, at a fixed size - and only the picture. The
screen still decides where the cards go, from start.stageGrid, and draws them 1:1.
That split is deliberate: a layout change is a number in start.lua and shows up on
the next frame, while adding a stage needs this tool run again only because the new
stage's picture has to be sized into a card.

Sprites written into data/ikemen1/system.sff (groups 240-242 are this tool's own):

    240,0 .. 240,<n-1>   one card per stage, in [ExtraStages] order, axis centred
    241,0                the picked card's frame in player 1's cursor green
    242,0                the same frame in player 2's cursor red

Run: python3 tools/build_stage_wall.py
"""

from __future__ import annotations

import os
import re
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYSTEM_SFF = os.path.join(ROOT, "data", "ikemen1", "system.sff")
SELECT_DEF = os.path.join(ROOT, "data", "select.def")

# The card's own size in motif pixels, and the number the screen draws it at. A
# different size here means a rebuild; where the cards sit does not.
CARD = (457, 150)
CARD_SPRITE = 240
FRAME_SPRITES = {1: 241, 2: 242}

# The layout below comes from start.stageGrid so the preview cannot drift from the
# screen again. WINDOW is the last known value, used only if start.lua cannot be read.
WINDOW = (80, 300, 1840, 970)
PAD = 14
# Three cards across is what the window holds, and a page is twelve of them -
# four rows, 642px - which is the size the wall was designed for. The pool is
# bigger than one page, so start.lua draws one page at a time with an arrow at
# the side of the window to turn it.
COLS = 3
PAGE_SIZE = 12
# the page arrow, and the four sprites it is baked as: left/right, at rest/lit
ARROW = (110, 150)
ARROW_SPRITE = 243
ARROW_STATES = {(False, "left"): 0, (True, "left"): 1,
                (False, "right"): 2, (True, "right"): 3}
ARROW_GOLD = (206, 168, 86)
ARROW_LIT = (255, 226, 150)
# The band a block bigger than the window may borrow: below the caption row and
# above the fighter names. start.f_stageGrid uses the same numbers.
BAND = (72, 1000)


def screen_window(path=None):
    """The stage wall's window, read from the screen that clips to it."""
    path = path or os.path.join(ROOT, "external", "script", "start.lua")
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return WINDOW
    hit = re.search(r"window\s*=\s*\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\}",
                    text)
    return tuple(int(g) for g in hit.groups()) if hit else WINDOW

# The two frame colours are the screenpack's own cursor ones, read off the sprites
# the character screen draws its cursor from: 223,0 is (72,232,96) over its shaded
# (43,139,57), 223,1 is (236,62,62) over (141,37,37). A flat single colour in a
# different green, and a blue for player 2, read as a different screen's art.
FRAME_COLOURS = {1: ((72, 232, 96), (43, 139, 57)),
                 2: ((236, 62, 62), (141, 37, 37))}
# The gold is the character cells' own gold, from 222,0, so the wall's rules and
# the names on the cards match the grid they are picked from.
GOLD = (206, 168, 86)
GOLD_DIM = (126, 96, 42)
INK = (10, 12, 16)

PREVIEW = os.path.join(ROOT, "artifacts", "stage_wall.png")


def pool():
    """The stage pool, in the order [ExtraStages] lists it.

    The screen indexes main.t_selectableStages, so card i belongs to entry i.
    """
    text = open(SELECT_DEF, encoding="utf-8", errors="replace").read()
    block = text.split("[ExtraStages]", 1)[1].split("[", 1)[0]
    refs = []
    for line in block.splitlines():
        line = line.split(";", 1)[0].strip()
        if line.lower().endswith(".def"):
            refs.append(line)
    return refs


def layout(count, window=None, pad=PAD, cols=COLS):
    """Where the screen will put the cards, for the preview only.

    Mirrors start.f_stageGrid: fixed-size cards, as many across as the window
    holds, the block centred in it - but pinned to its top-left corner when the
    block is bigger than the window, which is what the screen does too. A centred
    preview hid that: five rows of cards are 806px tall and the old 670px window
    pinned them to its top, leaving the bottom row 26px past the frame while the
    preview showed it neatly inside. Returns card centres.
    """
    window = window or screen_window()
    cw, ch = CARD
    x1, y1, x2, y2 = window
    avail_w, avail_h = x2 - x1, y2 - y1
    max_cols = max(1, (avail_w + pad) // (cw + pad))
    if cols <= 0:
        cols = min(count, max_cols)
    cols = max(1, min(cols, count))
    rows = -(-count // cols)
    block_w = cols * cw + (cols - 1) * pad
    block_h = rows * ch + (rows - 1) * pad
    ox = max(x1, x1 + (avail_w - block_w) / 2.0)
    oy = max(y1, y1 + (avail_h - block_h) / 2.0)
    if block_h > avail_h:
        oy = max(BAND[0], BAND[0] + (BAND[1] - BAND[0] - block_h) / 2.0)
    cards = []
    for i in range(count):
        col, row = i % cols, i // cols
        cards.append({"cx": ox + col * (cw + pad) + cw / 2.0,
                      "cy": oy + row * (ch + pad) + ch / 2.0,
                      "col": col, "row": row})
    return cards, cols, rows


def stage_name(def_path, fallback):
    try:
        text = open(os.path.join(ROOT, def_path), encoding="utf-8", errors="replace").read()
    except OSError:
        return fallback
    hit = re.search(r'^\s*name\s*=\s*"?([^"\r\n]+)"?\s*$', text, re.M)
    return hit.group(1).strip() if hit else fallback


def preview_art(def_path):
    """The stage's own preview sprite, scaled once to cover the card and centred.

    Cover rather than fit: a 1215x398 card and a 240x100 one are meant to read at
    the same size, and the 720p stages' previews are a different aspect. The crop
    comes from the middle, where the arena is.
    """
    w, h = CARD
    sff_path = os.path.join(ROOT, def_path[:-4] + ".sff")
    blank = Image.new("RGBA", CARD, (18, 20, 24, 255))
    try:
        data, sprites, pals = sff.read_sff(sff_path)
    except Exception:
        return blank
    chosen = None
    for want in ((9000, 1), (9000, 0)):
        for sp in sprites:
            if (sp["group"], sp["number"]) == want:
                chosen = sp
                break
        if chosen is not None:
            break
    if chosen is None:
        return blank
    img = sff.decode_sprite(data, chosen, pals).convert("RGBA")
    scale = max(w / float(img.width), h / float(img.height))
    nw = max(w, int(round(img.width * scale)))
    nh = max(h, int(round(img.height * scale)))
    img = img.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - w) // 2, (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def fit_text(draw, text, max_width, size=21, floor=13):
    while size > floor:
        f = art.font(size)
        if draw.textlength(text, font=f) <= max_width:
            return f
        size -= 1
    return art.font(floor)


def paint_card(def_path):
    """One finished card: the map, inside its gold rule, and nothing else.

    The map's name is not painted on the card. A card is a picture of the place;
    its name is drawn by the screen as text, once, where the screen's own text
    sits - so no name sits inside the art at a size and colour of its own.
    """
    w, h = CARD
    card = preview_art(def_path)
    draw = ImageDraw.Draw(card)
    draw.rectangle([0, 0, w - 1, h - 1], outline=GOLD + (255,), width=2)
    draw.rectangle([2, 2, w - 3, h - 3], outline=GOLD_DIM + (150,), width=1)
    return card


def paint_arrow(direction, lit):
    """One page arrow: a chevron on its plate, at the size the screen draws it.

    Two states, like every other control on this screen: the plate is dark and
    the chevron dim gold at rest, and both lift when the cursor stands on it -
    the same pairing the RANDOM word uses.
    """
    w, h = ARROW
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    plate = (56, 46, 26, 240) if lit else (22, 22, 24, 210)
    draw.rounded_rectangle([2, 2, w - 3, h - 3], radius=10, fill=plate,
                           outline=(ARROW_LIT if lit else ARROW_GOLD) + (255,), width=2)
    col = (ARROW_LIT if lit else ARROW_GOLD) + (255,)
    cx, cy = w / 2.0, h / 2.0
    step = 12 if direction == "right" else -12
    for k in (0, 1):
        base = cx + step * k - (6 if direction == "right" else -6)
        tip = base + (18 if direction == "right" else -18)
        draw.line([(base, cy - 30), (tip, cy)], fill=col, width=9)
        draw.line([(tip, cy), (base, cy + 30)], fill=col, width=9)
    return img


def arrow_cell(direction, window=None):
    """Where the screen puts a page arrow, in the same terms start.lua uses."""
    window = window or screen_window()
    w, h = ARROW
    x1, y1, x2, y2 = window
    cy = int(round((y1 + y2) / 2.0))
    if direction == "left":
        return {"cx": x1 + w // 2 + 16, "cy": cy}
    return {"cx": x2 - w // 2 - 16, "cy": cy}


def frame_sprite(colour, dim, reach=5, width=4):
    """The picked card's frame, in the player's own cursor colours.

    Two colours, bright face and shaded inner edge, which is how the character
    screen's cursor is shaded - and the corners run on past the card, the same
    corner marks the cursor has.
    """
    w, h = CARD[0] + reach * 2, CARD[1] + reach * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w - 1, h - 1], outline=colour + (255,), width=width)
    draw.rectangle([width, width, w - 1 - width, h - 1 - width],
                   outline=dim + (190,), width=1)
    for cx, cy, dx, dy in ((0, 0, 1, 1), (w - 1, 0, -1, 1),
                           (0, h - 1, 1, -1), (w - 1, h - 1, -1, -1)):
        draw.line([(cx, cy), (cx + dx * 18, cy)], fill=colour + (255,), width=width + 2)
        draw.line([(cx, cy), (cx, cy + dy * 18)], fill=colour + (255,), width=width + 2)
        draw.line([(cx + dx * width, cy + dy * width),
                   (cx + dx * 18, cy + dy * width)], fill=dim + (255,), width=1)
    return img


def rewrite_system_sff(images):
    """Replace groups 240-242 in system.sff, leaving everything else byte-exact.

    Dropping the old members of those groups first means a shorter pool cannot
    leave a stale card behind at the end of the wall.
    """
    _data, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    mine = {CARD_SPRITE, ARROW_SPRITE} | set(FRAME_SPRITES.values())
    out = []
    for sp in sprites:
        if sp["group"] in mine:
            continue
        out.append({"group": sp["group"], "number": sp["number"],
                    "raw": sp["raw"], "format": sp["format"],
                    "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                    "axis": sp["axis"], "pal": sp["pal"], "link": sp["link"]})
    for key in sorted(images):
        out.append({"group": key[0], "number": key[1], "image": images[key],
                    "axis": (images[key].width // 2, images[key].height // 2)})
    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: built system.sff has no signature")
    with open(SYSTEM_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(SYSTEM_SFF + ".tmp", SYSTEM_SFF)
    return len(out)


def main():
    refs = pool()
    if not refs:
        raise SystemExit("stage wall: [ExtraStages] is empty")

    images = {}
    for i, ref in enumerate(refs):
        images[(CARD_SPRITE, i)] = paint_card(ref)
    for side, group in FRAME_GROUPS_ITEMS():
        colour, dim = FRAME_COLOURS[side]
        images[(group, 0)] = frame_sprite(colour, dim)
    for (lit, direction), number in ARROW_STATES.items():
        images[(ARROW_SPRITE, number)] = paint_arrow(direction, lit)

    # The preview is what the screen shows: the first page, twelve cards, with its
    # page arrow on the right when there is a second page to turn to.
    wall = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    page = refs[:PAGE_SIZE]
    cards, cols, rows = layout(len(page))
    for i, cell in enumerate(cards):
        wall.alpha_composite(images[(CARD_SPRITE, i)],
                             (int(round(cell["cx"] - CARD[0] / 2.0)),
                              int(round(cell["cy"] - CARD[1] / 2.0))))
    if len(refs) > PAGE_SIZE:
        cell = arrow_cell("right")
        wall.alpha_composite(paint_arrow("right", False),
                             (int(round(cell["cx"] - ARROW[0] / 2.0)),
                              int(round(cell["cy"] - ARROW[1] / 2.0))))

    total = rewrite_system_sff(images)
    os.makedirs(os.path.dirname(PREVIEW), exist_ok=True)
    flat = Image.new("RGB", wall.size, (0, 0, 0))
    flat.paste(wall, (0, 0), wall)
    flat.save(PREVIEW)

    pages = max(1, -(-len(refs) // PAGE_SIZE))
    print("  stage cards: %d painted, %d card + %d frame + %d arrow sprites,"
          " system.sff now %d sprites"
          % (len(refs), len(refs), len(FRAME_SPRITES), len(ARROW_STATES), total))
    print("  card %dx%d, %d pages of %d (%d across, %d down)"
          % (CARD[0], CARD[1], pages, PAGE_SIZE, cols, rows))
    print("  preview: %s" % os.path.relpath(PREVIEW, ROOT))



def FRAME_GROUPS_ITEMS():
    return sorted(FRAME_SPRITES.items())


if __name__ == "__main__":
    main()
