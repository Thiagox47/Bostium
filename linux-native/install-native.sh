#!/bin/bash
set -e

# ========================================================
#   Instalador Nativo do Bostium para Linux
#   Funciona sem sudo (no perfil do usuário) ou com sudo
# ========================================================

echo "========================================================"
echo "      Instalador do Bostium Browser Nativo (Linux)     "
echo "========================================================"
echo ""

# Verifica se é root ou usuário normal
if [ "$(id -u)" -eq 0 ]; then
    INSTALL_DIR="/usr/lib/bostium"
    BIN_DIR="/usr/bin"
    DESKTOP_DIR="/usr/share/applications"
    ICON_DIR="/usr/share/icons/hicolor/256x256/apps"
    MODE="sistema"
else
    INSTALL_DIR="$HOME/.local/share/bostium-native"
    BIN_DIR="$HOME/.local/bin"
    DESKTOP_DIR="$HOME/.local/share/applications"
    ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
    MODE="usuario"
fi

echo "Modo de instalação: $MODE"
echo "Diretório de destino: $INSTALL_DIR"
echo ""

# 1. Verifica dependências de WebKitGTK e Python
echo "[1/4] Verificando dependências nativas do sistema..."

MISSING_DEPS=0
python3 -c "import gi; gi.require_version('Gtk', '3.0')" 2>/dev/null || MISSING_DEPS=1
python3 -c "import gi; (gi.require_version('WebKit2', '4.1') if hasattr(gi, 'require_version') else None)" 2>/dev/null || \
python3 -c "import gi; (gi.require_version('WebKit2', '4.0') if hasattr(gi, 'require_version') else None)" 2>/dev/null || MISSING_DEPS=1

if [ "$MISSING_DEPS" -eq 1 ]; then
    echo ""
    echo "[AVISO] Algumas bibliotecas do WebKitGTK / PyGObject precisam ser instaladas."
    echo "Para instalar agora no seu sistema:"
    if command -v apt &> /dev/null; then
        echo "  sudo apt install -y python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1 || sudo apt install -y python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.0"
    elif command -v dnf &> /dev/null; then
        echo "  sudo dnf install -y python3-gobject gtk3 webkit2gtk4.1 || sudo dnf install -y python3-gobject gtk3 webkit2gtk3"
    elif command -v pacman &> /dev/null; then
        echo "  sudo pacman -S --needed python-gobject gtk3 webkit2gtk-4.1"
    fi
    echo ""
    read -p "Deseja continuar a instalação dos arquivos? (s/N): " resp
    if [[ "$resp" != "s" && "$resp" != "S" ]]; then
        echo "Instalação interrompida."
        exit 1
    fi
else
    echo "  -> Todas as dependências (Python3, GTK3, WebKit2) estão prontas!"
fi

# 2. Cria diretórios
echo "[2/4] Criando pastas..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 3. Copia arquivos
echo "[3/4] Instalando arquivos do Bostium..."
cp -f "$SCRIPT_DIR/bostium.py" "$INSTALL_DIR/"
cp -f "$SCRIPT_DIR/bostium" "$BIN_DIR/bostium"
chmod +x "$BIN_DIR/bostium"

if [ -f "$SCRIPT_DIR/bostium.png" ]; then
    cp -f "$SCRIPT_DIR/bostium.png" "$ICON_DIR/bostium.png"
elif [ -f "$SCRIPT_DIR/bostium_logo.png" ]; then
    cp -f "$SCRIPT_DIR/bostium_logo.png" "$ICON_DIR/bostium.png"
fi

# 4. Configura atalho .desktop
echo "[4/4] Registrando atalho no menu de aplicativos..."
cat << EOF > "$DESKTOP_DIR/bostium.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Bostium
GenericName=Navegador Web
Comment=Navegador Web Ultraleve com Abas Virtuais Ghost Tabs
Exec=$BIN_DIR/bostium %U
Icon=bostium
Terminal=false
Categories=Network;WebBrowser;
MimeType=text/html;text/xml;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;
StartupWMClass=bostium.py
EOF

chmod +x "$DESKTOP_DIR/bostium.desktop"

# Atualiza caches do sistema
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t "$ICON_DIR/../.." 2>/dev/null || true
fi

echo ""
echo "========================================================"
echo "    [SUCESSO] Bostium Nativo instalado com sucesso!     "
echo "========================================================"
echo "- O navegador já está disponível no Menu de Aplicativos."
echo "- Para abrir via terminal, digite: bostium"
echo "- Para desinstalar, execute: ./uninstall-native.sh"
echo ""
