-- LeaderboardService : classement global persistant (compétition sociale).
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")

local LeaderboardService = {}
local orderedStore = DataStoreService:GetOrderedDataStore("{{CURRENCY_NAME}}_leaderboard_v1")

function LeaderboardService.Update(player: Player, amount: number)
	pcall(function()
		orderedStore:SetAsync("player_" .. player.UserId, amount)
	end)
end

function LeaderboardService.GetTop(count: number)
	local ok, pages = pcall(function()
		return orderedStore:GetSortedAsync(false, count)
	end)
	if not ok then
		return {}
	end
	return pages:GetCurrentPage()
end

return LeaderboardService
