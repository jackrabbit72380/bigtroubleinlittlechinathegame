"""Set every caption in the motif in one face, at one size.

The game had four faces doing the same job. The motif drew its headings in Body,
its menus in Display, its ranking tables in Menu2 and its countdown in the Timer
face, at scales of 1.5, 1.0 and 0.9 - so "PLAYER 1" and the fighter's name under
the grid were two sizes of two faces, and every screen disagreed with the next.
The fight screen's captions are Display (tools/build_fight_text.py), so the motif
joins them: Display for passive text, DisplayActive for anything lit, and one
size - 1.0 of the motif's own 1920x1080 space - for all of it.

Two places need more than the swap:

  * the select screen's player-one name was centred on x=75, so a name of any
    length started left of the screen edge and its first letter was cut off. It
    is left-aligned on the same x as the player-two name is right-aligned, which
    is also how the wins caption is placed in the fight.
  * a caption with no scale line of its own - the victory screen's name and win
    quote, the title menu's rows, the training pause list, the results screens -
    was left at 1.0, i.e. a third smaller than the same face everywhere else, so
    the size is written for those too, on the element their lit variants inherit
    theirs from.

The asset build replaces data/ with the engine's stock copy on every run, so this
is re-applied there instead of being a hand edit. Run it after the tools that
rewrite the motif (build_devhelp.py adds menu entries to it):

    python3 tools/build_text_faces.py
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MOTIF = os.path.join(ROOT, "data", "ikemen1", "system.def")

FACE = "10"          # Display
FACE_LIT = "12"      # DisplayActive: the same face, in its lit bank
# The caption size, in the motif's own 1920x1080 space. The fight screen's
# captions are 67.5 units tall on a 1080p screen, which used to be 1.5 of the
# Display cell (45px). tools/build_fonts.py bakes that cell at twice the pixels
# now so 4K gets real detail instead of stretched art, so the scale is measured
# off the shipped face rather than written down: 67.5 / cell. One size on paper,
# one size on the glass, whatever the face is baked at.
CAPTION_UNITS = 67.5


def caption_size():
    """The text scale that draws the caption face CAPTION_UNITS tall."""
    path = os.path.join(ROOT, "data", "ikemen1", "fonts", "Display.def")
    cell = 45.0
    if os.path.isfile(path):
        with open(path, encoding="utf-8-sig", errors="surrogateescape") as fh:
            for line in fh:
                if line.strip().lower().startswith("size"):
                    try:
                        cell = float(line.split("=", 1)[1].split(",")[1]) or 45.0
                    except (IndexError, ValueError):
                        pass
                    break
    scale = CAPTION_UNITS / cell
    return "%g, %g" % (scale, scale)


SIZE = caption_size()
ROW = "0, 74"        # row pitch: the 67.5 cell plus air, or the rows collide

# namespace.font = face, bank, alignment, r, g, b[, extra...]
FONT = re.compile(r"^(\s*)([A-Za-z0-9_*.]+)\.font(\s*=\s*)(-?\d+)(\s*,[^\r\n]*)?$")
SCALE = re.compile(r"^(\s*)([A-Za-z0-9_*.]+)\.scale(\s*=\s*)([^\r\n]*)$")


def is_lit(key):
    return "active" in key.lower() or "selected" in key.lower()


def patch(text):
    """Swap the face and the size of every captioned element, section by section."""
    lines = text.split("\n")
    faces = 0
    sizes = 0
    changed = []

    # which elements in each section are text (have a .font), so .scale only
    # touches those - portrait.scale, cursor.scale and the rest are geometry
    textkeys = {}
    section = "(top)"
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped
            continue
        m = FONT.match(line.split(";")[0].rstrip()) if not stripped.startswith(";") else None
        if m:
            textkeys.setdefault(section, set()).add(m.group(2).lower())

    section = "(top)"
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped
            continue
        if stripped.startswith(";"):
            continue
        body = line.split(";", 1)[0]
        m = FONT.match(body.rstrip())
        if m:
            want = FACE_LIT if is_lit(m.group(2)) else FACE
            if m.group(4) != want:
                rest = m.group(5) or ""
                lines[i] = "%s%s.font%s%s%s" % (m.group(1), m.group(2), m.group(3),
                                                want, rest)
                faces += 1
                changed.append("%s.font" % m.group(2))
            continue
        s = SCALE.match(body.rstrip())
        if s and s.group(2).lower() in textkeys.get(section, set()):
            value = s.group(4).strip()
            if value.replace(" ", "") != SIZE.replace(" ", ""):
                lines[i] = "%s%s.scale%s%s" % (s.group(1), s.group(2), s.group(3), SIZE)
                sizes += 1
                changed.append("%s.scale" % s.group(2))

    return "\n".join(lines), faces, sizes, changed


# A menu list is captions stacked at a fixed pitch, so the pitch grows with them.
SPACING = re.compile(r"^(\s*)([A-Za-z0-9_*.]+)\.spacing(\s*=\s*)(-?\d+)\s*,\s*(-?\d+)[^\r\n]*$")


def patch_spacing(text):
    """Give every menu list room for the taller rows."""
    lines = text.split("\n")
    made = 0
    for i, line in enumerate(lines):
        if line.strip().startswith(";"):
            continue
        m = SPACING.match(line.split(";")[0].rstrip())
        if not m:
            continue
        x, y = int(m.group(4)), int(m.group(5))
        # a zero y is a row that runs along x (team value markers, order icons),
        # not a stack of captions - it must keep its own pitch
        if y == 0 or abs(y) >= 74:
            continue
        lines[i] = "%s%s.spacing%s%d, %s" % (m.group(1), m.group(2), m.group(3),
                                             x, ROW.split(", ")[1]
                                             if y > 0 else "-" + ROW.split(", ")[1])
        made += 1
    return "\n".join(lines), made


# The select screen's corner names: p1 was centred and ran off the left edge.
NAMES = (
    # key                  value
    ("p1.name.font", "10, 0, 1, 255, 228, 140"),
    ("p2.name.font", "10, 0, -1, 255, 170, 96"),
)


def place_names(text):
    """Left- and right-align the two corner names on their own offsets."""
    start = text.find("[Select Info]")
    if start < 0:
        return text, False
    nxt = re.compile(r"^\[", re.M).search(text, start + len("[Select Info]"))
    end = nxt.start() if nxt else len(text)
    head, body, tail = text[:start], text[start:end], text[end:]
    made = False
    for key, value in NAMES:
        pattern = re.compile(r"^([ \t]*" + re.escape(key) + r"[ \t]*=[^\r\n]*)$", re.M)
        line = "%s = %s" % (key, value)
        if pattern.search(body):
            new = pattern.sub(line, body, count=1)
        else:
            new = body.rstrip("\r\n") + "\n" + line + "\n"
        if new != body:
            made = True
        body = new
    return head + body + tail, made


# The bottom row: the two corner names and the stage caption, on y=1035. A 67.5
# cell there ends at 1102, past the 1080 edge, so the ink at the bottom of every
# letter was being cut. Lifted by the growth in the cell height.
BOTTOM = (("p1.name.offset", "75, 1005"),
          ("p2.name.offset", "1845, 1005"),
          ("stage.pos", "960, 120"))


def place_bottom_row(text):
    start = text.find("[Select Info]")
    if start < 0:
        return text, False
    nxt = re.compile(r"^\[", re.M).search(text, start + len("[Select Info]"))
    end = nxt.start() if nxt else len(text)
    head, body, tail = text[:start], text[start:end], text[end:]
    made = False
    for key, value in BOTTOM:
        pattern = re.compile(r"^([ \t]*" + re.escape(key) + r"[ \t]*=[^\r\n]*)$", re.M)
        if pattern.search(body):
            body = pattern.sub("%s = %s" % (key, value), body, count=1)
            made = True
    return head + body + tail, made


# The lists that the taller rows no longer fit. A row is 74 apart now instead of
# 46-60, so the three screens whose blocks were sized for the small pitch lost
# their last rows off the bottom of the frame. Each entry keeps the block on the
# frame: the pause lists move up under their heading, the options list starts
# higher under its title, and the title list shows two fewer rows at once (it
# already scrolled - the wordmark needs the top half of the screen).
# The title list is the one block that cannot use the caption size: its room is
# the empty band the painted backdrop leaves under the wordmark (y 344..686 on a
# 1080 frame), and nine rows of a 77px face at 0.75 do not fit in 342px. 0.46
# draws the same face at 35px with ~3px between rows, which is what lets the list
# sit inside that hole instead of printing across the fighters. Written here
# because patch() has already forced every text scale to the caption size by the
# time the screens are fitted.
TITLE_SCALE = "0.46, 0.46"

FIT = {
    "[Pause Menu]": {"title.offset": "960, 118", "menu.pos": "960, 190"},
    "[Training Pause Menu]": {"title.offset": "960, 118", "menu.pos": "960, 190"},
    "[Option Info]": {"menu.pos": "945, 96"},
    # The pitch is restated here because patch_spacing() has already forced the
    # caption pitch on this block; title rows are 35px of ink, not 67.5.
    "[Title Info]": {"menu.window.visibleitems": "9",
                     "menu.item.spacing": "0, 38",
                     "menu.item.scale": TITLE_SCALE,
                     "menu.item.active.scale": TITLE_SCALE},
}


def fit_lists(text):
    """Re-seat the lists whose rows now run past the bottom of the frame."""
    lines = text.split("\n")
    section = "(top)"
    made = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped
            continue
        if section not in FIT or stripped.startswith(";"):
            continue
        kv = re.match(r"^(\s*)([A-Za-z0-9_.]+)(\s*=\s*)([^\r\n]*)$", line)
        if not kv:
            continue
        want = FIT[section].get(kv.group(2).lower())
        if want is None:
            continue
        lines[i] = "%s%s%s%s" % (kv.group(1), kv.group(2), kv.group(3), want)
        made.append("%s %s" % (section, kv.group(2)))
    return "\n".join(lines), made


# A caption's lit variants take their size from the element they belong to
# (menu.item.active.font draws at menu.item.scale), so it is the root that needs
# the number, once.
VARIANTS = (".selected.active", ".active2", ".active", ".selected", ".done",
            ".conflict")


FONT_LINE = re.compile(r"^(\s*)([A-Za-z0-9_*.]+)\.font\s*=")


def add_sizes(text):
    """Write the caption size on every element that only ever had a face."""
    lines = text.split("\n")
    section = "(top)"
    keys = {}
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped
            keys.setdefault(section, set())
            continue
        if stripped.startswith(";"):
            continue
        m = re.match(r"^\s*([A-Za-z0-9_.]+)\s*=", line)
        if m and section in keys:
            keys[section].add(m.group(1).lower())

    out, section, added = [], "(top)", []
    pending = {}   # section -> {root: number of the font line that owns it}
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped
            out.append(line)
            continue
        m = FONT_LINE.match(line.split(";")[0].rstrip()) if not stripped.startswith(";") else None
        out.append(line)
        if not m:
            continue
        base = m.group(2).lower()
        root = base
        for suffix in VARIANTS:
            if root.endswith(suffix):
                root = root[:-len(suffix)]
                break
        have = keys.get(section, set())
        if root + ".scale" in have or base + ".scale" in have:
            continue
        if root + ".font" in have and base != root:
            continue    # the root's own line is where the size goes
        out.append("%s%s.scale = %s" % (m.group(1), root, SIZE))
        added.append("%s %s" % (section, root + ".scale"))
    return "\n".join(out), added


def main():
    if not os.path.isfile(MOTIF):
        print("no %s - nothing to patch" % MOTIF)
        return 0
    with open(MOTIF, encoding="utf-8", errors="replace", newline="") as handle:
        original = handle.read()

    text, faces, sizes, changed = patch(original)
    text, sized = add_sizes(text)
    text, spaced = patch_spacing(text)
    text, names = place_names(text)
    text, lifted = place_bottom_row(text)
    text, fitted = fit_lists(text)

    if text == original:
        print("motif captions already in the Display face at one size")
        return 0

    with open(MOTIF + ".tmp", "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.replace(MOTIF + ".tmp", MOTIF)
    print("motif text: %d face(s), %d size(s), %d row pitch(es) set%s%s"
          % (faces, sizes, spaced, ", corner names aligned" if names else "",
             ", bottom row lifted" if lifted else ""))
    if sized:
        print("  sized %d caption(s) that had no scale: %s" % (len(sized), ", ".join(sized)))
    if fitted:
        print("  re-seated %d list block(s): %s" % (len(fitted), ", ".join(fitted)))
    return 0


# tools/build_fonts.py now bakes the Display and Body faces at twice their pixels
# so a 4K render samples real detail instead of stretched art. A bitmap glyph is
# drawn at its own pixel size times the text scale, so every text in the fight HUD
# that draws one of those faces needs half the scale to keep its old size on
# screen. The paired .font key says which texts those are; the round banner and the
# demo caption are named outright because their scale sits on a parent key.
FIGHT = os.path.join(ROOT, "data", "fight.def")
DOUBLED_FACES = ("Display.def", "Body.def", "DisplayActive.def")
DOUBLED_PREFIXES = ("round.", "mode.")
HALVES = {"1.5,1.5": "0.75, 0.75", "1,1": "0.5, 0.5", "2,2": "1, 1"}
# The round banner is the one text whose design size is 2, so it is halved to 1
# and left there: a second pass that saw 1 and halved again would shrink it.
BANNER = ("round.",)


def halved(key, value):
    """The scale this text needs once its face is baked at double pixels."""
    plain = value.replace(" ", "")
    if key.startswith(BANNER):
        return "1, 1" if plain == "2,2" else value
    return HALVES.get(plain, value)
FACE_LINE = re.compile(r"^\s*font(\d+)\s*=\s*(\S+)", re.M)
KEY_LINE = re.compile(r"^(\s*)([A-Za-z0-9_.]+)(\s*=\s*)(.*)$")


def patch_fight():
    """Halve the fight HUD's text scales for the doubled faces."""
    if not os.path.isfile(FIGHT):
        print("fight.def missing: %s" % FIGHT)
        return 1
    with open(FIGHT, encoding="utf-8-sig", errors="surrogateescape", newline="") as handle:
        original = handle.read()
    indices = {n for n, face in FACE_LINE.findall(original)
               if os.path.basename(face) in DOUBLED_FACES}
    prefixes = set()
    for line in original.splitlines():
        m = KEY_LINE.match(line)
        if m and m.group(2).lower().endswith(".font"):
            if m.group(4).split(",")[0].strip() in indices:
                prefixes.add(m.group(2).lower()[:-len(".font")])
    out, changed = [], 0
    for line in original.splitlines(True):
        m = KEY_LINE.match(line.rstrip("\r\n"))
        if m:
            key = m.group(2).lower()
            if key.endswith(".scale") and (key[:-len(".scale")] in prefixes
                                           or key.startswith(DOUBLED_PREFIXES)):
                value = m.group(4).strip()
                new = halved(key, value)
                if new != value:
                    line = (m.group(1) + m.group(2) + m.group(3) + new +
                            ("\r\n" if line.endswith("\r\n") else "\n"))
                    changed += 1
        out.append(line)
    text = "".join(out)
    if text != original:
        with open(FIGHT + ".tmp", "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(FIGHT + ".tmp", FIGHT)
        print("fight HUD: halved %d text scale(s) for the doubled faces" % changed)
    else:
        print("fight HUD scales already suit the doubled faces")
    return 0


if __name__ == "__main__":
    sys.exit(main() or patch_fight())
