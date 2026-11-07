-- Music select for Big Trouble in Little China.
--
-- Two albums ship in sound/ ("Big Trouble in Little China OST Movie Version" and
-- "... Game Version"). tools/build_music.py scans them and writes:
--
--   data/music.json   albums -> songs, with the title shown on screen
--   data/albums.sff   each album's boxFront.png, at group = the album's number
--
-- This file draws the browser and hands the chosen track to the engine through
-- main.t_musicSelect.params, which start.f_buildLoadStartParams appends to the
-- next match's params. Nothing else in the game changes: leaving the browser
-- without picking a track leaves the mode's own music alone.
--
-- How it draws. With the pause menu's own command-list text sprite, the same
-- one modnotice.lua and devhelp.lua draw with: it already carries the motif's
-- face and the engine is known to render it, so nothing here assigns a font at
-- all. One sprite draws every line, reset and repositioned per row, and it is
-- reset when the browser closes so the pause menu finds it as it left it.

main.t_musicSelect = main.t_musicSelect or {}
local ms = main.t_musicSelect

-- 1080p layout: cover on the left, track list to its right, all inside 1920x1080.
local COVER = {x = 470, y = 470}
local LIST = {x = 880, y = 330, pitch = 40, rows = 13}
local HEAD = {x = 960, y = 210}
local HINT = {x = 960, y = 990}
local CHOICE = {x = 960, y = 1030}

-- The shared sprite carries the motif's own face, so the rows sit at 1.0.
-- The old 1.5 came from the option-menu font this screen no longer needs.
local ROWSCALE = 1.0
local SMALLSCALE = 0.8
local HEADSCALE = 1.5
-- The two lines that can outgrow the frame: an album name (the longest in
-- sound/ is 44 characters, and at 1.5x it ran past both edges and lost its last
-- words) and a track title at the end of a row. Both are measured and scaled to
-- fit instead of being clipped, leaving 60px clear at the frame's edges.
local MAXHEAD = 1800
-- A row is drawn from LIST.x, so this is what is left of the 1920 frame for it.
local MAXROW = 1920 - LIST.x - 60

ms.params = nil
ms.chosen = nil

