"""Make the menus wear the title logo's face and palette.

The wordmark is painted by tools/build_title.py with art.font(), i.e. DejaVu Sans
Bold, gold on maroon. The screenpack's own menu fonts are bitmap faces in
blue/pink/grey, so nothing else in the game looked like the logo.

Three things happen here, all of them regenerated rather than hand-edited,
because build-assets.yml copies the engine's data/ over ours on every run and
anything typed into data/ikemen1/system.def by hand is lost:

1. The logo's TrueType face is copied to data/ikemen1/fonts/Display.ttf.
2. Display.sff/.def (34px menus and names) and Body.sff/.def (13px bottom bar)
   are baked from it with the wordmark's own treatment: a maroon extrusion down
   and right, a gold gradient face, and a cream lip along the top edge. Ikemen
   draws TrueType glyphs in one flat colour - src/font.go has no shadow or
   outline for them - so a 3D menu face has to be art, which is why these are
   bitmap fonts.
3. Every menu/select/scoreboard font spec in system.def is repointed at those
   two fonts.
4. Options > Video > Resolution gains 1440p and 4K entries. Ikemen builds that
   submenu from the motif's menu.itemname.menuvideo.resolution.<W>x<H> keys and
   the stock list stops at 1920x1080, so a 4K display had nothing to pick.

Run:  python3 tools/build_fonts.py
"""

from __future__ import annotations

import glob
import os
import re
import shutil
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sff  # noqa: E402  (local helper import after sys.path)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "data", "ikemen1", "fonts")
MOTIF = os.path.join(ROOT, "data", "ikemen1", "system.def")
# The stock faces, kept as the width reference the rebake measures against.
FONT_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "font_src")

# The palette taken from the wordmark: the gold the letters are gilded with, its
# highlight, the shade at their foot, and the maroon they sit on (lifted a little
# so it stays readable as text).
GOLD = "240, 196, 88"
BRIGHT = "255, 228, 140"
DEEP = "176, 126, 44"
RED = "214, 58, 48"
# Warmer than the gold, for player 2 and other secondary labels, so the two
# sides stay distinguishable without a second loud colour.
AMBER = "236, 158, 74"

D = "10"   # Display.def
DA = "12"  # DisplayActive.def
B = "11"   # Body.def

# Where the logo's face lives on a normal Linux box, best first. The matplotlib
# wheel ships the same DejaVu build, which covers machines with no system fonts.
TTF_NAMES = ("DejaVuSans-Bold.ttf",)
TTF_DIRS = (
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/TTF",
    "/usr/share/fonts/dejavu",
    "/usr/local/share/fonts",
)

