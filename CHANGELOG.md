# Changelog

Todas as mudanças notáveis do Bitswave são documentadas aqui.
O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e o projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.0.1] - 2026-07-08

### Added
- **Playlist temporária por seleção múltipla** (T7): o botão "＋" agora aceita vários
  arquivos de uma vez e os reproduz em sequência como uma playlist não salva, sem limite
  de faixas. Uma nova seleção — ou iniciar uma playlist salva — descarta a fila anterior.
- **Tooltip no botão de remover pasta** (T5): passar o mouse sobre o "✕" das pastas
  monitoradas explica a ação ("Remover esta pasta da busca automática de músicas recentes").
- Versão do app exibida na tela de Atalhos e centralizada em `version.py`.

### Fixed
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
