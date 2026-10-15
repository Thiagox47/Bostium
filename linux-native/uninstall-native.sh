#!/bin/bash

# Desinstalador do Bostium Nativo
if [ "$(id -u)" -eq 0 ]; then
    rm -rf /usr/lib/bostium
    rm -f /usr/bin/bostium
    rm -f /usr/share/applications/bostium.desktop
    rm -f /usr/share/icons/hicolor/256x256/apps/bostium.png
    update-desktop-database /usr/share/applications 2>/dev/null || true
else
    rm -rf "$HOME/.local/share/bostium-native"
    rm -f "$HOME/.local/bin/bostium"
    rm -f "$HOME/.local/share/applications/bostium.desktop"
    rm -f "$HOME/.local/share/icons/hicolor/256x256/apps/bostium.png"
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

echo "[SUCESSO] Bostium Nativo desinstalado com sucesso."
