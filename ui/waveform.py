"""Visualizador de waveform animado (decorativo) usado na tela de reprodução."""
import math
import tkinter as tk

from . import theme


class WaveformCanvas(tk.Canvas):
    """Barras estilo equalizador (espectro de frequência) que reagem à faixa tocando.

    Quando o espectro real da faixa já foi analisado (ver audio_spectrum.py), as barras
    seguem a energia por banda de frequência no instante atual de reprodução. Antes disso
    (análise ainda em andamento, ou arquivo não suportado), cai para uma animação
    decorativa de espera, para a UI nunca ficar parada/vazia."""

    _BAR_COUNT = 28
    _BAR_GAP = 4
    _MIN_HEIGHT_FRAC = 0.08
    _MAX_HEIGHT_FRAC = 0.95

    def __init__(self, master, height: int = 160, bg: str = theme.BG_DARK, **kwargs):
        super().__init__(master, height=height, bg=bg, highlightthickness=0, **kwargs)
        self._playing = False
        self._phase = 0.0
        self._spectrum_frames: list[list[float]] | None = None
        self._frame_duration = 0.08
        self._position = 0.0
        self.bind("<Configure>", lambda e: self._redraw())
        self._animate()

    def set_playing(self, playing: bool) -> None:
        self._playing = playing

    def set_spectrum(self, frames: list[list[float]], frame_duration: float) -> None:
        """Aplica o espectro pré-calculado da faixa atual (ver audio_spectrum.analyze)."""
        self._spectrum_frames = frames
        self._frame_duration = frame_duration if frame_duration > 0 else 0.08

    def clear_spectrum(self) -> None:
        """Volta para a animação decorativa (chamado ao trocar de faixa)."""
        self._spectrum_frames = None

    def set_position(self, position_sec: float) -> None:
        """Informa a posição atual de reprodução (segundos), usada para indexar o espectro."""
        self._position = max(0.0, position_sec)

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
        if self._spectrum_frames:
            frame_index = int(self._position / self._frame_duration)
            frame_index = max(0, min(frame_index, len(self._spectrum_frames) - 1))
            level = self._spectrum_frames[frame_index][index]
            return self._MIN_HEIGHT_FRAC + level * (self._MAX_HEIGHT_FRAC - self._MIN_HEIGHT_FRAC)
        return self._decorative_height_frac(index)

    def _decorative_height_frac(self, index: int) -> float:
        """Animação de espera usada enquanto o espectro real ainda não está pronto."""
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

    # Redesenho a ~20 fps: sincronizado com o tick de posição de 50 ms do
    # PlaybackView, elimina os degraus de ~5 fps que davam sensação de travamento.
    _REDRAW_MS = 50

    def _animate(self) -> None:
        if self._playing:
            # incremento da fase escalado pelo intervalo, para a animação decorativa
            # (usada enquanto o espectro real ainda é calculado) manter a mesma
            # velocidade visual de antes, independente da taxa de redesenho.
            self._phase += 0.35 * (self._REDRAW_MS / 80.0)
        self._redraw()
        self.after(self._REDRAW_MS, self._animate)
