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
-- How it draws. A text sprite built here has no font until one is assigned, and
-- with no font it renders nothing at all - which is what turned this screen into
-- a frozen sky with the background drawn and every row invisible. The sequence
-- below is copied from start.lua's RANDOM label, the one text sprite this game
-- is known to put on screen in front of a menu: textImgNew, then the font
-- (object or index, whichever this build takes), then align/scale/colour/pos,
-- then per frame textImgReset + textImgSetText + textImgDraw. The motif's own
-- TextSpriteData is deliberately not reused: those sprites are shared with the
-- options and title menus, and textImgSetPos rewrites a sprite's starting offset
-- permanently, so moving them here would leave those menus misplaced after one
-- visit.

main.t_musicSelect = main.t_musicSelect or {}
local ms = main.t_musicSelect

-- 1080p layout: cover on the left, track list to its right, all inside 1920x1080.
local COVER = {x = 470, y = 470}
local LIST = {x = 880, y = 330, pitch = 40, rows = 13}
local HEAD = {x = 960, y = 210}
local HINT = {x = 960, y = 990}
local CHOICE = {x = 960, y = 1030}

local ROWSCALE = 1.5
local SMALLSCALE = 1.0

ms.params = nil
ms.chosen = nil

local function albumsFromJson()
	-- jsonDecode decodes a STRING; it was handed the path 'data/music.json'.
	-- The pcall swallowed the failure, this function returned no albums, and
	-- ms.open() bailed out on its first early exit - which is exactly what
	-- "selecting MUSIC in the main menu does nothing" looked like: the item is
	-- there (this file appends it before EXIT) and the screen never opens.
	-- The file is read first, with the engine's own reader, then decoded.
	local raw = main.f_fileRead('data/music.json')
	if raw == nil or raw == '' then
		local f = io.open('data/music.json', 'r')
		if f ~= nil then
			raw = f:read('*a')
			f:close()
		end
	end
	local ok, music = pcall(jsonDecode, raw or '')
	if not ok or type(music) ~= 'table' then
		return {}
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
	return albums
end

-- Which way this build wants the font: the font table itself, its index into
-- motif.files.font, or that resolved object. Probed once, then reused.
local fontMode = nil

local function newText(font, align, scale, x, y)
	if font == nil then
		return nil
	end
	local idx = type(font) == 'table' and font[1] or font
	local tries = {}
	if fontMode == nil or fontMode == 'object' then
		tries[#tries + 1] = {mode = 'object', value = font}
	end
	if idx ~= nil and (fontMode == nil or fontMode == 'index') then
		tries[#tries + 1] = {mode = 'index', value = idx}
	end
	if idx ~= nil and motif.files ~= nil and motif.files.font ~= nil then
		local byIndex = motif.files.font['font' .. tostring(idx)]
		if byIndex ~= nil and fontMode ~= 'index' then
			tries[#tries + 1] = {mode = 'object', value = byIndex}
		end
	end
	for _, try in ipairs(tries) do
		local t = textImgNew()
		if t ~= nil and pcall(textImgSetFont, t, try.value) then
			fontMode = try.mode
			pcall(textImgSetAlign, t, align or 1)
			pcall(textImgSetScale, t, scale or 1, scale or 1)
			pcall(textImgSetColor, t, 255, 255, 255, 255)
			pcall(textImgSetPos, t, x or 0, y or 0)
			pcall(textImgSetText, t, '')
			return t
		end
	end
	return nil
end

local function drawAt(spr, text)
	if spr == nil then
		return
	end
	pcall(textImgReset, spr)
	pcall(textImgSetText, spr, text or '')
	pcall(textImgDraw, spr)
end


-- A failure the player can see. The console keeps the whole story; the screen
-- gets the one sentence. modnotice.lua is autoloaded beside this file; if a
-- build somehow lacks it, the print still happens.
local function report(consoleText, screenText)
	if type(modNotice) == 'function' then
		pcall(modNotice, consoleText, screenText)
	else
		print(consoleText)
	end
end

-- The browser borrows the option menu's sound and confirm keys, and falls back
-- to the title menu's when a screenpack has no [Option Info].
local function moveSnd()
	local ui = motif.option_info
	if ui and ui.cursor and ui.cursor.move and ui.cursor.move.snd then
		sndPlay(motif.Snd, ui.cursor.move.snd[1], ui.cursor.move.snd[2])
	end
end

local function doneSnd()
	local ui = motif.option_info
	if ui and ui.cursor and ui.cursor.done and ui.cursor.done.snd then
		sndPlay(motif.Snd, ui.cursor.done.snd[1], ui.cursor.done.snd[2])
	else
		sndPlay(motif.Snd, motif.title_info.cursor.done.snd.default[1], motif.title_info.cursor.done.snd.default[2])
	end
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
	pcall(animUpdate, anim)
	main.f_animPosDraw(anim, COVER.x, COVER.y)
end

-- Opens the browser. Runs its own frame loop, like main.f_warning, and returns
-- once the player confirms or backs out.
function ms.open()
	local albums = albumsFromJson()
	if #albums == 0 then
		report('musicselect: data/music.json has no albums',
			'No music albums found - see console.')
		return false
	end

	local ui = motif.option_info
	local titleFont = ui and ui.title and ui.title.font
	local rowFont = ui and ui.keymenu and ui.keymenu.item and ui.keymenu.item.font or titleFont

	local head = newText(titleFont, 0, 1.5, HEAD.x, HEAD.y)
	local rows = {}
	for i = 1, LIST.rows do
		local y = LIST.y + (i - 1) * LIST.pitch
		rows[i] = {
			normal = newText(rowFont, 1, ROWSCALE, LIST.x, y),
			active = newText(rowFont, 1, ROWSCALE, LIST.x, y),
		}
	end
	local hint = newText(rowFont, 0, SMALLSCALE, HINT.x, HINT.y)
	local choice = newText(rowFont, 0, SMALLSCALE, CHOICE.x, CHOICE.y)

	if head == nil and rows[1] ~= nil and rows[1].normal == nil then
		report('musicselect: no text sprite could be created, cannot draw the browser',
			'Music list unavailable - see console.')
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

		drawAt(head, main.f_itemnameUpper(album.name ~= '' and album.name or 'Default (stage music)', true))

		if songNo < scroll then
			scroll = songNo
		elseif songNo > scroll + LIST.rows - 1 then
			scroll = songNo - LIST.rows + 1
		end
		for i = 1, LIST.rows do
			local s = album.songs[scroll + i - 1]
			local pair = rows[i]
			if s == nil then
				drawAt(pair.normal, '')
			elseif scroll + i - 1 == songNo then
				drawAt(pair.active, '> ' .. s.title)
			else
				drawAt(pair.normal, '  ' .. s.title)
			end
		end

		drawAt(choice, ms.chosen and ('NOW: ' .. ms.chosen) or 'NOW: stage music')
		drawAt(hint, 'UP / DOWN  track      LEFT / RIGHT  album      ENTER  use      ESC  back')

		refresh()

		if esc() then
			resetKey()
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
					.. tostring(err), 'Music list unavailable - see console.')
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
			'Music list unavailable - see console.')
	end
end
