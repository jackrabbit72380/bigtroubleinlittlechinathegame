--;===========================================================
--; FONT
--;===========================================================
-- The game does not draw its text from a font file while it runs. Every face it
-- wears - the menu rows, the lifebar names, the round timer, the hit and combo
-- counters - is pre-painted art, baked by tools/build_fonts.py. That is why this
-- screen cannot simply change a point size: it picks one of the baked sets.
--
-- Options > Font opens the list below. Face steps between the gold logo face
-- and the Karate face; each size row steps between three baked sizes (S, M, L)
-- for that one face; Save writes the pick to save/font.cfg and points the motif
-- and the HUD at the matching files. Both files are read once, at startup, so a
-- saved change lands on the next launch - the Save row says so.
--
-- Nothing is written until Save is pressed, so backing out of the screen leaves
-- the game exactly as it was.

local FILE = 'save/font.cfg'
-- Measured letter heights, written by the generator with the faces themselves.
local METRICS = 'data/ikemen1/fonts/metrics.txt'
local MOTIF = 'data/ikemen1/system.def'
local HUD = 'data/fight.def'

local GROUPS = {'display', 'body', 'names', 'wins', 'info', 'timer', 'combo',
	'hits', 'power', 'round'}
local STEPS = {'S', 'M', 'L'}
-- Ink height of each face at its middle setting: what the rows print, so the
-- numbers on screen are the same ones the docs talk about.
local INK = {
	karate = {display = 77, body = 32, names = 25, wins = 14, info = 13,
		timer = 31, combo = 38, hits = 25, power = 20, round = 110},
	original = {display = 58, body = 23, names = 25, wins = 14, info = 13,
		timer = 31, combo = 38, hits = 25, power = 20, round = 110},
}
local FACE_NAME = {karate = 'KARATE', original = 'ORIGINAL'}
local ORDER = {'karate', 'original'}
-- %s is the size suffix: '' for M, '_S' or '_L' for the baked variants.
local KARATE = {
	display = 'ikemen1/fonts/DisplayK%s.def',
	active = 'ikemen1/fonts/DisplayActiveK%s.def',
	body = 'ikemen1/fonts/BodyK%s.def',
	names = 'ikemen1/fonts/Menu2%s.def',
	wins = 'ikemen1/fonts/Menu2Small%s.def',
	info = 'ikemen1/fonts/Pixel%s.def',
	timer = 'ikemen1/fonts/Timer%s.def',
	combo = 'ikemen1/fonts/ComboCounter%s.def',
	hits = 'ikemen1/fonts/HitNum%s.def',
	power = 'ikemen1/fonts/PowerbarNum%s.def',
	round = 'ikemen1/fonts/Round%s.def',
}
-- The original pick restores the two menu faces. The HUD's numbers were never
-- engraved in both typefaces, so they keep the shipped art whatever this says.
local ORIGINAL = {
	display = 'ikemen1/fonts/Display.def',
	active = 'ikemen1/fonts/DisplayActive.def',
	body = 'ikemen1/fonts/Body.def',
	names = 'ikemen1/fonts/Menu2.def',
	wins = 'ikemen1/fonts/Menu2Small.def',
	info = 'ikemen1/fonts/Pixel.def',
	timer = 'ikemen1/fonts/Timer.def',
	combo = 'ikemen1/fonts/ComboCounter.def',
	hits = 'ikemen1/fonts/HitNum.def',
	power = 'ikemen1/fonts/PowerbarNum.def',
	round = 'ikemen1/fonts/Round.def',
}
-- Which font index in each file draws which group.
local SYSTEM_INDEX = {{10, 'display'}, {11, 'body'}, {12, 'active'}}
local HUD_INDEX = {{1, 'names'}, {2, 'timer'}, {3, 'wins'}, {4, 'power'},
	{6, 'combo'}, {7, 'hits'}, {8, 'info'}, {9, 'round'}, {10, 'display'},
	{11, 'body'}}
-- Groups whose sizes only exist in the Karate set.
local KARATE_ONLY = {names = true, wins = true, info = true, timer = true,
	combo = true, hits = true, power = true, round = true}

local DEFAULT_FACE = 'karate'
local DEFAULT_STEP = 'M'

-- group -> step -> letter height, read from the shipped metrics
local HEIGHT = {}

