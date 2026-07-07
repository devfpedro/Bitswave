"""Tooltip leve para botões de ícone (mostra uma frase curta ao passar o mouse)."""
import tkinter as tk

from . import theme


class _Tooltip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tipwindow: tk.Toplevel | None = None
        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _show(self, event=None) -> None:
        if self.tipwindow is not None or not self.text:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6

        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        label = tk.Label(
            tw, text=self.text, justify="left", background=theme.CARD_BG_HOVER,
            foreground=theme.TEXT_PRIMARY, relief="solid", borderwidth=1,
            font=("Segoe UI", 10), padx=10, pady=6,
        )
        label.pack()
        tw.update_idletasks()
        width = tw.winfo_width()
        tw.wm_geometry(f"+{max(x - width // 2, 0)}+{y}")
        self.tipwindow = tw

    def _hide(self, event=None) -> None:
        if self.tipwindow is not None:
            self.tipwindow.destroy()
            self.tipwindow = None


def add_tooltip(widget, text: str) -> None:
    """Anexa um tooltip simples a um widget, exibido ao pairar o mouse sobre ele."""
    _Tooltip(widget, text)
