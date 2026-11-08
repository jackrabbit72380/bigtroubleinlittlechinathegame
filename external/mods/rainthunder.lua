-- Thunder for the rainfall stage.
--
-- A stage DEF cannot play a sound; the only audio a stage owns is its bgmusic.
-- So the storm's rumble comes from here, and three things make it possible:
--
--   * stages/stage3d_rain.def declares [Constants] RainThunder = 1, and Lua can
--     read that back with the stageConst() trigger;
--   * external/script/debug.lua's loop() runs on every match frame and calls the
--     hook list named "loop" - the engine is configured to execute that with
--     Lua = loop() in config.ini;
--   * data/system.snd carries the rumble as group 900, number 0, painted by
--     tools/build_thunder.py.
--
-- The flash is [Begin Action 9001] in the same def: a 327-tick cycle with a
-- strike at tick 150 and a distant flash at 315. This keeps its own tick count,
-- restarts it when the round restarts (resetBG = 1 restarts the stage's animation
-- too, so the two stay together), and rumbles two ticks after each flash - the
-- thunder arriving late is what makes it read as far away.
--
-- None of this is essential to the game. If the sample, the trigger or the hook
-- is missing, the module disables itself and the stage simply has no thunder.

local THUNDER_SND = 'data/system.snd'
local GROUP, NUMBER = 900, 0
local CYCLE = 327
-- tick into the cycle -> volume percent; 150 is the strike, 315 the distant flash
local STRIKES = { { 152, 70 }, { 317, 40 } }

local rt = main.t_rainThunder or {}
main.t_rainThunder = rt
rt.tick = 0
rt.loaded = false
rt.snd = nil
rt.enabled = true

local function bank()
	if rt.loaded then return rt.snd end
	rt.loaded = true
	local ok, loaded = pcall(sndNew, THUNDER_SND)
	if ok and loaded ~= nil then
		rt.snd = loaded
	end
	return rt.snd
end

local function inRainStage()
	local ok, value = pcall(stageConst, 'RainThunder')
	return ok and (value == 1 or value == true)
end

local function rumble(volume)
	local loaded = bank()
	if loaded == nil then return end
	pcall(sndPlay, loaded, GROUP, NUMBER, volume)
end

local function step()
	if not rt.enabled then return end
	local ok = pcall(function()
		if not inRainStage() then return end
		if roundStart() then rt.tick = 0 end
		rt.tick = rt.tick + 1
		if rt.tick > CYCLE then rt.tick = 1 end
		for _, strike in ipairs(STRIKES) do
			if rt.tick == strike[1] then
				rumble(strike[2])
			end
		end
	end)
	if not ok then
		-- one bad frame stands the module down: an error every frame would
		-- flood the console for the rest of the match, and no thunder is a
		-- far better outcome than a stuttering fight
		rt.enabled = false
	end
end

hook.add('loop', 'rainthunder', step)
