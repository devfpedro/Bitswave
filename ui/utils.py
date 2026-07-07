"""Funções utilitárias compartilhadas entre as views."""
import customtkinter as ctk

from . import icons, theme
from .tooltip import add_tooltip


def format_time(seconds: float) -> str:
    """Formata segundos para MM:SS."""
    if seconds < 0:
        seconds = 0
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def ellipsize(text: str, max_chars: int) -> str:
    """Trunca com reticências: labels do customtkinter não cortam nem quebram sozinhos,
    então textos longos (títulos de músicas) estouravam a largura da janela."""
    return text if len(text) <= max_chars else text[: max_chars - 1].rstrip() + "…"


def build_settings_button(container: ctk.CTkFrame, app) -> ctk.CTkButton:
    """Botão de engrenagem que abre a tela de atalhos.

    Fica dentro da topbar de cada tela (o chamador decide o pack/grid) em vez de
    flutuar por cima do conteúdo com `.place()`: um overlay fixo no canto inferior
    ficava por cima das listas roláveis (o `fg_color="transparent"` só reproduz a cor
    de fundo do próprio botão, não deixa ver o que está atrás dele na pilha de widgets),
    cobrindo texto de faixas/itens conforme a lista crescia. Encaixado na topbar, o
    espaço dele nunca se sobrepõe ao conteúdo rolável abaixo, em qualquer tamanho de janela.
    """
    btn = ctk.CTkButton(
        container, text="⚙", width=36, height=36, corner_radius=18,
        fg_color="transparent", hover_color=theme.CARD_BG_HOVER, text_color=theme.TEXT_SECONDARY,
        font=ctk.CTkFont(size=16), command=app.show_shortcuts,
    )
    icons.apply_icon(btn, "settings", theme.TEXT_SECONDARY, theme.TEXT_PRIMARY)
    add_tooltip(btn, "Atalhos de teclado")
    return btn
