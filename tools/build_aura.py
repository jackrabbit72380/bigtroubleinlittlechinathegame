"""Install the aura module and its pause menu row.

`tools/aura.zss` is the source of truth for the glow - the third-party module
with its glowing state rewritten to read the maps that `external/mods/
auraopts.lua` fills in. The asset build replaces `data/` with the engine's
stock copy, so the shipped copy is written here on every build rather than
being tracked by hand.

This also declares `menu.itemname.aura` in the pause menus: the menu is built
from those keys in the motif, and a hand edit there is lost with the next asset
build. The row does nothing on its own - the mod registers the `aura` handler
that draws the screen. Both halves are needed.

Run:  python3 tools/build_aura.py
"""

import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MOTIF = os.path.join(ROOT, "data", "ikemen1", "system.def")
SOURCE = os.path.join(HERE, "aura.zss")
TARGET = os.path.join(ROOT, "data", "aura.zss")

ENTRY = "menu.itemname.aura = Aura"
SECTIONS = ("[Pause Menu]", "[Training Pause Menu]")
EXISTING = re.compile(r"^\s*menu\.itemname\.aura\s*=", re.IGNORECASE)


def install_module():
    """Copy the module into data/, keeping its CRLF line endings."""
    if not os.path.isfile(SOURCE):
        raise SystemExit("tools/aura.zss is missing")
    with open(SOURCE, "rb") as handle:
        blob = handle.read()
    if b"[StateDef +1]" not in blob or b"[Function glow" not in blob:
        raise SystemExit("tools/aura.zss does not look like the aura module")
    if os.path.isfile(TARGET):
        with open(TARGET, "rb") as handle:
            if handle.read() == blob:
                return False
    with open(TARGET, "wb") as handle:
        handle.write(blob)
    return True


def patch_menu(text):
    lines = text.splitlines()
    out = []
    current = None
    has = {name: False for name in SECTIONS}
    added = []

    def close_section():
        if current in SECTIONS and not has[current]:
            out.append(ENTRY)
            has[current] = True
            added.append(current)

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            close_section()
            current = stripped
        if current in SECTIONS and EXISTING.match(line):
            has[current] = True
            line = ENTRY
        out.append(line)
    close_section()
    return "\n".join(out) + "\n", added


def main():
    changed = install_module()
    print("data/aura.zss %s" % ("written" if changed else "already current"))

    if not os.path.isfile(MOTIF):
        print("no %s - the pause menu row was not added" % MOTIF)
        return 0
    with open(MOTIF, "r", encoding="utf-8", errors="replace") as handle:
        original = handle.read()
    text, added = patch_menu(original)
    if text == original:
        print("pause menu already offers the Aura screen")
        return 0
    with open(MOTIF, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("added the Aura row to %s" % (", ".join(sorted(set(added))) or "nothing"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
