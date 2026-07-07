"""Diálogos modais reutilizáveis (criar/editar playlist, confirmação)."""
from tkinter import filedialog

import customtkinter as ctk

from . import icons, theme
from .utils import ellipsize


class _ModalDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str):
        super().__init__(parent)
        self.title(title)
        self.configure(fg_color=theme.BG_DARK)
        self.resizable(False, False)
        self.transient(parent)
        self.result = None
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda e: self._on_cancel())

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()

    def _center_on_parent(self) -> None:
        self.update_idletasks()
        parent = self.master
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h = self.winfo_width(), self.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def run(self):
        self._center_on_parent()
        self.grab_set()
        self.focus_force()
        self.wait_window()
        return self.result


def _build_button_row(dialog, on_ok, ok_label: str = "Salvar") -> None:
    row = ctk.CTkFrame(dialog, fg_color="transparent")
    row.pack(fill="x", padx=20, pady=(4, 20), side="bottom")
    ctk.CTkButton(
        row, text="Cancelar", width=100, fg_color="transparent", border_width=1,
        border_color=theme.TEXT_MUTED, text_color=theme.TEXT_SECONDARY,
        command=dialog._on_cancel,
    ).pack(side="right", padx=(8, 0))
    ctk.CTkButton(
        row, text=ok_label, width=100, fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
        command=on_ok,
    ).pack(side="right")


def playlist_form_dialog(
    parent, title: str, ok_label: str = "Salvar",
    initial_name: str = "", initial_description: str = "",
):
    """Formulário modal com campos Nome e Descrição. Retorna (nome, descrição) ou None se cancelado."""
    dialog = _ModalDialog(parent, title)
    dialog.geometry("380x300")

    ctk.CTkLabel(
        dialog, text=title, font=ctk.CTkFont(size=16, weight="bold"), text_color=theme.TEXT_PRIMARY,
    ).pack(padx=20, pady=(20, 12), anchor="w")

    ctk.CTkLabel(
        dialog, text="Nome da playlist", font=ctk.CTkFont(size=12), text_color=theme.TEXT_SECONDARY,
    ).pack(padx=20, anchor="w")
    name_entry = ctk.CTkEntry(dialog, placeholder_text="Ex: Rock dos anos 80")
    name_entry.pack(fill="x", padx=20, pady=(2, 12))
    name_entry.insert(0, initial_name)

    ctk.CTkLabel(
        dialog, text="Descrição (opcional)", font=ctk.CTkFont(size=12), text_color=theme.TEXT_SECONDARY,
    ).pack(padx=20, anchor="w")
    desc_entry = ctk.CTkEntry(dialog, placeholder_text="Uma frase sobre a playlist")
    desc_entry.pack(fill="x", padx=20, pady=(2, 8))
    desc_entry.insert(0, initial_description)

    error_label = ctk.CTkLabel(dialog, text="", text_color=theme.DANGER, font=ctk.CTkFont(size=11))
    error_label.pack(padx=20, anchor="w")

    def on_ok() -> None:
        name = name_entry.get().strip()
        if not name:
            error_label.configure(text="Informe um nome para a playlist.")
            return
        dialog.result = (name, desc_entry.get().strip())
        dialog.destroy()

    _build_button_row(dialog, on_ok, ok_label)
    name_entry.bind("<Return>", lambda e: on_ok())
    name_entry.focus_set()
    return dialog.run()


def simple_prompt(parent, title: str, label: str, initial: str = "") -> str | None:
    """Formulário modal com um único campo de texto. Retorna o texto ou None se cancelado."""
    dialog = _ModalDialog(parent, title)
    dialog.geometry("360x200")

    ctk.CTkLabel(
        dialog, text=title, font=ctk.CTkFont(size=16, weight="bold"), text_color=theme.TEXT_PRIMARY,
    ).pack(padx=20, pady=(20, 12), anchor="w")
    ctk.CTkLabel(
        dialog, text=label, font=ctk.CTkFont(size=12), text_color=theme.TEXT_SECONDARY,
    ).pack(padx=20, anchor="w")
    entry = ctk.CTkEntry(dialog)
    entry.pack(fill="x", padx=20, pady=(2, 8))
    entry.insert(0, initial)

    error_label = ctk.CTkLabel(dialog, text="", text_color=theme.DANGER, font=ctk.CTkFont(size=11))
    error_label.pack(padx=20, anchor="w")

    def on_ok() -> None:
        value = entry.get().strip()
        if not value:
            error_label.configure(text="Este campo não pode ficar vazio.")
            return
        dialog.result = value
        dialog.destroy()

    _build_button_row(dialog, on_ok)
    entry.bind("<Return>", lambda e: on_ok())
    entry.focus_set()
    return dialog.run()


