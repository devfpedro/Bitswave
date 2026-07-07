"""Visualizador de waveform animado (decorativo) usado na tela de reprodução."""
import math
import tkinter as tk

from . import theme


class WaveformCanvas(tk.Canvas):
    """Barras estilo equalizador que pulsam enquanto a música toca e ficam
    em repouso quando pausada/parada. Puramente decorativo (não é uma FFT real)."""

    _BAR_COUNT = 28
    _BAR_GAP = 4
    _MIN_HEIGHT_FRAC = 0.08
    _MAX_HEIGHT_FRAC = 0.95

    def __init__(self, master, height: int = 160, bg: str = theme.BG_DARK, **kwargs):
        super().__init__(master, height=height, bg=bg, highlightthickness=0, **kwargs)
        self._playing = False
        self._phase = 0.0
        self.bind("<Configure>", lambda e: self._redraw())
        self._animate()

    def set_playing(self, playing: bool) -> None:
        self._playing = playing

    def _bar_color(self, index: int) -> str:
        colors = theme.ACCENT_GRADIENT
        pos = index / max(1, self._BAR_COUNT - 1)
        # espelha o degradê a partir do centro, como no mockup (pico central mais claro)
        mirrored = 1 - abs(pos * 2 - 1)
        scaled = mirrored * (len(colors) - 1)
        return colors[int(round(scaled))]

    def _bar_height_frac(self, index: int) -> float:
        if not self._playing:
            return self._MIN_HEIGHT_FRAC
        center = (self._BAR_COUNT - 1) / 2
        distance = abs(index - center) / center if center else 0
        envelope = 1.0 - distance * 0.75
        wobble = 0.5 + 0.5 * math.sin(self._phase + index * 0.6)
        frac = self._MIN_HEIGHT_FRAC + envelope * wobble * (self._MAX_HEIGHT_FRAC - self._MIN_HEIGHT_FRAC)
        return max(self._MIN_HEIGHT_FRAC, min(self._MAX_HEIGHT_FRAC, frac))

    def _redraw(self) -> None:
        self.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 1 or height <= 1:
            return
        bar_width = max(2.0, (width / self._BAR_COUNT) - self._BAR_GAP)
        for i in range(self._BAR_COUNT):
            x0 = i * (bar_width + self._BAR_GAP)
            x1 = x0 + bar_width
            bar_h = height * self._bar_height_frac(i)
            y0 = (height - bar_h) / 2
            y1 = y0 + bar_h
            radius = min(bar_width / 2, 4)
            self._round_rect(x0, y0, x1, y1, radius, fill=self._bar_color(i))

    def _round_rect(self, x0, y0, x1, y1, r, **kwargs) -> None:
        """Desenha uma barra em forma de cápsula (extremidades arredondadas)."""
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        if r <= 0:
            self.create_rectangle(x0, y0, x1, y1, outline="", width=0, **kwargs)
            return
        self.create_oval(x0, y0, x1, y0 + 2 * r, outline="", width=0, **kwargs)
        self.create_oval(x0, y1 - 2 * r, x1, y1, outline="", width=0, **kwargs)
        self.create_rectangle(x0, y0 + r, x1, y1 - r, outline="", width=0, **kwargs)

    def _animate(self) -> None:
        if self._playing:
            self._phase += 0.35
        self._redraw()
        self.after(80, self._animate)
