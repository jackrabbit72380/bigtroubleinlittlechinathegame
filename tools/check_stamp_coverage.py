"""Fail when a file the Lua reads is missing from data/build_stamp.txt.

The stamp is how the updater decides a folder needs updating: Update and Play.bat
fetches data/build_stamp.txt from main and compares it with the copy beside the
game. A file the Lua opens but the stamp never hashes can therefore change on
main without any folder fetching it - which is what had happened to
data/music.json, data/albums.sff, external/gamecontrollerdb.txt and the external
shaders before they were added.

So: every string literal in the Lua under external/ that names a tracked file has
to be in the stamp, and every getDirectoryFiles() literal has to have all of its
tracked contents in the stamp, except dot-files: external/mods/.keep is git
holding an empty folder open, and main.lua filters that folder to .lua anyway.
Comments are stripped first - options.lua keeps a
stack of modifyGameOption examples commented out, and counting those would
demand stamps for data/common.air and font/debug.def, which the game never reads.

What a static scan cannot see: paths assembled at run time. The track files
listed in data/music.json, a storyboard taken out of the motif, anything built
with ".." or read from gameOption() is invisible here, which is why the sound/
audio is not claimed as covered.

Run:  python3 tools/check_stamp_coverage.py
"""

from __future__ import annotations

import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAMP = os.path.join(ROOT, "data", "build_stamp.txt")
LUA_ROOTS = ("external",)

# The game writes these for the player; they are never shipped and never stamped.
PLAYER_STATE = ("save/", "debug/")

STAMP_LINE = re.compile(r"^([0-9a-f]{64})  (\S.*)$")
LITERAL = re.compile(r"'((?:[^'\\\n]|\\.)*)'|\"((?:[^\"\\\n]|\\.)*)\"")
DIRECTORY_READ = re.compile(r"getDirectoryFiles\(\s*['\"]([^'\"\\\n]+)['\"]")


def strip_comments(src):
    """The source with comments removed and its line numbers kept.

    A literal in a file is not a read: a commented-out example is just text, and
    the engine never opens it.
    """
    out = []
    i, n = 0, len(src)
    quote = None
    while i < n:
        ch = src[i]
        if quote is not None:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(src[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in "'\"":
            quote = ch
            out.append(ch)
            i += 1
            continue
        if src.startswith("--", i):
            opened = re.match(r"--\[(=*)\[", src[i:])
            if opened:
                close = "]" + opened.group(1) + "]"
                end = src.find(close, i + opened.end())
                stop = n if end < 0 else end + len(close)
            else:
                end = src.find("\n", i)
                stop = n if end < 0 else end
            out.append("\n" * src.count("\n", i, stop))
            i = stop
            continue
        opened = re.match(r"\[(=*)\[", src[i:])
        if opened:
            close = "]" + opened.group(1) + "]"
            end = src.find(close, i + opened.end())
            stop = n if end < 0 else end + len(close)
            out.append("\n" * src.count("\n", i, stop))
            i = stop
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def stamp_paths():
    """The hashed paths, plus any stamp line that is not a hash line."""
    covered, broken = {}, []
    with open(STAMP, encoding="utf-8") as fh:
        for number, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            match = STAMP_LINE.match(line)
            if not match:
                broken.append(number)
                continue
            covered[match.group(2)] = match.group(1)
    return covered, broken


def tracked():
    """Every file git knows about: those are the bytes a checkout ships."""
    try:
        raw = subprocess.run(["git", "-C", ROOT, "ls-files", "-z"],
                             stdout=subprocess.PIPE, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        found = set()
        for base, dirs, names in os.walk(ROOT):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for name in names:
                rel = os.path.relpath(os.path.join(base, name), ROOT)
                found.add(rel.replace(os.sep, "/"))
        return found
    return {path for path in raw.decode("utf-8", "replace").split("\0") if path}


def lua_files():
    found = []
    for top in LUA_ROOTS:
        for base, dirs, names in os.walk(os.path.join(ROOT, top)):
            dirs.sort()
            for name in sorted(names):
                if name.lower().endswith(".lua"):
                    rel = os.path.relpath(os.path.join(base, name), ROOT)
                    found.append(rel.replace(os.sep, "/"))
    return sorted(found)


def normalize(text):
    path = text.replace("\\\\", "\\").replace("\\", "/").strip()
    while path.startswith("./"):
        path = path[2:]
    return path


def problems():
    covered, broken = stamp_paths()
    shipped = tracked()
    found = ["data/build_stamp.txt:%d is not a hash line" % number for number in broken]
    if not covered:
        found.append("data/build_stamp.txt lists no file, so nothing is covered")
    reads = folders = 0
    for rel in lua_files():
        with open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as fh:
            code = strip_comments(fh.read())
        reported = set()
        for match in LITERAL.finditer(code):
            text = match.group(1) if match.group(1) is not None else match.group(2)
            path = normalize(text)
            if not path or path.startswith(PLAYER_STATE) or path not in shipped:
                continue
            reads += 1
            if path in covered or path in reported:
                continue
            reported.add(path)
            line = code.count("\n", 0, match.start()) + 1
            found.append("%s:%d opens %s, which data/build_stamp.txt does not hash"
                         % (rel, line, path))
        for match in DIRECTORY_READ.finditer(code):
            folder = normalize(match.group(1)).rstrip("/") + "/"
            if folder.startswith(PLAYER_STATE):
                continue
            inside = sorted(path for path in shipped
                            if path.startswith(folder)
                            and not path.rsplit("/", 1)[-1].startswith("."))
            if not inside:
                continue
            folders += 1
            line = code.count("\n", 0, match.start()) + 1
            for path in inside:
                if path not in covered:
                    found.append("%s:%d lists %s, which holds %s, and the stamp "
                                 "does not hash it" % (rel, line, folder, path))
    return found, (len(covered), reads, folders)


def main():
    found, (hashed, reads, folders) = problems()
    for problem in found:
        print("FAIL " + problem)
    if not found:
        print("stamp coverage: clean (%d file(s) hashed, %d literal read(s), "
              "%d folder read(s))" % (hashed, reads, folders))
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
