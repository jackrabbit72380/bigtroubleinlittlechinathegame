"""Point the screenpack's menu music at the tracks that exist in sound/, and
build the music select's data from the albums in that folder.

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

Music select albums
-------------------
Every directory directly under sound/ is an album. Its audio files become the
album's track list and its boxFront.png (any case) becomes the cover art:

    sound/Big Trouble in Little China OST Movie Version/
        1 - Prologue.ogg
        boxFront.png
        Big Trouble in Little China OST Movie.metadata.pegasus.txt

That metadata file is what an album pack normally ships with, and it is read for
two things the filenames cannot give: the album's own playing order (one `game:`
entry per track, in order) and the track titles to print (the `game:` line, so
"1 - Prologue" is shown as written rather than rebuilt from the filename). Its
`assets.boxFront:` line is used for the cover when that file exists, and `file:`
paths are resolved leniently - from the repo root, inside the album folder, in
sound/ itself, or one folder down - so a pack written for `sound/x.ogg` still
works from the album directory, and a name that differs only in spacing or
punctuation still finds its file. Tracks in the folder but not in the metadata are
appended at the end rather than dropped, and a track the metadata lists without a
file on disk is reported and skipped.

The result lands in data/music.json for the browser
(external/mods/musicselect.lua) with a 1-based Order per track, and each cover is
packed into data/albums.sff at group = the album's number, so the browser shows
one cover per album. An album with no cover still lists its tracks, it just has
nothing to draw above them.

Stage fight music is separate: it lives in [Music] bgmusic of each stages/*.def.

Run:  python3 tools/build_music.py
"""

from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUND_DIR = os.path.join(ROOT, "sound")
MOTIF = os.path.join(ROOT, "data", "ikemen1", "system.def")
BASE_DEF = os.path.join(ROOT, "data", "system.base.def")
MUSIC_JSON = os.path.join(ROOT, "data", "music.json")
ALBUMS_SFF = os.path.join(ROOT, "data", "albums.sff")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Decodable extensions, most preferred first. Ikemen GO switches decoder on the
# file extension, so an .opus/.m4a/.aac track is silently ignored no matter what
# it contains.
EXTS = ("ogg", "mp3", "flac", "wav", "mid", "midi")
UNSUPPORTED = ("opus", "m4a", "aac", "wma", "aiff", "aif", "mp4", "mod", "xm", "it", "s3m")

COVER_NAMES = ("boxfront.png", "boxfront.jpg", "boxfront.jpeg")
COVER_MAX = 640  # the browser draws covers at 1:1 and caps them at this

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

MUSIC_BGDEF = """[MusicBGdef]
; Background for the music select browser (external/mods/musicselect.lua). It
; draws its own covers and text, so the block only has to clear the screen.
bgclearcolor = 0, 0, 0
"""


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


# ------------------------------------------------------------------ albums
def audio_in(folder):
    """Decodable audio directly in `folder`, most preferred encoding first."""
    try:
        names = os.listdir(folder)
    except OSError:
        return []
    found = {}
    for name in sorted(names):
        base, dot, ext = name.rpartition(".")
        if not dot:
            continue
        ext = ext.lower()
        if ext not in EXTS:
            if ext in UNSUPPORTED:
                print(f"  warning: {os.path.relpath(os.path.join(folder, name), ROOT)} "
                      f"is .{ext}, which Ikemen GO cannot decode")
            continue
        stem = base.lower()
        rank = EXTS.index(ext)
        if stem not in found or rank < found[stem][0]:
            found[stem] = (rank, name)
    return sorted(found.values(), key=lambda v: v[1].lower())


def cover_in(folder):
    try:
        names = os.listdir(folder)
    except OSError:
        return None
    for wanted in COVER_NAMES:
        for name in names:
            if name.lower() == wanted:
                return os.path.join(folder, name)
    return None


METADATA_SUFFIX = ".metadata.pegasus.txt"


def metadata_in(folder):
    """The Pegasus metadata file for an album folder, if it ships one."""
    try:
        names = sorted(os.listdir(folder), key=str.lower)
    except OSError:
        return None
    for name in names:
        if name.lower().endswith(METADATA_SUFFIX):
            return os.path.join(folder, name)
    return None


