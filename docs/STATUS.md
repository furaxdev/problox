# État du déploiement ProbloxDev

Snapshot maintenu à la main après chaque changement d'infra — plus fiable
qu'une recherche à chaque session. Dernière mise à jour : nuit du 21/09.

## Live

| | |
|---|---|
| Site (Vercel) | https://probloxdev.vercel.app |
| API (Render)  | https://probloxdev-api-h8pi.onrender.com |
| Repo | `furaxdev/problox`, branche `claude/problox-roblox-agent-ipenpi` |
| Workspace Render | **Plasma** (`tea-daomvrmgekts73at5up0`) |
| Team Vercel | **FuraxDev** (`team_1frYzsGbqEgzIcTqxeu7nM1q`) |
| Service Render | `probloxdev-api` (`srv-daon0n3bc2fs7383o4eg`) |
| Projet Vercel | `probloxdev` (`prj_sArMHzUAahAOUkfwu2700fSacIrp`) |

`GET /api/health` et `GET /api/status` répondent 200. Toolchain complète
détectée (`rojo`, `selene`, `stylua`, `aftman`, `wally` tous `true`). Un run
complet de bout en bout a été testé en production : design → génération
Luau → `rojo build` → `place.rbxlx` téléchargeable, sans erreur.

## Configuré

- Auto-deploy Render + Vercel sur push de la branche `claude/problox-roblox-agent-ipenpi`.
- CORS backend limité à `https://probloxdev.vercel.app`.
- Cookies de session `SameSite=None; Secure` (nécessaire cross-domaine Vercel↔Render).
- Protection SSO Vercel désactivée sur le projet (sinon le site serait
  inaccessible à qui n'est pas membre de l'équipe FuraxDev — contraire à
  l'objectif "outil global").

## PAS configuré (action humaine requise)

- **`ROBLOX_OAUTH_CLIENT_ID` / `ROBLOX_OAUTH_CLIENT_SECRET`** sur Render.
  Sans ça, `oauth_configured: false` dans `/api/status`, le bouton
  "Connecter Roblox" échoue avec un 503 propre. Procédure exacte :
  `docs/OAUTH_SETUP.md`. Redirect URI à déclarer côté Roblox :
  `https://probloxdev-api-h8pi.onrender.com/api/auth/roblox/callback`.
- **`ANTHROPIC_API_KEY`** sur Render. Sans ça, `game_designer.py` retombe
  sur le design "starter kit" statique (fonctionnel mais toujours le même
  thème générique) plutôt que de générer un vrai design via Claude.

Comment les poser : dashboard Render → service `probloxdev-api` →
Environment, ou `render env set <KEY> <VALUE> --service probloxdev-api`
une fois `render login` fait sur ta machine.

## Bugs réels trouvés et corrigés cette nuit

Tous invisibles avant parce que la toolchain complète (rojo etc.) n'avait
jamais tourné jusqu'ici en conditions réelles :

1. `aftman install` bloquait sur une confirmation interactive impossible en
   CI (`--no-trust-check`).
2. `$HOME` non persisté entre build et runtime sur Render → toolchain
   déplacée dans le repo checkout via `AFTMAN_ROOT`.
3. `GameDesign.luau` généré avec du JSON brut (`"clé": valeur`), invalide en
   Luau (`clé = valeur`) → vrai sérialiseur `_to_luau_literal`.
4. Chemin de sortie `rojo build` doublé avec un `out_dir` relatif (le cas
   réel en session web, jamais testé en local avec un chemin absolu).

Chacun a un test de régression dans `tests/`.

## Prochaines pistes (pas commencées)

Voir la todo dans le README / les commits à venir cette nuit pour ce qui a
effectivement été fait au-delà de ce point.
