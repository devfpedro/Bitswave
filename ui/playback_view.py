"""Tela principal de reprodução (Now Playing)."""
import json
import os
import queue
import random
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pygame

import audio_spectrum
from player import AudioPlayer

from . import theme
from .recent_files_panel import RecentFilesPanel
from .tooltip import add_tooltip
from .utils import add_settings_button, format_time as _format_time
from .waveform import WaveformCanvas

CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "player_config.json"
)


class PlaybackView(ctk.CTkFrame):
    """Tela "Now Playing": waveform, controles de transporte e volume."""

    ICON_MENU = "☰"
    ICON_ADD = "＋"
    ICON_PREV = "⏮"
    ICON_PLAY = "▶"
    ICON_PAUSE = "⏸"
    ICON_STOP = "⏹"
    ICON_NEXT = "⏭"
    ICON_SHUFFLE = "🔀"
    ICON_REPEAT = "🔁"
    ICON_REPEAT_ONE = "🔂"

    def __init__(self, master, app):
        super().__init__(master, fg_color=theme.BG_DARK)
        self.app = app
        self.player = app.player

        self._queue: list[str] = []
        self._index: int = -1
        self._seeking: bool = False
        self._elapsed_offset: float = 0.0
        self._current_duration: float = 0.0
        self._shuffle: bool = False
        self._repeat_mode: str = "off"
        self._spectrum_queue: queue.Queue = queue.Queue()
        self._analyzing: set[str] = set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        self._build_topbar()
        self._build_waveform()
        self._build_info()
        self._build_progress()
        self._build_controls()
        self.recent_files_panel = RecentFilesPanel(self, self.app)
        self.recent_files_panel.grid(row=5, column=0, sticky="ew", padx=16, pady=(0, 4))
        ctk.CTkFrame(self, fg_color="transparent").grid(row=6, column=0, sticky="nsew")
        add_settings_button(self, self.app)

        self._start_update_loop()

    # ------------------------------------------------------------------
    # Construção da UI
    # ------------------------------------------------------------------

    def _build_topbar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent", height=40)
        bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        bar.grid_columnconfigure(1, weight=1)

        icon_cfg = dict(
            width=40, height=40, corner_radius=20, font=ctk.CTkFont(size=16),
            fg_color=theme.CARD_BG, hover_color=theme.CARD_BG_HOVER, text_color=theme.TEXT_PRIMARY,
        )
        self.btn_menu = ctk.CTkButton(bar, text=self.ICON_MENU, command=self._on_open_playlists, **icon_cfg)
        self.btn_menu.grid(row=0, column=0, sticky="w")
        add_tooltip(self.btn_menu, "Abrir playlists")

        self.btn_add = ctk.CTkButton(bar, text=self.ICON_ADD, command=self._on_add_files, **icon_cfg)
        self.btn_add.grid(row=0, column=2, sticky="e")
        add_tooltip(self.btn_add, "Adicionar músicas")

    def _build_waveform(self) -> None:
        self.waveform = WaveformCanvas(self, height=130, bg=theme.BG_DARK)
        self.waveform.grid(row=1, column=0, sticky="ew", padx=24, pady=(16, 8))

    def _build_info(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=2, column=0, sticky="ew", padx=24)

        self.lbl_title = ctk.CTkLabel(
            frame, text="Nenhuma música selecionada", font=ctk.CTkFont(size=20, weight="bold"),
            text_color=theme.TEXT_PRIMARY, anchor="center",
        )
        self.lbl_title.pack(fill="x", pady=(4, 2))

        self.lbl_artist = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=14), text_color=theme.TEXT_SECONDARY, anchor="center",
        )
        self.lbl_artist.pack(fill="x")

    def _build_progress(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=3, column=0, sticky="ew", padx=24, pady=(16, 4))
        frame.grid_columnconfigure(1, weight=1)

        self.lbl_elapsed = ctk.CTkLabel(
            frame, text="00:00", font=ctk.CTkFont(size=12), text_color=theme.TEXT_SECONDARY, width=46,
        )
        self.lbl_elapsed.grid(row=0, column=0, padx=(0, 6))

        self.slider_progress = ctk.CTkSlider(
            frame, from_=0, to=1, number_of_steps=1000,
            progress_color=theme.ACCENT, button_color=theme.ACCENT, button_hover_color=theme.ACCENT_HOVER,
            command=self._on_progress_drag,
        )
        self.slider_progress.set(0)
        self.slider_progress.grid(row=0, column=1, sticky="ew")
        self.slider_progress.bind("<ButtonPress-1>", self._on_progress_press)
        self.slider_progress.bind("<ButtonRelease-1>", self._on_progress_release)

        self.lbl_duration = ctk.CTkLabel(
            frame, text="00:00", font=ctk.CTkFont(size=12), text_color=theme.TEXT_SECONDARY, width=46,
        )
        self.lbl_duration.grid(row=0, column=2, padx=(6, 0))

    def _build_controls(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=4, column=0, sticky="ew", padx=16, pady=(8, 24))

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(expand=True)

        mode_cfg = dict(
            width=36, height=36, corner_radius=18, font=ctk.CTkFont(size=14),
            fg_color="transparent", text_color=theme.TEXT_SECONDARY,
        )
        btn_cfg = dict(
            width=48, height=48, corner_radius=24, font=ctk.CTkFont(size=18),
            fg_color=theme.CARD_BG, hover_color=theme.CARD_BG_HOVER, text_color=theme.TEXT_PRIMARY,
        )

        self.btn_shuffle = ctk.CTkButton(btn_row, text=self.ICON_SHUFFLE, command=self._on_toggle_shuffle, **mode_cfg)
        self.btn_shuffle.pack(side="left", padx=(0, 8))
        add_tooltip(self.btn_shuffle, "Aleatório")

        self.btn_prev = ctk.CTkButton(btn_row, text=self.ICON_PREV, command=self._on_prev, **btn_cfg)
        self.btn_prev.pack(side="left", padx=4)
        add_tooltip(self.btn_prev, "Anterior")

        self.btn_play = ctk.CTkButton(
            btn_row, text=self.ICON_PLAY, command=self._on_play_pause,
            width=64, height=64, corner_radius=32, font=ctk.CTkFont(size=24),
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
        )
        self.btn_play.pack(side="left", padx=6)
        add_tooltip(self.btn_play, "Reproduzir / Pausar")

        self.btn_stop = ctk.CTkButton(btn_row, text=self.ICON_STOP, command=self._on_stop, **btn_cfg)
        self.btn_stop.pack(side="left", padx=4)
        add_tooltip(self.btn_stop, "Parar")

        self.btn_next = ctk.CTkButton(btn_row, text=self.ICON_NEXT, command=self._on_next, **btn_cfg)
        self.btn_next.pack(side="left", padx=4)
        add_tooltip(self.btn_next, "Próxima")

        self.btn_repeat = ctk.CTkButton(btn_row, text=self.ICON_REPEAT, command=self._on_cycle_repeat, **mode_cfg)
        self.btn_repeat.pack(side="left", padx=(8, 0))
        add_tooltip(self.btn_repeat, "Repetir")

        vol_row = ctk.CTkFrame(frame, fg_color="transparent")
        vol_row.pack(pady=(14, 0))
        self.lbl_volume_icon = ctk.CTkLabel(
            vol_row, text=self._volume_icon_for(0.7), font=ctk.CTkFont(size=16),
            text_color=theme.TEXT_SECONDARY, width=22,
        )
        self.lbl_volume_icon.pack(side="left", padx=(0, 6))
        add_tooltip(self.lbl_volume_icon, "Volume")
        self.slider_volume = ctk.CTkSlider(
            vol_row, from_=0, to=1, width=140,
            progress_color=theme.ACCENT, button_color=theme.ACCENT, button_hover_color=theme.ACCENT_HOVER,
            command=self._on_volume_change,
        )
        self.slider_volume.set(0.7)
        self.player.set_volume(0.7)
        self.slider_volume.pack(side="left")

    # ------------------------------------------------------------------
    # API pública (usada pelo App e por outras telas)
    # ------------------------------------------------------------------

    def on_show(self) -> None:
        pass

    def load_queue(self, filepaths: list[str], start_index: int = 0, shuffle: bool = False) -> None:
        """Substitui a fila atual e começa a tocar a partir de start_index."""
        if not filepaths:
            return
        self._queue = list(filepaths)
        self._shuffle = shuffle
        self.btn_shuffle.configure(fg_color=theme.ACCENT_ACTIVE if shuffle else "transparent")
        start_index = max(0, min(start_index, len(self._queue) - 1))
        if self._load_track(start_index):
            self.player.play()
            self.btn_play.configure(text=self.ICON_PAUSE)
            self.waveform.set_playing(True)

    def save_state(self) -> None:
        """Salva a fila atual, índice, volume e pastas monitoradas para a próxima sessão."""
        data = {
            "queue": self._queue,
            "index": self._index,
            "volume": self.slider_volume.get(),
            "watch_folders": self.app.folder_watcher.folders,
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def load_state(self) -> None:
        """Restaura a última fila tocada e as pastas monitoradas, se existirem."""
        if not os.path.isfile(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return

        volume = data.get("volume")
        if isinstance(volume, (int, float)):
            volume = max(0.0, min(1.0, float(volume)))
            self.slider_volume.set(volume)
            self._on_volume_change(volume)

        watch_folders = data.get("watch_folders")
        if isinstance(watch_folders, list):
            valid = [f for f in watch_folders if isinstance(f, str) and os.path.isdir(f)]
            if valid:
                self.app.folder_watcher.folders = valid

        queue = [f for f in data.get("queue", []) if isinstance(f, str) and os.path.isfile(f)]
        if not queue:
            return
        self._queue = queue
        index = data.get("index", 0)
        index = index if isinstance(index, int) and 0 <= index < len(queue) else 0
        self._load_track(index)

    # ------------------------------------------------------------------
    # Callbacks / Eventos
    # ------------------------------------------------------------------

    def _on_open_playlists(self) -> None:
        self.app.show_playlist_selection()

    def _on_add_files(self) -> None:
        """Abre diálogo para tocar arquivos MP3 avulsos (fila temporária, sem salvar playlist)."""
        files = filedialog.askopenfilenames(
            title="Selecionar arquivos MP3", filetypes=[("Arquivos MP3", "*.mp3")],
        )
        if not files:
            return
        start_fresh = not self._queue
        self._queue.extend(f for f in files if f not in self._queue)
        if start_fresh and self._load_track(0):
            self.player.play()
            self.btn_play.configure(text=self.ICON_PAUSE)
            self.waveform.set_playing(True)

    def _reset_now_playing(self) -> None:
        self.lbl_title.configure(text="Nenhuma música selecionada")
        self.lbl_artist.configure(text="")
        self.lbl_duration.configure(text="00:00")
        self.lbl_elapsed.configure(text="00:00")
        self.slider_progress.set(0)
        self.btn_play.configure(text=self.ICON_PLAY)
        self.waveform.set_playing(False)
        self._current_duration = 0.0
        self._elapsed_offset = 0.0

    def _load_track(self, index: int) -> bool:
        """Carrega a faixa pelo índice da fila atual.

        Retorna False (removendo a faixa da fila) se o arquivo não existir mais
        ou estiver corrompido/inválido, em vez de derrubar a aplicação.
        """
        if not (0 <= index < len(self._queue)):
            return False
        filepath = self._queue[index]
        try:
            self.player.load(filepath)
        except (FileNotFoundError, pygame.error) as exc:
            messagebox.showerror(
                "Erro ao carregar música",
                f"Não foi possível carregar o arquivo:\n{filepath}\n\n{exc}",
            )
            del self._queue[index]
            if index < self._index:
                self._index -= 1
            if 0 <= index < len(self._queue):
                return self._load_track(index)
            self._index = -1
            self._reset_now_playing()
            return False

        self._index = index
        self._elapsed_offset = 0.0
        self._current_duration = AudioPlayer.get_duration(filepath)
        self._load_spectrum(filepath)

        meta = AudioPlayer.get_metadata(filepath)
        self.lbl_title.configure(text=meta["title"])
        self.lbl_artist.configure(text=meta["artist"])
        self.lbl_duration.configure(text=_format_time(self._current_duration))
        self.slider_progress.set(0)
        self.lbl_elapsed.configure(text="00:00")
        return True

    # ------------------------------------------------------------------
    # Espectro de áudio (waveform reativa à música)
    # ------------------------------------------------------------------

    def _load_spectrum(self, filepath: str) -> None:
        """Aplica o espectro em cache ou dispara sua análise em segundo plano."""
        self.waveform.clear_spectrum()
        cached = audio_spectrum.get_cached(filepath)
        if cached is not None:
            self.waveform.set_spectrum(cached.frames, cached.frame_duration)
            return
        if filepath in self._analyzing:
            return
        self._analyzing.add(filepath)
        threading.Thread(target=self._spectrum_worker, args=(filepath,), daemon=True).start()

    def _spectrum_worker(self, filepath: str) -> None:
        """Roda em thread separada: decodifica e calcula a FFT sem travar a UI."""
        data = audio_spectrum.analyze(filepath)
        self._spectrum_queue.put((filepath, data))

    def _drain_spectrum_queue(self) -> None:
        """Aplica espectros calculados nas threads de análise (chamado no loop principal)."""
        try:
            while True:
                filepath, data = self._spectrum_queue.get_nowait()
                self._analyzing.discard(filepath)
                if data is not None and self.player.current_file == filepath:
                    self.waveform.set_spectrum(data.frames, data.frame_duration)
        except queue.Empty:
            pass

    def _on_play_pause(self) -> None:
        if not self._queue:
            return
        if self.player.is_playing():
            self.player.pause()
            self.btn_play.configure(text=self.ICON_PLAY)
            self.waveform.set_playing(False)
        elif self.player.is_paused():
            self.player.unpause()
            self.btn_play.configure(text=self.ICON_PAUSE)
            self.waveform.set_playing(True)
        else:
            if self._index == -1:
                if not self._load_track(0):
                    return
            self.player.play()
            self.btn_play.configure(text=self.ICON_PAUSE)
            self.waveform.set_playing(True)

    def _on_stop(self) -> None:
        self.player.stop()
        self.btn_play.configure(text=self.ICON_PLAY)
        self.slider_progress.set(0)
        self.lbl_elapsed.configure(text="00:00")
        self._elapsed_offset = 0.0
        self.waveform.set_playing(False)

    def _next_index_manual(self) -> int:
        if self._shuffle and len(self._queue) > 1:
            choices = [i for i in range(len(self._queue)) if i != self._index]
            return random.choice(choices)
        return (self._index + 1) % len(self._queue)

    def _prev_index_manual(self) -> int:
        if self._shuffle and len(self._queue) > 1:
            choices = [i for i in range(len(self._queue)) if i != self._index]
            return random.choice(choices)
        return (self._index - 1) % len(self._queue)

    def _on_prev(self) -> None:
        if not self._queue:
            return
        if not self._load_track(self._prev_index_manual()):
            return
        self.player.play()
        self.btn_play.configure(text=self.ICON_PAUSE)
        self.waveform.set_playing(True)

    def _on_next(self) -> None:
        if not self._queue:
            return
        if not self._load_track(self._next_index_manual()):
            return
        self.player.play()
        self.btn_play.configure(text=self.ICON_PAUSE)
        self.waveform.set_playing(True)

    @staticmethod
    def _volume_icon_for(value: float) -> str:
        if value <= 0.0:
            return "🔇"
        if value < 0.34:
            return "🔈"
        if value < 0.67:
            return "🔉"
        return "🔊"

    def _on_volume_change(self, value: float) -> None:
        self.player.set_volume(value)
        self.lbl_volume_icon.configure(text=self._volume_icon_for(value))

    def adjust_volume(self, delta: float) -> None:
        """Aumenta/diminui o volume em `delta` (usado pelos atalhos de teclado ↑/↓)."""
        new_volume = max(0.0, min(1.0, self.slider_volume.get() + delta))
        self.slider_volume.set(new_volume)
        self._on_volume_change(new_volume)

    def _on_toggle_shuffle(self) -> None:
        self._shuffle = not self._shuffle
        self.btn_shuffle.configure(fg_color=theme.ACCENT_ACTIVE if self._shuffle else "transparent")

    def _on_cycle_repeat(self) -> None:
        order = ["off", "all", "one"]
        self._repeat_mode = order[(order.index(self._repeat_mode) + 1) % len(order)]
        icon = self.ICON_REPEAT_ONE if self._repeat_mode == "one" else self.ICON_REPEAT
        active = self._repeat_mode != "off"
        self.btn_repeat.configure(text=icon, fg_color=theme.ACCENT_ACTIVE if active else "transparent")

    # ------------------------------------------------------------------
    # Barra de progresso — interação do usuário
    # ------------------------------------------------------------------

    def _on_progress_press(self, event) -> None:
        self._seeking = True

    def _on_progress_drag(self, value: float) -> None:
        if self._current_duration > 0:
            self.lbl_elapsed.configure(text=_format_time(value * self._current_duration))

    def _on_progress_release(self, event) -> None:
        self._seeking = False
        if self._current_duration > 0 and self.player.current_file:
            target = self.slider_progress.get() * self._current_duration
            self._elapsed_offset = target
            self.player.seek(target)

    def seek_relative(self, delta: float) -> None:
        """Avança/retrocede a posição atual em `delta` segundos (usado por atalhos de teclado)."""
        if not self.player.current_file or self._current_duration <= 0:
            return
        current = self._elapsed_offset + self.player.get_position()
        target = max(0.0, min(self._current_duration, current + delta))
        self._elapsed_offset = target
        self.player.seek(target)
        self.slider_progress.set(target / self._current_duration)
        self.lbl_elapsed.configure(text=_format_time(target))
        self.waveform.set_position(target)

    # ------------------------------------------------------------------
    # Loop de atualização
    # ------------------------------------------------------------------

    def _start_update_loop(self) -> None:
        self._update_progress()
        self._check_music_end()

    def _update_progress(self) -> None:
        self._drain_spectrum_queue()
        if self.player.is_playing() and not self._seeking and self._current_duration > 0:
            pos_sec = self._elapsed_offset + self.player.get_position()
            if pos_sec > self._current_duration:
                pos_sec = self._current_duration
            fraction = pos_sec / self._current_duration
            self.slider_progress.set(fraction)
            self.lbl_elapsed.configure(text=_format_time(pos_sec))
            self.waveform.set_position(pos_sec)
        self.after(200, self._update_progress)

    def _check_music_end(self) -> None:
        if not self._seeking and self.player.has_finished():
            self._auto_next()
        self.after(500, self._check_music_end)

    def _auto_next(self) -> None:
        if self._repeat_mode == "one":
            if self._load_track(self._index):
                self.player.play()
                self.btn_play.configure(text=self.ICON_PAUSE)
                self.waveform.set_playing(True)
            return
        if self._shuffle and len(self._queue) > 1:
            if self._load_track(self._next_index_manual()):
                self.player.play()
                self.btn_play.configure(text=self.ICON_PAUSE)
                self.waveform.set_playing(True)
            return
        if self._index < len(self._queue) - 1:
            self._on_next()
        elif self._repeat_mode == "all" and self._queue:
            if self._load_track(0):
                self.player.play()
                self.btn_play.configure(text=self.ICON_PAUSE)
                self.waveform.set_playing(True)
        else:
            self.player.stop()
            self.btn_play.configure(text=self.ICON_PLAY)
            self.slider_progress.set(0)
            self.lbl_elapsed.configure(text="00:00")
            self._elapsed_offset = 0.0
            self.waveform.set_playing(False)
