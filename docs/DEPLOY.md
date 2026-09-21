# Déployer ProbloxDev (Vercel + Render)

Deux déploiements séparés : le **site** (Next.js, statique + petites routes
client) sur Vercel, l'**agent** (FastAPI, process long-running, build Rojo,
appels Claude/Roblox) sur Render.

## Pourquoi pas tout sur Vercel

Les fonctions serverless Vercel sont conçues pour des réponses courtes et ne
gardent pas de process/binaire (`rojo`) installé entre deux invocations.
L'orchestrateur ProbloxDev lance `rojo build` en sous-process, tourne
potentiellement plusieurs dizaines de secondes/minutes en mode autonome, et
doit garder un état de session en mémoire pour le suivi des logs — un
service Render classique (process persistant) convient, une fonction Vercel
non.

## 1. Backend sur Render

Prérequis : avoir suivi `docs/OAUTH_SETUP.md` (Client ID/Secret Roblox).

### Option A — CLI

```bash
./scripts/install_render_cli.sh   # installe le binaire `render`
render login
render blueprint launch           # lit render.yaml à la racine du repo
```

Le CLI va demander les valeurs des variables marquées `sync: false` dans
`render.yaml` (`ANTHROPIC_API_KEY`, `ROBLOX_OAUTH_CLIENT_ID`,
`ROBLOX_OAUTH_CLIENT_SECRET`).

### Option B — Dashboard

"New +" → "Blueprint" → connecte le repo GitHub `furaxdev/problox` → Render
détecte `render.yaml` → renseigne les secrets demandés → Deploy.

### Vérifier après déploiement

```bash
curl https://probloxdev-api.onrender.com/api/health
# {"ok": true}
```

Si `rojo`/`aftman` ne sont pas trouvés au runtime (`problox check` ou
`/api/status` montre les tools à `false`), c'est que le `PATH` du process de
démarrage ne pointe pas vers où `scripts/setup_sandbox.sh` a installé
Aftman pendant le build — inspecte avec `render ssh <service>` où Aftman a
atterri (`$HOME/.aftman/bin`) et ajuste la variable d'env `PATH` dans
`render.yaml` en conséquence (je n'ai pas pu valider ce chemin exact sans
compte Render réel — c'est la seule partie de ce déploiement non testée
en conditions réelles).

## 2. Frontend sur Vercel

Le frontend Next.js vit dans `web/` (mono-repo).

### Option A — Dashboard Vercel

1. "Add New" → "Project" → importe `furaxdev/problox`.
2. **Root Directory** : `web` (important — sinon Vercel cherche un
   `package.json` à la racine du repo et ne le trouve pas).
3. Framework détecté automatiquement : Next.js.
4. Variable d'env : `NEXT_PUBLIC_API_URL=https://probloxdev-api.onrender.com`
5. Deploy.

### Option B — CLI Vercel

```bash
npm i -g vercel   # ou npx vercel, pas besoin d'install globale
cd web
vercel link
vercel env add NEXT_PUBLIC_API_URL production
vercel --prod
```

## 3. Boucler la config cross-domaine

Une fois les deux URLs connues (ex. `https://probloxdev.vercel.app` et
`https://probloxdev-api.onrender.com`), remets à jour sur Render :

```
FRONTEND_URL=https://probloxdev.vercel.app
ALLOWED_ORIGINS=https://probloxdev.vercel.app
ROBLOX_OAUTH_REDIRECT_URI=https://probloxdev-api.onrender.com/api/auth/roblox/callback
```

Et sur Roblox (Creator Dashboard → ton app OAuth) : mets exactement la même
Redirect URI.

Le cookie de session est `SameSite=None; Secure`, ce qui est nécessaire pour
que le navigateur l'envoie sur des requêtes cross-site Vercel → Render — ça
exige que le backend soit servi en HTTPS (Render le fait par défaut).

## 4. Test de bout en bout

1. Ouvre le site Vercel, clique "Connecter mon compte Roblox".
2. Autorise une expérience de test sur l'écran de consentement Roblox.
3. Tu dois revenir sur `/dashboard?connected=1` avec ton pseudo affiché.
4. Lance un run avec un thème — les logs doivent défiler en direct, puis
   `place.rbxlx` doit être publié sur la place choisie (vérifiable dans
   l'historique des versions sur create.roblox.com).
