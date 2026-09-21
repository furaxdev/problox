-- ShopService : boutique de gamepasses (monétisation Robux via MarketplaceService).
local MarketplaceService = game:GetService("MarketplaceService")

local ShopService = {}

-- Renseigné au build par luau_generator.py depuis le design (id de gamepass
-- réel à créer manuellement une fois sur create.roblox.com, Open Cloud ne
-- permet pas encore la création de gamepass par API).
local GAMEPASSES = {{GAMEPASSES_TABLE}}

function ShopService.ListGamepasses()
	return GAMEPASSES
end

function ShopService.OwnsGamepass(player: Player, gamepassId: number): boolean
	local ok, owns = pcall(function()
		return MarketplaceService:UserOwnsGamePassAsync(player.UserId, gamepassId)
	end)
	return ok and owns
end

function ShopService.PromptPurchase(player: Player, gamepassId: number)
	MarketplaceService:PromptGamePassPurchase(player, gamepassId)
end

return ShopService
