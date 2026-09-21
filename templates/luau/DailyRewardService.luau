-- DailyRewardService : récompense croissante à la connexion quotidienne (relance J+1).
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")

local DailyRewardService = {}
local rewardStore = DataStoreService:GetDataStore("daily_reward_v1")

local REWARDS = { 50, 75, 100, 150, 200, 300, 500 } -- Coins par jour de streak (1..7, plafonne à 500)
local SECONDS_PER_DAY = 24 * 60 * 60

function DailyRewardService.Claim(player: Player): (boolean, number, number)
	local key = "player_" .. player.UserId
	local ok, record = pcall(function()
		return rewardStore:GetAsync(key)
	end)
	record = (ok and record) or { streak = 0, lastClaim = 0 }

	local now = os.time()
	local elapsed = now - record.lastClaim
	if elapsed < SECONDS_PER_DAY then
		return false, 0, record.streak
	end

	local resetStreak = elapsed > (2 * SECONDS_PER_DAY)
	record.streak = resetStreak and 1 or math.min(record.streak + 1, #REWARDS)
	record.lastClaim = now

	pcall(function()
		rewardStore:SetAsync(key, record)
	end)

	local reward = REWARDS[record.streak]
	return true, reward, record.streak
end

return DailyRewardService
