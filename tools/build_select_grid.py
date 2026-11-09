"""Repaint the character-select screen as an MKT HD style portrait grid.

The staged screenpack lays the roster out as a 10x8 wall of 24px cells seen in
perspective, which reads nothing like the arcade game this project chases. This
paints the arcade layout instead: eight framed portraits across, six rows down -
the whole cast, no empty cells - the selected fighters standing large down the
left and right edges, and RANDOM set as a plain word under the wall.

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

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYSTEM_SFF = os.path.join(ROOT, "data", "ikemen1", "system.sff")
SYSTEM_DEF = os.path.join(ROOT, "data", "ikemen1", "system.def")

SCREEN = (1920, 1080)
# 8x6 = 48 cells, exactly the cast in data/select.def: eight portraits across and
# six rows down, so not one cell of the wall is empty. RANDOM is not a cell any
# more - it is a label under the wall, and the seventh row of the grid is only
# there to give it a cursor stop (seven skipslot slots and the randomselect).
#
# 8 * 112 + 7 * 2 = 910 wide, 6 * 140 + 5 * 2 = 850 tall, so the wall spans
# x=505 to x=1415 and the two side columns keep their air either side.
# The cells were 128x160 until the header and the RANDOM word were taken to the
# mode title's own size: that size needs a clean band at the top of the screen
# and a taller one under the frame, so the grid gives up 12px across and 15px
# down - still 4:5, so the portraits keep their shape, and the whole cast still
# fits one page.
CELL, CELL_H = 112, 140
CELL_PAD = 0               # no air: cell.spacing alone separates the boxes
GAP = 2
COLS, ROWS = 8, 7
# The painted wall, its frame and the name row are the fighter rows only: the
# last logical row is the RANDOM stop, drawn as text outside the frame.
FIGHTER_ROWS = ROWS - 1
# The wall is centred and hangs from y=108, not y=46: the header row (PLAYER 1 /
# VERSUS / PLAYER 2) is drawn at the mode title's own size, so the frame starts
# below that row instead of cutting through it, and the band under the frame is
# deep enough for RANDOM at the same size.
GRID = ((SCREEN[0] - (COLS * CELL + (COLS - 1) * GAP)) // 2, 108)
GRID_W = COLS * CELL + (COLS - 1) * GAP
GRID_H = FIGHTER_ROWS * CELL_H + (FIGHTER_ROWS - 1) * GAP

BG_SPR = (220, 0)          # the wall of cells, drawn by start.lua
BASE_SPR = (225, 0)        # the same backdrop without the wall
CELL_SPR = (222, 0)
CURSOR = ((223, 0), (223, 1), (223, 2), (223, 3))
AXIS = (0, 0)
# Big side portraits: the panel window the 9000,2 art is clipped to, left/right.
# The grid's frame padding ends at x=426 and x=1494, so each window stops well
# short of it and the standing fighters never meet the wall.
# The art is the full standing fighter now (build_portraits.py SIDE, doubled for
# a 960 localcoord character), and the panel is sized from it rather than from a
# number typed by hand. It used to be a 310x900 column of cropped fighter with
# 62% of his width cut away, hung from y=180 so the feet landed exactly on the
# 1080 clipping line: the two side fighters were slices with their shoes sawn
# off. The column is 426px before it meets the grid frame, so 380px of art with
# 20px of air either side is the widest a whole standing fighter can be here,
# and the top is derived from the art height and a foot margin.
SIDE_INSET = 20
SIDE_ART = (380, 500)          # 9000,2 at scale 1, in screen pixels
# The margin is the room the name line needs: p1/p2.name sit at y=1035, so a
# fighter standing on a 20px margin had his shoes drawn through his own name.
# 70px puts the art's floor at 1010, clear of the text.
FACE2_MARGIN = 70              # air under the feet, and the name line's room
FACE2_PAD = 2                  # the art is edge-to-edge; clip just outside it
FACE2_TOP = SCREEN[1] - SIDE_ART[1] - FACE2_MARGIN
FACE2_WIN_P1 = "%d,%d,%d,%d" % (SIDE_INSET - FACE2_PAD, FACE2_TOP - FACE2_PAD,
                               SIDE_INSET + SIDE_ART[0] + FACE2_PAD,
                               FACE2_TOP + SIDE_ART[1] + FACE2_PAD)
FACE2_WIN_P2 = "%d,%d,%d,%d" % (1920 - SIDE_INSET - SIDE_ART[0] - FACE2_PAD,
                               FACE2_TOP - FACE2_PAD,
                               1920 - SIDE_INSET + FACE2_PAD,
                               FACE2_TOP + SIDE_ART[1] + FACE2_PAD)

GREEN = (72, 232, 96)          # player 1's cursor, the green the RANDOM word uses
GREEN_LIT = (118, 246, 132)    # the RANDOM word once a player is on that stop
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
PLAYER_COLOURS = ((72, 232, 96), (236, 62, 62), (176, 132, 240), (96, 208, 232))
# Before a pick is confirmed the outline flashes white for both players; the
# colour is the done state. Same geometry, only the ink differs.
CURSOR_WHITE = ((224, 0), (224, 1), (224, 2), (224, 3))
# The cursor is painted at twice the cell and drawn at half scale: a 128x160
# sheet drawn 1:1 gave its rounded corners a staircase edge, which is what the
# selection box looked like up close. At 2x, resampled down, the corners are
# smooth and the rules stay 4 screen pixels wide.
CURSOR_RES = 2
# One action per player: the player's colour flashing white while choosing, so
# the flash runs on the engine's own animation clock. The done cursors stay
# solid, which is what tells a locked-in pick from one still being moved.
CURSOR_ACTIONS = ((160, (223, 0), (224, 0)), (170, (223, 1), (224, 1)),
                  (172, (223, 2), (224, 2)), (174, (223, 3), (224, 3)))
CURSOR_FLASH = 6

# The stage wall's lit card. The character cell's cursor art is 4:5, so stretching
# it over a 3:1 stage card gave the frame 14px sides and 4px top and bottom rules.
# These are painted at the card's own aspect instead - 1215x398, the size
# tools/build_stages.py bakes the card art at - so every side carries the same
# weight whatever the wall's cards are. start.lua builds them with animNew, the
# way it builds the RANDOM word, and draws the picked card's one in that
# player's colour.
STAGE_FRAME = ((230, 0), (230, 1), (230, 2), (230, 3))
STAGE_FRAME_SIZE = (1215, 398)


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


def background(grid=True):
    """1920x1080 select backdrop: stone, jade haze, gold frame.

    ``grid=False`` leaves the wall of portrait cells out, so the stage screen can
    stand on the same backdrop without a character grid showing behind its cards.
    """
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
    if not grid:
        d.rectangle([0, 0, SCREEN[0] - 1, SCREEN[1] - 1], outline=INK + (255,), width=1)
        d.rectangle([1, 1, SCREEN[0] - 2, SCREEN[1] - 2], outline=GOLD + (255,), width=4)
        d.rectangle([5, 5, SCREEN[0] - 6, SCREEN[1] - 6], outline=GOLD_DIM + (230,), width=2)
        img = art.vignette(img, strength=0.55)
        return art.grain(img, amount=5, seed=5)

    # The frame the grid sits in: a plate, a double gold rule, corner diamonds.
    pad = 15
    box = [GRID[0] - pad, GRID[1] - pad,
           GRID[0] + GRID_W + pad, GRID[1] + GRID_H + pad]
    # No plate behind the wall: the stone, the jade haze and the smoke are the
    # background, and the old near-black wash turned the middle of the screen
    # into a black board that the cells sat on.
    d.rectangle(box, outline=GOLD_DIM + (255,), width=5)
    d.rectangle([box[0] + 4, box[1] + 4, box[2] - 4, box[3] - 4],
                outline=GOLD + (255,), width=5)
    d.rectangle([box[0] + 8, box[1] + 8, box[2] - 8, box[3] - 8],
                outline=GOLD_DIM + (235,), width=3)
    for cx, cy in ((box[0], box[1]), (box[2], box[1]),
                   (box[0], box[3]), (box[2], box[3])):
        d.polygon([(cx, cy - 13), (cx + 13, cy), (cx, cy + 13), (cx - 13, cy)],
                  fill=GOLD + (255,), outline=(40, 32, 14, 255))

    # Side columns: rules marking where the two fighters stand. The PLAYER 1 /
    # PLAYER 2 captions are no longer painted here: they were set in a TrueType
    # face at their own size, while the mode title between them is the engine's
    # bitmap font 11, so the three words never matched in face, size or height.
    # start.lua draws both labels now, with the title's own font object on the
    # title's own row, so the three cannot drift apart.
    # Every portrait cell's frame is painted here and the engine's own plate is
    # switched off (cell.bg.spr = -1). The grid reserves a seventh row so the
    # RANDOM stop has somewhere to sit, and with cell.bg.spr set the engine
    # ruled that empty row too - the stray box under the wall. Painted frames
    # only exist where a fighter does.
    frame = cell_frame()
    for row in range(FIGHTER_ROWS):
        for col in range(COLS):
            img.alpha_composite(frame, (GRID[0] + col * (CELL + GAP),
                                        GRID[1] + row * (CELL_H + GAP)))

    # No painted "ARENA" caption: the engine draws the selected stage's own
    # name under the thumbnail, and the caption used to sit on top of the
    # preview box with nothing beneath it.

    img = art.vignette(img, strength=0.55)

    # The frame that used to be two gold lines near the side edges is now one
    # rule around the whole picture, on the very edge, in the same gold as the
    # portrait boxes.
    d2 = ImageDraw.Draw(img)
    d2.rectangle([0, 0, SCREEN[0] - 1, SCREEN[1] - 1], outline=INK + (255,), width=1)
    d2.rectangle([1, 1, SCREEN[0] - 2, SCREEN[1] - 2], outline=GOLD + (255,), width=4)
    d2.rectangle([5, 5, SCREEN[0] - 6, SCREEN[1] - 6], outline=GOLD_DIM + (230,), width=2)

    return art.grain(img, amount=5, seed=5)


LABEL_SPR = ((151, 20), (151, 21))
LABEL_WORDS = ("PLAYER 1", "PLAYER 2")
# The same three words again in the Karate face. The captions and the RANDOM stop
# are painted art, so they cannot follow Options > Font on their own; every word
# on this screen is set in the mode title's face, so each is painted twice and
# start.lua draws the pair the saved pick names.
KARATE_LABEL = ((151, 22), (151, 23))
KARATE_RANDOM = (151, 13)
KARATE_RANDOM_MARK = (151, 12)

# The words on the select screen are painted in the mode title's own face, at the
# title's own size. title.font is font 10, i.e. the bitmap Display face baked by
# tools/build_fonts.py, drawn at title.scale 0.75 - so copying glyphs out of
# Display.sff at that scale gives PLAYER 1, PLAYER 2 and RANDOM the exact size,
# shape, face and colours the engine gives VERSUS, instead of a second face
# (DejaVu at a size of its own, flat gold) that only looked similar.
DISPLAY_DEF = os.path.join(ROOT, "data", "ikemen1", "fonts", "Display.def")
DISPLAY_SFF = os.path.join(ROOT, "data", "ikemen1", "fonts", "Display.sff")
KARATE_DEF = os.path.join(ROOT, "data", "ikemen1", "fonts", "DisplayK.def")
KARATE_SFF = os.path.join(ROOT, "data", "ikemen1", "fonts", "DisplayK.sff")
TITLE_SCALE = 0.75             # title.scale in [Select Info]
WORD_PAD = 2                   # clear pixels round every word, so no ink on the edge


def face_files(face="original"):
    """The .def and .sff of one of the two faces this screen can wear."""
    if face == "karate":
        return KARATE_DEF, KARATE_SFF
    return DISPLAY_DEF, DISPLAY_SFF


def display_face(face="original"):
    """(glyphs by character, the face's space advance) from that face's art."""
    def_path, sff_path = face_files(face)
    if not (os.path.isfile(def_path) and os.path.isfile(sff_path)):
        raise SystemExit("select screen: the %s face is missing" % face)
    space = 30.0
    with open(def_path, encoding="utf-8-sig", errors="replace") as fh:
        for line in fh:
            if line.strip().lower().startswith("size"):
                try:
                    space = float(line.split("=", 1)[1].split(",")[0])
                except (IndexError, ValueError):
                    pass
                break
    data, sprites, palettes = sff.read_sff(sff_path)
    glyphs = {}
    for sp in sprites:
        if sp["group"] == 0 and 33 <= sp["number"] <= 126:
            glyphs[chr(sp["number"])] = sff.decode_sprite(
                data, sp, palettes, sp["pal"]).convert("RGBA")
    if not glyphs:
        raise SystemExit("select screen: the %s face has no glyphs" % face)
    return glyphs, space


def tint_word(img, colour):
    """Recolour a word, keeping the face's extrusion and lip shading."""
    alpha = img.getchannel("A")
    lum = img.convert("L")
    shade = Image.eval(lum, lambda v: 96 + (v * 159) // 255)
    out = Image.new("RGBA", img.size, tuple(colour) + (255,))
    out.putalpha(ImageChops.multiply(alpha, shade))
    return out


def display_word(text, scale=TITLE_SCALE, tint=None, face="original",
                 canvas=None, align="left"):
    """A word set the way the engine sets the mode title.

    Same glyph art, same advance (the engine advances by the sprite's width) and
    same text scale as title.font / title.scale, so a caption drawn from this is
    the title's own type, not an imitation of it.

    ``face`` picks which of the two baked typefaces the glyphs come from, and
    ``canvas`` pins the painted box instead of letting the word size it - that is
    what lands the second face on a sprite the screen already places by size.
    """
    glyphs, space = display_face(face)
    cell_h = max(g.height for g in glyphs.values())
    if canvas is not None:
        # Fit inside the box the other face fills: whichever limit bites first,
        # height or width, decides the scale, so no word can overflow.
        natural = sum(space if ch == " " else glyphs[ch].width
                      for ch in text if ch == " " or ch in glyphs)
        scale = min((canvas[1] - 2 * WORD_PAD) / float(cell_h),
                    (canvas[0] - 2 * WORD_PAD) / float(max(1, natural)))
    x = 0.0
    pieces = []
    for ch in text:
        if ch == " ":
            x += space * scale
            continue
        g = glyphs.get(ch)
        if g is None:
            raise SystemExit("select screen: the %s face has no %r" % (face, ch))
        w = max(1, int(round(g.width * scale)))
        h = max(1, int(round(g.height * scale)))
        pieces.append((x, g.resize((w, h), Image.LANCZOS) if (w, h) != g.size else g))
        x += g.width * scale
    if canvas is None:
        size = (int(round(x)) + 2 * WORD_PAD,
                int(round(cell_h * scale)) + 2 * WORD_PAD)
        left = WORD_PAD
    else:
        size = (canvas[0], canvas[1])
        left = WORD_PAD if align != "centre" else int(round((size[0] - x) / 2.0))
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    for px, g in pieces:
        img.alpha_composite(g, (int(round(px)) + left, WORD_PAD))
    if tint is not None:
        img = tint_word(img, tint)
    return img

def grid_overlay():
    """The wall of portrait cells on its own, for start.lua to draw."""
    img = Image.new("RGBA", SCREEN, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = 15
    box = [GRID[0] - pad, GRID[1] - pad,
           GRID[0] + GRID_W + pad, GRID[1] + GRID_H + pad]
    d.rectangle(box, outline=GOLD_DIM + (255,), width=5)
    d.rectangle([box[0] + 4, box[1] + 4, box[2] - 4, box[3] - 4],
                outline=GOLD + (255,), width=5)
    d.rectangle([box[0] + 8, box[1] + 8, box[2] - 8, box[3] - 8],
                outline=GOLD_DIM + (235,), width=3)
    for cx, cy in ((box[0], box[1]), (box[2], box[1]),
                   (box[0], box[3]), (box[2], box[3])):
        d.polygon([(cx, cy - 13), (cx + 13, cy), (cx, cy + 13), (cx - 13, cy)],
                  fill=GOLD + (255,), outline=(40, 32, 14, 255))
    frame = cell_frame()
    for row in range(FIGHTER_ROWS):
        for col in range(COLS):
            img.alpha_composite(frame, (GRID[0] + col * (CELL + GAP),
                                        GRID[1] + row * (CELL_H + GAP)))
    return img


def label_word(text, face="original", canvas=None):
    """PLAYER 1 / PLAYER 2 as their own sprite, in the mode title's own face.

    The select screen used to carry these two captions in the backdrop picture
    itself: they sat through the stage screen and could not be sized against the
    mode title drawn between them. They are drawn by start.lua now, at the size
    they are painted, so they sit on the title's own row.
    """
    return display_word(text, face=face, canvas=canvas)


def _plate(accent, dim):
    """One portrait cell: a hollow gold frame, inset inside its cell.

    The cells are 128x160, not squares: the grid reads as columns of figures
    rather than a wall of buttons, and the extra 32px is head room for the bust.

    The cell used to be a near-black plate filled to its own edges, so the wall
    read as a black board with gold boxes ruled onto it - and at a 2px cell
    spacing each box met the next one's box. The fill is gone, so the painted
    backdrop shows through the middle of every cell. The frame is drawn to the
    cell's own edges, so the only thing between two boxes is the engine's 2px
    cell.spacing: the gold rules of neighbours stand 2px apart and never touch.
    """
    w, h = CELL, CELL_H
    p = CELL_PAD
    r = max(4, min(w, h) // 8 - p)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    box = [p, p, w - 1 - p, h - 1 - p]
    d.rounded_rectangle(box, radius=r, outline=accent + (255,), width=4)
    d.rounded_rectangle([box[0] + 4, box[1] + 4, box[2] - 4, box[3] - 4],
                        radius=max(2, r - 2), outline=(26, 24, 20, 255), width=4)
    d.rounded_rectangle([box[0] + 9, box[1] + 9, box[2] - 9, box[3] - 9],
                        radius=max(2, r - 5), outline=dim + (215,), width=3)
    return img


def cell_frame():
    """The empty portrait cell, in the screenpack's gold."""
    return _plate(GOLD, GOLD_DIM)


def cursor_frame(colour):
    """A player's selection: the cell's frame in that player's colour, hollow.

    This was the whole plate, dark fill and all, so the selected cell was the one
    portrait nobody could see. Only the rules are drawn now - a dark keyline
    outside for contrast on pale art, the player's colour over it, a thin inner
    rule, and nothing at all in the middle, so the fighter shows through.

    Painted at CURSOR_RES times the cell and drawn at 1/CURSOR_RES, and at 4x
    inside that before being resampled, because at 1:1 the rounded corners were
    a staircase of single pixels - the "pixellated" edge on the selection box.
    """
    w, h = CELL * CURSOR_RES, CELL_H * CURSOR_RES
    ss = 4
    big = (w * ss, h * ss)
    img = Image.new("RGBA", big, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    k = CURSOR_RES * ss                       # screen pixel -> canvas pixel
    p = CELL_PAD * k
    W, H = big
    r = max(4, min(CELL, CELL_H) // 8 - CELL_PAD) * k
    dim = tuple(int(c * 0.60) for c in colour)
    d.rounded_rectangle([p, p, W - 1 - p, H - 1 - p], radius=r,
                        outline=INK + (215,), width=max(1, k))
    d.rounded_rectangle([p + k, p + k, W - 2 - p, H - 2 - p],
                        radius=max(2, r - k), outline=colour + (255,), width=4 * k)
    d.rounded_rectangle([p + 7 * k, p + 7 * k, W - 8 - p, H - 8 - p],
                        radius=max(2, r - 4 * k), outline=dim + (235,), width=2 * k)
    # corner ticks: the frame still reads when its rules run over bright art
    tick, inset = 22 * k, p + 6 * k
    for x, y, dx, dy in ((inset, inset, 1, 1), (W - 1 - inset, inset, -1, 1),
                         (inset, H - 1 - inset, 1, -1),
                         (W - 1 - inset, H - 1 - inset, -1, -1)):
        d.line([(x, y + dy * tick), (x, y), (x + dx * tick, y)],
               fill=colour + (255,), width=3 * k)
    return img.resize((w, h), Image.LANCZOS)


# The random slot is a word under the wall, not a portrait: 151,0 is RANDOM set
# in gold and 151,11 is the same word in green, which start.lua draws in place
# of the cell cursor. Neither carries a plate or a frame.
# The big side panels keep the stone card with the question mark.
RANDOM_CELL = (151, 0)
RANDOM_MARK = (151, 11)
RANDOM_LABEL = (128, 30)
RANDOM_PORTRAIT = (151, 10)
# The big panels clip to their portrait rect (8,150-308,670 on the left,
# 966,150-1266,670 on the right), so the random card is cut to fit that
# exactly - the validator refuses anything that would show around the art.
RANDOM_PANEL = (380, 500)


def stage_frame(colour):
    """The picked stage's frame: hollow, 3:1, in that player's colour."""
    w, h = STAGE_FRAME_SIZE
    ss = 2
    img = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    W, H = img.size
    key = 10 * ss                     # dark keyline, so the frame holds on pale art
    band = 10 * ss                    # the player's colour
    d.rectangle([0, 0, W - 1, H - 1], outline=(10, 14, 22, 255), width=key)
    d.rectangle([key, key, W - 1 - key, H - 1 - key], outline=colour + (255,), width=band)
    light = tuple(min(255, c + 70) for c in colour)
    d.rectangle([key + band, key + band, W - 1 - key - band, H - 1 - key - band],
                outline=light + (200,), width=2 * ss)
    # corner ticks, so the frame still reads where it crosses bright art
    tick, inset = 54 * ss, key
    for x, y, dx, dy in ((inset, inset, 1, 1), (W - 1 - inset, inset, -1, 1),
                         (inset, H - 1 - inset, 1, -1),
                         (W - 1 - inset, H - 1 - inset, -1, -1)):
        d.line([(x, y + dy * tick), (x, y), (x + dx * tick, y)],
               fill=colour + (255,), width=6 * ss)
    return img.resize((w, h), Image.LANCZOS)


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


def random_label(size=RANDOM_LABEL, lit=False, face="original", canvas=None):
    """RANDOM as plain type, in the mode title's own face and size.

    The stop is marked by the word itself changing colour. Nothing is drawn
    behind or around it: a plate there reads as an unselected cell and a frame
    reads as a box, and the one thing this position must not look like is the
    white selection box that used to sit under the wall. Both copies are painted
    from the same glyphs at the same size, so the word cannot shift or change
    size when a player's pick moves onto it.
    """
    return display_word("RANDOM", tint=GREEN_LIT if lit else None, face=face,
                        canvas=canvas, align="centre")


def repaint_random_mark():
    """Paint the random slot at cell size and at side-panel size.

    Both are painted with a zero axis. The stock 151,0 carries its corner at
    (-22,-18), so drawing it in a cell put the card 22px right and 18px down of
    the slot it belongs to - the misplaced "?" - and the select layout has no
    per-cell offset to undo that with.
    """
    d, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    here = {(sp["group"], sp["number"]): sp for sp in sprites}
    gold = here.get(RANDOM_CELL)
    if gold is None:
        raise SystemExit("select screen: 151,0 is missing, so Karate's RANDOM "
                         "has no box to fit")
    box = (gold["w"], gold["h"])
    wanted = {RANDOM_CELL: random_label(),
              RANDOM_MARK: random_label(lit=True),
              RANDOM_PORTRAIT: random_card(RANDOM_PANEL),
              KARATE_RANDOM: random_label(face="karate", canvas=box),
              KARATE_RANDOM_MARK: random_label(lit=True, face="karate", canvas=box)}
    out, done = [], set()
    for sp in sprites:
        key = (sp["group"], sp["number"])
        if key in wanted:
            out.append({"group": key[0], "number": key[1],
                        "image": wanted[key], "axis": (0, 0)})
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
    # There are no empty cells: the wall is eight by six and the cast fills it,
    # so nothing is drawn for a cell without a fighter. The last row is the
    # RANDOM stop, and searchemptyboxesdown walks right along it, which is what
    # lets any column on the wall reach RANDOM by pressing down.
    ("showemptyboxes", "0"),
    ("moveoveremptyboxes", "0"),
    ("searchemptyboxesdown", "1"),
    ("searchemptyboxesup", "1"),
    ("cell.size", "%d,%d" % (CELL, CELL_H)),
    ("cell.spacing", str(GAP)),
    ("cell.bg.spr", "-1"),
    ("cell.bg.scale", "1,1"),
    ("cell.bg.offset", "0,0"),
    ("cell.random.spr", "151,0"),
    ("cell.random.scale", "1,1"),
    # RANDOM is a word, so it takes no plate and no box cursor: start.lua skips
    # both on that slot and draws its own bright RANDOM text. This used to declare
    # cell.random.active.{spr,scale,offset} for that copy, but the engine's cell
    # struct has no "active" field: it rejected all three on every launch
    # ("field 'active' not found as struct or map field") and drew nothing.
    ("portrait.spr", "9000,0"),
    # the portrait art is painted at the cell's own size (build_portraits.py
    # CELL) and the bust is inset inside it, so it sits at the cell's origin -
    # nudging it in again double-counted the inset and pushed the art 4px past
    # the frame on two sides
    ("portrait.offset", "0,0"),
    # The portrait art is painted at twice the cell (build_portraits.CELL_RES)
    # and drawn at half scale, so the roster is 1:1 on screen instead of a 56x70
    # sheet blown up 2x. Both the engine and this motif's Lua select
    # multiply the portrait scale by motif.localcoord / the character's
    # localcoord, so the doubling cancels for every fighter. build_portraits.CELL
    # carries the same cell size, so a re-bake keeps the two in step.
    ("portrait.scale", "0.5,0.5"),
    # The stage card's position, scale, window and name band all belong to
    # tools/build_select_ui.py, which runs after this one; stage.pos is
    # deliberately not set here, because the card hangs from the band now and
    # a pos written here would put the name somewhere else entirely.
    ("stage.font", "11, 0, 0, 236, 200, 120"),
    # The stage caption was the one word on the screen at 1.5x, so the arena name
    # read a size larger than VERSUS and the fighter names. Font 11 at 1 is the
    # same size as the rest of them.
    ("stage.scale", "1.5, 1.5"),
    ("stage.active.font", "11, 0, 0, 255, 228, 140"),
    # No arena thumbnail on the character wall. tools/build_select_ui.py owns
    # this card - its window, its plate, its caption - and switches it off for
    # this screen, so this line was the only thing still drawing it: a 520x170
    # picture with its plate parked off-screen, hanging over the bottom row of
    # portraits. The preview is 2x and centred on the VS screen, where the
    # engine actually shows it.
    ("stage.portrait.spr", "-1"),
    # VERSUS is drawn by the engine: same face as the stage caption (font 11),
    # on the top edge, so it matches PLAYER 1 / PLAYER 2 and the stage name.
    # The wall's frame starts at y=25. The title's face is the bitmap Body face,
    # a 7x20 cell, so at scale 1,1 it is 20px of row from y=2 - clear of the
    # frame instead of lying across it. The two PLAYER labels take this very
    # offset, scale and font (start.lua reads them from the motif), so the three
    # words are one size, one face and one row by construction.
    ("title.offset", "960, 0"),
    ("title.font", "11, 0, 0, 255, 228, 140"),
    ("title.scale", "1.5,1.5"),
    # The big side art is the uniform 9000,2 portrait, so the two columns match
    # each other no matter how tall the fighter is in play. Its axis is the
    # top-left corner, so the offset is where that corner goes: SIDE_INSET in
    # from the screen edge, FACE2_TOP down, which leaves FACE2_MARGIN of air
    # under the feet instead of standing them on the clipping line.
    ("p1.face.window", "0,0,1,1"),
    ("p1.face2.spr", "9000,2"),
    ("p1.face2.offset", "%d, %d" % (SIDE_INSET, FACE2_TOP)),
    # Painted at twice the panel size (build_portraits.SIDE_RES) and drawn
    # at half scale: the panel is 380x500 on screen either way, but the art
    # is no longer a 190x250 sheet stretched across it.
    ("p1.face2.scale", "0.5,0.5"),
    ("p1.face2.window", FACE2_WIN_P1),
    ("p2.face.window", "0,0,1,1"),
    ("p2.face2.spr", "9000,2"),
    ("p2.face2.offset", "%d, %d" % (1920 - SIDE_INSET, FACE2_TOP)),
    # Painted at twice the panel size (build_portraits.SIDE_RES) and drawn
    # at half scale: the panel is 380x500 on screen either way, but the art
    # is no longer a 190x250 sheet stretched across it.
    ("p2.face2.scale", "0.5,0.5"),
    ("p2.face2.window", FACE2_WIN_P2),
    # The fighter names under the panels are font 11 at scale 1 - the same face
    # and the same scale as VERSUS and the stage caption, so every word on the
    # screen is one size. They were at 0.25 on the belief that name text is
    # drawn in a quarter-size space; it is not, so the names came out a quarter
    # of the caption size and could not be read beside PLAYER 1 / PLAYER 2.
    ("p1.name.font", "11, 0, 0, 255, 228, 140"),
    ("p1.name.scale", "1.5, 1.5"),
    ("p1.name.offset", "75, 1035"),
    ("p1.name.layerno", "2"),
    ("p2.name.font", "11, 0, -1, 255, 170, 96"),
    ("p2.name.scale", "1.5, 1.5"),
    ("p2.name.offset", "1845, 1035"),
    ("p2.name.layerno", "2"),
    # The "?" and the loading art stand in for the portrait, so they are drawn
    # inside the same rect and clipped by the same window. Left at the stock
    # 5x scale and a 476px-wide window they spilled past the panel and showed
    # around the preview art. Offsets below compensate for each sprite's axis:
    # 151,0 sits at (-22,-18), 151,1 (mirrored) at (31,0), 1000,1 at (0,0).
    # RANDOM is a word, not a portrait: the stand-in question-mark card in the
    # side panel is switched off, and the label under the wall (that player's
    # name, drawn by start.lua) is what lights up when the cursor is on the stop.
    ("p1.face2.random.spr", "-1, 0"),
    # 151,10 is still the old 300x520 card, so it is scaled to the 214px panel
    # instead of drawing into the grid.
    ("p1.face2.random.offset", "%d, %d" % (SIDE_INSET, FACE2_TOP)),
    ("p1.face2.random.scale", "1, 1"),
    ("p1.face2.random.window", FACE2_WIN_P1),
    ("p1.face2.loading.offset", "%d, %d" % (SIDE_INSET, FACE2_TOP)),
    ("p1.face2.loading.scale", "0.3333, 0.3333"),
    ("p1.face2.loading.window", FACE2_WIN_P1),
    ("p2.face2.random.spr", "-1, 0"),
    # p2 draws its panel art mirrored (facing = -1), so the offset is the
    # panel's right edge and the card lands on 1066-1276.
    ("p2.face2.random.offset", "%d, %d" % (1920 - SIDE_INSET, FACE2_TOP)),
    ("p2.face2.random.scale", "1, 1"),
    ("p2.face2.random.window", FACE2_WIN_P2),
    ("p2.face2.loading.offset", "%d, %d" % (1920 - SIDE_INSET, FACE2_TOP)),
    ("p2.face2.loading.scale", "0.3333, 0.3333"),
    ("p2.face2.loading.window", FACE2_WIN_P2),
    # The random box's "?" carries the same odd axis; at 1.6x it ran 20px into
    # the cells beside it.
    # The engine draws this in the seventh row of the grid, which starts at
    # y=1012 and runs past the 1080 frame: the word could be seen but the
    # cursor frame drawn over it could not, so RANDOM was the one stop on the
    # screen with no selection mark. start.lua draws the label under the wall
    # instead (start.f_drawRandomStop), so the cell sprite is switched off here
    # rather than drawn twice.
    ("cell.random.spr", "-1"),
    ("cell.random.offset", "0,0"),
    ("cell.random.scale", "1, 1"),
    # The stock screen re-rolls the random portrait every 4 ticks and plays
    # pX.random.move.snd on every roll, which stacked voices into a continuous
    # machine-gun tone while the "?" was highlighted. Half a second per roll,
    # and the cancel flag so a new roll stops the previous sound.
    ("cell.random.switchtime", "48"),
    ("stage.portrait.bg.spr", "%d, %d" % BASE_SPR),
    ("random.move.snd.cancel", "1"),
    # The confirm portrait. start.lua confirms a pick through pCfg.face2.done
    # (start.lua:3663) and f_animGet indexes params.scale as a table, so a group
    # the screenpack never spells out leaves scale nil and the key that confirms
    # a fighter kills the engine at start.lua:755. Both done groups are written
    # out here with their parent group's scale and window, and no sprite of
    # their own, so the flash costs nothing and cannot crash.
    ("p1.face.done.spr", "-1, 0"),
    ("p1.face.done.offset", "420, 840"),
    ("p1.face.done.scale", "0.5, 0.5"),
    ("p1.face.done.facing", "1"),
    ("p1.face.done.window", "0,0,1,1"),
    ("p2.face.done.spr", "-1, 0"),
    ("p2.face.done.offset", "1500, 840"),
    ("p2.face.done.scale", "0.5, 0.5"),
    ("p2.face.done.facing", "-1"),
    ("p2.face.done.window", "0,0,1,1"),
    ("p1.face2.done.spr", "-1, 0"),
    ("p1.face2.done.offset", "%d, %d" % (SIDE_INSET, FACE2_TOP)),
    ("p1.face2.done.scale", "0.5,0.5"),
    ("p1.face2.done.facing", "1"),
    ("p1.face2.done.window", FACE2_WIN_P1),
    ("p2.face2.done.spr", "-1, 0"),
    ("p2.face2.done.offset", "%d, %d" % (1920 - SIDE_INSET, FACE2_TOP)),
    ("p2.face2.done.scale", "0.5,0.5"),
    ("p2.face2.done.facing", "-1"),
    ("p2.face2.done.window", FACE2_WIN_P2),
)
# The active cursor is the player's colour flashing white (one action each, see
# CURSOR_ACTIONS), and the done cursor is the solid colour. Both are 2x art.
CURSOR_SCALE = "%.2f,%.2f" % (1.0 / CURSOR_RES, 1.0 / CURSOR_RES)
for (action, colour, _white), i in zip(CURSOR_ACTIONS, range(1, len(CURSOR_ACTIONS) + 1)):
    KEYS += ((f"p{i}.cursor.active.anim", str(action)),
             (f"p{i}.cursor.active.spr", "%d,%d" % colour),
             (f"p{i}.cursor.active.scale", CURSOR_SCALE),
             (f"p{i}.cursor.active.offset", "0,0"),
             (f"p{i}.cursor.done.spr", "%d,%d" % colour),
             (f"p{i}.cursor.done.scale", CURSOR_SCALE),
             (f"p{i}.cursor.done.offset", "0,0"))

# Keys that belong to the wall-of-cells layout and would fight the grid.
# cell.*-N. keys belong to the old per-slot layout, and cell.random.active.* keys
# were never readable at all (the engine's cell struct has no "active" field), so
# both are removed rather than left in the block for the engine to reject.
DROP = re.compile(r"^\s*(cell\.\*-\d+\.|cell\.random\.active\.)",
                  re.IGNORECASE)
# Anim-based overrides that would draw the old cursor or the perspective face2
# art on top of the new layout. stage.portrait.spr is deliberately NOT here:
# it is the arena thumbnail, and disabling it left the preview box empty.
DISABLE = re.compile(
    r"^\s*(p[1-4]\.cursor\.(active|done)\.anim|"
    r"p[12]\.face2\.(projection|yangle|focallength))\s*=", re.IGNORECASE)


def patch_cursor_actions():
    """Write the cursor flash actions: player's colour, then white.

    The motif's own 160..174 actions play the stock cursor art (group 160), which
    this screen no longer uses, so the active cursor could only ever be one fixed
    colour. Two frames on the engine's animation clock give the flash without a
    Lua timer.
    """
    def block(action, colour, white):
        return ("[Begin Action %d] ;player cursor, colour flashing white\n"
                "%d,%d, 0,0, %d\n%d,%d, 0,0, %d\n"
                % (action, colour[0], colour[1], CURSOR_FLASH,
                   white[0], white[1], CURSOR_FLASH))

    with open(SYSTEM_DEF, encoding="utf-8", errors="replace") as f:
        text = f.read()
    for action, colour, white in CURSOR_ACTIONS:
        # the block, and the blank line after it, replaced whole
        pattern = re.compile(r"^\[Begin Action %d\][^\n]*\n(?:[^\[\n][^\n]*\n)*\n?"
                             % action, re.M)
        if not pattern.search(text):
            raise SystemExit("system.def has no [Begin Action %d] to replace" % action)
        text = pattern.sub(block(action, colour, white) + "\n", text, count=1)
    with open(SYSTEM_DEF + ".tmp", "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(SYSTEM_DEF + ".tmp", SYSTEM_DEF)
    return len(CURSOR_ACTIONS)


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
        "spriteno = %d, %d\n" % BASE_SPR +
        "start = -640, 0\n"
        "layerno = 0\n"
        "mask = 1\n"
    )


def patch_bg_layer():
    """Point the backdrop layer at the version without the character wall.

    The layer is rewritten in place: appending a second one left the old grid
    layer drawn on top, which is how the wall of cells followed the stage screen.
    """
    with open(SYSTEM_DEF, encoding="utf-8", errors="replace") as f:
        text = f.read()
    pattern = re.compile(r"(\[SelectBG Portrait Grid\]\n(?:[^\[\n][^\n]*\n)*?spriteno = )\d+, \d+")
    if pattern.search(text):
        text = pattern.sub(lambda m: m.group(1) + "%d, %d" % BASE_SPR, text, count=1)
        with open(SYSTEM_DEF + ".tmp", "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(SYSTEM_DEF + ".tmp", SYSTEM_DEF)
        return True
    if "spriteno = %d, %d" % BASE_SPR in text:
        return False
    marker = "\n[VS Screen]"
    if marker not in text:
        raise SystemExit("system.def has no [VS Screen]; cannot place the background")
    text = text.replace(marker, layer_block() + marker, 1)
    with open(SYSTEM_DEF + ".tmp", "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(SYSTEM_DEF + ".tmp", SYSTEM_DEF)
    return True


def gold_box(spr, sprites):
    """The size the gold word is painted at, which the second face has to fit."""
    for sp in sprites:
        if (sp["group"], sp["number"]) == spr:
            return (sp["w"], sp["h"])
    raise SystemExit("select screen: %d,%d is not in system.sff" % spr)


def main():
    if not os.path.isfile(SYSTEM_SFF) or not os.path.isfile(SYSTEM_DEF):
        raise SystemExit("data/ikemen1 is missing - fetch the engine data first")

    images = {BG_SPR: grid_overlay(), BASE_SPR: background(grid=False),
              CELL_SPR: cell_frame()}
    for spr, word in zip(LABEL_SPR, ("PLAYER 1", "PLAYER 2")):
        images[spr] = label_word(word)
    # The captions again in Karate, fitted to the box the gold ones already sit in.
    _d, _now, _p = sff.read_sff(SYSTEM_SFF)
    for gold, karate, word in zip(LABEL_SPR, KARATE_LABEL, LABEL_WORDS):
        images[karate] = label_word(word, face="karate",
                                    canvas=gold_box(gold, _now))
    for spr, colour in zip(CURSOR, PLAYER_COLOURS):
        images[spr] = cursor_frame(colour)
    for spr in CURSOR_WHITE:
        images[spr] = cursor_frame((255, 255, 255))
    for spr, colour in zip(STAGE_FRAME, PLAYER_COLOURS):
        images[spr] = stage_frame(colour)

    rewrite_system_sff(images)
    marks = repaint_random_mark()
    patch_select_info()
    actions = patch_cursor_actions()
    added = patch_bg_layer()

    # Read back: a screen nobody can see is worse than the old one.
    _d, sprites, _p = sff.read_sff(SYSTEM_SFF)
    have = {(sp["group"], sp["number"]): sp for sp in sprites}
    for key in images:
        if key not in have:
            raise SystemExit(f"select-screen sprite {key} did not make it into system.sff")
        sp = have[key]
        if sp["group"] in (BG_SPR[0], BASE_SPR[0]) and (sp["w"], sp["h"]) != SCREEN:
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
          f"{marks} random card(s) painted, {actions} cursor actions")


if __name__ == "__main__":
    main()
