"""Resolução de caminhos que funciona tanto rodando de fonte quanto empacotado (PyInstaller).

Empacotado em modo --onefile, o executável se descompacta em uma pasta temporária
nova a cada execução (`sys._MEIPASS`) -- ótimo para assets somente-leitura (ícones,
imagens), mas catastrófico para dados persistentes: gravar o banco de playlists ou
o player_config.json ali faria os dois "resetarem" a cada abertura do programa.
Por isso as duas funções abaixo resolvem para lugares diferentes.
"""
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def is_frozen() -> bool:
    """True quando rodando como executável empacotado (PyInstaller)."""
    return getattr(sys, "frozen", False)


def resource_path(*parts: str) -> str:
    """Caminho para um asset somente-leitura empacotado junto do app (ex: models/icons/*.png)."""
    base = sys._MEIPASS if is_frozen() else _PROJECT_ROOT  # type: ignore[attr-defined]
    return os.path.join(base, *parts)


def user_data_dir(app_name: str = "Bitswave") -> str:
    """Diretório de dados persistentes do usuário, específico da plataforma.

    Usado (só quando empacotado) em vez de "ao lado do executável": essa
    suposição quebra no AppImage do Linux, que roda a partir de um mount
    squashfs somente-leitura (ou de uma pasta de extração temporária recriada
    a cada execução com --appimage-extract-and-run) -- `sys.executable` nesses
    casos nunca aponta para um lugar gravável e estável. Também evita o mesmo
    problema no Windows se o .exe ficar num diretório protegido (ex.: Program
    Files sem elevação) ou em mídia somente-leitura.
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    path = os.path.join(base, app_name)
    os.makedirs(path, exist_ok=True)
    return path


def data_path(*parts: str) -> str:
    """Caminho para um arquivo gravável e persistente entre execuções (banco, config).

    Empacotado, usa o diretório de dados do usuário (ver user_data_dir) --
    nunca a pasta do executável, que pode não ser gravável nem estável.
    Rodando de fonte, fica na raiz do projeto, como antes.
    """
    base = user_data_dir() if is_frozen() else _PROJECT_ROOT
    return os.path.join(base, *parts)
