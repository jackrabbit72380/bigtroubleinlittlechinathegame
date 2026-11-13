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

-- The pause list's own text scale: the size every menu in this game is set at,
-- and the sprite these screens borrow. Their offsets were written in multiples of
-- the face's own size, which was the menu's size only while the face was baked at
-- 45px - it is 90px now, so a bare 1 drew a row twice the height of the menus
-- around it. The 0.48 here is used only if the motif cannot be read.
local function menuScale()
	local s = nil
	pcall(function()
		local v = motif.pause_menu.movelist.text.scale
		if v ~= nil and v[1] ~= nil and v[1] > 0 then
			s = v[1]
		end
	end)
	return s or 0.48
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
		-- 1.5 rows above the menu's own size, and that size comes from the
		-- motif: 1.5 alone was 1.5 x the face, three menu rows tall
		local noticeScale = 1.5 * menuScale()
		pcall(textImgSetScale, txt, noticeScale, noticeScale)   -- optional on older builds
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
