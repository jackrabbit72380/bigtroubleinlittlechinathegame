-- Music select for Big Trouble in Little China.
--
-- Two albums ship in sound/ ("Big Trouble in Little China OST Movie Version" and
-- "... Game Version"). tools/build_music.py scans them and writes:
--
--   data/music.json   albums -> songs, with the title shown on screen
--   data/albums.sff   each album's boxFront.png, at group = the album's number
--
-- There are three pages. Page one is the game's own music - the track each
-- stage names in its [Music] bgmusic - and pages two and three are the albums:
-- moving onto them stops the game's music and starts the track under the
-- cursor, so an album can be heard as it is browsed. Picking on page one hands
-- the match back to the stage's music; picking on an album hands the track to
-- the engine through main.t_musicSelect.params, which
-- start.f_buildLoadStartParams appends to the next match's params, and plays it
-- at once so a browser opened from the pause menu changes the music in the
-- fight that is running.
--
-- The page, the track and whether anything is overridden are written to
-- save/music_now.cfg on every pick and read back at load and on open, so the
-- screen reopens where it was left with the playing track on its NOW line, and
-- the game starts with the track that was chosen last session.
--
-- How it draws. With the pause menu's own command-list text sprite, the same
-- one modnotice.lua and devhelp.lua draw with: it already carries the motif's
-- face and the engine is known to render it, so nothing here assigns a font at
-- all. One sprite draws every line, reset and repositioned per row, and it is
-- reset when the browser closes so the pause menu finds it as it left it.

main.t_musicSelect = main.t_musicSelect or {}
local ms = main.t_musicSelect

-- 1080p layout: cover on the left, track list to its right, all inside 1920x1080.
-- The album title sits in the frame across the top of this screen, the cover
-- fills the box on the left, and the rows start to its right. Every number
-- is in the same 1920x1080 pixels the rest of the motif uses.
-- The motif is a 1920x1080 screen and a text sprite has to be told so before
-- its scale and position are set. Left to itself the engine measures a text
-- sprite in a smaller space of its own, which drew every line on this screen
-- about twice its size and twice as far apart: the track list overlapped
-- itself and ran off the right of the frame.
-- The motif's own coordinate space, read once a frame: every position below is
-- in these units, so a screenpack that changes [Info] localcoord carries this
-- screen with it instead of leaving it on a 1920x1080 frame. The value here is
-- only what is used before a motif has been read.
local FRAME = {w = 1920, h = 1080}
local COVER = {x = 470, y = 470, w = 660, h = 680}
local LIST = {x = 880, y = 290, pitch = 40, rows = 13}
-- The three centred lines below take their x from the frame's own middle.
local HEAD_Y = 105
local HINT_Y = 990
local CHOICE_Y = 1030

local function readFrame()
	pcall(function()
		local lc = motif.info.localcoord
		if lc ~= nil and lc[1] ~= nil and lc[2] ~= nil and lc[1] > 0 and lc[2] > 0 then
			FRAME.w, FRAME.h = lc[1], lc[2]
		end
	end)
	return FRAME.w, FRAME.h
end

-- One size for the whole game, and it is the motif's own menu size rather than a
-- number kept here: this screen was pinned at 0.75, the size the menus used
-- before the face was rebaked, so every line in it drew half again as large as
-- the menus it opens from. The small lines are 0.8 of it, which keeps their
-- relationship to the rows when the menu changes.
local function menuScale()
	local s = nil
	pcall(function()
		local v = motif.option_info.menu.item.scale
		if v ~= nil and v[1] ~= nil and v[1] > 0 then
			s = v[1]
		end
	end)
	return s or 1
end

ms.params = nil
ms.chosen = nil

-- What the game is playing, remembered between sessions. The browser used to
-- forget everything when it closed: it reopened on page one, with the stage's
-- music, no idea that a track had been picked, so a pick only lasted until the
-- next match. The page, the track and whether anything is overridden are
-- written here when a pick is made and read back at load and on open.
local STATE_FILE = 'save/music_now.cfg'
ms.stage = nil          -- the stage the match is on, recorded by start.lua
ms.stageFileFor = nil   -- the stage the cached music below belongs to
ms.stageFile = nil      -- that stage's own bgmusic, read out of its .def

