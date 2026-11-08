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

# The faces are baked at this multiple of their on-screen size and drawn at the
# reciprocal text scale, so the glyphs carry twice the pixels they show at 1080p
# and stand up to a 4K render instead of being stretched into it. Baked art,
# .def Size and .def Offset all double together; the motif's text scales halve
# to match, which leaves every row, pitch and wrap exactly where it was.
SUPERSAMPLE = 2
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
    # The title screen's own clear colour. It was white, so every pixel the
    # painted sky and clouds did not reach - the bottom third of a 1080p
    # screen - was a white band with the menu floating above it.
    ("bgclearcolor", "0, 0, 0"),
    # The boot caption was the 13px Body face, sheared for a "speed" slant, at
    # the bottom-right corner: small, skewed and easy to miss. It is the Display
    # face at the menus' own size now, upright, and main.f_loadingDraw centres
    # it on the frame while its dots run.
    ("loading.font", f"{D}, 0, 0, {GOLD}"),
    ("loading.xshear", "0"),
    # Centred on the frame: 960 is its middle, and the caption sits under the
    # spinner at 594. The stock 1800,1020 put it in the bottom-right corner.
    ("loading.offset", "960, 594"),
    # The engine's own bottom bar ("I.K.E.M.E.N. GO" + version) is not rewritten
    # here but removed outright - see DROP_KEYS below.
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
    ("p1.teammenu.selftitle.font", f"{B}, 0, 1, {BRIGHT}"),
    ("p1.teammenu.enemytitle.font", f"{B}, 0, 1, {BRIGHT}"),
    # The stage-select row is caption type like every other label on that screen;
    # it had drifted onto the 13px Body face, so the stage name was the one line
    # under the wall set in another size.
    ("stage.font", f"{D}, 0, 0, {DEEP}"),
    ("stage.active.font", f"{D}, 0, 0, {BRIGHT}"),
    ("stage.active2.font", f"{D}, 0, 0, {DEEP}"),
    ("stage.done.font", f"{D}, 0, 0, {DEEP}"),
    ("stage.scale", "0.75, 0.75"),
    ("stage.active.scale", "0.75, 0.75"),
    ("stage.active2.scale", "0.75, 0.75"),
    ("stage.done.scale", "0.75, 0.75"),
    # Every active/selected variant draws the same doubled face as its base row,
    # so it carries the base row's scale rather than falling back to 1.0 and
    # drawing twice the size of the row above it.
    ("menu.item.active.scale", "0.75, 0.75"),
    ("menu.item.selected.scale", "0.75, 0.75"),
    ("menu.item.selected.active.scale", "0.75, 0.75"),
    ("menu.item.value.scale", "0.75, 0.75"),
    ("menu.item.value.active.scale", "0.75, 0.75"),
    ("menu.item.info.scale", "0.75, 0.75"),
    ("menu.item.info.active.scale", "0.75, 0.75"),
    ("p1.teammenu.item.font", f"{D}, 0, 1, {GOLD}"),
    ("p1.teammenu.item.active.font", f"{D}, 0, 1, {BRIGHT}"),
    ("p1.teammenu.item.active2.font", f"{D}, 0, 1, {BRIGHT}"),
    ("p2.teammenu.selftitle.font", f"{B}, 0, -1, {GOLD}"),
    ("p2.teammenu.enemytitle.font", f"{B}, 0, -1, {GOLD}"),
    ("p2.teammenu.item.font", f"{D}, 0, -1, {GOLD}"),
    ("p2.teammenu.item.active.font", f"{D}, 0, -1, {AMBER}"),
    ("p2.teammenu.item.active2.font", f"{D}, 0, -1, {AMBER}"),
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
    # the key list had no fonts of its own and inherited the 45px Display face
    # on a 36px pitch; it is a 15-row table, so it gets the 20px Body face
    ("keymenu.item.font", f"{B},0,-1, {GOLD}"),
    ("keymenu.item.active.font", f"{B},0,-1, {BRIGHT}"),
    ("keymenu.item.selected.font", f"{B},0,-1, {BRIGHT}"),
    ("keymenu.item.selected.active.font", f"{B},0,-1, {BRIGHT}"),
    ("movelist.title.font", f"{D}, 0, 0, {BRIGHT}"),
    ("movelist.text.font", f"{D}, 0, 1, {GOLD}"),
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

# Keys to delete from the motif rather than rewrite.
#
# Parking the footer's three text fields below the screen was not enough: the
# engine draws the footer's backdrop rect (footer.overlay, colour 0,0,64) from
# main.lua whenever the footer keys parse at all, and its "0, 0" alpha leaves
# the strip drawn - a black bar with nothing written on it. Deleting every
# footer.* key makes sec.footer nil in the engine, so neither the rect nor the
# text is drawn and the menus use the full height. Idempotent: stock keys that
# survive a re-stage are dropped again on every build.
DROP_KEYS = ()


