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
    # the black bar under the title screen
    ("footer.title.font", f"{B}, 0, 1, {GOLD}, 255, -1"),
    ("footer.info.font", f"{B}, 0, 0, {GOLD}, 255, -1"),
    ("footer.version.font", f"{B}, 0, -1, {DEEP}, 255, -1"),
    ("footer.title.scale", "1,1"),
    ("footer.info.scale", "1,1"),
    ("footer.version.scale", "1,1"),
    # The bar is rows 700-719; a 15px face at the engine's 715 clipped its
    # descenders, so centre the three fields inside the bar instead.
    ("footer.title.offset", "5, 700"),
    ("footer.info.offset", "640, 700"),
    ("footer.version.offset", "1275, 700"),
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
    ("menu.boxcursor.col", BRIGHT),
    ("menu.boxbg.col", "40, 10, 14"),
)

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


def _gradient(size, stops):
    """Vertical gradient over a whole cell, so the face shades like the logo."""
    w, h = size
    img = Image.new("RGBA", (w, h))
    pix = img.load()
    stops = sorted(stops)
    for y in range(h):
        t = y / max(1, h - 1)
        col = stops[-1][1]
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                k = (t - t0) / max(1e-6, t1 - t0)
                col = tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(3))
                break
        row = col + (255,)
        for x in range(w):
            pix[x, y] = row
    return img


def _shift(mask, dx, dy):
    out = Image.new("L", mask.size, 0)
    out.paste(mask, (dx, dy))
    return out


def glyph(ch, font, cell_h, depth, face_stops=FACE):
    """One glyph: maroon extrusion, gold face, cream lip along the top edge."""
    ascent, _descent = font.getmetrics()
    adv = max(1, int(round(font.getlength(ch))))
    w = adv + depth + 1
    mask = Image.new("L", (w, cell_h), 0)
    ImageDraw.Draw(mask).text((0, ascent), ch, font=font, fill=255, anchor="ls")

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

    touched = 0
    for key, value in REWRITES:
        text, count = set_key(text, key, value)
        if count:
            touched += count
        else:
            print(f"  warning: {key} not found in {os.path.basename(MOTIF)}")

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
