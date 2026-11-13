"""Bake the stage-select hint into the character-select screen.

The screenpack can already show and change the stage before a match: [Select
Info] in system.def has the stage name block (``stage.pos``, ``stage.font``,
``stage.active.font``, ``stage.done.font``) and the portrait window
(``stage.portrait.spr = 9000,1``, ``stage.portrait.window = 521,567,759,665``),
and select.def's [ExtraStages] is the list it walks. What nothing on screen says
is that the stage can be changed - so this paints a hint strip into system.sff
(group 221, unused by the engine's own art) and adds it to [SelectBGdef] just
above the stage name.

The strip names no keys: which input moves the stage cursor is the engine's
select-screen input, not a motif parameter, so the hint shows the affordance
(arrows around the word) rather than a binding that could be wrong.

Run:  python3 tools/build_select_ui.py
"""

from __future__ import annotations

import os
import re
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import build_select_grid as select_grid
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYSTEM_SFF = os.path.join(ROOT, "data", "ikemen1", "system.sff")
SYSTEM_DEF = os.path.join(ROOT, "data", "ikemen1", "system.def")

# The hint sits above the card, centred on the screen: the stage name moved
# down to the fighters' row, and the strip used to be pinned to the left edge.
SPRITE = (221, 0)
STRIP = (450, 45)
POS = (430, 962)

GOLD = (255, 214, 96)
GOLD_DEEP = (120, 78, 16)
INK = (12, 10, 24)


def chevron(d, x, y, size, facing, fill):
    """A solid triangular arrow pointing left (-1) or right (+1)."""
    d.polygon([(x - facing * size, y - size), (x - facing * size, y + size),
               (x + facing * size, y)], fill=fill)