def drop_keys(text, prefixes):
    """Delete every `key = value` line whose key starts with one of prefixes."""
    out, dropped = [], 0
    for line in text.splitlines(True):
        s = line.strip()
        if "=" in s and not s.startswith((";", "#", "/")):
            key = s.split("=", 1)[0].strip().lower()
            if any(key.startswith(p) for p in prefixes):
                dropped += 1
                continue
        out.append(line)
    return "".join(out), dropped


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
    # The list is centred on the frame both ways: labels are centre-aligned (0)
    # on 1920/2 = 960 and the rows start at 300 on a 60px pitch, so the ten rows
    # the window can show end at 891 on a 1080-tall frame. It used to be a
    # left-aligned block at 736,140, which read as top-left rather than centred -
    # and the row text was not even drawn from menu.pos: this engine bakes the
    # stock 320x240 [Menu Info] anchor into the pause item sprites, which put the
    # list at the bottom of the screen, off the edge, while the cursor band drew
    # at menu.pos. main.f_menuItemPos now places every row from menu.pos.
    ("menu.pos", "960, 300"),
    # No dark plate behind the pause list.
    ("menu.boxbg.visible", "0"),
    ("menu.item.spacing", "0, 60"),
    ("menu.window.visibleitems", "10"),
    # The heading sits over the centred column, not a third of the way across.
    ("title.offset", "960, 160"),
    # The band is centred on the same column as the rows and covers the 51px row
    # the 1.5x face draws: it is drawn from pos.y + coords[2] with height
    # coords[4]-coords[2]+1, so 0..50 sits on the row it marks.
    ("menu.boxcursor.coords", "-254, 0, 254, 50"),
    # Centre-aligned: every row centres on 960, so a long label cannot hang off
    # one side of the band the way the old left-aligned column did.
    ("menu.item.font", f"{D},0,0, {GOLD}"),
    ("menu.item.active.font", f"{DA},0,0, {BRIGHT}"),
    ("menu.item.selected.font", f"{D},0,0, {BRIGHT}"),
    ("menu.item.selected.active.font", f"{DA},0,0, {BRIGHT}"),
    # The command list was the 13px Body face at 1.5x (19px rows) while every
    # other screen sets 34px Display; it is the same face as the menus now, at
    # the face's own size, so a row is as tall as a pause-menu row.
    # The heading is centred on the frame's own width: 860 past movelist.pos.x
    # of 100 puts it at 960, level with the PAUSE title above it. It shipped as
    # 540 - the middle of the old 1280 frame - so the heading sat a third of the
    # way across while the list under it filled the screen.
    # `%s` is substituted with the character's name, so the screen only ever
    # said who the moves belonged to, never that it was the command list.
    ("movelist.title.text", "Command List - %s"),
    # A pad glyph sits 9px below the top of its own row and is scaled to the
    # row height, so it hung into the row below and collided with that row's
    # text. Flush with the row.
    ("movelist.glyphs.offset", "0, 0"),
    ("movelist.text.scale", "1, 1"),
    ("movelist.title.scale", "1, 1"),
    ("movelist.glyphs.scale", "1, 1"),
    ("movelist.text.spacing", "5, 4"),
    # Rows start below the heading. [Pause Menu] inherits this offset from the
    # stock motif, but [Training Pause Menu] is topped up from the engine's own
    # default motif instead of from ours, so without it written out that list's
    # first row draws on the heading's line.
    ("movelist.text.offset", "0, 54"),
    # The command list's columns are measured on screen (the script gives the
    # names the width of the longest one and puts the keys one gap past it), so
    # this window is only the box those rows are clipped to and the heading's
    # anchor. Keeping it symmetric on the frame - 210 + 1500 = 1710, 210 either
    # side - means a long list that reaches the margin still has room. It used to
    # start at 100, which put the box's middle on 850.
    # The heading offset keeps movelist.pos.x + title.offset.x on the frame's
    # middle (210 + 750 = 960).
    ("movelist.pos", "210, 90"),
    ("movelist.title.offset", "750, -18"),
    ("movelist.window.width", "1500"),
)

