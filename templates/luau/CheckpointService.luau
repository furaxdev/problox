-- CheckpointService : sauvegarde la progression du joueur (pas de perte de progrès = pas de frustration).
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")

local CheckpointService = {}
local checkpointStore = DataStoreService:GetDataStore("checkpoint_v1")
local cache = {}

function CheckpointService.Load(player: Player): number
	local ok, value = pcall(function()
		return checkpointStore:GetAsync("player_" .. player.UserId)
	end)
	cache[player.UserId] = (ok and value) or 1
	return cache[player.UserId]
end

function CheckpointService.Set(player: Player, checkpointIndex: number)
	if (cache[player.UserId] or 0) >= checkpointIndex then
		return
	end
	cache[player.UserId] = checkpointIndex
	pcall(function()
		checkpointStore:SetAsync("player_" .. player.UserId, checkpointIndex)
	end)
end

Players.PlayerRemoving:Connect(function(player)
	cache[player.UserId] = nil
end)

return CheckpointService
