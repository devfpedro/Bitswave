"""Funções utilitárias compartilhadas entre as views."""
import customtkinter as ctk

from . import theme
from .tooltip import add_tooltip


def format_time(seconds: float) -> str:
    """Formata segundos para MM:SS."""
    if seconds < 0:
        seconds = 0
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def add_settings_button(view: ctk.CTkFrame, app) -> ctk.CTkButton:
    """Ícone de engrenagem fixo no canto inferior esquerdo, abre a tela de atalhos.

    Sem fundo (apenas o glifo) para não cobrir visualmente o conteúdo das listas
    roláveis que ficam por baixo dele; o hover_color ainda dá feedback ao passar o mouse.
    """
    btn = ctk.CTkButton(
        view, text="⚙", width=36, height=36, corner_radius=18,
        fg_color="transparent", hover_color=theme.CARD_BG_HOVER, text_color=theme.TEXT_SECONDARY,
        font=ctk.CTkFont(size=16), command=app.show_shortcuts,
    )
    btn.place(relx=0.0, rely=1.0, x=16, y=-16, anchor="sw")
    btn.lift()
    add_tooltip(btn, "Atalhos de teclado")
    return btn
