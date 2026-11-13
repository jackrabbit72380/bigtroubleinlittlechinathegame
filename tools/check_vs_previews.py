"""Check that the VS screen's two pictures resolve at the size it draws them.

The VS screen draws a character portrait and a stage preview, and both come out
of the fighter's and the stage's own sprite sheet rather than from the screenpack:

* ``[VS Screen] p1.spr = 9000,1`` from each fighter's sheet. The engine scales a
  portrait by motif.localcoord / the character's localcoord, so the sheet holds
  the picture at target/factor - 60x70 for a 320-localcoord fighter, 180x210 for
  a 960 one - and either lands on the 360x420 art box.
* ``[VS Screen] stage.portrait.spr = 9000,1`` from each stage's sheet, scaled by
  the same localcoord ratio, by the stage's ``portraitscale`` and then by the
  motif's stage.portrait.scale. Every stage has to land on the roster's
  1215x398 card, or it is drawn at another shape inside the screen's window and
  cropped: the three Third Heights stages drew 1215x506, and the 3-D Lab drew
  1920x1440, while the 240x100 sheet picture was still on disk.

A stage or fighter missing the sprite shows a placeholder, so that is a failure
here too.

Run:  python3 tools/check_vs_previews.py
"""

import glob
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sff
import fit_stage_previews as fit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SELECT_DEF = os.path.join(ROOT, "data", "select.def")
CARD = fit.CARD                 # the stage preview, in motif units
PORTRAIT = (360, 420)           # the fighter art box, in motif units
TOLERANCE = 2.0


def setting(text, key, default):
    found = re.search(r"^\s*" + key + r"\s*=\s*([^;\r\n]+)", text, re.M | re.I)
    return found.group(1).strip() if found else default


def block(name):
    text = open(SELECT_DEF, encoding="utf-8", errors="replace").read()
    return text.split("[" + name + "]", 1)[1].split("[", 1)[0]


def fighters():
    """The roster's defs, as select.def names them (relative to chars/)."""
    refs = []
    for line in block("Characters").splitlines():
        line = line.split(";", 1)[0].strip()
        if not line or line.startswith(";"):
            continue
        ref = line.split(",")[0].strip()
        if ref.lower().endswith(".def"):
            refs.append(ref)
    return refs


def sprite_9000(def_path):
    """(width, height) of 9000,1 in the sheet this def points at, or None."""
    text = open(def_path, encoding="utf-8", errors="replace").read()
    # a fighter says "sprite =", a stage says "spr ="; without either, the sheet
    # is the def's own name
    name = setting(text, "sprite", None) or setting(text, "spr", None)
    if not name:
        name = os.path.basename(def_path)[:-4] + ".sff"
    path = os.path.join(os.path.dirname(def_path), name)
    if not os.path.isfile(path):
        return None
    _data, sprites, _pals = sff.read_sff(path)
    hit = next((sp for sp in sprites
                if (sp["group"], sp["number"]) == (9000, 1)), None)
    return None if hit is None else (hit["w"], hit["h"])


# The three stages built from the same island layer (tools/build_stage3d_rain.py)
# are meant to be told apart by the hour painted around the island - day, night,
# storm - so a shared picture is the failure that has already shipped twice: they
# have to resolve to three different cards.
SHARED_ISLAND = ("stages/stage3d.def", "stages/stage3d_outline.def",
                 "stages/stage3d_rain.def")


def card_pixels(def_path):
    """md5 of the 9000,1 picture's pixels, or None if it cannot be decoded."""
    text = open(def_path, encoding="utf-8", errors="replace").read()
    name = setting(text, "sprite", None) or setting(text, "spr", None)
    if not name:
        name = os.path.basename(def_path)[:-4] + ".sff"
    path = os.path.join(os.path.dirname(def_path), name)
    if not os.path.isfile(path):
        return None
    raw, sprites, pals = sff.read_sff(path)
    hit = next((sp for sp in sprites
                if (sp["group"], sp["number"]) == (9000, 1)), None)
    if hit is None:
        return None
    try:
        return hashlib.md5(sff.decode_sprite(raw, hit, pals, hit["pal"])
                           .convert("RGBA").tobytes()).hexdigest()
    except Exception:
        return None


def main():
    problems = []
    stages = checked = 0
    for ref in fit.pool():
        def_path = os.path.join(ROOT, ref.replace("/", os.sep))
        if not os.path.isfile(def_path):
            problems.append("%s: no such stage" % ref)
            continue
        stages += 1
        factor, _want = fit.drawn_size(def_path)
        size = sprite_9000(def_path)
        if size is None:
            problems.append("%s: no 9000,1 preview in its sheet" % ref)
            continue
        drawn = (size[0] * factor, size[1] * factor)
        if (abs(drawn[0] - CARD[0]) > TOLERANCE
                or abs(drawn[1] - CARD[1]) > TOLERANCE):
            problems.append("%s: preview draws %.0fx%.0f, not the %dx%d card "
                            "(sheet %dx%d at localcoord/portraitscale %.3f)"
                            % (ref, drawn[0], drawn[1], CARD[0], CARD[1],
                               size[0], size[1], factor))

    portraits = 0
    for ref in fighters():
        def_path = os.path.join(ROOT, "chars", ref.replace("/", os.sep))
        if not os.path.isfile(def_path):
            problems.append("%s: no such fighter" % ref)
            continue
        text = open(def_path, encoding="utf-8", errors="replace").read()
        try:
            localcoord = float(setting(text, "localcoord", "320,240").split(",")[0])
        except ValueError:
            localcoord = 320.0
        factor = fit.MOTIF_W / localcoord
        size = sprite_9000(def_path)
        if size is None:
            problems.append("%s: no 9000,1 portrait in its sheet" % ref)
            continue
        portraits += 1
        box = (size[0] * factor, size[1] * factor)
        if box[0] > PORTRAIT[0] + TOLERANCE or box[1] > PORTRAIT[1] + TOLERANCE:
            problems.append("%s: portrait draws %.0fx%.0f, past the %dx%d art box"
                            % (ref, box[0], box[1], PORTRAIT[0], PORTRAIT[1]))
        elif max(box[0] / PORTRAIT[0], box[1] / PORTRAIT[1]) < 0.85:
            problems.append("%s: portrait draws %.0fx%.0f, a cell rather than the "
                            "%dx%d art" % (ref, box[0], box[1],
                                           PORTRAIT[0], PORTRAIT[1]))

    # the shared-island stages: three stages, three pictures
    cards = 0
    seen = {}
    for ref in SHARED_ISLAND:
        def_path = os.path.join(ROOT, ref.replace("/", os.sep))
        if not os.path.isfile(def_path):
            problems.append("%s: no such stage" % ref)
            continue
        digest = card_pixels(def_path)
        if digest is None:
            problems.append("%s: 9000,1 could not be decoded" % ref)
            continue
        cards += 1
        for other, other_digest in seen.items():
            if other_digest == digest:
                problems.append("%s and %s draw the same preview picture"
                                % (ref, other))
        seen[ref] = digest

    print("vs previews: %d stage(s) and %d fighter(s) measured against the %dx%d "
          "card and the %dx%d art box"
          % (stages, portraits, CARD[0], CARD[1], PORTRAIT[0], PORTRAIT[1]))
    if problems:
        for line in problems:
            print("  FAIL " + line)
        return 1
    print("  ok  every VS preview and portrait lands on its size")
    print("  ok  the %d shared-island stage(s) draw %d different card(s)"
          % (cards, len(seen)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