local fontchoice = {}
local state = {face = DEFAULT_FACE, steps = {}}
local saved = {face = DEFAULT_FACE, steps = {}}
for _, group in ipairs(GROUPS) do
	state.steps[group] = DEFAULT_STEP
	saved.steps[group] = DEFAULT_STEP
end

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

local function hasStep(step)
	for _, v in ipairs(STEPS) do
		if v == step then
			return true
		end
	end
	return false
end

-- Replace one font index's path. Anchored to a line start and to the bare key,
-- so a commented copy, a longer key and the line's own ending are left alone.
local function setLine(text, index, value)
	local moved = 0
	-- %d, not "..": a number arriving as 7.0 would otherwise key look for font7.0
	local key = string.format('font%d', math.floor(tonumber(index) or 0))
	-- \r and \n are spelled out: %r is not a Lua character class, and inside a
	-- set it reads as a literal "r", which let the carriage return be swallowed
	-- into the value and quietly turned every CRLF line into a bare LF.
	text = text:gsub('(\n[ \t]*' .. key .. '[ \t]*=[ \t]*)([^;%s][^;\r\n]*)',
		function(head, old)
			if old == value then
				return head .. old
			end
			moved = moved + 1
			return head .. value
		end)
	return text, moved
end

local function paths()
	local out = {}
	local base = state.face == 'karate' and KARATE or ORIGINAL
	for _, group in ipairs(GROUPS) do
		local tmpl = base[group]
		if state.face == 'karate' then
			local step = state.steps[group] or DEFAULT_STEP
			out[group] = tmpl:format(step == 'M' and '' or ('_' .. step))
		else
			out[group] = tmpl
		end
	end
	if state.face == 'karate' then
		local step = state.steps.display or DEFAULT_STEP
		out.active = KARATE.active:format(step == 'M' and '' or ('_' .. step))
	else
		out.active = ORIGINAL.active
	end
	return out
end

local function indexMap(pairs_)
	local out = {}
	for _, pair in ipairs(pairs_) do
		out[pair[1]] = pair[2]
	end
	return out
end

-- Pure: rewrite the font lines of one file to a set of paths, and report how
-- many moved, so it can be tested without touching a file.
function fontchoice.applyTo(text, want)
	if type(text) ~= 'string' or type(want) ~= 'table' then
		return text, 0
	end
	local moved = 0
	for index, value in pairs(want) do
		local one, n = setLine(text, index, value)
		text, moved = one, moved + n
	end
	return text, moved
end

function fontchoice.apply()
	local want = paths()
	local wrote, total = false, 0
	local targets = {
		{MOTIF, indexMap(SYSTEM_INDEX)},
		{HUD, indexMap(HUD_INDEX)},
	}
	for _, target in ipairs(targets) do
		local text = readAll(target[1])
		if text ~= nil then
			local out = {}
			for index, group in pairs(target[2]) do
				out[index] = want[group]
			end
			local updated, moved = fontchoice.applyTo(text, out)
			if moved > 0 then
				wrote = writeAll(target[1], updated) or wrote
				total = total + moved
			end
		end
	end
	return wrote, total
end

local function loadMetrics()
	local text = readAll(METRICS)
	if type(text) ~= 'string' then
		return
	end
	for group, step, px in text:gmatch('(%a+)%s+([SML])%s+(%d+)') do
		HEIGHT[group] = HEIGHT[group] or {}
		HEIGHT[group][step] = tonumber(px)
	end
end

local function load()
	local text = readAll(FILE)
	if type(text) ~= 'string' then
		return
	end
	local face = text:lower():match('font%s*=%s*([%w_]+)')
	if face ~= nil and FACE_NAME[face] ~= nil then
		state.face = face
		saved.face = face
	end
	for _, group in ipairs(GROUPS) do
		local step = text:match('size%.' .. group .. '%s*=%s*(%a)')
		if step ~= nil and hasStep(step:upper()) then
			state.steps[group] = step:upper()
			saved.steps[group] = step:upper()
		end
	end
end

function fontchoice.save()
	local out = {'; Picked in Options > Font.', '; Read by external/mods/fontchoice.lua.',
		'font = ' .. state.face}
	for _, group in ipairs(GROUPS) do
		table.insert(out, 'size.' .. group .. ' = ' .. state.steps[group])
	end
	if not writeAll(FILE, table.concat(out, '\n') .. '\n') then
		return false
	end
	saved.face = state.face
	for _, group in ipairs(GROUPS) do
		saved.steps[group] = state.steps[group]
	end
	fontchoice.apply()
	return true
