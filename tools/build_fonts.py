"""Make the menus wear the title logo's face and palette.

The wordmark is painted by tools/build_title.py with art.font(), i.e. DejaVu Sans
Bold, gold on maroon. The screenpack's own menu fonts are bitmap faces in
blue/pink/grey, so nothing else in the game looked like the logo.

Three things happen here, all of them regenerated rather than hand-edited,
because build-assets.yml copies the engine's data/ over ours on every run and
anything typed into data/ikemen1/system.def by hand is lost:

1. The logo's TrueType face is copied to data/ikemen1/fonts/Display.ttf.
2. Display.def (36px, headings and menus) and Body.def (15px, footers and
   values) are written next to it. These are TrueType fonts, so the engine's
   ``R,G,B`` in a font spec actually tints them - bitmap fonts ignore it and go
   by palette bank, which is why the old menus could only be 8 fixed colours.
3. Every menu/select/scoreboard font spec in system.def is repointed at those
   two fonts and retinted to the logo's gold/red palette.

Run:  python3 tools/build_fonts.py
"""

from __future__ import annotations

import glob
import os
import re
import shutil
import sys

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
MAROON = "72, 10, 16"

D = "10"   # Display.def
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
    ("menu.item.active.font", f"{D},0,-1, {BRIGHT}"),
    ("menu.item.selected.font", f"{D},0,1, {RED}"),
    ("menu.item.selected.active.font", f"{D},0,1, {BRIGHT}"),
    ("menu.item.value.font", f"{B},0,-1, {DEEP}"),
    ("menu.item.value.active.font", f"{B},0,-1, {BRIGHT}"),
    ("menu.item.value.conflict.font", f"{B},0,-1, {RED}"),
    ("menu.item.info.font", f"{B},0,-1, {GOLD}"),
    ("menu.item.info.active.font", f"{B},0,-1, {BRIGHT}"),
    ("title.font", f"{D},0,0, {BRIGHT}"),
    ("loading.font", f"{B}, 0, -1, {DEEP}, 255, -1"),
    # the black bar under the title screen
    ("footer.title.font", f"{B}, 0, 1, {RED}, 255, -1"),
    ("footer.info.font", f"{B}, 0, 0, {GOLD}, 255, -1"),
    ("footer.version.font", f"{B}, 0, -1, {DEEP}, 255, -1"),
    ("footer.title.scale", "1,1"),
    ("footer.info.scale", "1,1"),
    ("footer.version.scale", "1,1"),
    ("footer.overlay.col", MAROON),
    # The bar is rows 700-719; a 15px face at the engine's 715 clipped its
    # descenders, so centre the three fields inside the bar instead.
    ("footer.title.offset", "5, 702"),
    ("footer.info.offset", "640, 702"),
    ("footer.version.offset", "1275, 702"),
    # infobox, game over text, story text
    ("text.font", f"{B}, 0, 1, {GOLD}"),
    # select screen
    ("p1.name.font", f"{D}, 0, 1, {GOLD}"),
    ("p2.name.font", f"{D}, 0, -1, {RED}"),
    ("stage.font", f"{B}, 0, 0, {DEEP}"),
    ("stage.active.font", f"{B}, 0, 0, {BRIGHT}"),
    ("stage.active2.font", f"{B}, 0, 0, {RED}"),
    ("stage.done.font", f"{B}, 0, 0, {DEEP}"),
    ("record.font", f"{B}, 0, 0, {DEEP}"),
    ("p1.teammenu.selftitle.font", f"{B}, 0, 0, {BRIGHT}"),
    ("p1.teammenu.enemytitle.font", f"{B}, 0, 0, {BRIGHT}"),
    ("p1.teammenu.item.font", f"{B}, 0, 1, {GOLD}"),
    ("p1.teammenu.item.active.font", f"{B}, 0, 1, {BRIGHT}"),
    ("p1.teammenu.item.active2.font", f"{B}, 0, 1, {RED}"),
    ("p2.teammenu.selftitle.font", f"{B}, 1, 0, {RED}"),
    ("p2.teammenu.enemytitle.font", f"{B}, 1, 0, {RED}"),
    ("p2.teammenu.item.font", f"{B}, 0, -1, {GOLD}"),
    ("p2.teammenu.item.active.font", f"{B}, 1, -1, {RED}"),
    ("p2.teammenu.item.active2.font", f"{B}, 1, -1, {BRIGHT}"),
    ("p1.palmenu.text.font", f"{B}, 0, 1, {GOLD}"),
    ("p2.palmenu.text.font", f"{B}, 0, -1, {RED}"),
    ("p1.palmenu.number.font", f"{B}, 0, 0, {GOLD}"),
    ("p2.palmenu.number.font", f"{B}, 0, 0, {RED}"),
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
    ("start.timer.font", f"{D}, 0, -1, {RED}"),
    # scoreboard
    ("item.rank.font", f"{B}, 0, -1, {DEEP}"),
    ("item.rank.active.font", f"{B}, 0, -1, {GOLD}"),
    ("item.rank.active2.font", f"{B}, 0, -1, {BRIGHT}"),
    ("item.result.font", f"{B}, 0, -1, {DEEP}"),
    ("item.result.active.font", f"{B}, 0, -1, {GOLD}"),
    ("item.result.active2.font", f"{B}, 0, -1, {BRIGHT}"),
    ("item.name.font", f"{B}, 0, 1, {GOLD}"),
    ("item.name.active.font", f"{B}, 0, 1, {BRIGHT}"),
    ("item.name.active2.font", f"{B}, 0, 1, {RED}"),
    # key config, movelist, menu chrome
    ("keymenu.p1.playerno.font", f"{B}, 0, 0, {GOLD}"),
    ("keymenu.p2.playerno.font", f"{B}, 0, 0, {RED}"),
    ("movelist.title.font", f"{D}, 0, 0, {BRIGHT}"),
    ("movelist.text.font", f"{B}, 0, 1, {GOLD}"),
    ("menu.boxcursor.col", BRIGHT),
    ("menu.boxbg.col", "40, 10, 14"),
)

