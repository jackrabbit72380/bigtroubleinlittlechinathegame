"""Add the Developer Keys and Music entries to the pause menus.

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

ENTRIES = (
    "menu.itemname.devkeys = Developer Keys",
    # MUSIC. The browser itself is external/mods/musicselect.lua; this is the row
    # that opens it, so the track can be picked from a paused fight as well as
    # from the title menu.
    "menu.itemname.music = MUSIC",
)
SECTIONS = ("[Pause Menu]", "[Training Pause Menu]")

# Anything already declaring one of the keys, so a second run cannot add twice.
EXISTING = re.compile(r"^\s*menu\.itemname\.(devkeys|music)\s*=", re.IGNORECASE)


def patch(text):
    """Append every ENTRY a pause menu section does not declare yet."""
    lines = text.splitlines()
    out = []
    current = None
    added = []
    in_section = {name: False for name in SECTIONS}
    has_key = {name: set() for name in SECTIONS}

    def close_section():
        if current in SECTIONS:
            for entry in ENTRIES:
                key = entry.split("=", 1)[0].strip().lower()
                if key not in has_key[current]:
                    out.append(entry)
                    has_key[current].add(key)
                    added.append(current)

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            close_section()
            current = stripped
            if current in SECTIONS:
                in_section[current] = True
        if current in SECTIONS:
            m = EXISTING.match(line)
            if m:
                has_key[current].add("menu.itemname." + m.group(1).lower())
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
        print("pause menu already offers Developer Keys and Music")
        return 0

    with open(MOTIF, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("added the pause menu entries to %s"
          % (", ".join(sorted(set(added))) or "nothing"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
