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


def caption_scale():
    """The size every caption on this screen is drawn at: the main menu's own.

    One text size for the whole game means one reference, so this reads the main
    menu's scale out of the motif rather than holding a copy of it. A copy is how
    the captions were left at 0.75 while the menu above them sat at 0.48, and how
    a test went on passing while the two screens drew different sizes.
    """
    import os as _os
    root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    text = open(_os.path.join(root, "data", "ikemen1", "system.def"),
                encoding="utf-8", errors="replace").read()
    block = re.search(r"\[Title Info\](.*?)(?=\n\[|\Z)", text, re.S | re.I)
    hit = block and re.search(r"^\s*menu\.item\.scale\s*=\s*([^;\r\n]+)",
                              block.group(1), re.M | re.I)
    return hit.group(1).strip().replace(" ", "") if hit else "0.48,0.48"


SFF = os.path.join(ROOT, "data", "ikemen1", "system.sff")


def grid_cell():
    """The roster cell, read from the generator that paints the wall."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "build_select_grid.py")
    with open(path, encoding="utf-8") as fh:
        m = re.search(r"^CELL, CELL_H = (\d+), (\d+)", fh.read(), re.M)
    if not m:
        raise SystemExit("build_select_grid.py has no CELL, CELL_H line")
    return int(m.group(1)), int(m.group(2))
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

    # one size for every word on the header row and the caption row: the fight
    # captions' own face (Display, font 10) at the WINS caption's size,
    # gave the rest of the game
    if (key(si, "title.font") or "").split(",")[0] != "10":
        problems.append("VERSUS is not drawn in the caption face")
    if (key(si, "title.scale") or "").replace(" ", "") != caption_scale():
        problems.append("VERSUS is not at the captions' scale")
    for side in ("p1", "p2"):
        if (key(si, side + ".name.font") or "").split(",")[0] != "10":
            problems.append(side + " name is not drawn in the caption face")
        if (key(si, side + ".name.scale") or "").replace(" ", "") != caption_scale():
            problems.append(side + " name is not at the captions' scale")
    for k in ("stage.font", "stage.active.font"):
        if (key(si, k) or "").split(",")[0] not in ("10", "12"):
            problems.append(k + " is not the caption face")
    if (key(si, "stage.scale") or "").replace(" ", "") != caption_scale():
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

    # The stage screen is the wall: every map is a baked card (240,<n>) and the
    # picked one is framed (241,0 for player 1, 242,0 for player 2), so there is no
    # separate preview card and no window to fit one into. What must hold is that
    # the wall still has its backdrop and the name is still on the caption row.
    if (key(si, "stage.portrait.spr") or "").replace(" ", "") != "-1":
        problems.append("the stage screen still draws a separate preview card")
    if (key(si, "stage.portrait.bg.spr") or "").replace(" ", "") != "225,0":
        problems.append("the stage screen has no backdrop under the wall")
    if (key(si, "stage.pos") or "").split(",")[-1].strip() != "120":
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
        elif (have[spr]["w"], have[spr]["h"]) != (2 * grid_cell()[0], 2 * grid_cell()[1]):
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
    if "RANDOM_SPR = {original = {base = 0, lit = 11}, karate = {base = 13, lit = 12}}" not in text:
        problems.append("start.lua no longer names the RANDOM sprites")
    if "'151,%d, 0,0, -1'" not in text:
        problems.append("start.lua does not draw the RANDOM word from its sprites")
    if "animNew, nil" in text:
        problems.append("start.lua builds runtime art with a nil sprite file, "
                        "so every frame is a missing sprite and nothing draws")
    if "spriteDraw(a, 0, 0)" not in text:
        problems.append("start.lua draws the wall through main.f_animPosDraw, "
                        "whose reset drops the 1080p space and blows the art up")
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


def check_stage_wall(problems):
    """The stage screen must show every map, and nothing else on it.

    It used to draw one card at a time on a blank field, with the pickers wiped off
    along with the wall. The layout is arithmetic in start.lua, so it is executed
    the way the game executes it (lupa) and the boxes are measured, not eyeballed.
    """
    text = read(START)
    if "function start.f_stageGrid" not in text:
        problems.append("start.lua has no layout for a wall of stage cards")
        return
    # The pictures are baked - tools/build_stage_wall.py paints each stage's
    # card into system.sff at its drawn size - and the screen places them, so a
    # layout tweak needs no rebuild and no stage art is scaled at runtime.
    if "local cards = start.f_stageGrid(stCount)" not in text:
        problems.append("the stage screen does not lay the maps out as a wall")
    if "spriteDraw(card, cell.x, cell.y)" not in text:
        problems.append("the stage cards are not drawn at the layout's own boxes")
    wall_at = text.find("local cards = start.f_stageGrid(stCount)")
    wall_end = text.find("-- The fighters are not drawn here", wall_at)
    wall_region = text[wall_at:wall_end] if wall_at >= 0 and wall_end > wall_at else ""
    if not wall_region:
        problems.append("the wall draw is not where the stage screen expects it")
    elif "animSetScale" in wall_region:
        problems.append("the wall still scales stage art at runtime")
    # the baked card size and the size the layout spaces cards at are the same
    # number in two files; if they drift the wall overlaps or opens gaps
    card = re.search(r"card = \{\s*(\d+),\s*(\d+)\s*\}", text)
    wall_tool = os.path.join(ROOT, "tools", "build_stage_wall.py")
    if card and os.path.isfile(wall_tool):
        baked = re.search(r"CARD = \((\d+), (\d+)\)", read(wall_tool))
        if baked is None:
            problems.append("build_stage_wall.py does not declare the card size")
        elif (int(card.group(1)), int(card.group(2))) != (int(baked.group(1)), int(baked.group(2))):
            problems.append("the layout and the baked cards disagree on the card size")

    if not os.path.isfile(wall_tool):
        problems.append("nothing bakes the stage cards into the screenpack")
    else:
        bake = read(wall_tool)
        for needle, why in (("CARD = (457, 150)", "the card size is not fixed"),
                            ("def frame_sprite(", "the pick has no baked frame"),
                            ("[ExtraStages]", "the cards are not baked from the stage pool")):
            if needle not in bake:
                problems.append("build_stage_wall.py: " + why)
    # that backdrop sprite is the character wall's frame: a grid of empty cells is
    # exactly what the stage screen must not show, and the select backdrop is
    # everything it should show instead
    if not re.search(r"if not stagePhase then\s*\n\s*main\.f_animPosDraw\(motif\.select_info\.stage\.portrait\.bg",
                     text):
        problems.append("the empty character grid is still drawn behind the maps")
    if "pcall(animPrepare, a, ref)" not in text:
        problems.append("the palette load does not pass the character index to animPrepare")
    if "start.stageSide" not in text or "start.f_stageFrameSprite" not in text:
        problems.append("the picked map is not outlined in the player's colour")
    grid_src = read(os.path.join(ROOT, "tools", "build_select_grid.py"))
    if "STAGE_FRAME" not in grid_src or "def stage_frame(" not in grid_src:
        problems.append("no 3:1 stage frame set is painted into system.sff")
    if wall_region and "cursor.done" in wall_region:
        problems.append("the wall still stretches the character cursor over the wide card")
    for tool in ("build_stages.py", "build_training.py", "build_hd_stage.py",
                 "build_stage3d_rain.py"):
        if "frame_card(" not in read(os.path.join(ROOT, "tools", tool)):
            problems.append("%s does not put the gold rule on the stage cards" % tool)
    if text.count("bgDraw(motif.selectbgdef.BGDef, 0)") < 2:
        problems.append("the stage screen has no backdrop of its own")
    # The fighters and their names are not on this screen any more: the wall and
    # the map's name are. What the test guards is that they were not left behind,
    # and that the name row keeps the guard that takes them off it.
    if wall_region and ("if stagePhase then" in wall_region or "f_drawPortraits" in wall_region):
        problems.append("the picked fighters are still drawn on the stage screen")
    if "if not stagePhase and #start.p[side].t_selTemp > 0 then" not in text:
        problems.append("the fighter names are still drawn on the stage screen")

    try:
        from lupa import LuaRuntime
    except ImportError:
        return                                  # geometry checked only with lupa
    start = text.index("-- >>> stage preview grid geometry")
    end = text.index("-- <<< stage preview grid geometry")
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("start = {}")
    lua.execute(text[start:end])
    # the real pool: thirteen stages, which is five rows of the card
    cards = lua.eval("start.f_stageGrid(13)")
    boxes = []
    for i in range(1, 14):
        cell = cards[i]
        if cell is None:
            problems.append("the stage wall has a hole at position %d" % i)
            return
        # a card's x and y are its centre, so its box is half a card either side
        w, h = float(cell["w"]), float(cell["h"])
        boxes.append((float(cell["x"]) - w / 2, float(cell["y"]) - h / 2, w, h))
    # the stage screen's own window, read from the screen instead of typed here
    win = lua.eval("start.stageGrid.window")
    x1, y1, x2, y2 = (float(win[k]) for k in (1, 2, 3, 4))
    band_top, band_bottom = 72.0, 1000.0
    for i, (x, y, w, h) in enumerate(boxes, 1):
        # this pool is bigger than the window, so the wall may use the band the
        # screen allows: the window's columns, below the captions, above the names
        if x < x1 - 0.5 or x + w > x2 + 0.5:
            problems.append("stage card %d falls outside the wall's columns" % i)
            break
        if y < band_top - 0.5 or y + h > band_bottom + 0.5:
            problems.append("stage card %d leaves the band it may use" % i)
            break
        # and on the screen: a card hanging off the bottom is a card nobody can pick
        if y + h > 1080.5 or y < -0.5:
            problems.append("stage card %d runs off the screen" % i)
            break
        if w < 200 or h < 60:
            problems.append("stage card %d is too small to read" % i)
            break
        # a map's card is a wide 3:1 picture, not a 128x160 character cell
        if not 2.4 < w / h < 3.6:
            problems.append("stage card %d is not a wide card (%.0fx%.0f)" % (i, w, h))
            break
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            ax, ay, aw, ah = boxes[i]
            bx, by, bw, bh = boxes[j]
            if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                problems.append("stage cards %d and %d overlap" % (i + 1, j + 1))
                return
    # The cursor walks that grid: every arrow moves it, either end wraps, and
    # neither direction can leave the wall. The arithmetic is the screen's own.
    # the pool this theme ships is twelve stages: four rows, inside the band below
    # the caption row and above the fighter names
    real = lua.eval("start.f_stageGrid(12)")
    rwin = lua.eval("start.stageGrid.window")
    ry1, ry2 = float(rwin[2]), float(rwin[4])
    for i in range(1, 13):
        if float(real[i]["y"]) - 75 < ry1 - 0.5 or float(real[i]["y"]) + 75 > ry2 + 0.5:
            problems.append("the twelve-stage wall does not sit inside its window")
            break
    # and the preview tool's layout must agree with the screen at every pool size,
    # so a preview can never show a wall the game would place somewhere else
    try:
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import build_stage_wall as wall_tool
    except Exception as exc:
        problems.append("the wall preview tool cannot be imported: %s" % exc)
    else:
        for count in range(1, 17):
            mine, _, _ = wall_tool.layout(count)
            theirs = lua.eval("start.f_stageGrid")(count)
            for i in range(count):
                if (abs(float(theirs[i + 1]["x"]) - mine[i]["cx"]) > 0.5
                        or abs(float(theirs[i + 1]["y"]) - mine[i]["cy"]) > 0.5):
                    problems.append("the wall preview disagrees with the screen at %d cards"
                                    % count)
                    break
    step = lua.eval("start.f_stageCursorStep")
    if step is None:
        problems.append("the stage wall has no cursor step")
        return
    # 13 cards, three across: rows of 3,3,3,3 and a short row of one, with RANDOM
    # as the row under the wall. The wall is 3 columns wide whatever the count, so
    # these are the real numbers this screen works with.
    COUNT, COLS = 13, 3
    checks = (
        ("keeps its row moving left", step(2, "L", COUNT, COLS, True), 1),
        ("keeps its row moving right", step(1, "R", COUNT, COLS, True), 2),
        ("wraps within its row going left", step(1, "L", COUNT, COLS, True), 3),
        ("wraps within its row going right", step(3, "R", COUNT, COLS, True), 1),
        ("keeps its column moving down", step(1, "D", COUNT, COLS, True), 4),
        ("keeps its column moving up", step(4, "U", COUNT, COLS, True), 1),
        ("clamps to the short last row", step(12, "D", COUNT, COLS, True), 13),
        ("is not taken off the wall into another row", step(12, "D", COUNT, COLS, True) in (1, 13), True),
        ("reaches RANDOM going down off the wall", step(13, "D", COUNT, COLS, True), 0),
        ("leaves RANDOM going up", step(0, "U", COUNT, COLS, True), 13),
        ("wraps from RANDOM to the top row", step(0, "D", COUNT, COLS, True), 1),
        ("wraps from the top row to RANDOM", step(1, "U", COUNT, COLS, True), 0),
        ("walks off RANDOM going left onto the last card", step(0, "L", COUNT, COLS, True), 13),
        ("walks off RANDOM going right onto the first card", step(0, "R", COUNT, COLS, True), 1),
        ("walks off the short last row going right onto RANDOM", step(13, "R", COUNT, COLS, True), 0),
        ("wraps to the short row with no RANDOM", step(1, "U", COUNT, COLS, False), 13),
        ("wraps to the top with no RANDOM", step(13, "D", COUNT, COLS, False), 1),
        ("a single column is a vertical list", step(2, "D", 5, 1, False), 3),
        ("an empty wall stays put", step(0, "D", 0, COLS, False), 0),
    )
    for why, got, expect in checks:
        if got is None or int(got) != int(expect):
            problems.append("the stage cursor %s (got %s, wanted %d)" % (why, got, expect))
    # left then right returns to the same card on every stop in a row that has
    # more than one card, so no press can slide the cursor sideways along a row.
    # A row one card wide has no sideways neighbour of its own - RANDOM is one, and
    # so is a short last row - and there a sideways press must simply move: that is
    # the wall's opening position, and answering it with nothing is what left the
    # whole wall unresponsive.
    def row_width(card):
        row = (card - 1) // COLS + 1
        return min(COLS, COUNT - (row - 1) * COLS)
    for card in range(1, COUNT + 1):
        if row_width(card) <= 1:
            for d in ("L", "R", "U", "D"):
                moved = step(card, d, COUNT, COLS, True)
                if moved is None or int(moved) == card:
                    problems.append("a one-card row answers %s with nothing at %d" % (d, card))
            continue
        back = step(step(card, "L", COUNT, COLS, True), "R", COUNT, COLS, True)
        if back is None or int(back) != card:
            problems.append("left then right does not return to card %d" % card)
    # up then down returns to the same card everywhere, except for the two columns
    # with no cell in RANDOM's one-card row: wrapping through it clamps to RANDOM,
    # the same clamp any move into the short last row does
    for card in (1,) + tuple(range(4, COUNT + 1)):
        back = step(step(card, "U", COUNT, COLS, True), "D", COUNT, COLS, True)
        if back is None or int(back) != card:
            problems.append("up then down does not return to card %d" % card)
    if int(step(step(2, "U", COUNT, COLS, True), "D", COUNT, COLS, True)) != 1:
        problems.append("a column clamped through RANDOM does not land on the first card")
    # all four arrows, read for both players, not just one key for one of them.
    # The wall must hand getInput the motif's own key tables - cell.left.key and
    # friends - because those are what the character grid moves on; rebuilt copies
    # holding invented names answered nothing and left the wall deaf.
    for needle, why in (("keyTable(cell.left)", "left from the grid's own left key"),
                        ("keyTable(cell.right)", "right from the grid's own right key"),
                        ("keyTable(cell.up)", "up from the grid's own up key"),
                        ("keyTable(cell.down)", "down from the grid's own down key"),
                        ("keyTable(stageKeys.previous)", "up from the screenpack's stage keys"),
                        ("keyTable(stageKeys.next)", "down from the screenpack's stage keys"),
                        ("keyTable(skip.previous)", "left from the screenpack's skip keys"),
                        ("keyTable(skip.next)", "right from the screenpack's skip keys"),
                        ("pcall(getInput", "its input through reads that cannot raise"),
                        ("for side = 1, 2 do", "the keys off both players")):
        if needle not in text:
            problems.append("the stage wall does not read %s" % why)


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
    before = len(problems)
    check_stage_wall(problems)
    print("  %s the stage screen shows the map wall and the map's name"
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