local function trim(s)
	return (tostring(s or ''):gsub('^%s+', ''):gsub('%s+$', ''))
end

local function readState()
	local raw = nil
	if type(main.f_fileRead) == 'function' then
		local ok, text = pcall(main.f_fileRead, STATE_FILE, 'r', true)
		if ok and type(text) == 'string' and text ~= '' then
			raw = text
		end
	end
	if raw == nil and type(io) == 'table' and io.open ~= nil then
		local ok, f = pcall(io.open, STATE_FILE, 'r')
		if ok and f ~= nil then
			raw = f:read('*a')
			f:close()
		end
	end
	if type(raw) ~= 'string' or raw == '' then
		return nil
	end
	local t = {}
	for line in raw:gmatch('[^\r\n]+') do
		local k, v = line:match('^([%w_]+)%s*=%s*(.*)$')
		if k ~= nil then
			t[k] = trim(v)
		end
	end
	-- a reader that hands back some other file must not invent a page
	if t.page == nil and t.override == nil then
		return nil
	end
	return t
end

local function writeState(page, track, file, override)
	local body = 'page=' .. tostring(page or '') .. '\r\n'
		.. 'track=' .. tostring(track or '') .. '\r\n'
		.. 'file=' .. tostring(file or '') .. '\r\n'
		.. 'override=' .. (override and '1' or '0') .. '\r\n'
	local written = false
	if type(main.f_fileWrite) == 'function' then
		written = pcall(main.f_fileWrite, STATE_FILE, body, 'w')
	end
	if not written and type(io) == 'table' and io.open ~= nil then
		written = pcall(function()
			local f = io.open(STATE_FILE, 'w')
			if f == nil then
				error('cannot write ' .. STATE_FILE)
			end
			f:write(body)
			f:close()
		end)
	end
	return written
end

