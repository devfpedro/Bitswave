import sys

from single_instance import acquire_single_instance_lock
from ui import App


def main() -> None:
    if not acquire_single_instance_lock():
        _notify_already_running()
        sys.exit(0)
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


def _notify_already_running() -> None:
    """Avisa que o Bitswave já está aberto e sai, sem abrir uma segunda janela."""
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Bitswave", "O Bitswave já está em execução.")
        root.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    main()
