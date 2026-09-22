"""Config du bot Hermès — tout vient de variables d'env, jamais de valeurs en dur."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _split_ids(raw: str | None) -> set[int]:
    if not raw:
        return set()
    out = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            out.add(int(part))
    return out


@dataclass
class HermesConfig:
    discord_token: str
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Accès : par défaut personne n'a les outils sensibles (code exec, génération
    # de jeux Roblox) tant que ces listes ne sont pas explicitement remplies —
    # un bot Discord est potentiellement joignable par n'importe qui sur un
    # serveur, donc "vide = fermé" plutôt que "vide = ouvert à tous".
    admin_user_ids: set[int] = field(default_factory=set)
    allowed_guild_ids: set[int] = field(default_factory=set)

    command_prefix: str = "!hermes "
    max_history_messages: int = 20
    max_tool_calls_per_turn: int = 8
    max_subagent_depth: int = 1

    sandbox_timeout_seconds: float = 10.0
    sandbox_memory_limit_mb: int = 256

    @property
    def has_admins(self) -> bool:
        return bool(self.admin_user_ids)

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_user_ids

    def guild_allowed(self, guild_id: int | None) -> bool:
        if not self.allowed_guild_ids:
            return True
        return guild_id in self.allowed_guild_ids


def load_config() -> HermesConfig:
    discord_token = os.environ.get("DISCORD_BOT_TOKEN", "")
    deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not discord_token:
        raise RuntimeError("DISCORD_BOT_TOKEN manquant (voir docs/HERMES_BOT.md)")
    if not deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY manquant (voir docs/HERMES_BOT.md)")

    return HermesConfig(
        discord_token=discord_token,
        deepseek_api_key=deepseek_api_key,
        deepseek_base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        deepseek_model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        admin_user_ids=_split_ids(os.environ.get("HERMES_ADMIN_USER_IDS")),
        allowed_guild_ids=_split_ids(os.environ.get("HERMES_ALLOWED_GUILD_IDS")),
        command_prefix=os.environ.get("HERMES_COMMAND_PREFIX", "!hermes "),
        max_history_messages=int(os.environ.get("HERMES_MAX_HISTORY", "20")),
        max_tool_calls_per_turn=int(os.environ.get("HERMES_MAX_TOOL_CALLS", "8")),
        max_subagent_depth=int(os.environ.get("HERMES_MAX_SUBAGENT_DEPTH", "1")),
        sandbox_timeout_seconds=float(os.environ.get("HERMES_SANDBOX_TIMEOUT", "10")),
        sandbox_memory_limit_mb=int(os.environ.get("HERMES_SANDBOX_MEMORY_MB", "256")),
    )
