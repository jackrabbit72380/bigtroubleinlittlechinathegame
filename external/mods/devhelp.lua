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
-- 14, not 12: 'Ctrl+Shift+F3' and 'Ctrl+Alt+1..9' are 13 characters, so a
-- 12-wide field did not pad them at all and the description ran straight on from
-- the key with no space between ("Ctrl+Shift+F3max power mode").
local KEYW = 14                          -- key column width, in characters
local ROWS = math.max(#LEFT, #RIGHT)     -- taller column decides the height
local TOP, BOTTOM = 96, 720              -- first row, and the floor it must not hit
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

-- The list is drawn with the pause menu's own text sprite - the one call the
-- engine demonstrably renders - but the placement no longer guesses how wide a
-- character is. Two guesses were wrong at once here: the advance was taken as
-- size[1] alone, while the motif adds spacing[1] to every glyph, so the pitch
-- came out a sixth short; and the block was centred on the list's own anchor
-- (100 units in), which pushed the left column's first half off the screen and
-- let the right one print through it.
--
-- So: the face is read from the motif, each field on its own, and the widths are
-- then measured through the engine. Every row is placed from those measurements.
local function motifText(sec)
	local charw, cell, gap, vscale, vgap = 7, 0, 0, 1, 0
	pcall(function()
		local m = sec.movelist.text
		local f = motif.files.font['font' .. m.font[1]]
		local w = 0
		if f ~= nil then
			if f.size ~= nil then
				if f.size[1] ~= nil and f.size[1] > 0 then w = f.size[1] end
				if f.size[2] ~= nil and f.size[2] > 0 then cell = f.size[2] end
			end
			-- read on its own: a build that does not expose font.spacing used
			-- to raise here and take the whole lookup with it, leaving the
			-- list on a guessed pitch
			if f.spacing ~= nil and f.spacing[2] ~= nil and f.spacing[2] > 0 then
				gap = f.spacing[2]
			end
		end
		if m.spacing ~= nil and m.spacing[1] ~= nil and m.spacing[1] > 0 then
			w = w + m.spacing[1]
		end
		if w > 0 then charw = w end
		if m.scale ~= nil and m.scale[2] ~= nil and m.scale[2] > 0 then
			vscale = m.scale[2]
		end
		if m.spacing ~= nil and m.spacing[2] ~= nil then
			vgap = m.spacing[2]
		end
	end)
	if cell < 1 then cell = charw * 3 end
	-- the engine's own pitch for this list, the one the command list is drawn on
	return charw, math.floor((cell + gap) * vscale + vgap)
end

-- Measured width of one cell, through the engine. The face is proportional, so
-- the only honest way to know where the second column starts is to ask.
local function cellWidth(ti, text, charw)
	local ok, w = pcall(textImgGetTextWidth, ti, text)
	if ok and type(w) == 'number' and w > 1 then
		return w
	end
	return string.len(text) * charw
end

local AVAIL = 1150                 -- room the block may use on the 1280-wide screen
local COL_GAP = 48                 -- clear space between the columns' inner edges
local FALLBACK_CX, FALLBACK_Y = 640, 96

-- Where the screenpack puts a centred thing: the pause title is centred on
-- movelist.pos + title.offset, and the block sits on that same point, so the
-- heading stays over the middle of the columns.
local function anchor(sec)
	local cx, cy = FALLBACK_CX, FALLBACK_Y
	pcall(function()
		local m = sec.movelist
		if m == nil then return end
		if m.pos ~= nil then
			if m.pos[1] ~= nil then cx = m.pos[1] end
			if m.pos[2] ~= nil then cy = m.pos[2] end
		end
		if m.title ~= nil and m.title.offset ~= nil and m.title.offset[1] ~= nil then
			cx = cx + m.title.offset[1]
		end
		if m.text ~= nil and m.text.offset ~= nil and m.text.offset[2] ~= nil then
			cy = cy + m.text.offset[2]
		end
	end)
	return cx, cy
end

-- Each row is two cells drawn from their measured widths - the left one starts
-- half the block left of the anchor, the right one exactly past the left column
-- and the gap - so the two cannot print through each other whatever the face
-- does. The block only shrinks if a longer key list ever outgrows the screen.
-- Positions are set, not added: the sprite's own base is the list's left margin,
-- which is not where a centred block belongs.
local function drawPlain(sec)
	local txt = sec.movelist.text.TextSpriteData
	local charw, lh = motifText(sec)
	local cx, cy = anchor(sec)
	-- keep the screenpack's own pitch unless a future key list would run off the
	-- bottom: only the last row's top has to stay inside, its glyph may sit on
	-- the edge exactly as the command list's last line does
	local room = BOTTOM - cy
	if room > 0 and lh * (ROWS - 1) > room then
		lh = math.floor(room / (ROWS - 1))
	end
	local lw, rw = 0, 0
	for i = 1, ROWS do
		local l, r = LEFT[i], RIGHT[i]
		if l ~= nil then
			local w = cellWidth(txt, lineOf(l), charw)
			if w > lw then lw = w end
		end
		if r ~= nil then
			local w = cellWidth(txt, lineOf(r), charw)
			if w > rw then rw = w end
		end
	end
	local total = lw + COL_GAP + rw
	local scale = 1
	if total > AVAIL then scale = AVAIL / total end
	local xl = cx - total * scale / 2
	local xr = xl + (lw + COL_GAP) * scale
	for i = 1, ROWS do
		local y = cy + lh * (i - 1)
		local l, r = LEFT[i], RIGHT[i]
		if l ~= nil then
			pcall(function()
				textImgReset(txt)
				textImgSetAlign(txt, 1)          -- 1 = left, the engine's font convention
				textImgSetScale(txt, scale, scale)
				textImgSetColor(txt, l[3][1], l[3][2], l[3][3], 255)
				textImgSetText(txt, lineOf(l))
				textImgSetPos(txt, xl, y)
				textImgDraw(txt)
			end)
		end
		if r ~= nil then
			pcall(function()
				textImgReset(txt)
				textImgSetAlign(txt, 1)
				textImgSetScale(txt, scale, scale)
				textImgSetColor(txt, r[3][1], r[3][2], r[3][3], 255)
				textImgSetText(txt, lineOf(r))
				textImgSetPos(txt, xr, y)
				textImgDraw(txt)
			end)
		end
	end
	-- leave the shared sprite as the pause menu expects to find it
	textImgReset(txt)
	pcall(textImgSetScale, txt, 1, 1)
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
