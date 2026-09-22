# IA open source pour le dev Roblox, la modélisation 3D et le GUI

Recherché et vérifié (licence, dépôt réel, besoins matériels) début
d'automne 2026 sur demande de Furax. Important en préambule : **aucun de
ces modèles n'est installé dans le backend ProbloxDev**. Le backend tourne
sur Render (pas de GPU, disque limité) — les modèles 3D listés ci-dessous
ont besoin de 16 Go+ de VRAM et pèsent plusieurs Go, donc les "télécharger"
dans ce sandbox n'aurait servi à rien (rien ici ne peut les faire tourner).
Ce doc explique quoi installer, où (ta machine avec GPU, ou un service
géré), et pourquoi je ne les ai pas branchés directement à l'agent.

## 1. Assistance au scripting Luau/Roblox (à côté de Studio)

ProbloxDev génère du code Luau de façon autonome et headless (sans Studio
ouvert). Les outils ci-dessous sont complémentaires : ils t'aident *toi*,
en direct dans Roblox Studio, pas l'agent.

| Outil | Licence | Ce que ça fait |
|---|---|---|
| [ZeroScript](https://github.com/sebattfg/ZeroScript-Free) | **GPL-3.0**, vraiment open source | Extension navigateur + pont local qui connecte un chat IA gratuit (ChatGPT web, DeepSeek, Gemini, Qwen...) à Roblox Studio. L'IA lit/édite tes scripts, exécute du Luau, génère des assets, directement dans Studio. Pas de clé API requise (utilise les sessions de chat web gratuites). |
| RoCode | Non vérifiable (bêta fermée sur le forum Roblox) | Mentionné comme "assistant IA construit spécifiquement pour Luau/Roblox" — pas de dépôt public trouvé au moment de la recherche, donc pas recommandable tel quel (voir `docs/TOOLS.md`, principe: pas d'installation à l'aveugle sans licence claire). |

**Installation** (si tu veux l'essayer, sur ta machine, pas sur le
serveur) : suit le README de `sebattfg/ZeroScript-Free` — extension
navigateur + petit pont local (Node), aucun GPU requis.

## 2. Génération de modèles 3D (texte -> mesh)

| Modèle | Licence | VRAM | Verdict |
|---|---|---|---|
| [Roblox/cube (Cube 3D)](https://github.com/Roblox/cube) | **Cube3D Research-Only RAIL-MS** — usage recherche/académique uniquement, **interdit en usage commercial ou service hébergé** | 16 Go mini, 24 Go recommandés (L40S/H100/A100, ou Apple Silicon M2-M4) | Le mieux entraîné pour du contenu Roblox (1,5M d'assets Roblox), mais **sa licence interdit explicitement de l'intégrer à un service comme ProbloxDev**. Utilisable seulement pour de l'expérimentation perso/recherche, sur ta propre machine. |
| [microsoft/TRELLIS.2](https://github.com/microsoft/TRELLIS.2) | **MIT**, vraiment permissive | GPU NVIDIA requis (non précisé exactement, TRELLIS original tournait sur ~16 Go) | Le meilleur choix si tu veux un jour brancher de la génération 3D *dans* ProbloxDev sans souci de licence — mais il faudrait un serveur avec GPU (pas Render free tier). |
| Hunyuan3D 2.1 (Tencent) | Licence "communautaire" Tencent, pas MIT/Apache — **à relire toi-même avant tout usage commercial** | GPU requis | Qualité comparable à TRELLIS, mais licence moins claire pour un usage produit — je ne l'ai pas assez vérifié pour le recommander sans réserve. |

**Verdict pratique pour ProbloxDev** : rien de tout ça n'est branchable
maintenant (pas de GPU côté Render). Si tu veux vraiment de la génération
3D dans l'agent un jour, deux options réalistes :
1. Héberger TRELLIS.2 (MIT) toi-même sur une machine avec GPU (louée ou
   perso), exposer une petite API HTTP, et faire appel à cette API depuis
   `luau_generator.py` — gros chantier, pas fait cette nuit.
2. Utiliser un service géré payant (Meshy, etc.) via API — plus simple mais
   pas "open source auto-hébergé" comme demandé.

## 3. Génération de GUI (interface)

| Outil | Licence | Ce que ça fait |
|---|---|---|
| [wandb/openui](https://github.com/wandb/openui) | **Apache-2.0** | Décrit une UI en langage naturel, génère du HTML/CSS/JS, rendu live. Tourne avec Ollama (local, gratuit) ou une clé API (OpenAI/Anthropic/etc). |
| [Penpot](https://penpot.app/) | **MPL-2.0**, auto-hébergeable | Pas un générateur IA en soi, mais une plateforme de design collaborative open source avec des hooks pour brancher des agents IA (design-to-code, code-to-design). Utile pour maquetter humainement les interfaces Roblox avant de les coder. |

**Limite honnête** : ces deux outils génèrent du **HTML/CSS**, pas des
`ScreenGui`/`Frame`/`TextButton` Luau natifs. Je n'ai trouvé **aucun outil
open source mature qui génère directement du GUI Roblox natif** à partir
d'un prompt. La voie la plus fiable reste ce qu'on fait déjà dans
`luau_generator.py` : des templates Luau écrits à la main, pas une IA
générique détournée de son usage web.

## Pourquoi rien n'a été installé ce soir

- Les modèles 3D ont besoin d'un GPU que ce sandbox n'a pas — les
  télécharger ici (plusieurs Go) n'aurait servi à rien.
- Cube 3D (le mieux adapté à Roblox) a une licence qui **interdit** de
  l'intégrer à un service hébergé comme ProbloxDev — l'installer quand
  même pour ce projet aurait été une violation de licence délibérée.
- ZeroScript est un outil pour *toi*, dans Studio, en humain — pas quelque
  chose à embarquer dans le backend headless de ProbloxDev.

Rien de bloquant : ce doc reste comme référence si tu veux un jour explorer
ces pistes toi-même, sur ta propre machine.
