from pathlib import Path

from problox.game_designer import GameDesign
from problox import luau_generator


def _sample_design() -> GameDesign:
    return GameDesign.model_validate(
        {
            "title": "Test Rush",
            "genre": "obby",
            "core_loop": "run, collect, upgrade",
            "systems": [{"name": "Currency", "description": "coins"}],
            "monetization": {
                "currency_name": "Gems",
                "gamepasses": [{"name": "Speed", "effect": "+10%", "suggested_price_robux": 99}],
            },
            "zones_or_levels": [{"name": "Zone 1", "description": "easy"}],
            "retention_hooks": ["daily streak"],
        }
    )


def test_generate_writes_expected_files(tmp_path: Path):
    design = _sample_design()
    out_dir = tmp_path / "build"

    luau_generator.generate(design, out_dir)

    services_dir = out_dir / "src" / "ServerScriptService" / "Services"
    assert (services_dir / "CurrencyService.luau").exists()
    assert "Gems" in (services_dir / "CurrencyService.luau").read_text()
    assert (services_dir / "LeaderboardService.luau").exists()
    assert (services_dir / "DailyRewardService.luau").exists()
    assert (services_dir / "CheckpointService.luau").exists()

    shop = (services_dir / "ShopService.luau").read_text()
    assert "Speed" in shop

    assert (out_dir / "default.project.json").exists()
    game_design_luau = (out_dir / "src" / "ReplicatedStorage" / "GameDesign.luau").read_text()
    assert 'title = "Test Rush"' in game_design_luau
    # Régression: json.dumps() produit `"clé": valeur`, invalide en Luau
    # (Luau veut `clé = valeur`) — a fait planter `rojo build` en prod.
    assert '": ' not in game_design_luau

    assert (out_dir / "selene.toml").read_text() == 'std = "roblox"\n'


def test_to_luau_literal_escapes_and_formats():
    assert luau_generator._to_luau_literal({"a": 1, "b": "x\"y"}) == '{a = 1, b = "x\\"y"}'
    assert luau_generator._to_luau_literal([1, "two", True, None]) == '{1, "two", true, nil}'
    assert luau_generator._to_luau_literal({"weird-key": 1}) == '{["weird-key"] = 1}'
