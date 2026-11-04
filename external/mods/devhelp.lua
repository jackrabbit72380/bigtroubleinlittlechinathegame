--;===========================================================
--; DEVELOPER KEYS
--;===========================================================
-- Two ways in, both added here because this file is autoloaded from
-- external/mods and survives the asset build, unlike external/script/*.lua:
--
--   pause menu -> Developer Keys   the whole list on one screen
--   Ctrl+F1                        the same list printed into the console
--
-- The screen draws with its own text sprite rather than the motif's movelist
-- one, for two reasons: the size can be picked here (big, two columns, no
-- scrolling) and changing it does not make the pause menu's Move List bigger as
-- a side effect. textImgNew/textImgSetScale are probed once; if a build lacks
-- them the screen falls back to the movelist sprite instead of failing. Every
-- startup step is inside a pcall because this module loads before the window
-- exists, and an error there would stop the game from starting at all.

local devhelp = { body = nil, sub = nil, failed = false }

-- Colour groups: display and view, time and speed, match, players.
local PALE  = {246, 222, 158}
local GOLD  = {240, 196, 88}
local EMBER = {226, 138, 84}
local JADE  = {150, 186, 124}
local DIM   = {150, 128, 92}

-- key, what it does, colour. Deliberately terse: two columns of it have to fit
-- on one screen at a legible size. docs/DEV_KEYS.md carries the long wording.
local LEFT = {
	{'Ctrl+D', 'debug readout', PALE},
	{'Ctrl+Shift+D', 'readout, extended', PALE},
	{'Shift+D', 'readout, pinned', PALE},
	{'Ctrl+C', 'collision boxes', PALE},
	{'Ctrl+W', 'wireframe', PALE},
	{'Ctrl+L', 'stock life bars', PALE},
	{'Ctrl+V', 'vsync on/off', PALE},
	{'Ctrl+S', 'cycle speed', GOLD},
	{'Ctrl+KP+ / KP-', 'speed +-0.01', GOLD},
	{'Pause', 'pause match', GOLD},
	{'ScrollLock', 'frame step', GOLD},
}

local RIGHT = {
	{'Shift+F4', 'RELOAD ENGINE', EMBER},
	{'F1 / Ctrl+F1', 'KO p2 / p1 side', EMBER},
	{'F2 / Ctrl+F2', 'KO all / p1 side', EMBER},
	{'F3', 'max power', EMBER},
	{'Ctrl+Shift+F3', 'max power mode', EMBER},
	{'F4 / F5', 'reset round / timer', EMBER},
	{'Space', 'refill life + power', EMBER},
	{'F9 / F10', 'load / save state', EMBER},
	{'F8', 'clear console', EMBER},
	{'Ctrl+I', 'stand fighters up', EMBER},
	{'Ctrl+1..8', 'toggle AI', JADE},
	{'Ctrl+Alt+1..9', 'take control', JADE},
}

local NOTE = 'needs Options > Engine > Debug Keys enabled'

-- Layout constants, in the screenpack's 1280x720 space.
local KEYW = 14                          -- key column width, in characters
local ROWS = math.max(#LEFT, #RIGHT)     -- taller column decides the height
local TOP, BOTTOM = 96, 700              -- first row, and the floor it must not hit
local LEFT_X, COL_W = 70, 540            -- where the columns start and how wide
local RIGHT_X = LEFT_X + COL_W + 60
local MAXSCALE, MINSCALE = 2.0, 1.0

local function lineOf(row)
	return string.format('%-' .. KEYW .. 's%s', row[1], row[2])
end

local function sceneFont(sec)
	local okf, font = pcall(function()
		return motif.files.font['font' .. sec.movelist.text.font[1]]
	end)
	if okf then return font end
	return nil
end

-- Real glyph metrics, so the scale below is chosen from the font that is
-- actually loaded instead of from a guess.
local function metrics(font)
	local adv, cell, gap = 7, 20, 0
	if font ~= nil then
		local okm, a, c, g = pcall(function()
			return font.size[1], font.size[2], font.spacing[2]
		end)
		if okm then
			if a ~= nil and a > 0 then adv = a end
			if c ~= nil and c > 0 then cell = c end
			if g ~= nil then gap = g end
		end
	end
	return adv, cell, gap
end

-- Largest text that still shows every row and stays inside the column, so
-- scrolling is not needed on a normal screen.
local function fit(adv, cell, gap)
	local widest = 0
	for _, col in ipairs({LEFT, RIGHT}) do
		for _, row in ipairs(col) do
			local n = string.len(lineOf(row))
			if n > widest then widest = n end
		end
	end
	local scale = MAXSCALE
	while scale > MINSCALE do
		local lh = math.floor((cell + gap) * scale + 4)
		if lh * ROWS <= BOTTOM - TOP and widest * adv * scale <= COL_W then
			break
		end
		scale = scale - 0.05
	end
	return scale, math.floor((cell + gap) * scale + 4)
end

-- One sprite per role, built on first use and reused every frame.
local function ensure(name)
	if devhelp[name] ~= nil then return devhelp[name] end
	if devhelp.failed then return nil end
	local okn, ti = pcall(function()
		local t = textImgNew()
		textImgSetAlign(t, 1)
		textImgSetScale(t, 1.0, 1.0)   -- older builds raise here; probe it once
		textImgSetColor(t, 255, 255, 255)
		textImgSetPos(t, 0, 0)
		textImgSetText(t, '')
		return t
	end)
	if okn and ti ~= nil then
		devhelp[name] = ti
		return ti
	end
	devhelp.failed = true
	return nil
end

local function put(ti, font, text, col, x, y, scale)
	if font ~= nil then textImgSetFont(ti, font) end
	textImgSetAlign(ti, 1)
	textImgSetText(ti, text)
	textImgSetColor(ti, col[1], col[2], col[3])
	textImgSetScale(ti, scale, scale)
	textImgSetPos(ti, x, y)
	textImgDraw(ti)
end

-- Used only if the engine has no textImgNew: the old one-column drawing from the
-- movelist sprite, which still shows every key, just smaller.
local function drawPlain(sec, lh)
	local txt = sec.movelist.text.TextSpriteData
	local i = 0
	for _, col in ipairs({LEFT, RIGHT}) do
		for _, row in ipairs(col) do
			textImgReset(txt)
			textImgSetAlign(txt, 1)
			textImgAddPos(txt, 0, lh * i)
			textImgSetText(txt, lineOf(row))
			textImgDraw(txt)
			i = i + 1
		end
	end
end

local function devhelpDraw(sec)
	local font = sceneFont(sec)
	local adv, cell, gap = metrics(font)
	local scale, lh = fit(adv, cell, gap)

	rectDraw(sec.movelist.overlay.RectData)

	-- The title moves up: the space it gives back is what the bigger list needs.
	textImgReset(sec.movelist.title.TextSpriteData)
	textImgSetText(sec.movelist.title.TextSpriteData, 'DEVELOPER KEYS')
	textImgAddPos(sec.movelist.title.TextSpriteData, 0, -34)
	textImgDraw(sec.movelist.title.TextSpriteData)

	local ti = ensure('body')
	if ti == nil then
		drawPlain(sec, lh)
	else
		local sub = ensure('sub')
		if sub ~= nil then
			put(sub, font, NOTE, DIM, LEFT_X, TOP - 30, math.max(0.7, scale * 0.55))
		end
		for i, row in ipairs(LEFT) do
			put(ti, font, lineOf(row), row[3], LEFT_X, TOP + lh * (i - 1), scale)
		end
		for i, row in ipairs(RIGHT) do
			put(ti, font, lineOf(row), row[3], RIGHT_X, TOP + lh * (i - 1), scale)
		end
	end

	if esc() or getInput(-1, sec.menu.cancel.key, sec.menu.done.key) then
		sndPlay(motif.Snd, sec.cancel.snd[1], sec.cancel.snd[2])
		menu.itemname = ''
	end
end

function devhelpPrint()
	print('--- developer keys (docs/DEV_KEYS.md) ---')
	for _, row in ipairs(LEFT) do print(lineOf(row)) end
	for _, row in ipairs(RIGHT) do print(lineOf(row)) end
	print(NOTE)
	print('--- end developer keys ---')
end

local ok, err = pcall(function()
	-- Pause menu entry. The item is declared by tools/build_devhelp.py; this
	-- handler is what opens the screen.
	menu.t_itemname['devkeys'] = function(t, item, cursorPosY, moveTxt, sec)
		if getInput(-1, sec.menu.done.key) then
			sndPlay(motif.Snd, sec.cursor.done.snd[1], sec.cursor.done.snd[2])
			menu.itemname = 'devkeys'
		end
		return true
	end

	-- menu.f_run draws keyboard/gamepad/commandlist screens itself; this adds
	-- ours to that list. Wrapped so a drawing error closes the screen instead of
	-- taking the pause menu with it.
	local baseRun = menu.f_run
	menu.f_run = function()
		if menu.itemname == 'devkeys' then
			local drawn, drawErr = pcall(devhelpDraw, motif.pause_menu.pause_menu)
			if not drawn then
				print('devhelp: could not draw the key list: ' .. tostring(drawErr))
				menu.itemname = ''
			end
			return main.pauseMenuActive
		end
		return baseRun()
	end

	addHotkey('F1', true, false, false, false, true, 'devhelpPrint()')
end)

if not ok then
	print('devhelp: the developer key screen was not registered: ' .. tostring(err))
end
