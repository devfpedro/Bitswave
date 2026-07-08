"""Descoberta de pastas conhecidas do Windows e varredura por novos arquivos de áudio."""
import ctypes
import os
import uuid
from ctypes import wintypes

AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}

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


def default_watch_folders() -> list[str]:
    """Pastas monitoradas por padrão: Downloads e Músicas do usuário atual."""
    downloads = _known_folder_path(_FOLDERID_DOWNLOADS) or os.path.join(
        os.path.expanduser("~"), "Downloads"
    )
    music = _known_folder_path(_FOLDERID_MUSIC) or os.path.join(os.path.expanduser("~"), "Music")

    folders = []
    for folder in (downloads, music):
        if folder and os.path.isdir(folder) and folder not in folders:
            folders.append(folder)
    return folders


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
