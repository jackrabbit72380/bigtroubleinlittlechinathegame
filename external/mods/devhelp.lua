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
-- a side effect.
--
-- Everything the engine is asked to do with that sprite is PROBED, not assumed.
-- A previous version set the font with the motif's font table and the whole
-- screen vanished: the call raised, the frame handler caught it, and the handler
-- closes the screen when drawing fails. So each engine call is tried, the call
-- that works is remembered, and if the fancy path cannot work at all the screen
-- falls back to the motif's own text sprite - smaller, but it always opens.

local devhelp = {
	body = nil,        -- big two-column sprite
	sub = nil,         -- the small note above the list
	failed = false,    -- the big path is out; stay on the plain list
	warned = false,    -- only print the fallback reason once
	fontMode = nil,    -- 'object' | 'index' | 'none', decided by probing
}

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
local KEYW = 12                          -- key column width, in characters
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

-- textImgSetFont takes the font table in some builds and its index in others,
-- and raises on the wrong one. Try once, remember what worked, and if neither
-- does, leave the sprite on its own font rather than losing the screen.
local function applyFont(ti, font, idx)
	if devhelp.fontMode == 'none' then return end
	if devhelp.fontMode == 'object' then
		pcall(textImgSetFont, ti, font)
		return
	end
	if devhelp.fontMode == 'index' then
		pcall(textImgSetFont, ti, idx)
		return
	end
	if font ~= nil and pcall(textImgSetFont, ti, font) then
		devhelp.fontMode = 'object'
		return
	end
	if idx ~= nil and pcall(textImgSetFont, ti, idx) then
		devhelp.fontMode = 'index'
		return
	end
	devhelp.fontMode = 'none'
end

-- One sprite per role, built on first use and reused every frame. The probe
-- covers every call the draw path makes, so a build missing any of them fails
-- here once instead of raising in the middle of a frame.
local function ensure(name)
	if devhelp[name] ~= nil then return devhelp[name] end
	if devhelp.failed then return nil end
	local ok, ti = pcall(function()
		local t = textImgNew()
		textImgSetAlign(t, 1)
		textImgSetScale(t, 1.0, 1.0)
		textImgSetColor(t, 255, 255, 255)
		textImgSetPos(t, 0, 0)
		textImgSetText(t, '')
		return t
	end)
	if ok and ti ~= nil then
		devhelp[name] = ti
		return ti
	end
	devhelp.failed = true
	return nil
end

local function put(ti, font, idx, text, col, x, y, scale)
	applyFont(ti, font, idx)
	textImgSetAlign(ti, 1)
	textImgSetText(ti, text)
	textImgSetColor(ti, col[1], col[2], col[3])
	textImgSetScale(ti, scale, scale)
	textImgSetPos(ti, x, y)
	textImgDraw(ti)
end

-- The always-available screen: the pause menu's own text sprite, one column,
-- drawn exactly the way the working version drew it. It sets its own pitch from
-- the motif's font and scale - the two-column pitch is far too tall for a single
-- column of every row.
local function plainPitch(sec)
	local h = 26
	pcall(function()
		local f = motif.files.font['font' .. sec.movelist.text.font[1]]
		h = math.floor((f.size[2] + f.spacing[2]) * sec.movelist.text.scale[2]
			+ sec.movelist.text.spacing[2])
	end)
	if h < 8 then h = 8 end
	return h
end

-- The list is drawn with the pause menu's own text sprite, the same call the
-- engine makes to draw the command list. The earlier two-column path built a
-- text sprite with textImgNew and set a font on it; on a real build that opened
-- an empty screen (the dim overlay drew, the rows did not), so the whole screen
-- is drawn with the one sprite the engine demonstrably renders: two columns,
-- offset with AddPos, no font swapping.
local function drawPlain(sec)
	local txt = sec.movelist.text.TextSpriteData
	local lh = plainPitch(sec)
	local COLS = {{0, LEFT}, {620, RIGHT}}
	for _, col in ipairs(COLS) do
		local x, rows = col[1], col[2]
		for i, row in ipairs(rows) do
			textImgReset(txt)
			textImgSetAlign(txt, 1)
			textImgSetText(txt, lineOf(row))
			textImgAddPos(txt, x, lh * (i - 1))
			textImgDraw(txt)
		end
	end
end

local function devhelpDraw(sec)
	rectDraw(sec.movelist.overlay.RectData)

	-- The title moves up: the space it gives back is what the bigger list needs.
	textImgReset(sec.movelist.title.TextSpriteData)
	textImgSetText(sec.movelist.title.TextSpriteData, 'DEVELOPER KEYS')
	textImgAddPos(sec.movelist.title.TextSpriteData, 0, -34)
	textImgDraw(sec.movelist.title.TextSpriteData)

	drawPlain(sec)

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
	-- ours to that list. Our own drawing never raises: if the two-column path
	-- cannot work it uses the plain list, so this stays open instead of closing
	-- the moment something in the engine disagrees with a call.
	local baseRun = menu.f_run
	menu.f_run = function()
		if menu.itemname == 'devkeys' then
			local drawn, drawErr = pcall(devhelpDraw, motif.pause_menu.pause_menu)
			if not drawn then
				print('devhelp: could not draw the key list: ' .. tostring(drawErr))
				devhelp.failed = true
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
