-- PlotService : mécanique tycoon minimale. Le joueur réclame une parcelle,
-- des "droppers" génèrent de la monnaie en continu, collectée au contact.
local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")

local CurrencyService = require(game:GetService("ServerScriptService").Services.CurrencyService)

local PlotService = {}

local DROP_INTERVAL = 4 -- secondes entre deux générations de monnaie par dropper
local DROP_VALUE = 10

local claimedPlots: { [Player]: Instance } = {}

local function findFreePlot(): Instance?
	local plotsFolder = Workspace:FindFirstChild("Plots")
	if not plotsFolder then
		return nil
	end
	for _, plot in ipairs(plotsFolder:GetChildren()) do
		if not plot:GetAttribute("Owner") then
			return plot
		end
	end
	return nil
end

local function startDropperLoop(player: Player, plot: Instance)
	local dropper = plot:FindFirstChild("Dropper")
	if not dropper then
		return
	end
	task.spawn(function()
		while claimedPlots[player] == plot do
			task.wait(DROP_INTERVAL)
			if claimedPlots[player] ~= plot then
				break
			end
			CurrencyService.Add(player, DROP_VALUE)
		end
	end)
end

function PlotService.Claim(player: Player): boolean
	if claimedPlots[player] then
		return false
	end
	local plot = findFreePlot()
	if not plot then
		return false
	end
	plot:SetAttribute("Owner", player.UserId)
	claimedPlots[player] = plot
	startDropperLoop(player, plot)
	return true
end

Players.PlayerRemoving:Connect(function(player)
	local plot = claimedPlots[player]
	if plot then
		plot:SetAttribute("Owner", nil)
	end
	claimedPlots[player] = nil
end)

return PlotService
