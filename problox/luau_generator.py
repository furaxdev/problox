"""Transforme un GameDesign en arborescence de fichiers Luau + projet Rojo."""

from __future__ import annotations

import json
import re
from pathlib import Path

from problox.game_designer import GameDesign

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "luau"


def _read_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text()


_LUAU_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _to_luau_literal(value) -> str:
    """Sérialise une valeur JSON-compatible (dict/list/str/int/float/bool/None)
    en littéral de table Luau valide. json.dumps ne convient pas: Luau utilise
    `clé = valeur`, pas `"clé": valeur` (bug réel rencontré en prod: rojo build
    échouait sur le fichier généré avec la sortie JSON brute)."""
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
    if isinstance(value, list):
        return "{" + ", ".join(_to_luau_literal(v) for v in value) + "}"
    if isinstance(value, dict):
        entries = []
        for k, v in value.items():
            key = k if _LUAU_IDENTIFIER.match(k) else f'["{k}"]'
            entries.append(f"{key} = {_to_luau_literal(v)}")
        return "{" + ", ".join(entries) + "}"
    raise TypeError(f"Type non sérialisable en Luau: {type(value)}")


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
        f"return {_to_luau_literal(design.to_dict())}\n"
    )

    _write_rojo_project(out_dir)
    _write_selene_config(out_dir)
    return out_dir


def _write_selene_config(out_dir: Path) -> None:
    # std = "roblox": sans ça, selene ne connaît pas les globals Roblox
    # (game, Instance, task, ...) et les signale comme non définis — du bruit
    # pur, pas de vraie erreur (rencontré en prod).
    (out_dir / "selene.toml").write_text('std = "roblox"\n')


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
