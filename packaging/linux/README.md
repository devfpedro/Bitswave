# Bitswave no Linux (AppImage)

Distribuição do Bitswave para Linux como **AppImage**: um único arquivo que roda por
duplo-clique, com ícone e entrada de menu, sem instalação nem privilégios de root.

> Por que AppImage (e não Docker): o Bitswave é um app **desktop com GUI** (CustomTkinter/Tk
> + áudio SDL). Docker exigiria o usuário montar sockets X11/Wayland, exportar `DISPLAY` e
> fazer passthrough de áudio — sem ícone/atalho nativo. AppImage entrega exatamente a
> experiência de "abrir pelo ícone" que o formato desktop pede.

## Construir

### Opção A — GitHub Actions (recomendado)

O binário Linux é construído automaticamente por CI, num ambiente Ubuntu limpo e
reprodutível (`.github/workflows/build-linux.yml`). É a boa prática: nada precisa ser
instalado na sua máquina, o runner é fixado em `ubuntu-22.04` (glibc 2.35) para
compatibilidade ampla, e o AppImage ainda passa por um smoke test sob display virtual.

- **Ao publicar um Release** (tag `v*`): o `.AppImage` é anexado ao próprio Release.
- **Manualmente:** aba *Actions* → *Build Linux AppImage* → *Run workflow* → baixe o
  artefato `Bitswave-linux-appimage`.

### Opção B — Localmente (em Linux x86_64)

Útil para testar/depurar. O script **não roda no Windows**:

```bash
bash packaging/linux/build_appimage.sh
```

Saída: `dist/Bitswave-x86_64.AppImage`.

> Atenção: um AppImage construído numa distro *mais nova* pode não rodar em sistemas
> *mais antigos* (glibc). Se for distribuir amplamente, prefira a Opção A (runner fixo).

### Requisitos do sistema (na máquina que constrói)

- `python3` (3.11+), `python3-venv`, `python3-tk`
  (o Tcl/Tk é embutido a partir do ambiente de build — por isso o `-tk` é necessário aqui)
- `wget` e conexão à internet (baixa o `appimagetool` na primeira execução)
- FUSE — ou nada, pois o script já usa `APPIMAGE_EXTRACT_AND_RUN=1` para ambientes sem FUSE (CI)

Exemplo em Debian/Ubuntu:

```bash
sudo apt install python3 python3-venv python3-tk wget
```

## Executar

```bash
chmod +x dist/Bitswave-x86_64.AppImage
./dist/Bitswave-x86_64.AppImage
```

Em distros baseadas em Ubuntu 22.04+ (como o **Zorin OS 17**), o runtime clássico de
AppImage depende do `libfuse2`, que não vem instalado por padrão. Se aparecer um erro de
FUSE, instale-o **ou** rode com extração automática:

```bash
sudo apt install libfuse2          # opção 1
./dist/Bitswave-x86_64.AppImage --appimage-extract-and-run   # opção 2 (sem instalar nada)
```

Para integrar ao menu de aplicativos, use uma ferramenta como o
[Gear Lever](https://github.com/mijorus/gearlever) ou `appimaged`.

## Arquivos

| Arquivo | Papel |
|---|---|
| `build_appimage.sh` | Script de build (venv → PyInstaller → AppDir → appimagetool). |
| `bitswave.desktop`  | Entrada freedesktop (nome, ícone, categoria, `StartupWMClass`). |
| `bitswave.png`      | Ícone 256×256 do app (derivado de `models/icons/iconApp.png`). |

## Notas

- O empacotamento reaproveita a mesma base do Windows (`main.py`, `--collect-all customtkinter`,
  `models/icons` como dados). A diferença de plataforma no separador de `--add-data` (`:` no
  Linux, `;` no Windows) já está tratada no script.
- Áudio: as *wheels* do `pygame-ce` trazem o SDL2, então o AppImage é autossuficiente para
  reprodução na maioria das distribuições.
- Dados graváveis (playlists, config) continuam ao lado do executável via `paths.py`
  (`data_path`), como no Windows.
