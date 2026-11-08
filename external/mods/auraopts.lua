--;===========================================================
--; AURA GLOW OPTIONS
--;===========================================================
-- data/aura.zss (written by tools/build_aura.py from tools/aura.zss) draws a
-- glow around each fighter as their power climbs. Its glowing state reads its
-- numbers from the character's own maps, and this file is what fills them in:
-- the settings below are pushed to every player each frame, so changing one on
-- this screen is live in the fight the menu was opened over.
--
-- The module is loaded from here too, with commonStatesInsert, so the player
-- never has to add "data/aura.zss" to a States line in save/config.ini.
--
-- The screen is the pause menu's own text sprite, drawn over the paused fight -
-- the same approach external/mods/devhelp.lua and musicselect.lua use, because a
-- textImgNew sprite given a font opened an empty screen on a real build here.
--
-- Settings persist in save/aura.cfg as "key = value" lines, so a choice survives
-- a restart without anyone editing a file by hand.

local FILE = 'save/aura.cfg'
local MODULE = 'data/aura.zss'

local COLOURS = {
	{name = 'RED',    r = 255, g = 0,   b = 0},
	{name = 'ORANGE', r = 255, g = 140, b = 0},
	{name = 'GREEN',  r = 0,   g = 255, b = 0},
	{name = 'CYAN',   r = 0,   g = 220, b = 255},
	{name = 'BLUE',   r = 40,  g = 90,  b = 255},
	{name = 'PURPLE', r = 170, g = 60,  b = 255},
	{name = 'GOLD',   r = 255, g = 210, b = 90},
	{name = 'WHITE',  r = 255, g = 255, b = 255},
}

local MODE_NAMES = {'OFF', 'POWER COLOURS', 'SINGLE COLOUR'}
local LIFE_STEPS = {0, 50, 30, 15}
local LIFE_NAMES = {[0] = 'ANY TIME', [50] = 'BELOW 50% LIFE',
                    [30] = 'BELOW 30% LIFE', [15] = 'BELOW 15% LIFE'}

-- mode:  0 off, 1 the module's own power ladder, 2 one colour
-- life:  0 always, otherwise show the aura below this percentage of life
local CFG = {mode = 1, colour = 1, size = 10, alpha = 100, quality = 50, life = 0}

local DEFAULT = {mode = 1, colour = 1, size = 10, alpha = 100, quality = 50, life = 0}

local function clampInt(value, lo, hi, fallback)
	value = tonumber(value)
	if value == nil then
		return fallback
	end
	if value < lo then return lo end
	if value > hi then return hi end
	return math.floor(value + 0.5)
end