# key -> new value. Every occurrence is rewritten, because the same key appears
# in several menu blocks (title, pause, options, exit, replay) and they should
# all match.
REWRITES = (
    # title screen menu
    ("menu.item.font", f"{D},0,-1, {GOLD}"),
    ("menu.item.active.font", f"{DA},0,-1, {BRIGHT}"),
    ("menu.item.selected.font", f"{D},0,1, {BRIGHT}"),
    ("menu.item.selected.active.font", f"{DA},0,1, {BRIGHT}"),
    ("menu.item.value.font", f"{B},0,-1, {DEEP}"),
    ("menu.item.value.active.font", f"{B},0,-1, {BRIGHT}"),
    ("menu.item.value.conflict.font", f"{B},0,-1, {RED}"),
    ("menu.item.info.font", f"{B},0,-1, {GOLD}"),
    ("menu.item.info.active.font", f"{B},0,-1, {BRIGHT}"),
    ("title.font", f"{D},0,0, {BRIGHT}"),
    ("loading.font", f"{B}, 0, -1, {DEEP}, 255, -1"),
    # the engine's own bottom bar ("I.K.E.M.E.N. GO" + version) is switched off:
    # the fields are parked below the 1280x720 screen and the motif's overlay
    # strip is left transparent, so no bar is drawn in any menu.
    ("footer.title.font", f"{B}, 0, 1, {GOLD}, 255, -1"),
    ("footer.info.font", f"{B}, 0, 0, {GOLD}, 255, -1"),
    ("footer.version.font", f"{B}, 0, -1, {DEEP}, 255, -1"),
    ("footer.title.scale", "1,1"),
    ("footer.info.scale", "1,1"),
    ("footer.version.scale", "1,1"),
    ("footer.title.offset", "5, 5000"),
    ("footer.info.offset", "640, 5000"),
    ("footer.version.offset", "1275, 5000"),
    # infobox, game over text, story text
    ("text.font", f"{B}, 0, 1, {GOLD}"),
    # select screen
    ("p1.name.font", f"{D}, 0, 1, {GOLD}"),
    ("p2.name.font", f"{D}, 0, -1, {AMBER}"),
    ("stage.font", f"{B}, 0, 0, {DEEP}"),
    ("stage.active.font", f"{B}, 0, 0, {BRIGHT}"),
    ("stage.active2.font", f"{B}, 0, 0, {DEEP}"),
    ("stage.done.font", f"{B}, 0, 0, {DEEP}"),
    ("record.font", f"{B}, 0, 0, {DEEP}"),
    ("p1.teammenu.selftitle.font", f"{B}, 0, 0, {BRIGHT}"),
    ("p1.teammenu.enemytitle.font", f"{B}, 0, 0, {BRIGHT}"),
    ("p1.teammenu.item.font", f"{B}, 0, 1, {GOLD}"),
    ("p1.teammenu.item.active.font", f"{B}, 0, 1, {BRIGHT}"),
    ("p1.teammenu.item.active2.font", f"{B}, 0, 1, {DEEP}"),
    ("p2.teammenu.selftitle.font", f"{B}, 0, 0, {GOLD}"),
    ("p2.teammenu.enemytitle.font", f"{B}, 0, 0, {GOLD}"),
    ("p2.teammenu.item.font", f"{B}, 0, -1, {GOLD}"),
    ("p2.teammenu.item.active.font", f"{B}, 1, -1, {AMBER}"),
    ("p2.teammenu.item.active2.font", f"{B}, 1, -1, {GOLD}"),
    ("p1.palmenu.text.font", f"{B}, 0, 1, {GOLD}"),
    ("p2.palmenu.text.font", f"{B}, 0, -1, {AMBER}"),
    ("p1.palmenu.number.font", f"{B}, 0, 0, {GOLD}"),
    ("p2.palmenu.number.font", f"{B}, 0, 0, {AMBER}"),
    # continue / yes / no
    ("continue.font", f"{B}, 0, 0, {GOLD}"),
    ("yes.font", f"{B}, 0, 0, {DEEP}"),
    ("yes.active.font", f"{B}, 0, 0, {BRIGHT}"),
    ("no.font", f"{B}, 0, 0, {DEEP}"),
    ("no.active.font", f"{B}, 0, 0, {BRIGHT}"),
    # win / game over
    ("wintext.font", f"{D}, 0, 0, {BRIGHT}"),
    ("winquote.font", f"{B}, 0, 1, {GOLD}"),
    ("credits.font", f"{B}, 0, 1, {DEEP}"),
    ("start.insert.font", f"{D}, 0, 0, {BRIGHT}"),
    ("start.press.font", f"{D}, 0, 0, {BRIGHT}"),
    ("start.timer.font", f"{D}, 0, -1, {GOLD}"),
    # scoreboard
    ("item.rank.font", f"{B}, 0, -1, {DEEP}"),
    ("item.rank.active.font", f"{B}, 0, -1, {GOLD}"),
    ("item.rank.active2.font", f"{B}, 0, -1, {BRIGHT}"),
    ("item.result.font", f"{B}, 0, -1, {DEEP}"),
    ("item.result.active.font", f"{B}, 0, -1, {GOLD}"),
    ("item.result.active2.font", f"{B}, 0, -1, {BRIGHT}"),
    ("item.name.font", f"{B}, 0, 1, {GOLD}"),
    ("item.name.active.font", f"{B}, 0, 1, {BRIGHT}"),
    ("item.name.active2.font", f"{B}, 0, 1, {DEEP}"),
    # key config, movelist, menu chrome
    ("keymenu.p1.playerno.font", f"{B}, 0, 0, {GOLD}"),
    ("keymenu.p2.playerno.font", f"{B}, 0, 0, {AMBER}"),
    ("movelist.title.font", f"{D}, 0, 0, {BRIGHT}"),
    ("movelist.text.font", f"{B}, 0, 1, {GOLD}"),
    # TrueType faces are drawn in a single flat colour - src/font.go has no
    # gradient or outline for them - so the last white/grey text (netplay
    # "connecting", the text input line, the debug overlay) is moved onto the
    # bitmap gradient face as well.
    ("font5", "ikemen1/fonts/Body.def"),
    ("font6", "ikemen1/fonts/Body.def"),
    ("font7", "ikemen1/fonts/Body.def"),
    ("menu.boxcursor.col", BRIGHT),
    ("menu.boxbg.col", "40, 10, 14"),
)

# Layout numbers that only make sense on one screen. REWRITES above is global
# (the same key lives in several menu blocks), but position and line pitch are
# per-screen: the title menu carries nine items where the stock motif was laid
# out for six, so at the stock 54px pitch the last two land at y=708 and 762 and
# fall outside the 40..690 item window; and the pause list has to fit inside its
# own highlight box, which starts at menu.pos.x and runs 462px to the right.
# The bitmap face is 45px tall, so a pitch under 45 overlaps the rows.
# Every "[* Pause Menu]" section is a separate motif block, and the engine tops
# derived ones up from its own default motif instead of from our [Pause Menu].
# Anything not written here renders with the stock layout, so they all share it.
PAUSE_LAYOUT = (
    ("menu.pos", "460, 140"),
    ("menu.item.spacing", "0, 50"),
    ("menu.window.visibleitems", "10"),
    # The cursor band is drawn from menu.pos + coords[2] while the item text is
    # drawn from menu.pos, so the stock -30 floated it 30px above every row and
    # it flashed over the item above. 0..44 covers the 45px glyph cell.
    ("menu.boxcursor.coords", "-15, 0, 462, 44"),
    # Left-aligned so the items sit inside the box, which is drawn from
    # menu.pos.x rightwards. The stock block right-aligned every item except
    # the selected one, which is why the list read as ragged.
    ("menu.item.font", f"{D},0,1, {GOLD}"),
    ("menu.item.active.font", f"{DA},0,1, {BRIGHT}"),
    ("menu.item.selected.font", f"{D},0,1, {BRIGHT}"),
    ("menu.item.selected.active.font", f"{DA},0,1, {BRIGHT}"),
)