end

function fontchoice.discard()
	state.face = saved.face
	for _, group in ipairs(GROUPS) do
		state.steps[group] = saved.steps[group]
	end
end

function fontchoice.dirty()
	if state.face ~= saved.face then
		return true
	end
	for _, group in ipairs(GROUPS) do
		if state.steps[group] ~= saved.steps[group] then
			return true
		end
	end
	return false
end

function fontchoice.face()
	return state.face
end

function fontchoice.step(group)
	return state.steps[group] or DEFAULT_STEP
end

function fontchoice.nextFace()
	for i, name in ipairs(ORDER) do
		if name == state.face then
			state.face = ORDER[(i % #ORDER) + 1]
			return state.face
		end
	end
	state.face = ORDER[1]
	return state.face
end

function fontchoice.nextStep(group)
	local step = state.steps[group] or DEFAULT_STEP
	for i, name in ipairs(STEPS) do
		if name == step then
			state.steps[group] = STEPS[(i % #STEPS) + 1]
			return state.steps[group]
		end
	end
	state.steps[group] = DEFAULT_STEP
	return state.steps[group]
end

-- What a row prints: the letter height that step actually draws.
function fontchoice.label(group)
	if group == 'face' then
		return FACE_NAME[state.face]
	end
	if group == 'save' then
		return fontchoice.dirty() and 'Press to save *' or 'Saved'
	end
	if state.face == 'original' and KARATE_ONLY[group] then
		return 'KARATE only'
	end
	local step = state.steps[group] or DEFAULT_STEP
	local px = nil
	if state.face == 'karate' and HEIGHT[group] ~= nil then
		px = HEIGHT[group][step]
	end
	if px == nil then
		local factor = (step == 'S' and 0.9) or (step == 'L' and 1.15) or 1.0
		px = math.floor(INK[state.face][group] * factor + 0.5)
	end
	return step .. '  ' .. px .. ' px' .. (fontchoice.dirty() and ' *' or '')
end

fontchoice.t_groups = GROUPS
fontchoice.t_steps = STEPS

local ROWS = {'face', 'display', 'body', 'names', 'wins', 'info', 'timer', 'combo',
	'hits', 'power', 'round', 'save'}

local function installRows()
	if type(options) ~= 'table' or type(options.t_itemname) ~= 'table'
		or type(options.t_vardisplay) ~= 'table' then
		return false
	end
	local function rowChanged(t, item)
		if type(t) == 'table' and type(t.items) == 'table' and t.items[item] ~= nil then
			t.items[item].vardisplay = fontchoice.label(t.items[item].itemname)
		end
		options.modified = true
	end
	for _, group in ipairs(ROWS) do
		local function display()
			return fontchoice.label(group)
		end
		local handler = function(t, item)
			-- Every row answers both directions, the way Fullscreen does, and
			-- wraps: S -> M -> L -> S and KARATE -> ORIGINAL -> KARATE.
			if getInput(-1, motif.option_info.menu.add.key, motif.option_info.menu.subtract.key) then
				sndPlay(motif.Snd, motif.option_info.cursor.move.snd[1], motif.option_info.cursor.move.snd[2])
				if group == 'face' then
					fontchoice.nextFace()
				elseif group == 'save' then
					fontchoice.save()
				else
					fontchoice.nextStep(group)
				end
				-- the save row's own label says Saved or Press to save, and every
				-- other row grows or loses its unsaved marker
				for _, name in ipairs(ROWS) do
					options.t_vardisplay[name] = options.t_vardisplay[name]
				end
				rowChanged(t, item)
			end
			return true
		end
		options.t_itemname[group] = handler
		options.t_vardisplay[group] = display
		-- the row may be declared as fontmenu_<group>; the engine keys a submenu
		-- row by the last part of its itemname, so both spellings answer.
		options.t_itemname['fontmenu_' .. group] = handler
		options.t_vardisplay['fontmenu_' .. group] = display
	end
	return true
end

loadMetrics()
load()
fontchoice.installed = installRows()

-- Heal files a rebuild reset (the generator writes the shipped default), so the
-- saved pick is what the next launch reads.
fontchoice.apply()

return fontchoice
