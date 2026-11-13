--;===========================================================
--; AURA GLOW OPTIONS
--;===========================================================
-- data/aura.zss (written by tools/build_aura.py from tools/aura.zss) draws a
-- glow around each fighter. Its glowing state reads its numbers from the
-- character's own maps, and this file is what fills them in.
--
-- DESIGNING
--   TARGET picks whose glow is on the bench: EVERYONE, or one of the characters
--   in the match (read with player()/name(), the same pair debug.lua uses).
--   The rows edit a draft, and sync() pushes the draft to the players the target
--   covers every frame - so the fight itself is the preview once a match is
--   running. APPLY stores the draft as that target's own look. RESET puts the
--   draft back to defaults without storing it. Characters with their own entry
--   keep it; EVERYONE only fills in the rest.
--
-- TWO KINDS, one module:
--   GLOW  the released Glow.zss numbers: one steady colour, full brightness,
--         a tight radius, at any power.
--   AURA  the same glow function driven by power: red from 1000, green from
--         2000, a colour that cycles from 3000 - or one colour, if STYLE says
--         SINGLE COLOUR.
-- Each kind remembers its own SIZE / OPACITY / DETAIL / LAYER / MIN POWER /
-- SHOW WHEN. Rows that cannot affect the current choice are greyed out.
--
-- The sample on the right is drawn from the same scatter the module uses -
-- copies of one word instead of copies of the fighter's current animation
-- frame. The fight blends them additively and this screen does not, so treat
-- its brightness as a guide, not a match.
--
-- The screen is the pause menu's own text sprite, drawn over the paused fight -
-- the same approach external/mods/devhelp.lua and musicselect.lua use, because a
-- textImgNew sprite given a font opened an empty screen on a real build here.
--
-- Settings persist in save/aura.cfg, one [section] per target, so choices
-- survive a restart without anyone editing a file by hand.

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

local TYPE_NAMES = {'OFF', 'GLOW', 'AURA'}
local STYLE_NAMES = {'POWER LADDER', 'SINGLE COLOUR'}
local LAYER_NAMES = {'BEHIND', 'IN FRONT'}
local LIFE_STEPS = {0, 50, 30, 15}
local LIFE_NAMES = {[0] = 'ANY TIME', [50] = 'BELOW 50% LIFE',
                    [30] = 'BELOW 30% LIFE', [15] = 'BELOW 15% LIFE'}
local POWER_STEPS = {0, 1000, 2000, 3000}
local POWER_NAMES = {[0] = 'ANY POWER', [1000] = '1000+',
                     [2000] = '2000+', [3000] = '3000+'}

local KINDS = {'glow', 'aura'}
local FIELDS = {'size', 'alpha', 'quality', 'life', 'layer', 'minpower'}

-- type:  0 off, 1 GLOW, 2 AURA
-- style: 1 the power ladder, 2 one colour (AURA only)
-- layer: 1 behind the fighter (a halo), 2 in front of it (a wash)
local function defaults()
	return {
		type = 2,
		style = 1,
		colour = 1,
		glow = {size = 6, alpha = 256, quality = 30, life = 0, layer = 1, minpower = 0},
		aura = {size = 10, alpha = 100, quality = 50, life = 0, layer = 1, minpower = 0},
	}
end

local DEFAULT = defaults()

local function copyOf(src)
	local out = {type = src.type, style = src.style, colour = src.colour}
	for _, kind in ipairs(KINDS) do
		out[kind] = {}
		for _, field in ipairs(FIELDS) do
			out[kind][field] = src[kind][field]
		end
	end
	return out
end

local function sameAs(a, b)
	if a.type ~= b.type or a.style ~= b.style or a.colour ~= b.colour then
		return false
	end
	for _, kind in ipairs(KINDS) do
		for _, field in ipairs(FIELDS) do
			if a[kind][field] ~= b[kind][field] then
				return false
			end
		end
	end
	return true
end

local LIMIT = {
	size = {4, 20},
	alpha = {40, 300},
	quality = {10, 70},
}

