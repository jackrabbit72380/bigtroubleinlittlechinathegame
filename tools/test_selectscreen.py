"""Checks the character-select screen the way the request describes it.

The screen is mostly data: the grid, the cursors and the captions are keys in
[Select Info], the art is in system.sff, and the stage screen is the same
section's stage block drawn by external/script/start.lua. Every check here is
something that was wrong on screen at some point - a white box where RANDOM
should be a word, a cursor with one fixed colour, VERSUS lying across the top
row of cells, a fighter with no legs on the VS screen.

Run:  python3 tools/test_selectscreen.py
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEF = os.path.join(ROOT, "data", "ikemen1", "system.def")
SFF = os.path.join(ROOT, "data", "ikemen1", "system.sff")
START = os.path.join(ROOT, "external", "script", "start.lua")


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def block(text, name):
    m = re.search(r"^\[%s\][^\n]*\n(.*?)(?=^\[|\Z)" % re.escape(name), text, re.M | re.S)
    return m.group(1) if m else ""


def key(text, name):
    m = re.search(r"^\s*%s\s*=\s*([^\r\n;]*)" % re.escape(name), text, re.M)
    return m.group(1).strip() if m else None


def check_motif(problems):
    text = read(DEF)
    si = block(text, "Select Info")

    # one size for every word on the header row and the caption row
    if (key(si, "title.font") or "").split(",")[0] != "11":
        problems.append("VERSUS is not drawn in the 20px face")
    if (key(si, "title.scale") or "").replace(" ", "") != "1.5,1.5":
        problems.append("VERSUS is not at the captions' scale")
    for side in ("p1", "p2"):
        if (key(si, side + ".name.font") or "").split(",")[0] != "11":
            problems.append(side + " name is not drawn in the 20px face")
        if (key(si, side + ".name.scale") or "").replace(" ", "") != "1.5,1.5":
            problems.append(side + " name is not at the captions' scale")
    for k in ("stage.font", "stage.active.font"):
        if (key(si, k) or "").split(",")[0] != "11":
            problems.append(k + " is not the caption face")
    if (key(si, "stage.scale") or "").replace(" ", "") != "1.5,1.5":
        problems.append("the stage name is not the caption size")

    # VERSUS clears the wall: the face is a 20px cell at 1.5, the frame is 15px
    # above the first cell
    pos = key(si, "pos") or ""
    m = re.match(r"(-?\d+)\s*,\s*(-?\d+)", pos)
    if not m:
        problems.append("[Select Info] has no grid position")
    else:
        top = int(m.group(2)) - 15
        if top < 30:
            problems.append("the VERSUS row (%dpx) runs into the grid frame at y=%d"
                            % (30, top))

    # cursor: 2x art at half scale, the player's colour flashing white
    for side, action, colour in (("p1", "160", "223,0"), ("p2", "170", "223,1")):
        if key(si, side + ".cursor.active.anim") != action:
            problems.append(side + " active cursor has no flash action")
        if (key(si, side + ".cursor.active.scale") or "").replace(" ", "") != "0.50,0.50":
            problems.append(side + " active cursor is not the half-scale art")
        if (key(si, side + ".cursor.done.spr") or "").replace(" ", "") != colour:
            problems.append(side + " done cursor is not its player's colour")
        if (key(si, side + ".cursor.done.scale") or "").replace(" ", "") != "0.50,0.50":
            problems.append(side + " done cursor is not the half-scale art")

    # RANDOM is a word, not a cell
    if (key(si, "cell.random.spr") or "").replace(" ", "") != "-1":
        problems.append("RANDOM still draws a cell sprite")

    # the stage screen: a card and a name, once the wall is gone
    if (key(si, "stage.portrait.spr") or "").replace(" ", "") != "9000,1":
        problems.append("the stage screen has no preview card")
    win = key(si, "stage.portrait.window") or ""
    if win.replace(" ", "") in ("", "0,0,0,0"):
        problems.append("the stage card's window is empty")
    if (key(si, "stage.pos") or "").split(",")[-1].strip() != "1035":
        problems.append("the stage name is not on the caption row")
    return text


def check_actions(problems, text):
    for action, colour, white in ((160, "223,0", "224,0"), (170, "223,1", "224,1")):
        body = block(text, "Begin Action %d" % action)
        if colour not in body or white not in body:
            problems.append("action %d does not flash between %s and %s"
                            % (action, colour, white))


def check_sprites(problems):
    _d, sprites, _p = sff.read_sff(SFF)
    have = {(s["group"], s["number"]): s for s in sprites}
    for spr in ((151, 0), (151, 11)):
        if spr not in have:
            problems.append("RANDOM word sprite %d,%d is missing" % spr)
        elif have[spr]["axis"] != (0, 0):
            problems.append("RANDOM word sprite %d,%d has a shifted axis" % spr)
    if (151, 0) in have and (151, 11) in have:
        gold = sff.decode_sprite(_d, have[(151, 0)], _p).convert("RGBA")
        green = sff.decode_sprite(_d, have[(151, 11)], _p).convert("RGBA")
        if gold.size != green.size:
            problems.append("the RANDOM word resizes when it is selected (%s vs %s)"
                            % (gold.size, green.size))
        else:
            w, h = green.size
            px = green.load()
            ring = ([(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)]
                    + [(0, y) for y in range(1, h - 1)]
                    + [(w - 1, y) for y in range(1, h - 1)])
            if any(px[x, y][3] > 10 for x, y in ring):
                problems.append("the selected RANDOM stop is drawn as a box, not a word")
            ink = [px[x, y] for y in range(h) for x in range(w) if px[x, y][3] > 120]
            if not ink:
                problems.append("the selected RANDOM word is blank")
            else:
                r = sum(p[0] for p in ink) / len(ink)
                g = sum(p[1] for p in ink) / len(ink)
                b = sum(p[2] for p in ink) / len(ink)
                if not (g > r + 40 and g > b + 40):
                    problems.append("the selected RANDOM word is not green")
    for spr in ((223, 0), (223, 1), (224, 0), (224, 1)):
        if spr not in have:
            problems.append("cursor sprite %d,%d is missing" % spr)
        elif (have[spr]["w"], have[spr]["h"]) != (256, 320):
            problems.append("cursor sprite %d,%d is %dx%d, not 2x the cell"
                            % (spr[0], spr[1], have[spr]["w"], have[spr]["h"]))
    bg = have.get((220, 0))
    if bg is None or (bg["w"], bg["h"]) != (1920, 1080):
        problems.append("the select backdrop is not a 1920x1080 plate")


def check_vs_portraits(problems):
    """Every fighter's VS action must play the full-body art, not the cell bust."""
    for air in sorted(glob.glob(os.path.join(ROOT, "chars", "*", "*.air"))):
        stem = os.path.splitext(air)[0]
        try:
            _d, sprites, _p = sff.read_sff(stem + ".sff")
        except Exception:
            continue
        if not any(s["group"] == 9000 and s["number"] == 1 for s in sprites):
            continue
        body = block(read(air), "Begin Action 9000")
        if not body:
            problems.append("%s has no VS action" % os.path.relpath(air, ROOT))
        elif "9000,1," not in body:
            problems.append("%s plays the bust, so the fighter loses his legs"
                            % os.path.relpath(air, ROOT))


