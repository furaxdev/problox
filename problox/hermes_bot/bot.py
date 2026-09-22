"""Client Discord — répond quand on le mentionne ou via le préfixe configuré,
délègue tout le raisonnement à `agent.run_turn`. Import de `discord.py`
retardé/optionnel (extra `hermes`) pour ne pas casser l'install de base."""

from __future__ import annotations

import asyncio
import logging

from problox.hermes_bot import agent
from problox.hermes_bot.config import HermesConfig, load_config
from problox.hermes_bot.memory import ChannelMemory

logger = logging.getLogger("hermes_bot")

DISCORD_MESSAGE_LIMIT = 2000


def _chunk(text: str, size: int = DISCORD_MESSAGE_LIMIT) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]


def build_client(config: HermesConfig):
    try:
        import discord
    except ImportError as exc:
        raise RuntimeError(
            "discord.py n'est pas installé — installe l'extra: pip install -e '.[hermes]'"
        ) from exc

    intents = discord.Intents.default()
    intents.message_content = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        logger.info("Hermès connecté en tant que %s", client.user)

    @client.event
    async def on_message(message: "discord.Message"):
        if message.author.bot:
            return
        if client.user not in message.mentions and not message.content.startswith(config.command_prefix):
            return
        if message.guild is not None and not config.guild_allowed(message.guild.id):
            return

        if message.content.startswith(config.command_prefix):
            text = message.content[len(config.command_prefix) :].strip()
        else:
            text = message.content
            for mention in message.mentions:
                text = text.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "")
            text = text.strip()

        if not text:
            return

        is_admin = config.is_admin(message.author.id)
        memory = ChannelMemory(message.channel.id, config.max_history_messages)

        async with message.channel.typing():
            try:
                reply, new_messages = await asyncio.to_thread(
                    agent.run_turn,
                    memory.messages,
                    text,
                    config=config,
                    channel_id=message.channel.id,
                    is_admin=is_admin,
                )
            except Exception as exc:  # noqa: BLE001 - le bot ne doit jamais crasher sur un message
                logger.exception("Erreur pendant le traitement du message")
                await message.reply(f"Erreur interne: {exc}")
                return

        memory.messages.extend(new_messages)
        if len(memory.messages) > memory.max_messages * 2:
            memory.messages = memory.messages[-memory.max_messages * 2 :]
        memory._save()  # noqa: SLF001 - append en lot, pas d'API publique pour ça

        for chunk in _chunk(reply):
            if chunk:
                await message.reply(chunk, mention_author=False)

    return client


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    if not config.has_admins:
        logger.warning(
            "HERMES_ADMIN_USER_IDS vide: personne ne pourra utiliser execute_code / "
            "problox_build_game / spawn_subagent tant que ce n'est pas configuré."
        )
    client = build_client(config)
    client.run(config.discord_token)


if __name__ == "__main__":
    main()
