"""Write data/build_stamp.txt: a one-line-per-file fingerprint of the shipped data.

The updater used to decide "already up to date" from a recorded commit hash, which
is only true if the previous run actually wrote the files. One interrupted run, one
file held open by the game or a scanner, and the folder keeps a hash it does not
match - and every later launch says "up to date", starts the old build, and the
engine prints warnings that were fixed long ago.

So the build leaves a stamp: the SHA-256 of the files whose content decides whether
a folder is current. Update and Play.bat fetches this file from main (a few KB) and
compares it with the copy in the folder. Different stamp means the folder is not
main, whatever applied.txt says, and the update runs.

Run:  python3 tools/build_stamp.py        (build_all.py calls it last)
"""

from __future__ import annotations

import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "build_stamp.txt")

# Everything the launch console depends on: the motif, the HUD, the roster, the
# settings template and the Lua that reads them.
FILES = (
    "data/ikemen1/system.def",
    "data/system.base.def",
    "data/fight.def",
    "data/select.def",
    "data/ikemen1/logo.def",
    "data/ikemen1/credits.def",
    "external/script/start.lua",
    "external/script/options.lua",
    "external/mods/musicselect.lua",
)


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
        digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
        lines.append(f"{digest}  {rel}")
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"  data/build_stamp.txt: {len(FILES) - missing} file(s)"
          + (f", {missing} missing" if missing else ""))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
