--;===========================================================
--; MOD FAILURE NOTICE
--;===========================================================
-- A mod screen that fails used to leave one line in the console, behind the
-- game, so the menu item looked dead rather than broken. This draws the same
-- news where the player can see it: a black frame, one sentence, any key to
-- dismiss, four seconds if nobody touches it.
--
-- It lives in external/mods because that folder is autoloaded and survives the
-- asset build, while external/script is regenerated. Mods call it as
--     modNotice('<detail for the console>', '<sentence for the player>')
-- and the print always happens first, so a build that cannot draw text at all
-- still reports - just where it did before.
--
-- The sprite is the pause menu's own movelist text sprite, not a textImgNew
-- one: this project has seen the engine render that sprite, and a textImgNew
-- sprite with a font opened an empty screen on a real build (external/mods/
-- devhelp.lua records the same finding for the key list).

local KEYS = {'U', 'D', 'L', 'R'}
local FRAMES = 240                 -- four seconds at 60 fps, then it lets go

local function screenSize()
	local w, h = 1920, 1080
	pcall(function()
		local lc = motif.info.localcoord
		if lc ~= nil and lc[1] ~= nil and lc[2] ~= nil and lc[1] > 0 and lc[2] > 0 then
			w, h = lc[1], lc[2]
		end
	end)
	return w, h
end

local function noticeSprite()
	local ok, txt = pcall(function()
		return motif.pause_menu.pause_menu.movelist.text.TextSpriteData
	end)
	if ok and txt ~= nil then
		return txt
	end
	-- last resort: a build whose motif has no pause text sprite at all
	local made, spr = pcall(textImgNew)
	if made and spr ~= nil then
		return spr
	end
	return nil
end

function modNotice(consoleText, screenText)
	print(consoleText or '')
	local txt = noticeSprite()
	if txt == nil then
		return false                 -- the console line is all this build can show
	end
	local drawn = pcall(function()
		local sw, sh = screenSize()
		textImgReset(txt)
		textImgSetAlign(txt, 0)      -- 0 = centred, the engine's font convention
		pcall(textImgSetScale, txt, 1.5, 1.5)   -- optional on older builds
		textImgSetColor(txt, 255, 228, 140, 255)
		textImgSetText(txt, screenText or consoleText or '')
		textImgSetPos(txt, sw / 2, sh / 2)
		-- the key that opened the failing screen may still be down: clear it so
		-- the notice is not dismissed before it is drawn once
		resetKey()
		esc(false)
		for _ = 1, FRAMES do
			if esc() or getKey() ~= '' or getInput(-1, KEYS) then
				break
			end
			clearColor(0, 0, 0)
			textImgDraw(txt)
			refresh()
		end
		resetKey()
	end)
	-- leave the shared sprite exactly as the pause menu expects to find it
	pcall(textImgReset, txt)
	pcall(textImgSetScale, txt, 1, 1)
	return drawn
end
