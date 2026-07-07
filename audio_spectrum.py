"""Análise de espectro de frequência (FFT) usada pelo visualizador de waveform.

Decodifica a faixa inteira uma vez (via pygame.mixer.Sound) e pré-calcula a energia
por banda de frequência a cada poucos milissegundos. Durante a reprodução, a UI
apenas consulta o quadro correspondente à posição atual -- não há FFT em tempo real
sobre o áudio de saída, pois o pygame.mixer não expõe o stream que está tocando.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass

import numpy as np
import pygame

BAR_COUNT = 28
FRAME_MS = 80
_MIN_FREQ_HZ = 40.0
_DB_RANGE = 55.0  # faixa dinâmica (dB) mapeada para 0..1; abaixo disso vira silêncio visual
_MAX_CACHE_ENTRIES = 20


@dataclass
class SpectrumData:
    """Energia normalizada (0..1) por banda de frequência, quadro a quadro."""

    frames: list[list[float]]
    frame_duration: float


_cache: dict[str, SpectrumData] = {}
_cache_lock = threading.Lock()


def get_cached(filepath: str) -> SpectrumData | None:
    with _cache_lock:
        return _cache.get(filepath)


def _store_cache(filepath: str, data: SpectrumData) -> None:
    with _cache_lock:
        if filepath not in _cache and len(_cache) >= _MAX_CACHE_ENTRIES:
            _cache.pop(next(iter(_cache)))
        _cache[filepath] = data


def analyze(filepath: str) -> SpectrumData | None:
    """Decodifica `filepath` e calcula o espectro ao longo do tempo.

    Retorna None se o arquivo não puder ser decodificado -- o chamador deve manter
    a animação decorativa como alternativa nesse caso. Resultado fica em cache.
    """
    cached = get_cached(filepath)
    if cached is not None:
        return cached

    try:
        sound = pygame.mixer.Sound(filepath)
        raw = sound.get_raw()
        init = pygame.mixer.get_init()
        if not raw or init is None:
            return None
        sample_rate, _fmt, channels = init
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
        if channels > 1:
            samples = samples.reshape(-1, channels).mean(axis=1)
        if samples.size == 0:
            return None
    except Exception:
        return None

    frame_size = max(256, int(sample_rate * FRAME_MS / 1000))
    n_frames = samples.size // frame_size
    if n_frames == 0:
        return None
    samples = samples[: n_frames * frame_size].reshape(n_frames, frame_size)

    window = np.hanning(frame_size)
    spectrum = np.abs(np.fft.rfft(samples * window, axis=1))

    freqs = np.fft.rfftfreq(frame_size, d=1.0 / sample_rate)
    edges = np.logspace(np.log10(_MIN_FREQ_HZ), np.log10(sample_rate / 2), BAR_COUNT + 1)
    bin_idx = np.searchsorted(freqs, edges)

    bands = np.zeros((n_frames, BAR_COUNT), dtype=np.float32)
    for b in range(BAR_COUNT):
        lo, hi = bin_idx[b], max(bin_idx[b] + 1, bin_idx[b + 1])
        if hi > lo:
            bands[:, b] = spectrum[:, lo:hi].mean(axis=1)

    db = 20.0 * np.log10(bands + 1.0)
    peak = float(db.max())
    floor = peak - _DB_RANGE
    span = max(1e-6, peak - floor)
    normalized = np.clip((db - floor) / span, 0.0, 1.0)

    data = SpectrumData(frames=normalized.tolist(), frame_duration=FRAME_MS / 1000.0)
    _store_cache(filepath, data)
    return data
