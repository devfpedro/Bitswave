"""Carrega os ícones PNG gerados por IA (models/icons/) e os prepara para uso em CTkButton.

Os arquivos-fonte não seguem um padrão único: alguns já têm canal alfa real
(fundo transparente), outros foram exportados com fundo branco opaco. Este
módulo normaliza os dois casos para uma máscara (silhueta) recortada e
colore essa máscara com as cores do tema, gerando um par normal/hover pronto
para trocar via `<Enter>`/`<Leave>`.
"""
import os
from functools import lru_cache

import customtkinter as ctk
from PIL import Image, ImageOps

_ICONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "icons"
)

DEFAULT_SIZE = 20
HOVER_SIZE_BUMP = 2

# Correções pontuais dos assets gerados por IA (ver models/ICON_PROMPTS.md):
# alguns arquivos saíram invertidos ou com o conteúdo errado em relação ao nome do arquivo.
_FLIP_HORIZONTAL = {"back"}  # saiu apontando para a direita; o app precisa dele apontando p/ esquerda
_MISMATCHED_CONTENT: set[str] = set()  # shuffle.png foi regerado corretamente em 2026-07-07 e removido daqui


def _has_real_alpha(im: Image.Image) -> bool:
    if im.mode != "RGBA":
        return False
    return im.getchannel("A").getextrema()[0] < 250


_LUMINANCE_WHITE_THRESHOLD = 235  # luminância >= isso vira alfa 0 (fundo/vinheta)
_LUMINANCE_CONTRAST_RANGE = 80  # faixa (abaixo do threshold) que já satura em alfa 255


def _alpha_from_luminance(im: Image.Image) -> Image.Image:
    """Para PNGs exportados com fundo branco opaco: deriva alfa a partir do quão escuro é o pixel.

    Usa um corte + curva de contraste (não uma inversão linear direta): os exports têm uma
    leve vinheta/ruído de compressão no "branco" de fundo que nunca chega a luminância 255
    pura. Com inversão linear isso vira alfa baixo espalhado pelo canvas inteiro, o que
    impede o recorte por bbox (nada bate exatamente 0) e dilui o ícone quase a ponto de
    ficar invisível quando redimensionado para o tamanho pequeno final do botão.
    """
    rgba = im.convert("RGBA")
    r, g, b, _ = rgba.split()
    luminance = Image.merge("RGB", (r, g, b)).convert("L")
    threshold = _LUMINANCE_WHITE_THRESHOLD
    contrast_range = _LUMINANCE_CONTRAST_RANGE
    alpha = luminance.point(
        lambda v: 0 if v >= threshold else min(255, int((threshold - v) * 255 / contrast_range))
    )
    rgba.putalpha(alpha)
    return rgba


@lru_cache(maxsize=None)
def _load_mask(name: str) -> Image.Image | None:
    """Retorna a silhueta do ícone (RGBA, alfa = forma), recortada e centralizada num canvas quadrado."""
    if name in _MISMATCHED_CONTENT:
        return None
    path = os.path.join(_ICONS_DIR, f"{name}.png")
    if not os.path.isfile(path):
        return None
    im = Image.open(path)
    im = im if _has_real_alpha(im) else _alpha_from_luminance(im)
    if name in _FLIP_HORIZONTAL:
        im = ImageOps.mirror(im)

    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    side = max(im.size, default=1)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(im, ((side - im.width) // 2, (side - im.height) // 2), im)
    return square


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def _boost_alpha(im: Image.Image) -> Image.Image:
    """Normaliza o canal alfa para que o pico chegue a 255.

    Traços de 2px desenhados em canvases grandes (512-1920px) diluem muito ao
    reduzir para os ~14-26px finais dos botões: dependendo do ícone o pico de
    alfa pós-resize varia de ~70 (chevrons, quase invisíveis) a 255. Um fator
    fixo não cobre os dois extremos; normalizar pelo pico deixa todos os ícones
    com a mesma presença visual sem estourar os que já estão fortes.
    """
    alpha = im.getchannel("A")
    peak = alpha.getextrema()[1]
    if 0 < peak < 255:
        factor = 255 / peak
        alpha = alpha.point(lambda v: min(255, int(v * factor)))
        im.putalpha(alpha)
    return im


@lru_cache(maxsize=None)
def get(name: str, size: int = DEFAULT_SIZE, color: str = "#F3F4F6") -> "ctk.CTkImage | None":
    """CTkImage do ícone `name`, recolorido para `color` e redimensionado para `size`px. None se não existir."""
    mask = _load_mask(name)
    if mask is None:
        return None
    r, g, b = _hex_to_rgb(color)
    colored = Image.new("RGBA", mask.size, (r, g, b, 0))
    colored.putalpha(mask.getchannel("A"))
    colored = colored.resize((size, size), Image.LANCZOS)
    colored = _boost_alpha(colored)
    return ctk.CTkImage(colored, size=(size, size))


def pair(
    name: str,
    normal_color: str,
    hover_color: str,
    size: int = DEFAULT_SIZE,
    hover_size: int | None = None,
) -> tuple["ctk.CTkImage | None", "ctk.CTkImage | None"]:
    """Retorna (imagem_normal, imagem_hover) do ícone, ou (None, None) se o arquivo não existir."""
    hover_size = hover_size if hover_size is not None else size + HOVER_SIZE_BUMP
    return get(name, size, normal_color), get(name, hover_size, hover_color)


def bind_hover(widget, normal_img, hover_img) -> None:
    """Troca a imagem do botão em `<Enter>`/`<Leave>` (customtkinter não faz isso sozinho)."""
    if normal_img is None or hover_img is None:
        return

    def _enter(_event=None) -> None:
        widget.configure(image=hover_img)

    def _leave(_event=None) -> None:
        widget.configure(image=normal_img)

    widget.bind("<Enter>", _enter, add="+")
    widget.bind("<Leave>", _leave, add="+")


def available(name: str) -> bool:
    """True se existir um ícone utilizável (arquivo presente e não sinalizado como incorreto)."""
    if name in _MISMATCHED_CONTENT:
        return False
    return os.path.isfile(os.path.join(_ICONS_DIR, f"{name}.png"))


def apply_icon(
    button: ctk.CTkButton,
    name: str,
    normal_color: str,
    hover_color: str,
    size: int = DEFAULT_SIZE,
    hover_size: int | None = None,
) -> bool:
    """Troca o texto do botão pelo ícone `name` (com hover). Mantém o texto atual se o ícone não existir.

    Retorna True se o ícone foi aplicado, False se manteve o fallback de texto.
    """
    normal_img, hover_img = pair(name, normal_color, hover_color, size, hover_size)
    if normal_img is None:
        return False
    button.configure(image=normal_img, text="")
    bind_hover(button, normal_img, hover_img)
    return True
