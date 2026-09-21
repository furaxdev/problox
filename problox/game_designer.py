"""Génère un game design document structuré à partir d'un thème, via Claude.

Le design est un JSON strict (voir GameDesign) que luau_generator.py sait
transformer en arborescence de scripts. Si aucune clé Anthropic n'est
configurée, on retombe sur un design "starter kit" codé en dur (toujours
fonctionnel, juste moins créatif) pour que le pipeline reste utilisable hors
ligne / en démo.
"""

from __future__ import annotations

import json
from typing import Any

from anthropic import Anthropic
from pydantic import BaseModel, Field

SYSTEM_PROMPT = """Tu es un game designer senior spécialisé Roblox. Tu conçois
des boucles de jeu à forte rétention (mécaniques éprouvées : progression
courte, récompenses variables, économie virtuelle, compétition sociale,
FOMO raisonnable). Contraintes strictes :
- Respecte les Community Standards Roblox : pas de violence réaliste/graphique,
  pas de contenu sexuel, pas de gambling avec argent réel, pas de dark
  patterns manipulatoires envers les mineurs au-delà des pratiques
  standards de l'industrie (récompenses quotidiennes oui, loot box payante
  agressive non).
- Réponds UNIQUEMENT avec un JSON valide conforme au schéma demandé, sans
  texte autour.
"""

SCHEMA_HINT = {
    "title": "string",
    "genre": "string (ex: obby, tycoon, simulator, battle royale casual)",
    "core_loop": "string décrivant la boucle 30-90s action->récompense",
    "systems": [
        {
            "name": "string (ex: Currency, DailyReward, Leaderboard, Checkpoint, Shop)",
            "description": "string",
        }
    ],
    "monetization": {
        "currency_name": "string",
        "gamepasses": [{"name": "string", "effect": "string", "suggested_price_robux": "int"}],
    },
    "zones_or_levels": [{"name": "string", "description": "string"}],
    "retention_hooks": ["string (ex: streak quotidien, événement limité, classement hebdo)"],
}


class GameSystem(BaseModel):
    name: str
    description: str


class Gamepass(BaseModel):
    name: str
    effect: str
    suggested_price_robux: int = 99


class Monetization(BaseModel):
    currency_name: str = "Coins"
    gamepasses: list[Gamepass] = Field(default_factory=list)


class Zone(BaseModel):
    name: str
    description: str


class GameDesign(BaseModel):
    title: str
    genre: str
    core_loop: str
    systems: list[GameSystem]
    monetization: Monetization
    zones_or_levels: list[Zone]
    retention_hooks: list[str]

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


def _fallback_design(theme: str) -> GameDesign:
    return GameDesign(
        title=f"{theme.title()} Rush",
        genre="obby + simulator hybride",
        core_loop=(
            "Le joueur court un parcours d'obstacles courts (30-60s), gagne des "
            "Coins à chaque checkpoint, peut les dépenser en boutique pour des "
            "boosts de vitesse/apparence, puis relance immédiatement une manche."
        ),
        systems=[
            GameSystem(name="Currency", description="Coins persistants via DataStoreService"),
            GameSystem(name="Checkpoint", description="Sauvegarde de progression par checkpoint touché"),
            GameSystem(name="Leaderboard", description="Classement global OrderedDataStore (Coins totaux)"),
            GameSystem(name="DailyReward", description="Récompense croissante à la connexion quotidienne"),
            GameSystem(name="Shop", description="Boutique de boosts/skins contre Coins ou Robux"),
        ],
        monetization=Monetization(
            currency_name="Coins",
            gamepasses=[
                Gamepass(name="Speed Boost", effect="+20% vitesse permanente", suggested_price_robux=149),
                Gamepass(name="2x Coins", effect="Double les gains de Coins", suggested_price_robux=199),
            ],
        ),
        zones_or_levels=[
            Zone(name="Zone 1 - Départ", description="Obstacles simples, tutoriel implicite"),
            Zone(name="Zone 2 - Accélération", description="Plateformes mobiles, difficulté progressive"),
            Zone(name="Zone 3 - Défi", description="Section optionnelle à haute difficulté, forte récompense"),
        ],
        retention_hooks=[
            "Récompense quotidienne croissante (streak)",
            "Classement global visible en permanence",
            "Nouvelle zone débloquée par palier de Coins cumulés",
        ],
    )


def design(theme: str, anthropic_api_key: str | None, previous: dict | None = None) -> GameDesign:
    if not anthropic_api_key:
        return _fallback_design(theme)

    client = Anthropic(api_key=anthropic_api_key)
    user_prompt = (
        f"Thème demandé : {theme}\n\n"
        f"Schéma JSON attendu :\n{json.dumps(SCHEMA_HINT, ensure_ascii=False, indent=2)}\n\n"
    )
    if previous:
        user_prompt += (
            "Design précédent (itère dessus, améliore la rétention et ajoute UNE "
            f"nouvelle mécanique cohérente) :\n{json.dumps(previous, ensure_ascii=False)}\n"
        )

    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    data = json.loads(text)
    return GameDesign.model_validate(data)
