# Bostium Browser - Versão Nativa para Linux (Sem Wine)

Esta é a versão **100% nativa do Bostium para distribuições Linux** (Ubuntu, Debian, Linux Mint, Pop!_OS, Fedora, Arch Linux, Manjaro, openSUSE, etc.), construída com a stack oficial do ecossistema GNOME/Linux: **Python 3 + GTK 3 + WebKit2GTK**.

---

## ⚡ Recursos Nativos Inclusos
- **Arquitetura Ghost Tabs:** Hiberna abas em segundo plano automaticamente para manter o consumo de RAM em níveis mínimos (< 50 MB).
- **Picture-in-Picture (PiP):** Destaca vídeos em reprodução com 1 clique (`📺 PiP` ou `Ctrl+Shift+P`).
- **Limpador de Memória Instantâneo:** Badge `⚡ RAM` e atalho `Ctrl+Shift+O` para limpar caches e garbage collector em tempo real.
- **Barra de Favoritos e Sessão:** Salva abas e favoritos automaticamente em `~/.config/bostium/`.
- **Atalhos Rápidos:**
  - `Ctrl+T`: Nova aba
  - `Ctrl+W`: Fechar aba ativa
  - `Ctrl+L`: Focar barra de endereços
  - `Ctrl+R` / `F5`: Recarregar página
  - `Ctrl+Shift+O`: Limpar RAM
  - `Ctrl+Shift+P`: Picture-in-Picture

---

## 📦 Como Instalar

### Opção 1: Via Pacote `.deb` (Ubuntu, Debian, Linux Mint, Pop!_OS, Zorin OS)
Basta dar dois cliques no arquivo `bostium_1.0_all.deb` ou instalar via terminal:
```bash
sudo apt install ./bostium_1.0_all.deb
```
*(O `apt` resolverá e instalará automaticamente todas as dependências de WebKitGTK e GTK3).*

---

### Opção 2: Via Pacote Portátil / Script Instalador (Qualquer Linux: Fedora, Arch, etc.)
1. Extraia o arquivo `Bostium-Linux-Nativo.tar.gz`:
   ```bash
   tar -xzvf Bostium-Linux-Nativo.tar.gz
   cd linux-native
   ```

2. Execute o instalador (instala no perfil do usuário sem precisar de senha de administrador):
   ```bash
   chmod +x install-native.sh
   ./install-native.sh
   ```

3. **Pronto!** O atalho **Bostium** estará disponível no menu de aplicativos do seu sistema na categoria **Internet / Navegadores**. Você também pode abrir pelo terminal digitando:
   ```bash
   bostium
   ```

---

## 🗑️ Como Desinstalar

- Se instalou pelo `.deb`:
  ```bash
  sudo apt remove bostium
  ```

- Se instalou pelo script:
  ```bash
  ./uninstall-native.sh
  ```
