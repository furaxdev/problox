# Meilleurs outils open source pour le dev de jeux Roblox

Sélection utilisée/intégrée par Problox, installée via gestionnaires de
paquets officiels (pas de clone-and-run aveugle).

| Outil | Rôle | Pourquoi il est intégré |
|---|---|---|
| [Rojo](https://github.com/rojo-rbx/rojo) | Synchronise un dossier de fichiers `.lua`/`.luau` ↔ Roblox Studio | Standard de facto pour développer du Luau hors-Studio (donc scriptable par un agent CLI). Problox génère un projet Rojo complet (`default.project.json`) puis `rojo build` en `.rbxlx`. |
| [Aftman](https://github.com/LPGhatguy/aftman) | Gestionnaire de version d'outils (comme `asdf`) | Installe Rojo/Selene/StyLua de façon reproductible via `aftman.toml`. |
| [Wally](https://github.com/UpliftGames/wally) | Gestionnaire de paquets Luau | Permet d'ajouter des libs communautaires (ProfileService-like, Signal, Promise) sans réinventer la roue à chaque run de l'agent. |
| [Selene](https://github.com/Kampfkarren/selene) | Linter Luau | Détecte les bugs évidents dans le Luau généré par le LLM avant publication. |
| [StyLua](https://github.com/JohnnyMorganz/StyLua) | Formatteur Luau | Code généré cohérent, review humaine plus facile. |
| [Roblox Open Cloud API](https://create.roblox.com/docs/cloud) | API officielle (places, DataStores, assets, messaging) | Seul canal d'automatisation autorisé par les ToS Roblox — utilisé par `roblox_cloud.py`. |
| [roblox-open-cloud (Python)](https://github.com/rblx-open-cloud) / SDK officiel Node | Clients Open Cloud | Alternative aux appels HTTP bruts si on veut un SDK typé. |
| [Roblox Studio MCP Server](https://github.com/Roblox/studio-rust-mcp-server) | Serveur MCP **officiel Roblox** exposant Studio à des agents IA (insertion d'objets, exécution de commandes, lecture de la hiérarchie) | Le complément direct de Problox : Problox génère/publie via Open Cloud, le MCP Studio permet en plus un contrôle interactif de l'éditeur si l'agent tourne à côté d'une session Studio ouverte. Recommandé pour la phase d'itération manuelle. |
| [RoStruct](https://github.com/ekrctb/rostruct) | Exécution de scripts Lua "hors ligne" dans un faux environnement Roblox pour tests | Utile pour des tests unitaires légers sans lancer Studio. |
| [Roblox-ts](https://roblox-ts.com/) | Compile TypeScript -> Luau | Alternative si on préfère générer du TS typé plutôt que du Luau brut (non utilisé par défaut, mais compatible avec le pipeline Rojo). |

## Explicitement exclus (et pourquoi)

- **Bots d'automatisation par cookie `.ROBLOSECURITY`** (ex: certains forks de
  `noblox.js` utilisés pour "jouer" un compte) : viole les ToS Roblox
  (automatisation d'un compte utilisateur hors API officielle), risque de ban
  définitif. Problox ne les installe pas.
- **"Agents IA Roblox" packagés non maintenus / sans licence claire trouvés
  sur GitHub** : trop de faux projets réutilisent le nom "Roblox AI agent"
  pour distribuer du code non audité. Preferer les briques ci-dessus
  (officielles ou largement adoptées, >1k stars, licence MIT/Apache) et
  composer soi-même l'orchestration (c'est le rôle de `orchestrator.py`).

## Installation

Voir `scripts/setup_sandbox.sh` — installe Aftman puis laisse `aftman.toml`
piloter les versions de Rojo/Selene/StyLua, installe Wally séparément, et
`pip install -e .` pour Problox lui-même.
