"""Add the Developer Keys entry to the pause menus.

The pause menu is built from `menu.itemname.*` keys in the motif, so the item has
to be declared in data/ikemen1/system.def. The asset build replaces data/ with the
engine's stock copy on every run, so a hand edit there is lost: this script
re-applies it, which is what tools/build_all.py calls.

The item itself does nothing on its own - external/mods/devhelp.lua registers the
`devkeys` handler that draws the screen. Both halves are needed.

Run:  python3 tools/build_devhelp.py
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MOTIF = os.path.join(ROOT, "data", "ikemen1", "system.def")

ENTRY = "menu.itemname.devkeys = Developer Keys"
SECTIONS = ("[Pause Menu]", "[Training Pause Menu]")

# Anything already declaring the key, so a second run cannot add it twice.
EXISTING = re.compile(r"^\s*menu\.itemname\.devkeys\s*=", re.IGNORECASE)


def patch(text):
    """Append ENTRY to each pause menu section that does not declare it yet."""
    lines = text.splitlines()
    out = []
    current = None
    added = []
    in_section = {name: False for name in SECTIONS}
    has_key = {name: False for name in SECTIONS}

    def close_section():
        if current in SECTIONS and not has_key[current]:
            out.append(ENTRY)
            has_key[current] = True
            added.append(current)

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            close_section()
            current = stripped
            if current in SECTIONS:
                in_section[current] = True
        if current in SECTIONS and EXISTING.match(line):
            has_key[current] = True
        out.append(line)
    close_section()

    return "\n".join(out) + "\n", added, in_section


def main():
    if not os.path.isfile(MOTIF):
        print("no %s - nothing to patch" % MOTIF)
        return 0
    with open(MOTIF, "r", encoding="utf-8", errors="replace") as handle:
        original = handle.read()

    text, added, seen = patch(original)

    missing = [name for name in SECTIONS if not seen[name]]
    if missing:
        print("motif has no %s section; the pause menu entry was not added"
              % ", ".join(missing))
        return 0

    if text == original:
        print("pause menu already offers Developer Keys")
        return 0

    with open(MOTIF, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("added the Developer Keys entry to %s" % (", ".join(added) or "nothing"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