local function tidy()
	CFG.mode = clampInt(CFG.mode, 0, 2, DEFAULT.mode)
	CFG.colour = clampInt(CFG.colour, 1, #COLOURS, DEFAULT.colour)
	CFG.size = clampInt(CFG.size, 4, 20, DEFAULT.size)
	CFG.alpha = clampInt(CFG.alpha, 40, 220, DEFAULT.alpha)
	CFG.quality = clampInt(CFG.quality, 10, 70, DEFAULT.quality)
	local life = clampInt(CFG.life, 0, 100, DEFAULT.life)
	for _, v in ipairs(LIFE_STEPS) do
		if v == life then CFG.life = life; return end
	end
	CFG.life = 0
end

local function load()
	local ok = pcall(function()
		local f = io.open(FILE, 'r')
		if f == nil then
			return
		end
		for line in f:lines() do
			local key, value = line:match('^%s*([%a_]+)%s*=%s*(-?%d+)%s*$')
			if key ~= nil and CFG[key] ~= nil then
				CFG[key] = tonumber(value)
			end
		end
		f:close()
	end)
	if not ok then
		print('auraopts: could not read ' .. FILE .. ' - using the defaults')
	end
	tidy()
end

local function save()
	local ok, err = pcall(function()
		local f = io.open(FILE, 'w')
		if f == nil then
			error('cannot open ' .. FILE .. ' for writing')
		end
		f:write('# aura glow settings, written by the in-game Aura screen\n')
		for _, key in ipairs({'mode', 'colour', 'size', 'alpha', 'quality', 'life'}) do
			f:write(string.format('%s = %d\n', key, CFG[key]))
		end
		f:close()
	end)
	if not ok then
		print('auraopts: could not save ' .. FILE .. ': ' .. tostring(err))
	end
end

load()

--;===========================================================
--; PUSH THE SETTINGS INTO THE FIGHT
--;===========================================================
-- 1.0 renamed charMapSet to mapSet and the argument lists moved with it, so each
-- shape is tried once and whichever the engine accepts is used from then on. A
-- build that accepts none leaves the module on its own defaults instead of
-- taking the screen down with it.
local CANDIDATES = {
	function(p, k, v) return mapSet(p, k, v, 'set') end,
	function(p, k, v) return mapSet(p, k, v) end,
	function(p, k, v) return charMapSet(p, k, v, 'set') end,
	function(p, k, v) return charMapSet(p, k, v) end,
}
local setter
local failed = false

local function applyMap(p, key, value)
	if failed then
		return false
	end
	if setter ~= nil and pcall(setter, p, key, value) then
		return true
	end
	for _, fn in ipairs(CANDIDATES) do
		if pcall(fn, p, key, value) then
			setter = fn
			return true
		end
	end
	failed = true
	print('auraopts: this build has no writable character maps - '
		.. 'the aura keeps its built-in colours')
	return false
end

local function sync()
	if failed then
		return
	end
	local colour = COLOURS[CFG.colour] or COLOURS[1]
	local single = (CFG.mode == 2) and 1 or 0
	local off = (CFG.mode == 0) and 1 or 0
	for p = 1, 8 do
		applyMap(p, 'btlc_aura_off', off)
		applyMap(p, 'btlc_aura_single', single)
		applyMap(p, 'btlc_aura_size', CFG.size)
		applyMap(p, 'btlc_aura_alpha', CFG.alpha)
		applyMap(p, 'btlc_aura_quality', CFG.quality)
		applyMap(p, 'btlc_aura_life', CFG.life)
		applyMap(p, 'btlc_aura_r', colour.r)
		applyMap(p, 'btlc_aura_g', colour.g)
		applyMap(p, 'btlc_aura_b', colour.b)
	end
end

if type(hook) == 'table' and type(hook.add) == 'function' then
	hook.add('loop', 'auraopts', function()
		if type(game) == 'function' and game() then
			sync()
		end
	end)
end

local loaded
local okLoad, errLoad = pcall(function()
	if type(commonStatesInsert) ~= 'function' then
		error('commonStatesInsert is not available in this build')
	end
	commonStatesInsert(MODULE)
	loaded = true
end)
if not okLoad then
	print('auraopts: could not load ' .. MODULE .. ': ' .. tostring(errLoad))
end

--;===========================================================
--; THE SCREEN
--;===========================================================
local ROWS = {
	{
		label = 'AURA',
		value = function() return MODE_NAMES[CFG.mode + 1] end,
		step = function(d)
			CFG.mode = (CFG.mode + d) % 3
			if CFG.mode < 0 then CFG.mode = 2 end
		end,
	},
	{
		label = 'COLOUR',
		value = function() return COLOURS[CFG.colour].name end,
		step = function(d)
			CFG.colour = CFG.colour + d
			if CFG.colour < 1 then CFG.colour = #COLOURS end
			if CFG.colour > #COLOURS then CFG.colour = 1 end
		end,
		dim = function() return CFG.mode ~= 2 end,
	},
	{
		label = 'SIZE',
		value = function() return tostring(CFG.size) end,
		step = function(d) CFG.size = CFG.size + d * 1 end,
		dim = function() return CFG.mode == 0 end,
	},
	{
		label = 'OPACITY',
		value = function() return tostring(CFG.alpha) end,
		step = function(d) CFG.alpha = CFG.alpha + d * 10 end,
		dim = function() return CFG.mode == 0 end,
	},
	{
		label = 'DETAIL',
		value = function() return tostring(CFG.quality) end,
		step = function(d) CFG.quality = CFG.quality + d * 5 end,
		dim = function() return CFG.mode == 0 end,
	},
	{
		label = 'SHOW WHEN',
		value = function() return LIFE_NAMES[CFG.life] or 'ANY TIME' end,
		step = function(d)
			local at = 1
			for i, v in ipairs(LIFE_STEPS) do
				if v == CFG.life then at = i end
			end
			at = at + d
			if at < 1 then at = #LIFE_STEPS end
			if at > #LIFE_STEPS then at = 1 end
			CFG.life = LIFE_STEPS[at]
		end,
		dim = function() return CFG.mode == 0 end,
	},
	{
		label = 'RESET',
		value = function() return 'BACK TO DEFAULTS' end,
		step = function()
			for k, v in pairs(DEFAULT) do CFG[k] = v end
			save()
			sync()
		end,
		action = true,
	},
}

local PALE = {208, 186, 136}
local GOLD = {255, 228, 140}
local DIMC = {128, 112, 84}
local LABELW = 16

local function screenSize()
	local w, h = 1920, 1080
	pcall(function()
		local lc = motif.info.localcoord
		if lc ~= nil and lc[1] ~= nil and lc[2] ~= nil and lc[1] > 0 and lc[2] > 0 then
			w, h = lc[1], lc[2]
		end
	end)
	return w, h
end

local function key(sec, name, fallback)
	local got, value = pcall(function()
		return sec.menu[name].key
	end)
	if got and value ~= nil then
		return value
	end
	return fallback
end

local function drawRow(txt, text, x, y, colour, scale)
	pcall(function()
		textImgReset(txt)
		textImgSetAlign(txt, 1)                    -- 1 = left
		pcall(textImgSetScale, txt, scale, scale)
		textImgSetColor(txt, colour[1], colour[2], colour[3], 255)
		textImgSetText(txt, text)
		textImgSetPos(txt, x, y)
		textImgDraw(txt)
	end)
end

local function auraDraw(sec)
	pcall(rectDraw, sec.movelist.overlay.RectData)

	local sw, sh = screenSize()
	local ok, txt = pcall(function() return sec.movelist.text.TextSpriteData end)
	if not ok or txt == nil then
		return
	end
	local title = nil
	pcall(function() title = sec.movelist.title.TextSpriteData end)

	local y = sh * 0.16
	if title ~= nil then
		pcall(function()
			textImgReset(title)
			textImgSetAlign(title, 0)              -- 0 = centred
			textImgSetText(title, 'AURA')
			textImgSetPos(title, sw / 2, y)
			textImgDraw(title)
		end)
	end
	y = y + 70

	local x = sw * 0.24
	local pitch = 52
	for i, row in ipairs(ROWS) do
		local here = (i == menu.cursorPosY)
		local dimmed = (row.dim ~= nil) and row.dim()
		local colour = PALE
		if dimmed then
			colour = DIMC
		end
		if here then
			colour = GOLD
		end
		local value = row.value()
		drawRow(txt, string.format('%-' .. LABELW .. 's%s', row.label, value),
			x, y + (i - 1) * pitch, colour, 1)
	end

	y = y + (#ROWS) * pitch + 30
	drawRow(txt, 'UP / DOWN  ROW      LEFT / RIGHT  CHANGE', x, y, DIMC, 0.8)
	drawRow(txt, 'Z  SAVE AND CLOSE      ESC  CLOSE', x, y + 34, DIMC, 0.8)

	local status = 'aura module loaded'
	if not loaded then
		status = 'aura module NOT loaded - see console'
	elseif failed then
		status = 'colour changes need a build with writable maps'
	end
	drawRow(txt, status, x, y + 74, DIMC, 0.8)

	-- leave the shared sprite as the pause menu expects it
	pcall(textImgReset, txt)
	pcall(textImgSetScale, txt, 1, 1)
end

local function auraUpdate(sec)
	local up = key(sec, 'up', {'U'})
	local down = key(sec, 'down', {'D'})
	local left = key(sec, 'left', {'L'})
	local right = key(sec, 'right', {'R'})

	if getInput(-1, up) then
		menu.cursorPosY = menu.cursorPosY - 1
		if menu.cursorPosY < 1 then menu.cursorPosY = #ROWS end
	elseif getInput(-1, down) then
		menu.cursorPosY = menu.cursorPosY + 1
		if menu.cursorPosY > #ROWS then menu.cursorPosY = 1 end
	elseif getInput(-1, right) then
		local row = ROWS[menu.cursorPosY]
		if row ~= nil then
			row.step(1)
			tidy()
			sync()
			if row.action then save() end
		end
	elseif getInput(-1, left) then
		local row = ROWS[menu.cursorPosY]
		if row ~= nil then
			row.step(-1)
			tidy()
			sync()
			if row.action then save() end
		end
	end

	if esc() or getInput(-1, key(sec, 'cancel', {'ESC'}), key(sec, 'done', {'a'})) then
		pcall(function() sndPlay(motif.Snd, sec.cancel.snd[1], sec.cancel.snd[2]) end)
		save()
		sync()
		menu.itemname = ''
		menu.cursorPosY = menu.pauseCursor or 1
	end
end

local okMenu, errMenu = pcall(function()
	-- Pause menu entry. The row itself is declared by tools/build_aura.py; this
	-- registers what it opens.
	menu.t_itemname['aura'] = function(t, item, cursorPosY, moveTxt, sec)
		if getInput(-1, sec.menu.done.key) then
			pcall(function() sndPlay(motif.Snd, sec.cursor.done.snd[1], sec.cursor.done.snd[2]) end)
			-- the pause menu's own cursor is borrowed for this screen, so
			-- remember where it was and give it back on the way out
			if menu.itemname ~= 'aura' then
				menu.pauseCursor = menu.cursorPosY
			end
			menu.cursorPosY = 1
			menu.itemname = 'aura'
		end
		return true
	end

	-- menu.f_run draws the pause menu's own screens; this adds ours to the list.
	local baseRun = menu.f_run
	menu.f_run = function()
		if menu.itemname == 'aura' then
			local drawn, drawErr = pcall(function()
				local sec = motif.pause_menu.pause_menu
				pcall(auraUpdate, sec)
				auraDraw(sec)
			end)
			if not drawn then
				print('auraopts: could not draw the aura screen: ' .. tostring(drawErr))
				if type(modNotice) == 'function' then
					pcall(modNotice, 'auraopts: ' .. tostring(drawErr),
						'Aura settings unavailable - see console.')
				end
				menu.itemname = ''
			end
			local active = main.pauseMenuActive
			if not active then
				menu.pauseExitDelay = -1
			end
			return active
		end
		return baseRun()
	end
end)

if not okMenu then
	print('auraopts: the aura screen was not registered: ' .. tostring(errMenu))
end
