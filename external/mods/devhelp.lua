--;===========================================================
--; DEVELOPER KEYS
--;===========================================================
-- Two ways in, both added here because this file is autoloaded from
-- external/mods and survives the asset build, unlike external/script/*.lua:
--
--   pause menu -> Developer Keys   the whole list on one screen
--   Ctrl+F1                        the same list printed into the console
--
-- The screen borrows the pause menu's own text sprite instead of building one:
-- that is the sprite the engine is known to render here (a sprite made with
-- textImgNew and given a font opened an empty screen on a real build), and it
-- already carries the command list's face, so the columns are measured in the
-- face they are drawn in. It is reset at the end of every frame, so the pause
-- menu finds it exactly as it left it.

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

local function lineOf(row)
	return string.format('%-' .. KEYW .. 's%s', row[1], row[2])
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

local COL_GAP = 48                          -- clear space between the columns' inner edges
local FALLBACK_W, FALLBACK_H = 1920, 1080   -- [Info] localcoord of this motif
local FALLBACK_X, FALLBACK_Y = 640, 96      -- the motif's own list anchor
local SIDE_MARGIN, FLOOR_MARGIN = 90, 70    -- edge the block may not enter

-- The motif's own coordinate space, as declared by [Info] localcoord. The pause
-- menu draws in these units, not in the 1280x720 the def's comments talk about,
-- so where the middle of the screen is and how far the rows can run both depend
-- on it: at 1920x1080 the title's anchor is a third of the way across, not the
-- centre, and the list had been squeezed into the top 720 units of 1080.
local function screenSize()
	local w, h = FALLBACK_W, FALLBACK_H
	pcall(function()
		local lc = motif.info.localcoord
		if lc ~= nil and lc[1] ~= nil and lc[2] ~= nil and lc[1] > 0 and lc[2] > 0 then
			w, h = lc[1], lc[2]
		end
	end)
	return w, h
end

-- Where the motif puts the pause title: movelist.pos + title.offset. The list is
-- centred on the screen itself, and this is how far the heading has to move to
-- stay over the middle of it.
local function anchor(sec)
	local cx, cy = FALLBACK_X, FALLBACK_Y
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
	local _, cy = anchor(sec)
	local sw, sh = screenSize()
	local cx = sw / 2
	local avail = sw - SIDE_MARGIN * 2
	local room = sh - FLOOR_MARGIN - cy
	-- the rows share out the height the screen actually has: the motif's own
	-- pitch is the floor (that is what the command list uses) and the band over
	-- the rows is the ceiling, capped so a tall screen cannot space it out
	if room > 0 and ROWS > 1 then
		local pitch = math.floor(room / (ROWS - 1))
		local cap = math.ceil(lh * 1.7)
		if pitch > cap then pitch = cap end
		if pitch > lh then lh = pitch end
	end
	if lh < 4 then lh = 4 end
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
	if total > avail then scale = avail / total end
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

	-- The heading moves up, and across to the screen's centre so it sits over the
	-- list: the motif anchors it a third of the way across, not in the middle.
	local sw = screenSize()
	textImgReset(sec.movelist.title.TextSpriteData)
	textImgSetText(sec.movelist.title.TextSpriteData, 'DEVELOPER KEYS')
	textImgAddPos(sec.movelist.title.TextSpriteData, sw / 2 - anchor(sec), -34)
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
	-- ours to that list. Every engine call inside the drawing is probed, so a
	-- build that is missing one draws what it can instead of closing the screen.
	local baseRun = menu.f_run
	menu.f_run = function()
		if menu.itemname == 'devkeys' then
			local drawn, drawErr = pcall(devhelpDraw, motif.pause_menu.pause_menu)
			if not drawn then
				print('devhelp: could not draw the key list: ' .. tostring(drawErr))
				menu.itemname = ''
			end
			-- the same bookkeeping the pause menu's own f_run does before it
			-- returns, so an unpause while this screen is open still clears the
			-- exit delay instead of carrying it into the next pause
			local active = main.pauseMenuActive
			if not active then
				menu.pauseExitDelay = -1
			end
			return active
		end
		return baseRun()
	end

	addHotkey('F1', true, false, false, false, true, 'devhelpPrint()')
end)

if not ok then
	print('devhelp: the developer key screen was not registered: ' .. tostring(err))
end
