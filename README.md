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
  (pelo título da tag ID3, não pelo nome do arquivo) ou aleatória — a lista exibida,
  o clique duplo numa faixa e o botão "▶ Tocar" respeitam sempre o mesmo modo escolhido.
- Metadados e capa de álbum lidos das tags ID3 (`mutagen`).
- Monitoramento de pastas (Downloads/Músicas por padrão, editável pelo usuário):
  novos arquivos de áudio aparecem automaticamente no painel "Adicionadas
  recentemente".
- Espectro de áudio real: a faixa é decodificada e analisada via FFT em uma thread
  separada; as barras da tela de reprodução seguem a energia por banda de
  frequência da música no instante atual (com fallback decorativo enquanto a
  análise ainda não terminou).
- Conjunto de ícones próprio (`models/icons/`) com estado de hover, substituindo
  emojis/glifos de texto nos botões; títulos, artistas e caminhos longos são
  truncados com reticências para nunca estourar a largura da janela.
- Atalhos de teclado globais (tela dedicada em "⚙" → Atalhos de Teclado):

  | Atalho | Ação |
  |---|---|
  | `Espaço` | Reproduzir / Pausar |
  | `←` / `→` | Retroceder / avançar 5 segundos |
  | `Ctrl` + `←` / `→` | Próxima música / música anterior |
  | `↑` / `↓` | Aumentar / diminuir volume |
  | `Ctrl + R` | Ativar/desativar reprodução aleatória |
  | `Ctrl + S` | Abrir seleção de playlists |
  | `Ctrl + O` | Abrir seletor de músicas manual |

- Estado de sessão (fila, volume, pastas monitoradas) salvo em `player_config.json`
  e restaurado ao abrir o app.

## Estrutura do projeto

```
main.py                    # ponto de entrada
paths.py                   # resolve caminhos de asset (somente-leitura) vs. dados (graváveis),
                            # necessário para o .exe empacotado funcionar corretamente
player.py                  # AudioPlayer: playback (pygame.mixer) + metadados (mutagen)
audio_spectrum.py          # análise de espectro (FFT) usada pela waveform
db.py                       # PlaylistDB: persistência de playlists (SQLite)
folder_watch.py             # descoberta de pastas conhecidas do Windows + varredura de áudio
Bitswave.spec               # receita do PyInstaller para gerar o .exe
ui/
  app.py                    # janela principal, navegação entre telas, atalhos globais
  playback_view.py          # tela "Now Playing"
  playlist_selection_view.py
  playlist_detail_view.py
  shortcuts_view.py          # tela de atalhos de teclado
  shortcuts.py                # fonte única da lista de atalhos (usada pela tela e pelos bindings)
  recent_files_panel.py      # painel "Adicionadas recentemente"
  dialogs.py                 # diálogos modais (criar/editar playlist, gerenciar pastas, confirmação)
  icons.py                   # normaliza os PNGs de models/icons/ em CTkImage temáticos, com cache e hover
  waveform.py                 # canvas do espectro de áudio
  theme.py / tooltip.py / utils.py
models/
  icons/                     # ícones do app (PNG) + iconApp.ico/png
  ICON_PROMPTS.md            # prompts usados para gerar os ícones via IA
  prints/                    # screenshots de QA (fora do controle de versão, ver .gitignore)
tests/                       # suíte pytest (player, db)
```

## Instalação

**Executável (recomendado para uso normal):** baixe `Bitswave.exe` na aba
[Releases](https://github.com/devfpedro/Bitswave/releases) do GitHub e rode —
não precisa de Python instalado. Na primeira execução o Windows Defender
SmartScreen pode avisar que é um app de "editor desconhecido" (não é
assinado digitalmente); clique em "Mais informações" → "Executar assim mesmo".

**A partir do código-fonte (para desenvolver):**

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

Para gerar o `.exe` você mesmo:

```
pip install pyinstaller
pyinstaller Bitswave.spec
```

O resultado fica em `dist/Bitswave.exe` (o `.spec` já inclui o ícone e os
assets de `models/icons/` e da `customtkinter`).

### Espaço em disco necessário

| Método | Instalado (em repouso) | Durante a execução |
|---|---|---|
| `.exe` (Releases) | ~44 MB | +~85 MB temporários em `%TEMP%` (a build `--onefile` se autoextrai a cada abertura); liberados ao fechar o app normalmente |
| Código-fonte + venv | ~6 MB (código) + ~150 MB (dependências Python) | sem uso extra de `%TEMP%` |

O `.exe` some com a pasta temporária de ~85MB ao fechar a janela normalmente.
Se o processo for encerrado à força (Gerenciador de Tarefas, queda de energia),
essa pasta pode ficar para trás em `%TEMP%\_MEI*` e se acumular a cada crash —
seguro de apagar manualmente se notar acúmulo. Nenhum dos dois métodos conta o
espaço da sua biblioteca de música em si, que não é copiada pelo app (as
faixas continuam nas pastas originais do usuário).

## Notas de plataforma

- O monitoramento automático de pastas (`folder_watch.py`) usa a API
  `SHGetKnownFolderPath` do Windows para localizar Downloads/Músicas do usuário —
  é específico para Windows.
- A interface foi calibrada para Windows com escala de DPI de até 150%; em telas
  com escala maior, o layout de dois blocos de controles (modo / transporte) e o
  truncamento de texto evitam cortes, mas não foi testado acima desse valor.

## Limitações conhecidas

- Os menus de contexto ("⋮" nas faixas e nos cards de playlist) usam `tk.Menu`
  nativo do Windows, então aparecem no tema claro padrão do sistema em vez do
  tema escuro do app.
- `models/prints/` (screenshots de QA) e o cache local do `graphify` não são
  versionados (ver `.gitignore`); os demais arquivos em `models/` (ícones e
  prompts) fazem parte do repositório.
