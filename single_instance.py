"""Garantia de instância única do Bitswave (Windows e Linux).

Abrir o app várias vezes criaria janelas simultâneas disputando o mesmo banco
SQLite e o mesmo player_config.json (ambos gravados no fechamento -- a última
instância a fechar sobrescreveria as outras). Este módulo obtém um *advisory
lock* do SO sobre um arquivo no diretório de dados do usuário:

- POSIX (Linux/macOS): ``fcntl.flock`` com ``LOCK_EX | LOCK_NB``.
- Windows: ``msvcrt.locking`` com ``LK_NBLCK``.

Em ambos os casos o lock é liberado automaticamente pelo SO quando o processo
termina -- inclusive em caso de crash --, então não sobra lock preso exigindo
limpeza manual (a vantagem sobre checar apenas se um arquivo existe).
"""
import sys

from paths import data_path

_LOCK_FILENAME = "bitswave.lock"

# Mantém o(s) handle(s) abertos pela vida do processo: se o arquivo fosse fechado
# (ou coletado pelo GC), o lock seria liberado e uma segunda instância entraria.
_held_handles: list = []


def _lock_file(path: str):
    """Tenta obter o lock exclusivo do arquivo. Retorna o handle aberto, ou None
    se já estiver travado por outra instância."""
    handle = open(path, "a+")
    handle.seek(0)
    try:
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    return handle


def acquire_single_instance_lock(lock_path: str | None = None) -> bool:
    """Retorna True se esta é a única instância (lock obtido); False se já há outra rodando.

    Se, por algum motivo de ambiente, o arquivo de lock não puder ser aberto/criado,
    falha em modo permissivo (retorna True) -- é preferível abrir o app a impedir seu
    uso por causa do mecanismo de exclusividade.
    """
    if lock_path is None:
        lock_path = data_path(_LOCK_FILENAME)
    try:
        handle = _lock_file(lock_path)
    except OSError:
        return True
    if handle is None:
        return False
    _held_handles.append(handle)
    return True
