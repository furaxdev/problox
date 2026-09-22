# Bot Discord Hermès

Assistant IA conversationnel sur Discord, branché sur DeepSeek (function
calling) avec des outils : recherche web, exécution de code Python
sandboxée, sous-agents, et génération de jeux Roblox via le pipeline
ProbloxDev (`game_designer` + `luau_generator` + `rojo_project`, jusqu'au
`.rbxlx` — **sans publication**, le bot n'a pas de credentials Roblox par
utilisateur).

## Ce que c'est / n'est pas

- Sandbox de code = isolation par subprocess + rlimits (CPU/mémoire/temps),
  **pas** une isolation kernel type Docker/Firecracker. Suffisant contre un
  script maladroit, pas contre un utilisateur malveillant déterminé à sortir
  du bac à sable. D'où les outils sensibles réservés aux admins.
- `problox_build_game` génère le jeu jusqu'au build local, ne publie rien
  sur Roblox.
- `spawn_subagent` a une profondeur limitée (1 par défaut,
  `HERMES_MAX_SUBAGENT_DEPTH`) pour éviter une récursion incontrôlée qui
  ferait exploser les coûts API.

## 1. Créer le bot Discord

1. https://discord.com/developers/applications -> **New Application**.
2. Onglet **Bot** -> **Reset Token**, copie le token (c'est `DISCORD_BOT_TOKEN`,
   ne le commit jamais).
3. Toujours sur l'onglet Bot : active **Message Content Intent** (obligatoire,
   sinon le bot ne reçoit pas le texte des messages).
4. Onglet **OAuth2 > URL Generator** : coche `bot`, permissions minimales
   (`Send Messages`, `Read Message History`), ouvre l'URL générée pour
   inviter le bot sur ton serveur.
5. Active le **mode développeur** Discord (Réglages > Avancés) pour pouvoir
   clic-droit sur ton propre compte -> **Copier l'ID** : c'est ton
   `HERMES_ADMIN_USER_IDS` (liste séparée par des virgules si plusieurs
   admins). **Sans ça, personne ne peut utiliser les outils sensibles.**

## 2. Clé DeepSeek

https://platform.deepseek.com -> API keys -> nouvelle clé (`DEEPSEEK_API_KEY`).
API compatible OpenAI, modèle par défaut `deepseek-chat`
(`DEEPSEEK_MODEL` pour changer, ex: `deepseek-reasoner`).

## 3. Variables d'environnement

```
DISCORD_BOT_TOKEN=...
DEEPSEEK_API_KEY=...
DEEPSEEK_MODEL=deepseek-chat          # optionnel
HERMES_ADMIN_USER_IDS=123456789012345 # obligatoire pour débloquer les outils sensibles
HERMES_ALLOWED_GUILD_IDS=             # optionnel: vide = tous les serveurs où le bot est invité
HERMES_COMMAND_PREFIX=!hermes         # optionnel, sinon @mention le bot
```

## 4. Lancer en local

```bash
pip install -e ".[hermes]"
export DISCORD_BOT_TOKEN=...
export DEEPSEEK_API_KEY=...
export HERMES_ADMIN_USER_IDS=ton_id_discord
problox hermes
```

Dans Discord : `@Hermès crée-moi un jeu obby lave parkour` (admin) ou
`!hermes salut` (tout le monde, sans les outils sensibles).

## 5. Déployer

`render.yaml` contient un service `probloxdev-hermes-bot` (type `worker` —
pas de plan gratuit Render pour ça, un bot Discord garde une connexion
websocket ouverte en permanence). Renseigne les secrets dans le dashboard
Render après le déploiement du blueprint (jamais dans `render.yaml`).

Alternative moins chère si tu ne veux pas payer Render pour ça : n'importe
quelle petite VM/conteneur capable de tourner un process Python en continu
(un Raspberry Pi chez toi marche très bien pour un bot perso).

## Sécurité

- N'ouvre **jamais** `execute_code` à des non-admins sur un serveur public —
  même avec les rlimits, un utilisateur déterminé peut chercher une évasion
  de sandbox. Si tu veux un jour l'ouvrir plus largement, fais tourner tout
  le process du bot dans un conteneur/VM jetable, isolé du reste de
  l'infra ProbloxDev (pas le même host que le backend web).
- `HERMES_ALLOWED_GUILD_IDS` vide = le bot répond sur n'importe quel serveur
  où il est invité (mais reste fermé aux outils sensibles hors admins).
- Aucun secret n'est loggé ; les erreurs DeepSeek/outils sont renvoyées
  telles quelles dans Discord — évite de mettre des infos sensibles dans un
  prompt si le salon n'est pas privé.
