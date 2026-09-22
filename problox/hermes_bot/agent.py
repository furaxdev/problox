"""Boucle agentique : message utilisateur -> DeepSeek (+ tool calling) ->
exécution d'outils -> réponse finale. Utilisée à la fois pour la conversation
principale d'un salon et pour les sous-agents (`spawn_subagent`)."""

from __future__ import annotations

import json
import logging
from typing import Any

from problox.hermes_bot import tools
from problox.hermes_bot.config import HermesConfig
from problox.hermes_bot.deepseek_client import DeepSeekClient, DeepSeekError

logger = logging.getLogger("hermes_bot")

SYSTEM_PROMPT = """Tu es Hermès, l'assistant IA du projet ProbloxDev (agent
autonome qui conçoit et code des jeux Roblox). Tu réponds sur Discord : sois
concis, direct, en français par défaut sauf si on te parle en anglais.
Utilise les outils à ta disposition quand ils sont utiles plutôt que de
deviner (recherche web pour une info fraîche, exécution de code pour un
calcul/test, génération de jeu pour une demande de prototype Roblox). N'
invente jamais un résultat d'outil que tu n'as pas réellement obtenu."""

SUBAGENT_SYSTEM_PROMPT = """Tu es un sous-agent temporaire spawné par
Hermès pour une tâche précise et autonome. Fais UNIQUEMENT cette tâche,
utilise les outils si utile, puis rends un résultat final concis en texte —
pas de suivi de conversation, pas de question, une seule réponse."""


def _is_admin_tool(name: str) -> bool:
    return name in tools.admin_only_tool_names()


def run_tool(
    name: str,
    args: dict[str, Any],
    *,
    config: HermesConfig,
    channel_id: int,
    is_admin: bool,
    subagent_depth: int,
) -> str:
    if _is_admin_tool(name) and not is_admin:
        return "Erreur: cet outil est réservé aux admins Hermès configurés."

    if name == "web_search":
        return tools.web_search(args)
    if name == "execute_code":
        return tools.execute_code(args, config)
    if name == "problox_build_game":
        return tools.problox_build_game(args, channel_id)
    if name == "spawn_subagent":
        if subagent_depth >= config.max_subagent_depth:
            return "Erreur: profondeur maximale de sous-agents atteinte."
        task = (args.get("task") or "").strip()
        if not task:
            return "Erreur: paramètre 'task' manquant."
        return run_subagent(task, config=config, channel_id=channel_id, depth=subagent_depth + 1)

    return f"Erreur: outil inconnu '{name}'."


def _available_tools(config: HermesConfig, is_admin: bool, subagent_depth: int) -> list[dict[str, Any]]:
    declared = tools.TOOL_DECLARATIONS
    if not is_admin:
        declared = [t for t in declared if t["function"]["name"] not in tools.admin_only_tool_names()]
    elif subagent_depth >= config.max_subagent_depth:
        declared = [t for t in declared if t["function"]["name"] != "spawn_subagent"]
    return declared


def run_turn(
    history: list[dict[str, Any]],
    user_message: str,
    *,
    config: HermesConfig,
    channel_id: int,
    is_admin: bool,
    subagent_depth: int = 0,
) -> tuple[str, list[dict[str, Any]]]:
    """Fait tourner la boucle agentique pour UN message utilisateur.

    Retourne (réponse_finale, nouveaux_messages_à_persister) — les nouveaux
    messages incluent le message utilisateur, les éventuels tool calls/
    résultats intermédiaires, et la réponse finale, dans l'ordre.
    """
    client = DeepSeekClient(config.deepseek_api_key, config.deepseek_base_url, config.deepseek_model)

    system = SUBAGENT_SYSTEM_PROMPT if subagent_depth > 0 else SYSTEM_PROMPT
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
    messages.extend({k: v for k, v in m.items() if k in ("role", "content", "tool_calls", "tool_call_id", "name")} for m in history)
    messages.append({"role": "user", "content": user_message})

    new_messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]
    available = _available_tools(config, is_admin, subagent_depth)

    for _ in range(config.max_tool_calls_per_turn):
        try:
            assistant_msg = client.chat(messages, tools=available or None)
        except DeepSeekError as exc:
            error_text = f"Erreur DeepSeek: {exc}"
            new_messages.append({"role": "assistant", "content": error_text})
            return error_text, new_messages

        tool_calls = assistant_msg.get("tool_calls")
        if not tool_calls:
            content = assistant_msg.get("content") or "(réponse vide)"
            new_messages.append({"role": "assistant", "content": content})
            return content, new_messages

        messages.append(assistant_msg)
        new_messages.append(assistant_msg)

        for call in tool_calls:
            fn = call.get("function", {})
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}

            logger.info("hermes tool call: %s(%s)", name, args)
            result = run_tool(
                name,
                args,
                config=config,
                channel_id=channel_id,
                is_admin=is_admin,
                subagent_depth=subagent_depth,
            )
            tool_msg = {"role": "tool", "tool_call_id": call.get("id", ""), "name": name, "content": result}
            messages.append(tool_msg)
            new_messages.append(tool_msg)

    fallback = "Désolé, j'ai atteint la limite d'appels d'outils pour ce tour sans conclure."
    new_messages.append({"role": "assistant", "content": fallback})
    return fallback, new_messages


def run_subagent(task: str, *, config: HermesConfig, channel_id: int, depth: int) -> str:
    result, _ = run_turn(
        history=[],
        user_message=task,
        config=config,
        channel_id=channel_id,
        is_admin=True,  # un sous-agent hérite des droits de celui qui l'a spawné (toujours un admin, voir run_tool)
        subagent_depth=depth,
    )
    return result
