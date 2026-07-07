"""Tela de uma playlist em reprodução: faixas, ordem, edição e exclusão de faixas."""
import io
import random
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from player import AudioPlayer

from . import dialogs, icons, theme
from .tooltip import add_tooltip
from .utils import build_settings_button, ellipsize, format_time

_COVER_SIZE = 110
_THUMB_SIZE = 40
_ORDER_LABELS = [
    ("sequencial", "Sequencial"),
    ("alfabetica", "Alfabética"),
    ("aleatoria", "Aleatória"),
]


class _TrackRow(ctk.CTkFrame):
    """Uma linha da lista de faixas: capa pequena, título/artista, duração e menu."""

    def __init__(self, master, view: "PlaylistDetailView", track_row, position: int):
        super().__init__(master, fg_color=theme.CARD_BG, corner_radius=10, height=56)
        self.grid_propagate(False)
        self.track_id = track_row["id"]
        self.filepath = track_row["filepath"]
        self._view = view
        self._position = position

        self.grid_columnconfigure(1, weight=1)

        meta = AudioPlayer.get_metadata(self.filepath)
        duration = AudioPlayer.get_duration(self.filepath)

        thumb_pil = None
        cover_bytes = AudioPlayer.get_cover_art(self.filepath)
        if cover_bytes:
            try:
                thumb_pil = Image.open(io.BytesIO(cover_bytes)).convert("RGB").resize(
                    (_THUMB_SIZE, _THUMB_SIZE)
                )
            except Exception:
                thumb_pil = None
        if thumb_pil is None:
            thumb_pil = Image.new("RGB", (_THUMB_SIZE, _THUMB_SIZE), theme.BG_PANEL)
        self._thumb_image = ctk.CTkImage(thumb_pil, size=(_THUMB_SIZE, _THUMB_SIZE))
        thumb_label = ctk.CTkLabel(self, image=self._thumb_image, text="")
        thumb_label.grid(row=0, column=0, rowspan=2, padx=(10, 10), pady=6)

        title_label = ctk.CTkLabel(
            self, text=ellipsize(meta["title"], 30), font=ctk.CTkFont(size=13, weight="bold"),
            text_color=theme.TEXT_PRIMARY, anchor="w",
        )
        title_label.grid(row=0, column=1, sticky="ew", pady=(8, 0))

        artist_label = ctk.CTkLabel(
            self, text=ellipsize(meta["artist"], 38), font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_SECONDARY, anchor="w",
        )
        artist_label.grid(row=1, column=1, sticky="ew", pady=(0, 8))

        duration_label = ctk.CTkLabel(
            self, text=format_time(duration), font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY,
        )
        duration_label.grid(row=0, column=2, rowspan=2, padx=(4, 4))

        menu_btn = ctk.CTkButton(
            self, text="⋮", width=26, height=26, corner_radius=13,
            fg_color="transparent", hover_color=theme.CARD_BG_HOVER, text_color=theme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=16), command=self._show_menu,
        )
        icons.apply_icon(menu_btn, "more_vertical", theme.TEXT_SECONDARY, theme.TEXT_PRIMARY, size=16)
        menu_btn.grid(row=0, column=3, rowspan=2, padx=(4, 8))
        add_tooltip(menu_btn, "Remover da playlist")

        for widget in (self, thumb_label, title_label, artist_label, duration_label):
            widget.bind("<Double-Button-1>", self._on_double_click)

    def _on_double_click(self, event) -> None:
        self._view.play_from_track(self._position)

    def _show_menu(self) -> None:
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Remover da playlist", command=lambda: self._view.remove_track(self.track_id))
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        menu.tk_popup(x, y)


