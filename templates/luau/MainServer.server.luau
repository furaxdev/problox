-- MainServer : point d'entrée serveur, câble les services entre eux.
local ServerScriptService = game:GetService("ServerScriptService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CurrencyService = require(ServerScriptService.Services.CurrencyService)
local LeaderboardService = require(ServerScriptService.Services.LeaderboardService)
local DailyRewardService = require(ServerScriptService.Services.DailyRewardService)
local CheckpointService = require(ServerScriptService.Services.CheckpointService)
{{PLOT_REQUIRE_LINE}}
local dailyRewardClaimed = ReplicatedStorage:WaitForChild("DailyRewardClaimed") :: RemoteEvent

Players.PlayerAdded:Connect(function(player)
	CheckpointService.Load(player)
{{PLOT_CLAIM_LINE}}
	task.wait(1) -- laisse leaderstats se créer via CurrencyService
	local granted, amount, streak = DailyRewardService.Claim(player)
	if granted then
		CurrencyService.Add(player, amount)
		dailyRewardClaimed:FireClient(player, amount, streak)
	end

	LeaderboardService.Update(player, CurrencyService.Get(player))
end)
