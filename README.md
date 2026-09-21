# ProbloxDev

Un agent IA autonome qui tourne dans un sandbox Debian, pilote un compte Roblox
via l'**Open Cloud API**, et fabrique une expérience Roblox complète (place +
scripts Luau + boucle de progression/monétisation) en autonomie : conception du
game design, génération du code, synchronisation vers Roblox Studio (via Rojo),
et publication. Piloté soit en CLI, soit depuis le **site ProbloxDev**
(dashboard local, voir plus bas).

> ⚠️ ProbloxDev ne peut **pas** deviner tes identifiants. Il lui faut une clé
> Open Cloud API et un `UNIVERSE_ID`/`PLACE_ID` que **toi seul** peux créer
> depuis le Creator Dashboard Roblox (voir "Mise en route" ci-dessous). Sans
> ça, l'agent tourne en mode "dry-run" : il génère tout le jeu sur disque mais
> ne publie rien.

## Architecture

```
problox/
  config.py          # lit les credentials/env vars, aucune clé en dur
  game_designer.py    # LLM (Claude) -> game design doc orienté "boucle addictive"
  luau_generator.py   # design doc -> arborescence de scripts Luau (Rojo)
  rojo_project.py      # construit un projet Rojo (default.project.json) + build .rbxlx
  roblox_cloud.py       # client Open Cloud API (publish place, manage universe, DataStores)
  state.py               # mémoire persistante de l'agent entre les runs (JSON)
  orchestrator.py         # boucle autonome: design -> code -> sync -> publish -> itère
  cli.py                   # `problox run`, `problox web`, `problox check`
  web.py                    # API FastAPI du site ProbloxDev (statut, run, logs, design, build)
  webapp/index.html          # UI du site (une page, vanilla JS, pas de build step)
templates/luau/            # briques de gameplay réutilisables (voir plus bas)
docker/Dockerfile           # sandbox Debian avec Rojo, Aftman, Wally, Selene, StyLua, Python
scripts/setup_sandbox.sh     # installe la toolchain Roblox dans le sandbox
docs/TOOLS.md                  # comparatif des meilleurs outils open source Roblox
docs/ARCHITECTURE.md            # détail de la boucle de l'agent
```

## Boucle "hyper addictive" générée par défaut

Le `game_designer` compose systématiquement ces mécaniques, qui sont les
piliers validés des jeux Roblox à forte rétention (obby/tycoon/simulateur
hybride) :

- **Boucle de progression courte** (30-90s) : action -> récompense -> feedback visuel/sonore
- **Monnaie virtuelle + Gamepasses** (boutique in-game via MonetizationService)
- **Récompenses quotidiennes** (DailyReward, relance J+1)
- **Leaderboard global** (OrderedDataStore, compétition sociale)
- **Checkpoints persistants** (DataStoreService, pas de perte de progression)
- **Événements limités dans le temps** (relance via FOMO, config déclarative)

Ce sont des templates de départ, pas une garantie de succès — l'agent les
assemble et les adapte au thème choisi, mais le tuning (difficulté, économie,
UGC) reste itératif une fois le jeu en ligne.

## Mise en route

1. **Créer les credentials Roblox** (humain, obligatoire) :
   - Crée une expérience vide sur https://create.roblox.com pour obtenir un `UNIVERSE_ID` et un `PLACE_ID`.
   - Génère une clé Open Cloud API sur https://create.roblox.com/dashboard/credentials avec les scopes `universe-places:write`, `universe-places:read`, `universe.place.luau-execution-session:write` (si tu veux l'exécution de scripts à distance), `assets:write`.
2. Copie `.env.example` vers `.env` et renseigne :
   ```
   ROBLOX_API_KEY=...
   ROBLOX_UNIVERSE_ID=...
   ROBLOX_PLACE_ID=...
   ANTHROPIC_API_KEY=...   # pour la génération du design + du code
   ```
3. Construis/lance le sandbox :
   ```bash
   docker build -t problox -f docker/Dockerfile .
   docker run --env-file .env -v $(pwd):/workspace -it problox
   ```
4. Dans le sandbox :
   ```bash
   ./scripts/setup_sandbox.sh   # installe Rojo/Aftman/Wally/Selene/StyLua
   pip install -e .
   problox run --theme "obby simulateur de course" --autonomous
   ```

Sans `.env` rempli, `problox run` génère quand même tout le projet Rojo dans
`build/` (place buildable en local dans Studio) mais saute l'étape de
publication Open Cloud et te dit exactement quoi faire pour publier
toi-même.

## Le site ProbloxDev

Un dashboard local pour piloter l'agent sans taper de commandes : thème du
jeu, mode autonome, logs en direct, dernier design généré (JSON), et
téléchargement du `.rbxlx` buildé.

```bash
pip install -e .
problox web            # http://127.0.0.1:8787
```

C'est un serveur local (FastAPI + une page HTML/JS sans build step) qui
tourne dans ton sandbox et pilote le même `orchestrator.py` que la CLI — pas
de service tiers, pas d'exposition publique par défaut (`--host` si tu veux
l'ouvrir sur le réseau, à tes risques).

## Sécurité & ToS

- Aucune automatisation de compte via cookies/`.ROBLOSECURITY` : ça viole les
  conditions d'utilisation de Roblox et expose ton compte à un ban. Problox
  n'utilise que l'**Open Cloud API officielle**, authentifiée par clé API.
- Les outils tiers listés dans `docs/TOOLS.md` sont installés via leurs
  gestionnaires de paquets officiels (Aftman, Wally, pip, npm) — jamais de
  scripts arbitraires téléchargés et exécutés en aveugle.

Voir `docs/ARCHITECTURE.md` pour le détail de la boucle autonome et
`docs/TOOLS.md` pour le comparatif d'outils open source.
