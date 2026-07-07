# Prompts de ícones para a IA do Canva

Lista de todos os ícones usados nas interfaces do Bitswave hoje (emojis/glifos de texto),
com um prompt pronto para gerar cada um na IA de imagem do Canva. Depois de gerar,
salve os PNGs em `models/icons/` (crie a pasta) com o nome de arquivo sugerido — é o
nome que o código vai procurar quando fizermos a troca dos glifos de texto pelas imagens.

## Estilo geral (use em todos os prompts)

Todos os ícones devem seguir a mesma linguagem visual do `iconApp.png` (o logo do app:
onda de áudio em gradiente ciano-azul sobre fundo escuro arredondado), para que a UI
pareça um sistema único, não um conjunto de emojis genéricos.

**Prefixo de estilo** (cole no início de cada prompt abaixo):

> Flat minimalist line icon, vector style, 2px stroke weight, rounded line caps,
> centered on a fully transparent background, no drop shadow, no text, no border box,
> square canvas 256x256px, simple and modern (similar to Material Symbols / Feather Icons).

## Duas variações por ícone

Cada ícone precisa de **2 arquivos**: um estado normal (repouso) e um estado em destaque
(hover/ativo). Isso cobre o pedido de melhorar a interação visual dos ícones:

- **Normal**: contorno (outline), cor cinza-claro sólida `#9CA3AF`.
- **Hover / Ativo**: preenchido (filled/solid) ou com o gradiente de destaque do app —
  `#22D3EE` → `#38BDF8` → `#3B82F6` → `#6366F1` (esquerda para direita), usado nos
  botões quando pressionados, tocando, ou em modos ativados (shuffle/repeat ligados).

---

## 1. Tela de Reprodução (`ui/playback_view.py`)

| Ícone atual | Uso | Arquivo sugerido |
|---|---|---|
| ☰ | Abrir playlists | `menu` |
| ＋ | Adicionar músicas avulsas | `add` |
| ⏮ | Faixa anterior | `prev` |
| ▶ | Tocar | `play` |
| ⏸ | Pausar | `pause` |
| ⏹ | Parar | `stop` |
| ⏭ | Próxima faixa | `next` |
| 🔀 | Alternar modo aleatório | `shuffle` |
| 🔁 | Alternar repetição (loop da playlist) | `repeat` |
| 🔂 | Repetição de uma faixa só | `repeat_one` |
| 🔇 🔈 🔉 🔊 | Ícone de volume (4 estágios) | `volume_mute`, `volume_low`, `volume_mid`, `volume_high` |

**Prompts:**

- `menu`: "[prefixo de estilo]. Three horizontal parallel lines stacked vertically (hamburger menu icon), evenly spaced, equal length."
- `add`: "[prefixo de estilo]. A simple plus sign (+), thick, perfectly centered, equal horizontal and vertical bars."
- `prev`: "[prefixo de estilo]. A 'skip to previous track' icon: a vertical bar on the left, followed by a solid triangle pointing left."
- `play`: "[prefixo de estilo]. A single solid triangle pointing right (play button), centered."
- `pause`: "[prefixo de estilo]. Two vertical parallel bars, evenly spaced (pause icon)."
- `stop`: "[prefixo de estilo]. A single rounded square (stop icon), centered."
- `next`: "[prefixo de estilo]. A 'skip to next track' icon: a solid triangle pointing right, followed by a vertical bar on the right."
- `shuffle`: "[prefixo de estilo]. Two crossing curved arrows forming an X shape (shuffle/randomize icon), both ending in small arrowheads pointing right."
- `repeat`: "[prefixo de estilo]. A looping repeat icon: two arrows forming a rounded rectangular loop, arrowheads at each end."
- `repeat_one`: "[prefixo de estilo]. Same as a repeat loop icon (two arrows forming a rounded rectangular loop), but with a small number '1' centered inside the loop."
- `volume_mute`: "[prefixo de estilo]. A speaker icon (trapezoid with a small square) with a small 'X' next to it indicating muted audio."
- `volume_low`: "[prefixo de estilo]. A speaker icon (trapezoid with a small square) with a single small sound wave arc next to it."
- `volume_mid`: "[prefixo de estilo]. A speaker icon (trapezoid with a small square) with two small sound wave arcs next to it, increasing in size."
- `volume_high`: "[prefixo de estilo]. A speaker icon (trapezoid with a small square) with three small sound wave arcs next to it, increasing in size."

