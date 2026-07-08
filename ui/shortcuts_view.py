"""Tela de atalhos de teclado (somente leitura, baseada em ui/shortcuts.py)."""
import customtkinter as ctk

from version import __version__

from . import icons, theme
from .shortcuts import SHORTCUTS
from .tooltip import add_tooltip


class ShortcutsView(ctk.CTkFrame):
    """Lista os atalhos de teclado disponíveis no Bitswave."""

    def __init__(self, master, app):
        super().__init__(master, fg_color=theme.BG_DARK)
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_topbar()
        self._build_header()
        self._build_list()

    def _build_topbar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 4))
        back_btn = ctk.CTkButton(
            bar, text="←", width=36, height=36, corner_radius=18,
            fg_color=theme.CARD_BG, hover_color=theme.CARD_BG_HOVER, text_color=theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=16), command=self._on_back,
        )
        icons.apply_icon(back_btn, "back", theme.TEXT_PRIMARY, theme.TEXT_PRIMARY)
        back_btn.pack(side="left")
        add_tooltip(back_btn, "Voltar")

    def _build_header(self) -> None:
        box = ctk.CTkFrame(self, fg_color="transparent")
        box.grid(row=1, column=0, sticky="ew", padx=20, pady=(4, 8))
        ctk.CTkLabel(
            box, text="Atalhos de Teclado", font=ctk.CTkFont(size=20, weight="bold"),
            text_color=theme.TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            box, text="Controle o Bitswave sem tirar as mãos do teclado",
            font=ctk.CTkFont(size=12), text_color=theme.TEXT_SECONDARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            box, text=f"Bitswave v{__version__}",
            font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED,
        ).pack(anchor="w", pady=(4, 0))

    def _build_list(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 20))
        scroll.grid_columnconfigure(1, weight=1)

        for index, (combo, description) in enumerate(SHORTCUTS):
            row = ctk.CTkFrame(scroll, fg_color=theme.CARD_BG, corner_radius=10)
            row.grid(row=index, column=0, sticky="ew", padx=4, pady=4)
            row.grid_columnconfigure(1, weight=1)

            badge = ctk.CTkLabel(
                row, text=combo, font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.ACCENT,
                fg_color=theme.BG_PANEL, corner_radius=8, width=100, height=28,
            )
            badge.grid(row=0, column=0, padx=(12, 12), pady=10, sticky="w")

            ctk.CTkLabel(
                row, text=description, font=ctk.CTkFont(size=13), text_color=theme.TEXT_PRIMARY, anchor="w",
            ).grid(row=0, column=1, sticky="ew", padx=(0, 12))

    def on_show(self) -> None:
        pass

    def _on_back(self) -> None:
        self.app.go_back_from_shortcuts()
