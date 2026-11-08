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
    241,0                the picked card's frame, player 1's green, axis centred
    242,0                the same frame in player 2's blue

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

# Only used to composite the preview image below with the same numbers
# start.stageGrid uses, so the preview shows the wall as the screen lays it out.
WINDOW = (80, 300, 1840, 970)
PAD = 14
COLS = 0

GOLD = (236, 200, 120)
GOLD_DIM = (150, 118, 62)
INK = (10, 12, 16)
P1_GREEN = (116, 255, 128)
P2_BLUE = (122, 200, 255)
NAME_STRIP = 30

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


def layout(count, window=WINDOW, pad=PAD, cols=COLS):
    """Where the screen will put the cards, for the preview only.

    Mirrors start.f_stageGrid: fixed-size cards, as many across as the window
    holds, the block centred in it. Returns card centres.
    """
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
    ox = x1 + (avail_w - block_w) / 2.0
    oy = y1 + (avail_h - block_h) / 2.0
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
    """One finished card: the map, a gold rule, and the stage's name under it."""
    w, h = CARD
    card = preview_art(def_path)
    name = stage_name(def_path,
                      os.path.basename(def_path)[:-4].replace("_", " ").title())
    strip = Image.new("RGBA", (w, NAME_STRIP), INK + (216,))
    card.paste(strip, (0, h - NAME_STRIP), strip)
    draw = ImageDraw.Draw(card)
    font = fit_text(draw, name, w - 24)
    tw = draw.textlength(name, font=font)
    bbox = draw.textbbox((0, 0), name, font=font)
    draw.text(((w - tw) / 2.0,
               h - NAME_STRIP + (NAME_STRIP - (bbox[3] - bbox[1])) / 2.0 - bbox[1]),
              name, font=font, fill=GOLD + (255,))
    draw.rectangle([0, 0, w - 1, h - 1], outline=GOLD + (255,), width=2)
    draw.rectangle([2, 2, w - 3, h - 3], outline=GOLD_DIM + (150,), width=1)
    return card


def frame_sprite(colour, reach=5, width=4):
    """The picked card's frame, centred on its card like the card itself."""
    w, h = CARD[0] + reach * 2, CARD[1] + reach * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w - 1, h - 1], outline=colour + (255,), width=width)
    draw.rectangle([width, width, w - 1 - width, h - 1 - width],
                   outline=colour + (90,), width=1)
    for cx, cy, dx, dy in ((0, 0, 1, 1), (w - 1, 0, -1, 1),
                           (0, h - 1, 1, -1), (w - 1, h - 1, -1, -1)):
        draw.line([(cx, cy), (cx + dx * 18, cy)], fill=colour + (255,), width=width + 2)
        draw.line([(cx, cy), (cx, cy + dy * 18)], fill=colour + (255,), width=width + 2)
    return img


def rewrite_system_sff(images):
    """Replace groups 240-242 in system.sff, leaving everything else byte-exact.

    Dropping the old members of those groups first means a shorter pool cannot
    leave a stale card behind at the end of the wall.
    """
    _data, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    mine = {CARD_SPRITE} | set(FRAME_SPRITES.values())
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
    wall = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    cards, cols, rows = layout(len(refs))
    for i, (ref, cell) in enumerate(zip(refs, cards)):
        card = paint_card(ref)
        images[(CARD_SPRITE, i)] = card
        wall.alpha_composite(card, (int(round(cell["cx"] - CARD[0] / 2.0)),
                                    int(round(cell["cy"] - CARD[1] / 2.0))))
    for side, group in FRAME_GROUPS_ITEMS():
        images[(group, 0)] = frame_sprite(P1_GREEN if side == 1 else P2_BLUE)

    total = rewrite_system_sff(images)
    os.makedirs(os.path.dirname(PREVIEW), exist_ok=True)
    flat = Image.new("RGB", wall.size, (0, 0, 0))
    flat.paste(wall, (0, 0), wall)
    flat.save(PREVIEW)

    print("  stage cards: %d painted, %d card + %d frame sprites, system.sff now %d sprites"
          % (len(refs), len(refs), len(FRAME_SPRITES), total))
    print("  card %dx%d, layout preview at %dx%d cards (%d across)"
          % (CARD[0], CARD[1], cols, rows, cols))
    print("  preview: %s" % os.path.relpath(PREVIEW, ROOT))


def FRAME_GROUPS_ITEMS():
    return sorted(FRAME_SPRITES.items())


if __name__ == "__main__":
    main()