local function clampInt(value, lo, hi, fallback)
	value = tonumber(value)
	if value == nil then
		return fallback
	end
	if value < lo then return lo end
	if value > hi then return hi end
	return math.floor(value + 0.5)
end

local function onSteps(value, steps, fallback)
	for _, step in ipairs(steps) do
		if step == value then
			return value
		end
	end
	return fallback
end

local function tidyOne(cfg)
	cfg.type = clampInt(cfg.type, 0, 2, DEFAULT.type)
	cfg.style = clampInt(cfg.style, 1, 2, DEFAULT.style)
	cfg.colour = clampInt(cfg.colour, 1, #COLOURS, DEFAULT.colour)
	for _, kind in ipairs(KINDS) do
		local got, fallback = cfg[kind], DEFAULT[kind]
		if type(got) ~= 'table' then
			got = {}
			cfg[kind] = got
		end
		got.size = clampInt(got.size, LIMIT.size[1], LIMIT.size[2], fallback.size)
		got.alpha = clampInt(got.alpha, LIMIT.alpha[1], LIMIT.alpha[2], fallback.alpha)
		got.quality = clampInt(got.quality, LIMIT.quality[1], LIMIT.quality[2], fallback.quality)
		got.layer = clampInt(got.layer, 1, 2, fallback.layer)
		got.life = onSteps(clampInt(got.life, 0, 100, fallback.life), LIFE_STEPS, 0)
		got.minpower = onSteps(clampInt(got.minpower, 0, 3000, fallback.minpower), POWER_STEPS, 0)
	end
end

--;===========================================================
--; SAVED LOOKS, ONE PER TARGET
--;===========================================================
local SAVED = {everyone = defaults()}
local DRAFT = defaults()          -- what the rows edit
local targets = {{key = 'everyone', label = 'EVERYONE'}}
local TARGET = targets[1]
local notice = nil

local function assignValue(cfg, key, value)
	if key == 'type' then
		cfg.type = value
	elseif key == 'style' then
		cfg.style = value
	elseif key == 'colour' then
		cfg.colour = value
	elseif key == 'mode' then              -- written before the two kinds existed
		cfg.type = (value == 0) and 0 or 2
		cfg.style = (value == 2) and 2 or 1
	else
		local kind, field = key:match('^(%a+)_(%a+)$')
		if kind ~= nil and cfg[kind] ~= nil and cfg[kind][field] ~= nil then
			cfg[kind][field] = value
		elseif cfg.aura[key] ~= nil then
			cfg.aura[key] = value           -- a bare "size = 12" from the first version
		end
	end
end

local function load()
	local legacy = {}
	local ok = pcall(function()
		local f = io.open(FILE, 'r')
		if f == nil then
			return
		end
		local section = nil
		for line in f:lines() do
			local header = line:match('^%s*%[(.-)%s*%]%s*$')
			if header ~= nil then
				local key = header:lower()
				if key ~= 'everyone' and SAVED[key] == nil then
					SAVED[key] = defaults()
				end
				section = SAVED[key] or SAVED.everyone
			else
				local field, value = line:match('^%s*([%a_]+)%s*=%s*(-?%d+)%s*$')
				if field ~= nil then
					if section == nil then
						legacy[field] = tonumber(value)
					else
						assignValue(section, field, tonumber(value))
					end
				end
			end
		end
		f:close()
	end)
	if not ok then
		print('auraopts: could not read ' .. FILE .. ' - using the defaults')
	end
	for field, value in pairs(legacy) do
		assignValue(SAVED.everyone, field, value)
	end
	for _, cfg in pairs(SAVED) do
		tidyOne(cfg)
	end
	DRAFT = copyOf(SAVED.everyone)
end

local function save()
	local keys = {}
	for key in pairs(SAVED) do
		keys[#keys + 1] = key
	end
	table.sort(keys)
	local ok, err = pcall(function()
		local f = io.open(FILE, 'w')
		if f == nil then
			error('cannot open ' .. FILE .. ' for writing')
		end
		f:write('# aura glow settings, written by the in-game Aura screen\n')
		f:write('# one section per target: everyone, or a character name in lowercase\n')
		for _, key in ipairs(keys) do
			local cfg = SAVED[key]
			f:write(string.format('[%s]\n', key))
			f:write(string.format('type = %d\n', cfg.type))
			f:write(string.format('style = %d\n', cfg.style))
			f:write(string.format('colour = %d\n', cfg.colour))
			for _, kind in ipairs(KINDS) do
				for _, field in ipairs(FIELDS) do
					f:write(string.format('%s_%s = %d\n', kind, field, cfg[kind][field]))
				end
			end
		end
		f:close()
	end)
	if not ok then
		print('auraopts: could not save ' .. FILE .. ': ' .. tostring(err))
	end
end

-- The numbers the chosen kind is using right now.
local function active()
	if DRAFT.type == 1 then
		return DRAFT.glow
	end
	return DRAFT.aura
end

--;===========================================================
--; WHO IS WHO
--;===========================================================
-- player(n) selects that player and answers whether it exists; name() then
-- reads the selected entity's name. Both are how debug.lua inspects a player,
-- and the current selection is handed back so the engine is left as it was.
local function playerName(p)
	if type(player) ~= 'function' then
		return nil
	end
	local hadId, previous = pcall(id)
	local ok, got = pcall(function()
		if not player(p) then
			return nil
		end
		if type(name) ~= 'function' then
			return nil
		end
		return name()
	end)
	if hadId and previous ~= nil then
		pcall(playerId, previous)
	end
	if ok and type(got) == 'string' and got ~= '' then
		return got
	end
	return nil
end

-- EVERYONE first, then each character in the match once.
local function refreshTargets()
	targets = {{key = 'everyone', label = 'EVERYONE'}}
	local seen = {everyone = true}
	for p = 1, 8 do
		local got = playerName(p)
		if got ~= nil then
			local key = got:lower()
			if not seen[key] then
				seen[key] = true
				targets[#targets + 1] = {key = key, label = got:upper()}
			end
		end
	end
	for _, entry in ipairs(targets) do
		if entry.key == TARGET.key then
			TARGET = entry
			return
		end
	end
	TARGET = targets[1]
end

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

-- Whose numbers a player should be wearing right now: the draft when the target
-- covers them, otherwise their own entry, otherwise the shared one.
local function configFor(p, got)
	if got ~= nil and TARGET.key ~= 'everyone' and got:lower() == TARGET.key then
		return DRAFT
	end
	if got ~= nil then
		local own = SAVED[got:lower()]
		if own ~= nil then
			return own
		end
	end
	if TARGET.key == 'everyone' then
		return DRAFT
	end
	return SAVED.everyone
end

local function pushOne(p, cfg)
	local colour = COLOURS[cfg.colour] or COLOURS[1]
	local off = (cfg.type == 0) and 1 or 0
	local kind = (cfg.type == 1) and 1 or 2
	local single = (cfg.style == 2) and 1 or 0
	local under = (cfg.type ~= 0 and cfg[cfg.type == 1 and 'glow' or 'aura'].layer == 2) and 1 or 0
	local got = cfg[cfg.type == 1 and 'glow' or 'aura']

	applyMap(p, 'btlc_aura_off', off)
	applyMap(p, 'btlc_aura_type', kind)
	applyMap(p, 'btlc_aura_style', cfg.style)
	applyMap(p, 'btlc_aura_single', single)
	applyMap(p, 'btlc_aura_under', under)
	applyMap(p, 'btlc_aura_size', got.size)
	applyMap(p, 'btlc_aura_alpha', got.alpha)
	applyMap(p, 'btlc_aura_quality', got.quality)
	applyMap(p, 'btlc_aura_life', got.life)
	applyMap(p, 'btlc_aura_minpower', got.minpower)
	applyMap(p, 'btlc_aura_r', colour.r)
	applyMap(p, 'btlc_aura_g', colour.g)
	applyMap(p, 'btlc_aura_b', colour.b)
end

local function sync()
	if failed then
		return
	end
	for p = 1, 8 do
		local got = playerName(p)
		if got ~= nil then
			local cfg = configFor(p, got)
			if cfg ~= nil then
				pushOne(p, cfg)
			end
		end
	end
end

-- In a match or not. game() is not that test: the engine's game() runs a
-- whole match with the current settings, so asking it from a frame hook
-- started a new match from inside the running one, over and over, until
-- the engine stopped on a stack of "Error executing Lua code: loop".
-- gameRunning() only answers the question; pcall keeps an older build
-- that lacks it from stopping the module.
local function inMatch()
	if type(gameRunning) ~= 'function' then
		return false
	end
	local ok, running = pcall(gameRunning)
	return ok and running == true
end

if type(hook) == 'table' and type(hook.add) == 'function' then
	hook.add('loop', 'auraopts', function()
		if failed or not inMatch() then
			return
		end
		-- A map write that a build refuses must not take the window down with
		-- it: the first refusal turns the push off and says so once.
		local ok, err = pcall(sync)
		if not ok then
			failed = true
			print('auraopts: the aura settings could not be pushed - ' .. tostring(err))
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

load()
refreshTargets()
if TARGET.key == 'everyone' then
	DRAFT = copyOf(SAVED.everyone)
end

--;===========================================================
--; THE SCREEN
--;===========================================================
local ROWS = {
	{
		label = 'DESIGN FOR',
		value = function() return TARGET.label end,
		step = function(d)
			refreshTargets()
			local at = 1
			for i, entry in ipairs(targets) do
				if entry.key == TARGET.key then at = i end
			end
			at = at + d
			if at < 1 then at = #targets end
			if at > #targets then at = 1 end
			TARGET = targets[at]
			DRAFT = copyOf(SAVED[TARGET.key] or DEFAULT)
			notice = nil
		end,
	},
	{
		label = 'TYPE',
		value = function() return TYPE_NAMES[DRAFT.type + 1] end,
		step = function(d)
			DRAFT.type = (DRAFT.type + d) % 3
			if DRAFT.type < 0 then DRAFT.type = 2 end
		end,
	},
	{
		label = 'STYLE',
		value = function() return STYLE_NAMES[DRAFT.style] end,
		step = function()
			DRAFT.style = (DRAFT.style == 1) and 2 or 1
		end,
		dim = function() return DRAFT.type ~= 2 end,
	},
	{
		label = 'COLOUR',
		value = function() return COLOURS[DRAFT.colour].name end,
		step = function(d)
			DRAFT.colour = DRAFT.colour + d
			if DRAFT.colour < 1 then DRAFT.colour = #COLOURS end
			if DRAFT.colour > #COLOURS then DRAFT.colour = 1 end
		end,
		-- the ladder picks its own colours, so COLOUR only matters for GLOW
		-- and for AURA in single-colour mode
		dim = function() return DRAFT.type == 0 or (DRAFT.type == 2 and DRAFT.style == 1) end,
	},
	{
		label = 'LAYER',
		value = function() return LAYER_NAMES[active().layer] end,
		step = function()
			active().layer = (active().layer == 1) and 2 or 1
		end,
		dim = function() return DRAFT.type == 0 end,
	},
	{
		label = 'SIZE',
		value = function() return tostring(active().size) end,
		step = function(d) active().size = active().size + d end,
		dim = function() return DRAFT.type == 0 end,
	},
	{
		label = 'OPACITY',
		value = function() return tostring(active().alpha) end,
		step = function(d) active().alpha = active().alpha + d * 10 end,
		dim = function() return DRAFT.type == 0 end,
	},
	{
		label = 'DETAIL',
		value = function() return tostring(active().quality) end,
		step = function(d) active().quality = active().quality + d * 5 end,
		dim = function() return DRAFT.type == 0 end,
	},
	{
		label = 'MIN POWER',
		value = function() return POWER_NAMES[active().minpower] or 'ANY POWER' end,
		step = function(d)
			local at = 1
			for i, step in ipairs(POWER_STEPS) do
				if step == active().minpower then at = i end
			end
			at = at + d
			if at < 1 then at = #POWER_STEPS end
			if at > #POWER_STEPS then at = 1 end
			active().minpower = POWER_STEPS[at]
		end,
		dim = function() return DRAFT.type == 0 end,
	},
	{
		label = 'SHOW WHEN',
		value = function() return LIFE_NAMES[active().life] or 'ANY TIME' end,
		step = function(d)
			local at = 1
			for i, step in ipairs(LIFE_STEPS) do
				if step == active().life then at = i end
			end
			at = at + d
			if at < 1 then at = #LIFE_STEPS end
			if at > #LIFE_STEPS then at = 1 end
			active().life = LIFE_STEPS[at]
		end,
		dim = function() return DRAFT.type == 0 end,
	},
	{
		label = 'APPLY',
		value = function()
			if sameAs(DRAFT, SAVED[TARGET.key] or DEFAULT) then
				return 'ALREADY SET'
			end
			return 'STORE FOR ' .. TARGET.label
		end,
		step = function()
			SAVED[TARGET.key] = copyOf(DRAFT)
			save()
			sync()
			notice = 'APPLIED TO ' .. TARGET.label
		end,
		action = true,
	},
	{
		label = 'RESET',
		value = function() return 'BACK TO DEFAULTS' end,
		step = function()
			DRAFT = defaults()
			sync()
			notice = 'RESET - PRESS APPLY TO KEEP IT'
		end,
		action = true,
	},
}

local PALE = {208, 186, 136}
local GOLD = {255, 228, 140}
local DIMC = {128, 112, 84}
local LABELW = 13

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

-- The pause list's own text scale: the size every menu in this game is set at,
-- and the sprite these screens borrow. Their offsets were written in multiples of
-- the face's own size, which was the menu's size only while the face was baked at
-- 45px - it is 90px now, so a bare 1 drew a row twice the height of the menus
-- around it. The 0.48 here is used only if the motif cannot be read.
local function menuScale()
	local s = nil
	pcall(function()
		local v = motif.pause_menu.movelist.text.scale
		if v ~= nil and v[1] ~= nil and v[1] > 0 then
			s = v[1]
		end
	end)
	return s or 0.48
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

-- The selected row, haloed in the colour being designed: eight faint copies
-- around the text, the same trick the module uses on the fighter.
local function drawGlowRow(txt, text, x, y, colour, got)
	local reach = 3 + got.size * 0.45
	local base = math.floor(got.alpha / 8)
	if base < 10 then base = 10 end
	if base > 70 then base = 70 end
	for i = 0, 7 do
		local angle = i * math.pi / 4
		local dx, dy = math.cos(angle) * reach, math.sin(angle) * reach
		pcall(function()
			textImgReset(txt)
			textImgSetAlign(txt, 1)
			pcall(textImgSetScale, txt, 0.8 * menuScale(), 0.8 * menuScale())
			textImgSetColor(txt, colour[1], colour[2], colour[3], base)
			textImgSetText(txt, text)
			textImgSetPos(txt, x + dx, y + dy)
			textImgDraw(txt)
		end)
	end
end

-- The module scatters copies of the fighter's current animation frame; this
-- scatters copies of one word with the same grid, colour, opacity and radius.
-- The fight blends additively and this does not, so brightness is only a guide.
local function drawSample(txt, sw, sh)
	local cx, cy = sw * 0.78, sh * 0.40
	drawRow(txt, 'LIVE SAMPLE', cx - 120, cy - 170, DIMC, 0.8 * menuScale())
	drawRow(txt, 'for ' .. TARGET.label, cx - 120, cy - 142, DIMC, 0.8 * menuScale())

	if DRAFT.type == 0 then
		drawRow(txt, 'nothing drawn', cx - 120, cy, DIMC, 0.8 * menuScale())
		return
	end

	local got = active()
	local colour = COLOURS[DRAFT.colour] or COLOURS[1]
	local n = math.floor(got.quality / 10)
	if n < 2 then n = 2 end
	local reach = 50 + got.size * 7
	local step = reach / (n - 1)
	local base = math.floor(got.alpha * 2 / (n * n))
	if base < 6 then base = 6 end
	if base > 60 then base = 60 end

	for i = 0, n - 1 do
		for h = 0, n - 1 do
			pcall(function()
				textImgReset(txt)
				textImgSetAlign(txt, 0)            -- 0 = centred on the point
				pcall(textImgSetScale, txt, menuScale(), menuScale())
				textImgSetColor(txt, colour[1], colour[2], colour[3], base)
				textImgSetText(txt, 'GLOW')
				textImgSetPos(txt, cx + (h - (n - 1) / 2) * step,
					cy + (i - (n - 1) / 2) * step)
				textImgDraw(txt)
			end)
		end
	end

	drawRow(txt, string.format('%d copies at %d each', n * n, base),
		cx - 120, cy + 100, DIMC, 0.8 * menuScale())
	drawRow(txt, string.format('%.0f opacity per copy in the fight',
		got.alpha / (got.quality * 0.25)), cx - 120, cy + 134, DIMC, 0.8 * menuScale())
	if got.minpower > 0 then
		drawRow(txt, string.format('only from %d power', got.minpower),
			cx - 120, cy + 168, DIMC, 0.8 * menuScale())
	end
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

	local y = sh * 0.10
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

	local x = sw * 0.20
	local pitch = 46
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
		local line = string.format('%-' .. LABELW .. 's%s', row.label, value)
		local rowY = y + (i - 1) * pitch
		if here and DRAFT.type ~= 0 then
			drawGlowRow(txt, line, x, rowY, COLOURS[DRAFT.colour], active())
		end
		drawRow(txt, line, x, rowY, colour, 1)
	end

	drawSample(txt, sw, sh)

	y = y + (#ROWS) * pitch + 18
	drawRow(txt, 'UP / DOWN  ROW      LEFT / RIGHT  CHANGE', x, y, DIMC, 0.8 * menuScale())
	drawRow(txt, 'Z  APPLY AND CLOSE      ESC  CLOSE', x, y + 32, DIMC, 0.8 * menuScale())

	local status = notice
	if status == nil then
		if not sameAs(DRAFT, SAVED[TARGET.key] or DEFAULT) then
			status = 'UNSAVED - APPLY TO KEEP IT'
		elseif not loaded then
			status = 'aura module NOT loaded - see console'
		elseif failed then
			status = 'colour changes need a build with writable maps'
		else
			status = 'saved for ' .. TARGET.label
		end
	end
	drawRow(txt, status, x, y + 70, DIMC, 0.8 * menuScale())

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
	elseif getInput(-1, right) or getInput(-1, left) then
		local d = getInput(-1, right) and 1 or -1
		local row = ROWS[menu.cursorPosY]
		if row ~= nil then
			row.step(d)
			tidyOne(DRAFT)
			if row.action then
				notice = notice            -- APPLY/RESET set their own message
			else
				notice = nil
			end
			sync()
		end
	end

	if esc() or getInput(-1, key(sec, 'cancel', {'ESC'}), key(sec, 'done', {'a'})) then
		pcall(function() sndPlay(motif.Snd, sec.cancel.snd[1], sec.cancel.snd[2]) end)
		-- leaving never throws the draft away: it becomes the target's look
		SAVED[TARGET.key] = copyOf(DRAFT)
		save()
		sync()
		notice = nil
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
			notice = nil
			refreshTargets()
			DRAFT = copyOf(SAVED[TARGET.key] or DEFAULT)
			sync()
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
			local activePause = main.pauseMenuActive
			if not activePause then
				menu.pauseExitDelay = -1
			end
			return activePause
		end
		return baseRun()
	end
end)

if not okMenu then
	print('auraopts: the aura screen was not registered: ' .. tostring(errMenu))
end
