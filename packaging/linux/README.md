# Bitswave no Linux (AppImage)

Distribuição do Bitswave para Linux como **AppImage**: um único arquivo que roda por
duplo-clique, com ícone e entrada de menu, sem instalação nem privilégios de root.

> Por que AppImage (e não Docker): o Bitswave é um app **desktop com GUI** (CustomTkinter/Tk
> + áudio SDL). Docker exigiria o usuário montar sockets X11/Wayland, exportar `DISPLAY` e
> fazer passthrough de áudio — sem ícone/atalho nativo. AppImage entrega exatamente a
> experiência de "abrir pelo ícone" que o formato desktop pede.

## Construir

Executar **em Linux x86_64** (o script não roda no Windows):

```bash
bash packaging/linux/build_appimage.sh
```

Saída: `dist/Bitswave-x86_64.AppImage`.

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
