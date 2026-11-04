--;===========================================================
--; DEVELOPER KEYS
--;===========================================================
-- Two ways in, both added here because this file is autoloaded from
-- external/mods and survives the asset build, unlike external/script/*.lua:
--
--   pause menu -> Developer Keys   the list as a screen you can scroll
--   Ctrl+F1                        the same list printed into the console
--
-- The pause menu item is declared in data/ikemen1/system.def by
-- tools/build_devhelp.py; this file supplies the handler. Everything that runs
-- during startup is inside a pcall: this module loads before the game window
-- exists, so an error here would stop the game from starting at all.

local devhelp = { line = 1 }

devhelp.t_lines = {
	'Ctrl+D            debug display: char/helper, action, anim state, physics',
	'                  press again for the next player or helper',
	'Ctrl+Shift+D      debug display with extended detail',
	'Shift+D           debug display pinned to the current player',
	'Ctrl+C            collision boxes (attack and hurt)',
	'Ctrl+W            wireframe rendering',
	'Ctrl+L            stock life bars',
	'Ctrl+V            vsync on/off',
	'',
	'Ctrl+S            cycle speed: 1x 2x 4x 0.25x 0.5x',
	'Ctrl+KP+ / KP-    speed up/down in 0.01 steps',
	'Pause             pause the match',
	'ScrollLock        single frame step while paused',
	'',
	'Shift+F4          RELOAD ENGINE - picks up Lua and def changes',
	'F1 / Ctrl+F1      KO the second player side / the first player side',
	'F2 / Ctrl+F2      KO everyone / KO the first player side',
	'F3 / Ctrl+Shift+F3  max power / max power mode',
	'F4                reset the round',
	'F5                round timer to 0',
	'Space             refill life and power, reset the timer',
	'F9 / F10          load state / save state',
	'F8                clear the console',
	'Ctrl+I            stand every fighter up',
	'',
	'Ctrl+1..8         toggle AI for that player',
	'Ctrl+Alt+1..9     take control of that player or helper',
	'',
	'These need Options > Engine > Debug Keys enabled.',
}

local t_lines = devhelp.t_lines

function devhelpPrint()
	print('--- developer keys (docs/DEV_KEYS.md) ---')
	for _, line in ipairs(t_lines) do
		print(line)
	end
	print('--- end developer keys ---')
end

-- Draws the list over the pause menu, using the movelist text sprites the pause
-- menu already sets up so no extra art is needed.
local function devhelpDraw(sec)
	local visible = sec.movelist.window.visibleitems
	if visible < 1 then visible = 1 end

	local fonts = motif.files.font['font' .. sec.movelist.text.font[1]]
	local lineHeight = 20
	if fonts ~= nil then
		lineHeight = main.f_round((fonts.size[2] + fonts.spacing[2]) * sec.movelist.text.scale[2] + sec.movelist.text.spacing[2])
	end

	local scroll = 0
	if getInput(-1, sec.menu.previous.key) then
		scroll = -1
	elseif getInput(-1, sec.menu.next.key) then
		scroll = 1
	end
	if scroll ~= 0 and #t_lines > visible then
		devhelp.line = devhelp.line + scroll
		if devhelp.line > #t_lines - visible + 1 then
			devhelp.line = #t_lines - visible + 1
		elseif devhelp.line < 1 then
			devhelp.line = 1
		end
		sndPlay(motif.Snd, sec.cursor.move.snd[1], sec.cursor.move.snd[2])
	end

	rectDraw(sec.movelist.overlay.RectData)

	textImgReset(sec.movelist.title.TextSpriteData)
	textImgSetText(sec.movelist.title.TextSpriteData, 'DEVELOPER KEYS')
	textImgDraw(sec.movelist.title.TextSpriteData)

	local txt = sec.movelist.text.TextSpriteData
	for i = devhelp.line, math.min(devhelp.line + visible - 1, #t_lines) do
		textImgReset(txt)
		textImgSetAlign(txt, 1)
		textImgAddPos(txt, 0, lineHeight * (i - devhelp.line))
		textImgSetText(txt, t_lines[i])
		textImgDraw(txt)
	end

	if esc() or getInput(-1, sec.menu.cancel.key, sec.menu.done.key) then
		sndPlay(motif.Snd, sec.cancel.snd[1], sec.cancel.snd[2])
		menu.itemname = ''
		devhelp.line = 1
	end
end

local ok, err = pcall(function()
	-- Pause menu entry. The item is declared by tools/build_devhelp.py; this
	-- handler is what opens the screen.
	menu.t_itemname['devkeys'] = function(t, item, cursorPosY, moveTxt, sec)
		if getInput(-1, sec.menu.done.key) then
			sndPlay(motif.Snd, sec.cursor.done.snd[1], sec.cursor.done.snd[2])
			devhelp.line = 1
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
