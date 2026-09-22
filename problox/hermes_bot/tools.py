"""Outils exposés à l'agent Hermès via le tool calling DeepSeek.

Chaque outil est une fonction Python pure `(args: dict) -> str` (le résultat
texte renvoyé au modèle) + une déclaration JSON-schema pour l'API. Certains
outils (`execute_code`, `problox_build_game`, `spawn_subagent`) sont
réservés aux admins configurés (`HermesConfig.admin_user_ids`) car ils
consomment des ressources/API payantes ou exécutent du code.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

import httpx

from problox import game_designer, luau_generator, rojo_project
from problox.hermes_bot import sandbox
from problox.hermes_bot.config import HermesConfig

BUILDS_DIR = Path("hermes_builds")

ToolFn = Callable[[dict[str, Any]], str]


def web_search(args: dict[str, Any]) -> str:
    """Recherche web best-effort sans clé API : scrape la version HTML de
    DuckDuckGo. Pas de garantie de fraîcheur/exactitude — c'est un résumé de
    résultats, pas un accès direct aux pages."""
    query = (args.get("query") or "").strip()
    if not query:
        return "Erreur: paramètre 'query' manquant."
    try:
        response = httpx.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (ProbloxDev Hermes bot)"},
            timeout=15.0,
        )
    except httpx.HTTPError as exc:
        return f"Erreur réseau pendant la recherche: {exc}"
    if response.status_code >= 400:
        return f"Recherche échouée ({response.status_code})"

    titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', response.text, re.S)
    links = re.findall(r'class="result__a"\s+href="([^"]+)"', response.text)
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', response.text, re.S)

    def clean(s: str) -> str:
        return re.sub(r"<[^>]+>", "", s).strip()

    results = []
    for i, (title, link) in enumerate(zip(titles, links)):
        snippet = clean(snippets[i]) if i < len(snippets) else ""
        results.append(f"{i + 1}. {clean(title)} — {link}\n   {snippet}")
        if len(results) >= 5:
            break

    if not results:
        return "Aucun résultat trouvé."
    return "\n".join(results)


def execute_code(args: dict[str, Any], config: HermesConfig) -> str:
    code = args.get("code") or ""
    if not code.strip():
        return "Erreur: paramètre 'code' manquant."
    result = sandbox.run_python(
        code,
        timeout_seconds=config.sandbox_timeout_seconds,
        memory_limit_mb=config.sandbox_memory_limit_mb,
    )
    parts = [f"exit_code={result.exit_code}"]
    if result.timed_out:
        parts.append("(TIMEOUT)")
    if result.stdout:
        parts.append(f"stdout:\n{result.stdout}")
    if result.stderr:
        parts.append(f"stderr:\n{result.stderr}")
    return "\n".join(parts)


def problox_build_game(args: dict[str, Any], channel_id: int) -> str:
    """Génère un design + le projet Rojo (scripts Luau) pour un thème donné,
    et build un .rbxlx — SANS publier sur Roblox (aucun credential
    utilisateur disponible côté bot). Retourne le chemin du build."""
    theme = (args.get("theme") or "").strip()
    if not theme:
        return "Erreur: paramètre 'theme' manquant."

    build_dir = BUILDS_DIR / str(channel_id)
    design = game_designer.design(theme, anthropic_api_key=None)
    luau_generator.generate(design, build_dir)

    warnings = list(rojo_project.lint_and_format(build_dir))
    try:
        rbxlx_path = rojo_project.build(build_dir)
    except rojo_project.RojoNotFoundError as exc:
        return (
            f"Design '{design.title}' ({design.genre}) généré dans {build_dir}/, "
            f"mais le build Rojo a échoué: {exc}"
        )

    summary = (
        f"Jeu généré: {design.title} ({design.genre})\n"
        f"Boucle: {design.core_loop}\n"
        f"Systèmes: {', '.join(s.name for s in design.systems)}\n"
        f"Build: {rbxlx_path}"
    )
    if warnings:
        summary += f"\nAvertissements lint: {len(warnings)}"
    return summary


TOOL_DECLARATIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Cherche sur le web (résultats DuckDuckGo, texte brut) pour une info récente ou externe.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "La requête de recherche"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_code",
            "description": (
                "Exécute un script Python dans un sandbox isolé (pas d'accès réseau garanti, "
                "limites CPU/mémoire/temps). Réservé aux admins."
            ),
            "parameters": {
                "type": "object",
                "properties": {"code": {"type": "string", "description": "Code Python à exécuter"}},
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "problox_build_game",
            "description": (
                "Génère un jeu Roblox complet (design + scripts Luau + build .rbxlx) pour un thème "
                "donné via le pipeline ProbloxDev. Ne publie pas sur Roblox. Réservé aux admins."
            ),
            "parameters": {
                "type": "object",
                "properties": {"theme": {"type": "string", "description": "Thème du jeu, ex: 'obby lave parkour'"}},
                "required": ["theme"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "spawn_subagent",
            "description": (
                "Délègue une sous-tâche autonome à un agent enfant avec son propre contexte "
                "(recherche web + code, pas de récursion supplémentaire). Utile pour une tâche "
                "indépendante qui polluerait la conversation principale. Réservé aux admins."
            ),
            "parameters": {
                "type": "object",
                "properties": {"task": {"type": "string", "description": "Description précise et autonome de la sous-tâche"}},
                "required": ["task"],
            },
        },
    },
]


def admin_only_tool_names() -> set[str]:
    return {"execute_code", "problox_build_game", "spawn_subagent"}
