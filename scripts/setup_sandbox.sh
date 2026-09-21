#!/usr/bin/env bash
# Installe la toolchain de dev Roblox dans le sandbox Debian, via les
# gestionnaires de paquets officiels des outils (pas de curl|bash aveugle
# vers des sources non versionnées).
set -euo pipefail

echo "== Problox sandbox setup =="

# Sur Render (et toute plateforme "build puis déploie une image à part"),
# $HOME peut ne pas être persisté entre le build et le runtime — seul le
# checkout du repo (le cwd ici) l'est de façon fiable. On installe donc
# Aftman et ses outils dans un dossier du projet plutôt que $HOME, via la
# variable AFTMAN_ROOT qu'Aftman respecte nativement. En local (CLI/Docker),
# $HOME fonctionne très bien et reste la valeur par défaut.
export AFTMAN_ROOT="${AFTMAN_ROOT:-$HOME/.aftman}"

if ! command -v aftman >/dev/null 2>&1 && [ ! -x "$AFTMAN_ROOT/bin/aftman" ]; then
  echo "-- Installation d'Aftman (gestionnaire de version d'outils Roblox) --"
  ARCH="$(uname -m)"
  case "$ARCH" in
    x86_64) AFTMAN_ARCH="linux-x86_64" ;;
    aarch64) AFTMAN_ARCH="linux-aarch64" ;;
    *) echo "Architecture non supportée par Aftman: $ARCH" >&2; exit 1 ;;
  esac
  TMP_DIR="$(mktemp -d)"
  LATEST_URL=$(curl -fsSL https://api.github.com/repos/LPGhatguy/aftman/releases/latest \
    | grep browser_download_url | grep "$AFTMAN_ARCH" | grep '.zip"' | head -n1 | cut -d '"' -f4)
  curl -fsSL "$LATEST_URL" -o "$TMP_DIR/aftman.zip"
  unzip -q "$TMP_DIR/aftman.zip" -d "$TMP_DIR"
  mkdir -p "$AFTMAN_ROOT/bin"
  mv "$TMP_DIR/aftman" "$AFTMAN_ROOT/bin/aftman"
  chmod +x "$AFTMAN_ROOT/bin/aftman"
  rm -rf "$TMP_DIR"
fi

export PATH="$AFTMAN_ROOT/bin:$PATH"

if [ ! -f aftman.toml ]; then
  cat > aftman.toml <<'EOF'
[tools]
rojo = "rojo-rbx/rojo@7.4.4"
selene = "Kampfkarren/selene@0.27.1"
stylua = "JohnnyMorganz/StyLua@0.20.0"
wally = "UpliftGames/wally@0.3.2"
EOF
  echo "aftman.toml créé."
fi

echo "-- Installation des outils déclarés dans aftman.toml --"
# --no-trust-check: nécessaire en environnement non-interactif (CI/Render) —
# sans ça, Aftman demande une confirmation manuelle pour chaque outil jamais
# installé sur la machine. Les versions sont épinglées ci-dessus, donc pas de
# risque de dérive silencieuse.
aftman install --no-trust-check

echo "-- Installation des dépendances Python (Problox) --"
python3 -m pip install --break-system-packages -e .

echo "== Setup terminé =="
echo "Vérifie avec: problox check"
