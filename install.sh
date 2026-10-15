#!/bin/bash
set -e

# =========================================================
#   Instalador do Bostium Browser para Linux
#   Instalação por usuário (sem necessidade de sudo/root)
# =========================================================

INSTALL_DIR="$HOME/.local/share/bostium"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
BIN_DIR="$HOME/.local/bin"

echo "========================================================="
echo "        Instalador do Bostium Browser para Linux         "
echo "========================================================="
echo ""

# Verifica se o Wine está instalado no sistema
if ! command -v wine &> /dev/null; then
    echo "[AVISO] O 'wine' não foi encontrado no seu sistema."
    echo "O Bostium foi desenvolvido para Windows e utiliza o motor WebView2."
    echo "Para executá-lo no Linux, instale o Wine:"
    echo "  - Ubuntu/Debian/Mint:  sudo apt install wine"
    echo "  - Fedora:              sudo dnf install wine"
    echo "  - Arch Linux / Manjaro: sudo pacman -S wine"
    echo ""
    read -p "Deseja continuar com a instalação mesmo assim? (s/N): " resp
    if [[ "$resp" != "s" && "$resp" != "S" ]]; then
        echo "Instalação cancelada pelo usuário."
        exit 1
    fi
fi

# Cria diretórios de destino no perfil do usuário
echo "[1/4] Criando diretórios em $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"
mkdir -p "$BIN_DIR"

# Diretório onde o script instalador está rodando
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copia arquivos do navegador
echo "[2/4] Copiando arquivos do Bostium..."
cp -f "$SCRIPT_DIR/Bostium.exe" "$INSTALL_DIR/" 2>/dev/null || true
cp -f "$SCRIPT_DIR"/Microsoft.Web.WebView2.*.dll "$INSTALL_DIR/" 2>/dev/null || true
cp -f "$SCRIPT_DIR/WebView2Loader.dll" "$INSTALL_DIR/" 2>/dev/null || true
cp -f "$SCRIPT_DIR/bostium.ico" "$INSTALL_DIR/" 2>/dev/null || true
if [ -d "$SCRIPT_DIR/runtimes" ]; then
    cp -rf "$SCRIPT_DIR/runtimes" "$INSTALL_DIR/"
fi
if [ -f "$SCRIPT_DIR/bostium_logo.png" ]; then
    cp -f "$SCRIPT_DIR/bostium_logo.png" "$ICON_DIR/bostium.png"
fi

# Cria o wrapper executável em ~/.local/bin/bostium
echo "[3/4] Criando comando de terminal 'bostium'..."
cat << 'EOF' > "$BIN_DIR/bostium"
#!/bin/bash
WINE_CMD="wine"
APP_PATH="$HOME/.local/share/bostium/Bostium.exe"

if command -v wine &> /dev/null; then
    wine "$APP_PATH" "$@"
else
    echo "Erro: Wine não está instalado. Instale o Wine para executar o Bostium."
    exit 1
fi
EOF
chmod +x "$BIN_DIR/bostium"

# Cria o lançador de aplicativo (.desktop) para o menu do sistema
echo "[4/4] Integrando com o menu de aplicativos do Linux..."
cat << EOF > "$DESKTOP_DIR/bostium.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Bostium
GenericName=Navegador Web
Comment=Navegador Web Leve Bostium
Exec=$BIN_DIR/bostium %U
Icon=bostium
Terminal=false
Categories=Network;WebBrowser;
MimeType=text/html;text/xml;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;
StartupWMClass=Bostium.exe
EOF

chmod +x "$DESKTOP_DIR/bostium.desktop"

# Atualiza caches do ambiente de desktop (GNOME, KDE, XFCE, etc)
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo ""
echo "========================================================="
echo "   [SUCESSO] Bostium instalado com sucesso no Linux!     "
echo "========================================================="
echo "- O atalho já aparece no seu Menu de Aplicativos (Internet/Navegador)."
echo "- Você também pode abrir pelo terminal digitando: bostium"
echo "- Para desinstalar a qualquer momento, execute: ./uninstall.sh"
echo ""
