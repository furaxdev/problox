# Configurer l'app OAuth Roblox de ProbloxDev

Cette étape est humaine et se fait **une seule fois**, par l'opérateur du
service (toi). Elle donne à ProbloxDev un `CLIENT_ID`/`CLIENT_SECRET` propres
au produit ; chaque visiteur du site connectera ensuite *son propre* compte
via ces credentials, sans jamais te confier de mot de passe ou de clé API
personnelle.

## 1. Créer l'app

1. Va sur **https://create.roblox.com/dashboard/credentials**, onglet
   "OAuth Apps" (ou "API Access" selon la version de l'UI — Roblox renomme
   parfois ses sections, cherche "OAuth").
2. Crée une nouvelle app :
   - **Nom** : `ProbloxDev` (ou ce que tu veux, visible sur l'écran de
     consentement montré aux utilisateurs).
   - **Redirect URI** : l'URL de callback de ton backend Render, ex.
     `https://probloxdev-api.onrender.com/api/auth/roblox/callback`
     (doit correspondre exactement à `ROBLOX_OAUTH_REDIRECT_URI`).
   - **Scopes** à activer pour l'app : `openid`, `profile`, et les scopes
     Open Cloud `universe-places:read` + `universe-places:write` (ce sont
     ceux que `problox/roblox_oauth.py` demande par défaut — modifie
     `DEFAULT_SCOPES` si tu veux en retirer/ajouter).
3. Roblox te donne un **Client ID** et un **Client Secret**. Le secret n'est
   affiché qu'une fois — copie-le immédiatement.

## 2. Configurer le backend

Sur Render (dashboard ou `render env set` via le CLI), renseigne :

```
ROBLOX_OAUTH_CLIENT_ID=<client id>
ROBLOX_OAUTH_CLIENT_SECRET=<client secret>
ROBLOX_OAUTH_REDIRECT_URI=https://probloxdev-api.onrender.com/api/auth/roblox/callback
SESSION_SECRET=<chaîne aléatoire longue — render.yaml en génère une automatiquement>
FRONTEND_URL=https://probloxdev.vercel.app
ALLOWED_ORIGINS=https://probloxdev.vercel.app
ANTHROPIC_API_KEY=<optionnel, sinon design "starter kit">
```

## 3. Ce que voit un visiteur du site

1. Il clique "Connecter mon compte Roblox" sur le site ProbloxDev.
2. Roblox affiche un écran de consentement **standard Roblox** listant les
   expériences de son compte ; il choisit lui-même lesquelles autoriser
   ProbloxDev à gérer (il peut n'en choisir aucune, ou une seule — jamais
   "tout le compte").
3. Roblox redirige vers ProbloxDev avec un code d'autorisation ;
   `roblox_callback` (`problox/web.py`) l'échange contre un access/refresh
   token **scopé aux ressources choisies**, stocké côté serveur dans la
   session du visiteur (jamais exposé au navigateur).
4. ProbloxDev peut désormais publier des places uniquement sur les
   expériences que ce visiteur a explicitement autorisées.

## ⚠️ Risque connu : la publication pourrait ne pas marcher via OAuth

Vérifié contre la doc officielle (`create.roblox.com/docs/cloud/reference/Place`
et `oauth2-reference`) : l'endpoint qui publie réellement le **contenu** d'une
place — `POST /universes/v1/{universeId}/places/{placeId}/versions`, utilisé
par `roblox_cloud.publish_place()` — n'est documenté qu'avec l'authentification
**API Key**, pas OAuth 2.0. Seuls des endpoints `GET`/`PATCH
/cloud/v2/.../places/{id}` (métadonnées de la place, pas son contenu) supportent
explicitement OAuth d'après le tableau de la doc.

Concrètement : la connexion OAuth (identité, choix de l'expérience, listage des
places via `GET /cloud/v2/universes/{id}/places` qui supporte OAuth) devrait
fonctionner, mais l'étape finale de **publication** avec le token OAuth de
l'utilisateur risque de renvoyer 401/403. Pas encore confirmé en conditions
réelles (nécessite un vrai Client ID/Secret + un run complet pour vérifier)
— à tester en priorité dès que l'app OAuth existe. Le filet de sécurité déjà
en place (téléchargement du `.rbxlx` pour publier à la main dans Roblox
Studio, cf. `GET /api/build/place.rbxlx`) reste utilisable dans tous les cas
si la publication OAuth échoue.

Pistes si ça échoue réellement :
- Vérifier si Roblox a depuis ajouté le support OAuth à cet endpoint (la doc
  traîne parfois derrière l'implémentation réelle) — retester directement.
- Sinon, il faudra soit demander à l'utilisateur connecté de fournir *aussi*
  une clé API personnelle pour la seule étape de publication (dégrade
  l'expérience "juste OAuth" mais reste fonctionnel), soit se limiter à
  OAuth pour l'identité/le choix d'expérience et au téléchargement manuel
  pour la publication.

## Autres vérifications à faire toi-même

Les noms exacts d'endpoints/scopes OAuth Roblox (`problox/roblox_oauth.py`)
sont documentés d'après https://create.roblox.com/docs/cloud/auth/oauth2-reference
au moment de l'écriture de ce code — Roblox modifie parfois ces surfaces. Un
point précis déjà repéré : la doc du discovery document liste les scopes
`openid`, `profile`, `email`, `verification`, `credentials`, `age`, `premium`,
`roles` mais ne confirme *pas* explicitement `universe-places:read`/`write`
comme scopes OAuth valides (contrairement aux clés API classiques où ces
scopes existent). Avant un déploiement en prod, fais un aller-retour complet
(login -> consentement -> callback -> `GET /api/me`) et compare les réponses
JSON réelles à ce qu'attend `roblox_oauth.py` (`fetch_userinfo`,
`fetch_granted_resources`) ; ajuste si Roblox rejette le scope ou change la
forme de la réponse.
