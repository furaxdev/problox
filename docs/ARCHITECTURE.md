# Boucle autonome de Problox

```
 ┌───────────────┐      ┌────────────────┐      ┌──────────────────┐
 │ game_designer  │ ---> │ luau_generator  │ ---> │  rojo_project     │
 │ (Claude: thème │      │ (design doc ->  │      │ (arbo Rojo,       │
 │  -> design doc)│      │  fichiers .luau)│      │  rojo build)      │
 └───────────────┘      └────────────────┘      └────────┬──────────┘
                                                            │
                          ┌─────────────────────────────────┘
                          v
                 ┌────────────────┐        ┌──────────────┐
                 │  roblox_cloud   │ -----> │  Roblox       │
                 │ (Open Cloud API)│        │  (place live) │
                 └────────┬────────┘        └──────────────┘
                          │
                          v
                 ┌────────────────┐
                 │     state       │  <- mémoire persistante (JSON) :
                 │ (.problox_state)│     version du design, itération,
                 └────────────────┘     métriques si dispo (via API)
```

## `orchestrator.py` — `run(theme, autonomous, max_iterations)`

1. Charge/initialise l'état (`state.py`).
2. `game_designer.design(theme, state)` -> `GameDesign` (JSON structuré :
   boucle de jeu, systèmes, économie, zones, monétisation).
3. `luau_generator.generate(design)` -> écrit les fichiers dans
   `build/src/**/*.luau` + assemble `default.project.json` (Rojo).
4. `rojo_project.build()` -> exécute `rojo build` -> `build/place.rbxlx`.
5. Lint/format best-effort (`selene`, `stylua`) si présents dans le PATH ;
   échec de lint = warning loggé, jamais bloquant (le jeu doit quand même se
   construire).
6. Si les credentials Open Cloud sont présents : `roblox_cloud.publish_place()`
   uploade `place.rbxlx` sur `ROBLOX_UNIVERSE_ID`/`ROBLOX_PLACE_ID`. Sinon,
   log clair "dry-run — publication manquée, voir README".
7. Sauvegarde l'état (itération incrémentée, hash du design) dans
   `.problox_state.json`.
8. Si `autonomous=True` et `max_iterations>1` : relit l'état, décide (LLM) une
   itération d'amélioration (nouvelle mécanique, ajustement d'économie) et
   reboucle à l'étape 2 avec le design précédent comme contexte, jusqu'à
   `max_iterations` ou convergence (pas de diff significatif proposé).

## Pourquoi pas une boucle 100% infinie par défaut

Publier en boucle infinie sans supervision humaine sur un compte réel est
risqué (quota API, contenu généré non modéré avant mise en ligne). Par
défaut `max_iterations` est borné (5) et chaque run affiche un résumé des
changements. Le mode vraiment illimité (`--autonomous --max-iterations 0`)
est possible mais documenté comme "à tes risques", avec rate-limiting
intégré dans `roblox_cloud.py`.

## Modération de contenu

Roblox exige que tout texte/asset généré respecte les Community Standards.
`game_designer.py` inclut un garde-fou de prompt (pas de contenu violent
réaliste, pas de contenu adulte, pas d'incitation au gambling réel) — mais
ça n'est **pas** un filtre de modération certifié : une revue humaine avant
publication publique reste recommandée, surtout pour les assets visuels.