def hint_strip():
    """The painted affordance: dark plate, gold rule, arrows either side."""
    scale = 3
    w, h = STRIP[0] * scale, STRIP[1] * scale
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    plate = [scale * 2, scale * 2, w - scale * 2, h - scale * 2]
    d.rounded_rectangle(plate, radius=scale * 6, fill=INK + (190,),
                        outline=GOLD_DEEP + (255,), width=scale)
    d.rounded_rectangle([plate[0] + scale, plate[1] + scale,
                         plate[2] - scale, plate[3] - scale],
                        radius=scale * 5, outline=GOLD + (150,), width=max(1, scale // 2))

    text = "CHANGE STAGE"
    size = 0.9 * h
    font = art.font(int(round(size)))
    while font.getlength(text) > (w * 0.62) and size > 8:
        size -= 1
        font = art.font(int(round(size)))
    box = font.getbbox(text)
    tw, th = box[2] - box[0], box[3] - box[1]
    tx = (w - tw) // 2 - box[0]
    ty = (h - th) // 2 - box[1]
    # a dark pass under the type keeps it legible over the plate's own gradient
    d.text((tx, ty), text, font=font, fill=(0, 0, 0, 210),
           stroke_width=max(1, scale // 2), stroke_fill=(0, 0, 0, 210))
    d.text((tx, ty - scale // 2), text, font=font, fill=GOLD + (255,))

    mid = h // 2
    for facing in (-1, 1):
        base_x = scale * 12 if facing < 0 else w - scale * 12
        chevron(d, base_x, mid, scale * 5, facing, GOLD + (255,))
        chevron(d, base_x + facing * scale * 3, mid, scale * 3, facing,
                GOLD + (170,))

    img = img.filter(ImageFilter.GaussianBlur(0.5 * scale))
    return img.resize(STRIP, Image.LANCZOS)


def write_sprite(image, axis=(STRIP[0] // 2, STRIP[1] // 2)):
    _d, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    out, replaced = [], False
    for sp in sprites:
        if (sp["group"], sp["number"]) == SPRITE:
            out.append({"group": SPRITE[0], "number": SPRITE[1],
                        "image": image, "axis": axis})
            replaced = True
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"],
                        "link": sp["link"]})
    if not replaced:
        out.append({"group": SPRITE[0], "number": SPRITE[1], "image": image,
                    "axis": axis})

    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: built file has no SFF signature")
    with open(SYSTEM_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(SYSTEM_SFF + ".tmp", SYSTEM_SFF)
    return len(out)



# The stage card: the preview picture and nothing else. The stage name used to
# be drawn inside a band at the bottom of the plate, which read as the name
# sitting in the preview box; the name is drawn under the card now, on the same
# row as the fighters' names, so the box only ever holds the picture.
#
# Every stage bakes a 1215x398 establishing shot as sprite 9000,1 and both the
# select screen and the VS screen draw it. A stage's 9000,1 is drawn at
# (motif localcoord / stage localcoord) of the .def scale, which is 1280/1920 =
# 2/3 for these 1920-wide stages; at the card's own scale the picture would
# land 307px wide inside a 460px window, a postage stamp in a frame. Scaling by
# the reciprocal makes the art cover the window and the window clip it.
STAGE_ART = (1215, 398)
CARD_W = 520                  # the grid card's width, on the character wall
# The stage screens draw the preview at 2x the wall card: 520px on a 1920 frame
# read as a thumbnail on the screen whose whole job is showing the stage, so the
# stage screen and the VS screen now carry the same 1040x341 picture, centred on
# 960, with the name row underneath it.
VS_CARD_W = 1040
ART_H = int(round(CARD_W * STAGE_ART[1] / float(STAGE_ART[0])))   # 151
CARD_H = ART_H
CARD_CX = 960
NAME_ROW_Y = 1035                       # the row the fighter names sit on
CARD_CX = 960
# A stage's 9000,1 is drawn at (motif localcoord / stage localcoord) of the
# scale in the .def, which is 1280/1920 = 2/3 for these 1920-wide stages. At
# the card's own scale the picture landed 307px wide inside a 460px window - a
# postage stamp in a frame, which is what "the preview does not fill the box"
# looked like. Overscaling by that ratio makes the art cover the window and the
# window clip it, so the box is full whatever a stage's localcoord turns out
# to be.
MOTIF_LOCALCOORD = 1920
STAGE_LOCALCOORD = 1920
CARD_FILL = STAGE_LOCALCOORD / float(MOTIF_LOCALCOORD)
# 20px of cap height. The name used to be font 11 (the 13px Body face) at
# scale .5, i.e. six pixels tall: legible nowhere, least of all on a television.
# It is the Display face now at 20/34, which is what the rest of the screenpack
# draws its headings with, so the stage name reads at the same weight. The card
# is 60px wider for it, and its bottom edge moved down to 660 to keep the top
# clear of the portrait grid, which ends at y=460.
NAME_PX = 13
NAME_FONT = 11                           # Body, a 13px cell: the face the
                                         # engine sets VERSUS in


def _card(bottom_y, text_y=NAME_ROW_Y, portrait=True, card_w=CARD_W):
    """The stage card, and the point its name is drawn from.

    Everything the .def measures from ``stage.pos`` hangs off the name, and the
    name is under the card now, so every offset is computed from there: the art
    sits ``art_centre - text_y`` above the name, and the plate's own corner goes
    the same way. The window is inset inside the plate's 2px gold rule, or the
    picture paints over the frame and the card loses its outline.
    """
    if not portrait:
        # The character-select screen shows no stage card: that space belongs to
        # the portrait grid now, and the stage is chosen on a screen of its own
        # once both fighters are picked. The keys are still written, empty, so a
        # build over an older system.def cannot leave the old card on screen.
        return (
            ("stage.portrait.spr", "-1"),
            ("stage.portrait.window", "0, 0, 0, 0"),
            ("stage.portrait.bg.offset", "-4000, -4000"),
            ("stage.portrait.loading.anim", "-1"),
            ("stage.portrait.loading.offset", "-4000, -4000"),
            ("stage.pos", "%d, %d" % (CARD_CX, text_y)),
        )
    card_h = int(round(card_w * STAGE_ART[1] / float(STAGE_ART[0])))
    left = CARD_CX - card_w // 2
    top = bottom_y - card_h
    scale = card_w / float(STAGE_ART[0]) * CARD_FILL
    art_centre = top + card_h / 2.0
    window = "%d, %d, %d, %d" % (left + 3, top + 3, left + card_w - 3, bottom_y - 3)
    corner = "%d, %d" % (left - CARD_CX, top - text_y)
    # the plate behind the picture is drawn at its own size, so it has to grow
    # with the card or a wide card shows a small frame around a big photo
    plate_scale = card_w / float(CARD_W)
    return (
        ("stage.portrait.spr", "9000,1"),
        ("stage.portrait.offset", "0, %d" % int(round(art_centre - text_y))),
        ("stage.portrait.scale", "%.4f, %.4f" % (scale, scale)),
        ("stage.portrait.window", window),
        ("stage.portrait.bg.offset", corner),
        ("stage.portrait.bg.scale", "%.4f, %.4f" % (plate_scale, plate_scale)),
        # the "random" and "loading" placeholders are drawn over the same
        # picture area, so they take the plate's corner and its clip
        # the loading anim draws a scrolling grid over the picture while the
        # preview loads; over a card this size it read as a stray tile in the
        # corner, so the plate is what shows instead
        ("stage.portrait.loading.anim", "-1"),
        ("stage.portrait.loading.offset", corner),
        ("stage.portrait.loading.scale", "1, 1"),
        ("stage.portrait.loading.window", window),
        ("stage.pos", "%d, %d" % (CARD_CX, text_y)),
    )


# The name is under the card now, on the fighters' row, so it is the same 13px
# cell as their names - font 11 at 1:1, which is the face and size the engine
# sets VERSUS and the fighter names in.
#
# The engine cycles the stage name through three states while the stage menu is
# open: stage, active and active2, swapping every ``stage.active.switchtime``
# frames. The stock motif sets that to 2 and gives all three a different gold,
# which is a 30Hz strobe. One colour and a switchtime longer than anyone will
# sit on this screen makes the name hold still.
# 43.2 units - the menu's own line - on the 40px cell of the face above, so a run
# of this tool on its own already puts the stage name where tools/build_fonts.py
# will leave it. It was 1.5, which is 60 units on that cell: another copy of the
# size the menu stopped using, and 1.39x the name when this tool ran alone.
NAME_SCALE = "1.08, 1.08"
NAME_GOLD = "236, 200, 120"
SELECT_TEXT = (
    ("stage.font", f"{NAME_FONT}, 0, 0, {NAME_GOLD}"),
    ("stage.active.font", f"{NAME_FONT}, 0, 0, {NAME_GOLD}"),
    ("stage.active2.font", f"{NAME_FONT}, 0, 0, {NAME_GOLD}"),
    ("stage.done.font", f"{NAME_FONT}, 0, 0, {NAME_GOLD}"),
    ("stage.text", "%s"),
    ("stage.active.text", "%s"),
    ("stage.scale", NAME_SCALE),
    ("stage.active.switchtime", "300000"),
    # Stage select. f_stageMenu reads motif.select_info.stage.previous.key and its
    # three siblings (next, skip.previous, skip.next) straight off this section,
    # and the motif declared none of them - so opening the stage screen indexed
    # nil with 'key' and the engine closed the game with an error box. These are
    # the stock defaults, in the motif's own key names.
    ("stage.randomselect", "1"),
    ("stage.previous.key", "U"),
    ("stage.next.key", "D"),
    ("stage.skip.previous.key", "L"),
    ("stage.skip.next.key", "R"),
)


# The card hangs from its bottom edge, which is where both screens had it
# before, so nothing else on either screen moves.
# The stage screen's card is the VS card's size, sitting dead centre of the frame
# (341 tall, so 711 at the bottom puts its centre on 540) instead of hanging from
# the name row: the screen carries one picture, and it belongs in the middle of
# it with the name underneath.
STAGE_PORTRAIT = _card(711, portrait=True, card_w=VS_CARD_W)   # [Select Info]: the stage screen
def _stage_backdrop():
    """The screen the stage card sits on: the select grid's own background.

    The stage screen used to clear to black and put a small card in the middle
    of it, which read as a screen that had failed to draw. The grid background
    is the picture the character wall already sits on, so the same sprite is
    drawn behind the card, over the whole frame, anchored on the stage name row
    the way every other stage key is (stage.pos = 960, 1035).
    """
    frame = (1920, 1080)          # the motif's localcoord
    grid_spr = (220, 0)           # [SelectBG Portrait Grid]
    _d, sprites, _p = sff.read_sff(SYSTEM_SFF)
    grid = next((sp for sp in sprites
                 if (sp["group"], sp["number"]) == grid_spr), None)
    if grid is None:
        raise SystemExit("system.sff has no grid background %d,%d" % grid_spr)
    return (
        ("stage.portrait.bg.anim", "-1"),
        ("stage.portrait.bg.spr", "%d,%d" % grid_spr),
        ("stage.portrait.bg.offset", "%d, %d" % (-frame[0] // 2, -NAME_ROW_Y)),
        ("stage.portrait.bg.scale", "%.4f, %.4f" % (
            frame[0] / float(grid["w"]), frame[1] / float(grid["h"]))),
    )


SELECT_PLATE = STAGE_PORTRAIT + _stage_backdrop() + (
    # the select screen draws the plate as [Begin Action 110]; pin it to its
    # first sprite so the anim's own offsets cannot shift the plate
) + SELECT_TEXT
# The VS screen is the one screen the stage preview is actually for. 520px on a
# 1920 frame read as a thumbnail, and 900 was still short of "twice as big";
# 1040 is exactly 2x the card the character wall used to carry, and gives a
# 1040x341 picture centred on 960 whose top edge (657) clears the VS mark and
# whose bottom (998) leaves the caption row at 1035 to the names.
VS_PLATE = _card(998, card_w=VS_CARD_W) + (
    ("stage.portrait.bg.spr", "112,0"),
)

# Text on the VS screen. The two names were within a few units of each other,
# so both sides looked like the same orange: P1 is the motif's bright cream and
# P2 a warmer amber. The stage name is under the card here as well.
VS_TEXT = (
    # the VS portraits are baked at 2x and drawn at half the scale
    # The VS portraits are painted 360x420 (build_portraits BIG) and the engine
    # multiplies a portrait's scale by motif.localcoord / char.localcoord, so at
    # scale 1 each fighter stands 360x420 on screen. 0.25 - the stock value,
    # meant for the engine's own 120x140 art - drew a 90x105 stamp in the corner:
    # the biggest screen in the game with the smallest fighters on it. 1.5 puts
    # them at 540x630, filling most of the 838px portrait window.
    ("p1.scale", "1.5, 1.5"),
    ("p2.scale", "1.5, 1.5"),
    # The portrait's axis is its top-left corner, so the offset is where the
    # art's corner goes. The stock 666,810 was written for art anchored at its
    # feet; with a corner anchor it hung the fighter off the bottom of the
    # screen, and at the new width it also ran under the VS logo. 180 + 630
    # lands the feet on 810 (the stock foot line) and 268 + 540 stops 0.5px
    # inside the p1 window at 808.5.
    ("p1.offset", "268, 180"),
    ("p2.offset", "1652, 180"),
    # The fighter names belong on the caption row under the card, where the
    # stage name already is. At y=615 they sat across the middle of the screen,
    # which is the VS logo's own row, so the right-hand name printed on the
    # logo's foot. One row, three captions: P1 left, the stage centred, P2 right.
    ("p1.name.offset", f"20, {NAME_ROW_Y}"),
    ("p2.name.offset", f"1900, {NAME_ROW_Y}"),
    ("p1.name.font", "10, 0, 1, 255, 228, 140"),
    ("p2.name.font", "10, 0, -1, 255, 170, 96"),
    # The motif ships "p1.anim = 0", which asks each character for action 0 - the
    # fighting stance. That is anchored at the fighter's own axis, so at the 1.5
    # portrait scale the body was drawn upward out of the top of the frame and
    # the screen came up with two names, the card and no fighters.
    #
    # Action 9000 is the portrait entrance now: every character carries it
    # (tools/add_vs_portrait_anim.py) and it plays the 9000,1 picture, whose
    # 0,0 axis is what the offsets and windows above are measured from. The done
    # variants point at it too, or finishing order selection would swap the
    # fighting stance back in on top of it. spr stays as the fallback for a
    # character added later that has the art but not the action.
    ("p1.anim", "9000"),
    ("p1.spr", "9000, 1"),
    ("p2.anim", "9000"),
    ("p2.spr", "9000, 1"),
    ("p1.done.anim", "9000"),
    ("p2.done.anim", "9000"),
    # the VS screen's "Match %i" caption: same gold as every other caption
    ("match.font", f"{NAME_FONT}, 0, 0, " + NAME_GOLD),
    ("stage.font", f"{NAME_FONT}, 0, 0, {NAME_GOLD}"),
    ("stage.text", "%s"),
    ("stage.scale", NAME_SCALE),
)


# [VS Screen] is not only drawn with these tables: start.lua:4427 hands the
# player table to start.f_animGet as `params` (and, once the selection order is
# confirmed, hands over `pX.done` instead), then hands the same player table over
# again as the velocity source. The stock motif carries every field that
# function indexes; this section was generated with just the drawing keys, so
# the first VS portrait indexed a nil - which is the engine error VS MODE hit
# (start.lua:755, the animSetScale/animSetTrans pair). These are the stock
# values, so nothing about the picture changes.
VS_MOTION = tuple(
    (f"{p}.{key}", value)
    for p in ("p1", "p2")
    for key, value in (
        ("velocity", "0, 0"), ("maxdist", "0, 0"), ("accel", "0, 0"),
        ("friction", "1, 1"), ("xshear", "0"), ("angle", "0"),
        ("xangle", "0"), ("yangle", "0"),
        ("projection", "orthographic"), ("focallength", "2048"),
        ("layerno", "0"),
    )
)

# Each side also has a second portrait group, `face2`. Stock ships both of its
# groups switched off with every field present; this section had neither, so the
# line right after the first portrait - `pCfg.face2.done.anim` - would have been
# the next nil index. anim -1 with spr -1,0 means "no picture", which is what a
# one-portrait VS screen wants.
VS_FACE2 = tuple(
    (f"{grp}.{key}", value)
    for p in ("p1", "p2")
    for grp in (f"{p}.face2", f"{p}.face2.done")
    for key, value in (
        ("anim", "-1"), ("spr", "-1, 0"), ("offset", "0, 0"), ("facing", "1"),
        ("scale", "1.0, 1.0"), ("xshear", "0"), ("angle", "0"),
        ("xangle", "0"), ("yangle", "0"), ("projection", "orthographic"),
        ("focallength", "2048"), ("layerno", "0"),
        ("window", "0, 0, 1, 1"), ("applypal", "0"),
        # No velocity/maxdist/accel/friction here. The engine rejects all four on a
        # face2 group ("field 'velocity' not found as struct or map field") and
        # discards them, so declaring them only ever added warning lines to the
        # launch console; start.lua reads the velocity source through pair(), which
        # covers the nil.
    )
)


def vs_done_pairs(text):
    """`pX.done` mirrors `pX`, field for field.

    start.lua loads the done group as `params` and the main group as the
    velocity source, so the two have to describe the same picture in the same
    place. Only `anim` was written before, which is why the done group alone had
    no scale to read.
    """
    pairs = [("p1.done.anim", "9000"), ("p2.done.anim", "9000"),
             ("p1.done.applypal", "0"), ("p2.done.applypal", "0")]
    for p in ("p1", "p2"):
        for key in ("spr", "offset", "facing", "scale", "window"):
            found = re.search(
                rf"(?mi)^[ \t]*{p}\.{key}[ \t]*=[ \t]*([^;\r\n]*?)[ \t]*(?:;.*)?$", text)
            if found and found.group(1).strip():
                pairs.append((f"{p}.done.{key}", found.group(1).strip()))
        for key, value in (("xshear", "0"), ("angle", "0"), ("xangle", "0"),
                           ("yangle", "0"), ("projection", "orthographic"),
                           ("focallength", "2048"), ("layerno", "0")):
            pairs.append((f"{p}.done.{key}", value))
    return pairs


def _apply_section(text, section, pairs):
    """Set keys inside one [section] block only."""
    start = text.find(section)
    if start < 0:
        return text, []
    nxt = re.compile(r"^\[", re.M).search(text, start + len(section))
    end = nxt.start() if nxt else len(text)
    head, body, tail = text[:start], text[start:end], text[end:]
    changed = []
    for key, value in pairs:
        pat = re.compile(rf"^;?[ \t]*{re.escape(key)}[ \t]*=[^\r\n]*$", re.M)
        if pat.search(body):
            # every occurrence, not just the first: a duplicate line further
            # down the same section would win at load time, which is how the
            # card ended up drawn at one scale inside another's window
            new = pat.sub(f"{key} = {value}", body)
            # ...and collapse the duplicates the old appending left behind, so
            # the section carries one line per key
            seen = [m.start() for m in pat.finditer(new)]
            for at in reversed(seen[:-1]):
                line_end = new.find("\n", at)
                new = new[:at] + new[line_end + 1:]
        else:
            new = body.rstrip("\r\n") + f"\n{key} = {value}\n"
        if new != body:
            changed.append(f"{section} {key}")
        body = new
    return head + body + tail, changed


def layout(text):
    """Switch the stage preview on in both screens that draw it."""
    changed = []
    for section, extra in (("[Select Info]", SELECT_PLATE),
                           ("[VS Screen]", VS_PLATE + VS_TEXT)):
        text, done = _apply_section(text, section, extra)
        changed += done
    # The VS portrait groups carry every field start.f_animGet indexes, not only
    # the ones that decide how the picture looks: see VS_MOTION and VS_FACE2.
    # vs_done_pairs reads the main group's values, so it runs after VS_TEXT.
    text, done = _apply_section(
        text, "[VS Screen]", VS_MOTION + tuple(vs_done_pairs(text)) + VS_FACE2)
    changed += done
    return text, changed

def layer_block():
    return (
        "\n;------------------------------------\n"
        "; Stage-select hint, painted by tools/build_select_ui.py\n"
        "[SelectBG Stage Hint]\n"
        "type = normal\n"
        f"spriteno = {SPRITE[0]}, {SPRITE[1]}\n"
        f"start = {POS[0]}, {POS[1]}\n"
        "layerno = 2\n"
        "mask = 1\n"
    )


# The stock plates behind the stage preview are grey panels with a large
# question mark printed on them: group 110 (select), 112 (VS) and 111/113 (the
# random and loading slots). The picture is drawn over the plate, so every
# pixel of the preview art that is transparent shows the question mark through
# it - which is why the VS card looked framed by one. Only group 110 was
# repainted, so the VS screen still had the "?" around its preview. All four
# groups are repainted now: each slot reads as an empty gold picture frame
# until a preview is drawn in it.
FRAME_GROUPS = (110, 111, 112, 113)


def frame_plate(w, h, band=0):
    """A dark plate with the same gold rule as the rest of the screenpack.

    ``band`` paints the name band across the top of the plate: a darker strip
    with a gold rule under it. The stage art is clipped below that band, and
    the engine's stage text is drawn in it, so the name always has a dark
    backing no matter how bright the stage behind the card is.
    """
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], fill=(16, 13, 20, 205),
                outline=GOLD_DEEP + (255,), width=2)
    d.rectangle([2, 2, w - 3, h - 3], outline=GOLD + (140,), width=1)
    if band:
        # the band is under the art: a darker strip at the bottom of the plate
        # with a gold rule above it, so the name never sits over the picture
        band_top = h - 3 - band
        d.rectangle([2, band_top, w - 3, h - 3], fill=(9, 7, 12, 240))
        d.line([(3, band_top - 2), (w - 4, band_top - 2)],
               fill=GOLD_DEEP + (255,), width=2)
        d.line([(3, band_top - 1), (w - 4, band_top - 1)],
               fill=GOLD + (150,), width=1)
    return img


# The two plates the card itself is drawn on. They are repainted at the card's
# own size, so the card's .def scale is 1 and its offsets are screen pixels;
# the other frame sprites keep whatever size the engine shipped them at.
CARD_PLATES = ((110, 0), (112, 0))
# 111 is the random slot: the grey question-mark card, at the picture's size.
RANDOM_PLATES = ((111, 0),)


STAGE_PREVIEW_SFFS = (os.path.join(ROOT, "stages", "stage0.sff"),)


def _cover(img, size):
    """Scale to fill `size` without distortion, then centre-crop."""
    tw, th = size
    ratio = max(tw / img.width, th / img.height)
    new = (max(tw, int(round(img.width * ratio))),
           max(th, int(round(img.height * ratio))))
    img = img.resize(new, Image.LANCZOS)
    left, top = (img.width - tw) // 2, (img.height - th) // 2
    return img.crop((left, top, left + tw, top + th))


def normalise_stage_previews():
    """Rebake any stage preview that is not the size the card expects.

    The card draws a stage's 9000,1 at the motif's scale, and the engine also
    scales it by (motif localcoord / stage localcoord): two thirds for the
    1920-wide stages here, four for the engine's 320x240 training room. The HD
    stages all bake the same 1215x398 shot, so they land identically whatever
    that ratio turns out to be. The training room shipped a 240x100 arcade
    crop, which is why its picture was a small tile in a corner of the box
    instead of filling it - rebaked at the size the others use, it fills the
    window the same way and the window clips it.
    """
    fixed = 0
    for path in STAGE_PREVIEW_SFFS:
        if not os.path.isfile(path):
            continue
        raw, sprites, palettes = sff.read_sff(path)
        out, changed = [], False
        for sp in sprites:
            if (sp["group"], sp["number"]) == (9000, 1) and (sp["w"], sp["h"]) != STAGE_ART:
                img = _cover(sff.decode_sprite(raw, sp, palettes), STAGE_ART)
                out.append({"group": 9000, "number": 1, "image": img,
                            "axis": (STAGE_ART[0] // 2, STAGE_ART[1] // 2)})
                changed = True
                continue
            out.append(sp)
        if not changed:
            continue
        blob = sff.write_sff(out, [p["rgba"] for p in palettes])
        if blob[:12] != sff.SIG:
            raise SystemExit("refusing to write: rebuilt stage sff has no signature")
        with open(path + ".tmp", "wb") as f:
            f.write(blob)
        os.replace(path + ".tmp", path)
        fixed += 1
    return fixed


def clean_frames():
    """Repaint the stage-preview frame without its question mark."""
    _d, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    out, replaced = [], 0
    for sp in sprites:
        if sp["group"] in FRAME_GROUPS:
            if (sp["group"], sp["number"]) in CARD_PLATES:
                img = frame_plate(CARD_W, CARD_H)
                axis = (0, 0)
            elif (sp["group"], sp["number"]) in RANDOM_PLATES:
                # the stand-in the roster grid uses, at the card's own size -
                # repainting it as an empty frame left the random stage with
                # nothing in the box at all
                img = select_grid.random_card((CARD_W - 6, CARD_H - 6))
                axis = (0, 0)
            else:
                img = frame_plate(sp["w"], sp["h"])
                axis = sp["axis"]
            out.append({"group": sp["group"], "number": sp["number"],
                        "image": img, "axis": axis})
            replaced += 1
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"],
                        "link": sp["link"]})
    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: built file has no SFF signature")
    with open(SYSTEM_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(SYSTEM_SFF + ".tmp", SYSTEM_SFF)
    return replaced


# The VS screen's logo and "NEXT MATCH" banner are the engine's own silver
# chrome art (groups 200 and 202), which reads as a different game beside the
# gold-and-red wordmark used everywhere else. A .def cannot tint a sprite, so
# the colour is baked instead: each sprite's luminance is pushed through the
# logo's own ramp, which keeps its shading and hard outline, and the alpha is
# left alone. Pixels that are already coloured are kept as they are, so a
# second build does not shift the art again.
RAMP = ((0.00, (255, 246, 206)), (0.30, (255, 204, 96)),
        (0.62, (238, 122, 44)), (1.00, (146, 24, 30)))
VS_ART_GROUPS = (200, 202)


def _ramp_colour(t):
    for i in range(len(RAMP) - 1):
        t0, c0 = RAMP[i]
        t1, c1 = RAMP[i + 1]
        if t0 <= t <= t1:
            k = (t - t0) / max(1e-6, t1 - t0)
            return tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(3))
    return RAMP[-1][1]


def _is_warm(img):
    """True when the art already carries this ramp, so a rebuild is a no-op.

    Without it every build would multiply the shading in again and the logo
    would creep darker each time data/ was rebuilt.
    """
    stat = ImageStat.Stat(img.convert("RGB"), img.getchannel("A"))
    r, _g, b = stat.mean
    return (r - b) > 45 and r > 90


def goldify(img):
    """Repaint a silver sprite as the wordmark's gold, shaded down to red.

    The colour comes from a vertical gradient over the sprite rather than from
    its own luminance. The engine's VS art is chrome with a hard light/dark
    split down the middle; ramping *that* printed a band straight across the
    logo. Here the gradient runs cream -> gold -> red from top to bottom, the
    source's shading only multiplies it, and the near-black outline is kept
    exactly as it was so the silhouette still reads against the sky.
    """
    img = img.convert("RGBA")
    w, h = img.size
    if _is_warm(img):
        return img
    strip = Image.new("RGB", (1, max(1, h)))
    put = strip.load()
    for y in range(max(1, h)):
        put[0, y] = _ramp_colour(y / float(max(1, h - 1)))
    body = strip.resize((w, h)).convert("RGB")
    lum = img.convert("L")
    # Blur the source shading before it multiplies the gradient. The chrome art
    # has one hard light/dark split down its middle, and multiplying that
    # unblurred printed a seam across the logo; softened, it only models the
    # face, and the gradient carries the colour.
    smooth = lum.filter(ImageFilter.GaussianBlur(max(2, h // 22)))
    shade = smooth.point(lambda v: 96 + int(v * 0.66))
    body = ImageChops.multiply(body, Image.merge("RGB", (shade, shade, shade)))
    outline = lum.point(lambda v: 255 if v < 44 else 0)
    out = Image.composite(img.convert("RGB"), body, outline).convert("RGBA")
    out.putalpha(img.getchannel("A"))
    return out


def retint_vs_art():
    """Bake the game's colours into the engine's silver VS-screen art."""
    raw, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    out, done = [], 0
    for sp in sprites:
        if sp["group"] in VS_ART_GROUPS:
            img = sff.decode_sprite(raw, sp, palettes)
            out.append({"group": sp["group"], "number": sp["number"],
                        "image": goldify(img), "axis": sp["axis"]})
            done += 1
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"],
                        "link": sp["link"]})
    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: retinted system.sff has no signature")
    with open(SYSTEM_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(SYSTEM_SFF + ".tmp", SYSTEM_SFF)
    return done


# The VS screen's sky. [VersusBG Background Sky] in system.def points at sprite
# 204,0, which the engine ships at 1280x960 - sized for a 1280x720 motif - while
# these layers draw 1:1 in this motif's 1920x1080 localcoord, so the
# "scale = 1.5" written on them does nothing. The backdrop therefore covered
# only the left two thirds of the frame and stopped 120px above the bottom, and
# bgclearcolor showed through: black down the right-hand side and across the
# bottom, right where the menu and the stage card sit.
VS_SKY = (204, 0)
# [VersusBG Background Clouds Bottom] is the layer that reaches the floor of the
# screen, and it is 960 tall - the same 1280x720-era size the sky was. It stops
# 120px short of the bottom, so the last strip of the frame was bare dark sky
# with a hard line across it. It is baked to the frame's height here (tiled
# horizontally by the layer itself, so the width is left alone).
VS_CLOUD_BOTTOM = (102, 3)
FRAME = (1920, 1080)


def full_frame(img):
    """Cover the frame with the sky, keeping its top edge where it was."""
    if tuple(img.size) == FRAME:
        return img.convert("RGBA")
    k = max(FRAME[0] / float(img.width), FRAME[1] / float(img.height))
    wide = img.resize((max(FRAME[0], int(round(img.width * k))),
                       max(FRAME[1], int(round(img.height * k)))),
                      Image.LANCZOS)
    return wide.convert("RGBA").crop((0, 0, FRAME[0], FRAME[1]))


def paint_vs_backdrop():
    """Bake the sky at frame size so no layer has to be rescaled or moved."""
    raw, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    out, grew = [], False
    for sp in sprites:
        if (sp["group"], sp["number"]) == VS_SKY:
            img = full_frame(sff.decode_sprite(raw, sp, palettes))
            grew = (sp["w"], sp["h"]) != FRAME
            out.append({"group": VS_SKY[0], "number": VS_SKY[1], "image": img,
                        "axis": sp["axis"]})
        elif (sp["group"], sp["number"]) == VS_CLOUD_BOTTOM:
            img = sff.decode_sprite(raw, sp, palettes)
            if img.height != FRAME[1]:
                # a 12.5% vertical stretch: the layer is soft cloud, and it puts
                # the last row of it on the last row of the frame
                img = img.resize((img.width, FRAME[1]), Image.LANCZOS)
            out.append({"group": VS_CLOUD_BOTTOM[0],
                        "number": VS_CLOUD_BOTTOM[1], "image": img,
                        "axis": sp["axis"]})
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"],
                        "link": sp["link"]})
    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: rebuilt system.sff has no signature")
    with open(SYSTEM_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(SYSTEM_SFF + ".tmp", SYSTEM_SFF)
    return grew


def strip_dead_scale():
    """Drop the "scale = 1.5" lines from the [VersusBG] layers.

    They were meant to blow the 1280x720-era backdrop up to this motif's frame
    and the engine never applied them - the layers draw 1:1. With the sky baked
    at frame size they only misread as a statement about how the art is sized.
    Idempotent: a def without them is left untouched.
    """
    with open(SYSTEM_DEF, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    out, section, dropped = [], "", 0
    for line in lines:
        s = line.strip().lower()
        if s.startswith("["):
            section = s
        elif section.startswith("[versusbg") \
                and s.replace(" ", "").startswith("scale=1.5,1.5"):
            dropped += 1
            continue
        out.append(line)
    if not dropped:
        return 0
    with open(SYSTEM_DEF + ".tmp", "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    os.replace(SYSTEM_DEF + ".tmp", SYSTEM_DEF)
    return dropped


def patch_def():
    """Fix the stage preview, then add the hint layer to [SelectBGdef] once.

    The layout pass runs on every build: it used to sit behind the "hint not
    added yet" check below, so after the first run the stage preview was never
    switched back on when data/ was reset from the engine copy.
    """
    with open(SYSTEM_DEF, encoding="utf-8", errors="replace") as f:
        text = f.read()
    text, changed = layout(text)
    print("  system.def layout: " + (", ".join(changed) or "already set"))
    added = False
    if f"spriteno = {SPRITE[0]}, {SPRITE[1]}" not in text:
        marker = "\n[VS Screen]"
        if marker not in text:
            raise SystemExit("system.def has no [VS Screen]; cannot place the hint")
        text = text.replace(marker, layer_block() + marker, 1)
        added = True
    with open(SYSTEM_DEF + ".tmp", "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(SYSTEM_DEF + ".tmp", SYSTEM_DEF)
    return added


# The VS screen and the main menu draw each other's backdrop: the VS layers here
# point at the title set (100,0 sky with the 100,2 and 100,3 clouds) and
# tools/build_title.py points the title layers at the VS set, so the two screens
# have swapped backgrounds. Only the sprite numbers change - each layer keeps its
# own seat, window, tile, velocity and trans, and every sprite involved is baked
# at the frame's size, so nothing has to be reseated or rescaled.
BACKDROP_SWAP = (("versusbg background sky", 100, 0),
                 ("versusbg background clouds top", 100, 2),
                 ("versusbg background clouds bottom", 100, 3))


def swap_backdrop_layers():
    """Point the VS backdrop layers at the main menu's art."""
    path = os.path.join(ROOT, "data", "ikemen1", "system.def")
    if not os.path.isfile(path):
        return 0
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    wanted = {name: (group, number) for name, group, number in BACKDROP_SWAP}
    out, section, changed = [], "", 0
    for line in lines:
        s = line.strip().lower()
        if s.startswith("["):
            section = s.strip("[]").strip()
        elif s.startswith("spriteno") and section in wanted:
            group, number = wanted[section]
            line = "spriteno = " + str(group) + "," + str(number)
            changed += 1
        out.append(line)
    if changed:
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
        os.replace(path + ".tmp", path)
    return changed


def build():
    if not os.path.isfile(SYSTEM_SFF) or not os.path.isfile(SYSTEM_DEF):
        raise SystemExit("data/ikemen1 is missing - fetch the engine data first")

    strip = hint_strip()
    total = write_sprite(strip)
    frames = clean_frames()
    centred = normalise_stage_previews()
    tinted = retint_vs_art()
    grew = paint_vs_backdrop()
    dropped = strip_dead_scale()
    added = patch_def()

    # Read back: the hint is worth nothing if the layer points at nothing.
    _d, sprites, _p = sff.read_sff(SYSTEM_SFF)
    have = {(sp["group"], sp["number"]) for sp in sprites}
    if SPRITE not in have:
        raise SystemExit(f"hint sprite {SPRITE} did not make it into system.sff")
    with open(SYSTEM_DEF, encoding="utf-8", errors="replace") as f:
        text = f.read()
    if f"spriteno = {SPRITE[0]}, {SPRITE[1]}" not in text:
        raise SystemExit("system.def does not reference the hint sprite")
    sky = next((sp for sp in sprites if (sp["group"], sp["number"]) == VS_SKY), None)
    if sky is None or (sky["w"], sky["h"]) != FRAME:
        raise SystemExit("the VS backdrop is not %dx%d" % FRAME)
    cloud = next((sp for sp in sprites
                  if (sp["group"], sp["number"]) == VS_CLOUD_BOTTOM), None)
    if cloud is None or cloud["h"] != FRAME[1]:
        raise SystemExit("the bottom cloud layer does not reach the frame's floor")

    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    strip.save(os.path.join(ROOT, "artifacts", "select_hint.png"))
    swap_backdrop_layers()
    print(f"stage-select hint: sprite {SPRITE[0]},{SPRITE[1]} "
          f"({'added' if total else 'kept'}), frame repaints {frames}, "
          f"stage previews centred {centred}, "
          f"VS art retinted {tinted}, "
          f"VS backdrop {FRAME[0]}x{FRAME[1]} "
          f"({'painted' if grew else 'already frame size'}), "
          f"{dropped} dead scale line(s) dropped, "
          f"SelectBG layer {'added' if added else 'already present'}")


if __name__ == "__main__":
    build()