def parse_metadata(path):
    """Read (tracks, cover) out of a Pegasus metadata file.

    tracks is [(file, title)] in file order and cover is the boxFront path exactly
    as written (or None). Only `game:`/`title:`, `file:`/`path:` and
    `assets.boxFront:` are used; developer, release, genre, sort, description and
    the other assets are skipped, and `collection:` is ignored because the folder
    name is the album's name here.
    """
    tracks = []
    cover = None
    current = None
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            key, sep, value = line.partition(":")
            if not sep:
                continue
            key = key.strip().lower()
            value = value.strip()
            if key in ("game", "title"):
                current = {"file": None, "title": value}
                tracks.append(current)
            elif key in ("file", "path"):
                if current is None:
                    current = {"file": None, "title": None}
                    tracks.append(current)
                current["file"] = value
            elif key == "assets.boxfront" and cover is None and value:
                cover = value
    return [(t["file"], t["title"]) for t in tracks if t["file"]], cover


def _clean_path(written):
    written = written.replace("\\", "/").strip()
    while written.startswith("./"):
        written = written[2:]
    return written.lstrip("/")


def _rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def _listing(place):
    try:
        return sorted(os.listdir(place))
    except OSError:
        return []


def _places(folder):
    """Where a track named in metadata can be, the album folder first."""
    places = [folder, SOUND_DIR]
    for name in _listing(folder):
        sub = os.path.join(folder, name)
        if os.path.isdir(sub):
            places.append(sub)
    return places


def _norm(name):
    """A filename with spacing and punctuation removed, for tolerant matching."""
    return re.sub(r"[^0-9a-z]+", "", name.lower())


def resolve_track(folder, written):
    """Repo-relative path of a track named in metadata, or None if it is absent.

    Metadata paths are written for Pegasus, not for this folder layout, so they are
    tried where the file can actually be: as a path from the repo root, then by name
    inside the album, in sound/ itself, or one folder down inside the album. The
    last pass ignores spacing and punctuation, because a list and the files it
    ships with do drift there ("12- Lopan's" for "12 - Lopan's").
    """
    path = _clean_path(written)
    if os.path.isfile(os.path.join(ROOT, path)):
        return path
    base = path.rpartition("/")[2]
    for candidate in (os.path.join(folder, base), os.path.join(SOUND_DIR, base)):
        if os.path.isfile(candidate):
            return _rel(candidate)
    for place in _places(folder):
        for name in _listing(place):
            candidate = os.path.join(place, name)
            if (name == base or name.lower() == base.lower()) and os.path.isfile(candidate):
                return _rel(candidate)
    wanted = _norm(base)
    if wanted:
        for place in _places(folder):
            for name in _listing(place):
                candidate = os.path.join(place, name)
                if _norm(name) == wanted and os.path.isfile(candidate):
                    rel = _rel(candidate)
                    print(f"  note: {os.path.basename(folder)}: metadata says {written}, "
                          f"using {rel} (names differ in spacing or punctuation)")
                    return rel
    return None


def resolve_cover(folder, written):
    """The cover: the metadata's boxFront if it exists, else boxFront.png."""
    if written:
        path = _clean_path(written)
        for base in (folder, SOUND_DIR, ROOT):
            candidate = os.path.join(base, path)
            if os.path.isfile(candidate):
                return candidate
    return cover_in(folder)


def album_dirs():
    if not os.path.isdir(SOUND_DIR):
        return []
    return sorted(
        (name for name in os.listdir(SOUND_DIR) if os.path.isdir(os.path.join(SOUND_DIR, name))),
        key=str.lower,
    )


def nice_title(filename):
    stem = filename.rpartition(".")[0]
    return stem.replace("_", " ").strip()


