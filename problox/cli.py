from __future__ import annotations

import logging

import click

from problox.config import load_config
from problox.orchestrator import run as run_orchestrator


@click.group()
def main() -> None:
    """Problox — agent IA autonome pour la création de jeux Roblox."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


@main.command()
@click.option("--theme", required=True, help="Thème du jeu (ex: 'obby simulateur de course').")
@click.option("--autonomous", is_flag=True, help="Itère plusieurs fois sans confirmation manuelle.")
@click.option("--max-iterations", default=1, show_default=True, type=int)
def run(theme: str, autonomous: bool, max_iterations: int) -> None:
    """Lance la boucle complète: design -> code -> build -> publication."""
    config = load_config()
    if not config.has_anthropic_credentials:
        click.echo(
            "ANTHROPIC_API_KEY manquant — utilisation du design 'starter kit' par "
            "défaut (fonctionnel mais générique). Renseigne .env pour une "
            "génération créative via Claude.",
            err=True,
        )
    run_orchestrator(theme, config, autonomous=autonomous, max_iterations=max_iterations)


@main.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8787, show_default=True, type=int)
def web(host: str, port: int) -> None:
    """Lance le site ProbloxDev (dashboard pour piloter l'agent depuis un navigateur)."""
    import uvicorn

    click.echo(f"ProbloxDev sur http://{host}:{port}")
    uvicorn.run("problox.web:app", host=host, port=port, log_level="warning")


@main.command()
def hermes() -> None:
    """Lance le bot Discord Hermès (nécessite l'extra `hermes` installé)."""
    from problox.hermes_bot.bot import main as hermes_main

    hermes_main()


@main.command()
def check() -> None:
    """Vérifie la config et la présence des outils (rojo/selene/stylua)."""
    import shutil

    config = load_config()
    click.echo(f"Anthropic API key: {'OK' if config.has_anthropic_credentials else 'manquante'}")
    click.echo(f"Roblox Open Cloud: {'OK' if config.has_roblox_credentials else 'incomplet (' + ', '.join(config.missing_roblox_vars()) + ')'}")
    for tool in ("rojo", "selene", "stylua", "aftman", "wally"):
        click.echo(f"{tool}: {'trouvé' if shutil.which(tool) else 'absent'}")


if __name__ == "__main__":
    main()
