"""Write data/build_stamp.txt: a one-line-per-file fingerprint of the shipped data.

The updater decides "already up to date" by fetching this file from main and
comparing it with the copy in the folder. Different stamp means the folder is not
main, whatever applied.txt or the recorded commit says, and the update runs.

Two things it got wrong before:

  * it hashed a hand-kept list, and menu.lua and debug.lua were both missing from
    it - the two files that draw the pause menu and register the debug keys - so a
    fix to either would have shipped without forcing the folder to update;
  * it hashed the working tree, and this repository is normally built with work
    in progress in it, so the recorded hash could describe bytes no shipped copy
    of the file ever has.

So the Lua is discovered rather than listed, and each file is hashed from its
committed blob when git has one.

Run:  python3 tools/build_stamp.py        (build_all.py calls it last)
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "build_stamp.txt")

# Everything the launch console depends on: the motif, the HUD, the roster, the
# settings template, the music browser's album list and cover art, and the
# controller database external/script/options.lua hands the engine.
#
# music.json and albums.sff are read by external/mods/musicselect.lua, so an
# update that changed only one of them has to count as an update too - while
# music.json was left out, a folder holding an older album list compared equal
# to main everywhere that list is used. The mapping database is the same story
# from options.lua: Config.GamepadMappings points at it, so a controller that
# mapped before a change and not after is an update that never arrived.
DATA_FILES = (
    "data/ikemen1/system.def",
    "data/system.base.def",
    "data/fight.def",
    # the motif's own sound bank: external/mods/rainthunder.lua plays the rain
    # stage's rumble out of it, so a re-painted sample has to count as an update
    "data/system.snd",
    "data/select.def",
    "data/music.json",
    "data/retired.txt",
    "data/albums.sff",
    "data/ikemen1/logo.def",
    "data/ikemen1/credits.def",
    "external/gamecontrollerdb.txt",
)


def lua_scripts():
    """Every Lua script under external/, in a stable order."""
    found = []
    for base, dirs, names in os.walk(os.path.join(ROOT, "external")):
        dirs.sort()
        for name in sorted(names):
            if name.lower().endswith(".lua"):
                rel = os.path.relpath(os.path.join(base, name), ROOT)
                found.append(rel.replace(os.sep, "/"))
    return sorted(found)


def shader_files():
    """Every external shader, in a stable order.

    options.lua builds the shader menu by enumerating external/shaders and puts
    the chosen names into Video.ExternalShaders, so whatever ships there is
    something the game can be told to load. The list is discovered for the same
    reason the Lua is: a shader nobody remembered to add would otherwise be
    invisible to the update.
    """
    found = []
    for base, dirs, names in os.walk(os.path.join(ROOT, "external", "shaders")):
        dirs.sort()
        for name in sorted(names):
            rel = os.path.relpath(os.path.join(base, name), ROOT)
            found.append(rel.replace(os.sep, "/"))
    return sorted(found)


FILES = DATA_FILES + tuple(lua_scripts()) + tuple(shader_files())


def content(rel):
    """The bytes that will be shipped: the committed blob when git has one."""
    try:
        out = subprocess.run(
            ["git", "-C", ROOT, "show", "HEAD:" + rel],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return out.stdout
    except Exception:
        with open(os.path.join(ROOT, rel.replace("/", os.sep)), "rb") as handle:
            return handle.read()


def main():
    lines = [
        "# Big Trouble in Little China - data stamp. Written by tools/build_stamp.py.",
        "# Update and Play.bat compares this file with main's copy: a difference means",
        "# the folder needs an update, whatever the recorded commit says.",
    ]
    missing = 0
    for rel in FILES:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.isfile(path):
            lines.append(f"missing  {rel}")
            missing += 1
            continue
        digest = hashlib.sha256(content(rel)).hexdigest()
        lines.append(f"{digest}  {rel}")
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"  data/build_stamp.txt: {len(FILES) - missing} file(s)"
          + (f", {missing} missing" if missing else ""))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