SECTION_LAYOUT = {
    "Title Info": (
        ("menu.pos", "1240, 250"),
        ("menu.item.spacing", "0, 46"),
        ("menu.window.visibleitems", "10"),
    ),
    "Option Info": (
        # Thirteen rows at the stock 42px pitch overlapped by 3px under the 45px
        # bitmap face; 46 is the smallest pitch that separates them and still
        # ends the last row at y=696, inside the 21..718 item window.
        ("menu.item.spacing", "0, 46"),
        # Alignment -1 is RIGHT in this engine (the default motif's left-hand
        # title menu uses 1, and our own [Title Info] sits at x=1240 with -1),
        # so the stock x=414 made every row end at 414 and grow leftwards. The
        # shipped Display face sets "RETURN WITHOUT SAVING" 492px wide, which
        # put its first pixel at -78: off the left edge of a 1280-wide screen.
        # 784 leaves 292px of margin for that worst case, and the values start
        # 30px later and end at 987 with the longest one measured (173px).
        ("menu.pos", "784, 99"),
        ("menu.item.font", f"{D},0,-1, {GOLD}"),
        ("menu.item.active.font", f"{DA},0,-1, {BRIGHT}"),
        # The highlighted row used to switch to 1 (left), so it jumped to the
        # right and overlapped the value column. Same alignment as the rest now.
        ("menu.item.selected.font", f"{D},0,-1, {BRIGHT}"),
        ("menu.item.selected.active.font", f"{DA},0,-1, {BRIGHT}"),
        # Values get a column of their own. They inherited the label's -1
        # (RIGHT) alignment, so each value ended at menu.pos.x + 30 = 814 while
        # its label ended at 784: the value was printed across the last third
        # of the label, which is what made Video Settings unreadable (every
        # row read "RendererOpenGL 3.3"). Left-aligned (1) at +40 starts the
        # column at 824, past the end of every label, and the longest value in
        # the video menu ends before 1080.
        #
        # The face was Body (a 13px cell) beside 45px labels, so "OpenGL 3.3"
        # and "1920x1080" were a third of the height of the word they belonged
        # to and could not be read across a room. Display is the menu's own
        # face, so a row now reads as one line of text. The column starts at
        # 824 and runs to the 1280 edge, which at 34px is room for 22 glyphs -
        # every value in this menu is 16 or fewer.
        ("menu.item.value.font", f"{D},0,1, {DEEP}"),
        ("menu.item.value.active.font", f"{DA},0,1, {BRIGHT}"),
        ("menu.item.value.conflict.font", f"{D},0,1, {RED}"),
        ("menu.item.info.font", f"{D},0,1, {GOLD}"),
        ("menu.item.info.active.font", f"{DA},0,1, {BRIGHT}"),
        # The key config rows inherit menu.item.value.font above, and they sit
        # on a 36px pitch with their values 303px in from the label - a 34px
        # face there would stack on the row below. They keep Body.
        ("keymenu.item.value.font", f"{B},0,1, {GOLD}"),
        ("keymenu.item.value.active.font", f"{B},1,1, {BRIGHT}"),
        ("keymenu.item.value.conflict.font", f"{B},0,1, {RED}"),
        ("menu.item.value.offset", "40, 0"),
        ("menu.item.value.active.offset", "40, 0"),
        ("menu.item.value.conflict.offset", "40, 0"),
        ("menu.item.info.offset", "40, 0"),
        ("menu.item.info.active.offset", "40, 0"),
        # The band spans both columns now: 272 to 1064, instead of stopping at
        # 999 with the values past its right edge.
        ("menu.boxcursor.coords", "-512, 0, 280, 44"),
    ),
    "Replay Info": (
        # 42px rows, so the band matches the pitch exactly.
        ("menu.boxcursor.coords", "-15, 0, 462, 41"),
    ),
    "Pause Menu": PAUSE_LAYOUT,
    "Training Pause Menu": PAUSE_LAYOUT,
}

# The wordmark's own layers, from tools/build_title.py.
FACE = [(0.00, (255, 250, 208)), (0.34, (255, 233, 142)),
        (0.68, (255, 197, 60)), (1.00, (236, 139, 24))]
EXTRUDE = [(0.00, (152, 33, 45)), (0.55, (122, 20, 32)), (1.00, (82, 10, 20))]
LIP = (255, 248, 230)
# The selected item: the same gold lifted toward white, as the logo's highlight
# band. Bitmap glyphs are truecolor, so a font spec's R,G,B cannot tint them -
# the active look has to be baked as well.
FACE_ACTIVE = [(0.00, (255, 255, 240)), (0.34, (255, 246, 190)),
               (0.68, (255, 214, 110)), (1.00, (250, 166, 52))]

FONTS = (("Display", 34, 3, FACE), ("DisplayActive", 34, 3, FACE_ACTIVE),
         ("Body", 13, 2, FACE))

# The screenpack's remaining bitmap faces. They are stock MUGEN fonts - white or
# grey glyphs in eight palette banks - and they are what still showed through in
# the scoreboard names, the round timer, the hit and combo counters, the win
# quotes, the match number on the VS screen, the credits and the debug font.
# They are rebaked from the same typeface with the wordmark's gradient, and
# their .def files are left exactly as they are, so every Size/Spacing/Offset
# the motif was laid out against still holds.
#                 name          cell height, i.e. its .def Size.y   extrusion
STOCK_FONTS = (("Menu1",           42, 3),
               ("Menu2",           38, 3),
               ("Menu2Small",      20, 2),
               ("Pixel",           18, 2),
               ("PixelFlat",       14, 2),
               ("Timer",           49, 3),
               ("HitNum",          38, 3),
               ("PowerbarNum",     30, 2),
               ("ComboCounter",    60, 3),
               ("Round",          180, 6),
               ("Action",          16, 1))


