"""Génère un game design document structuré à partir d'un thème, via Claude.

Le design est un JSON strict (voir GameDesign) que luau_generator.py sait
transformer en arborescence de scripts. Si aucune clé Anthropic n'est
configurée, on retombe sur un design "starter kit" codé en dur (toujours
fonctionnel, juste moins créatif) pour que le pipeline reste utilisable hors
ligne / en démo.
"""

from __future__ import annotations

import json
from collections.abc import Callable
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


_OBBY_KEYWORDS = ("obby", "parkour", "course", "rush", "runner", "saut")
_TYCOON_KEYWORDS = ("tycoon", "usine", "empire", "business", "argent", "fabrique", "entreprise")
_ARENA_KEYWORDS = ("pvp", "arène", "arene", "combat", "bataille", "battle", "duel", "fight")


def _pick_archetype(theme: str) -> str:
    lowered = theme.lower()
    if any(k in lowered for k in _TYCOON_KEYWORDS):
        return "tycoon"
    if any(k in lowered for k in _ARENA_KEYWORDS):
        return "arena"
    if any(k in lowered for k in _OBBY_KEYWORDS):
        return "obby"
    # Thème générique sans mot-clé reconnu: on fait quand même varier
    # l'archétype (déterministe sur le thème) plutôt que de toujours
    # retomber sur le même jeu — c'était le cas avant, tous les designs
    # fallback produisaient exactement le même code, seul le titre changeait.
    archetypes = ("obby", "tycoon", "arena")
    return archetypes[sum(theme.encode()) % len(archetypes)]


def _fallback_design(theme: str) -> GameDesign:
    archetype = _pick_archetype(theme)
    title = f"{theme.title()} {'Tycoon' if archetype == 'tycoon' else 'Rush' if archetype == 'obby' else 'Arena'}"

    if archetype == "tycoon":
        return GameDesign(
            title=title,
            genre="tycoon",
            core_loop=(
                "Le joueur réclame une parcelle libre, des droppers y génèrent des "
                "Coins en continu, il les collecte au contact puis les dépense en "
                "boutique pour accélérer sa production ou débloquer des upgrades."
            ),
            systems=[
                GameSystem(name="Currency", description="Coins persistants via DataStoreService"),
                GameSystem(name="Plot", description="Réclamation de parcelle + droppers générant des Coins en continu"),
                GameSystem(name="Leaderboard", description="Classement global OrderedDataStore (Coins totaux)"),
                GameSystem(name="DailyReward", description="Récompense croissante à la connexion quotidienne"),
                GameSystem(name="Shop", description="Boutique d'upgrades de production contre Coins ou Robux"),
            ],
            monetization=Monetization(
                currency_name="Coins",
                gamepasses=[
                    Gamepass(name="2x Production", effect="Double le rendement des droppers", suggested_price_robux=249),
                    Gamepass(name="Parcelle VIP", effect="Accès à une parcelle premium plus rentable", suggested_price_robux=349),
                ],
            ),
            zones_or_levels=[
                Zone(name="Parcelles de départ", description="Production de base, premières upgrades accessibles"),
                Zone(name="Parcelles avancées", description="Débloquées à un palier de Coins cumulés, meilleur rendement"),
            ],
            retention_hooks=[
                "Production qui continue même à faible interaction (retour régulier payant)",
                "Récompense quotidienne croissante (streak)",
                "Classement global visible en permanence",
            ],
        )

    if archetype == "arena":
        return GameDesign(
            title=title,
            genre="battle royale casual",
            core_loop=(
                "Manches courtes (60-90s) en arène réduite: le joueur élimine des "
                "adversaires ou survit jusqu'à la fin, gagne des Coins selon sa "
                "performance, puis relance immédiatement une nouvelle manche."
            ),
            systems=[
                GameSystem(name="Currency", description="Coins persistants via DataStoreService"),
                GameSystem(name="Leaderboard", description="Classement global OrderedDataStore (Coins totaux)"),
                GameSystem(name="DailyReward", description="Récompense croissante à la connexion quotidienne"),
                GameSystem(name="Shop", description="Boutique de skins/effets visuels contre Coins ou Robux"),
            ],
            monetization=Monetization(
                currency_name="Coins",
                gamepasses=[
                    Gamepass(name="2x Coins", effect="Double les gains de Coins par manche", suggested_price_robux=199),
                    Gamepass(name="Skin exclusif", effect="Apparence unique en arène", suggested_price_robux=149),
                ],
            ),
            zones_or_levels=[
                Zone(name="Arène principale", description="Map de manche standard"),
                Zone(name="Arène événement", description="Variante à rotation limitée dans le temps (FOMO)"),
            ],
            retention_hooks=[
                "Manches très courtes -> relance immédiate sans friction",
                "Récompense quotidienne croissante (streak)",
                "Classement global visible en permanence",
            ],
        )

    return GameDesign(
        title=title,
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


def design(
    theme: str,
    anthropic_api_key: str | None,
    previous: dict | None = None,
    log: Callable[[str], None] = lambda _msg: None,
) -> GameDesign:
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

    try:
        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        data = json.loads(text)
        return GameDesign.model_validate(data)
    except Exception as exc:  # noqa: BLE001 - un run public ne doit pas mourir sur un aléa d'API
        log(
            f"Claude a échoué ({exc.__class__.__name__}: {exc}) — repli sur le "
            "design starter kit pour cette itération."
        )
        return _fallback_design(theme)
