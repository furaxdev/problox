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
    # OAuth app (mode web multi-utilisateurs — voir roblox_oauth.py). Un seul
    # jeu de credentials pour tout ProbloxDev ; chaque visiteur du site
    # connecte ensuite son propre compte Roblox via ces credentials.
    roblox_oauth_client_id: str | None = None
    roblox_oauth_client_secret: str | None = None
    roblox_oauth_redirect_uri: str | None = None
    session_secret: str | None = None
    frontend_url: str | None = None
    allowed_origins: tuple[str, ...] = ()

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

    @property
    def has_oauth_app(self) -> bool:
        return bool(self.roblox_oauth_client_id and self.roblox_oauth_client_secret and self.roblox_oauth_redirect_uri)


def load_config() -> Config:
    origins = os.environ.get("ALLOWED_ORIGINS", "")
    return Config(
        roblox_api_key=os.environ.get("ROBLOX_API_KEY") or None,
        roblox_universe_id=os.environ.get("ROBLOX_UNIVERSE_ID") or None,
        roblox_place_id=os.environ.get("ROBLOX_PLACE_ID") or None,
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
        roblox_oauth_client_id=os.environ.get("ROBLOX_OAUTH_CLIENT_ID") or None,
        roblox_oauth_client_secret=os.environ.get("ROBLOX_OAUTH_CLIENT_SECRET") or None,
        roblox_oauth_redirect_uri=os.environ.get("ROBLOX_OAUTH_REDIRECT_URI") or None,
        session_secret=os.environ.get("SESSION_SECRET") or None,
        frontend_url=os.environ.get("FRONTEND_URL") or None,
        allowed_origins=tuple(o.strip() for o in origins.split(",") if o.strip()),
    )