def _gradient(size, stops):
    """Vertical gradient over a whole cell, so the face shades like the logo."""
    w, h = size
    stops = sorted(stops)
    col = Image.new("RGBA", (1, h))
    pix = col.load()
    for y in range(h):
        t = y / max(1, h - 1)
        c = stops[-1][1]
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                k = (t - t0) / max(1e-6, t1 - t0)
                c = tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(3))
                break
        pix[0, y] = c + (255,)
    return col.resize((w, h), Image.NEAREST)


def _shift(mask, dx, dy):
    out = Image.new("L", mask.size, 0)
    out.paste(mask, (dx, dy))
    return out


def glyph(ch, font, cell_h, depth, face_stops=FACE, base=None, cell_w=None):
    """One glyph: maroon extrusion, gold face, cream lip along the top edge.

    ``cell_w`` pins the sprite to the width the stock face gave that character.
    Ikemen advances by the sprite's own width, not by the .def's Size
    (src/font.go: CharWidth returns fci.w), so a narrower sprite silently
    shortens every string the motif was laid out against.
    """
    ascent, _descent = font.getmetrics()
    if base is None:
        base = ascent
    adv = max(1, int(round(font.getlength(ch))))
    ink = Image.new("L", (adv + 1, cell_h), 0)
    ImageDraw.Draw(ink).text((0, base), ch, font=font, fill=255, anchor="ls")
    if cell_w:
        w = max(2, int(cell_w))
        room = max(1, w - depth)
        # only squeeze when the glyph genuinely would not fit the stock cell
        if ink.width > room:
            ink = ink.resize((room, cell_h), Image.LANCZOS)
        mask = Image.new("L", (w, cell_h), 0)
        mask.paste(ink, (0, 0))
    else:
        w = adv + depth + 1
        mask = Image.new("L", (w, cell_h), 0)
        mask.paste(ink, (0, 0))

    solid = mask
    for i in range(1, depth + 1):
        solid = ImageChops.lighter(solid, _shift(mask, i, i))

    out = Image.new("RGBA", (w, cell_h), (0, 0, 0, 0))
    block = _gradient((w, cell_h), EXTRUDE)
    block.putalpha(solid)
    out.alpha_composite(block)

    face = _gradient((w, cell_h), face_stops)
    face.putalpha(mask)
    out.alpha_composite(face)

    lip = Image.new("RGBA", (w, cell_h), LIP + (255,))
    lip.putalpha(ImageChops.subtract(mask, _shift(mask, 0, 1)))
    out.alpha_composite(lip)
    return out


def write_font(name, px, depth, ttf, face_stops=FACE):
    """Bake Display/Body into bitmap fonts and write their .def."""
    font = ImageFont.truetype(ttf, px)
    ascent, descent = font.getmetrics()
    cell_h = ascent + descent + depth + 1
    space_w = max(2, int(round(font.getlength(" "))) + depth)

    sprites = []
    for code in range(33, 127):
        sprites.append({"group": 0, "number": code, "axis": (0, 0),
                        "image": glyph(chr(code), font, cell_h, depth, face_stops)})
    # the engine takes the space advance from Size, not from a glyph
    with open(os.path.join(FONT_DIR, name + ".sff"), "wb") as fh:
        fh.write(sff.write_sff(sprites))

    body = (f'[FNT v2]\n; FNT v2 version number.  Don\'t change this.\n'
            f'fntversion = 2,00\n; Name of this font.\nname = "{name}"\n\n'
            f'[Def]\n; Bitmap glyphs: the gold face and maroon extrusion are in the art,\n'
            f'; so the engine draws the wordmark look instead of a flat colour.\n'
            f'Type = bitmap\nBankType = palette\n'
            f'; width is the space advance, height is the cell height\n'
            f'Size = {space_w},{cell_h}\nSpacing = 0,0\n; the engine shifts glyphs by offset.y - Size.y + 1, and the TrueType\n; defs this replaces had no Size at all, so this cancels the shift and\n; puts the top of each glyph on the y the menu asks for\nOffset = 0,{cell_h - 1}\n'
            f'File = {name}.sff\n')
    path = os.path.join(FONT_DIR, name + ".def")
    if not os.path.isfile(path) or open(path, encoding="utf-8-sig").read() != body:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
    print(f"  baked {name}: {len(sprites)} glyphs, {px}px face, "
          f"{depth}px extrusion, cell {space_w}x{cell_h}")
    return len(sprites)


def stock_cells(name):
    """Per-character sprite width from the unmodified face.

    Kept in tools/font_src/ because the shipped .sff files are the ones these
    replace. The engine's advance is the glyph sprite's width, so reproducing
    these numbers is what keeps every string exactly as wide as the menues were
    drawn for - the scoreboard columns, the credits, the continue countdown and
    the key config all measure text to place it.
    """
    path = os.path.join(FONT_SRC, name + ".sff")
    if not os.path.isfile(path):
        return {}
    _n, sprites, _p = sff.read_sff(path)
    return {chr(sp["number"]): sp["w"] for sp in sprites
            if sp["group"] == 0 and 33 <= sp["number"] <= 126}


