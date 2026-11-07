"""Run external/mods/musicselect.lua against a stubbed engine.

The MUSIC item in the pause menu once did nothing at all. [OptionBGdef] in this
screenpack carries no bgclearcolor line, the browser read it unguarded inside
open(), and the pause menu's handler caught the raise in a pcall that only
printed, so the item looked dead. This test puts the mod in front of a fake
engine shaped like the motifs we ship - the backdrop with the key, without it,
without a bgdef at all, and refusing to draw entirely - and asserts that the
browser opens, draws its albums and hands the menu back in every one, so a motif
change that loses a key fails here instead of in a menu.

It is not a substitute for running Ikemen itself - tools/engine_linux.sh does
that. It runs in a second and needs data/music.json, which ships.

    python3 -m pip install lupa      # once
    python3 tools/test_musicselect.py

Exits 0 when every behaviour passes, 1 on a regression, and 77 when lupa is not
installed (the check could not run).
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, "external", "mods", "musicselect.lua")
MUSIC = os.path.join(ROOT, "data", "music.json")

# The browser draws a title, the album tabs and a page of rows; anything under
# this means it opened but had nothing to show.
MIN_DRAWS = 10

try:
    import lupa
except ImportError:                                    # pragma: no cover
    print("SKIP: lupa is not installed (python3 -m pip install lupa)")
    raise SystemExit(77)

from lupa import LuaRuntime

PRELUDE = r"""
local MODE = ...
draws, logs, frames = {}, {}, 0
INPUT_DOWN, ESC_READY = false, false
FILE_TEXT, JSON = '', {}

local function sprite(tag) return { tag = tag } end