-- The stage's own fight music, read out of its .def. This is what page one hands
-- playback back to, and start.lua records the stage on every match it builds so
-- a browser opened from the pause menu knows it too.
local function stageMusic()
	if ms.stage == nil or ms.stage == '' then
		return nil
	end
	if ms.stageFileFor == ms.stage then
		return ms.stageFile
	end
	ms.stageFileFor = ms.stage
	ms.stageFile = nil
	-- A stage reaches this screen as whatever select.def or the mode wrote:
	-- "stages/x.def", "stages/x", or a bare "x". All three are tried, because
	-- forgetting the first one that fails would leave page one silent for the
	-- rest of the session.
	local candidates = { ms.stage }
	if not ms.stage:find('[/\\]') then
		candidates[#candidates + 1] = 'stages/' .. ms.stage
	end
	for _, path in ipairs(candidates) do
		if not path:find('%.def$') then
			candidates[#candidates + 1] = path .. '.def'
		end
	end
	local raw = nil
	if type(main.f_fileRead) == 'function' then
		for _, path in ipairs(candidates) do
			local ok, text = pcall(main.f_fileRead, path, 'r', true)
			if ok and type(text) == 'string' and text:find('%[Music%]') then
				raw = text
				break
			end
		end
	end
	if raw == nil then
		return nil
	end
	local music = raw:match('%[Music%](.-)%[') or raw
	local file = music:match('bgmusic%s*=%s*([^%s;]+)')
	if file ~= nil and file ~= '' then
		ms.stageFile = file
	end
	return ms.stageFile
end

-- The remembered pick, restored when the game starts, so the track chosen last
-- session is the one the next match takes with it.
local savedNow = readState()
if savedNow ~= nil and savedNow.override == '1' and savedNow.file ~= nil
	and savedNow.file ~= '' then
	ms.params = 'bgmusic=' .. savedNow.file
	ms.chosen = (savedNow.page ~= '' and savedNow.page or 'Music') .. ' - '
		.. tostring(savedNow.track or '')
end

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
				albums[#albums + 1] = {
					name = tostring(name),
					songs = songs,
					art = album.Art,
					-- the size the cover was packed at, so it can be fitted to its box
					artW = tonumber(album.ArtW),
					artH = tonumber(album.ArtH),
				}
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

-- The rows are drawn with the menu's own item sprites, never with a marker
-- character in front of them: the row under the cursor uses the motif's active
-- face and the rest use its normal one, which is how the title, pause and option
-- menus show where the cursor is. A screenpack that has no item sprites falls
-- back to the command-list sprite for both, so the list still draws.
local function rowSprites()
	local normal, active = nil, nil
	local ok, item = pcall(function()
		return motif.pause_menu.pause_menu.menu.item
	end)
	if ok and type(item) == 'table' then
		pcall(function() normal = item.TextSpriteData end)
		pcall(function() active = item.active and item.active.TextSpriteData end)
	end
	if normal == nil then
		normal = listSprite()
	end
	if active == nil then
		active = normal
	end
	return normal, active
end

-- One line on the shared sprite. Every engine call is probed: a build missing
-- one of them loses a line, not the whole browser.
local function drawLine(spr, text, x, y, align, scale)
	if spr == nil then
		return false
	end
	return pcall(function()
		textImgReset(spr)
		pcall(textImgSetLocalcoord, spr, FRAME.w, FRAME.h)
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
		pcall(textImgSetLocalcoord, spr, FRAME.w, FRAME.h)
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

-- Switching album silences the music that was already running: the left and
-- right keys are there to look at another album, and the track from before the
-- browser opened is not it. Engine builds differ on whether this call exists at
-- all, so it is probed like every other engine call in this file - a build
-- without it browses exactly as before.
local function stopGameMusic()
	-- stopBgm is the name the engine documents for Lua. Lua is case-sensitive,
	-- so bgmStop and musicStop are different functions and only exist in older
	-- builds; they are tried after it rather than instead of it.
	if type(stopBgm) == 'function' then
		if pcall(stopBgm) then
			return true
		end
	end
	for _, name in ipairs({ 'bgmStop', 'musicStop' }) do
		local fn = _G[name]
		if type(fn) == 'function' and fn ~= stopBgm then
			if pcall(fn) then
				return true
			end
		end
	end
	return false
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

-- Plays the picked track, where the engine can. Builds spell this differently
-- (and some have no call at all), so every name is probed and a build with none
-- of them still records the choice for the next match.
local function playTrack(file)
	if file == nil or file == '' then
		return false
	end
	-- playBgm is the call the engine documents, and it takes a table: playBgm{
	-- bgm = path }. Passing the path on its own - or to playBGM, which is a
	-- different name in a case-sensitive language - does nothing at all, so the
	-- table form is tried first and the older spellings only after it.
	if type(playBgm) == 'function' then
		if pcall(playBgm, { bgm = file }) then
			return true
		end
	end
	for _, name in ipairs({ 'playBGM', 'bgmPlay', 'musicPlay' }) do
		local fn = _G[name]
		if type(fn) == 'function' and fn ~= playBgm then
			if pcall(fn, file) then
				return true
			end
			if pcall(fn, { file }) then
				return true
			end
		end
	end
	return false
end

-- Playback back on the stage's own track. The engine can restore that itself
-- from the stage's def - which also brings back its volume and loop points -
-- but a def that names no music leaves the fight silent, so nothing is done
-- unless the def actually names a track.
local function playGameMusic()
	local file = stageMusic()
	if file == nil then
		return false
	end
	if type(playBgm) == 'function' then
		if pcall(playBgm, { source = 'stagedef' }) then
			return true
		end
	end
	stopGameMusic()
	return playTrack(file)
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
	-- Fitted to the box rather than drawn at whatever size it was packed at: the
	-- cover and the box are not the same shape, and an unfitted sprite showed one
	-- corner of the artwork. The packed size travels with the album, so the scale
	-- is the box divided by the art, never more than 1 - a small cover keeps its
	-- own pixels instead of being blown up.
	local scale = 1
	if album.artW ~= nil and album.artH ~= nil and album.artW > 0 and album.artH > 0 then
		scale = math.min(COVER.w / album.artW, COVER.h / album.artH)
		if scale > 1 then
			scale = 1
		end
	end
	pcall(animSetScale, anim, scale, scale)
	pcall(animSetPos, anim, COVER.x, COVER.y)
	-- Clipped to the cover's own column, so artwork of any shape stays clear of
	-- the track list at x 880.
	pcall(animSetWindow, anim, COVER.x - COVER.w / 2, COVER.y - COVER.h / 2,
		COVER.x + COVER.w / 2, COVER.y + COVER.h / 2)
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
	local rowSpr, rowActive = rowSprites()
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

	-- Where the browser was left: the page and the track on it, so opening it
	-- again shows what is playing instead of snapping back to page one.
	local saved = readState()
	local albumNo, songNo, scroll = 1, 1, 1
	if saved ~= nil then
		for i, a in ipairs(albums) do
			local wantGame = (saved.page == nil or saved.page == '')
			if (wantGame and a.name == '') or (not wantGame and a.name == saved.page) then
				albumNo = i
				break
			end
		end
		local picked = albums[albumNo]
		if picked ~= nil and (saved.track ~= nil or saved.file ~= nil) then
			for i, track in ipairs(picked.songs) do
				if track.title == saved.track or (saved.file ~= nil and track.file == saved.file) then
					songNo = i
					break
				end
			end
		end
		scroll = math.max(1, math.min(songNo, #albums[albumNo].songs - LIST.rows + 1))
	end
	-- Accept is edge-triggered. The list stays open after a pick now, and an
	-- engine that reports a held key on every frame would otherwise re-pick
	-- the same row each time.
	local acceptHeld = false
	-- Switching album or track silences whatever is playing and starts the
	-- track now under the cursor: the browser is the player too, so an album
	-- can be heard as it is browsed instead of only after a confirm.
	-- Page one is the game's own music, pages two and three are the albums.
	-- Moving the cursor on page one hands playback back to the stage's track
	-- instead of leaving an album playing under it; moving on an album stops the
	-- game's music and starts the track under the cursor.
	local function preview(album, song)
		if album == nil or album.name == '' then
			-- No stage track to hand back to (an unassigned stage, or a def that
			-- names none): leave whatever is playing rather than fall silent.
			playGameMusic()
			ms.playing = nil
			return
		end
		stopGameMusic()
		if song ~= nil and song.file ~= nil then
			playTrack(song.file)
			ms.playing = { album = album.name, title = song.title, file = song.file }
		end
	end
	-- Z picks a track exactly like Enter. The motif's own done keys are added to
	-- it rather than used instead: this screenpack lists a, b, c, x, y, z, s in
	-- some sections and only a, b, c in others, and reaching for Z must work on
	-- either of them.
	local acceptKeys = { 'z' }
	local confirmKeys = doneKeys()
	if type(confirmKeys) == 'table' then
		for _, key in ipairs(confirmKeys) do
			acceptKeys[#acceptKeys + 1] = key
		end
	elseif confirmKeys ~= nil then
		acceptKeys[#acceptKeys + 1] = confirmKeys
	end

	-- A stale Escape from the menu that opened this would close it on frame one.
	esc(false)

	while true do
		local album = albums[albumNo]
		local song = album.songs[songNo]
		local acceptNow = hit(acceptKeys) or hit(OK_FALLBACK)
		-- Released keys re-arm the latch. A frame where an arrow won the
		-- branch above must not count as an accept that already happened.
		if not acceptNow then
			acceptHeld = false
		end

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

		-- Everything below is placed from the motif's space: the frame's middle for
		-- the centred lines, its width for how far a row may run, and its menu size
		-- for the text. The lines that can outgrow the frame - an album name (the
		-- longest in sound/ is 44 characters), a track title at the end of a row and
		-- the now-playing line, which carries an album and a track at once - are
		-- measured and scaled to fit instead of clipping, leaving 60 units clear at
		-- the frame's edges.
		local fw = readFrame()
		local cx = fw / 2
		local rowScale = menuScale()
		local smallScale = rowScale * 0.8
		local maxHead = fw - 120
		local maxRow = fw - LIST.x - 60

		drawFitted(spr,
			main.f_itemnameUpper(album.name ~= '' and album.name or 'Game music', true),
			cx, HEAD_Y, 0, rowScale, maxHead)
		-- which of the three pages this is, so the game's music and the albums can
		-- be told apart at a glance
		drawFitted(spr, 'PAGE ' .. albumNo .. ' OF ' .. #albums, cx, HEAD_Y + 46, 0,
			smallScale, maxHead)

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
			-- The cursor is the motif's highlight, not a character: the row under
			-- it is drawn with the active item sprite and carries no marker.
			local use = (index == songNo and rowActive ~= nil) and rowActive or rowSpr
			drawFitted(use, s ~= nil and s.title or '', LIST.x,
				LIST.y + (i - 1) * LIST.pitch, 1, rowScale, maxRow)
		end

		-- Centred on the screen and measured, so a chosen track's long
		-- "album - title" keeps the line centred instead of running past the
		-- frame; the short line and the long one sit in the same place.
		drawFitted(spr, ms.chosen and ('NOW: ' .. ms.chosen) or 'NOW: game music',
			cx, CHOICE_Y, 0, smallScale, maxHead)
		drawLine(spr, 'UP / DOWN  track      LEFT / RIGHT  album      ENTER / Z  use      ESC  back',
			cx, HINT_Y, 0, smallScale)

		refresh()

		if esc() then
			resetKey()
			pcall(textImgReset, spr)
			pcall(textImgReset, rowSpr)
			if rowActive ~= rowSpr then pcall(textImgReset, rowActive) end
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
			preview(albums[albumNo], albums[albumNo].songs[songNo])
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
			preview(albums[albumNo], albums[albumNo].songs[songNo])
		elseif hit(LEFT) then
			moveSnd()
			albumNo = albumNo - 1
			if albumNo < 1 then
				albumNo = #albums
			end
			songNo, scroll = 1, 1
			preview(albums[albumNo], albums[albumNo].songs[1])
		elseif hit(RIGHT) then
			moveSnd()
			albumNo = albumNo + 1
			if albumNo > #albums then
				albumNo = 1
			end
			songNo, scroll = 1, 1
			preview(albums[albumNo], albums[albumNo].songs[1])
		elseif acceptNow and not acceptHeld then
			doneSnd()
			if album.name ~= '' and song ~= nil and song.file ~= nil then
				-- the engine's own param form: key=value, no spaces around the =
				ms.params = 'bgmusic=' .. song.file
				ms.chosen = album.name .. ' - ' .. song.title
				-- Playing it now is what makes the pick live: the browser can be
				-- opened from the pause menu over a fight already in progress.
				playTrack(song.file)
				writeState(album.name, song.title, song.file, true)
			else
				-- Page one hands the match back to the mode's own music, and
				-- remembers that nothing is overridden any more.
				ms.params = nil
				ms.chosen = nil
				playGameMusic()
				writeState('', '', '', false)
			end
			resetKey()
			acceptHeld = true
		end
	end
end

-- Options menu entry. The browser is a setting, not a game mode, so its row
-- lives on the options menu now instead of beside Arcade and Versus. Appended
-- before the options menu's Back row, and the behaviour registered on the
-- options module itself - the same two halves the pause menu's row uses.
if type(motif) == 'table' and type(motif.option_info) == 'table'
	and type(motif.option_info.menu) == 'table' then
	pcall(main.f_appendItemname, motif.option_info.menu, '', 'music', 'Music', 'back')
end

-- The options menu calls every item's function each frame and keeps the item
-- when it returns true, so this waits for the done key and opens the browser
-- over the options screen, leaving it standing when the browser closes.
-- main.lua sets the global `options` before the mods are loaded, so that is the
-- table to extend; require is only the fallback for a build that has not set it.
local optionsMod = options
if type(optionsMod) ~= 'table' then
	local ok, mod = pcall(require, 'external.script.options')
	optionsMod = ok and mod or nil
end
if type(optionsMod) == 'table' and type(optionsMod.t_itemname) == 'table' then
	optionsMod.t_itemname['music'] = function(t, item, cursorPosY, moveTxt)
		local keys = nil
		pcall(function() keys = motif.option_info.menu.done.key end)
		if keys ~= nil and getInput(-1, keys) then
			pcall(function()
				sndPlay(motif.Snd, motif.option_info.cursor.done.snd[1],
					motif.option_info.cursor.done.snd[2])
			end)
			local opened, err = pcall(ms.open)
			if not opened then
				report('musicselect: the browser could not open from the options menu: '
					.. tostring(err), 'Music list: ' .. shortError(err))
			end
			resetKey()
		end
		return true
	end
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
