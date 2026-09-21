# ProbloxDev

Un agent IA autonome qui tourne dans un sandbox Debian, pilote un compte Roblox
via l'**Open Cloud API**, et fabrique une expérience Roblox complète (place +
scripts Luau + boucle de progression/monétisation) en autonomie : conception du
game design, génération du code, synchronisation vers Roblox Studio (via Rojo),
et publication. Deux façons de le piloter :

- **CLI locale** (`problox run`) avec une clé Open Cloud API perso dans `.env`.
- **Site ProbloxDev** (`web/` sur Vercel + backend sur Render) : n'importe
  qui peut se connecter avec **son propre compte Roblox via OAuth** — pas de
  clé API à partager, l'outil est utilisable par tout le monde sans que
  chaque visiteur doive créer/gérer des credentials Open Cloud lui-même.

> ⚠️ ProbloxDev ne peut **pas** deviner tes identifiants. Il lui faut soit une
> clé Open Cloud API + `UNIVERSE_ID`/`PLACE_ID` (mode CLI), soit une
> connexion OAuth Roblox (mode site — voir `docs/OAUTH_SETUP.md`), que **toi
> seul** peux créer depuis le Creator Dashboard Roblox. Sans ça, l'agent
> tourne en mode "dry-run" : il génère tout le jeu sur disque mais ne publie
> rien.

## Architecture

```
problox/
  config.py          # lit les credentials/env vars, aucune clé en dur
  game_designer.py    # LLM (Claude) -> game design doc orienté "boucle addictive"
  luau_generator.py   # design doc -> arborescence de scripts Luau (Rojo)
  rojo_project.py      # construit un projet Rojo (default.project.json) + build .rbxlx
  roblox_cloud.py       # client Open Cloud API (x-api-key OU Bearer OAuth)
  roblox_oauth.py        # flow OAuth 2.0 + PKCE contre Roblox (mode multi-utilisateurs)
  state.py                 # mémoire persistante de l'agent entre les runs (JSON)
  orchestrator.py           # boucle autonome: design -> code -> sync -> publish -> itère
  cli.py                     # `problox run`, `problox web`, `problox check`
  web.py                      # backend FastAPI (sessions, OAuth, run, logs, design, build)
  webapp/index.html            # dashboard local minimal (mode CLI/local uniquement)
web/                              # frontend Next.js déployé sur Vercel (le "site ProbloxDev")
templates/luau/                    # briques de gameplay réutilisables (voir plus bas)
docker/Dockerfile                   # sandbox Debian avec Rojo, Aftman, Wally, Selene, StyLua, Python
scripts/setup_sandbox.sh              # installe la toolchain Roblox
scripts/install_render_cli.sh          # installe le CLI Render (déploiement backend)
render.yaml                              # blueprint Render pour le backend
docs/TOOLS.md                              # comparatif des meilleurs outils open source Roblox
docs/ARCHITECTURE.md                        # détail de la boucle de l'agent
docs/OAUTH_SETUP.md                          # créer l'app OAuth Roblox (étape humaine, une fois)
docs/DEPLOY.md                                # déployer web/ sur Vercel + backend sur Render
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

## Le site ProbloxDev (public, multi-utilisateurs)

`web/` est un site Next.js pensé pour être déployé sur **Vercel** et parler à
un backend FastAPI déployé sur **Render** (`problox/web.py`). N'importe quel
visiteur clique "Connecter mon compte Roblox", passe par l'écran de
consentement **OAuth officiel Roblox** (il choisit lui-même quelles
expériences autoriser), puis pilote l'agent sur son propre compte — jamais
via une clé API partagée. Voir `docs/OAUTH_SETUP.md` (config une fois, côté
opérateur) et `docs/DEPLOY.md` (déploiement Vercel + Render).

En local pour développer :

```bash
# backend
pip install -e .
problox web            # http://127.0.0.1:8787

# frontend (autre terminal)
cd web
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://127.0.0.1:8787
npm install
npm run dev             # http://localhost:3000
```

Sans OAuth configuré (`ROBLOX_OAUTH_CLIENT_ID`/`SECRET`), le bouton
"Connecter Roblox" renvoie une erreur claire plutôt qu'un plantage, et
l'agent continue de fonctionner en dry-run.

Il existe aussi `problox/webapp/index.html`, un dashboard local minimaliste
(vanilla JS, pas de build step) pour piloter la CLI mode `.env` sans passer
par Next.js/Vercel — pratique pour un usage strictement local/solo.

## Sécurité & ToS

- Aucune automatisation de compte via cookies/`.ROBLOSECURITY` : ça viole les
  conditions d'utilisation de Roblox et expose un compte à un ban. Problox
  n'utilise que l'**Open Cloud API officielle**, via clé API (mode CLI) ou
  **OAuth 2.0** (mode site — accès limité aux ressources que chaque
  utilisateur choisit explicitement d'autoriser).
- Les outils tiers listés dans `docs/TOOLS.md` sont installés via leurs
  gestionnaires de paquets officiels (Aftman, Wally, pip, npm) — jamais de
  scripts arbitraires téléchargés et exécutés en aveugle.
- Le store de sessions web est en mémoire (process unique) — voir
  l'avertissement en tête de `problox/web.py` avant un vrai déploiement multi-instance.

Voir `docs/ARCHITECTURE.md` pour le détail de la boucle autonome,
`docs/TOOLS.md` pour le comparatif d'outils open source, et
`docs/DEPLOY.md`/`docs/OAUTH_SETUP.md` pour la mise en prod.