print = function(...)
    local bits = {}
    for i = 1, select('#', ...) do bits[#bits + 1] = tostring((select(i, ...))) end
    logs[#logs + 1] = table.concat(bits, ' ')
end

textImgNew = function() return sprite('new') end
textImgReset = function() end
textImgAddPos = function() end
textImgSetAlign = function() end
textImgSetColor = function() end
textImgSetPos = function() end
textImgSetText = function() end
textImgSetFont = function() end
textImgSetScale = function() end
textImgGetTextWidth = function() return 120 end
textImgDraw = function(t) draws[#draws + 1] = t and t.tag or '?' end
sndPlay = function() end
resetKey = function() end
clearColor = function() end
bgReset = function() end
bgDraw = function() end
sffNew = function() return {} end
animNew = function() return {} end
animUpdate = function() end
jsonDecode = function() return JSON end
refresh = function() frames = frames + 1; ESC_READY = true end
esc = function(clear) if clear == false then ESC_READY = false; return false end return ESC_READY end
getInput = function(player, keys)
    if type(keys) == 'table' then
        local first = keys[1]
        if first == 'U' or first == 'D' or first == 'L' or first == 'R' then return false end
    end
    return INPUT_DOWN
end

-- The engine hands the browser motif.optionbgdef; the shipped one has no
-- bgclearcolor, which is the shape that used to kill the screen.
local function backdrop()
    local bg = { BGDef = {} }
    if MODE ~= 'nobgclearcolor' and MODE ~= 'baddraw' then bg.bgclearcolor = { 0, 0, 0 } end
    return bg
end

motif = {
    info = { localcoord = { 1920, 1080 } },
    Snd = {},
    files = { font = { font10 = { size = { 7, 20 }, spacing = { 0, 3 } },
                       font11 = { size = { 7, 20 }, spacing = { 0, 3 } } } },
    option_info = {
        title = { font = 10 },
        keymenu = { item = { font = 11 } },
        menu = { done = { key = { 'a' } } },
        cursor = { move = { snd = { 1, 0 } }, done = { snd = { 1, 1 } } },
    },
    titlebgdef = { bgclearcolor = { 0, 0, 0 }, BGDef = {} },
    title_info = { menu = {} },
    pause_menu = { pause_menu = {
        menu = { done = { key = { 'b' } }, cancel = { key = { 'm' } } },
        cursor = { done = { snd = { 1, 1 } } },
        exit = { snd = { 1, 2 } }, cancel = { snd = { 1, 2 } },
        overlay = { RectData = {} },
        movelist = { title = { TextSpriteData = sprite('title') },
                     text = { TextSpriteData = sprite('text'), font = { 11 }, spacing = { 3, 3 } } },
    } },
}
if MODE ~= 'nooptionbg' then
    motif.optionbgdef = backdrop()
end
if MODE == 'baddraw' then
    bgDraw = function() error('this build cannot draw a backdrop') end
end

main = {
    pauseMenuActive = true,
    t_itemname = {},
    f_fileRead = function(path) return FILE_TEXT end,
    f_itemnameUpper = function(text) return text end,
    f_animPosDraw = function() end,
    f_appendItemname = function() end,
}
menu = { t_itemname = {}, itemname = '', f_run = function() return true end }
"""

# label, motif shape
MODES = [
    ("the [OptionBGdef] this screenpack ships, no bgclearcolor", "nobgclearcolor"),
    ("[OptionBGdef] with a clear colour", "solid"),
    ("no [OptionBGdef], title backdrop only", "nooptionbg"),
    ("a backdrop that refuses to draw", "baddraw"),
]


def lua_literal(value):
    if isinstance(value, dict):
        return "{" + ",".join("[%s]=%s" % (lua_literal(k), lua_literal(v)) for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "{" + ",".join(lua_literal(v) for v in value) + "}"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if value is None:
        return "nil"
    return '"%s"' % str(value).replace("\\", "\\\\").replace('"', '\\"')


def after_press(lua, g, where: str) -> list[str]:
    """What the last screen did, and clear the record for the next one."""
    problems: list[str] = []
    for line in ([str(v) for v in g.logs.values()] if g.logs else []):
        if "could not open" in line or "was not registered" in line:
            problems.append(f"{where}: {line}")
    if g.frames < 1:
        problems.append(f"{where}: the browser never ran a frame")
    drawn = len(list(g.draws.values())) if g.draws else 0
    if drawn < MIN_DRAWS:
        problems.append(f"{where}: only {drawn} draw calls; the albums did not render")
    lua.execute("draws, logs, frames = {}, {}, 0")
    return problems


def check(mode: str) -> list[str]:
    problems: list[str] = []
    lua = LuaRuntime(unpack_returned_tuples=True)
    g = lua.globals()
    lua.execute(PRELUDE, mode)

    try:
        with open(MUSIC, encoding="utf-8") as handle:
            raw = handle.read()
    except OSError as exc:
        return [f"cannot read data/music.json: {exc}"]
    g.FILE_TEXT = raw
    lua.execute("JSON = " + lua_literal(json.loads(raw)))

    with open(MOD, encoding="utf-8") as handle:
        lua.execute(handle.read())

    if not lua.eval("type(menu.t_itemname['music']) == 'function'"):
        problems.append("the pause menu entry was not registered")
    if not lua.eval("type(main.t_itemname.music) == 'function'"):
        problems.append("the title menu entry was not registered")
    if problems:
        return problems

    # selecting MUSIC from the pause menu, done key held
    g.INPUT_DOWN = True
    lua.execute("menu.t_itemname['music'](nil, 1, 1, 0, motif.pause_menu.pause_menu)")
    problems += after_press(lua, g, "pause menu")
    g.INPUT_DOWN = False

    # and from the title menu, which opens the same browser in place
    lua.execute("menu.itemname = ''")
    lua.execute("main.t_itemname.music(nil, 1)")
    problems += after_press(lua, g, "title menu")
    if g.menu.itemname != "":
        problems.append("the browser left the menu in a selected state")
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
        print(f"\nthe music browser regressed in {len(failures)} motif shape(s)")
        return 1
    print("\nthe music browser opens, draws its albums and hands the menu back in every motif shape")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
