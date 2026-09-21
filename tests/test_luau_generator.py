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
    assert (out_dir / "src" / "ReplicatedStorage" / "GameDesign.luau").exists()
