#!/bin/bash

# =========================================================
#   Desinstalador do Bostium Browser para Linux
# =========================================================

INSTALL_DIR="$HOME/.local/share/bostium"
DESKTOP_FILE="$HOME/.local/share/applications/bostium.desktop"
ICON_FILE="$HOME/.local/share/icons/hicolor/256x256/apps/bostium.png"
BIN_FILE="$HOME/.local/bin/bostium"

echo "Removendo o Bostium do seu sistema Linux..."

rm -rf "$INSTALL_DIR"
rm -f "$DESKTOP_FILE"
rm -f "$ICON_FILE"
rm -f "$BIN_FILE"

if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

echo "[SUCESSO] Bostium desinstalado com sucesso."
