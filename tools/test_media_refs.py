"""Prove the media check catches a stage or a screen pointing at nothing.

The check exists because a def naming a file nobody shipped is silent: no error,
no layer, and the credits simply have no clip. Like tools/test_launchers.py, this
feeds the checker the broken form and the correct form, so a check that quietly
stopped reading a kind of file cannot keep passing.

Run:  python3 tools/test_media_refs.py
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

_spec = importlib.util.spec_from_file_location(
    "validate_media", os.path.join(HERE, "validate.py"))
validate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate)


def write(root, rel, text=""):
    path = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def git(root, *args):
    subprocess.run(["git", "-C", root] + list(args), stdout=subprocess.PIPE,
                   stderr=subprocess.DEVNULL, check=True)


def run(root):
    validate.ROOT = root
    validate.errors.clear()
    validate.notes.clear()
    validate.check_media_refs()
    return list(validate.errors)


def main():
    good = tempfile.mkdtemp()
    bad = tempfile.mkdtemp()
    try:
        # every reference resolves: from the game root, or beside the def itself
        write(good, "sound/track.ogg", "x")
        write(good, "video/clip.webm", "x")
        write(good, "stages/fine.def",
              "[Music]\nbgmusic = sound/track.ogg\n"
              "[BG fog]\ntype = video\npath = video/clip.webm\n")
        write(good, "stages/local/track.ogg", "x")
        write(good, "stages/local/own.def", "[Music]\nbgmusic = track.ogg\n")
        write(good, "data/ikemen1/system.def", "[Music]\ntitle.bgm = sound/track.ogg\n")
        write(good, "data/ikemen1/credits.def",
              "[SceneDef]\nbgm = sound/track.ogg\n"
              "[BG0]\ntype = video\npath = video/clip.webm\n")
        # a commented-out reference is not a read
        write(good, "stages/quiet.def", "; bgmusic = sound/never.ogg\n[Music]\nbgmusic =\n")
        write(good, "external/script/screen.lua",
              "-- sndPlay(\"sound/never.ogg\")\n"
              "sndPlay(\"sound/track.ogg\")\n"
              "local label = \"menu.itemname.menuvideo.window\"\n")
        write(good, "data/music.json", '{"Album": {"1": "sound/track.ogg"}}')
        errors = run(good)
        assert not errors, "a clean tree reported %r" % (errors,)

        # every way a stage or screen can point at nothing
        write(bad, "sound/track.ogg", "x")
        write(bad, "stages/silent.def", "[Music]\nbgmusic = sound/gone.ogg\n")
        write(bad, "stages/fog.def", "[BG fog]\ntype = video\npath = video/gone.webm\n")
        write(bad, "data/ikemen1/credits.def",
              "[BG0]\ntype = video\npath = ik_credits.webm\n")
        write(bad, "external/script/screen.lua", "sndPlay(\"sound/missing.ogg\")\n")
        write(bad, "data/music.json",
              '{"Album": {"1": "sound/track.ogg", "2": "sound/absent.ogg"}}')
        errors = run(bad)
        for want in ("sound/gone.ogg", "video/gone.webm", "ik_credits.webm",
                     "sound/missing.ogg", "sound/absent.ogg"):
            assert any(want in e for e in errors), \
                "%s was not reported: %r" % (want, errors)
        # one message per reference, not one per line the file appears on
        assert sum("video/gone.webm" in e for e in errors) == 1, errors
        # the clean reference in the same tree is still clean
        assert not any("sound/track.ogg" in e for e in errors), errors

        # a clip that is in the folder but in no commit does not ship: the
        # updater copies what main has, so the reference is still broken
        loose = tempfile.mkdtemp()
        try:
            write(loose, "video/local_only.webm", "x")
            write(loose, "data/ikemen1/credits.def",
                  "[BG0]\ntype = video\npath = video/local_only.webm\n")
            git(loose, "init", "-q")
            git(loose, "add", "data")
            errors = run(loose)
            assert any("not in the repo" in e for e in errors), errors
        finally:
            shutil.rmtree(loose, ignore_errors=True)
    finally:
        shutil.rmtree(good, ignore_errors=True)
        shutil.rmtree(bad, ignore_errors=True)

    print("media references: 5 broken form(s) and an untracked clip caught, "
          "clean tree passes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