-- A JSON reader small enough to keep here. data/music.json is written by
-- tools/build_music.py and is plain JSON - objects, arrays, strings, numbers,
-- true/false/null, no comments - so the only reason the browser asked the
-- engine for its decoder was convenience. That also made the screen depend on
-- a call some builds do not expose: the pcall around it turned a missing
-- decoder into "no albums found", which is what the console said.
local function decodeJson(text)
	text = text:gsub('^\239\187\191', '')     -- a byte order mark nothing asked for
	local pos = 1
	local function fail(what) error({ json = what .. ' at byte ' .. pos }, 0) end
	local function skip()
		while true do
			local c = text:sub(pos, pos)
			if c == ' ' or c == '\t' or c == '\n' or c == '\r' then
				pos = pos + 1
			else
				return
			end
		end
	end
	local function readString()
		pos = pos + 1
		local out = {}
		while true do
			local c = text:sub(pos, pos)
			if c == '' then fail('unterminated string') end
			if c == '"' then
				pos = pos + 1
				return table.concat(out)
			elseif c == '\\' then
				local esc = text:sub(pos + 1, pos + 1)
				pos = pos + 2
				if esc == 'n' then out[#out + 1] = '\n'
				elseif esc == 't' then out[#out + 1] = '\t'
				elseif esc == 'r' then out[#out + 1] = '\r'
				elseif esc == 'u' then
					-- album and track names here are ASCII; a code point outside
					-- it is kept as a placeholder rather than dropped
					local hex = text:sub(pos, pos + 3)
					pos = pos + 4
					local n = tonumber(hex, 16)
					if n ~= nil and n < 128 then out[#out + 1] = string.char(n)
					else out[#out + 1] = '?' end
				else out[#out + 1] = esc end
			else
				out[#out + 1] = c
				pos = pos + 1
			end
		end
	end
	local function readNumber()
		local rest = text:sub(pos)
		local m = rest:match('^-?%d+%.?%d*[eE][-+]?%d+') or rest:match('^-?%d+%.?%d*')
		if m == nil then fail('bad number') end
		pos = pos + #m
		return tonumber(m)
	end
	local readValue
	local function readObject()
		pos = pos + 1
		local t = {}
		skip()
		if text:sub(pos, pos) == '}' then pos = pos + 1 return t end
		while true do
			skip()
			if text:sub(pos, pos) ~= '"' then fail('expected a key') end
			local k = readString()
			skip()
			if text:sub(pos, pos) ~= ':' then fail('expected a colon') end
			pos = pos + 1
			t[k] = readValue()
			skip()
			local c = text:sub(pos, pos)
			if c == ',' then pos = pos + 1
			elseif c == '}' then pos = pos + 1 return t
			else fail('expected , or }') end
		end
	end
	local function readArray()
		pos = pos + 1
		local t = {}
		skip()
		if text:sub(pos, pos) == ']' then pos = pos + 1 return t end
		while true do
			t[#t + 1] = readValue()
			skip()
			local c = text:sub(pos, pos)
			if c == ',' then pos = pos + 1
			elseif c == ']' then pos = pos + 1 return t
			else fail('expected , or ]') end
		end
	end
	readValue = function()
		skip()
		local c = text:sub(pos, pos)
		if c == '{' then return readObject() end
		if c == '[' then return readArray() end
		if c == '"' then return readString() end
		if text:sub(pos, pos + 3) == 'true' then pos = pos + 4 return true end
		if text:sub(pos, pos + 4) == 'false' then pos = pos + 5 return false end
		if text:sub(pos, pos + 3) == 'null' then pos = pos + 4 return nil end
		return readNumber()
	end
	local ok, res = pcall(function()
		local v = readValue()
		skip()
		return v
	end)
	if not ok then
		return nil, type(res) == 'table' and res.json or tostring(res)
	end
	return res
end

local function albumsFromJson()
	-- noError: without it a folder missing the file calls panicError instead
	-- of returning nil, and the browser would die before it could say why.
	local raw = main.f_fileRead('data/music.json', 'r', true)
	if raw == nil or raw == '' then
		if type(io) == 'table' and io.open ~= nil then
			local f = io.open('data/music.json', 'r')
			if f ~= nil then
				raw = f:read('*a')
				f:close()
			end
		end
	end
	if raw == nil or raw == '' then
		return {}, 'data/music.json is missing or empty'
	end
	local music, decodeErr = decodeJson(raw)
	if type(music) ~= 'table' then
		return {}, 'data/music.json could not be read: ' .. tostring(decodeErr)
	end
	local albums = {}
	for name, album in pairs(music) do
		if type(album) == 'table' and type(album.Songs) == 'table' then
			local songs = {}
			for key, song in pairs(album.Songs) do
				if type(song) == 'table' then
					songs[#songs + 1] = {
						key = tostring(key),
						title = tostring(song.Title or key),
						file = song.file,
						order = tonumber(song.Order),
					}
				end
			end
			-- Albums ship a track list (the build writes Order from the album's own
			-- metadata), so that order wins; naming is only the fallback, because
			-- alphabetically "10 - ..." would come before "2 - ...".
			table.sort(songs, function(a, b)
				if a.order ~= nil and b.order ~= nil and a.order ~= b.order then
					return a.order < b.order
				end
				return string.lower(a.title) < string.lower(b.title)
			end)
			if #songs > 0 then
				albums[#albums + 1] = {name = tostring(name), songs = songs, art = album.Art}
			end
		end
	end
	-- "" is the option album (Default / Mute) and always sorts first.
	table.sort(albums, function(a, b)
		if a.name == '' or b.name == '' then
			return a.name == '' and b.name ~= ''
		end
		return string.lower(a.name) < string.lower(b.name)
	end)
	if #albums == 0 then
		return albums, 'data/music.json lists no album with songs'
	end
	return albums, nil
end

-- The sprite everything is drawn with: the pause menu's own command-list text.
-- It is the one text sprite this project has watched Ikemen draw, and it
-- already carries the motif's face, so no font is assigned here. That is the
-- point: a textImgNew sprite given a font opened an empty screen on a real
-- build (external/mods/devhelp.lua records the same finding), and the font
-- lookup this screen used to do is why it could end up with no sprite at all.
local function listSprite()
	local ok, spr = pcall(function()
		return motif.pause_menu.pause_menu.movelist.text.TextSpriteData
	end)
	if ok and spr ~= nil then
		return spr
	end
	return nil
end

-- One line on the shared sprite. Every engine call is probed: a build missing
-- one of them loses a line, not the whole browser.
local function drawLine(spr, text, x, y, align, scale)
	if spr == nil then
		return false
	end
	return pcall(function()
		textImgReset(spr)
		pcall(textImgSetAlign, spr, align or 0)
		pcall(textImgSetScale, spr, scale or 1, scale or 1)
		pcall(textImgSetColor, spr, 255, 255, 255, 255)
		textImgSetText(spr, text or '')
		textImgSetPos(spr, x, y)
		textImgDraw(spr)
	end)
end

-- A line sized to fit. Measuring at 1.0 and scaling down is the only way to do
-- this without guessing glyph widths: textImgGetTextWidth reports the string in
-- the sprite's own face, so a short line keeps its full scale and a long one
-- shrinks until it fits rather than being clipped at the frame's edge.
local function drawFitted(spr, text, x, y, align, ceiling, maxWidth)
	if spr == nil then
		return false
	end
	return pcall(function()
		textImgReset(spr)
		pcall(textImgSetAlign, spr, align or 0)
		pcall(textImgSetColor, spr, 255, 255, 255, 255)
		textImgSetText(spr, text or '')
		local scale = ceiling or 1
		local ok, width = pcall(textImgGetTextWidth, spr)
		if ok and type(width) == 'number' and width > 0 and maxWidth ~= nil
			and width * scale > maxWidth then
			scale = maxWidth / width
		end
		pcall(textImgSetScale, spr, scale, scale)
		textImgSetPos(spr, x, y)
		textImgDraw(spr)
	end)
end

-- The first part of a raise, short enough for one notice line.
local function shortError(err)
	local short = tostring(err):gsub('%s+', ' ')
	if #short > 44 then
		short = short:sub(1, 41) .. '...'
	end
	return short
end

-- The whole story, written down. The engine only writes a log when it panics;
-- a raise caught by a pcall wrote nothing at all, which is why a broken music
-- screen left no evidence behind.
local function writeReport(detail)
	local body = detail .. '\r\n' .. tostring(os.date('%Y-%m-%d %H:%M:%S')) .. '\r\n'
	for _, path in ipairs({ 'save/music_error.txt', 'music_error.txt' }) do
		local ok = pcall(function()
			local f = io.open(path, 'w')
			if f == nil then
				error('cannot write ' .. path)
			end
			f:write(body)
			f:close()
		end)
		if ok then
			return path
		end
	end
	return nil
end

-- A failure the player can see. The console keeps the whole story; the screen
-- gets the one sentence. modnotice.lua is autoloaded beside this file; if a
-- build somehow lacks it, the print still happens.
local function report(consoleText, screenText)
	local path = writeReport(consoleText)
	if path ~= nil then
		consoleText = consoleText .. ' (written to ' .. path .. ')'
	end
	if type(modNotice) == 'function' then
		pcall(modNotice, consoleText, screenText)
	else
		print(consoleText)
	end
end

-- The browser borrows the option menu's sound and confirm keys, and falls back
-- to the title menu's when a screenpack has no [Option Info].
-- Both sounds are optional here: [Option Info] in this screenpack carries no
-- cursor group, so indexing it raised on the first arrow press and took the
-- browser down a frame after it opened. The fallback is the title menu's own.
local function moveSnd()
	pcall(function()
		local ui = motif.option_info
		local snd = ui and ui.cursor and ui.cursor.move and ui.cursor.move.snd
		if snd ~= nil then
			sndPlay(motif.Snd, snd[1], snd[2])
		end
	end)
end

local function doneSnd()
	pcall(function()
		local ui = motif.option_info
		local snd = ui and ui.cursor and ui.cursor.done and ui.cursor.done.snd
		if snd == nil then
			local ti = motif.title_info
			local fallback = ti and ti.cursor and ti.cursor.done and ti.cursor.done.snd
			snd = fallback and fallback.default
		end
		if snd ~= nil then
			sndPlay(motif.Snd, snd[1], snd[2])
		end
	end)
end

local function doneKeys()
	local ui = motif.option_info
	if ui and ui.menu and ui.menu.done and ui.menu.done.key then
		return ui.menu.done.key
	end
	-- the same read one section over: title_info may have no menu group either
	local ti = motif.title_info
	if ti and ti.menu and ti.menu.done and ti.menu.done.key then
		return ti.menu.done.key
	end
	return { 'a', 'b', 'c', 'x', 'y', 'z' }
end

-- data/albums.sff holds every boxFront.png; sffNew is the engine call that opens
-- one at runtime, and animNew takes "group, image, x, y, ..." the same way the
-- motif does.
local function drawAlbumArt(albumData, album)
	if albumData == nil or album == nil or album.art == nil then
		return
	end
	local ok, anim = pcall(animNew, albumData, tostring(album.art) .. ', 0, 0, 0, -1')
	if not ok or anim == nil then
		return
	end
	-- A runtime animation is not in the motif's coordinate space until it is told
	-- to be. The engine starts it in its own default one, and on this 1080p
	-- screenpack that multiplied both the position and the size: 470,470 became
	-- about 2820,2115 and the cover about six times too big, so a corner of it
	-- appeared in the bottom-right of the screen instead of the cover column on
	-- the left. main.lua sets this for every portrait, for the same reason. With
	-- the motif's own space, the numbers below are the same 1920x1080 pixels every
	-- text line on this screen uses.
	pcall(animSetLocalcoord, anim, motif.info.localcoord[1], motif.info.localcoord[2])
	pcall(animSetPos, anim, COVER.x, COVER.y)
	-- Clipped to the cover's own column, so artwork of any shape stays clear of
	-- the track list at x 880.
	pcall(animSetWindow, anim, COVER.x - 330, COVER.y - 340, COVER.x + 330, COVER.y + 340)
	pcall(animUpdate, anim)
	pcall(animDraw, anim)
end

-- Opens the browser. Runs its own frame loop, like main.f_warning, and returns
-- once the player confirms or backs out.
function ms.open()
	local albums, why = albumsFromJson()
	if #albums == 0 then
		report('musicselect: ' .. tostring(why or 'data/music.json has no albums'),
			'No music albums found - see save/music_error.txt')
		return false
	end

		local ui = motif.option_info
	local spr = listSprite()
	if spr == nil then
		report('musicselect: no text sprite to draw with: the motif has no ' ..
			'[Pause Menu] movelist.text.TextSpriteData',
			'Music list: no text sprite to draw with')
		return false
	end

	-- Background: the motif's own definition, cleared and drawn with
	-- clearColor/bgReset/bgDraw like every menu in external/script/main.lua, and
	-- only its back layer - the front layer is the title logo, which would sit
	-- on top of this screen's text.
	local bgSec = ui and motif.optionbgdef or motif.titlebgdef or nil
	-- [OptionBGdef] in this screenpack has no bgclearcolor line - only
	-- [TitleBGdef] and [AttractBGdef] carry one - and indexing it directly raised
	-- inside open(). The pause menu calls open() through a pcall that only prints,
	-- so the failure looked like the MUSIC item doing nothing at all. The colour
	-- is optional; the layers below are what this screen actually needs.
	local bgR, bgG, bgB = 0, 0, 0
	if type(bgSec) == 'table' then
		local clear = bgSec.bgclearcolor
		if type(clear) == 'table' then
			bgR, bgG, bgB = clear[1] or 0, clear[2] or 0, clear[3] or 0
		end
		if bgSec.BGDef == nil then
			bgSec = nil
		end
	end
	local okArt, albumData = pcall(sffNew, 'data/albums.sff')
	if not okArt then
		albumData = nil
	end

	-- Direction keys by their engine names. getInput takes key names ('U', 'D',
	-- 'L', 'R'), never the word "UP": passing a string where the engine wants a
	-- table of names is why no arrow did anything on this screen.
	local UP, DOWN, LEFT, RIGHT = {'U'}, {'D'}, {'L'}, {'R'}
	local OK_FALLBACK = {'a', 'b', 'c', 'x', 'y', 'z', 's'}
	local function hit(keys)
		if keys == nil then
			return false
		end
		local ok, res = pcall(getInput, -1, keys)
		return (ok and res ~= nil and res ~= false) and true or false
	end

	local albumNo, songNo, scroll = 1, 1, 1
	local confirmKeys = doneKeys()

	-- A stale Escape from the menu that opened this would close it on frame one.
	esc(false)

	while true do
		local album = albums[albumNo]
		local song = album.songs[songNo]

		if bgSec then
			clearColor(bgR, bgG, bgB)
			-- probed, like every other engine call in this file: a backdrop that
			-- cannot be drawn must not take the whole browser down with it.
			local bgDrawn, bgErr = pcall(function()
				bgReset(bgSec.BGDef)
				bgDraw(bgSec.BGDef, 0)
			end)
			if not bgDrawn then
				print('musicselect: the backdrop could not be drawn: ' .. tostring(bgErr))
				bgSec = nil
			end
		end
		drawAlbumArt(albumData, album)

		drawFitted(spr,
			main.f_itemnameUpper(album.name ~= '' and album.name or 'Default (stage music)', true),
			HEAD.x, HEAD.y, 0, HEADSCALE, MAXHEAD)

		if songNo < scroll then
			scroll = songNo
		elseif songNo > scroll + LIST.rows - 1 then
			scroll = songNo - LIST.rows + 1
		end
		for i = 1, LIST.rows do
			local index = scroll + i - 1
			local s = album.songs[index]
			-- an empty slot still draws: the list keeps its rhythm, and a screen
			-- that renders nothing at all is easier to tell from a short one
			local mark = ''
			if s ~= nil then
				mark = (index == songNo and '> ' or '  ') .. s.title
			end
			drawFitted(spr, mark, LIST.x, LIST.y + (i - 1) * LIST.pitch, 1, ROWSCALE, MAXROW)
		end

		drawLine(spr, ms.chosen and ('NOW: ' .. ms.chosen) or 'NOW: stage music',
			CHOICE.x, CHOICE.y, 0, SMALLSCALE)
		drawLine(spr, 'UP / DOWN  track      LEFT / RIGHT  album      ENTER  use      ESC  back',
			HINT.x, HINT.y, 0, SMALLSCALE)

		refresh()

		if esc() then
			resetKey()
			pcall(textImgReset, spr)
			return false
		elseif hit(UP) then
			moveSnd()
			songNo = songNo - 1
			if songNo < 1 then
				albumNo = albumNo - 1
				if albumNo < 1 then
					albumNo = #albums
				end
				songNo = #albums[albumNo].songs
			end
		elseif hit(DOWN) then
			moveSnd()
			songNo = songNo + 1
			if songNo > #album.songs then
				albumNo = albumNo + 1
				if albumNo > #albums then
					albumNo = 1
				end
				songNo = 1
			end
		elseif hit(LEFT) then
			moveSnd()
			albumNo = albumNo - 1
			if albumNo < 1 then
				albumNo = #albums
			end
			songNo, scroll = 1, 1
		elseif hit(RIGHT) then
			moveSnd()
			albumNo = albumNo + 1
			if albumNo > #albums then
				albumNo = 1
			end
			songNo, scroll = 1, 1
		elseif hit(confirmKeys) or hit(OK_FALLBACK) then
			doneSnd()
			if song ~= nil and song.file ~= nil then
				ms.params = 'bgmusic = ' .. song.file
				ms.chosen = album.name .. ' - ' .. song.title
			else
				-- The option album's rows ("Default") hand the match back to the
				-- mode's own music.
				ms.params = nil
				ms.chosen = nil
			end
			resetKey()
			pcall(textImgReset, spr)
			return true
		end
	end
end

-- Title menu entry. Appended before EXIT so it reads with the other modes, and
-- the handler opens the browser in place, exactly like OPTIONS.
if type(motif) == 'table' and type(motif.title_info) == 'table' and type(motif.title_info.menu) == 'table' then
	pcall(main.f_appendItemname, motif.title_info.menu, '', 'music', 'MUSIC', 'exit')
end

-- Returns nothing on purpose: the title menu assigns the return value to
-- main.menu.f and, when that is non-nil, fades the screen out and calls it as a
-- function. The browser is a screen of its own, so the title menu just stays.
-- Pause menu entry. Same two halves as the Developer Keys screen
-- (external/mods/devhelp.lua): tools/build_devhelp.py declares the row in the
-- motif, this registers what the row does. menu is a global - main.lua does
-- menu = require('external.script.menu') - so a mod can add to its list.
local pauseEntry = pcall(function()
	menu.t_itemname['music'] = function(t, item, cursorPosY, moveTxt, sec)
		if getInput(-1, sec.menu.done.key) then
			sndPlay(motif.Snd, sec.cursor.done.snd[1], sec.cursor.done.snd[2])
			-- The browser runs its own loop and draws over the paused fight, the
			-- way the developer key list does. It closes itself and the pause
			-- menu is still standing when it returns; a failure inside it must
			-- not take the pause menu down, so it is caught and logged.
			local ok, err = pcall(ms.open)
			if not ok then
				report('musicselect: the browser could not open from the pause menu: '
					.. tostring(err), 'Music list: ' .. shortError(err))
			end
		end
		return true
	end
end)
if not pauseEntry then
	print('musicselect: the pause menu entry was not registered')
end

main.t_itemname.music = function(t, item)
	-- A screen of its own, so a failure inside it must not take the engine down
	-- with an error dialog: it is logged and the title menu is left standing.
	local ok, err = pcall(ms.open)
	if not ok then
		report('musicselect: the browser could not open: ' .. tostring(err),
			'Music list: ' .. shortError(err))
	end
end
