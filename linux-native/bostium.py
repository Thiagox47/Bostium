#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bostium Browser - Versão Nativa para Linux
Baseado em GTK 3 e WebKit2GTK com arquitetura Ghost Tabs e gestão ultraleve de RAM.
"""

import os
import sys
import json
import gc
import re
import urllib.parse
from datetime import datetime

# Configuração de versões das bibliotecas do GNOME
import gi
try:
    gi.require_version('WebKit2', '4.1')
except (ValueError, AttributeError):
    try:
        gi.require_version('WebKit2', '4.0')
    except (ValueError, AttributeError):
        pass

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, WebKit2, Pango

# Caminhos de dados do usuário (Padrão XDG Linux)
CONFIG_DIR = os.path.expanduser("~/.config/bostium")
BOOKMARKS_FILE = os.path.join(CONFIG_DIR, "bookmarks.json")
SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")
os.makedirs(CONFIG_DIR, exist_ok=True)

DEFAULT_URL = "https://www.google.com"
MAX_ACTIVE_ENGINES = 2

# Estilização CSS Dark Premium (Inspirada no Arc / Chrome Dark)
CSS_STYLE = b"""
window, .main-window {
    background-color: #121216;
    color: #F3F4F6;
}

.top-bar {
    background-color: #1A1B22;
    border-bottom: 1px solid #282A36;
    padding: 4px 8px;
}

.tab-strip {
    background-color: #14141A;
    border-bottom: 1px solid #232530;
    padding: 3px 6px 0px 6px;
}

.tab-item {
    background-color: #1C1D24;
    border: 1px solid #2C2E3B;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    padding: 4px 10px;
    margin-right: 4px;
    color: #9CA3AF;
    font-size: 12px;
    transition: all 150ms ease-in-out;
}

.tab-item:hover {
    background-color: #242632;
    color: #F3F4F6;
}

.tab-item.active {
    background-color: #22242F;
    border-color: #3B82F6;
    border-top: 2px solid #3B82F6;
    color: #FFFFFF;
    font-weight: bold;
}

.tab-item.hibernated {
    color: #6B7280;
    font-style: italic;
}

.omnibox {
    background-color: #121215;
    border: 1px solid #2E3242;
    border-radius: 8px;
    color: #F3F4F6;
    padding: 6px 12px;
    font-size: 13px;
    caret-color: #3B82F6;
}

.omnibox:focus {
    border-color: #3B82F6;
    box-shadow: 0 0 0 1px #3B82F6;
}

.nav-btn {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    color: #9CA3AF;
    padding: 4px 8px;
    font-size: 14px;
}

.nav-btn:hover {
    background-color: #282A38;
    color: #FFFFFF;
}

.badge-ram {
    background-color: #1E2333;
    border: 1px solid #3B82F6;
    border-radius: 6px;
    color: #60A5FA;
    font-weight: bold;
    font-size: 11px;
    padding: 3px 8px;
}

.badge-ram:hover {
    background-color: #2563EB;
    color: #FFFFFF;
}

.badge-auto {
    background-color: #162B20;
    border: 1px solid #22C55E;
    border-radius: 6px;
    color: #4ADE80;
    font-size: 11px;
    padding: 3px 6px;
}

.badge-auto.off {
    background-color: #2E1B1B;
    border-color: #EF4444;
    color: #F87171;
}

.bookmarks-bar {
    background-color: #181920;
    border-bottom: 1px solid #242633;
    padding: 2px 8px;
}

.bm-item {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    color: #D1D5DB;
    font-size: 11px;
    padding: 2px 6px;
}

.bm-item:hover {
    background-color: #262836;
    color: #FFFFFF;
}

