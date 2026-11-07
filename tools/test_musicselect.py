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
NOTICE = os.path.join(ROOT, "external", "mods", "modnotice.lua")

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
draws, logs, frames, texts, WRITES = {}, {}, 0, {}, {}
INPUT_DOWN, ESC_READY, RIGHT_FRAMES = false, false, 0
FILE_TEXT, JSON = '', {}

local function sprite(tag) return { tag = tag } end

print = function(...)
    local bits = {}
    for i = 1, select('#', ...) do bits[#bits + 1] = tostring((select(i, ...))) end
    logs[#logs + 1] = table.concat(bits, ' ')
end

textImgNew = function() return sprite('new') end
-- writes are captured, not performed: a test must not leave files in the repo
io = { open = function(path)
    local handle = { data = '' }
    function handle:write(s) self.data = self.data .. s; WRITES[path] = self.data end
    function handle:read() return '' end
    function handle:close() end
    return handle
end }
textImgReset = function() end
textImgAddPos = function() end
textImgSetAlign = function() end
textImgSetColor = function() end
textImgSetPos = function(t, x, y) POSX, POSY = x, y end
textImgSetText = function(t, s) texts[#texts + 1] = s; if t ~= nil then t.text = s end end
textImgSetFont = function() end
-- the shared sprite's face measures about 30px per character at 1.0, which puts
-- the longest album name past the screen at 1.5x: the reason the head is fitted
LAST_SCALE, DRAWN, SPRITED, POS = { 1, 1 }, {}, {}, {}
POSX, POSY = 0, 0
textImgSetScale = function(t, sx, sy) LAST_SCALE = { sx or 1, sy or 1 } end
textImgGetTextWidth = function(t) return #tostring(t ~= nil and t.text or '') * 30 end
textImgDraw = function(t)
    draws[#draws + 1] = t and t.tag or '?'
    if t ~= nil and t.text ~= nil then
        DRAWN[t.text] = LAST_SCALE[1]
        SPRITED[t.text] = t.tag
        POS[t.text] = { POSX, POSY }
    end
end
sndPlay = function() end
resetKey = function() end
clearColor = function() end
bgReset = function() end
bgDraw = function() end
sffNew = function() return {} end
animNew = function() return {} end
animUpdate = function() end
-- the cover: what the browser asks the engine for, so the test can tell the
-- difference between "drawn" and "drawn in the right place, at the right size"
ANIM = { localcoord = nil, pos = nil, window = nil, draws = 0 }
animSetLocalcoord = function(a, w, h) ANIM.localcoord = { w, h } end
animSetPos = function(a, x, y) ANIM.pos = { x, y } end
animSetWindow = function(a, x1, y1, x2, y2) ANIM.window = { x1, y1, x2, y2 } end
animSetScale = function(a, sx, sy) ANIM.scale = { sx, sy } end
animDraw = function(a) ANIM.draws = ANIM.draws + 1 end
-- deliberately broken: the browser must not need the engine's decoder
jsonDecode = function() error('this build has no jsonDecode') end
getKey = function() return '' end
-- Escape stays down for the first frames: when the stub answered it on frame
-- one the browser left before a single key was read, so no test could ever get
-- past the "Default" album or see the artwork.
refresh = function() frames = frames + 1; if frames > 2 then ESC_READY = true end end
esc = function(clear) if clear == false then ESC_READY = false; return false end return ESC_READY end
getInput = function(player, keys)
    if type(keys) == 'table' then
        local first = keys[1]
        -- one step right, then the key is released: the browser opens on the
        -- "Default" option album, which has no cover art to draw
        if first == 'R' and RIGHT_FRAMES > 0 then
            RIGHT_FRAMES = RIGHT_FRAMES - 1
            return true
        end
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
        menu = { done = { key = { 'b' } }, cancel = { key = { 'm' } },
                 item = { TextSpriteData = sprite('row'),
                          active = { TextSpriteData = sprite('rowon') } } },
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
if MODE == 'nofile' then
    -- no engine reader and no io.open: the file really is missing
    main.f_fileRead = function() return nil end
    io = { open = function() return nil end }
end
if MODE == 'notextimg' then
    -- a build where a fresh text sprite cannot be made at all
    textImgNew = function() return nil end
end
if MODE == 'badfont' then
    -- and one where assigning a font raises: the browser no longer assigns one
    textImgSetFont = function() error('this build cannot set a font') end
end
if MODE == 'faildraw' then
    -- the browser raises mid-frame, the way a missing engine binding would
    main.f_itemnameUpper = function() error('this build cannot measure text') end
end
"""

# label, motif shape
MODES = [
    ("the [OptionBGdef] this screenpack ships, no bgclearcolor", "nobgclearcolor"),
    ("[OptionBGdef] with a clear colour", "solid"),
    ("no [OptionBGdef], title backdrop only", "nooptionbg"),
    ("a backdrop that refuses to draw", "baddraw"),
    ("a build where a new text sprite cannot be made", "notextimg"),
    ("a build where assigning a font raises", "badfont"),
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
    titles = []
    if raw:
        lua.execute("JSON = " + lua_literal(json.loads(raw)))
        for album in json.loads(raw).values():
            if isinstance(album, dict):
                for song in (album.get("Songs") or {}).values():
                    if isinstance(song, dict) and song.get("Title"):
                        titles.append(str(song["Title"]))

    with open(NOTICE, encoding="utf-8") as handle:
        lua.execute(handle.read())
    with open(MOD, encoding="utf-8") as handle:
        lua.execute(handle.read())

    if not lua.eval("type(menu.t_itemname['music']) == 'function'"):
        problems.append("the pause menu entry was not registered")
    if not lua.eval("type(main.t_itemname.music) == 'function'"):
        problems.append("the title menu entry was not registered")
    if problems:
        return problems

    # selecting MUSIC from the pause menu, done key held. One step right first:
    # album one is the "Default" option row and has no artwork, so a screen that
    # only ever showed that album would still hide a broken cover.
    g.INPUT_DOWN = True
    g.RIGHT_FRAMES = 1
    lua.execute("menu.t_itemname['music'](nil, 1, 1, 0, motif.pause_menu.pause_menu)")
    problems += after_press(lua, g, "pause menu")
    # a draw count alone does not prove the albums reached the screen: one empty
    # row per slot draws too. A real track title has to be among the strings.
    if titles:
        drawn = [str(v) for v in g.texts.values()] if g.texts else []
        if not any(title in d for title in titles for d in drawn):
            problems.append("no track title from data/music.json reached the screen")
    # The cover: an animation left in the engine's default coordinate space was
    # drawn six times its size in the bottom-right corner. It has to be opened in
    # the motif's own space, placed at the cover column, and drawn.
    lc = g.ANIM.localcoord
    if lc is None:
        problems.append("the cover is never given the motif's local coordinates")
    elif abs(lc[1] - 1920) > 0.5 or abs(lc[2] - 1080) > 0.5:
        problems.append(f"the cover is opened in localcoord {lc[1]}x{lc[2]}, not 1920x1080")
    pos = g.ANIM.pos
    if pos is None:
        problems.append("the cover is never positioned")
    elif abs(pos[1] - 470) > 0.5 or abs(pos[2] - 470) > 0.5:
        problems.append(f"the cover is placed at {pos[1]},{pos[2]}, not 470,470")
    if (g.ANIM.draws or 0) == 0:
        problems.append("the cover animation is never drawn")
    # fitted, not cropped: the scale it is drawn at must put the whole packed
    # cover inside the 660x680 box
    sizes = [(a.get("ArtW"), a.get("ArtH"))
             for a in json.loads(raw).values() if a.get("ArtW") and a.get("ArtH")]
    sc = [g.ANIM.scale and g.ANIM.scale[1], g.ANIM.scale and g.ANIM.scale[2]]
    if not sc:
        problems.append("the cover is never scaled to its box")
    elif sizes:
        for w, h in sizes:
            if w * sc[0] > 660 + 0.5 or h * sc[1] > 680 + 0.5:
                problems.append(
                    f"a {w}x{h} cover is drawn {w * sc[0]:.0f}x{h * sc[1]:.0f}, past its box")
    # The album title has to fit: at the stub's 30px per character the 44-letter
    # name is 1980px wide at 1.5x, so the head must be measured and scaled down
    # instead of running off both edges of a 1920 screen.
    heads = {str(k): float(v) for k, v in (g.DRAWN or {}).items() if "OST" in str(k).upper()}
    if not heads:
        problems.append("no album title reached the screen")
    # the title belongs in the frame at the top of the screen, not halfway down it
    head_y = [float(v[2]) for k, v in (g.POS or {}).items() if "OST" in str(k).upper()]
    if head_y and min(head_y) > 120:
        problems.append(f"the album title is drawn at y {min(head_y):.0f}, below its frame")
    for text, scale in heads.items():
        if scale > 1.5 + 1e-6:
            problems.append(f"the album title is drawn at {scale:.2f}x, above its own maximum")
        width = len(text) * 30 * scale
        if width > 1800 + 0.5:
            problems.append(f"the album title is {width:.0f}px wide on a 1920px screen")
    # and the rows: they start at x 880, so 980px is all the room a title has,
    # they carry no marker character, and the cursor is the motif's own highlight
    rows = {str(k): float(v) for k, v in (g.DRAWN or {}).items() if str(k) in titles}
    if not rows:
        problems.append("no track rows reached the screen")
    if any(str(k).startswith(("> ", "  ")) for k in (g.DRAWN or {})):
        problems.append("a row is still marked with a '>' instead of the menu highlight")
    sprited = {str(k): str(v) for k, v in (g.SPRITED or {}).items()}
    if "rowon" not in sprited.values():
        problems.append("the selected row is not drawn with the menu's active sprite")
    if "row" not in sprited.values():
        problems.append("the other rows are not drawn with the menu's item sprite")
    for text, scale in rows.items():
        width = len(text) * 30 * scale
        if width > 980 + 0.5:
            problems.append(
                f"the row {text.strip()[:28]!r} is {width:.0f}px wide past the list edge")
    g.INPUT_DOWN = False

    # and from the title menu, which opens the same browser in place
    lua.execute("menu.itemname = ''")
    lua.execute("main.t_itemname.music(nil, 1)")
    problems += after_press(lua, g, "title menu")
    if g.menu.itemname != "":
        problems.append("the browser left the menu in a selected state")
    return problems


def notice_problems(g, screen: str, console: str) -> list[str]:
    problems: list[str] = []
    drawn = [str(v) for v in g.texts.values()] if g.texts else []
    if not any(screen in text for text in drawn):
        problems.append(f"nothing said {screen!r} on screen (drew {len(drawn)} strings)")
    logs = [str(v) for v in g.logs.values()] if g.logs else []
    if not any(console in line for line in logs):
        problems.append("the console line is missing")
    return problems


def engine_for(mode: str, raw: str):
    lua = LuaRuntime(unpack_returned_tuples=True)
    g = lua.globals()
    lua.execute(PRELUDE, mode)
    g.FILE_TEXT = raw
    if raw:
        lua.execute("JSON = " + lua_literal(json.loads(raw)))
    with open(NOTICE, encoding="utf-8") as handle:
        lua.execute(handle.read())
    with open(MOD, encoding="utf-8") as handle:
        lua.execute(handle.read())
    return lua, g


def failure_cases():
    cases = []
    # the album list is empty: open() bails, and the player must be told
    lua, g = engine_for("nobgclearcolor", "{}")
    g.INPUT_DOWN = True          # the done key: the handler only opens on a press
    lua.execute("pcall(menu.t_itemname['music'], nil, 1, 1, 0, motif.pause_menu.pause_menu)")
    cases.append(("an empty album list reports on screen",
                  notice_problems(g, "No music albums found", "no album with songs")))
    # the browser raises mid-frame: the handler must not leave it silent
    with open(MUSIC, encoding="utf-8") as handle:
        raw = handle.read()
    lua, g = engine_for("faildraw", raw)
    g.INPUT_DOWN = True
    lua.execute("menu.t_itemname['music'](nil, 1, 1, 0, motif.pause_menu.pause_menu)")
    problems = notice_problems(g, "Music list:", "could not open from the pause menu")
    written = None
    if g.WRITES:
        try:
            written = g.WRITES["save/music_error.txt"]
        except Exception:
            written = None
    if written is None or "could not open from the pause menu" not in str(written):
        problems.append("the raise was not written to save/music_error.txt")
    cases.append(("a raise inside the browser reports on screen and in a file", problems))
    # the data file itself is missing: the console must say so, not "no albums"
    lua, g = engine_for("nofile", "")
    g.FILE_TEXT = ""
    g.INPUT_DOWN = True
    lua.execute("menu.t_itemname['music'](nil, 1, 1, 0, motif.pause_menu.pause_menu)")
    cases.append(("a missing music.json says so on screen",
                  notice_problems(g, "No music albums found", "is missing or empty")))
    return cases


def main() -> int:
    failures = []
    for label, mode in MODES:
        problems = check(mode)
        print(f"  {'ok ' if not problems else 'FAIL'} {label}"
              + ("" if not problems else f": {'; '.join(problems)}"))
        if problems:
            failures.append((label, problems))
    for label, problems in failure_cases():
        print(f"  {'ok ' if not problems else 'FAIL'} {label}"
              + ("" if not problems else f": {'; '.join(problems)}"))
        if problems:
            failures.append((label, problems))
    if failures:
        print(f"\nthe music browser regressed in {len(failures)} case(s)")
        return 1
    print("\nthe music browser opens, draws its albums and hands the menu back in every motif shape")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
