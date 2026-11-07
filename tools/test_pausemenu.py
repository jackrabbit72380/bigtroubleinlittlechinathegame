"""Check the pause menu's list geometry and that rows are placed, not added.

The engine bakes a base position into every menu item text sprite, and this build
bakes the stock motif's 320x240 [Menu Info] anchor into the pause rows: the list
drew at the bottom of the screen, off the edge, while the cursor band drew at
menu.pos. main.f_menuItemPos places each row from the section's own geometry and
main.f_menuItemPlace sets it, so the baked base cannot move anything. This runs
that block against the shipped system.def and a base that is deliberately wrong.

Run:  PYTHONPATH=/tmp/pylibs python3 tools/test_pausemenu.py
"""

import os
import re
import sys

from lupa import LuaRuntime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEF = os.path.join(ROOT, "data", "ikemen1", "system.def")
MAIN = os.path.join(ROOT, "external", "script", "main.lua")
MENU = os.path.join(ROOT, "external", "script", "menu.lua")
DEVHELP = os.path.join(ROOT, "external", "mods", "devhelp.lua")

BEGIN = "-- >>> pause menu item geometry"
END = "-- <<< pause menu item geometry"
MOV_BEGIN = "-- >>> command list geometry"
MOV_END = "-- <<< command list geometry"

STUB = """
main = {}
-- where this build bakes a pause item's base: the stock 320x240 anchor, x6
BASE_X, BASE_Y = 954, 948
POS = {}                     -- absolute positions the block set
SPR = {}                     -- per-sprite position after add/set
textImgSetPos = function(spr, x, y) SPR[spr] = {x, y}; POS[#POS + 1] = {x, y} end
textImgAddPos = function(spr, x, y)
    local b = SPR[spr] or {BASE_X, BASE_Y}
    SPR[spr] = {b[1] + x, b[2] + y}
end
"""


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def section_values(text, name):
    values, cur = {}, None
    for line in text.splitlines():
        head = re.match(r"^\s*\[([^\]]+)\]", line)
        if head:
            cur = head.group(1).strip()
            values[cur] = {}
        elif cur is not None and not line.strip().startswith(";"):
            kv = re.match(r"^\s*([A-Za-z0-9_.]+)\s*=\s*([^;]*)", line)
            if kv:
                values[cur][kv.group(1).lower()] = kv.group(2).strip()
    return values.get(name, {})


def geometry_block():
    text = read(MAIN)
    start = text.index(BEGIN)
    end = text.index(END, start)
    return text[start:end]


def numbers(text):
    return [float(v) for v in text.split(",")]


def lua_literal(values):
    return "{" + ",".join(repr(float(v)) for v in values) + "}"


def check_section(label, values, frame_w, frame_h):
    problems = []
    try:
        pos = numbers(values["menu.pos"])
        pitch = numbers(values["menu.item.spacing"])[1]
        rows = max(1, int(float(values.get("menu.window.visibleitems", "10"))))
        align = int(values["menu.item.font"].split(",")[2].strip())
        band = numbers(values["menu.boxcursor.coords"])
    except (KeyError, ValueError, IndexError) as exc:
        return [f"{label}: the section has no layout numbers ({exc})"]

    lua = LuaRuntime(unpack_returned_tuples=True)
    g = lua.globals()
    lua.execute(STUB)
    lua.execute(geometry_block())
    lua.execute(
        "m = {pos = %s, item = {spacing = {0, %r}, offset = {0, 0},"
        " value = {offset = {447, 0}, active = {offset = {447, 0}},"
        " conflict = {offset = {447, 0}}},"
        " info = {offset = {0, 0}, active = {offset = {0, 0}}}}}"
        % (lua_literal(pos), pitch)
    )

    if pos[0] != frame_w / 2:
        problems.append(f"{label}: menu.pos.x is {pos[0]:.0f}, not the frame's middle")
    if align != 0:
        problems.append(f"{label}: rows are not centre-aligned")

    row_h = max(45.0, band[3] - band[1] + 1)
    for i in range(1, rows + 1):
        x, y = lua.eval("main.f_menuItemPos(m, %d, 0, 0, 0)" % i)
        if abs(x - frame_w / 2) > 0.01:
            problems.append(f"{label}: row {i} is placed at x={x:.0f}, not centred")
        want = pos[1] + (i - 1) * pitch
        if abs(y - want) > 0.01:
            problems.append(f"{label}: row {i} is placed at y={y:.0f}, not {want:.0f}")
    last = pos[1] + (rows - 1) * pitch + row_h
    if last > frame_h - 20:
        problems.append(f"{label}: row {rows} ends at y={last:.0f} on a {frame_h:.0f} frame")
    centre = (pos[1] + last) / 2.0
    if abs(centre - frame_h / 2) > 100:
        problems.append(f"{label}: the block centres on y={centre:.0f}, not the middle")

    # the baked base must be ignored: a sprite already sitting at the stock
    # anchor still lands where the section says. The sprite is a name so the
    # stub's table can be read back from Python.
    lua.execute("SPR['spr1'] = {BASE_X, BASE_Y}")
    ok = lua.eval("main.f_menuItemPlace('spr1', 960, 300)")
    if not ok:
        problems.append(f"{label}: a row could not be placed at all")
    placed = g.SPR["spr1"]
    if abs(placed[1] - 960) > 0.01 or abs(placed[2] - 300) > 0.01:
        problems.append(f"{label}: the baked sprite base still decides the row "
                        f"(drew at {placed[1]:.0f},{placed[2]:.0f})")
    if len(g.POS) != 1:
        problems.append(f"{label}: placing a row set {len(g.POS)} positions, not one")

    # a build without textImgSetPos still draws, by the old additive path
    g.textImgSetPos = None
    lua.execute("SPR['spr2'] = {BASE_X, BASE_Y}")
    if not lua.eval("main.f_menuItemPlace('spr2', 0, 0)"):
        problems.append(f"{label}: a build without textImgSetPos cannot place a row")
    return problems


