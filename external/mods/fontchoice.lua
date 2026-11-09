--;===========================================================
--; FONT
--;===========================================================
-- The menus, the fighter names and the label rows are not drawn from a font
-- file while the game runs: tools/build_fonts.py bakes them into three bitmap
-- faces, registered in the motif as font10, font11 and font12. It bakes two
-- sets into identical cells - the gold logo face the game has always worn, and
-- the Karate face added for the player - so swapping one for the other changes
-- the letterforms and nothing else: same height, same advance, same rows.
--
-- Options > Font picks a set. The motif is read once, at startup, so a
-- pick lands on the next launch; the row's own label says so. The choice is
-- kept in save/font.cfg, and the motif's three font lines are pointed at it
-- from here on every load as well, so a rebuild that reset them is corrected
-- at the next start instead of silently forgetting what was picked.
--
-- The row itself is put on the options screen by appending to options.t_itemname
-- and options.t_vardisplay, which is the hook the engine's own options script
-- documents for external modules. Without those handlers the engine would draw
-- the motif's row and do nothing when it is pressed.

local FILE = 'save/font.cfg'
local MOTIF = 'data/ikemen1/system.def'
-- The in-game HUD is a file of its own and names the same two faces for the
-- lifebar names and the demo caption, so the pick has to follow it there too.
-- Its numbers are baked art rather than a font line, so those simply ship in
-- the picked face.
local HUD = 'data/fight.def'

-- The two faces, in the order the row steps through them.
local ORDER = {'karate', 'original'}
local NAME = {karate = 'KARATE', original = 'ORIGINAL'}
local SETS = {
	karate = {
		[10] = 'ikemen1/fonts/DisplayK.def',
		[11] = 'ikemen1/fonts/BodyK.def',
		[12] = 'ikemen1/fonts/DisplayActiveK.def',
	},
	original = {
		[10] = 'ikemen1/fonts/Display.def',
		[11] = 'ikemen1/fonts/Body.def',
		[12] = 'ikemen1/fonts/DisplayActive.def',
	},
}
local HUD_SET = {
	karate = {
		[10] = 'ikemen1/fonts/DisplayK.def',
		[11] = 'ikemen1/fonts/BodyK.def',
	},
	original = {
		[10] = 'ikemen1/fonts/Display.def',
		[11] = 'ikemen1/fonts/Body.def',
	},
}
-- What a fresh install wears: the face this was asked for.
local DEFAULT = 'karate'

local fontchoice = {}

local function canRead()
	return type(io) == 'table' and io.open ~= nil
end

local function readAll(path)
	if not canRead() then
		return nil
	end
	local file = io.open(path, 'r')
	if file == nil then
		return nil
	end
	local text = file:read('*a')
	file:close()
	return text
end

local function writeAll(path, text)
	if not canRead() then
		return false
	end
	local file = io.open(path, 'w')
	if file == nil then
		return false
	end
	file:write(text)
	file:close()
	return true
end

-- The pick on disk, or the default when there is no file, no io, or a value
-- this build no longer has a face for.
function fontchoice.choice()
	local text = readAll(FILE)
	if type(text) == 'string' then
		local picked = text:lower():match('font%s*=%s*([%w_]+)')
		if picked ~= nil and SETS[picked] ~= nil then
			return picked
		end
	end
	return DEFAULT
end

function fontchoice.save(choice)
	if SETS[choice] == nil then
		return false
	end
	return writeAll(FILE, '; Picked in Options > Font.\n'
		.. '; Read by external/mods/fontchoice.lua.\n'
		.. 'font = ' .. choice .. '\n')
end

-- Point the motif's three font lines at one set. Pure, and it reports how many
-- lines actually moved, so it can be checked without touching a file: a second
-- pass over the same text moves nothing.
function fontchoice.applyTo(text, choice, mapping)
	local set = mapping or SETS[choice]
	if set == nil or type(text) ~= 'string' then
		return text, 0
	end
	local moved = 0
	for index in pairs(set) do
		local value = set[index]
		-- Anchored to the start of a line and to the bare key, so the
		-- font10.height line beside it and any commented-out copy are left
		-- alone, and only the value is replaced - the line's own ending, its
		-- spacing and its trailing comment all survive.
		text = text:gsub('(\n[ \t]*font' .. index .. '[ \t]*=[ \t]*)([^;%s][^;\r\n]*)',
			function(head, old)
				if old == value then
					return head .. old
				end
				moved = moved + 1
				return head .. value
			end)
	end
	return text, moved
end

function fontchoice.apply(choice)
	choice = choice or fontchoice.choice()
	if SETS[choice] == nil then
		return false, 0
	end
	local wrote, total = false, 0
	for _, target in ipairs({{MOTIF, SETS[choice]}, {HUD, HUD_SET[choice]}}) do
		local text = readAll(target[1])
		if text ~= nil then
			local updated, moved = fontchoice.applyTo(text, choice, target[2])
			if moved > 0 then
				wrote = writeAll(target[1], updated) or wrote
				total = total + moved
			end
		end
	end
	return wrote, total
end

function fontchoice.next(choice)
	choice = choice or fontchoice.choice()
	for i, name in ipairs(ORDER) do
		if name == choice then
			return ORDER[(i % #ORDER) + 1]
		end
	end
	return ORDER[1]
end

function fontchoice.label(choice)
	return NAME[choice or fontchoice.choice()] or NAME[DEFAULT]
end

fontchoice.t_sets = SETS
fontchoice.t_order = ORDER

local function installRow()
	if type(options) ~= 'table' or type(options.t_itemname) ~= 'table'
		or type(options.t_vardisplay) ~= 'table' then
		return false
	end
	local function display()
		return fontchoice.label()
	end
	local handler = function(t, item, cursorPosY, moveTxt)
		-- A two-state row, so either direction steps it, the way Fullscreen
		-- and Keep Aspect Ratio answer to both keys.
		if getInput(-1, motif.option_info.menu.add.key, motif.option_info.menu.subtract.key) then
			sndPlay(motif.Snd, motif.option_info.cursor.move.snd[1], motif.option_info.cursor.move.snd[2])
			local picked = fontchoice.next()
			fontchoice.save(picked)
			fontchoice.apply(picked)
			if type(t) == 'table' and type(t.items) == 'table' and t.items[item] ~= nil then
				t.items[item].vardisplay = fontchoice.label(picked)
			end
			options.modified = true
		end
		return true
	end
	-- The engine keys a row by the last part of its itemname; the row is
	-- declared as "font" on the Options screen (an earlier build put it inside
	-- the Video submenu), so both spellings are registered.
	options.t_itemname['font'] = handler
	options.t_itemname['menuvideo_font'] = handler
	options.t_vardisplay['font'] = display
	options.t_vardisplay['menuvideo_font'] = display
	return true
end

fontchoice.installed = installRow()

-- Heal a motif whose font lines were reset (a rebuild regenerates them from the
-- colours in build_fonts.py), so the saved pick is what the next launch reads.
fontchoice.apply()

return fontchoice
