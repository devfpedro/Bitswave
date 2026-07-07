"""Tela de seleção de playlists: criar, abrir, renomear e excluir."""
import io
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

from player import AudioPlayer

from . import dialogs, theme
from .tooltip import add_tooltip

_COLUMNS = 2
_COVER_SIZE = 130
_CARD_WIDTH = 170
_CARD_HEIGHT = 214


def _cover_image_for_playlist(app, playlist_id: int) -> Image.Image:
    """Usa a capa embutida (ID3) da primeira faixa da playlist, se houver."""
    tracks = app.db.get_tracks(playlist_id)
    if tracks:
        cover_bytes = AudioPlayer.get_cover_art(tracks[0]["filepath"])
        if cover_bytes:
            try:
                return Image.open(io.BytesIO(cover_bytes)).convert("RGB").resize(
                    (_COVER_SIZE, _COVER_SIZE)
                )
            except Exception:
                pass
    return Image.new("RGB", (_COVER_SIZE, _COVER_SIZE), theme.CARD_BG_HOVER)


class _PlaylistCard(ctk.CTkFrame):
    """Card de uma playlist na grade: capa, nome, contagem de músicas e menu de opções."""

    def __init__(self, master, view: "PlaylistSelectionView", playlist_row):
        super().__init__(master, fg_color=theme.CARD_BG, corner_radius=14,
                          width=_CARD_WIDTH, height=_CARD_HEIGHT)
        self.grid_propagate(False)
        self.playlist_id = playlist_row["id"]
        self._view = view

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=(6, 0))
        self._menu_btn = ctk.CTkButton(
            top, text="⋮", width=26, height=26, corner_radius=13,
            fg_color="transparent", hover_color=theme.CARD_BG_HOVER, text_color=theme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=16), command=self._show_menu,
        )
        self._menu_btn.pack(side="right")
        add_tooltip(self._menu_btn, "Renomear ou excluir")

        cover_pil = _cover_image_for_playlist(view.app, self.playlist_id)
        self._cover_image = ctk.CTkImage(cover_pil, size=(_COVER_SIZE, _COVER_SIZE))
        cover_label = ctk.CTkLabel(self, image=self._cover_image, text="")
        cover_label.pack(padx=14, pady=(2, 8))

        name_label = ctk.CTkLabel(
            self, text=playlist_row["name"], font=ctk.CTkFont(size=14, weight="bold"),
            text_color=theme.TEXT_PRIMARY, wraplength=_COVER_SIZE - 4, justify="left", anchor="w",
        )
        name_label.pack(padx=12, fill="x")

        count = playlist_row["track_count"]
        subtitle_text = f"{count} música" + ("" if count == 1 else "s")
        subtitle = ctk.CTkLabel(
            self, text=subtitle_text, font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_SECONDARY, anchor="w",
        )
        subtitle.pack(padx=12, pady=(0, 10), fill="x")

        for widget in (self, cover_label, name_label, subtitle):
            widget.bind("<Button-1>", self._on_click_open)

    def _on_click_open(self, event) -> None:
        self._view.app.show_playlist_detail(self.playlist_id)

    def _show_menu(self) -> None:
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Renomear", command=lambda: self._view.rename_playlist(self.playlist_id))
        menu.add_command(label="Excluir", command=lambda: self._view.delete_playlist(self.playlist_id))
        x = self._menu_btn.winfo_rootx()
        y = self._menu_btn.winfo_rooty() + self._menu_btn.winfo_height()
        menu.tk_popup(x, y)


class PlaylistSelectionView(ctk.CTkFrame):
    """Grade de playlists salvas: criar, abrir, renomear e excluir."""

    def __init__(self, master, app):
        super().__init__(master, fg_color=theme.BG_DARK)
        self.app = app
        self._cards: list = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_topbar()
        self._build_create_button()
        self._build_grid()

    def _build_topbar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        back_btn = ctk.CTkButton(
            bar, text="←", width=40, height=40, corner_radius=20,
            fg_color=theme.CARD_BG, hover_color=theme.CARD_BG_HOVER, text_color=theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=16), command=self.app.show_playback,
        )
        back_btn.pack(side="left")
        add_tooltip(back_btn, "Voltar para reprodução")

        title_box = ctk.CTkFrame(bar, fg_color="transparent")
        title_box.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(
            title_box, text="Playlists", font=ctk.CTkFont(size=20, weight="bold"), text_color=theme.TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box, text="Suas coleções de músicas", font=ctk.CTkFont(size=12), text_color=theme.TEXT_SECONDARY,
        ).pack(anchor="w")

    def _build_create_button(self) -> None:
        create_btn = ctk.CTkButton(
            self, text="＋ Criar Nova Playlist", height=40, corner_radius=20,
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER, font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_create_playlist,
        )
        create_btn.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 12))

    def _build_grid(self) -> None:
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        for col in range(_COLUMNS):
            self.scroll.grid_columnconfigure(col, weight=1)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def on_show(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        for card in self._cards:
            card.destroy()
        self._cards = []

        playlists = self.app.db.list_playlists()
        if not playlists:
            empty = ctk.CTkLabel(
                self.scroll, text="Nenhuma playlist ainda.\nCrie a primeira acima!",
                font=ctk.CTkFont(size=13), text_color=theme.TEXT_SECONDARY, justify="center",
            )
            empty.grid(row=0, column=0, columnspan=_COLUMNS, pady=40)
            self._cards.append(empty)
            return

        for index, row in enumerate(playlists):
            card = _PlaylistCard(self.scroll, self, row)
            r, c = divmod(index, _COLUMNS)
            card.grid(row=r, column=c, padx=8, pady=8, sticky="n")
            self._cards.append(card)

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------

    def _on_create_playlist(self) -> None:
        result = dialogs.playlist_form_dialog(self.app, "Nova Playlist", ok_label="Criar")
        if not result:
            return
        name, description = result
        try:
            self.app.db.create_playlist(name, description)
        except ValueError as exc:
            messagebox.showerror("Não foi possível criar a playlist", str(exc))
            return
        self.refresh()

    def rename_playlist(self, playlist_id: int) -> None:
        playlist = self.app.db.get_playlist(playlist_id)
        if playlist is None:
            return
        new_name = dialogs.simple_prompt(
            self.app, "Renomear Playlist", "Novo nome", initial=playlist["name"],
        )
        if not new_name:
            return
        try:
            self.app.db.rename_playlist(playlist_id, new_name)
        except ValueError as exc:
            messagebox.showerror("Não foi possível renomear", str(exc))
            return
        self.refresh()

    def delete_playlist(self, playlist_id: int) -> None:
        playlist = self.app.db.get_playlist(playlist_id)
        if playlist is None:
            return
        if dialogs.confirm(
            self.app, "Excluir Playlist",
            f'Tem certeza que deseja excluir "{playlist["name"]}"? Essa ação não pode ser desfeita.',
            danger=True,
        ):
            self.app.db.delete_playlist(playlist_id)
            self.refresh()
