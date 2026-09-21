#!/usr/bin/env bash
# Installe le CLI Render (déploiement/gestion du backend ProbloxDev).
# L'API GitHub (api.github.com) est bloquée par certaines politiques réseau
# (proxy d'entreprise, sandbox restreint) ; ce script télécharge donc
# directement l'asset de release connu au lieu de résoudre "latest" via
# l'API, avec repli sur raw.githubusercontent.com pour lister les versions.
set -euo pipefail

RENDER_CLI_VERSION="${RENDER_CLI_VERSION:-1.1.0}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"

ARCH="$(uname -m)"
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
case "$ARCH" in
  x86_64) ARCH="amd64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *) echo "Architecture non supportée: $ARCH" >&2; exit 1 ;;
esac

ASSET="cli_${RENDER_CLI_VERSION}_${OS}_${ARCH}.zip"
URL="https://github.com/render-oss/cli/releases/download/v${RENDER_CLI_VERSION}/${ASSET}"

echo "== Installation Render CLI v${RENDER_CLI_VERSION} (${OS}/${ARCH}) =="
TMP_DIR="$(mktemp -d)"
curl -fsSL -o "$TMP_DIR/render.zip" "$URL"
unzip -oq "$TMP_DIR/render.zip" -d "$TMP_DIR"

BIN_PATH=$(find "$TMP_DIR" -maxdepth 1 -type f -name "cli_v*" -o -maxdepth 1 -type f -name "render" | head -n1)
if [ -z "$BIN_PATH" ]; then
  BIN_PATH=$(find "$TMP_DIR" -maxdepth 1 -type f -perm -u+x | head -n1)
fi

mkdir -p "$INSTALL_DIR"
cp "$BIN_PATH" "$INSTALL_DIR/render"
chmod +x "$INSTALL_DIR/render"
rm -rf "$TMP_DIR"

echo "Installé dans $INSTALL_DIR/render"
echo "Ajoute-le au PATH si besoin: export PATH=\"$INSTALL_DIR:\$PATH\""
"$INSTALL_DIR/render" --version

echo
echo "Prochaine étape: 'render login' puis 'render services create' ou déploie"
echo "directement le blueprint render.yaml (voir docs/DEPLOY.md)."
