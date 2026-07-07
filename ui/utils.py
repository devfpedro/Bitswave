"""Funções utilitárias compartilhadas entre as views."""


def format_time(seconds: float) -> str:
    """Formata segundos para MM:SS."""
    if seconds < 0:
        seconds = 0
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"