SECTION_LAYOUT = {
    "Title Info": (
        # The same centred column as the pause and options lists, on the
        # wordmark's own axis: labels are centre-aligned (0) on 1920/2 = 960, so
        # every row centres under the centred logo instead of hanging off a
        # left-aligned edge at 800 - the column used to be right-aligned at 1240,
        # which pushed long labels off the frame, then left-aligned at 800, which
        # left the block looking shifted. It stays at 470 instead of being
        # centred vertically: the wordmark fills the top half of the screen, and
        # a centred block would sit through "CHINA". From 470 the nine rows at a
        # 56px pitch end at 963, which leaves the bottom headroom the logo has
        # above them.
        ("menu.pos", "960, 470"),
        # The keys this screen's script reads. options.lua and start.lua call
        # getInput with motif.title_info.menu.done.key and the section defined
        # no menu keys at all, so nothing confirmed anything here; the bindings
        # are the ones the select screen already uses (palmenu.done).
        ("menu.done.key", "a, b, c, x, y, z"),
        # Centre-aligned like the other two lists: the item's own box is centred
        # on menu.pos.x, so a longer label grows either side of 960 rather than
        # rightwards off the column.
        ("menu.item.font", f"{D},0,0, {GOLD}"),
        ("menu.item.active.font", f"{DA},0,0, {BRIGHT}"),
        ("menu.item.spacing", "0, 56"),
        ("menu.window.visibleitems", "10"),
        # The engine's own footer ("I.K.E.M.E.N. GO" bottom-left, build number
        # bottom-right) is drawn from these keys. Deleting them did not remove
        # it - the engine falls back to its stock footer - so they are written
        # parked below the screen with an empty overlay window instead.
        ("footer.title.font", f"{B}, 0, 1, {GOLD}, 255, -1"),
        ("footer.title.offset", "5, 5000"),
        ("footer.title.scale", "1, 1"),
        ("footer.info.font", f"{B}, 0, 0, {GOLD}, 255, -1"),
        ("footer.info.offset", "640, 5000"),
        ("footer.info.scale", "1, 1"),
        ("footer.version.font", f"{B}, 0, -1, {DEEP}, 255, -1"),
        ("footer.version.offset", "1275, 5000"),
        ("footer.version.scale", "1, 1"),
        ("footer.overlay.col", "0, 0, 0"),
        ("footer.overlay.alpha", "0, 0"),
        ("footer.overlay.window", "0, 0, 1, 1"),
    ),
    "Option Info": (
        # Thirteen rows at the stock 42px pitch overlapped by 3px under the 45px
        # bitmap face; 46 is the smallest pitch that separates them. All thirteen
        # fit: rows run from 242 to 839 on a 1080-tall frame, centred on it.
        ("menu.item.spacing", "0, 46"),
        # The same centred column as the pause list. Alignment -1 is RIGHT in
        # this engine, so labels end at menu.pos.x and grow leftwards; values are
        # left-aligned (1) and start menu.pos.x + value.offset further on. With
        # the labels ending at 945 and the values starting at 975, the boundary
        # between the two columns sits on 960 - the middle of the frame - and
        # every row straddles the centre instead of the whole list sitting on the
        # right-hand half, which is where 940/99 put it. The gutter is 30px, so
        # a right-aligned label can never reach the value column whatever its
        # width; the longest one, "RETURN WITHOUT SAVING" (777px), starts at 168.
        ("menu.pos", "945, 242"),
        # Both arrows still sat on 642, the 1280 frame's centre, while the
        # heading above them was already at 960. Same place as [Pause Menu]'s.
        ("menu.arrow.up.offset", "960, -76"),
        ("menu.arrow.down.offset", "960, 788"),
        # options.lua reads these six paths on every frame it runs and the
        # section defined none of them: the list drew, and then no key did
        # anything on it, because each read was nil. Bindings follow the select
        # screen's palette menu - A/B/C/X/Y/Z confirms, M backs out, the same
        # U/R and D/L pairs step values - so the menu answers the keys a player
        # has already been using two screens earlier.
        ("menu.done.key", "a, b, c, x, y, z"),
        ("menu.add.key", "U, R"),
        ("menu.subtract.key", "D, L"),
        ("menu.cancel.key", "m"),
        ("keymenu.done.key", "a, b, c, x, y, z"),
        # The title was still at 640 - a number carried over from the 1280-wide
        # stock motif - so on a 1920 frame it sat a third of the screen to the
        # left of centre while the list sat to the right of it. Font field 0 is
        # centre alignment, so 960 is the middle of the screen.
        ("title.offset", "960, 48"),
        ("menu.item.font", f"{D},0,-1, {GOLD}"),
        ("menu.item.active.font", f"{DA},0,-1, {BRIGHT}"),
        # The highlighted row used to switch to 1 (left), so it jumped to the
        # right and overlapped the value column. Same alignment as the rest now.
        ("menu.item.selected.font", f"{D},0,-1, {BRIGHT}"),
        ("menu.item.selected.active.font", f"{DA},0,-1, {BRIGHT}"),
        # Values get a column of their own, left-aligned 30px past the labels'
        # right edge (975 on this frame). They used to inherit the label's -1
        # (RIGHT) alignment, so each value ended where its label did and printed
        # across the last third of it - which is what made Video Settings
        # unreadable (every row read "RendererOpenGL 3.3").
        #
        # The face was Body (a 13px cell) beside 45px labels, so "OpenGL 3.3"
        # and "1920x1080" were a third of the height of the word they belonged
        # to. Display is the menu's own face, so a row reads as one line of
        # text; from 975 to the 1920 edge is room for far more than the 16
        # glyphs the longest value needs.
        ("menu.item.value.font", f"{D},0,1, {DEEP}"),
        ("menu.item.value.active.font", f"{DA},0,1, {BRIGHT}"),
        ("menu.item.value.conflict.font", f"{D},0,1, {RED}"),
        ("menu.item.info.font", f"{D},0,1, {GOLD}"),
        ("menu.item.info.active.font", f"{DA},0,1, {BRIGHT}"),
        # No dark plate behind the options list any more.
        ("menu.boxbg.visible", "0"),
        # The key and joystick screens are one table drawn twice, side by side,
        # so both panes share one face, one size and one pair of columns. They
        # did not before: the labels were Body while the (F1)/(Esc) notes still
        # inherited the 45px Display face from menu.item.info above, and the
        # values started 454px into a 270px pane, so P2's values ran off the
        # right edge of the 1280 frame.
        ("keymenu.item.font", f"{B},0,1, {GOLD}"),
        ("keymenu.item.active.font", f"{B},0,1, {BRIGHT}"),
        ("keymenu.item.selected.font", f"{B},0,1, {BRIGHT}"),
        ("keymenu.item.selected.active.font", f"{B},0,1, {BRIGHT}"),
        ("keymenu.item.scale", "1.5, 1.5"),
        ("keymenu.item.active.scale", "1.5, 1.5"),
        ("keymenu.item.selected.scale", "1.5, 1.5"),
        ("keymenu.item.selected.active.scale", "1.5, 1.5"),
        ("keymenu.item.value.font", f"{B},0,-1, {GOLD}"),
        ("keymenu.item.value.active.font", f"{B},1,-1, {BRIGHT}"),
        ("keymenu.item.value.conflict.font", f"{B},0,-1, {RED}"),
        ("keymenu.item.value.scale", "1.5, 1.5"),
        ("keymenu.item.value.active.scale", "1.5, 1.5"),
        ("keymenu.item.value.conflict.scale", "1.5, 1.5"),
        ("keymenu.item.info.font", f"{B},0,-1, {GOLD}"),
        ("keymenu.item.info.active.font", f"{B},1,-1, {BRIGHT}"),
        ("keymenu.item.info.scale", "1.5, 1.5"),
        ("keymenu.item.info.active.scale", "1.5, 1.5"),
        # One label column and one value column per pane: the label is drawn
        # from the pane's left edge and the bound key ends on its right edge,
        # 540px in. The two panes are identical, so P1 and P2 mirror each other.
        ("keymenu.item.value.offset", "675, 0"),
        ("keymenu.item.value.active.offset", "675, 0"),
        ("keymenu.item.value.conflict.offset", "675, 0"),
        ("keymenu.item.info.offset", "675, 0"),
        ("keymenu.item.info.active.offset", "675, 0"),
        ("menu.item.value.offset", "30, 0"),
        ("menu.item.value.active.offset", "30, 0"),
        ("menu.item.value.conflict.offset", "30, 0"),
        ("menu.item.info.offset", "30, 0"),
        ("menu.item.info.active.offset", "30, 0"),
        # The band spans both columns: it starts level with the widest label
        # (400) and runs to 1220, instead of sitting under the middle of the
        # list.
        ("menu.boxcursor.coords", "-800, 0, 20, 44"),
        # Key and joystick config put two panels side by side, each column
        # anchored on this offset and right-aligned against it. At 276 the
        # widest label ("CONFIG ALL", 370px) started at x=-94 and was cut off by
        # the screen edge; the panels are 154px further right, so labels start
        # at 60 and the P2 values end at 1348, still inside 1920.
        # Two panes of the same width with an 80px gutter: 60..600 and
        # 680..1220 on the 1280-wide motif, so both columns sit fully on screen
        # and the pair reads as one centred block.
        ("keymenu.p1.menuoffset", "210, 128"),
        ("keymenu.p2.menuoffset", "1035, 128"),
        # The stock 54px pitch put the 18th row (Config all, the 15 bindings,
        # Back) at y=1017, off a 720-tall screen. 30 fits them from 128 to 638.
        ("keymenu.item.spacing", "0, 36"),
        # The band covers the row it is on, not a 35px slice of the one above.
        ("keymenu.boxcursor.coords", "-10, 0, 685, 36"),
        # Player labels centred over their own pane instead of the stock 234.
        ("keymenu.p1.playerno.offset", "548, 96"),
        ("keymenu.p2.playerno.offset", "1372, 96"),
        ("keymenu.p1.playerno.scale", "1.5, 1.5"),
        ("keymenu.p2.playerno.scale", "1.5, 1.5"),
    ),
    "Select Info": (
        # Team mode: the cursor was animation 180, a 22px arrow that slides 3px a
        # frame - the spinning arrow. It is the arrow's own still now, and the
        # blink is gone because active2.font is set to the active colour.
        # The record line (WINS / LOSSES) sat at y=1008, under the bottom edge
        # of the stage card, so it read as part of the card. It is above the
        # card now, clear of the box and the two portraits.
        ("record.offset", "960, 684"),
        ("p1.teammenu.item.cursor.anim", "-1"),
        ("p1.teammenu.item.cursor.spr", "180,0"),
        ("p2.teammenu.item.cursor.anim", "-1"),
        ("p2.teammenu.item.cursor.spr", "180,0"),
        # "TEAM MODE" was drawn through a perspective projection: yangle 52.5 on
        # both sides, so the heading came out as a skewed parallelogram that read
        # as a broken face next to the upright Single/Simul/Tag/Turns list. It is
        # flat now (yangle 0) and starts where the list starts: left on P1's
        # side, right on P2's, at the same 120/1796 edges the item font uses.
        ("p1.teammenu.selftitle.yangle", "0"),
        ("p1.teammenu.enemytitle.yangle", "0"),
        ("p2.teammenu.selftitle.yangle", "0"),
        ("p2.teammenu.enemytitle.yangle", "0"),
        ("p1.teammenu.selftitle.offset", "0, 23"),
        # The slot markers are placed by start.f_teamMenu from the measured word
        # width, so their def offsets must stay 0 or a baked-in offset would be
        # added on top and float them out over the portrait grid again.
        ("p1.teammenu.value.icon.offset", "0, 0"),
        ("p1.teammenu.value.empty.icon.offset", "0, 0"),
        ("p2.teammenu.value.icon.offset", "0, 0"),
        ("p2.teammenu.value.empty.icon.offset", "0, 0"),
        ("p1.teammenu.value.spacing", "38, 0"),
        ("p2.teammenu.value.spacing", "-38, 0"),
        ("p1.teammenu.enemytitle.offset", "0, 23"),
        ("p2.teammenu.selftitle.offset", "0, 23"),
        ("p2.teammenu.enemytitle.offset", "0, 23"),
    ),
    # [VS Screen] belongs to build_select_ui.py (VS_TEXT / VS_PLATE), which
    # runs after this tool. This block was a leftover copy of an earlier fix
    # and, being written later, quietly won: it put P2's name back at y=615
    # (across the VS mark instead of on the fighters' row) and shrank the
    # stage preview back to the old 0.5267 panel inside a 640px window. One
    # owner per section from now on.
    "Replay Info": (
        # 42px rows, so the band matches the pitch exactly.
        ("menu.boxcursor.coords", "-15, 0, 462, 41"),
        # The rows were already at the converted 1.5x pitch and scale, but the
        # heading and both arrows were still on 640/642 - the 1280 frame's
        # centre - so they sat a third of the screen left of the list's middle.
        # The column itself (menu.pos 621) is right-aligned and is left alone:
        # its band geometry for right-aligned text is a separate question.
        ("title.offset", "960, 48"),
        ("menu.arrow.up.offset", "960, -76"),
        ("menu.arrow.down.offset", "960, 788"),
    ),
    "Pause Menu": PAUSE_LAYOUT,
    # The training pause list is the same centred column: it is another set of
    # rows on the same screen, not another screen, and it has to fit the same
    # frame. Its old left position put it a third of the way across while the
    # rows ran past the bottom.
    "Training Pause Menu": PAUSE_LAYOUT,
    # The warning box keeps the stock 284px left margin for its body text; only
    # its heading was still centred on the 1280 frame.
    "Warning Info": (
        ("title.offset", "960, 48"),
    ),
    # MUGEN 1.0's info box - same leftover, one pixel row higher.
    "Infobox": (
        ("title.offset", "960, 38"),
    ),
    # legacymode is off, so nothing draws this layout, but it was still the old
    # centre; the extended screen it replaced already uses counter.offset 960,540.
    "Continue Screen": (
        ("pos", "960, 240"),
    ),
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
    # The cell has to come out at exactly SUPERSAMPLE times the size the face
    # used to declare, or the halved text scale would not land on the old pixels:
    # the +depth+1 in the height is a constant, not something that scales, so it
    # is measured on a face of the original size and the whole cell multiplied.
    ref = ImageFont.truetype(ttf, max(1, px // SUPERSAMPLE))
    ref_asc, ref_desc = ref.getmetrics()
    ref_depth = max(1, depth // SUPERSAMPLE)
    cell_h = (ref_asc + ref_desc + ref_depth + 1) * SUPERSAMPLE
    space_w = max(2, int(round(ref.getlength(" "))) + ref_depth) * SUPERSAMPLE

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
        write_font(name, px * SUPERSAMPLE, depth * SUPERSAMPLE, dst, face_stops)
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
    head = re.compile(r"^[ \t]*\[" + re.escape(section) + r"\][ \t]*(?:;.*)?$",
                      re.MULTILINE | re.IGNORECASE).search(text)
    if not head:
        print(f"  warning: section [{section}] not found in "
              f"{os.path.basename(MOTIF)}")
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
    head = re.compile(r"^[ \t]*\[" + re.escape(section) + r"\][ \t]*(?:;.*)?$",
                      re.MULTILINE | re.IGNORECASE).search(text)
    if not head:
        print(f"  warning: section [{section}] not found in "
              f"{os.path.basename(MOTIF)}")
        return text, 0
    start = head.end()
    nxt = re.compile(r"^[ \t]*\[[^\]]*\]", re.MULTILINE).search(text, start)
    end = nxt.start() if nxt else len(text)
    body, count = set_key(text[start:end], key, value)
    return text[:start] + body + text[end:], count


def repair_font_files(text):
    """Repoint [Files] font entries that name a file the engine cannot find.

    The motif ships ``font1 = f-4x6.def``, but that file only exists in the
    repository's source ``font/`` folder; motif paths resolve against ``data/``,
    so the engine looked for data/f-4x6.def, did not find it, and reported a
    missing font at every boot for an entry nothing in the motif uses. Anything
    that does not resolve is pointed at the body font, which does.
    """
    head = re.compile(r"^[ \t]*\[Files\][ \t]*$", re.MULTILINE | re.IGNORECASE).search(text)
    if not head:
        return text, 0
    nxt = re.compile(r"^[ \t]*\[[^\]]*\]", re.MULTILINE).search(text, head.end())
    end = nxt.start() if nxt else len(text)
    body = text[head.end():end]

    motif_dir = os.path.dirname(MOTIF)                 # data/ikemen1
    data_dir = os.path.dirname(motif_dir)              # data
    fallback = "ikemen1/fonts/Body.def"
    if not os.path.isfile(os.path.join(data_dir, fallback)):
        return text, 0

    fixed = []

    def repl(match):
        value = match.group(2).strip()
        if not value:
            return match.group(0)
        if any(os.path.isfile(os.path.join(base, value))
               for base in (data_dir, motif_dir)):
            return match.group(0)
        fixed.append(value)
        return match.group(1) + fallback

    body = re.sub(r"(?im)^([ \t]*font[0-9]+[ \t]*=[ \t]*)([^;\r\n]+)([ \t]*;?[^\r\n]*)$",
                  repl, body)
    if not fixed:
        return text, 0
    print(f"  repointed {len(fixed)} missing font file(s) at {fallback}: "
          + ", ".join(sorted(set(fixed))))
    return text[:head.end()] + body + text[end:], len(fixed)


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
    "menu.itemname.menuvideo.resolution = RENDER SIZE\n"
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


# The engine keys the video submenus on the itemname line as written, so a row
# that starts with a tab is a different key ("\tmenu.itemname...") and never
# matches: the resolution list came up empty however many sizes it held. Every
# menuvideo row is therefore forced flush left on each build, whatever wrote it.
MENUVIDEO_ROW = re.compile(r"^[ \t]+(menu\.itemname\.menuvideo\.[^\r\n]*)$",
                           re.MULTILINE)


def dedent_menuvideo(text):
    """Strip leading whitespace from every menu.itemname.menuvideo row."""
    return MENUVIDEO_ROW.subn(r"\1", text)


# The engine builds Options > Video out of the itemname rows of [Option Info]
# only. Rows written into another block - [Title Info] is where these kept
# landing, because the anchor was the title menu's own "options" item - are
# labels for a menu that never asks for them, so the Resolution submenu came up
# with no sizes in it however many rows the file held. The whole table is
# therefore rewritten from RESOLUTION_MENU + WINDOW_MENU and re-inserted right
# after the [Option Info] header on every build, between markers that let the
# next run replace it cleanly instead of stacking a copy each time.
OPTION_HEADER = re.compile(r"^\[Option Info\][^\r\n]*$", re.MULTILINE)
VIDEO_BLOCK = re.compile(
    r"^;[ \t]*>>>[ \t]*video submenu[^\r\n]*(?:\r?\n|$)"
    r".*?"
    r"^;[ \t]*<<<[ \t]*video submenu[^\r\n]*(?:\r?\n|$)",
    re.MULTILINE | re.DOTALL)
VIDEO_ROW = re.compile(r"^[ \t]*menu\.itemname\.menuvideo[^\r\n]*(?:\r?\n|$)",
                       re.MULTILINE)


def place_video_menu(text):
    """Put the video submenu table inside [Option Info], where it is read."""
    if not OPTION_HEADER.search(text):
        return text, 0
    nl = "\r\n" if "\r\n" in text else "\n"
    stripped = VIDEO_BLOCK.sub("", text)
    stripped = VIDEO_ROW.sub("", stripped)
    header = OPTION_HEADER.search(stripped)
    if not header:
        return text, 0
    block = (nl + "; >>> video submenu (generated by tools/build_fonts.py)" + nl
             + RESOLUTION_MENU.rstrip("\r\n").replace("\n", nl) + nl
             + WINDOW_MENU.rstrip("\r\n").replace("\n", nl) + nl
             + "; <<< video submenu" + nl)
    # The header line's own newline terminates the block, and any blank lines
    # left behind by an older copy are dropped, so a rebuild reproduces the file
    # byte for byte instead of growing a blank line each time.
    rest = stripped[header.end():].lstrip("\r\n")
    out = stripped[:header.end()] + block + rest
    return out, (1 if out != text else 0)


def strip_base_footer():
    """Drop the footer rows from the engine's base text table as well.

    The black strip's backdrop rect is drawn from these keys. Leaving them in
    the base table while the motif has none is the half-fixed state that kept a
    bar at the bottom of the menus, so both tables are cleared together.
    """
    if not os.path.isfile(BASE_DEF):
        return 0
    with open(BASE_DEF, "r", encoding="utf-8", errors="surrogateescape",
              newline="") as fh:
        text = fh.read()
    new, dropped = drop_keys(text, DROP_KEYS)
    if dropped:
        with open(BASE_DEF, "w", encoding="utf-8", errors="surrogateescape",
                  newline="") as fh:
            fh.write(new)
    return dropped


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
            new = pattern.sub("%s = %s" % (key, value), text, count=1)
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
        text = text[:anchor.end()] + nl + "%s = %s" % (key, value) + text[anchor.end():]
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
        block = nl + nl.join(row for row in rows)
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
        text = text[:anchor.end()] + nl + "%s = %s" % (key, value) + text[anchor.end():]
        prev = key
        changed += 1
    return text, changed



# The scales a doubled face has to be drawn at to keep its old size on screen.
# Only these two forms are rewritten: anything else is reported, because a scale
# left alone would draw that one label twice as large as it used to be.
SCALE_HALVES = (("1.5, 1.5", "0.75, 0.75"),
                ("1.5,1.5", "0.75, 0.75"),
                ("1, 1", "0.5, 0.5"),
                ("1,1", "0.5, 0.5"))

KEY_LINE = re.compile(r"^(\s*)([A-Za-z0-9_.]+)(\s*=\s*)(.*)$")


def ensure_variant_scales(text, scale="0.75, 0.75"):
    """Give every row that draws one of the doubled faces a scale of its own.

    ``active``, ``selected`` and ``active2`` variants were the rows left out: a
    row without a scale draws at 1.0, i.e. twice the size of the row it sits
    under, which is what made the pause list and the title menu mix two sizes.
    The insert is per block, so the same key name in another screen is untouched.
    """
    lines = text.splitlines(True)
    ours = {"10", "11", "12"}
    cur, rows, seen = "", {}, {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            cur = stripped.lower()
            continue
        m = KEY_LINE.match(stripped)
        if not m or m.lastindex is None or m.lastindex < 4:
            continue
        key = m.group(2).lower()
        if key.endswith(".font") and m.group(4).split(",")[0].strip() in ours:
            rows.setdefault(cur, []).append((i, key[:-len(".font")]))
        elif key.endswith(".scale"):
            seen.setdefault(cur, set()).add(key[:-len(".scale")])
    missing = {}
    for sec, items in rows.items():
        for i, prefix in items:
            if prefix not in seen.get(sec, set()):
                missing[i] = prefix
    if not missing:
        return text, 0
    out = []
    for i, line in enumerate(lines):
        out.append(line)
        if i in missing:
            if not line.endswith("\n"):
                out[-1] = line + "\n"
            indent = line[:len(line) - len(line.lstrip())]
            out.append("%s%s.scale = %s\n" % (indent, missing[i], scale))
    return "".join(out), len(missing)

def halve_paired_scales(text):
    """Halve the .scale of every text that draws one of the doubled faces.

    A bitmap glyph is drawn at its own pixel width times the text scale, so art
    baked at twice the size needs half the scale to land on the same pixels. The
    .def Size and Offset doubled with the art, which keeps the line pitch and the
    engine's glyph shift where they were.
    """
    ours = {"10", "11", "12"}      # Display, Body, DisplayActive
    prefixes = set()
    for line in text.splitlines():
        m = KEY_LINE.match(line)
        if not m:
            continue
        key = m.group(2).lower()
        if key.endswith(".font") and m.group(4).split(",")[0].strip() in ours:
            prefixes.add(key[:-len(".font")])

    out, changed, skipped = [], 0, []
    for line in text.splitlines(True):
        m = KEY_LINE.match(line.rstrip("\r\n"))
        if m:
            key = m.group(2).lower()
            for prefix in prefixes:
                if key == prefix + ".scale":
                    value = m.group(4).strip()
                    for old, new in SCALE_HALVES:
                        if value == old:
                            line = (m.group(1) + m.group(2) + m.group(3) + new +
                                    ("\r\n" if line.endswith("\r\n") else "\n"))
                            changed += 1
                            break
                    else:
                        skipped.append((m.group(2), value))
                    break
        out.append(line)
    have = set()
    for line in text.splitlines():
        m = KEY_LINE.match(line)
        if m and m.group(2).lower().endswith(".scale"):
            have.add(m.group(2).lower()[:-len(".scale")])
    added, out2 = 0, []
    for line in out:
        out2.append(line)
        m = KEY_LINE.match(line.rstrip("\r\n"))
        if m:
            key = m.group(2).lower()
            if (key.endswith(".font")
                    and m.group(4).split(",")[0].strip() in ours
                    and key[:-len(".font")] not in have):
                # 0.75 is the scale every paired row already carries: the face
                # is baked at twice its design size, and a label with no scale
                # drawn the glyphs at their full cell (90px) instead of the 34px
                # row the rest of the screen uses - which read as text that was
                # too big and clipped by whatever box it sat in.
                out2.append(f"{m.group(1)}{m.group(2)[:-len('.font')]}.scale = "
                            f"0.75, 0.75\n")
                added += 1
    if added:
        print(f"  added {added} missing text scale(s) for the doubled faces")
    out = out2
    for key, value in skipped:
        print(f"  kept {key} = {value} (not a known half; check it draws at the "
              f"size it used to)")
    if changed:
        print(f"  halved {changed} text scale(s) to suit the doubled faces")
    return "".join(out)


# The Nakama engine build (RollinJay/IkemenGo-Nakama) has these three title menu
# items; the stock engine has no handler for them. Its menu builder prunes
# itemnames it has no handler for (main.lua, "Remove / recurse submenus"), so the
# NETWORK submenu is exactly as it was before on the engine this game ships.
ONLINE_ITEMS = (
    ("menu.itemname.menunetwork.onlinematch", "QUICK MATCH"),
    ("menu.itemname.menunetwork.onlineranked", "RANKED MATCH"),
    ("menu.itemname.menunetwork.onlinelobby", "ONLINE LOBBIES"),
)


def ensure_online_menu(text):
    """Put the online items at the top of the NETWORK submenu.

    They sit directly after the parent row so they lead the submenu, before
    HOST GAME and JOIN GAME. A row that is already written is left alone, so
    this runs again without adding anything.
    """
    have = sum(1 for key, _ in ONLINE_ITEMS if key in text)
    if have == len(ONLINE_ITEMS):
        return text, 0
    if have:
        print("  warning: only some online itemnames are present; leaving the "
              "NETWORK submenu alone")
        return text, 0
    m = re.search(r"^[ \t]*menu\.itemname\.menunetwork[ \t]*=[^\r\n]*(\r?\n)",
                  text, re.MULTILINE)
    if m is None:
        print("  warning: no menu.itemname.menunetwork row to add the online "
              "items after")
        return text, 0
    eol = m.group(1)
    block = (
        "; Nakama build only. The stock engine prunes itemnames it has no handler" + eol
        + "; for, so this submenu is unchanged on the engine this game ships." + eol
    )
    for key, label in ONLINE_ITEMS:
        block += f"{key} = {label}{eol}"
    end = m.end()
    return text[:end] + block + text[end:], len(ONLINE_ITEMS)


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

    text, _repointed = repair_font_files(text)

    text, res_added = ensure_resolution_menu(text)
    if res_added:            print(f"  rewrote the video resolution list in "
                  f"{os.path.basename(MOTIF)}")

    text, win_added = ensure_window_menu(text)
    if win_added:
        print(f"  wrote the window-size submenu in {os.path.basename(MOTIF)}")

    text, online_added = ensure_online_menu(text)
    if online_added:
        print(f"  wrote {online_added} online item(s) into the NETWORK submenu")

    text, dedented = dedent_menuvideo(text)
    if dedented:
        print(f"  un-indented {dedented} video menu row(s): an indented row "
              f"never matches its itemname, so the submenu stayed empty")

    base_dropped = strip_base_footer()
    if base_dropped:
        print(f"  removed {base_dropped} footer key(s) from "
              f"{os.path.basename(BASE_DEF)} as well")

    text, moved = place_video_menu(text)
    if moved:
        print("  placed the video submenu rows inside [Option Info], the block "
              "the options screen reads them from")

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

    text, dropped_keys = drop_keys(text, DROP_KEYS)
    if dropped_keys:
        print(f"  removed the {dropped_keys}-key menu footer (its dark strip "
              f"was the bar left at the bottom)")

    for section, settings in SECTION_LAYOUT.items():
        for key, value in settings:
            text, count = set_section_key(text, section, key, value)
            if not count:
                text, count = add_section_key(text, section, key, value)
            touched += count
            if not count:
                print(f"  warning: [{section}] {key} not found in "
                      f"{os.path.basename(MOTIF)}")

    text, filled = ensure_variant_scales(text)
    if filled:
        print(f"  gave {filled} unpaired text row(s) the caption scale")
    if text != original:
        text = halve_paired_scales(text)

        with open(MOTIF, "w", encoding="utf-8", errors="surrogateescape", newline="") as fh:
            fh.write(text)
        print(f"  retinted {touched} menu keys and {added} font registrations")
        print(f"updated {os.path.relpath(MOTIF, ROOT)}")
    else:
        print(f"{os.path.relpath(MOTIF, ROOT)} already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