.status-bar {
    background-color: #101115;
    border-top: 1px solid #20222C;
    padding: 2px 10px;
    color: #6B7280;
    font-size: 11px;
}
"""


class TabInfo:
    """Representa o estado de uma aba (ativa ou hibernada/ghost)."""
    def __init__(self, url=DEFAULT_URL, title="Nova Guia"):
        self.url = url
        self.title = title
        self.is_hibernated = False
        self.is_pinned = False
        self.webview = None
        self.container = None
        self.tab_widget = None
        self.lbl_title = None
        self.btn_close = None
        self.last_accessed = datetime.now()


class BostiumApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Bostium Browser")
        self.set_default_size(1200, 780)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.get_style_context().add_class("main-window")

        # Configura contexto WebKit otimizado para baixa memória
        self.web_context = WebKit2.WebContext.get_default()
        self.web_context.set_cache_model(WebKit2.CacheModel.DOCUMENT_VIEWER)

        self.tabs = []
        self.active_index = -1
        self.auto_hibernate = True
        self.bookmarks = self.load_bookmarks()

        self.setup_ui()
        self.setup_shortcuts()
        self.setup_css()

        # Inicia temporizador de monitor de RAM (a cada 2 segundos)
        GLib.timeout_add(2000, self.update_memory_info)

        # Restaura ou abre primeira guia
        self.restore_session()
        if not self.tabs:
            self.create_tab(DEFAULT_URL)

    def setup_ui(self):
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.main_box)

        # 1. Barra de Abas (TabStrip)
        self.tab_strip_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.tab_strip_box.get_style_context().add_class("tab-strip")

        # Scroll para muitas abas
        self.tab_scroll = Gtk.ScrolledWindow()
        self.tab_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        self.tab_scroll.set_shadow_type(Gtk.ShadowType.NONE)

        self.tabs_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.tab_scroll.add(self.tabs_container)
        self.tab_strip_box.pack_start(self.tab_scroll, True, True, 0)

        # Botão Nova Guia (+)
        self.btn_new_tab = Gtk.Button(label="+")
        self.btn_new_tab.get_style_context().add_class("nav-btn")
        self.btn_new_tab.set_tooltip_text("Nova Guia (Ctrl+T)")
        self.btn_new_tab.connect("clicked", lambda b: self.create_tab(DEFAULT_URL))
        self.tab_strip_box.pack_start(self.btn_new_tab, False, False, 4)

        self.main_box.pack_start(self.tab_strip_box, False, False, 0)

        # 2. Barra de Navegação (NavBar / Omnibox)
        self.nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.nav_box.get_style_context().add_class("top-bar")

        # Botões de Navegação
        self.btn_back = Gtk.Button(label="◀")
        self.btn_back.get_style_context().add_class("nav-btn")
        self.btn_back.connect("clicked", self.on_back_clicked)
        self.nav_box.pack_start(self.btn_back, False, False, 0)

        self.btn_forward = Gtk.Button(label="▶")
        self.btn_forward.get_style_context().add_class("nav-btn")
        self.btn_forward.connect("clicked", self.on_forward_clicked)
        self.nav_box.pack_start(self.btn_forward, False, False, 0)

        self.btn_reload = Gtk.Button(label="⟳")
        self.btn_reload.get_style_context().add_class("nav-btn")
        self.btn_reload.connect("clicked", self.on_reload_clicked)
        self.nav_box.pack_start(self.btn_reload, False, False, 0)

        # Barra de Endereços (Omnibox)
        self.omnibox = Gtk.Entry()
        self.omnibox.get_style_context().add_class("omnibox")
        self.omnibox.set_placeholder_text("Digite uma URL ou pesquise no Google...")
        self.omnibox.connect("activate", self.on_omnibox_activate)
        self.nav_box.pack_start(self.omnibox, True, True, 4)

        # Botão Favoritar (★)
        self.btn_star = Gtk.Button(label="☆")
        self.btn_star.get_style_context().add_class("nav-btn")
        self.btn_star.set_tooltip_text("Adicionar aos Favoritos")
        self.btn_star.connect("clicked", self.toggle_bookmark)
        self.nav_box.pack_start(self.btn_star, False, False, 0)

        # Botão PiP (Picture in Picture)
        self.btn_pip = Gtk.Button(label="📺 PiP")
        self.btn_pip.get_style_context().add_class("nav-btn")
        self.btn_pip.set_tooltip_text("Destacar Vídeo em Picture-in-Picture (Ctrl+Shift+P)")
        self.btn_pip.connect("clicked", self.toggle_pip)
        self.nav_box.pack_start(self.btn_pip, False, False, 0)

        # Botão Fixar Guia (📌)
        self.btn_pin = Gtk.Button(label="📌")
        self.btn_pin.get_style_context().add_class("nav-btn")
        self.btn_pin.set_tooltip_text("Fixar esta guia (não hiberna)")
        self.btn_pin.connect("clicked", self.toggle_pin_active_tab)
        self.nav_box.pack_start(self.btn_pin, False, False, 0)

        # Botão Auto-Hibernação
        self.btn_auto_hib = Gtk.Button(label="💤 Auto: ON")
        self.btn_auto_hib.get_style_context().add_class("badge-auto")
        self.btn_auto_hib.set_tooltip_text("Alternar auto-hibernação de guias em segundo plano")
        self.btn_auto_hib.connect("clicked", self.toggle_auto_hibernate)
        self.nav_box.pack_start(self.btn_auto_hib, False, False, 2)

        # Badge Limpeza de RAM
        self.btn_ram_badge = Gtk.Button(label="⚡ RAM: -- MB")
        self.btn_ram_badge.get_style_context().add_class("badge-ram")
        self.btn_ram_badge.set_tooltip_text("Clique para liberar RAM imediatamente (Ctrl+Shift+O)")
        self.btn_ram_badge.connect("clicked", lambda b: self.purge_memory())
        self.nav_box.pack_start(self.btn_ram_badge, False, False, 2)

        self.main_box.pack_start(self.nav_box, False, False, 0)

        # 3. Barra de Favoritos
        self.bm_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.bm_bar.get_style_context().add_class("bookmarks-bar")
        self.main_box.pack_start(self.bm_bar, False, False, 0)
        self.render_bookmarks()

        # 4. Host Central de Páginas Web (Stack)
        self.web_stack = Gtk.Stack()
        self.web_stack.set_transition_type(Gtk.StackTransitionType.NONE)
        self.main_box.pack_start(self.web_stack, True, True, 0)

        # 5. Barra de Status Inferior
        self.status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.status_bar.get_style_context().add_class("status-bar")

        self.lbl_status_msg = Gtk.Label(label="Pronto")
        self.lbl_status_msg.set_alignment(0, 0.5)
        self.status_bar.pack_start(self.lbl_status_msg, True, True, 0)

        self.lbl_status_tabs = Gtk.Label(label="Guias: 0 (Ativas: 0 | Hibernadas: 0)")
        self.status_bar.pack_end(self.lbl_status_tabs, False, False, 10)

        self.lbl_status_ram = Gtk.Label(label="RAM Alocada: -- MB")
        self.status_bar.pack_end(self.lbl_status_ram, False, False, 10)

        self.main_box.pack_start(self.status_bar, False, False, 0)

        self.connect("destroy", self.on_close_app)

    def setup_shortcuts(self):
        """Atalhos de teclado ágeis estilo Chrome / Arc."""
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)

        # Ctrl+T: Nova Guia
        key, mod = Gtk.accelerator_parse("<Primary>t")
        accel_group.connect(key, mod, Gtk.AccelFlags.VISIBLE, lambda *a: self.create_tab(DEFAULT_URL))

        # Ctrl+W: Fechar Guia
        key, mod = Gtk.accelerator_parse("<Primary>w")
        accel_group.connect(key, mod, Gtk.AccelFlags.VISIBLE, lambda *a: self.close_active_tab())

        # Ctrl+R: Recarregar
        key, mod = Gtk.accelerator_parse("<Primary>r")
        accel_group.connect(key, mod, Gtk.AccelFlags.VISIBLE, lambda *a: self.on_reload_clicked(None))

        # F5: Recarregar
        key, mod = Gtk.accelerator_parse("F5")
        accel_group.connect(key, mod, Gtk.AccelFlags.VISIBLE, lambda *a: self.on_reload_clicked(None))

        # Ctrl+L: Focar barra de endereços
        key, mod = Gtk.accelerator_parse("<Primary>l")
        accel_group.connect(key, mod, Gtk.AccelFlags.VISIBLE, lambda *a: self.omnibox.grab_focus())

        # Ctrl+Shift+O: Otimizar RAM
        key, mod = Gtk.accelerator_parse("<Primary><Shift>o")
        accel_group.connect(key, mod, Gtk.AccelFlags.VISIBLE, lambda *a: self.purge_memory())

        # Ctrl+Shift+P: PiP
        key, mod = Gtk.accelerator_parse("<Primary><Shift>p")
        accel_group.connect(key, mod, Gtk.AccelFlags.VISIBLE, lambda *a: self.toggle_pip(None))

    def setup_css(self):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS_STYLE)
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    # ==========================================
    # GESTÃO DE GUIAS E GHOST TABS (BAIXA RAM)
    # ==========================================

    def create_tab(self, url=DEFAULT_URL, is_pinned=False):
        tab = TabInfo(url=url)
        tab.is_pinned = is_pinned

        # Widget visual da aba
        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        tab_box.get_style_context().add_class("tab-item")

        lbl_title = Gtk.Label(label="Carregando...")
        lbl_title.set_max_width_chars(18)
        lbl_title.set_ellipsize(Pango.EllipsizeMode.END)
        tab_box.pack_start(lbl_title, False, False, 0)
        tab.lbl_title = lbl_title

        btn_close = Gtk.Button(label="✕")
        btn_close.get_style_context().add_class("nav-btn")
        btn_close.connect("clicked", lambda b: self.close_tab(tab))
        tab_box.pack_start(btn_close, False, False, 0)
        tab.btn_close = btn_close

        # Evento de clique para ativar a aba
        event_box = Gtk.EventBox()
        event_box.add(tab_box)
        event_box.connect("button-press-event", lambda w, e: self.switch_to_tab(self.tabs.index(tab)))
        tab.tab_widget = event_box

        self.tabs_container.pack_start(event_box, False, False, 0)
        event_box.show_all()

        # Container do WebView
        tab_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.web_stack.add_named(tab_container, str(id(tab)))
        tab.container = tab_container

        self.tabs.append(tab)
        self.switch_to_tab(len(self.tabs) - 1)
        self.manage_active_engines()
        self.update_tab_counts()
        return tab

    def init_tab_engine(self, tab):
        """Instancia o motor WebKitGTK para uma aba que foi hibernada."""
        if tab.webview is not None:
            return

        settings = WebKit2.Settings()
        settings.set_enable_developer_extras(False)
        settings.set_enable_media_stream(True)
        settings.set_enable_webaudio(True)
        settings.set_enable_smooth_scrolling(True)

        webview = WebKit2.WebView.new_with_context(self.web_context)
        webview.set_settings(settings)

        # Sinais de carregamento
        webview.connect("load-changed", self.on_webview_load_changed, tab)
        webview.connect("notify::title", self.on_webview_title_changed, tab)
        webview.connect("notify::uri", self.on_webview_uri_changed, tab)

        tab.container.pack_start(webview, True, True, 0)
        webview.show_all()
        tab.webview = webview
        tab.is_hibernated = False

        if tab.url:
            webview.load_uri(tab.url)

    def hibernate_tab(self, tab):
        """Descarta o motor WebKitGTK da aba inativa, liberando dezenas de MBs de RAM."""
        if tab.is_hibernated or tab.is_pinned or tab == self.get_active_tab():
            return

        if tab.webview is not None:
            # Salva URL atual para restaurar depois
            uri = tab.webview.get_uri()
            if uri:
                tab.url = uri
            tab.container.remove(tab.webview)
            tab.webview.destroy()
            tab.webview = None

        tab.is_hibernated = True
        self.update_tab_ui(tab)
        self.purge_memory()
        self.update_tab_counts()

    def switch_to_tab(self, index):
        if index < 0 or index >= len(self.tabs):
            return

        self.active_index = index
        active_tab = self.tabs[index]
        active_tab.last_accessed = datetime.now()

        # Acorda aba se estiver hibernada
        if active_tab.is_hibernated or active_tab.webview is None:
            self.init_tab_engine(active_tab)

        self.web_stack.set_visible_child_name(str(id(active_tab)))

        # Atualiza Omnibox e barra de navegação
        curr_url = active_tab.webview.get_uri() if active_tab.webview else active_tab.url
        self.omnibox.set_text(curr_url or "")
        self.update_bookmark_icon(curr_url or "")
        self.update_pin_button(active_tab.is_pinned)

        # Atualiza estilo visual de todas as abas
        for i, tab in enumerate(self.tabs):
            self.update_tab_ui(tab, is_active=(i == index))

        self.manage_active_engines()
        self.update_tab_counts()

    def manage_active_engines(self):
        """Aplica a regra Ghost Tabs: hiberna abas em segundo plano além do limite."""
        if not self.auto_hibernate:
            return

        # Conta motores ativos e hiberna as mais antigas não fixadas
        active_tabs = [t for t in self.tabs if not t.is_hibernated and t != self.get_active_tab() and not t.is_pinned]
        if len(active_tabs) > MAX_ACTIVE_ENGINES:
            # Ordena por último acesso (mais antigas primeiro)
            active_tabs.sort(key=lambda t: t.last_accessed)
            for old_tab in active_tabs[:-MAX_ACTIVE_ENGINES]:
                self.hibernate_tab(old_tab)

    def update_tab_ui(self, tab, is_active=None):
        if is_active is None:
            is_active = (self.tabs.index(tab) == self.active_index)

        box = tab.tab_widget.get_child()
        context = box.get_style_context()

        # Remove classes antigas
        context.remove_class("active")
        context.remove_class("hibernated")

        title = tab.title or "Sem título"
        if tab.is_pinned:
            title = "📌 " + title
        if tab.is_hibernated:
            title = "💤 " + title
            context.add_class("hibernated")

        if is_active:
            context.add_class("active")

        tab.lbl_title.set_text(title)

    def close_tab(self, tab):
        idx = self.tabs.index(tab)
        if tab.webview:
            tab.container.remove(tab.webview)
            tab.webview.destroy()

        self.web_stack.remove(tab.container)
        self.tabs_container.remove(tab.tab_widget)
        self.tabs.remove(tab)

        if not self.tabs:
            self.create_tab(DEFAULT_URL)
        else:
            new_idx = min(idx, len(self.tabs) - 1)
            self.switch_to_tab(new_idx)

        self.purge_memory()
        self.update_tab_counts()

    def close_active_tab(self):
        if 0 <= self.active_index < len(self.tabs):
            self.close_tab(self.tabs[self.active_index])

    def get_active_tab(self):
        if 0 <= self.active_index < len(self.tabs):
            return self.tabs[self.active_index]
        return None

    # ==========================================
    # EVENTOS DO MOTOR WEB E NAVEGAÇÃO
    # ==========================================

    def on_omnibox_activate(self, entry):
        text = entry.get_text().strip()
        if not text:
            return

        # Verifica se é URL ou busca
        if re.match(r'^(https?://|localhost|\d+\.\d+\.\d+\.\d+)', text):
            url = text
        elif "." in text and " " not in text:
            url = "https://" + text
        else:
            url = f"https://www.google.com/search?q={urllib.parse.quote(text)}"

        active_tab = self.get_active_tab()
        if active_tab and active_tab.webview:
            active_tab.url = url
            active_tab.webview.load_uri(url)

    def on_webview_load_changed(self, webview, load_event, tab):
        if load_event == WebKit2.LoadEvent.COMMITTED:
            uri = webview.get_uri()
            if tab == self.get_active_tab():
                self.omnibox.set_text(uri)
                self.update_bookmark_icon(uri)
        elif load_event == WebKit2.LoadEvent.FINISHED:
            self.update_tab_ui(tab)
            self.save_session()

    def on_webview_title_changed(self, webview, param, tab):
        title = webview.get_title()
        if title:
            tab.title = title
            self.update_tab_ui(tab)

    def on_webview_uri_changed(self, webview, param, tab):
        uri = webview.get_uri()
        if uri:
            tab.url = uri
            if tab == self.get_active_tab():
                self.omnibox.set_text(uri)

    def on_back_clicked(self, btn):
        tab = self.get_active_tab()
        if tab and tab.webview and tab.webview.can_go_back():
            tab.webview.go_back()

    def on_forward_clicked(self, btn):
        tab = self.get_active_tab()
        if tab and tab.webview and tab.webview.can_go_forward():
            tab.webview.go_forward()

    def on_reload_clicked(self, btn):
        tab = self.get_active_tab()
        if tab and tab.webview:
            tab.webview.reload()

    # ==========================================
    # CONTROLE DE MEMÓRIA RAM & MONITOR REAL-TIME
    # ==========================================

    def get_linux_ram_usage_mb(self):
        """Lê o consumo de RAM exato no Linux através de /proc/self/status (VmRSS)."""
        try:
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        parts = line.split()
                        kb = int(parts[1])
                        return kb / 1024.0
        except Exception:
            pass
        return 0.0

    def update_memory_info(self):
        ram_mb = self.get_linux_ram_usage_mb()
        self.btn_ram_badge.set_label(f"⚡ RAM: {ram_mb:.1f} MB")
        self.lbl_status_ram.set_text(f"RAM Alocada: {ram_mb:.1f} MB")
        return True  # Mantém temporizador ativo

    def purge_memory(self):
        """Libera buffers de cache de rede, decodificação de imagens e Garbage Collector."""
        self.web_context.clear_cache()
        gc.collect()
        ram_mb = self.get_linux_ram_usage_mb()
        self.btn_ram_badge.set_label(f"⚡ RAM: {ram_mb:.1f} MB")
        self.lbl_status_msg.set_text("Memória RAM otimizada com sucesso!")

    def update_tab_counts(self):
        total = len(self.tabs)
        hib = sum(1 for t in self.tabs if t.is_hibernated)
        active = total - hib
        self.lbl_status_tabs.set_text(f"Guias: {total} (Ativas: {active} | Hibernadas: {hib})")

    # ==========================================
    # PICTURE-IN-PICTURE & RECURSOS AVANÇADOS
    # ==========================================

    def toggle_pip(self, btn):
        """Destaca vídeo em modo Picture-in-Picture nativo ou janela flutuante."""
        tab = self.get_active_tab()
        if not tab or not tab.webview:
            return

        # Executa script JS para acionar Picture-in-Picture na tag <video>
        js_code = """
        (function() {
            var v = document.querySelector('video');
            if (v) {
                if (document.pictureInPictureElement) {
                    document.exitPictureInPicture();
                } else if (v.requestPictureInPicture) {
                    v.requestPictureInPicture();
                }
            } else {
                alert('Nenhum vídeo em reprodução encontrado nesta página.');
            }
        })();
        """
        tab.webview.run_javascript(js_code, None, None, None)

    def toggle_pin_active_tab(self, btn):
        tab = self.get_active_tab()
        if tab:
            tab.is_pinned = not tab.is_pinned
            self.update_pin_button(tab.is_pinned)
            self.update_tab_ui(tab)

    def update_pin_button(self, is_pinned):
        if is_pinned:
            self.btn_pin.set_label("📌 Fixada")
        else:
            self.btn_pin.set_label("📌")

    def toggle_auto_hibernate(self, btn):
        self.auto_hibernate = not self.auto_hibernate
        ctx = self.btn_auto_hib.get_style_context()
        if self.auto_hibernate:
            self.btn_auto_hib.set_label("💤 Auto: ON")
            ctx.remove_class("off")
            self.manage_active_engines()
        else:
            self.btn_auto_hib.set_label("💤 Auto: OFF")
            ctx.add_class("off")

    # ==========================================
    # FAVORITOS & SESSÃO PERSISTENTE
    # ==========================================

    def load_bookmarks(self):
        if os.path.exists(BOOKMARKS_FILE):
            try:
                with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return [
            {"title": "Google", "url": "https://www.google.com"},
            {"title": "GitHub", "url": "https://github.com"},
            {"title": "YouTube", "url": "https://www.youtube.com"}
        ]

    def save_bookmarks(self):
        try:
            with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.bookmarks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Erro ao salvar favoritos:", e)

    def render_bookmarks(self):
        for child in self.bm_bar.get_children():
            self.bm_bar.remove(child)

        for bm in self.bookmarks:
            btn = Gtk.Button(label=bm["title"])
            btn.get_style_context().add_class("bm-item")
            url = bm["url"]
            btn.connect("clicked", lambda b, u=url: self.create_tab(u))
            self.bm_bar.pack_start(btn, False, False, 2)
        self.bm_bar.show_all()

    def toggle_bookmark(self, btn):
        tab = self.get_active_tab()
        if not tab:
            return
        url = tab.webview.get_uri() if tab.webview else tab.url
        title = tab.title or "Favorito"

        existing = next((b for b in self.bookmarks if b["url"] == url), None)
        if existing:
            self.bookmarks.remove(existing)
            self.btn_star.set_label("☆")
        else:
            self.bookmarks.append({"title": title[:20], "url": url})
            self.btn_star.set_label("★")

        self.save_bookmarks()
        self.render_bookmarks()

    def update_bookmark_icon(self, url):
        is_bm = any(b["url"] == url for b in self.bookmarks)
        self.btn_star.set_label("★" if is_bm else "☆")

    def save_session(self):
        session_data = []
        for tab in self.tabs:
            u = tab.webview.get_uri() if tab.webview else tab.url
            if u:
                session_data.append({"url": u, "title": tab.title, "pinned": tab.is_pinned})
        try:
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def restore_session(self):
        if not os.path.exists(SESSION_FILE):
            return
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    for item in data:
                        self.create_tab(item.get("url", DEFAULT_URL), is_pinned=item.get("pinned", False))
        except Exception:
            pass

    def on_close_app(self, *args):
        self.save_session()
        Gtk.main_quit()


def main():
    app = BostiumApp()
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
