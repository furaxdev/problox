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
