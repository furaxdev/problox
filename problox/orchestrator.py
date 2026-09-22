"""Boucle autonome: design -> code -> build -> (publish) -> itère.

`run()` est appelée à la fois par la CLI (un seul utilisateur, credentials
dans .env) et par le backend web (potentiellement plusieurs utilisateurs en
parallèle, credentials OAuth par session) — d'où les paramètres `build_dir`,
`state_path` et `roblox_client` qui permettent d'isoler chaque run au lieu de
partager un état global.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from problox import game_designer, luau_generator, rojo_project, roblox_cloud
from problox.config import Config
from problox.state import STATE_PATH, AgentState

logger = logging.getLogger("problox")

BUILD_DIR = Path("build")


def run(
    theme: str,
    config: Config,
    autonomous: bool = False,
    max_iterations: int = 1,
    build_dir: Path = BUILD_DIR,
    state_path: Path = STATE_PATH,
    roblox_client: roblox_cloud.RobloxCloudClient | None = None,
    log: Callable[[str], None] = logger.info,
) -> None:
    """Si `roblox_client` est fourni (ex: session OAuth web), il est utilisé
    tel quel pour la publication et prime sur les credentials de `config`."""
    state = AgentState.load(state_path)
    state.theme = state.theme or theme

    iterations = max(1, max_iterations) if autonomous else 1

    for i in range(iterations):
        log(f"=== Itération {i + 1}/{iterations} ===")
        previous_design = state.design_history[-1] if state.design_history else None

        design = game_designer.design(
            theme,
            config.anthropic_api_key,
            previous=previous_design,
            log=log,
            groq_api_key=config.groq_api_key,
        )
        log(f"Design: {design.title} ({design.genre})")

        luau_generator.generate(design, build_dir)
        log(f"Projet Rojo généré dans {build_dir}/")

        for w in rojo_project.lint_and_format(build_dir):
            log(f"AVERTISSEMENT: {w}")

        try:
            rbxlx_path = rojo_project.build(build_dir)
            log(f"Build Rojo -> {rbxlx_path}")
        except rojo_project.RojoNotFoundError as exc:
            log(str(exc))
            state.record_iteration(design.to_dict())
            state.save(state_path)
            continue

        client = roblox_client
        if client is None and config.has_roblox_credentials:
            client = roblox_cloud.RobloxCloudClient(
                api_key=config.roblox_api_key,
                universe_id=config.roblox_universe_id,
                place_id=config.roblox_place_id,
            )

        if client is not None:
            try:
                version = client.publish_place(rbxlx_path)
                state.last_place_version = version
                log(f"Publié sur Roblox — version {version}")
                _run_smoke_test(client, version, log)
            except roblox_cloud.RobloxCloudError as exc:
                hint = ""
                if "401" in str(exc) or "403" in str(exc):
                    hint = (
                        " (401/403 avec un token OAuth: l'API Roblox de publication de "
                        "place ne documente que l'auth par clé API, pas OAuth — voir "
                        "docs/OAUTH_SETUP.md. Le build reste disponible en téléchargement.)"
                    )
                log(f"ERREUR: échec de publication: {exc}{hint}")
        else:
            missing = config.missing_roblox_vars()
            log(
                f"Dry-run: variables manquantes ({', '.join(missing)}) — le jeu est prêt "
                f"dans {build_dir}/ mais n'a pas été publié. Ouvre {build_dir}/place.rbxlx "
                "dans Roblox Studio pour le voir, ou connecte un compte Roblox puis relance."
            )

        state.record_iteration(design.to_dict())
        state.save(state_path)

    log(f"Terminé. Itération courante: {state.iteration}")


_SMOKE_TEST_SCRIPT = """
local ServerScriptService = game:GetService("ServerScriptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local services = ServerScriptService:FindFirstChild("Services")
local gameDesign = ReplicatedStorage:FindFirstChild("GameDesign")
if services and gameDesign then
    print("SMOKE_OK")
else
    print("SMOKE_FAIL: services=" .. tostring(services ~= nil) .. " gameDesign=" .. tostring(gameDesign ~= nil))
end
"""


def _run_smoke_test(client: roblox_cloud.RobloxCloudClient, version: int, log: Callable[[str], None]) -> None:
    """Exécute un test headless (sans Studio) sur la version publiée, via
    l'API Open Cloud Luau Execution Session — vérifie juste que le serveur
    démarre et que la hiérarchie attendue existe, pas que le jeu est
    "amusant". Best-effort : un échec ici (scope manquant, timeout) ne fait
    pas échouer le run, juste un avertissement loggé."""
    try:
        result = client.execute_luau(version, _SMOKE_TEST_SCRIPT)
    except roblox_cloud.RobloxCloudError as exc:
        log(f"Smoke test non exécuté: {exc}")
        return

    output = " | ".join(result.output_lines) or "(pas de sortie)"
    if result.success and "SMOKE_OK" in output:
        log(f"Smoke test: OK ({output})")
    elif result.error:
        log(f"Smoke test: échec — {result.error}")
    else:
        log(f"Smoke test: résultat inattendu — {output}")