def check_script(problems):
    text = read(START)
    if "'151,0, 0,0, -1'" not in text or "'151,11, 0,0, -1'" not in text:
        problems.append("start.lua does not draw the RANDOM word from its sprites")
    if "not sideOnRandomStop(v.player)" not in text:
        problems.append("start.lua still draws a box cursor on the RANDOM stop")
    if "local stagePhase = false" not in text:
        problems.append("start.lua has no stage screen of its own")
    stage = text[text.index("if main.stageMenu and not stageEnd then --Stage select"):
                 text.index("if main.stageMenu and not stageEnd then --Stage select") + 1200]
    if "fadeOutInit" not in stage or "fadeInInit" not in stage:
        problems.append("the wall is not faded out and the stage screen faded in")
    if "not (t.char == 'randomselect' or t.hidden == 3)" not in text:
        problems.append("a done cursor can still be drawn on the RANDOM stop")


def check_metrics(problems):
    text = read(START)
    if "local function dims(" not in text:
        problems.append("start.lua has no flattener for the motif's grid metrics")
    if not re.search(r"local cellW, cellH = dims\(si\.cell\.size\)", text):
        problems.append("start.lua still reads cell.size as a flat pair")
    # This engine build nests pair metrics per side (cell.size = {{128,160}});
    # indexing one straight and multiplying it is what put the menu in the
    # error box, so every read has to go through the flattener.
    for m in re.finditer(r"(?m)^.*\.(?:size|spacing|pos|offset)\[\d\].*$", text):
        line = m.group(0).strip()
        if line.startswith("--"):
            continue
        problems.append("start.lua indexes a motif metric straight: " + line[:90])


def main():
    problems = []
    text = check_motif(problems)
    print("  %s every caption is one size and VERSUS clears the wall"
          % ("ok " if not problems else "FAIL"))
    before = len(problems)
    check_actions(problems, text)
    print("  %s the cursors are the player's colour flashing white"
          % ("ok " if len(problems) == before else "FAIL"))
    before = len(problems)
    check_sprites(problems)
    print("  %s the RANDOM stop is green type and the cursors are 2x art"
          % ("ok " if len(problems) == before else "FAIL"))
    before = len(problems)
    check_vs_portraits(problems)
    print("  %s every VS portrait plays the full-body art"
          % ("ok " if len(problems) == before else "FAIL"))
    before = len(problems)
    check_script(problems)
    print("  %s the screen runs the wall, the word and the stage phase"
          % ("ok " if len(problems) == before else "FAIL"))
    before = len(problems)
    check_metrics(problems)
    print("  %s the grid metrics are read through the flattener"
          % ("ok " if len(problems) == before else "FAIL"))
    if problems:
        print("\nthe select screen regressed in %d place(s)" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1
    print("\nthe select screen says RANDOM, marks both players and stages the match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
