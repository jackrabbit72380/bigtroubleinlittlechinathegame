"""Point the screenpack's menu music at the tracks that exist in sound/.

Ikemen GO reads menu BGM paths from the [Music] block of data/ikemen1/system.def,
but that block ships with the engine, hard-coded to sound/Title.mp3,
sound/Select.mp3, ... and is replaced every time the engine data is staged into
this repo. So instead of hand-editing the 2,700-line motif, the paths are derived
from the files actually present:

    sound/Title.ogg     -> title.bgm
    sound/Select.ogg    -> select.bgm
    sound/Versus.ogg    -> vs.bgm
    sound/Winner.ogg    -> victory.bgm
    sound/Continue.ogg  -> continue.bgm
    sound/Options.ogg   -> option.bgm
    sound/Replay.ogg    -> replay.bgm
    sound/Results.ogg   -> results.bgm
    sound/Hiscore.ogg   -> hiscore.bgm

Stems are matched case-insensitively. Only extensions the engine can decode are
eligible (it picks its decoder from the extension), and when several encodings of
one track exist the first of EXTS wins. A slot with a matching file points at it;
a slot without one still names the conventional path (sound/Title.ogg and so on),
so a player who drops their own track into sound/ gets music without editing
anything. Volume, loop and loop-point lines are never touched.

Stage fight music is separate: it lives in [Music] bgmusic of each stages/*.def.

Run:  python3 tools/build_music.py
"""

from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUND_DIR = os.path.join(ROOT, "sound")
MOTIF = os.path.join(ROOT, "data", "ikemen1", "system.def")

# Decodable extensions, most preferred first. Ikemen GO switches decoder on the
# file extension, so an .opus/.m4a/.aac track is silently ignored no matter what
# it contains.
EXTS = ("ogg", "mp3", "flac", "wav", "mid", "midi")
UNSUPPORTED = ("opus", "m4a", "aac", "wma", "aiff", "aif", "mp4", "mod", "xm", "it", "s3m")

SLOTS = (
    ("Title", "title.bgm"),
    ("Select", "select.bgm"),
    ("Versus", "vs.bgm"),
    ("Winner", "victory.bgm"),
    ("Continue", "continue.bgm"),
    ("Options", "option.bgm"),
    ("Replay", "replay.bgm"),
    ("Results", "results.bgm"),
    ("Hiscore", "hiscore.bgm"),
)


def sound_files():
    if not os.path.isdir(SOUND_DIR):
        return []
    return sorted(os.listdir(SOUND_DIR))


def find_track(stem, files):
    """Return 'sound/<name>' for the best decodable file with this stem."""
    for ext in EXTS:
        for name in files:
            base, dot, found = name.rpartition(".")
            if not dot:
                continue
            if base.lower() == stem.lower() and found.lower() == ext:
                return f"sound/{name}"
    return None


def set_key(text, key, value):
    """Replace the value of `key = ...`, keeping its trailing comment."""
    pattern = re.compile(
        r"^(?P<pre>[ \t]*" + re.escape(key) + r"[ \t]*=[ \t]*)(?P<val>[^;\r\n]*?)"
        r"[ \t]*(?P<comment>;.*)?$",
        re.MULTILINE,
    )

    def repl(match):
        comment = match.group("comment")
        return match.group("pre") + value + (f" {comment}" if comment else "")

    return pattern.subn(repl, text)


def main():
    files = sound_files()

    # A track the engine cannot decode is the most common way to lose an hour:
    # say so plainly instead of shipping silence.
    bad = [f for f in files if f.rpartition(".")[2].lower() in UNSUPPORTED]
    for name in bad:
        ext = name.rpartition(".")[2].lower()
        print(f"  warning: sound/{name} is .{ext}, which Ikemen GO cannot decode "
              f"(use {'/'.join(EXTS[:5])})")

    if not os.path.isfile(MOTIF):
        print(f"missing motif: {MOTIF}", file=sys.stderr)
        return 1

    with open(MOTIF, "r", encoding="utf-8", errors="surrogateescape") as fh:
        original = fh.read()

    text = original
    for stem, key in SLOTS:
        found = find_track(stem, files)
        path = found or f"sound/{stem}.ogg"
        text, count = set_key(text, key, path)
        if count == 0:
            print(f"  warning: {key} not found in {os.path.basename(MOTIF)}")
            continue
        print(f"  {key} = {path}" + ("" if found else " (track not present yet)"))

    if text != original:
        with open(MOTIF, "w", encoding="utf-8", errors="surrogateescape", newline="") as fh:
            fh.write(text)
        print(f"updated {os.path.relpath(MOTIF, ROOT)}")
    else:
        print(f"{os.path.relpath(MOTIF, ROOT)} already up to date")

    if not any(find_track(stem, files) for stem, _ in SLOTS):
        print("note: no menu tracks in sound/ yet; every slot still names its conventional\n"
              "      filename, so dropping sound/Title.ogg in is enough to start the music")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
