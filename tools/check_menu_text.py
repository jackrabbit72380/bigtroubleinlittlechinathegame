"""Check that every menu in the game draws its text at the same size.

Two things are checked, because a screen can go large either way:

* the motif's own rows - every ``<something>.font`` in data/ikemen1/system.def
  paired with its ``.scale``, measured as font cell x scale in the motif's
  1920x1080 space and compared with the menu's line (tools/build_fonts.py owns
  that number). This covers all eighteen sections of the screenpack: title,
  select, stage, VS, pause, training pause, options, replay, victory, loading,
  continue, game over, demo, dialogue.
* the Lua screens that draw text themselves - they borrow the pause list's
  sprite, so their scale is a multiple of the menu's, and a bare number in
  ``textImgSetScale`` means one screen kept a copy of the size instead of
  reading it (musicselect drew at 0.75, auraopts at 0.8, devhelp at 1 and
  modnotice at 1.5 of the face, which was the menu's size only while the face
  was baked at 45px). A literal 1 is allowed: that is the reset these modules
  leave the shared sprite in for the pause menu.

Run:  python3 tools/check_menu_text.py
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEF = os.path.join(ROOT, "data", "ikemen1", "system.def")
LUA_DIRS = ("external/script", "external/mods")

sys.path.insert(0, HERE)
from build_fonts import FACE_INK, MENU_INK  # the menu's line, and each face's cell

TOLERANCE = 1.0        # units; a row within this of the menu line is the menu size
SCALE_ARG = re.compile(r"textImgSetScale[,(]\s*[\w.\[\]'\"]+\s*,\s*(-?[0-9.]+)\s*[,)]")


def rows(text):
    """Yield (section, element, font, scale text, cell x scale) for every text row."""
    section, fonts, scales = None, {}, {}
    order = []
    for line in text.split("\n"):
        body = line.split(";")[0].strip()
        if not body:
            continue
        head = re.match(r"^\[([^\]]+)\]", body)
        if head:
            section = head.group(1).strip()
            fonts.setdefault(section, {})
            scales.setdefault(section, {})
            continue
        kv = re.match(r"^([A-Za-z0-9_.]+)\s*=\s*(.*)$", body)
        if not kv or section is None:
            continue
        key, value = kv.group(1).lower(), kv.group(2).strip()
        if key.endswith(".font"):
            root = key[:-len(".font")]
            fonts[section][root] = value.split(",")[0].strip()
            if (section, root) not in order:
                order.append((section, root))
        elif key.endswith(".scale"):
            scales[section][key[:-len(".scale")]] = value
    for section, root in order:
        face = fonts[section][root]
        scale = scales.get(section, {}).get(root)
        cell = FACE_INK.get(face)
        height = None
        if scale is not None and cell is not None:
            try:
                height = cell * float(scale.split(",")[0])
            except ValueError:
                height = None
        yield section, root, face, scale, height


def check_motif(problems):
    with open(DEF, encoding="utf-8-sig", errors="surrogateescape") as handle:
        text = handle.read()
    sections, count = set(), 0
    for section, root, face, scale, height in rows(text):
        sections.add(section)
        count += 1
        if height is None:
            problems.append("system.def %s %s: no size can be read (font %s, "
                            "scale %s)" % (section, root, face, scale))
        elif abs(height - MENU_INK) > TOLERANCE:
            problems.append("system.def %s %s: %.1f units, not the menu's %.1f "
                            "(font %s at %s)"
                            % (section, root, height, MENU_INK, face, scale))
    return len(sections), count


def check_lua(problems):
    drawn = []
    for folder in LUA_DIRS:
        base = os.path.join(ROOT, folder)
        for name in sorted(os.listdir(base)):
            if not name.endswith(".lua"):
                continue
            path = os.path.join(base, name)
            with open(path, encoding="utf-8", errors="surrogateescape") as handle:
                for number, line in enumerate(handle, 1):
                    if "textImgSetScale" not in line:
                        continue
                    drawn.append("%s:%d" % (name, number))
                    for value in SCALE_ARG.findall(line):
                        if abs(float(value) - 1.0) <= 1e-9:
                            continue        # the reset the pause menu expects
                        problems.append("%s:%d draws text at a bare %s - a size that "
                                        "should come from the motif"
                                        % (name, number, value))
    return len(drawn)


def main():
    problems = []
    sections, count = check_motif(problems)
    drawn = check_lua(problems)
    print("menu text: %d row(s) in %d section(s) of system.def measured against the "
          "%.1f-unit menu line, %d Lua draw site(s) checked"
          % (count, sections, MENU_INK, drawn))
    if problems:
        for line in problems:
            print("  FAIL " + line)
        return 1
    if "-v" in sys.argv:
        with open(DEF, encoding="utf-8-sig", errors="surrogateescape") as handle:
            for section, root, face, scale, height in rows(handle.read()):
                size = "-" if height is None else "%.1f" % height
                print("    %-22s %-32s font %-2s scale %-12s %s units"
                      % (section, root, face, scale, size))
    print("  ok  every menu draws its text at the menu's own size")
    return 0


if __name__ == "__main__":
    sys.exit(main())
