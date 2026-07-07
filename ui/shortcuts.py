"""Fonte única dos atalhos de teclado do Bitswave.

Usado hoje apenas como documentação e para os bindings em ui/app.py._bind_shortcuts.
Pensado para futuramente alimentar uma tela de atalhos dentro do próprio app.
"""

SHORTCUTS = [
    ("Espaço", "Reproduzir / Pausar"),
    ("←", "Retroceder 5 segundos"),
    ("→", "Avançar 5 segundos"),
    ("Ctrl + ←", "Próxima música"),
    ("Ctrl + →", "Música anterior"),
    ("↑", "Aumentar volume"),
    ("↓", "Diminuir volume"),
    ("Ctrl + R", "Ativar/desativar reprodução aleatória"),
    ("Ctrl + S", "Abrir seleção de playlists"),
    ("Ctrl + O", "Abrir seletor de músicas manual"),
]
