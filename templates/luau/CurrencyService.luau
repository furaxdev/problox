-- CurrencyService : gère la monnaie virtuelle persistante du joueur.
-- Généré par Problox. Nom de la monnaie injecté depuis le game design.
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")

local CurrencyService = {}
local currencyStore = DataStoreService:GetDataStore("{{CURRENCY_NAME}}_v1")
local cache = {}

local function loadCurrency(player: Player)
	local ok, value = pcall(function()
		return currencyStore:GetAsync("player_" .. player.UserId)
	end)
	cache[player.UserId] = (ok and value) or 0

	local leaderstats = Instance.new("Folder")
	leaderstats.Name = "leaderstats"
	leaderstats.Parent = player

	local currency = Instance.new("IntValue")
	currency.Name = "{{CURRENCY_NAME}}"
	currency.Value = cache[player.UserId]
	currency.Parent = leaderstats
end

local function saveCurrency(player: Player)
	local amount = cache[player.UserId]
	if amount == nil then
		return
	end
	pcall(function()
		currencyStore:SetAsync("player_" .. player.UserId, amount)
	end)
end

function CurrencyService.Add(player: Player, amount: number)
	local leaderstats = player:FindFirstChild("leaderstats")
	local currency = leaderstats and leaderstats:FindFirstChild("{{CURRENCY_NAME}}")
	if not currency then
		return
	end
	cache[player.UserId] = (cache[player.UserId] or 0) + amount
	currency.Value = cache[player.UserId]
end

function CurrencyService.Get(player: Player): number
	return cache[player.UserId] or 0
end

Players.PlayerAdded:Connect(loadCurrency)
Players.PlayerRemoving:Connect(saveCurrency)
game:BindToClose(function()
	for _, player in ipairs(Players:GetPlayers()) do
		saveCurrency(player)
	end
end)

return CurrencyService