DISPLAY_DEF = """[FNT v2]
; FNT v2 version number.  Don't change this.
fntversion = 2,00
; Name of this font.
name = "Display"

[Def]
; TrueType, so system.def can tint it with R,G,B.
Type = truetype
; Size of font: width, height.  Only height is used for truetype fonts.
Size = 36,36
Spacing = 1,1
Offset = 0,0
; The same face the title wordmark is painted with.
File = Display.ttf
Blend = 1
"""

BODY_DEF = """[FNT v2]
; FNT v2 version number.  Don't change this.
fntversion = 2,00
; Name of this font.
name = "Body"

[Def]
; TrueType, so system.def can tint it with R,G,B.
Type = truetype
; Size of font: width, height.  Only height is used for truetype fonts.
Size = 15,15
Spacing = 1,1
Offset = 0,0
; The same face the title wordmark is painted with.
File = Display.ttf
Blend = 1
"""

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
    for fname, body in (("Display.def", DISPLAY_DEF), ("Body.def", BODY_DEF)):
        path = os.path.join(FONT_DIR, fname)
        if not os.path.isfile(path) or open(path, encoding="utf-8-sig").read() != body:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(body)
            print(f"  wrote {os.path.relpath(path, ROOT)}")
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
    """Register Display/Body as font10/font11 unless they already are."""
    if re.search(r"^[ \t]*font1[01][ \t]*=", text, re.MULTILINE | re.IGNORECASE):
        return text, 0
    nl = "\r\n" if "\r\n" in text else "\n"
    anchor = re.search(r"^[ \t]*font9[ \t]*=.*$", text, re.MULTILINE | re.IGNORECASE)
    if anchor is None:
        anchor = re.search(r"^[ \t]*font[0-9]+[ \t]*=.*$", text, re.MULTILINE | re.IGNORECASE)
    if anchor is None:
        return text, 0
    added = (nl + "font10 = ikemen1/fonts/Display.def" + nl
             + "font11 = ikemen1/fonts/Body.def")
    return text[:anchor.end()] + added + text[anchor.end():], 2


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