def confirm(parent, title: str, message: str, danger: bool = False) -> bool:
    """Diálogo de confirmação Sim/Não. Retorna True se confirmado."""
    dialog = _ModalDialog(parent, title)
    dialog.geometry("360x180")
    dialog.result = False

    ctk.CTkLabel(
        dialog, text=title, font=ctk.CTkFont(size=16, weight="bold"), text_color=theme.TEXT_PRIMARY,
    ).pack(padx=20, pady=(20, 8), anchor="w")
    ctk.CTkLabel(
        dialog, text=message, font=ctk.CTkFont(size=13), text_color=theme.TEXT_SECONDARY,
        wraplength=320, justify="left",
    ).pack(padx=20, anchor="w")

    def on_confirm() -> None:
        dialog.result = True
        dialog.destroy()

    row = ctk.CTkFrame(dialog, fg_color="transparent")
    row.pack(fill="x", padx=20, pady=(16, 20), side="bottom")
    ctk.CTkButton(
        row, text="Cancelar", width=100, fg_color="transparent", border_width=1,
        border_color=theme.TEXT_MUTED, text_color=theme.TEXT_SECONDARY,
        command=dialog._on_cancel,
    ).pack(side="right", padx=(8, 0))
    confirm_color = theme.DANGER if danger else theme.ACCENT
    confirm_hover = theme.DANGER_HOVER if danger else theme.ACCENT_HOVER
    ctk.CTkButton(
        row, text="Confirmar", width=100, fg_color=confirm_color, hover_color=confirm_hover,
        command=on_confirm,
    ).pack(side="right")

    return dialog.run()


def manage_folders_dialog(parent, folders: list[str]) -> list[str] | None:
    """Diálogo para gerenciar as pastas monitoradas para adição automática de músicas.

    Retorna a lista atualizada de pastas ao salvar, ou None se cancelado.
    """
    dialog = _ModalDialog(parent, "Pastas Monitoradas")
    dialog.geometry("420x380")
    current = list(folders)

    ctk.CTkLabel(
        dialog, text="Pastas Monitoradas", font=ctk.CTkFont(size=16, weight="bold"),
        text_color=theme.TEXT_PRIMARY,
    ).pack(padx=20, pady=(20, 4), anchor="w")
    ctk.CTkLabel(
        dialog,
        text='Novos arquivos de áudio nessas pastas aparecem automaticamente em "Adicionadas recentemente".',
        font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY, wraplength=380, justify="left",
    ).pack(padx=20, pady=(0, 10), anchor="w")

    list_frame = ctk.CTkScrollableFrame(dialog, fg_color=theme.CARD_BG, height=160)
    list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 8))
    list_frame.grid_columnconfigure(0, weight=1)

    def _remove(folder: str) -> None:
        current.remove(folder)
        _render_rows()

    def _render_rows() -> None:
        for widget in list_frame.winfo_children():
            widget.destroy()
        if not current:
            ctk.CTkLabel(
                list_frame, text="Nenhuma pasta monitorada.", font=ctk.CTkFont(size=12),
                text_color=theme.TEXT_SECONDARY,
            ).grid(row=0, column=0, pady=16)
            return
        for i, folder in enumerate(current):
            row = ctk.CTkFrame(list_frame, fg_color="transparent")
            row.grid(row=i, column=0, sticky="ew", pady=2)
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                row, text=ellipsize(folder, 42), font=ctk.CTkFont(size=12),
                text_color=theme.TEXT_PRIMARY, anchor="w",
            ).grid(row=0, column=0, sticky="ew", padx=(4, 8))
            remove_btn = ctk.CTkButton(
                row, text="✕", width=26, height=26, corner_radius=13,
                fg_color="transparent", hover_color=theme.CARD_BG_HOVER, text_color=theme.DANGER,
                font=ctk.CTkFont(size=12), command=lambda f=folder: _remove(f),
            )
            icons.apply_icon(remove_btn, "remove", theme.DANGER, theme.DANGER_HOVER, size=16)
            remove_btn.grid(row=0, column=1)

    def _add_folder() -> None:
        chosen = filedialog.askdirectory(title="Selecionar pasta para monitorar", parent=dialog)
        if chosen and chosen not in current:
            current.append(chosen)
            _render_rows()

    ctk.CTkButton(
        dialog, text="＋ Adicionar Pasta", height=34, corner_radius=17,
        fg_color=theme.CARD_BG, hover_color=theme.CARD_BG_HOVER, text_color=theme.TEXT_PRIMARY,
        font=ctk.CTkFont(size=12), command=_add_folder,
    ).pack(padx=20, pady=(0, 8), anchor="w")

    def on_ok() -> None:
        dialog.result = list(current)
        dialog.destroy()

    _render_rows()
    _build_button_row(dialog, on_ok, "Salvar")
    return dialog.run()
