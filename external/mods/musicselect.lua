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

main.t_musicSelect = main.t_musicSelect or {}
local ms = main.t_musicSelect

-- 1080p layout. The album cover sits left of the list, which is right of centre,
-- so the two never overlap at any cover size up to the 640px cap.
local COVER = {x = 560, y = 470, cap = 640}
local LIST = {x = 1010, y = 300, pitch = 52, rows = 13}
local HEAD = {x = 1010, y = 190}
local HINT = {x = 960, y = 1010}
local CHOICE = {x = 960, y = 1050}

ms.params = nil
ms.chosen = nil

local function albumsFromJson()
	local ok, music = pcall(jsonDecode, 'data/music.json')
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
					}
				end
			end
			table.sort(songs, function(a, b)
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

local function makeText(font, x, y, scale)
	local t = textImgNew()
	textImgApplyFontTuple(t, font)
	textImgSetPos(t, x, y)
	if scale then
		textImgSetScale(t, scale, scale)
	end
	return t
end

local function setText(sprite, text)
	textImgSetText(sprite, text or '')
	return sprite
end

local function drawAlbumArt(albumData, album, x, y)
	if albumData == nil or album.art == nil then
		return
	end
	local ok, anim = pcall(animNew, albumData, tostring(album.art) .. ', 0, 0, 0, -1')
	if not ok or anim == nil then
		return
	end
	local scale = 1
	local w = math.max(1, album.artWidth or 0)
	if w > COVER.cap then
		scale = COVER.cap / w
	end
	pcall(animSetScale, anim, scale, scale)
	pcall(animUpdate, anim)
	main.f_animPosDraw(anim, x, y)
end

-- Opens the browser. Runs its own frame loop, like the reference module, and
-- returns once the player confirms or backs out.
function ms.open()
	local albums = albumsFromJson()
	if #albums == 0 then
		return false
	end

	local titleFont = motif.title_info.menu.item.font
	local activeFont = motif.title_info.menu.item.active.font or titleFont
	local smallFont = motif.option_info and motif.option_info.menu and motif.option_info.menu.item.font or titleFont
	local head = makeText(titleFont, HEAD.x, HEAD.y)
	local hint = makeText(smallFont, HINT.x, HINT.y, 0.5)
	local choice = makeText(smallFont, CHOICE.x, CHOICE.y, 0.5)
	local rows = {}
	for i = 1, LIST.rows do
		rows[i] = {
			normal = makeText(smallFont, LIST.x, LIST.y + (i - 1) * LIST.pitch),
			active = makeText(activeFont, LIST.x, LIST.y + (i - 1) * LIST.pitch),
		}
	end

	local okBg, bg = pcall(bgNew, sffNew(motif.files.spr), gameOption('Config.Motif'), 'musicBG')
	if not okBg then
		bg = nil
	end
	local okArt, albumData = pcall(sffNew, 'data/albums.sff')
	if not okArt then
		albumData = nil
	end

	local albumNo, songNo, scroll = 1, 1, 1
	textImgSetText(hint, 'UP / DOWN  track      LEFT / RIGHT  album      ENTER  use      ESC  back')

	while true do
		local album = albums[albumNo]
		local song = album.songs[songNo]

		if bg then
			bgReset(bg)
			bgDraw(bg, 0)
		end
		drawAlbumArt(albumData, album, COVER.x, COVER.y)

		textImgSetText(head, main.f_itemnameUpper(album.name ~= '' and album.name or 'Options', true))
		textImgDraw(head)

		if songNo < scroll then
			scroll = songNo
		elseif songNo > scroll + LIST.rows - 1 then
			scroll = songNo - LIST.rows + 1
		end
		for i = 1, LIST.rows do
			local s = album.songs[scroll + i - 1]
			local pair = rows[i]
			if s == nil then
				textImgSetText(pair.normal, '')
				textImgSetText(pair.active, '')
			end
			if s ~= nil then
				local label = (scroll + i - 1 == songNo and '> ' or '  ') .. s.title
				textImgSetText(pair.normal, label)
				textImgSetText(pair.active, label)
			end
			if s ~= nil then
				textImgDraw((scroll + i - 1 == songNo) and pair.active or pair.normal)
			end
		end

		textImgSetText(choice, ms.chosen and ('NOW: ' .. ms.chosen) or 'NOW: stage music')
		textImgDraw(choice)
		textImgDraw(hint)

		refresh()

		if esc() then
			return false
		elseif main.f_input({1}, {'$U', 'LS_Y-'}) then
			sndPlay(motif.Snd, motif.option_info.cursor.move.snd[1], motif.option_info.cursor.move.snd[2])
			songNo = songNo - 1
			if songNo < 1 then
				albumNo = albumNo - 1
				if albumNo < 1 then
					albumNo = #albums
				end
				songNo = #albums[albumNo].songs
			end
		elseif main.f_input({1}, {'$D', 'LS_Y+'}) then
			sndPlay(motif.Snd, motif.option_info.cursor.move.snd[1], motif.option_info.cursor.move.snd[2])
			songNo = songNo + 1
			if songNo > #album.songs then
				albumNo = albumNo + 1
				if albumNo > #albums then
					albumNo = 1
				end
				songNo = 1
			end
		elseif main.f_input({1}, {'$L', 'LS_X-'}) then
			sndPlay(motif.Snd, motif.option_info.cursor.move.snd[1], motif.option_info.cursor.move.snd[2])
			albumNo = albumNo - 1
			if albumNo < 1 then
				albumNo = #albums
			end
			songNo, scroll = 1, 1
		elseif main.f_input({1}, {'$R', 'LS_X+'}) then
			sndPlay(motif.Snd, motif.option_info.cursor.move.snd[1], motif.option_info.cursor.move.snd[2])
			albumNo = albumNo + 1
			if albumNo > #albums then
				albumNo = 1
			end
			songNo, scroll = 1, 1
		elseif main.f_input({1}, motif.option_info.menu.done.key) then
			sndPlay(motif.Snd, motif.option_info.cursor.done.snd[1], motif.option_info.cursor.done.snd[2])
			if song.file ~= nil then
				ms.params = 'bgmusic = ' .. song.file
				ms.chosen = album.name .. ' - ' .. song.title
			else
				-- The option album's rows ("Default") hand the match back to the
				-- mode's own music.
				ms.params = nil
				ms.chosen = nil
			end
			return true
		end
	end
end

-- Title menu entry. Appended before EXIT so it reads with the other modes, and
-- the handler opens the browser in place, exactly like OPTIONS.
if type(motif) == 'table' and type(motif.title_info) == 'table' and type(motif.title_info.menu) == 'table' then
	pcall(main.f_appendItemname, motif.title_info.menu, '', 'music', 'MUSIC', 'exit')
end

main.t_itemname.music = function(t, item)
	ms.open()
	return true
end
