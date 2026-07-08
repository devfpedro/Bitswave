#!/usr/bin/env bash
#
# Constrói um AppImage do Bitswave — um único arquivo executável por duplo-clique,
# com ícone e entrada de menu, sem instalação nem root.
#
# EXECUTAR EM LINUX x86_64 (não funciona no Windows). Requisitos no sistema:
#   - python3 (3.11+), python3-venv, python3-tk   (Tcl/Tk é embutido a partir daqui)
#   - wget e conexão à internet (baixa o appimagetool na primeira vez)
#   - FUSE, ou a variável APPIMAGE_EXTRACT_AND_RUN=1 (já setada abaixo p/ CI sem FUSE)
#
# Uso:  bash packaging/linux/build_appimage.sh
# Saída: dist/Bitswave-x86_64.AppImage
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
BUILD="$ROOT/build/linux"
APPDIR="$BUILD/Bitswave.AppDir"

echo ">> [1/6] Limpando build anterior"
rm -rf "$BUILD"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$ROOT/dist"

echo ">> [2/6] Criando venv e instalando dependências (+ pyinstaller)"
python3 -m venv "$BUILD/venv"
# shellcheck disable=SC1091
source "$BUILD/venv/bin/activate"
pip install --upgrade pip >/dev/null
pip install -r "$ROOT/requirements.txt" pyinstaller

echo ">> [3/6] Empacotando com PyInstaller (onefile)"
# No Linux o separador de --add-data é ':' (no Windows é ';').
# --hidden-import PIL._tkinter_finder: sem isso, o Pillow não acha o _tkinter
# empacotado em tempo de execução e qualquer widget com imagem (ícones) quebra
# com "ModuleNotFoundError: No module named 'PIL._tkinter_finder'" ao iniciar.
pyinstaller --noconfirm --clean \
  --name bitswave --onefile --windowed \
  --add-data "$ROOT/models/icons:models/icons" \
  --collect-all customtkinter \
  --hidden-import PIL._tkinter_finder \
  --distpath "$BUILD/dist" --workpath "$BUILD/work" --specpath "$BUILD" \
  "$ROOT/main.py"

echo ">> [4/6] Montando o AppDir"
install -Dm755 "$BUILD/dist/bitswave" "$APPDIR/usr/bin/bitswave"
install -Dm644 "$HERE/bitswave.desktop" "$APPDIR/bitswave.desktop"
install -Dm644 "$HERE/bitswave.png" "$APPDIR/bitswave.png"
# ícone também no caminho padrão hicolor (integração de menu ao instalar)
install -Dm644 "$HERE/bitswave.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/bitswave.png"
install -Dm644 "$HERE/bitswave.desktop" "$APPDIR/usr/share/applications/bitswave.desktop"

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/bitswave" "$@"
EOF
chmod +x "$APPDIR/AppRun"

echo ">> [5/6] Obtendo o appimagetool"
TOOL="$BUILD/appimagetool-x86_64.AppImage"
if [ ! -x "$TOOL" ]; then
  wget -q -O "$TOOL" \
    "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
  chmod +x "$TOOL"
fi

echo ">> [6/6] Gerando o AppImage"
export APPIMAGE_EXTRACT_AND_RUN=1   # funciona em ambientes sem FUSE (CI)
ARCH=x86_64 "$TOOL" "$APPDIR" "$ROOT/dist/Bitswave-x86_64.AppImage"

echo ""
echo ">> Pronto: dist/Bitswave-x86_64.AppImage"
echo "   Torne-o executável e rode:  chmod +x dist/Bitswave-x86_64.AppImage && ./dist/Bitswave-x86_64.AppImage"
