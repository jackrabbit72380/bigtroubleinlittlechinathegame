--;===========================================================
--; DEVELOPER HELP
--;===========================================================
-- Ctrl+F1 prints every debug hotkey into the console (F8 clears it).
-- The same list, with more detail, is in docs/DEV_KEYS.md.
--
-- This file is autoloaded at startup from external/mods, which runs before the
-- game window exists, so an error here would stop the game from starting. Keep
-- it small, and keep the hotkey registration inside a pcall.

local t_lines = {
	'Ctrl+D          debug display: char/helper, action, anim elem, state, physics',
	'                press again to cycle the readout to the next player/helper',
	'Ctrl+Shift+D    same readout with extended detail',
	'Shift+D         readout pinned to the current player',
	'Ctrl+C          collision boxes      Ctrl+W  wireframe',
	'Ctrl+L          stock life bars      Ctrl+V  vsync',
	'Ctrl+S          cycle game speed 1x 2x 4x 0.25x 0.5x',
	'Ctrl+KP +/-     speed up/down in 0.01 steps',
	'Pause           pause                ScrollLock  single frame step',
	'Shift+F4        RELOAD ENGINE, picks up Lua and def changes',
	'F1 / F2 / F3    KO side / KO all / max power    F4  reset round',
	'F5              time to 0            Space  refill life+power, reset timer',
	'F9 / F10        load state / save state',
	'Ctrl+1..8       toggle AI per player',
	'Ctrl+Alt+1..9   take control of that player or helper',
	'F8              clear console',
}

function devhelpPrint()
	print('--- developer keys (docs/DEV_KEYS.md) ---')
	for _, line in ipairs(t_lines) do
		print(line)
	end
	print('--- end developer keys ---')
end

local ok, err = pcall(function()
	addHotkey('F1', true, false, false, false, true, 'devhelpPrint()')
end)

if not ok then
	print('devhelp: Ctrl+F1 help was not registered: ' .. tostring(err))
end