def write_stock(name, cell_h, depth, ttf):
    """Rebake a stock bitmap face in the gradient, leaving its .def alone.

    A stock .def carries Offset = 0,0 and the engine draws each glyph at
    y - Size.y + 1, so the cell height has to stay exactly Size.y or every row
    of the scoreboard shifts; and because the engine advances by the sprite
    width, each cell also keeps the stock width. Action.def is an RGBA font
    whose banks are sprite groups, so all six of its banks get written.
    """
    px = max(6, int(round(cell_h * 0.74)))
    font = ImageFont.truetype(ttf, px)
    ascent, _descent = font.getmetrics()
    base = min(cell_h - depth - 1, ascent)
    banks = (0, 1, 2, 3, 4, 5) if name == "Action" else (0,)
    cells = stock_cells(name)
    sprites = []
    for bank in banks:
        for code in range(33, 127):
            sprites.append({"group": bank, "number": code, "axis": (0, 0),
                            "image": glyph(chr(code), font, cell_h, depth,
                                           base=base,
                                           cell_w=cells.get(chr(code)))})
    with open(os.path.join(FONT_DIR, name + ".sff"), "wb") as fh:
        fh.write(sff.write_sff(sprites))
    print(f"  rebaked {name}: {len(sprites)} glyphs, {cell_h}px cell")
    return len(sprites)


NOTICE = """The Display.ttf face shipped here is {name}, the same one
tools/build_title.py uses to paint the title wordmark, so the menus and the logo
are the same typeface.

DejaVu fonts are distributed under a free licence derived from the Bitstream Vera
font licence; the full text is at https://dejavu-fonts.github.io/License.html

Copyright (c) 2003 by Bitstream, Inc. All Rights Reserved. Bitstream Vera is a
trademark of Bitstream, Inc. DejaVu changes are in the public domain.
"""


def find_ttf():
    """Return (path, filename) for the logo's face, or (None, None)."""
    for name in TTF_NAMES:
        for folder in TTF_DIRS:
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                return path, name
    # matplotlib bundles the same family, which covers lean images.
    try:
        import matplotlib  # noqa: F401  (imported for its data path)

        folder = os.path.join(os.path.dirname(matplotlib.__file__),
                              "mpl-data", "fonts", "ttf")
        for name in TTF_NAMES:
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                return path, name
    except Exception:
        pass
    for name in TTF_NAMES:
        hits = glob.glob(os.path.join("/usr", "**", name), recursive=True)
        if hits:
            return hits[0], name
    # Last resort: the copy this generator already vendored. It is the same
    # face, so rebuilding on a box with no DejaVu installed is a no-op instead
    # of a hard failure.
    vendored = os.path.join(FONT_DIR, "Display.ttf")
    if os.path.isfile(vendored):
        return vendored, TTF_NAMES[0]
    return None, None


