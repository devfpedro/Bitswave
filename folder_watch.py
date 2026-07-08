"""Descoberta das pastas Downloads/Músicas do usuário e varredura por arquivos de áudio.

Multiplataforma: no Windows resolve as *Known Folders* (respeita pastas movidas pelo
usuário) via shell32; em Linux/BSD usa `xdg-user-dir`. Em ambos, cai para
``~/Downloads`` e ``~/Music`` se a resolução específica da plataforma falhar.
"""
import os
import sys

AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}


if sys.platform == "win32":
    import ctypes
    import uuid
    from ctypes import wintypes

    _FOLDERID_DOWNLOADS = "{374DE290-123F-4565-9164-39C4925E467B}"
    _FOLDERID_MUSIC = "{4BD8D571-6D19-48D3-BE97-422220080E43}"

    class _GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", ctypes.c_byte * 8),
        ]

        def __init__(self, guid_str: str):
            super().__init__()
            u = uuid.UUID(guid_str)
            self.Data1, self.Data2, self.Data3 = u.fields[0], u.fields[1], u.fields[2]
            for i, byte in enumerate(u.bytes[8:]):
                self.Data4[i] = byte

    def _known_folder_path(guid_str: str) -> str | None:
        """Resolve uma Known Folder do Windows (respeita pastas movidas pelo usuário)."""
        try:
            guid = _GUID(guid_str)
            path_ptr = ctypes.c_wchar_p()
            result = ctypes.windll.shell32.SHGetKnownFolderPath(  # type: ignore[attr-defined]
                ctypes.byref(guid), 0, 0, ctypes.byref(path_ptr)
            )
            if result != 0 or not path_ptr.value:
                return None
            path = path_ptr.value
            ctypes.windll.ole32.CoTaskMemFree(path_ptr)  # type: ignore[attr-defined]
            return path
        except Exception:
            return None

    def _resolve_platform_folders() -> list[tuple[str | None, str]]:
        return [
            (_known_folder_path(_FOLDERID_DOWNLOADS), "Downloads"),
            (_known_folder_path(_FOLDERID_MUSIC), "Music"),
        ]

else:
    def _xdg_user_dir(name: str) -> str | None:
        """Resolve uma pasta de usuário XDG (Linux/BSD) via `xdg-user-dir`, se disponível."""
        try:
            import subprocess

            out = subprocess.run(
                ["xdg-user-dir", name], capture_output=True, text=True, timeout=2
            ).stdout.strip()
            return out or None
        except Exception:
            return None

    def _resolve_platform_folders() -> list[tuple[str | None, str]]:
        return [
            (_xdg_user_dir("DOWNLOAD"), "Downloads"),
            (_xdg_user_dir("MUSIC"), "Music"),
        ]


def default_watch_folders() -> list[str]:
    """Pastas monitoradas por padrão: Downloads e Músicas do usuário atual."""
    home = os.path.expanduser("~")
    fallbacks = {"Downloads": os.path.join(home, "Downloads"), "Music": os.path.join(home, "Music")}

    folders: list[str] = []
    for resolved, key in _resolve_platform_folders():
        path = resolved or fallbacks[key]
        if path and os.path.isdir(path) and path not in folders:
            folders.append(path)
    return folders


def resolve_saved_folders(config: dict, defaults: list[str]) -> list[str]:
    """Decide as pastas monitoradas a partir da configuração salva.

    Regra: a adição automática de Downloads/Músicas só vale enquanto o usuário
    nunca configurou nada. A chave ``watch_folders`` no config é criada assim que
    ele abre/salva o gerenciador de pastas; a partir daí ela é a preferência
    explícita e vence -- **inclusive quando vazia** (o usuário removeu todas).
    É essa distinção entre "chave ausente" e "lista vazia" que impede as pastas
    removidas de reaparecerem sozinhas. Caminhos que não existem mais são
    descartados para não sujar a lista.
    """
    saved = config.get("watch_folders")
    if isinstance(saved, list):
        return [f for f in saved if isinstance(f, str) and os.path.isdir(f)]
    return list(defaults)


class FolderWatcher:
    """Mantém uma lista de pastas e varre-as por arquivos de áudio (não recursivo)."""

    def __init__(self, folders: list[str] | None = None):
        self.folders: list[str] = list(folders) if folders else []

    def add_folder(self, path: str) -> bool:
        path = os.path.normpath(path)
        if os.path.isdir(path) and path not in self.folders:
            self.folders.append(path)
            return True
        return False

    def remove_folder(self, path: str) -> None:
        path = os.path.normpath(path)
        if path in self.folders:
            self.folders.remove(path)

    def scan(self, limit: int = 30) -> list[str]:
        """Retorna os arquivos de áudio das pastas monitoradas, mais recentes primeiro.

        "Mais recente" usa o mais tardio entre `st_ctime` (data de criação do arquivo
        *neste disco*, no Windows) e `st_mtime` (última modificação do conteúdo).
        Só mtime não bastava: copiar/baixar um arquivo costuma preservar o mtime
        original (data de quando o conteúdo foi criado, não de quando chegou aqui) --
        uma pasta de música inteira migrada para a máquina em um único dia aparecia
        "antiga" no painel, atrás de poucos arquivos com mtime coincidentemente mais
        recente, mesmo tendo chegado à pasta monitorada há muito mais tempo.
        """
        found: dict[str, float] = {}
        for folder in self.folders:
            try:
                with os.scandir(folder) as entries:
                    for entry in entries:
                        if not entry.is_file():
                            continue
                        ext = os.path.splitext(entry.name)[1].lower()
                        if ext not in AUDIO_EXTENSIONS:
                            continue
                        try:
                            stat = entry.stat()
                        except OSError:
                            continue
                        found[entry.path] = max(stat.st_ctime, stat.st_mtime)
            except OSError:
                continue
        ordered = sorted(found.items(), key=lambda item: item[1], reverse=True)
        return [path for path, _ in ordered[:limit]]