def write_music_json(albums):
    payload = {
        # The empty album is the browser's option row: no file means "hand the
        # match back to whatever music the mode selected for itself".
        "": {"Songs": {"Default": {"Title": "Default (stage music)"}}},
    }
    for i, album in enumerate(albums, start=1):
        songs = {}
        for order, track in enumerate(album["tracks"], start=1):
            key = track["title"]
            if key in songs:  # two tracks with one name would otherwise collide
                key = f"{key} ({order})"
            songs[key] = {
                "file": track["file"],
                "Title": track["title"],
                "Order": order,
            }
        if songs:
            payload[album["name"]] = {"Art": i, "Songs": songs}
    with open(MUSIC_JSON, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    total = sum(len(a["tracks"]) for a in albums)
    print(f"  data/music.json: {len(payload) - 1} album(s), {total} track(s)")


def write_albums_sff(albums):
    """Pack each album's cover at group = its 1-based number, index 0."""
    from PIL import Image

    import sff

    sprites = []
    for i, album in enumerate(albums, start=1):
        if not album["cover"]:
            continue
        try:
            img = Image.open(album["cover"]).convert("RGBA")
        except Exception as err:  # a broken PNG should not sink the whole build
            print(f"  warning: could not read {os.path.relpath(album['cover'], ROOT)}: {err}")
            continue
        if max(img.size) > COVER_MAX:
            scale = COVER_MAX / max(img.size)
            img = img.resize((max(1, round(img.width * scale)),
                              max(1, round(img.height * scale))), Image.LANCZOS)
        sprites.append({
            "group": i,
            "number": 0,
            "axis": (img.width // 2, img.height // 2),
            "image": img,
        })
    if not sprites:
        print("  data/albums.sff: no boxFront.png in any album, nothing to pack")
        return
    with open(ALBUMS_SFF, "wb") as fh:
        fh.write(sff.write_sff(sprites))
    print(f"  data/albums.sff: {len(sprites)} cover(s)")


def ensure_music_bgdef():
    """The browser's background block has to exist in the motif it loads.

    Both copies are checked: the base def so a rebuilt motif inherits it, and the
    staged motif because build_fonts rewrites that file in place rather than
    regenerating it from the base, so anything appended to one does not reach the
    other on its own."""
    for path in (BASE_DEF, MOTIF):
        if not os.path.isfile(path):
            print(f"  warning: {os.path.relpath(path, ROOT)} missing", file=sys.stderr)
            continue
        with open(path, "r", encoding="utf-8", errors="surrogateescape") as fh:
            text = fh.read()
        if re.search(r"(?mi)^\[MusicBGdef\]", text):
            continue
        if not text.endswith("\n"):
            text += "\n"
        with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="") as fh:
            fh.write(text + "\n" + MUSIC_BGDEF)
        print(f"  [MusicBGdef] added to {os.path.relpath(path, ROOT)}")


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

    ensure_music_bgdef()

    albums = []
    for name in album_dirs():
        folder = os.path.join(SOUND_DIR, name)
        tracks = []
        cover_hint = None
        source = ""
        meta = metadata_in(folder)
        if meta:
            listed, cover_hint = parse_metadata(meta)
            used = set()
            for written, title in listed:
                path = resolve_track(folder, written)
                if path is None:
                    print(f"  warning: {name}: metadata lists {written}, "
                          f"which is not on disk")
                    continue
                if path.lower() in used:
                    continue
                used.add(path.lower())
                tracks.append({
                    "file": path,
                    "title": title or nice_title(path.rpartition("/")[2]),
                })
            # Nothing in the folder should go missing just because the metadata
            # forgot it, so unlisted audio joins the end of the list.
            for _, fname in audio_in(folder):
                rel = f"sound/{name}/{fname}"
                if rel.lower() in used:
                    continue
                used.add(rel.lower())
                tracks.append({"file": rel, "title": nice_title(fname)})
                print(f"  note: {name}: {fname} is not in the metadata, "
                      f"added at the end")
            source = f", {os.path.basename(meta)}"
        else:
            tracks = [{"file": f"sound/{name}/{f}", "title": nice_title(f)}
                      for _, f in audio_in(folder)]
        if not tracks:
            continue
        cover = resolve_cover(folder, cover_hint)
        albums.append({"name": name, "tracks": tracks, "cover": cover})
        print(f"  album: {name} ({len(tracks)} track(s){source}"
              f"{', cover found' if cover else ', no boxFront.png'})")
    if not albums:
        print("note: no album folders under sound/ yet; put the two OST folders there\n"
              "      with their .ogg tracks and boxFront.png and rerun this tool")
    write_music_json(albums)
    write_albums_sff(albums)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