## 2. Painel "Adicionadas recentemente" (`ui/recent_files_panel.py`)

| Ícone atual | Uso | Arquivo sugerido |
|---|---|---|
| ⌄ / ⌃ | Expandir / recolher painel | `chevron_down`, `chevron_up` |
| 📁 | Gerenciar pastas monitoradas | `folder` |

**Prompts:**

- `chevron_down`: "[prefixo de estilo]. A simple chevron/arrow pointing downward (like a 'V' shape), thin and wide."
- `chevron_up`: "[prefixo de estilo]. A simple chevron/arrow pointing upward (like an inverted 'V' shape), thin and wide."
- `folder`: "[prefixo de estilo]. A simple closed file folder icon, classic tab-on-top shape."

## 3. Navegação e ações comuns (aparecem em várias telas)

| Ícone atual | Uso | Arquivo sugerido |
|---|---|---|
| ← | Voltar (playlists, atalhos) | `back` |
| ✕ | Fechar / voltar (detalhe de playlist, diálogo de pastas) | `close` |
| ⚙ | Abrir tela de atalhos (canto inferior esquerdo, todas as telas) | `settings` |
| ⋮ | Menu de opções (card de playlist, linha de faixa) | `more_vertical` |

**Prompts:**

- `back`: "[prefixo de estilo]. A simple arrow pointing left, thin, no arrow tail decoration."
- `close`: "[prefixo de estilo]. A simple 'X' shape made of two crossing diagonal lines, equal length."
- `settings`: "[prefixo de estilo]. A classic gear/cog icon with 8 evenly spaced teeth and a circular hole in the center."
- `more_vertical`: "[prefixo de estilo]. Three small solid dots stacked vertically, evenly spaced (vertical kebab menu icon)."

## 4. Tela de Seleção de Playlists (`ui/playlist_selection_view.py`)

Reaproveita `back`, `settings` e `more_vertical` acima. Ícone próprio:

| Ícone atual | Uso | Arquivo sugerido |
|---|---|---|
| ＋ (dentro do botão "Criar Nova Playlist") | Criar playlist | reaproveita `add` |

## 5. Tela de Detalhe da Playlist (`ui/playlist_detail_view.py`)

Reaproveita `close`, `settings`, `more_vertical`, `add` (no botão "Adicionar Músicas") e
`play` (no botão "Tocar"). Nenhum ícone exclusivo além desses.

## 6. Diálogo "Pastas Monitoradas" (`ui/dialogs.py`)

| Ícone atual | Uso | Arquivo sugerido |
|---|---|---|
| ✕ (vermelho) | Remover pasta da lista | `remove` |
| ＋ (no botão "Adicionar Pasta") | Adicionar pasta | reaproveita `add` |

**Prompt:**

- `remove`: "[prefixo de estilo]. A simple 'X' shape made of two crossing diagonal lines, equal length, in a warning/danger red color `#EF4444` instead of the default gray."

---

## Notas de implementação (para quando formos trocar os glifos pelas imagens)

- `customtkinter.CTkButton` aceita um parâmetro `image=CTkImage(...)` além de `text=""`
  — dá para usar as imagens exportadas diretamente, sem precisar de biblioteca nova.
- `CTkImage` já aceita `light_image` e `dark_image` separados, mas como o app só usa tema
  escuro (`ctk.set_appearance_mode("dark")`), basta uma imagem por estado.
- Para o hover funcionar como imagem (não só cor de fundo), é preciso trocar a imagem do
  botão manualmente nos eventos `<Enter>`/`<Leave>` (customtkinter não faz isso sozinho).
  Isso é um trabalho de código à parte, a ser feito depois que as imagens existirem.
- Exporte todos os PNGs com fundo transparente e o mesmo tamanho final (recomendo 48x48px
  ou 64x64px) para não precisar reajustar posição/escala em cada botão.
