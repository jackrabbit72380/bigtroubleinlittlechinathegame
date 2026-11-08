"""Paint the stage-select wall into the screenpack, at the size it is drawn.

The wall used to be assembled at runtime: one animation per stage, scaled by the
motif's stage.portrait.scale, the stage's portraitscale and the space between
the motif's localcoord and the stage's, then re-scaled again into the card's box
and clipped by a window. Every one of those factors is a chance for the picture
to land at the wrong size, and they did: the cards came out at half the box the
grid reserved for them, in a wall of gaps, with the picked card's frame drawn
somewhere else entirely.

This paints the finished wall instead. Each card is decoded from its stage's own
preview sprite (9000,1), scaled once, framed, given a name strip, and composited
at the position the grid gives it - all in Python, where the result can be looked
at. The screen then draws one sprite at 0,0, the same 1:1 draw the PLAYER captions
and the character wall use.

Sprites written into data/ikemen1/system.sff:

    240,0        the whole wall, 1920x1080, axis 0,0 - draw at 0,0
    241,0-11     the picked card's frame, player 1's green, one per card
    242,0-11     the same frame in player 2's blue

The frames carry their own position in their axis, so the screen draws them at
0,0 as well and needs no layout of its own.

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

WALL_SPRITE = (240, 0)
FRAME_GROUPS = {1: 241, 2: 242}

# The layout, mirroring start.stageGrid in external/script/start.lua. NOMINAL is
# what a card is DRAWN at: stage.portrait.scale 0.856 (and each stage's own
# portraitscale, and the stage's localcoord) already land every stage's preview
# at 1040x341 motif pixels, so one pair of numbers frames all twelve.
SCREEN = (1920, 1080)
WINDOW = (80, 300, 1840, 970)
PAD = 14
NOMINAL_W, NOMINAL_H = 1040.0, 341.0

GOLD = (236, 200, 120)
GOLD_DIM = (150, 118, 62)
INK = (10, 12, 16)
P1_GREEN = (116, 255, 128)
P2_BLUE = (122, 200, 255)

NAME_STRIP = 30
PREVIEW = os.path.join(ROOT, "artifacts", "stage_wall.png")


def pool():
    """The stage pool, in the order [ExtraStages] lists it.

    The screen indexes this list, so the bake has to walk it in the same order:
    card i is sprite 241/242,<i-1>.
    """
    text = open(SELECT_DEF, encoding="utf-8", errors="replace").read()
    block = text.split("[ExtraStages]", 1)[1]
    block = block.split("[", 1)[0]
    refs = []
    for line in block.splitlines():
        line = line.split(";", 1)[0].strip()
        if line.lower().endswith(".def"):
            refs.append(line)
    return refs


def grid(count):
    """The card boxes, worked out the way start.f_stageGrid does.

    Same fit: pick the column count that makes the cards biggest, then hand back
    each card's box. Kept in step with the Lua by tools/test_selectscreen.py,
    which runs the Lua block and compares the two.
    """
    def fit(cols):
        cols = min(cols, count)
        rows = -(-count // cols)
        cw = ((WINDOW[2] - WINDOW[0]) - PAD * (cols + 1)) / float(cols)
        ch = ((WINDOW[3] - WINDOW[1]) - PAD * (rows + 1)) / float(rows)
        return min(cw / NOMINAL_W, ch / NOMINAL_H), rows, cw, ch

    best, cols = 0.0, 1
    for c in range(1, count + 1):
        sc = fit(c)[0]
        if sc > best + 1e-9:
            best, cols = sc, c
    scale, rows, cell_w, cell_h = fit(cols)
    cols = -(-count // rows)
    w, h = NOMINAL_W * scale, NOMINAL_H * scale
    cards = []
    for i in range(1, count + 1):
        col = (i - 1) % cols
        row = (i - 1) // cols
        cards.append({
            "x": WINDOW[0] + PAD + col * (cell_w + PAD) + (cell_w - w) * 0.5,
            "y": WINDOW[1] + PAD + row * (cell_h + PAD) + (cell_h - h) * 0.5,
            "w": w,
            "h": h,
        })
    return cards


def stage_name(def_path, fallback):
    """The name the stage screen shows for this stage."""
    try:
        text = open(os.path.join(ROOT, def_path), encoding="utf-8", errors="replace").read()
    except OSError:
        return fallback
    hit = re.search(r'^\s*name\s*=\s*"?([^"\r\n]+)"?\s*$', text, re.M)
    if hit:
        return hit.group(1).strip()
    return fallback


def preview_art(def_path, size):
    """The stage's preview sprite, scaled to cover `size` and centred.

    Cover rather than fit: a 1215x398 card and a 240x100 one are meant to read at
    the same size, and the 720p stages' previews are a different aspect. Filling
    the box keeps the wall even; the crop is taken from the middle, where the
    arena is.
    """
    sff_path = os.path.join(ROOT, def_path[:-4] + ".sff")
    w, h = int(round(size[0])), int(round(size[1]))
    try:
        data, sprites, pals = sff.read_sff(sff_path)
    except Exception:
        return Image.new("RGBA", (w, h), (18, 20, 24, 255))
    chosen = None
    for want in ((9000, 1), (9000, 0)):
        for sp in sprites:
            if (sp["group"], sp["number"]) == want:
                chosen = sp
                break
        if chosen is not None:
            break
    if chosen is None:
        return Image.new("RGBA", (w, h), (18, 20, 24, 255))
    art_img = sff.decode_sprite(data, chosen, pals).convert("RGBA")
    scale = max(w / float(art_img.width), h / float(art_img.height))
    nw = max(w, int(round(art_img.width * scale)))
    nh = max(h, int(round(art_img.height * scale)))
    art_img = art_img.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    return art_img.crop((left, top, left + w, top + h))


def fit_text(draw, text, max_width, size=21, floor=13):
    """The display face at the largest size that fits the strip."""
    while size > floor:
        f = art.font(size)
        if draw.textlength(text, font=f) <= max_width:
            return f
        size -= 1
    return art.font(floor)


def paint_card(def_path, box, index):
    """One finished card: the preview, its gold frame and its name."""
    w, h = int(round(box["w"])), int(round(box["h"]))
    card = preview_art(def_path, (w, h))
    draw = ImageDraw.Draw(card)

    # the name strip: the wall has no room for a caption row under it, and the
    # shared one collided with the two fighter names
    name = stage_name(def_path, os.path.basename(def_path)[:-4].replace("_", " ").title())
    strip_h = NAME_STRIP
    strip = Image.new("RGBA", (w, strip_h), INK + (216,))
    card.paste(strip, (0, h - strip_h), strip)
    draw = ImageDraw.Draw(card)
    font = fit_text(draw, name, w - 24)
    tw = draw.textlength(name, font=font)
    box_t = draw.textbbox((0, 0), name, font=font)
    draw.text(((w - tw) / 2.0, h - strip_h + (strip_h - (box_t[3] - box_t[1])) / 2.0 - box_t[1]),
              name, font=font, fill=GOLD + (255,))

    # the frame every card wears, and the shade that separates it from its
    # neighbour when two cards meet
    draw.rectangle([0, 0, w - 1, h - 1], outline=GOLD + (255,), width=2)
    draw.rectangle([2, 2, w - 3, h - 3], outline=GOLD_DIM + (150,), width=1)
    return card


def frame_sprite(box, colour, reach=6, width=4):
    """The picked card's frame, with its position in the axis.

    Axis = -(corner), so drawing the sprite at 0,0 puts it on the card it marks.
    """
    w = int(round(box["w"])) + reach * 2
    h = int(round(box["h"])) + reach * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w - 1, h - 1], outline=colour + (255,), width=width)
    draw.rectangle([width, width, w - 1 - width, h - 1 - width],
                   outline=colour + (90,), width=1)
    # corner ticks, so the frame still reads over a bright card
    for cx, cy, dx, dy in ((0, 0, 1, 1), (w - 1, 0, -1, 1),
                           (0, h - 1, 1, -1), (w - 1, h - 1, -1, -1)):
        draw.line([(cx, cy), (cx + dx * 18, cy)], fill=colour + (255,), width=width + 2)
        draw.line([(cx, cy), (cx, cy + dy * 18)], fill=colour + (255,), width=width + 2)
    axis = (int(round(-(box["x"] - reach))), int(round(-(box["y"] - reach))))
    return img, axis


def rewrite_system_sff(images, axes, blank_groups=(240, 241, 242)):
    """Replace or append sprites in system.sff, leaving the rest byte-exact.

    Groups 240-242 are this tool's own: whatever an older bake left there is
    dropped first, so the pool can shrink without orphans staying in the file.
    """
    _data, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    out, done = [], set()
    for sp in sprites:
        key = (sp["group"], sp["number"])
        if sp["group"] in blank_groups:
            continue
        if key in images:
            continue
        out.append({"group": sp["group"], "number": sp["number"],
                    "raw": sp["raw"], "format": sp["format"],
                    "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                    "axis": sp["axis"], "pal": sp["pal"], "link": sp["link"]})
    for key in sorted(images):
        out.append({"group": key[0], "number": key[1],
                    "image": images[key], "axis": axes.get(key, (0, 0))})
        done.add(key)
    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: built system.sff has no signature")
    with open(SYSTEM_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(SYSTEM_SFF + ".tmp", SYSTEM_SFF)
    return len(out), len(done)


def main():
    refs = pool()
    if not refs:
        raise SystemExit("stage wall: [ExtraStages] is empty")
    cards = grid(len(refs))

    wall = Image.new("RGBA", SCREEN, (0, 0, 0, 0))
    images, axes = {}, {}
    for i, (ref, box) in enumerate(zip(refs, cards), start=1):
        card = paint_card(ref, box, i)
        wall.alpha_composite(card, (int(round(box["x"])), int(round(box["y"]))))
        for side, group in FRAME_GROUPS.items():
            colour = P1_GREEN if side == 1 else P2_BLUE
            img, axis = frame_sprite(box, colour)
            images[(group, i - 1)] = img
            axes[(group, i - 1)] = axis

    images[WALL_SPRITE] = wall
    axes[WALL_SPRITE] = (0, 0)
    total, written = rewrite_system_sff(images, axes)

    os.makedirs(os.path.dirname(PREVIEW), exist_ok=True)
    flat = Image.new("RGB", SCREEN, (0, 0, 0))
    flat.paste(wall, (0, 0), wall)
    flat.save(PREVIEW)

    print("  stage wall: %d cards, %d sprites (wall + %d frames), system.sff now %d sprites"
          % (len(refs), written, written - 1, total))
    cols = len({round(c["x"], 3) for c in cards})
    rows = len({round(c["y"], 3) for c in cards})
    card = cards[0]
    print("  %d cards in %d columns x %d rows, card %dx%d at %.0f,%.0f"
          % (len(refs), cols, rows, round(card["w"]), round(card["h"]),
             card["x"], card["y"]))
    print("  preview: %s" % os.path.relpath(PREVIEW, ROOT))


if __name__ == "__main__":
    main()