def movelist_block():
    text = read(MAIN)
    start = text.index(MOV_BEGIN)
    return text[start:text.index(MOV_END, start)]


def check_movelist(label, values, frame_w):
    """The command list's window and heading have to straddle the frame."""
    problems = []
    try:
        pos = numbers(values["movelist.pos"])
        width = float(values["movelist.window.width"])
        title = numbers(values["movelist.title.offset"])
        toff = numbers(values["movelist.text.offset"])
    except (KeyError, ValueError, IndexError) as exc:
        return [f"{label}: the command list has no geometry ({exc})"]

    if abs((pos[0] + width) - (frame_w - pos[0])) > 1:
        problems.append(f"{label}: command list window {pos[0]:.0f}..{pos[0]+width:.0f} "
                        "is not symmetric on the frame")
    if abs(pos[0] + title[0] - frame_w / 2) > 1:
        problems.append(f"{label}: command list heading at x={pos[0]+title[0]:.0f}, "
                        "not the frame's middle")

    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("main = {}")
    lua.execute(movelist_block())
    lua.execute("sec = {movelist = {pos = %s, text = {offset = %s}, title = {offset = %s}}}"
                % (lua_literal(pos), lua_literal(toff), lua_literal(title)))
    for i in (1, 3, 7):
        x, y = lua.eval("main.f_movelistPos(sec, %d, 750, 0, 41)" % i)
        want_x = pos[0] + toff[0] + 750
        want_y = pos[1] + toff[1] + 41 * (i - 1)
        if abs(x - want_x) > 0.01:
            problems.append(f"{label}: row {i} is placed at x={x:.0f}, not {want_x:.0f}")
        if abs(y - want_y) > 0.01:
            problems.append(f"{label}: row {i} is placed at y={y:.0f}, not {want_y:.0f}")
    ty = lua.eval("main.f_movelistTitleY(sec)")
    if abs(ty - (pos[1] + title[1])) > 0.01:
        problems.append(f"{label}: heading y={ty:.0f}, not {pos[1] + title[1]:.0f}")

    menu_text = read(MENU)
    if "textImgAddPos" in menu_text:
        problems.append(f"{label}: the command list still adds to a baked sprite base")
    return problems


def main():
    problems = []
    try:
        text = read(DEF)
    except OSError as exc:
        print(f"cannot read data/ikemen1/system.def: {exc}")
        return 1
    lc = re.search(r"^\s*localcoord\s*=\s*(\d+)\s*,\s*(\d+)", text, re.I | re.M)
    frame_w, frame_h = (float(lc.group(1)), float(lc.group(2))) if lc else (1920.0, 1080.0)
    names = [n for n in re.findall(r"^\s*\[([^\]]+)\]", text, re.M)
             if n.strip().lower().endswith("pause menu")]
    if not names:
        problems.append("system.def has no pause menu sections")
    for name in names:
        found = check_section(f"[{name}]", section_values(text, name), frame_w, frame_h)
        print(f"  {'ok ' if not found else 'FAIL'} [{name}]")
        for line in found:
            print(f"       {line}")
        problems += found

    for name in names:
        found = check_movelist(f"[{name}]", section_values(text, name), frame_w)
        print(f"  {'ok ' if not found else 'FAIL'} [{name}] command list")
        for line in found:
            print(f"       {line}")
        problems += found

    devhelp = read(DEVHELP)
    if "textImgSetPos(sec.movelist.title.TextSpriteData" not in devhelp:
        problems.append("the developer key heading is still added to its base")
    else:
        print("  ok  developer key heading is placed, not added")

    if problems:
        print(f"\nthe pause list regressed in {len(problems)} place(s)")
        return 1
    print("\nthe pause list is centred, fits the frame and ignores the baked sprite base")
    return 0


if __name__ == "__main__":
    sys.exit(main())