class PlaylistDetailView(ctk.CTkFrame):
    """Detalhe de uma playlist: capa, descrição, ordem de reprodução e lista de faixas."""

    def __init__(self, master, app):
        super().__init__(master, fg_color=theme.BG_DARK)
        self.app = app
        self._playlist_id: int | None = None
        self._order_mode: str = "sequencial"
        self._order_buttons: dict[str, ctk.CTkButton] = {}
        self._track_rows: list = []
        self._cover_image = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self._build_topbar()
        self._build_header()
        self._build_order_row()
        self._build_tracks_section()

    # ------------------------------------------------------------------
    # Construção da UI
    # ------------------------------------------------------------------

    def _build_topbar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 4))
        close_btn = ctk.CTkButton(
            bar, text="✕", width=36, height=36, corner_radius=18,
            fg_color=theme.CARD_BG, hover_color=theme.CARD_BG_HOVER, text_color=theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=14), command=self.app.show_playlist_selection,
        )
        icons.apply_icon(close_btn, "close", theme.TEXT_PRIMARY, theme.TEXT_PRIMARY)
        close_btn.pack(side="left")
        add_tooltip(close_btn, "Voltar para playlists")
        ctk.CTkLabel(
            bar, text="Playlist", font=ctk.CTkFont(size=13), text_color=theme.TEXT_SECONDARY,
        ).pack(side="left", padx=(10, 0))
        build_settings_button(bar, self.app).pack(side="right")

    def _build_header(self) -> None:
        card = ctk.CTkFrame(self, fg_color=theme.CARD_BG, corner_radius=16)
        card.grid(row=1, column=0, sticky="ew", padx=20, pady=(8, 8))
        card.grid_columnconfigure(1, weight=1)

        self._cover_label = ctk.CTkLabel(card, text="")
        self._cover_label.grid(row=0, column=0, rowspan=3, padx=16, pady=16)

        self._title_label = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont(size=18, weight="bold"), text_color=theme.TEXT_PRIMARY,
            anchor="w", justify="left",
        )
        self._title_label.grid(row=0, column=1, sticky="ew", padx=(0, 16), pady=(16, 0))

        self._desc_label = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont(size=12), text_color=theme.TEXT_SECONDARY,
            anchor="w", justify="left", wraplength=220,
        )
        self._desc_label.grid(row=1, column=1, sticky="ew", padx=(0, 16))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.grid(row=2, column=1, sticky="w", padx=(0, 16), pady=(8, 16))
        ctk.CTkButton(
            btn_row, text="▶ Tocar", width=100, fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
            command=self._on_play_all,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_row, text="Editar", width=90, fg_color="transparent", border_width=1,
            border_color=theme.TEXT_MUTED, text_color=theme.TEXT_SECONDARY,
            command=self._on_edit_playlist,
        ).pack(side="left")

    def _build_order_row(self) -> None:
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=2, column=0, sticky="ew", padx=20, pady=(4, 8))
        ctk.CTkLabel(
            row, text="Ordem de reprodução", font=ctk.CTkFont(size=12), text_color=theme.TEXT_SECONDARY,
        ).pack(anchor="w")

        seg = ctk.CTkFrame(row, fg_color=theme.CARD_BG, corner_radius=16)
        seg.pack(fill="x", pady=(4, 0))
        for index, (mode, label) in enumerate(_ORDER_LABELS):
            # width=1 (mínimo real): sem isso, CTkButton usa o padrão width=140, que a
            # 150% de escala de tela vira 210px físicos — 3 botões (630px) não cabem
            # nos ~540px físicos disponíveis a 400px de janela, e o pack espremia o
            # último ("Aleatória") a ~78px, cortando o texto. Com width=1 + expand+fill
            # o pack distribui o espaço real disponível igualmente entre os 3.
            padx = (10, 2) if index == 0 else (2, 10) if index == len(_ORDER_LABELS) - 1 else 2
            btn = ctk.CTkButton(
                seg, text=label, width=1, corner_radius=13, height=30,
                fg_color="transparent", text_color=theme.TEXT_SECONDARY, font=ctk.CTkFont(size=11),
                command=lambda m=mode: self._on_set_order_mode(m),
            )
            btn.pack(side="left", expand=True, fill="x", padx=padx, pady=3)
            self._order_buttons[mode] = btn

    def _build_tracks_section(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=3, column=0, sticky="ew", padx=20, pady=(4, 4))
        ctk.CTkLabel(
            header, text="Faixas", font=ctk.CTkFont(size=14, weight="bold"), text_color=theme.TEXT_PRIMARY,
        ).pack(side="left")
        ctk.CTkButton(
            header, text="＋ Adicionar Músicas", height=30, corner_radius=15,
            fg_color=theme.CARD_BG, hover_color=theme.CARD_BG_HOVER, text_color=theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=11), command=self._on_add_tracks,
        ).pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=4, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.scroll.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def on_show(self, playlist_id: int) -> None:
        self._playlist_id = playlist_id
        self._load_playlist()

    def play_from_track(self, position: int) -> None:
        """Toca a partir da faixa clicada, seguindo a mesma ordem mostrada na lista."""
        filepaths = [t["filepath"] for t in self._ordered_tracks()]
        self.app.play_queue(
            filepaths, start_index=position, shuffle=self._order_mode == "aleatoria",
        )

    def remove_track(self, track_id: int) -> None:
        self.app.db.remove_track(track_id)
        self._refresh_tracks()
        self._refresh_cover()

    # ------------------------------------------------------------------
    # Carregamento / atualização
    # ------------------------------------------------------------------

    def _load_playlist(self) -> None:
        playlist = self.app.db.get_playlist(self._playlist_id)
        if playlist is None:
            self.app.show_playlist_selection()
            return
        self._order_mode = playlist["order_mode"]
        self._title_label.configure(text=playlist["name"])
        self._desc_label.configure(text=playlist["description"] or "Sem descrição.")
        self._refresh_order_buttons()
        self._refresh_cover()
        self._refresh_tracks()

    def _refresh_order_buttons(self) -> None:
        for mode, btn in self._order_buttons.items():
            active = mode == self._order_mode
            btn.configure(
                fg_color=theme.ACCENT if active else "transparent",
                text_color=theme.TEXT_PRIMARY if active else theme.TEXT_SECONDARY,
            )

    def _refresh_cover(self) -> None:
        tracks = self.app.db.get_tracks(self._playlist_id)
        cover_pil = None
        if tracks:
            cover_bytes = AudioPlayer.get_cover_art(tracks[0]["filepath"])
            if cover_bytes:
                try:
                    cover_pil = Image.open(io.BytesIO(cover_bytes)).convert("RGB").resize(
                        (_COVER_SIZE, _COVER_SIZE)
                    )
                except Exception:
                    cover_pil = None
        if cover_pil is None:
            cover_pil = Image.new("RGB", (_COVER_SIZE, _COVER_SIZE), theme.CARD_BG_HOVER)
        self._cover_image = ctk.CTkImage(cover_pil, size=(_COVER_SIZE, _COVER_SIZE))
        self._cover_label.configure(image=self._cover_image)

    def _ordered_tracks(self) -> list:
        """Faixas na ordem do modo atual — a mesma ordem da lista exibida e da reprodução.

        "alfabetica" ordena pelo título ID3 (o texto que o usuário vê na lista), não
        pelo nome do arquivo: os dois costumam divergir em arquivos baixados, o que
        fazia a reprodução alfabética parecer fora de ordem. "aleatoria" mantém a
        exibição sequencial; o sorteio acontece só na hora de tocar.
        """
        tracks = list(self.app.db.get_tracks(self._playlist_id))
        if self._order_mode == "alfabetica":
            tracks.sort(
                key=lambda t: AudioPlayer.get_metadata(t["filepath"])["title"].casefold()
            )
        return tracks

    def _refresh_tracks(self) -> None:
        for row in self._track_rows:
            row.destroy()
        self._track_rows = []

        tracks = self._ordered_tracks()
        if not tracks:
            empty = ctk.CTkLabel(
                self.scroll, text="Nenhuma música nesta playlist ainda.",
                font=ctk.CTkFont(size=12), text_color=theme.TEXT_SECONDARY,
            )
            empty.grid(row=0, column=0, pady=20)
            self._track_rows.append(empty)
            return

        for index, track in enumerate(tracks):
            row = _TrackRow(self.scroll, self, track, index)
            row.grid(row=index, column=0, sticky="ew", pady=3)
            self._track_rows.append(row)

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------

    def _on_set_order_mode(self, mode: str) -> None:
        self.app.db.set_order_mode(self._playlist_id, mode)
        self._order_mode = mode
        self._refresh_order_buttons()
        self._refresh_tracks()

    def _on_play_all(self) -> None:
        queue = [t["filepath"] for t in self._ordered_tracks()]
        if not queue:
            messagebox.showinfo("Playlist vazia", "Adicione músicas a esta playlist antes de tocar.")
            return
        shuffle = self._order_mode == "aleatoria"
        if shuffle:
            random.shuffle(queue)
        self.app.play_queue(queue, start_index=0, shuffle=shuffle)

    def _on_add_tracks(self) -> None:
        files = filedialog.askopenfilenames(
            title="Adicionar músicas à playlist", filetypes=[("Arquivos MP3", "*.mp3")],
        )
        if not files:
            return
        for f in files:
            self.app.db.add_track(self._playlist_id, f)
        self._refresh_tracks()
        self._refresh_cover()

    def _on_edit_playlist(self) -> None:
        playlist = self.app.db.get_playlist(self._playlist_id)
        result = dialogs.playlist_form_dialog(
            self.app, "Editar Playlist", ok_label="Salvar",
            initial_name=playlist["name"], initial_description=playlist["description"],
        )
        if not result:
            return
        name, description = result
        try:
            self.app.db.rename_playlist(self._playlist_id, name)
        except ValueError as exc:
            messagebox.showerror("Não foi possível salvar", str(exc))
            return
        self.app.db.update_description(self._playlist_id, description)
        self._load_playlist()
