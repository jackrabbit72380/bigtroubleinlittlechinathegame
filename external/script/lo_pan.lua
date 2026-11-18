-- The Legacy of Lo Pan - the Story Mode arc declared in data/select.def.
--
-- Story Mode has no select screen and no random roster, so this file is the
-- whole campaign: the player is always Jack, and FIGHTS names one match per
-- entry, in the order the film runs. A chapter that is several fights in a row
-- (the bar's waves, the three storms, Lo Pan's three phases) is just several
-- entries in a row, and only the first of them carries a card.
--
-- matchNo() is the index into FIGHTS. A continue restarts this file with the
-- same match number, so the fight that was lost is the fight that is played
-- again and no chapter is skipped or played twice.
--
-- To retune a chapter, edit its entry:
--   opponents = character def paths, exactly as data/select.def writes them
--               (one path is a single fight, two paths fight you at once)
--   stage     = stage def path
--   ai        = AI level, 1 (gentlest) to 8
--   card      = chapter card shown before the fight

local PLAYER = 'jackburton_rig/jackburton.def'
local INTRO = 'data/story/lo_pan_intro.def'
local ENDING = 'data/story/lo_pan_ending.def'

local FIGHTS = {
	-- Act I - Little China --------------------------------------------------
	{
		card = 'data/story/lo_pan_01_airport.def',
		opponents = {'minion1_rig/minion1.def'},
		stage = 'stages/airport_terminal.def',
		ai = 1,
	},
	{
		opponents = {'wingkong_gerald_rig/wingkong_gerald.def'},
		stage = 'stages/airport_terminal.def',
		ai = 2,
	},
	{
		card = 'data/story/lo_pan_02_streets.def',
		opponents = {'minion2_rig/minion2.def'},
		stage = 'stages/chinatown_market.def',
		ai = 2,
	},
	{
		opponents = {'joe_lucky_rig/joe_lucky.def'},
		stage = 'stages/chinatown_market.def',
		ai = 3,
	},
	{
		card = 'data/story/lo_pan_03_alleys.def',
		opponents = {'wingkong_hatchet_rig/wingkong_hatchet.def'},
		stage = 'stages/chinatown_alley.def',
		ai = 3,
	},
	{
		opponents = {'needles_rig/needles.def'},
		stage = 'stages/chinatown_alley.def',
		ai = 3,
	},
	{
		card = 'data/story/lo_pan_04_market.def',
		opponents = {'wingkong_bai_rig/wingkong_bai.def', 'minion1_rig/minion1.def'},
		stage = 'stages/fish_market.def',
		ai = 4,
	},
	{
		card = 'data/story/lo_pan_05_restaurant.def',
		opponents = {'wingkong_gou_rig/wingkong_gou.def', 'wingkong_ma_rig/wingkong_ma.def'},
		stage = 'stages/dragon_restaurant.def',
		ai = 4,
	},
	{
		card = 'data/story/lo_pan_06_apartment.def',
		opponents = {'minion2_rig/minion2.def'},
		stage = 'stages/gracies_apartment.def',
		ai = 4,
	},
	{
		opponents = {'one_ear_rig/one_ear.def'},
		stage = 'stages/gracies_apartment.def',
		ai = 5,
	},
	{
		card = 'data/story/lo_pan_07_bar.def',
		opponents = {'minion1_rig/minion1.def'},
		stage = 'stages/white_tiger_bar.def',
		ai = 5,
	},
	{
		opponents = {'minion2_rig/minion2.def'},
		stage = 'stages/white_tiger_bar.def',
		ai = 5,
	},
	{
		opponents = {'wingkong_shen_rig/wingkong_shen.def'},
		stage = 'stages/white_tiger_bar.def',
		ai = 6,
	},
	{
		card = 'data/story/lo_pan_08_sewers.def',
		opponents = {'minion1_rig/minion1.def', 'minion2_rig/minion2.def'},
		stage = 'stages/the_upside_down.def',
		ai = 5,
	},
	{
		opponents = {'sewermonster_rig/sewermonster.def'},
		stage = 'stages/the_upside_down.def',
		ai = 6,
	},

	-- Act II - the Wing Kong Exchange ---------------------------------------
	{
		card = 'data/story/lo_pan_09_exchange.def',
		opponents = {'wingkong_gerald_rig/wingkong_gerald.def'},
		stage = 'stages/wingkong_lobby.def',
		ai = 6,
	},
	{
		card = 'data/story/lo_pan_10_prison.def',
		opponents = {'security1_rig/security1.def'},
		stage = 'stages/wingkong_prison.def',
		ai = 6,
	},
	{
		opponents = {'security2_rig/security2.def'},
		stage = 'stages/wingkong_prison.def',
		ai = 6,
	},
	{
		card = 'data/story/lo_pan_11_sinners.def',
		opponents = {'lotus_rig/lotus.def'},
		stage = 'stages/hell_sinners.def',
		ai = 6,
	},
	{
		opponents = {'guardian_rig/guardian.def'},
		stage = 'stages/hell_sinners.def',
		ai = 7,
	},
	{
		card = 'data/story/lo_pan_12_office.def',
		opponents = {'security2_rig/security2.def'},
		stage = 'stages/lopan_office.def',
		ai = 6,
	},
	{
		card = 'data/story/lo_pan_13_storms.def',
		opponents = {'thunder_rig/thunder.def'},
		stage = 'stages/stage3d_outline.def',
		ai = 7,
	},
	{
		opponents = {'rain_rig/rain.def'},
		stage = 'stages/stage3d_rain.def',
		ai = 7,
	},
	{
		opponents = {'lightning_rig/lightning.def'},
		stage = 'stages/stage3d.def',
		ai = 7,
	},
	{
		card = 'data/story/lo_pan_14_ritual.def',
		opponents = {'guardian_rig/guardian.def'},
		stage = 'stages/lopans_ceremony.def',
		ai = 7,
	},
	{
		card = 'data/story/lo_pan_15_sanctum.def',
		opponents = {'lopan_rig/lopan.def'},
		stage = 'stages/lopans_throne.def',
		ai = 8,
	},
	{
		opponents = {'lopan_rig/lopan.def'},
		stage = 'stages/lopans_throne.def',
		ai = 8,
	},
	{
		opponents = {'lopan_rig/lopan.def'},
		stage = 'stages/lopans_throne.def',
		ai = 8,
	},
}

local function fightData(entry)
	local opponents = entry.opponents
	return {
		p1char = {PLAYER},
		p1teammode = 'single',
		p1numchars = 1,
		p2char = opponents,
		p2numchars = #opponents,
		p2teammode = #opponents > 1 and 'simul' or 'single',
		stage = entry.stage,
		ai = entry.ai,
	}
end

if matchNo() == 1 and not continued() then
	launchStoryboard(INTRO)
end

local first = matchNo()
if first == nil or first < 1 then
	setMatchNo(-1)
	return
end

for i = first, #FIGHTS do
	local entry = FIGHTS[i]
	if entry.card ~= nil then
		launchStoryboard(entry.card)
	end
	if not launchFight(fightData(entry)) then
		return
	end
end

if not launchStoryboard(ENDING) then
	printConsole('The Legacy of Lo Pan: no ending storyboard at ' .. ENDING)
end
setMatchNo(-1)
