# Bitswave

Reprodutor de música desktop para Windows, escrito em Python com interface gráfica
em `customtkinter`. Toca MP3 (e outros formatos suportados pelo `pygame.mixer`),
organiza playlists em SQLite, descobre automaticamente músicas novas em pastas
monitoradas (Downloads/Músicas) e exibe um espectro de áudio real (FFT) sincronizado
com a faixa tocando.

## Funcionalidades

- Reprodução com play/pause/stop/seek, volume, aleatório e repetição (desligado /
  playlist / faixa única).
- Playlists persistentes em SQLite, com ordem de reprodução sequencial, alfabética
  ou aleatória.
- Metadados e capa de álbum lidos das tags ID3 (`mutagen`).
- Monitoramento de pastas (Downloads/Músicas por padrão, editável pelo usuário):
  novos arquivos de áudio aparecem automaticamente no painel "Adicionadas
  recentemente".
- Espectro de áudio real: a faixa é decodificada e analisada via FFT em uma thread
  separada; as barras da tela de reprodução seguem a energia por banda de
  frequência da música no instante atual (com fallback decorativo enquanto a
  análise ainda não terminou).
- Atalhos de teclado globais (tela dedicada em "⚙" → Atalhos de Teclado).
- Estado de sessão (fila, volume, pastas monitoradas) salvo em `player_config.json`
  e restaurado ao abrir o app.

## Estrutura do projeto

```
main.py                  # ponto de entrada
player.py                # AudioPlayer: playback (pygame.mixer) + metadados (mutagen)
audio_spectrum.py         # análise de espectro (FFT) usada pela waveform
db.py                     # PlaylistDB: persistência de playlists (SQLite)
folder_watch.py           # descoberta de pastas conhecidas do Windows + varredura de áudio
ui/
  app.py                  # janela principal, navegação entre telas, atalhos globais
  playback_view.py        # tela "Now Playing"
  playlist_selection_view.py
  playlist_detail_view.py
  shortcuts_view.py        # tela de atalhos de teclado
  recent_files_panel.py    # painel "Adicionadas recentemente"
  dialogs.py               # diálogos modais (criar/editar playlist, gerenciar pastas, confirmação)
  waveform.py               # canvas do espectro de áudio
  theme.py / tooltip.py / utils.py / shortcuts.py
models/                    # ícone do app, screenshots, prompts de ícones (ICON_PROMPTS.md)
tests/                     # suíte pytest (player, db)
```

## Rodando localmente

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Para rodar os testes:

```
pip install -r requirements-dev.txt
pytest
```

## Notas de plataforma

O monitoramento automático de pastas (`folder_watch.py`) usa a API `SHGetKnownFolderPath`
do Windows para localizar Downloads/Músicas do usuário — é específico para Windows.