def install_ttf():
    src, name = find_ttf()
    if src is None:
        print("no DejaVuSans-Bold.ttf found: install fonts-dejavu-core, or drop it in "
              "data/ikemen1/fonts/Display.ttf yourself", file=sys.stderr)
        return False
    os.makedirs(FONT_DIR, exist_ok=True)
    dst = os.path.join(FONT_DIR, "Display.ttf")
    if not (os.path.isfile(dst) and os.path.getsize(dst) == os.path.getsize(src)
            and open(dst, "rb").read() == open(src, "rb").read()):
        shutil.copyfile(src, dst)
        print(f"  vendored {name} from {src}")
    else:
        print(f"  {os.path.relpath(dst, ROOT)} already current")
    for name, px, depth, face_stops in FONTS:
        write_font(name, px, depth, dst, face_stops)
    for name, cell_h, depth in STOCK_FONTS:
        write_stock(name, cell_h, depth, dst)
    with open(os.path.join(FONT_DIR, "Display-NOTICE.txt"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(NOTICE.format(name=name))
    return True


def set_key(text, key, value):
    """Replace the value of `key = ...`, keeping its trailing comment."""
    if not re.search(r"^[ \t]*" + re.escape(key) + r"[ \t]*=", text, re.MULTILINE | re.I):
        return text, 0
    pattern = re.compile(
        r"^(?P<pre>[ \t]*" + re.escape(key) + r"[ \t]*=[ \t]*)(?P<val>[^;\r\n]*?)"
        r"[ \t]*(?P<comment>;.*)?$",
        re.MULTILINE | re.IGNORECASE,
    )

    def repl(match):
        comment = match.group("comment")
        return match.group("pre") + value + (f" {comment}" if comment else "")

    return pattern.subn(repl, text)


def add_section_key(text, section, key, value):
    """Insert `key = value` at the top of [section] when the key is absent.

    Derived menu sections such as [Training Pause Menu] ship empty, and the
    engine fills them from its own default motif rather than from our
    [Pause Menu], so their keys have to be written out explicitly.
    """
    head = re.compile(r"^[ \t]*\[" + re.escape(section) + r"\][ \t]*$",
                      re.MULTILINE | re.IGNORECASE).search(text)
    if not head:
        return text, 0
    start = head.end()
    nxt = re.compile(r"^[ \t]*\[[^\]]*\]", re.MULTILINE).search(text, start)
    end = nxt.start() if nxt else len(text)
    if re.search(r"^[ \t]*" + re.escape(key) + r"[ \t]*=", text[start:end],
                 re.MULTILINE | re.IGNORECASE):
        return text, 0
    nl = "\r\n" if "\r\n" in text else "\n"
    return text[:start] + nl + f"{key} = {value}" + text[start:], 1


def set_section_key(text, section, key, value):
    """set_key, but only inside one [section] block."""
    head = re.compile(r"^[ \t]*\[" + re.escape(section) + r"\][ \t]*$",
                      re.MULTILINE | re.IGNORECASE).search(text)
    if not head:
        return text, 0
    start = head.end()
    nxt = re.compile(r"^[ \t]*\[[^\]]*\]", re.MULTILINE).search(text, start)
    end = nxt.start() if nxt else len(text)
    body, count = set_key(text[start:end], key, value)
    return text[:start] + body + text[end:], count


def ensure_font_files(text):
    """Register Display, Body and DisplayActive as font10, font11, font12."""
    wanted = (("Display", 10), ("Body", 11), ("DisplayActive", 12))
    missing = [f"font{handle} = ikemen1/fonts/{name}.def"
               for name, handle in wanted
               if not re.search(r"^\s*font%d\s*=" % handle, text,
                                re.MULTILINE | re.IGNORECASE)]
    if not missing:
        return text, 0
    nl = "\r\n" if "\r\n" in text else "\n"
    last = None
    for last in re.finditer(r"^\s*font[0-9]+\s*=.*$", text,
                            re.MULTILINE | re.IGNORECASE):
        pass
    if last is None:
        return text, 0
    added = "".join(nl + line for line in missing)
    return text[:last.end()] + added + text[last.end():], len(missing)


# The one ordered copy of the size ladder. Both tables that can drive
# Options > Video > Resolution are written from it: RESOLUTION_MENU for the
# motif, and ensure_widescreen_resolutions() for data/system.base.def.
RESOLUTION_LADDER = (
    ("1280x720", "(720p)"),
    ("1366x768", "(768p)"),
    ("1600x900", "(900p)"),
    ("1920x1080", "(1080p)"),
    ("2560x1440", "(2K)"),
    ("3840x2160", "(4K)"),
    ("5120x2880", "(5K)"),
    ("6016x3384", "(6K)"),
    ("7168x4032", "(7K)"),
    ("7680x4320", "(8K)"),
    ("7680x2160", "(2x 4K)"),
    ("11520x2160", "(3x 4K)"),
)

RESOLUTION_MENU = (
    """; Options > Video > Resolution. The engine takes the size straight from the
suffix, so this block IS the list.
;
; This is the WINDOW size, not the render size. Ikemen's render resolution is
; Video.GameWidth/GameHeight in config.ini and it has no option-menu item at
; all, so nothing in this list can add detail to the art - picking 4K here
; draws the same sprites, scaled up, into a 4K window. The labels say so
; rather than implying the picture gets sharper.
;
; The art in this game is painted at 1920x1080 (localcoord), so 1920x1080 is
; the one window where every sprite lands on whole pixels; 2560x1440 and
; 3840x2160 are clean 1.33x and 2x scales of that same art.
"""
    "menu.itemname.menuvideo.resolution = RESOLUTION\n"
    "menu.itemname.menuvideo.resolution.1280x720 = 1280x720   (720p)\n"
    "menu.itemname.menuvideo.resolution.1366x768 = 1366x768   (768p)\n"
    "menu.itemname.menuvideo.resolution.1600x900 = 1600x900   (900p)\n"
    "menu.itemname.menuvideo.resolution.1920x1080 = 1920x1080   (1080p)\n"
    "menu.itemname.menuvideo.resolution.2560x1440 = 2560x1440   (2K)\n"
    "menu.itemname.menuvideo.resolution.3840x2160 = 3840x2160   (4K)\n"
    "menu.itemname.menuvideo.resolution.5120x2880 = 5120x2880   (5K)\n"
    "menu.itemname.menuvideo.resolution.6016x3384 = 6016x3384   (6K)\n"
    "menu.itemname.menuvideo.resolution.7168x4032 = 7168x4032   (7K)\n"
    "menu.itemname.menuvideo.resolution.7680x4320 = 7680x4320   (8K)\n"
    "menu.itemname.menuvideo.resolution.7680x2160 = 7680x2160   (2x 4K)\n"
    "menu.itemname.menuvideo.resolution.11520x2160 = 11520x2160   (3x 4K)\n"
    "menu.itemname.menuvideo.resolution.back = BACK\n"
)

# Video.GameWidth/GameHeight is the engine's RENDER size; the window it is drawn
# in is Video.WindowWidth/WindowHeight, and the stock menu exposes only the
# first. Both are offered here so a 4K render can sit in a 1080p window (or a
# 3-monitor window can hold a 1080p render).
#
# The item names carry a trailing "w": the engine keys each submenu row's
# handler by the bare last segment of the itemname, so "3840x2160" would
# overwrite the resolution row's handler. The labels still show the real size.
WINDOW_MENU = (
    "menu.itemname.menuvideo.window = WINDOW SIZE\n"
    "menu.itemname.menuvideo.window.windowauto = Match Render Size\n"
    "menu.itemname.menuvideo.window.1280x720w = 1280x720   (720p)\n"
    "menu.itemname.menuvideo.window.1366x768w = 1366x768   (768p)\n"
    "menu.itemname.menuvideo.window.1600x900w = 1600x900   (900p)\n"
    "menu.itemname.menuvideo.window.1920x1080w = 1920x1080   (1080p)\n"
    "menu.itemname.menuvideo.window.2560x1440w = 2560x1440   (2K)\n"
    "menu.itemname.menuvideo.window.3840x2160w = 3840x2160   (4K)\n"
    "menu.itemname.menuvideo.window.5120x2880w = 5120x2880   (5K)\n"
    "menu.itemname.menuvideo.window.6016x3384w = 6016x3384   (6K)\n"
    "menu.itemname.menuvideo.window.7168x4032w = 7168x4032   (7K)\n"
    "menu.itemname.menuvideo.window.7680x4320w = 7680x4320   (8K)\n"
    "menu.itemname.menuvideo.window.7680x2160w = 7680x2160   (2x 4K)\n"
    "menu.itemname.menuvideo.window.11520x2160w = 11520x2160   (3x 4K)\n"
    "menu.itemname.menuvideo.window.back = BACK\n"
)

RESOLUTION_ANCHOR = re.compile(r"^menu\.itemname\.options\s*=.*$", re.MULTILINE)

# The engine's base text table still offers three 4:3 sizes next to our 16:9
# ones. KeepAspect is on by default, so picking one pillarboxes the whole game
# between black bars - and every stage, menu and character in this build is 16:9
# end to end, so those entries can only break the picture.
BASE_DEF = os.path.join(ROOT, "data", "system.base.def")
FOUR_THREE = ("menu.itemname.menuvideo.resolution.320x240",
              "menu.itemname.menuvideo.resolution.640x480",
              "menu.itemname.menuvideo.resolution.960x720")


def ensure_widescreen_resolutions():
    """Fix the engine's base text table for 16:9 displays.

    The engine builds the Options > Video > Resolution submenu out of the
    ``menu.itemname.menuvideo.resolution.*`` keys it finds, and this table is
    what it ships with. Two things were wrong for a widescreen build: the 4:3
    sizes it lists (320x240, 640x480, 960x720) pillarbox the game behind black
    bars, and the list stopped at 1920x1080, so a 1440p or 4K display had
    nothing to pick - naming them in the motif alone was not enough.
    """
    if not os.path.isfile(BASE_DEF):
        return 0
    with open(BASE_DEF, "r", encoding="utf-8", errors="surrogateescape",
              newline="") as fh:
        text = fh.read()
    changed = 0
    for key in FOUR_THREE:
        pattern = re.compile(r"^([ \t]*)(" + re.escape(key) + r")([ \t]*=.*)$",
                             re.MULTILINE)
        text, n = pattern.subn(
            lambda m: f"{m.group(1)};{m.group(2)}{m.group(3)}  ; 4:3 pillarboxes",
            text)
        changed += n

    # The submenu is whatever keys exist, in file order, so the ladder is
    # rewritten as one block on every run: a row per size, ascending, labelled
    # from RESOLUTION_LADDER. Inserting only the sizes that were missing parked
    # each new one wherever its anchor happened to be - the list came out 720p,
    # 768p, 900p, 1080p, 5K, 6K, 7K, 8K, 2K, 4K, ordered by the history of the
    # edits rather than by size.
    size_row = re.compile(
        r"^[ \t]*menu\.itemname\.menuvideo\.resolution\.\d+x\d+[ \t]*=[^\r\n]*\r?\n",
        re.MULTILINE)
    rows = size_row.findall(text)
    if rows:
        indent = re.match(r"[ \t]*", rows[0]).group(0)
        nl = "\r\n" if rows[0].endswith("\r\n") else "\n"
        known = {size for size, _label in RESOLUTION_LADDER}
        extra = "".join(row for row in rows
                        if re.search(r"resolution\.(\d+x\d+)", row).group(1)
                        not in known)
        block = "".join(
            "%smenu.itemname.menuvideo.resolution.%s = %s   %s%s"
            % (indent, size, size, label, nl)
            for size, label in RESOLUTION_LADDER) + extra
        start = size_row.search(text).start()
        stripped = size_row.sub("", text)
        candidate = stripped[:start] + block + stripped[start:]
        if candidate != text:
            text = candidate
            changed += 1

    # Same short labels here as in the motif, so the submenu reads the same
    # whichever table the engine resolves last: the size, then its everyday
    # name. A list of "(16:9 QHD window, 1.33x)" was accurate and unreadable.
    for size, label in (("1280x720", "(720p)"), ("1366x768", "(768p)"),
                        ("1600x900", "(900p)"), ("1920x1080", "(1080p)"),
                        ("2560x1440", "(2K)"), ("3840x2160", "(4K)"),
                        ("5120x2880", "(5K)"), ("6016x3384", "(6K)"),
                        ("7168x4032", "(7K)"), ("7680x4320", "(8K)"),
                        ("7680x2160", "(2x 4K)"),
                        ("11520x2160", "(3x 4K)")):
        pattern = re.compile(
            r"^([ \t]*)menu\.itemname\.menuvideo\.resolution\." + re.escape(size)
            + r"[ \t]*=[ \t]*" + re.escape(size) + r"([ \t]*[^\r\n;]*)",
            re.MULTILINE)
        text, n = pattern.subn(
            lambda m, s=size, l=label: "%smenu.itemname.menuvideo.resolution.%s = %s   %s"
            % (m.group(1), s, s, l), text)
        changed += n

    if changed:
        with open(BASE_DEF, "w", encoding="utf-8", errors="surrogateescape",
                  newline="") as fh:
            fh.write(text)
    return changed


def ensure_resolution_menu(text):
    """Write the video resolution list, and keep its labels current.

    It used to bail out as soon as the 4K key existed, so a motif that already
    had the list kept the old labels for ever - which is how "(QHD)" and "(4K
    ULTRA HD)" survived a change that had stopped calling them right.
    """
    nl = "\r\n" if "\r\n" in text else "\n"
    wanted = {}
    for line in RESOLUTION_MENU.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        key, _sep, value = line.partition(" = ")
        wanted[key.strip()] = value.strip()

    changed = 0
    if "menu.itemname.menuvideo.resolution.3840x2160" not in text:
        head = RESOLUTION_ANCHOR.search(text)
        if not head:
            return text, 0
        block = nl + nl + RESOLUTION_MENU.replace("\n", nl).rstrip("\r\n")
        text = text[:head.end()] + block + text[head.end():]
        changed += 1

    for key, value in wanted.items():
        pattern = re.compile(r"^[ \t]*" + re.escape(key) + r"[ \t]*=[^;\r\n]*",
                             re.MULTILINE)
        if pattern.search(text):
            new = pattern.sub("\t%s = %s" % (key, value), text, count=1)
            if new != text:
                changed += 1
                text = new

    # A motif that already carries the list keeps exactly the rows it has, so a
    # size added to RESOLUTION_MENU later never reached it - which is how the
    # engine's own screen still showed a 1920x1080 ceiling. Any size in the
    # block above that is missing goes in after the row before it, keeping the
    # list ascending.
    header = re.compile(r"^[ \t]*menu\.itemname\.menuvideo\.resolution[ \t]*=[^\r\n]*",
                        re.MULTILINE)
    prev = None
    for line in RESOLUTION_MENU.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        key, _sep, value = line.partition(" = ")
        key, value = key.strip(), value.strip()
        if not re.fullmatch(r"menu\.itemname\.menuvideo\.resolution\.\d+x\d+", key):
            continue
        if re.search(r"^[ \t]*" + re.escape(key) + r"[ \t]*=", text, re.MULTILINE):
            prev = key
            continue
        anchor = None
        if prev:
            anchor = re.search(r"^[ \t]*" + re.escape(prev) + r"[ \t]*=[^\r\n]*",
                               text, re.MULTILINE)
        anchor = anchor or header.search(text)
        if not anchor:
            continue
        text = text[:anchor.end()] + nl + "\t%s = %s" % (key, value) + text[anchor.end():]
        prev = key
        changed += 1
    return text, changed


def ensure_window_menu(text):
    """Add the Window Size submenu right after the resolution list.

    The engine builds the submenu from the itemname keys it finds, so the keys
    are the menu. The row handlers live in external/script/options.lua; without
    them these rows would open and do nothing, so both are written together.
    """
    nl = "\r\n" if "\r\n" in text else "\n"
    rows = [line for line in WINDOW_MENU.splitlines() if line.strip()]
    header = "menu.itemname.menuvideo.window"
    if not re.search(r"^[ \t]*" + re.escape(header) + r"[ \t]*=", text, re.MULTILINE):
        anchor = re.search(
            r"^[ \t]*menu\.itemname\.menuvideo\.resolution\.back[ \t]*=[^\r\n]*",
            text, re.MULTILINE)
        if not anchor:
            return text, 0
        block = nl + nl.join("\t" + row for row in rows)
        return text[:anchor.end()] + nl + block + text[anchor.end():], 1

    # An existing block keeps whatever sizes it has, so new ones go in after
    # the row before them, the same way the resolution list is kept current.
    changed = 0
    prev = None
    for row in rows:
        key = row.partition(" = ")[0].strip()
        value = row.partition(" = ")[2].strip()
        if re.search(r"^[ \t]*" + re.escape(key) + r"[ \t]*=", text, re.MULTILINE):
            prev = key
            continue
        anchor = None
        if prev:
            anchor = re.search(r"^[ \t]*" + re.escape(prev) + r"[ \t]*=[^\r\n]*",
                               text, re.MULTILINE)
        if not anchor:
            continue
        text = text[:anchor.end()] + nl + "\t%s = %s" % (key, value) + text[anchor.end():]
        prev = key
        changed += 1
    return text, changed


def main():
    if not os.path.isfile(MOTIF):
        print(f"missing motif: {MOTIF}", file=sys.stderr)
        return 1
    if not install_ttf():
        return 1

    with open(MOTIF, "r", encoding="utf-8", errors="surrogateescape", newline="") as fh:
        original = fh.read()

    text, added = ensure_font_files(original)
    if added:
        print(f"  registered font10/font11 in {os.path.basename(MOTIF)}")

    text, res_added = ensure_resolution_menu(text)
    if res_added:            print(f"  rewrote the video resolution list in "
                  f"{os.path.basename(MOTIF)}")

    text, win_added = ensure_window_menu(text)
    if win_added:
        print(f"  wrote the window-size submenu in {os.path.basename(MOTIF)}")

    dropped = ensure_widescreen_resolutions()
    if dropped:
        print(f"  dropped {dropped} 4:3 size(s) from "
              f"{os.path.basename(BASE_DEF)}")

    touched = 0
    for key, value in REWRITES:
        text, count = set_key(text, key, value)
        if count:
            touched += count
        else:
            print(f"  warning: {key} not found in {os.path.basename(MOTIF)}")

    for section, settings in SECTION_LAYOUT.items():
        for key, value in settings:
            text, count = set_section_key(text, section, key, value)
            if not count:
                text, count = add_section_key(text, section, key, value)
            touched += count
            if not count:
                print(f"  warning: [{section}] {key} not found in "
                      f"{os.path.basename(MOTIF)}")

    if text != original:
        with open(MOTIF, "w", encoding="utf-8", errors="surrogateescape", newline="") as fh:
            fh.write(text)
        print(f"  retinted {touched} menu keys and {added} font registrations")
        print(f"updated {os.path.relpath(MOTIF, ROOT)}")
    else:
        print(f"{os.path.relpath(MOTIF, ROOT)} already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
