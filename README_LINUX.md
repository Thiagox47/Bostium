# Bostium Browser para Linux

Instalador e instruções de execução do Bostium Browser em distribuições Linux (Ubuntu, Debian, Linux Mint, Fedora, Arch Linux, Manjaro, etc.).

---

## 🚀 Como Instalar no Linux

1. Extraia o arquivo `Bostium_Linux.tar.gz` (ou clique com botão direito e escolha "Extrair Aqui"):
   ```bash
   tar -xzvf Bostium_Linux.tar.gz
   cd Bostium_Linux
   ```

2. Execute o instalador (não precisa de `sudo`/root):
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Pronto!** O Bostium será instalado em `~/.local/share/bostium` e o atalho **Bostium** estará disponível no menu de aplicativos do seu sistema na categoria **Internet / Navegadores**.

---

## ⚙️ Pré-requisitos (Wine)

Como o Bostium utiliza o motor WebView2 e APIs de controle de memória nativas, ele roda no Linux através da camada de compatibilidade **Wine**. Se você ainda não tem o Wine instalado:

- **Ubuntu / Debian / Linux Mint:**
  ```bash
  sudo apt update
  sudo apt install wine
  ```

- **Fedora / RHEL:**
  ```bash
  sudo dnf install wine
  ```

- **Arch Linux / Manjaro:**
  ```bash
  sudo pacman -S wine
  ```

---

## 🗑️ Como Desinstalar

Para remover completamente o Bostium do seu sistema:
```bash
chmod +x uninstall.sh
./uninstall.sh
```
