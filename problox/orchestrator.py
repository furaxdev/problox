"""Boucle autonome: design -> code -> build -> (publish) -> itère."""

from __future__ import annotations

import logging
from pathlib import Path

from problox import game_designer, luau_generator, rojo_project, roblox_cloud
from problox.config import Config
from problox.state import AgentState

logger = logging.getLogger("problox")

BUILD_DIR = Path("build")


def run(theme: str, config: Config, autonomous: bool = False, max_iterations: int = 1) -> None:
    state = AgentState.load()
    state.theme = state.theme or theme

    iterations = max(1, max_iterations) if autonomous else 1

    for i in range(iterations):
        logger.info("=== Itération %d/%d ===", i + 1, iterations)
        previous_design = state.design_history[-1] if state.design_history else None

        design = game_designer.design(theme, config.anthropic_api_key, previous=previous_design)
        logger.info("Design: %s (%s)", design.title, design.genre)

        luau_generator.generate(design, BUILD_DIR)
        logger.info("Projet Rojo généré dans %s/", BUILD_DIR)

        warnings = rojo_project.lint_and_format(BUILD_DIR)
        for w in warnings:
            logger.warning(w)

        try:
            rbxlx_path = rojo_project.build(BUILD_DIR)
            logger.info("Build Rojo -> %s", rbxlx_path)
        except rojo_project.RojoNotFoundError as exc:
            logger.warning(str(exc))
            state.record_iteration(design.to_dict())
            state.save()
            continue

        if config.has_roblox_credentials:
            client = roblox_cloud.RobloxCloudClient(
                api_key=config.roblox_api_key,
                universe_id=config.roblox_universe_id,
                place_id=config.roblox_place_id,
            )
            try:
                version = client.publish_place(rbxlx_path)
                state.last_place_version = version
                logger.info("Publié sur Roblox — version %s", version)
            except roblox_cloud.RobloxCloudError as exc:
                logger.error("Échec de publication: %s", exc)
        else:
            missing = config.missing_roblox_vars()
            logger.warning(
                "Dry-run: variables manquantes (%s) — le jeu est prêt dans %s/ "
                "mais n'a pas été publié. Ouvre build/place.rbxlx dans Roblox Studio "
                "pour le voir, ou renseigne .env puis relance.",
                ", ".join(missing),
                BUILD_DIR,
            )

        state.record_iteration(design.to_dict())
        state.save()

    logger.info("Terminé. Itération courante: %d", state.iteration)
