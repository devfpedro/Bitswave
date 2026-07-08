"""Janela principal: hospeda as 3 telas e gerencia a navegação entre elas."""
import os
import sys
import tkinter as tk

import customtkinter as ctk

from db import PlaylistDB
from folder_watch import FolderWatcher, default_watch_folders
from paths import resource_path
from player import AudioPlayer

from . import theme
from .playback_view import PlaybackView
from .playlist_detail_view import PlaylistDetailView
from .playlist_selection_view import PlaylistSelectionView
from .shortcuts_view import ShortcutsView

ICON_PATH = resource_path("models", "icons", "iconApp.png")
ICON_ICO_PATH = resource_path("models", "icons", "iconApp.ico")


class App(ctk.CTk):
    """Janela principal do Bitswave, com navegação entre as 3 telas."""

    def __init__(self, player: AudioPlayer | None = None, db: PlaylistDB | None = None):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.player = player if player is not None else AudioPlayer()
        self.db = db if db is not None else PlaylistDB()
        self.folder_watcher = FolderWatcher(default_watch_folders())

        self.title("Bitswave")
        self.wm_iconname("Bitswave")
        self.geometry("400x580")
        self.minsize(360, 540)
        self.configure(fg_color=theme.BG_DARK)
        self._set_window_icon()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.playback_view = PlaybackView(self, self)
        self.playlist_selection_view = PlaylistSelectionView(self, self)
        self.playlist_detail_view = PlaylistDetailView(self, self)
        self.shortcuts_view = ShortcutsView(self, self)

        for view in (
            self.playback_view, self.playlist_selection_view,
            self.playlist_detail_view, self.shortcuts_view,
        ):
            view.grid(row=0, column=0, sticky="nsew")

        self._active_show = self.show_playback

        self._bind_shortcuts()
        self.playback_view.load_state()
        self.show_playback()

    def _set_window_icon(self) -> None:
        # iconbitmap (.ico) é o que o Windows realmente usa para o ícone no canto
        # superior esquerdo da barra de título; iconphoto (.png) cobre a barra de
        # tarefas/Alt+Tab. Os dois são necessários para o ícone aparecer em todo lugar
        # no Windows. No Linux, o Tk/X11 não entende .ico (espera XBM) e o ícone vem
        # do iconphoto (.png) + do .desktop do AppImage, então pulamos o iconbitmap.
        if sys.platform == "win32" and os.path.isfile(ICON_ICO_PATH):
            try:
                self.iconbitmap(default=ICON_ICO_PATH)
            except tk.TclError:
                pass
        if os.path.isfile(ICON_PATH):
            try:
                self._icon_image = tk.PhotoImage(file=ICON_PATH)
                self.iconphoto(True, self._icon_image)
            except tk.TclError:
                pass

    def _bind_shortcuts(self) -> None:
        """Vincula os atalhos de teclado globais. Lista completa em ui/shortcuts.py."""
        self.bind("<space>", lambda e: self.playback_view._on_play_pause())
        self.bind("<Left>", lambda e: self.playback_view.seek_relative(-5))
        self.bind("<Right>", lambda e: self.playback_view.seek_relative(5))
        self.bind("<Control-Left>", lambda e: self.playback_view._on_next())
        self.bind("<Control-Right>", lambda e: self.playback_view._on_prev())
        self.bind("<Up>", lambda e: self.playback_view.adjust_volume(0.05))
        self.bind("<Down>", lambda e: self.playback_view.adjust_volume(-0.05))
        self.bind("<Control-r>", lambda e: self.playback_view._on_toggle_shuffle())
        self.bind("<Control-s>", lambda e: self.show_playlist_selection())
        self.bind("<Control-o>", lambda e: self.playback_view._on_add_files())

    # ------------------------------------------------------------------
    # Navegação
    # ------------------------------------------------------------------

    def show_playback(self) -> None:
        self._active_show = self.show_playback
        self.playback_view.on_show()
        self.playback_view.tkraise()

    def show_playlist_selection(self) -> None:
        self._active_show = self.show_playlist_selection
        self.playlist_selection_view.on_show()
        self.playlist_selection_view.tkraise()

    def show_playlist_detail(self, playlist_id: int) -> None:
        self._active_show = lambda: self.show_playlist_detail(playlist_id)
        self.playlist_detail_view.on_show(playlist_id)
        self.playlist_detail_view.tkraise()

    def show_shortcuts(self) -> None:
        """Abre a tela de atalhos, lembrando de qual tela veio para o botão voltar."""
        self.shortcuts_view.on_show()
        self.shortcuts_view.tkraise()

    def go_back_from_shortcuts(self) -> None:
        self._active_show()

    def play_queue(self, filepaths: list[str], start_index: int = 0, shuffle: bool = False) -> None:
        """Carrega uma fila de faixas no player e muda para a tela de reprodução."""
        self.playback_view.load_queue(filepaths, start_index=start_index, shuffle=shuffle)
        self.show_playback()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def on_closing(self) -> None:
        """Salva o estado e libera recursos ao fechar a janela."""
        self.playback_view.save_state()
        self.player.cleanup()
        self.db.close()
        self.destroy()
