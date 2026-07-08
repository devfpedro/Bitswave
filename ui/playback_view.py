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
from folder_watch import resolve_saved_folders
from paths import data_path
from player import AudioPlayer

from . import icons, theme
from .recent_files_panel import RecentFilesPanel
from .tooltip import add_tooltip
from .utils import build_settings_button, ellipsize as _ellipsize, format_time as _format_time
from .waveform import WaveformCanvas

CONFIG_FILE = data_path("player_config.json")


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
        icons.apply_icon(self.btn_menu, "menu", theme.TEXT_PRIMARY, theme.ACCENT)
        add_tooltip(self.btn_menu, "Abrir playlists")

        right_box = ctk.CTkFrame(bar, fg_color="transparent")
        right_box.grid(row=0, column=2, sticky="e")

        self.btn_add = ctk.CTkButton(right_box, text=self.ICON_ADD, command=self._on_add_files, **icon_cfg)
        self.btn_add.pack(side="left")
        icons.apply_icon(self.btn_add, "add", theme.TEXT_PRIMARY, theme.ACCENT)
        add_tooltip(self.btn_add, "Adicionar músicas")

        build_settings_button(right_box, self.app).pack(side="left", padx=(8, 0))

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
        frame.grid(row=4, column=0, sticky="ew", padx=16, pady=(4, 12))

        # Shuffle/repeat ficam numa fileira própria, separada dos 4 botões de transporte
        # principais (prev/play/stop/next). Testes com o app real mostraram que, em janelas
        # estreitas com o Windows em 150% de escala (DPI alta), 6 colunas numa única fileira
        # não cabem de forma confiável — o último botão acaba sem largura para o ícone
        # renderizar. Duas fileiras eliminam esse limite de espaço por completo.
        mode_row = ctk.CTkFrame(frame, fg_color="transparent")
        mode_row.pack(pady=(0, 6))

        mode_cfg = dict(
            width=32, height=32, corner_radius=16, font=ctk.CTkFont(size=13),
            fg_color="transparent", hover_color=theme.CARD_BG_HOVER, text_color=theme.TEXT_SECONDARY,
        )
        self.btn_shuffle = ctk.CTkButton(mode_row, text=self.ICON_SHUFFLE, command=self._on_toggle_shuffle, **mode_cfg)
        self.btn_shuffle.pack(side="left", padx=10)
        icons.apply_icon(self.btn_shuffle, "shuffle", theme.TEXT_SECONDARY, theme.TEXT_PRIMARY)
        add_tooltip(self.btn_shuffle, "Aleatório")

        self.btn_repeat = ctk.CTkButton(mode_row, text=self.ICON_REPEAT, command=self._on_toggle_repeat, **mode_cfg)
        self.btn_repeat.pack(side="left", padx=10)
        add_tooltip(self.btn_repeat, "Repetir faixa atual")
        self._img_repeat = icons.get("repeat", 18, theme.TEXT_SECONDARY)
        self._img_repeat_one = icons.get("repeat_one", 18, theme.TEXT_SECONDARY)
        self._set_repeat_icon()

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(expand=True)

        # Dimensões medidas empiricamente: com ícones-imagem o CTkButton cresce além
        # do width= pedido, e a 150% de DPI a fileira de 4 botões estourava a largura
        # mínima da janela (360px), cortando o botão "próxima". Com 44/58 + ícones
        # 24/20 + padx 3/4 a fileira mede 474px físicos contra 492 disponíveis.
        btn_cfg = dict(
            width=44, height=44, corner_radius=22, font=ctk.CTkFont(size=17),
            fg_color=theme.CARD_BG, hover_color=theme.CARD_BG_HOVER, text_color=theme.TEXT_PRIMARY,
        )

        self.btn_prev = ctk.CTkButton(btn_row, text=self.ICON_PREV, command=self._on_prev, **btn_cfg)
        self.btn_prev.pack(side="left", padx=3)
        icons.apply_icon(self.btn_prev, "prev", theme.TEXT_PRIMARY, theme.ACCENT, size=24, hover_size=26)
        add_tooltip(self.btn_prev, "Anterior")

        self.btn_play = ctk.CTkButton(
            btn_row, text=self.ICON_PLAY, command=self._on_play_pause,
            width=58, height=58, corner_radius=29, font=ctk.CTkFont(size=22),
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
        )
        self.btn_play.pack(side="left", padx=4)
        add_tooltip(self.btn_play, "Reproduzir / Pausar")
        self._img_play = icons.get("play", 20, theme.TEXT_PRIMARY)
        self._img_pause = icons.get("pause", 20, theme.TEXT_PRIMARY)
        self._set_play_icon(False)

        self.btn_stop = ctk.CTkButton(btn_row, text=self.ICON_STOP, command=self._on_stop, **btn_cfg)
        self.btn_stop.pack(side="left", padx=3)
        icons.apply_icon(self.btn_stop, "stop", theme.TEXT_PRIMARY, theme.ACCENT, size=24, hover_size=26)
        add_tooltip(self.btn_stop, "Parar")

        self.btn_next = ctk.CTkButton(btn_row, text=self.ICON_NEXT, command=self._on_next, **btn_cfg)
        self.btn_next.pack(side="left", padx=3)
        icons.apply_icon(self.btn_next, "next", theme.TEXT_PRIMARY, theme.ACCENT, size=24, hover_size=26)
        add_tooltip(self.btn_next, "Próxima")

        vol_row = ctk.CTkFrame(frame, fg_color="transparent")
        vol_row.pack(pady=(14, 0))
        self.lbl_volume_icon = ctk.CTkLabel(
            vol_row, text="", font=ctk.CTkFont(size=16),
            text_color=theme.TEXT_SECONDARY, width=22,
        )
        self.lbl_volume_icon.pack(side="left", padx=(0, 6))
        add_tooltip(self.lbl_volume_icon, "Volume")
        self._img_volume = {
            level: icons.get(f"volume_{level}", 18, theme.TEXT_SECONDARY)
            for level in ("mute", "low", "mid", "high")
        }
        self._set_volume_icon(0.7)
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
            self._set_play_icon(True)
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

        # Respeita a preferência salva de pastas -- inclusive uma lista esvaziada --
        # em vez de recair nas pastas padrão (ver resolve_saved_folders).
        self.app.folder_watcher.folders = resolve_saved_folders(
            data, self.app.folder_watcher.folders
        )

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
        """Abre diálogo para tocar arquivos MP3 avulsos como uma playlist temporária.

        A seleção (1 ou vários arquivos, sem limite) *substitui* a fila atual e vira uma
        "playlist não salva": toca do primeiro em diante, e as faixas seguintes avançam
        em sequência via _auto_next, respeitando Aleatório/Repetir se estiverem ativos
        (o estado desses modos é preservado -- só a fila é trocada). Uma nova seleção
        aqui, ou iniciar uma playlist salva (load_queue), descarta esta fila temporária.
        """
        files = filedialog.askopenfilenames(
            title="Selecionar arquivos MP3", filetypes=[("Arquivos MP3", "*.mp3")],
        )
        if not files:
            return
        self._queue = list(files)
        if self._load_track(0):
            self.player.play()
            self._set_play_icon(True)
            self.waveform.set_playing(True)

    def _reset_now_playing(self) -> None:
        self.lbl_title.configure(text="Nenhuma música selecionada")
        self.lbl_artist.configure(text="")
        self.lbl_duration.configure(text="00:00")
        self.lbl_elapsed.configure(text="00:00")
        self.slider_progress.set(0)
        self._set_play_icon(False)
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
        self.lbl_title.configure(text=_ellipsize(meta["title"], 32))
        self.lbl_artist.configure(text=_ellipsize(meta["artist"], 48))
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
            self._set_play_icon(False)
            self.waveform.set_playing(False)
        elif self.player.is_paused():
            self.player.unpause()
            self._set_play_icon(True)
            self.waveform.set_playing(True)
        else:
            if self._index == -1:
                if not self._load_track(0):
                    return
            self.player.play()
            self._set_play_icon(True)
            self.waveform.set_playing(True)

    def _on_stop(self) -> None:
        self.player.stop()
        self._set_play_icon(False)
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
        self._set_play_icon(True)
        self.waveform.set_playing(True)

    def _on_next(self) -> None:
        if not self._queue:
            return
        if not self._load_track(self._next_index_manual()):
            return
        self.player.play()
        self._set_play_icon(True)
        self.waveform.set_playing(True)

    _VOLUME_TEXT = {"mute": "🔇", "low": "🔈", "mid": "🔉", "high": "🔊"}

    @staticmethod
    def _volume_level_for(value: float) -> str:
        if value <= 0.0:
            return "mute"
        if value < 0.34:
            return "low"
        if value < 0.67:
            return "mid"
        return "high"

    def _set_volume_icon(self, value: float) -> None:
        level = self._volume_level_for(value)
        img = self._img_volume.get(level)
        if img is not None:
            self.lbl_volume_icon.configure(image=img, text="")
        else:
            self.lbl_volume_icon.configure(text=self._VOLUME_TEXT[level])

    def _on_volume_change(self, value: float) -> None:
        self.player.set_volume(value)
        self._set_volume_icon(value)

    def adjust_volume(self, delta: float) -> None:
        """Aumenta/diminui o volume em `delta` (usado pelos atalhos de teclado ↑/↓)."""
        new_volume = max(0.0, min(1.0, self.slider_volume.get() + delta))
        self.slider_volume.set(new_volume)
        self._on_volume_change(new_volume)

    def _on_toggle_shuffle(self) -> None:
        self._shuffle = not self._shuffle
        self.btn_shuffle.configure(fg_color=theme.ACCENT_ACTIVE if self._shuffle else "transparent")

    def _on_toggle_repeat(self) -> None:
        """Liga/desliga a repetição da faixa atual (loop ininterrupto até desativar).

        Alterna apenas entre "off" e "one": ao final da faixa, se ativo, ela recomeça
        do zero indefinidamente (ver _auto_next), independente de haver ou não playlist.
        """
        self._repeat_mode = "one" if self._repeat_mode == "off" else "off"
        self._set_repeat_icon()

    def _set_play_icon(self, playing: bool) -> None:
        """Troca o ícone do botão principal entre play/pause (imagem custom, com fallback de texto)."""
        img = self._img_pause if playing else self._img_play
        if img is not None:
            self.btn_play.configure(image=img, text="")
        else:
            self.btn_play.configure(text=self.ICON_PAUSE if playing else self.ICON_PLAY)

    def _set_repeat_icon(self) -> None:
        """Atualiza o ícone/realce do botão de repetição conforme o modo atual."""
        active = self._repeat_mode == "one"
        img = self._img_repeat_one if active else self._img_repeat
        if img is not None:
            self.btn_repeat.configure(image=img, text="")
        else:
            self.btn_repeat.configure(text=self.ICON_REPEAT_ONE if active else self.ICON_REPEAT)
        self.btn_repeat.configure(fg_color=theme.ACCENT_ACTIVE if active else "transparent")

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
        self._update_spectrum()
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
        self.after(200, self._update_progress)

    def _update_spectrum(self) -> None:
        """Sincroniza a posição do espectro numa cadência alta (~20 fps), separada do
        loop de progresso de 200 ms.

        O espectro é pré-calculado em quadros de ~80 ms; amostrar a posição só a cada
        200 ms (junto do slider/labels) fazia as barras avançarem em degraus de ~5 fps,
        com aparência de travamento/dessincronia. Este tick dedicado atualiza apenas a
        posição consultada pelo WaveformCanvas -- sem redesenhar slider ou textos, que
        não precisam dessa frequência.
        """
        if self.player.is_playing() and not self._seeking and self._current_duration > 0:
            pos_sec = min(self._elapsed_offset + self.player.get_position(), self._current_duration)
            self.waveform.set_position(pos_sec)
        self.after(50, self._update_spectrum)

    def _check_music_end(self) -> None:
        if not self._seeking and self.player.has_finished():
            self._auto_next()
        self.after(500, self._check_music_end)

    def _auto_next(self) -> None:
        if self._repeat_mode == "one":
            if self._load_track(self._index):
                self.player.play()
                self._set_play_icon(True)
                self.waveform.set_playing(True)
            return
        if self._shuffle and len(self._queue) > 1:
            if self._load_track(self._next_index_manual()):
                self.player.play()
                self._set_play_icon(True)
                self.waveform.set_playing(True)
            return
        if self._index < len(self._queue) - 1:
            self._on_next()
        else:
            self.player.stop()
            self._set_play_icon(False)
            self.slider_progress.set(0)
            self.lbl_elapsed.configure(text="00:00")
            self._elapsed_offset = 0.0
            self.waveform.set_playing(False)
