"""Write web/files.json, the file list the browser build reads the game through.

mugen-js reads a MUGEN tree through a FileSource: it asks for a JSON array of
every path in the tree, then fetches the ones it needs. This checkout *is* that
tree - chars/, stages/, data/, font/, sound/ - so the list is generated from it
and the web version shares every asset with the desktop one instead of shipping
a second copy of 850 MB of sprites.

Nothing outside the game's own folders is listed: tools/, docs/, web/ and the
workflows are not content, and the engine would only waste a fetch on them.

Run:  python3 tools/build_web_files.py
"""

from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "web", "files.json")

# The folders the engine reads. A stage's own .def and its sprites live in
# stages/, a character's in chars/, and everything a motif points at is under
# data/ or font/; sound/ is the music the defs name.
TREES = ("chars", "stages", "data", "font", "sound", "video")

# A file the desktop build keeps but the browser must not read: the data stamp is
# build bookkeeping, not art, and the engine's own cache folders are not content.
SKIP_FILES = {"data/build_stamp.txt"}
SKIP_DIRS = {"__pycache__", ".git"}


def collect():
    files = []
    for tree in TREES:
        base = os.path.join(ROOT, tree)
        if not os.path.isdir(base):
            continue
        for folder, dirs, names in os.walk(base):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for name in names:
                rel = os.path.relpath(os.path.join(folder, name), ROOT)
                rel = rel.replace(os.sep, "/")
                if rel in SKIP_FILES or name.startswith("."):
                    continue
                files.append(rel)
    return sorted(files)


def main():
    files = collect()
    body = json.dumps(files, indent=0, ensure_ascii=False) + "\n"
    old = None
    if os.path.isfile(OUT):
        with open(OUT, "r", encoding="utf-8") as fh:
            old = fh.read()
    if old == body:
        print(f"web/files.json already lists {len(files)} file(s)")
        return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    print(f"web/files.json: {len(files)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
