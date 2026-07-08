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


def data_path(*parts: str) -> str:
    """Caminho para um arquivo gravável e persistente entre execuções (banco, config).

    Empacotado, fica ao lado do .exe (não dentro da pasta temporária de extração);
    rodando de fonte, fica na raiz do projeto -- igual ao comportamento anterior.
    """
    base = os.path.dirname(os.path.abspath(sys.executable)) if is_frozen() else _PROJECT_ROOT
    return os.path.join(base, *parts)
