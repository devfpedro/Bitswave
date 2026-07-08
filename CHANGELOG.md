# Changelog

Todas as mudanças notáveis do Bitswave são documentadas aqui.
O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e o projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.0.3] - 2026-07-08

### Fixed
- **Múltiplas instâncias simultâneas** (Windows e Linux): era possível abrir o Bitswave
  várias vezes, com janelas concorrentes disputando o mesmo banco SQLite e o mesmo
  `player_config.json` (gravado no fechamento — a última instância a fechar sobrescrevia
  as outras). Agora um *advisory lock* do SO (`fcntl.flock` no Linux, `msvcrt.locking` no
  Windows) garante instância única; abrir uma segunda vez apenas avisa "O Bitswave já está
  em execução" e encerra. O lock é liberado automaticamente pelo SO ao fim do processo,
  sem sobrar arquivo preso após um crash.

### Docs
- README com passo a passo de execução no Linux, incluindo como marcar o AppImage como
  executável (via terminal com `chmod +x` e pelo gerenciador de arquivos) e a nota de
  `libfuse2`.

## [1.0.2] - 2026-07-08

### Fixed
- **Crash ao abrir o AppImage no Linux** (`sqlite3.OperationalError: unable to open
  database file`): `data_path()` resolvia dados persistentes (banco de playlists,
  config) para a pasta do executável, que no AppImage é um mount squashfs
  somente-leitura (ou uma pasta de extração temporária recriada a cada execução).
  Agora usa o diretório de dados do usuário específico da plataforma —
  `%LOCALAPPDATA%\Bitswave` no Windows, `$XDG_DATA_HOME/Bitswave` (ou
  `~/.local/share/Bitswave`) no Linux — o que também protege o Windows do mesmo
  tipo de falha em diretórios sem permissão de escrita (ex.: Program Files sem
  elevação).

## [1.0.1] - 2026-07-08

### Added
- **Suporte a Linux via AppImage** (T8): novo `packaging/linux/` com script de build
  (`build_appimage.sh`), entrada `.desktop` e ícone. Gera um `Bitswave-x86_64.AppImage`
  executável por duplo-clique, com ícone e menu, sem instalação nem root. Descoberta de
  pastas Downloads/Músicas agora é multiplataforma (`xdg-user-dir` no Linux).
- **CI de build Linux** (`.github/workflows/build-linux.yml`): constrói o AppImage num
  Ubuntu fixo (glibc estável), faz smoke test sob display virtual (xvfb) e anexa o
  binário ao Release ao publicá-lo. Roda também sob demanda (workflow_dispatch).
- **Playlist temporária por seleção múltipla** (T7): o botão "＋" agora aceita vários
  arquivos de uma vez e os reproduz em sequência como uma playlist não salva, sem limite
  de faixas. Uma nova seleção — ou iniciar uma playlist salva — descarta a fila anterior.
- **Tooltip no botão de remover pasta** (T5): passar o mouse sobre o "✕" das pastas
  monitoradas explica a ação ("Remover esta pasta da busca automática de músicas recentes").
- Versão do app exibida na tela de Atalhos e centralizada em `version.py`.

### Fixed
- **Espectro de áudio com travamentos** (T1): a posição que indexa o quadro do espectro
  (quadros de ~80 ms) só era amostrada no loop de 200 ms, fazendo as barras avançarem a
  ~5 fps. Agora um tick dedicado de 50 ms alimenta a posição e o canvas redesenha a 20 fps
  (medido: ~5 → ~19 atualizações/s).
- **Ícone da barra de título desproporcional** (T2): `iconApp.png` era 666×375 (paisagem)
  e era esticado para o slot quadrado, achatando o logo numa tira vertical. Regenerado
  como PNG quadrado 409×409 com o logo centrado.
- **Ícone do executável na barra de tarefas** (T3): `iconApp.ico` regenerado a partir do
  logo quadrado, com frames grandes centrados e variante simplificada legível nos tamanhos
  pequenos (16–24 px).
- **Remoção de pastas monitoradas não persistia** (T4): remover todas as pastas fazia
  Downloads/Músicas reaparecerem na reabertura. Agora uma preferência salva — inclusive
  vazia — é respeitada, e a remoção é persistida imediatamente.
- **"Repetir" com comportamento divergente** (T6): antes ciclava off→playlist→faixa; o
  primeiro clique repetia a playlist inteira. Agora é um toggle direto que repete a faixa
  atual em loop até ser desativado. "Aleatório" foi auditado (já correto) e ganhou testes.

## [1.0.0] - 2026-07-07

- Primeira versão executável (`Bitswave.exe`), licença MIT, empacotamento via PyInstaller.
- Player MP3 com espectro de áudio, playlists, pastas monitoradas e atalhos de teclado.
