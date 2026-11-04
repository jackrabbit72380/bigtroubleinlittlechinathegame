"""Run external/mods/devhelp.lua against a stubbed engine.

The Developer Keys screen once closed itself instead of opening: an engine call
raised, and the frame handler answers a drawing error by closing the screen, so
the pause menu item looked dead. This test puts the mod in front of a fake engine
that can behave like each build we might meet, and asserts that the screen opens
and draws in every one.

It is not a substitute for running Ikemen itself - tools/engine_linux.sh does that.
It is the regression net that catches the class of bug the real engine showed us,
and it runs in a second.

    python3 -m pip install lupa      # once
    python3 tools/test_devhelp.py

Exits 0 when every behaviour passes, 1 on a regression, and 77 when lupa is not
installed (the check could not run).
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, "external", "mods", "devhelp.lua")

try:
    import lupa
except ImportError:                                    # pragma: no cover
    print("SKIP: lupa is not installed (python3 -m pip install lupa)")
    raise SystemExit(77)

from lupa import LuaRuntime

PRELUDE = r"""
MODE = ...
draws = {}
basecalls = 0
print = function() end

local function sprite(tag) return { tag = tag } end

textImgNew = function()
    if MODE == 'nonew' then error('this build has no textImgNew') end
    return sprite('new')
end
textImgSetAlign = function() end
textImgSetScale = function()
    if MODE == 'noscale' then error('this build has no textImgSetScale') end
end
textImgSetColor = function() end
textImgSetPos = function() end
textImgSetText = function() end
textImgSetFont = function(t, f)
    if MODE == 'index' and type(f) ~= 'number' then error('font must be an index') end
    if MODE == 'table' and type(f) ~= 'table' then error('font must be a table') end
end
textImgDraw = function(t) table.insert(draws, t and t.tag or '?') end
textImgReset = function() end
textImgAddPos = function() end
rectDraw = function() end
sndPlay = function() end
getInput = function() return INPUT_DOWN end
esc = function() return false end
addHotkey = function() end

INPUT_DOWN = false

motif = {
    Snd = {},
    files = { font = { font11 = { size = { 7, 20 }, spacing = { 0, 3 } } } },
    pause_menu = { pause_menu = {
        movelist = {
            overlay = { RectData = {} },
            title = { TextSpriteData = sprite('title') },
            text = { TextSpriteData = sprite('text'), font = { 11 }, spacing = { 3, 3 } },
        },
        menu = { cancel = { key = 'a' }, done = { key = 'b' },
                 previous = { key = 'c' }, next = { key = 'd' } },
        cancel = { snd = { 1, 2 } },
        cursor = { done = { snd = { 1, 2 } } },
    } },
}
main = { pauseMenuActive = true }
menu = { t_itemname = {}, itemname = '', f_run = function() basecalls = basecalls + 1; return true end }
"""

# label, engine behaviour
MODES = [
    ("font takes an index", "index"),
    ("font takes a table", "table"),
    ("no textImgNew", "nonew"),
    ("no textImgSetScale", "noscale"),
]


def check(mode: str) -> list[str]:
    problems: list[str] = []
    lua = LuaRuntime(unpack_returned_tuples=True)
    g = lua.globals()
    lua.execute(PRELUDE, mode)
    with open(MOD, encoding="utf-8") as handle:
        lua.execute(handle.read())

    # the pause menu handler: pressing "done" must select our screen
    g.INPUT_DOWN = True
    lua.execute("menu.t_itemname.devkeys(nil, 1, 1, 0, motif.pause_menu.pause_menu)")
    if g.menu.itemname != "devkeys":
        problems.append("selecting the item did not open the screen")
    g.INPUT_DOWN = False

    # the frame that draws it
    ok = lua.eval("(function() return pcall(menu.f_run) end)")()
    if not ok:
        problems.append("drawing the frame raised")
    if g.menu.itemname != "devkeys":
        problems.append("the screen closed itself instead of drawing")
    tags = list(g.draws.values())
    if tags.count("new") + tags.count("text") < 12:
        problems.append(f"only {len(tags)} draw calls; the list did not render")

    # and the pause menu still runs when our screen is not selected
    lua.execute("menu.itemname = ''")
    lua.execute("menu.f_run()")
    if g.basecalls != 1:
        problems.append("the pause menu did not run underneath")
    return problems


def main() -> int:
    failures = []
    for label, mode in MODES:
        problems = check(mode)
        print(f"  {'ok ' if not problems else 'FAIL'} {label}"
              + ("" if not problems else f": {'; '.join(problems)}"))
        if problems:
            failures.append((label, problems))
    if failures:
        print(f"\nthe developer keys screen regressed in {len(failures)} engine behaviour(s)")
        return 1
    print("\nthe developer keys screen opens and draws in every engine behaviour")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
