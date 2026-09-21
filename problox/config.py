"""Chargement de la configuration depuis l'environnement. Aucune clé en dur."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    roblox_api_key: str | None
    roblox_universe_id: str | None
    roblox_place_id: str | None
    anthropic_api_key: str | None

    @property
    def has_roblox_credentials(self) -> bool:
        return bool(self.roblox_api_key and self.roblox_universe_id and self.roblox_place_id)

    @property
    def has_anthropic_credentials(self) -> bool:
        return bool(self.anthropic_api_key)

    def missing_roblox_vars(self) -> list[str]:
        missing = []
        if not self.roblox_api_key:
            missing.append("ROBLOX_API_KEY")
        if not self.roblox_universe_id:
            missing.append("ROBLOX_UNIVERSE_ID")
        if not self.roblox_place_id:
            missing.append("ROBLOX_PLACE_ID")
        return missing


def load_config() -> Config:
    return Config(
        roblox_api_key=os.environ.get("ROBLOX_API_KEY") or None,
        roblox_universe_id=os.environ.get("ROBLOX_UNIVERSE_ID") or None,
        roblox_place_id=os.environ.get("ROBLOX_PLACE_ID") or None,
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
    )
