"""Painel "Adicionadas recentemente": lista arquivos de áudio das pastas monitoradas."""
import customtkinter as ctk

from player import AudioPlayer

from . import dialogs, icons, theme
from .tooltip import add_tooltip
from .utils import ellipsize

_SCAN_INTERVAL_MS = 8000
_MAX_VISIBLE = 8


class RecentFilesPanel(ctk.CTkFrame):
    """Painel retrátil com os arquivos de áudio mais recentes das pastas monitoradas."""

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._expanded = False
        self._last_scan: list[str] = []
        self._row_widgets: list = []

        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_list()
        self._collapse()

        self._schedule_scan()

    _LABEL = "Adicionadas recentemente"

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        self._img_chevron_down = icons.get("chevron_down", 16, theme.TEXT_SECONDARY)
        self._img_chevron_up = icons.get("chevron_up", 16, theme.TEXT_SECONDARY)

        self.toggle_btn = ctk.CTkButton(
            header, text="⌄  " + self._LABEL, anchor="w", fg_color="transparent",
            hover_color=theme.CARD_BG_HOVER, text_color=theme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=12), height=28, command=self._on_toggle_expanded,
        )
        self.toggle_btn.grid(row=0, column=0, sticky="ew")
        self._set_toggle_icon(expanded=False)

        folders_btn = ctk.CTkButton(
            header, text="📁", width=28, height=28, corner_radius=14,
            fg_color="transparent", hover_color=theme.CARD_BG_HOVER, text_color=theme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=13), command=self._on_manage_folders,
        )
        icons.apply_icon(folders_btn, "folder", theme.TEXT_SECONDARY, theme.TEXT_PRIMARY, size=16)
        folders_btn.grid(row=0, column=1, padx=(4, 0))
        add_tooltip(folders_btn, "Gerenciar pastas monitoradas")

    def _set_toggle_icon(self, expanded: bool) -> None:
        img = self._img_chevron_up if expanded else self._img_chevron_down
        if img is not None:
            self.toggle_btn.configure(image=img, text="  " + self._LABEL, compound="left")
        else:
            prefix = "⌃" if expanded else "⌄"
            self.toggle_btn.configure(text=f"{prefix}  {self._LABEL}")

    def _build_list(self) -> None:
        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color=theme.CARD_BG, corner_radius=10, height=108,
        )
        self.list_frame.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.list_frame.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # Expandir / recolher
    # ------------------------------------------------------------------

    def _on_toggle_expanded(self) -> None:
        self._expand() if not self._expanded else self._collapse()

    def _collapse(self) -> None:
        self._expanded = False
        self.list_frame.grid_remove()
        self._set_toggle_icon(expanded=False)

    def _expand(self) -> None:
        self._expanded = True
        self.list_frame.grid()
        self._set_toggle_icon(expanded=True)
        self._render_rows()

    # ------------------------------------------------------------------
    # Pastas monitoradas
    # ------------------------------------------------------------------

    def _on_manage_folders(self) -> None:
        updated = dialogs.manage_folders_dialog(self.app, self.app.folder_watcher.folders)
        if updated is None:
            return
        self.app.folder_watcher.folders = updated
        # Persiste na hora: a preferência (inclusive uma lista esvaziada) precisa sobreviver
        # mesmo que o app seja encerrado sem o fechamento limpo que dispara save_state().
        self.app.playback_view.save_state()
        self._last_scan = []
        self._render_rows()

    # ------------------------------------------------------------------
    # Varredura periódica
    # ------------------------------------------------------------------

    def _schedule_scan(self) -> None:
        self._rescan()
        self.after(_SCAN_INTERVAL_MS, self._schedule_scan)

    def _rescan(self) -> None:
        found = self.app.folder_watcher.scan(limit=_MAX_VISIBLE)
        if found != self._last_scan:
            self._last_scan = found
            if self._expanded:
                self._render_rows()

    def _render_rows(self) -> None:
        for widget in self._row_widgets:
            widget.destroy()
        self._row_widgets = []

        if not self._last_scan:
            empty = ctk.CTkLabel(
                self.list_frame, text="Nenhum arquivo encontrado nas pastas monitoradas.",
                font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY,
            )
            empty.grid(row=0, column=0, pady=12)
            self._row_widgets.append(empty)
            return

        for index, filepath in enumerate(self._last_scan):
            meta = AudioPlayer.get_metadata(filepath)
            row = ctk.CTkButton(
                self.list_frame, text=ellipsize(f"{meta['title']}  —  {meta['artist']}", 52),
                anchor="w", fg_color="transparent", hover_color=theme.CARD_BG_HOVER,
                text_color=theme.TEXT_PRIMARY, font=ctk.CTkFont(size=12), height=30,
                command=lambda i=index: self._on_play_recent(i),
            )
            row.grid(row=index, column=0, sticky="ew", padx=4, pady=1)
            self._row_widgets.append(row)

    def _on_play_recent(self, index: int) -> None:
        self.app.play_queue(list(self._last_scan), start_index=index)
