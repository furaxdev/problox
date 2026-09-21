"""Transforme un GameDesign en arborescence de fichiers Luau + projet Rojo."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from problox.game_designer import GameDesign

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "luau"


def _read_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text()


def _gamepasses_lua_table(design: GameDesign) -> str:
    entries = []
    for gp in design.monetization.gamepasses:
        entries.append(
            f'\t\t{{ name = "{gp.name}", effect = "{gp.effect}", '
            f"id = 0, -- TODO: crée ce gamepass sur create.roblox.com et colle son ID ici\n"
            f"\t}},"
        )
    body = "\n".join(entries)
    return "{\n" + body + "\n\t}"


def generate(design: GameDesign, out_dir: Path) -> Path:
    """Écrit build/src/**/*.luau + default.project.json, retourne le dossier build."""
    src_dir = out_dir / "src"
    services_dir = src_dir / "ServerScriptService" / "Services"
    services_dir.mkdir(parents=True, exist_ok=True)

    currency_name = design.monetization.currency_name

    currency = _read_template("CurrencyService.luau").replace("{{CURRENCY_NAME}}", currency_name)
    (services_dir / "CurrencyService.luau").write_text(currency)

    leaderboard = _read_template("LeaderboardService.luau").replace("{{CURRENCY_NAME}}", currency_name)
    (services_dir / "LeaderboardService.luau").write_text(leaderboard)

    (services_dir / "DailyRewardService.luau").write_text(_read_template("DailyRewardService.luau"))
    (services_dir / "CheckpointService.luau").write_text(_read_template("CheckpointService.luau"))

    shop = _read_template("ShopService.luau").replace(
        "{{GAMEPASSES_TABLE}}", _gamepasses_lua_table(design)
    )
    (services_dir / "ShopService.luau").write_text(shop)

    server_dir = src_dir / "ServerScriptService"
    (server_dir / "MainServer.server.luau").write_text(_read_template("MainServer.server.luau"))

    replicated_dir = src_dir / "ReplicatedStorage"
    replicated_dir.mkdir(parents=True, exist_ok=True)
    (replicated_dir / "GameDesign.luau").write_text(
        "-- Snapshot du game design ayant généré ce build (lecture seule).\n"
        f"return {json.dumps(design.to_dict(), ensure_ascii=False, indent=2)}\n"
    )

    _write_rojo_project(out_dir)
    return out_dir


def _write_rojo_project(out_dir: Path) -> None:
    project = {
        "name": "problox-experience",
        "tree": {
            "$className": "DataModel",
            "ServerScriptService": {"$path": "src/ServerScriptService"},
            "ReplicatedStorage": {
                "$path": "src/ReplicatedStorage",
                "DailyRewardClaimed": {"$className": "RemoteEvent"},
            },
        },
    }
    (out_dir / "default.project.json").write_text(json.dumps(project, indent=2))
