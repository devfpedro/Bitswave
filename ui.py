import os
import tkinter as tk
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from player import AudioPlayer


def _format_time(seconds: float) -> str:
    """Formata segundos para MM:SS."""
    if seconds < 0:
        seconds = 0
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


class AudioPlayerUI(ctk.CTk):
    """Janela principal do reprodutor de músicas."""

    # Ícones Unicode para botões
    ICON_PREV = "⏮"
    ICON_PLAY = "▶"
    ICON_PAUSE = "⏸"
    ICON_STOP = "⏹"
    ICON_NEXT = "⏭"

    def __init__(self, player: AudioPlayer):
        super().__init__()

        self.player = player

        # --- Estado interno ---
        self._playlist: list[str] = []          # caminhos completos dos MP3
        self._current_index: int = -1           # índice da música atual
        self._seeking: bool = False             # True enquanto o usuário arrasta o slider
        self._elapsed_offset: float = 0.0       # offset acumulado para seek
        self._current_duration: float = 0.0     # duração da música atual

        # --- Configuração da janela ---
        self.title("audioPlayer")
        self.geometry("520x640")
        self.minsize(440, 560)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._build_ui()
        self._start_update_loop()

    # ==================================================================
    # Construção da UI
    # ==================================================================

    def _build_ui(self) -> None:
        """Monta todos os widgets da interface."""

        # Container principal com padding
        self.grid_rowconfigure(0, weight=0)   # info
        self.grid_rowconfigure(1, weight=0)   # progresso
        self.grid_rowconfigure(2, weight=0)   # controles
        self.grid_rowconfigure(3, weight=1)   # playlist
        self.grid_rowconfigure(4, weight=0)   # botão adicionar
        self.grid_columnconfigure(0, weight=1)

        self._build_info_frame()
        self._build_progress_frame()
        self._build_controls_frame()
        self._build_playlist_frame()
        self._build_add_button()

    # ------------------------------------------------------------------
    # Seção: Informações da música
    # ------------------------------------------------------------------

    def _build_info_frame(self) -> None:
        frame = ctk.CTkFrame(self, corner_radius=12)
        frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(
            frame, text="Nenhuma música selecionada",
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        )
        self.lbl_title.grid(row=0, column=0, padx=16, pady=(14, 2), sticky="ew")

        self.lbl_artist = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60"),
            anchor="w",
        )
        self.lbl_artist.grid(row=1, column=0, padx=16, pady=(0, 4), sticky="ew")

        self.lbl_album = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray50"),
            anchor="w",
        )
        self.lbl_album.grid(row=2, column=0, padx=16, pady=(0, 14), sticky="ew")

    # ------------------------------------------------------------------
    # Seção: Barra de progresso
    # ------------------------------------------------------------------

    def _build_progress_frame(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=1, column=0, padx=16, pady=4, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)

        self.lbl_elapsed = ctk.CTkLabel(
            frame, text="00:00", font=ctk.CTkFont(size=12), width=46,
        )
        self.lbl_elapsed.grid(row=0, column=0, padx=(0, 6))

        self.slider_progress = ctk.CTkSlider(
            frame, from_=0, to=1, number_of_steps=1000,
            command=self._on_progress_drag,
        )
        self.slider_progress.set(0)
        self.slider_progress.grid(row=0, column=1, sticky="ew")

        # Bind para detectar quando o usuário começa/termina de arrastar
        self.slider_progress.bind("<ButtonPress-1>", self._on_progress_press)
        self.slider_progress.bind("<ButtonRelease-1>", self._on_progress_release)

        self.lbl_duration = ctk.CTkLabel(
            frame, text="00:00", font=ctk.CTkFont(size=12), width=46,
        )
        self.lbl_duration.grid(row=0, column=2, padx=(6, 0))

    # ------------------------------------------------------------------
    # Seção: Controles de reprodução + volume
    # ------------------------------------------------------------------

    def _build_controls_frame(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=2, column=0, padx=16, pady=8, sticky="ew")

        # Sub-frame centralizado para os botões
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(side="left", expand=True)

        btn_cfg = dict(width=48, height=48, corner_radius=24, font=ctk.CTkFont(size=18))

        self.btn_prev = ctk.CTkButton(btn_frame, text=self.ICON_PREV, command=self._on_prev, **btn_cfg)
        self.btn_prev.pack(side="left", padx=4)

        self.btn_play = ctk.CTkButton(
            btn_frame, text=self.ICON_PLAY, command=self._on_play_pause,
            width=56, height=56, corner_radius=28,
            font=ctk.CTkFont(size=22),
            fg_color=("#3B82F6", "#2563EB"),
            hover_color=("#2563EB", "#1D4ED8"),
        )
        self.btn_play.pack(side="left", padx=4)

        self.btn_stop = ctk.CTkButton(btn_frame, text=self.ICON_STOP, command=self._on_stop, **btn_cfg)
        self.btn_stop.pack(side="left", padx=4)

        self.btn_next = ctk.CTkButton(btn_frame, text=self.ICON_NEXT, command=self._on_next, **btn_cfg)
        self.btn_next.pack(side="left", padx=4)

        # Volume
        vol_frame = ctk.CTkFrame(frame, fg_color="transparent")
        vol_frame.pack(side="right", padx=(12, 0))

        lbl_vol = ctk.CTkLabel(vol_frame, text="🔊", font=ctk.CTkFont(size=16))
        lbl_vol.pack(side="left", padx=(0, 4))

        self.slider_volume = ctk.CTkSlider(
            vol_frame, from_=0, to=1, width=100,
            command=self._on_volume_change,
        )
        self.slider_volume.set(0.7)
        self.player.set_volume(0.7)
        self.slider_volume.pack(side="left")

    # ------------------------------------------------------------------
    # Seção: Playlist
    # ------------------------------------------------------------------

    def _build_playlist_frame(self) -> None:
        container = ctk.CTkFrame(self, corner_radius=12)
        container.grid(row=3, column=0, padx=16, pady=8, sticky="nsew")
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        lbl_header = ctk.CTkLabel(
            container, text="Playlist",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        lbl_header.grid(row=0, column=0, padx=14, pady=(10, 4), sticky="w")

        self.playlist_scroll = ctk.CTkScrollableFrame(
            container, corner_radius=8,
        )
        self.playlist_scroll.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="nsew")
        self.playlist_scroll.grid_columnconfigure(0, weight=1)

        # Lista de labels de playlist (para referência e highlight)
        self._playlist_labels: list[ctk.CTkLabel] = []

    # ------------------------------------------------------------------
    # Seção: Botão adicionar
    # ------------------------------------------------------------------

    def _build_add_button(self) -> None:
        self.btn_add = ctk.CTkButton(
            self, text="＋  Adicionar Músicas",
            font=ctk.CTkFont(size=14),
            height=40,
            command=self._on_add_files,
        )
        self.btn_add.grid(row=4, column=0, padx=16, pady=(4, 16), sticky="ew")

    # ==================================================================
    # Callbacks / Eventos
    # ==================================================================

    def _on_add_files(self) -> None:
        """Abre diálogo para selecionar MP3 e adiciona à playlist."""
        files = filedialog.askopenfilenames(
            title="Selecionar arquivos MP3",
            filetypes=[("Arquivos MP3", "*.mp3")],
        )
        for f in files:
            if f not in self._playlist:
                self._playlist.append(f)
                self._add_playlist_label(f, len(self._playlist) - 1)
        # Se nenhuma música está tocando e adicionamos pelo menos uma, seleciona a primeira
        if self._current_index == -1 and self._playlist:
            self._current_index = 0
            self._load_track(0)

    def _add_playlist_label(self, filepath: str, index: int) -> None:
        """Cria um label na playlist para o arquivo."""
        meta = AudioPlayer.get_metadata(filepath)
        display = meta["title"]
        if meta["artist"] != "Artista desconhecido":
            display = f"{meta['artist']}  —  {display}"

        lbl = ctk.CTkLabel(
            self.playlist_scroll,
            text=display,
            font=ctk.CTkFont(size=13),
            anchor="w",
            padx=10,
            pady=6,
            corner_radius=6,
        )
        lbl.grid(row=index, column=0, padx=4, pady=2, sticky="ew")
        lbl.bind("<Double-Button-1>", lambda e, idx=index: self._on_playlist_double_click(idx))
        # Hover effect
        lbl.bind("<Enter>", lambda e, l=lbl: l.configure(fg_color=("gray80", "gray28")))
        lbl.bind("<Leave>", lambda e, l=lbl, idx=index: self._reset_label_color(l, idx))
        self._playlist_labels.append(lbl)

    def _reset_label_color(self, lbl: ctk.CTkLabel, index: int) -> None:
        """Restaura a cor do label (highlight se for a música atual)."""
        if index == self._current_index:
            lbl.configure(fg_color=("#3B82F6", "#1E3A5F"))
        else:
            lbl.configure(fg_color="transparent")

    def _highlight_current(self) -> None:
        """Destaca a música atualmente selecionada na playlist."""
        for i, lbl in enumerate(self._playlist_labels):
            if i == self._current_index:
                lbl.configure(fg_color=("#3B82F6", "#1E3A5F"))
            else:
                lbl.configure(fg_color="transparent")

    def _on_playlist_double_click(self, index: int) -> None:
        """Toca a música clicada na playlist."""
        self._load_track(index)
        self.player.play()
        self.btn_play.configure(text=self.ICON_PAUSE)
        self._highlight_current()

    def _load_track(self, index: int) -> None:
        """Carrega a faixa pelo índice da playlist."""
        if 0 <= index < len(self._playlist):
            self._current_index = index
            filepath = self._playlist[index]
            self.player.load(filepath)
            self._elapsed_offset = 0.0
            self._current_duration = AudioPlayer.get_duration(filepath)

            # Atualizar informações
            meta = AudioPlayer.get_metadata(filepath)
            self.lbl_title.configure(text=meta["title"])
            self.lbl_artist.configure(text=meta["artist"])
            self.lbl_album.configure(text=meta["album"])
            self.lbl_duration.configure(text=_format_time(self._current_duration))
            self.slider_progress.set(0)
            self.lbl_elapsed.configure(text="00:00")
            self._highlight_current()

    def _on_play_pause(self) -> None:
        """Alterna entre play e pause."""
        if not self._playlist:
            return
        if self.player.is_playing():
            self.player.pause()
            self.btn_play.configure(text=self.ICON_PLAY)
        elif self.player.is_paused():
            self.player.unpause()
            self.btn_play.configure(text=self.ICON_PAUSE)
        else:
            # Nada tocando — iniciar
            if self._current_index == -1:
                self._current_index = 0
                self._load_track(0)
            self.player.play()
            self.btn_play.configure(text=self.ICON_PAUSE)

    def _on_stop(self) -> None:
        """Para a reprodução."""
        self.player.stop()
        self.btn_play.configure(text=self.ICON_PLAY)
        self.slider_progress.set(0)
        self.lbl_elapsed.configure(text="00:00")
        self._elapsed_offset = 0.0

    def _on_prev(self) -> None:
        """Vai para a música anterior."""
        if not self._playlist:
            return
        new_index = (self._current_index - 1) % len(self._playlist)
        self._load_track(new_index)
        self.player.play()
        self.btn_play.configure(text=self.ICON_PAUSE)

    def _on_next(self) -> None:
        """Vai para a próxima música."""
        if not self._playlist:
            return
        new_index = (self._current_index + 1) % len(self._playlist)
        self._load_track(new_index)
        self.player.play()
        self.btn_play.configure(text=self.ICON_PAUSE)

    def _on_volume_change(self, value: float) -> None:
        """Atualiza o volume."""
        self.player.set_volume(value)

    # ------------------------------------------------------------------
    # Barra de progresso — interação do usuário
    # ------------------------------------------------------------------

    def _on_progress_press(self, event) -> None:
        """Chamado quando o usuário começa a arrastar o slider de progresso."""
        self._seeking = True

    def _on_progress_drag(self, value: float) -> None:
        """Atualiza o label de tempo enquanto o slider é arrastado."""
        if self._current_duration > 0:
            self.lbl_elapsed.configure(text=_format_time(value * self._current_duration))

    def _on_progress_release(self, event) -> None:
        """Chamado quando o usuário solta o slider — executa o seek."""
        self._seeking = False
        if self._current_duration > 0 and self.player.current_file:
            target = self.slider_progress.get() * self._current_duration
            self._elapsed_offset = target
            self.player.seek(target)

    # ==================================================================
    # Loop de atualização
    # ==================================================================

    def _start_update_loop(self) -> None:
        """Inicia o loop periódico de atualização da UI."""
        self._update_progress()
        self._check_music_end()

    def _update_progress(self) -> None:
        """Atualiza a barra de progresso a cada 200ms."""
        if self.player.is_playing() and not self._seeking and self._current_duration > 0:
            # pygame.mixer.music.get_pos() retorna ms desde o último play()
            pos_sec = self._elapsed_offset + (self.player.get_position())
            if pos_sec > self._current_duration:
                pos_sec = self._current_duration
            fraction = pos_sec / self._current_duration
            self.slider_progress.set(fraction)
            self.lbl_elapsed.configure(text=_format_time(pos_sec))
        self.after(200, self._update_progress)

    def _check_music_end(self) -> None:
        """Verifica se a música terminou para auto-avançar na playlist."""
        # pygame.event não funciona bem sem display, então checamos via mixer
        if (self.player._playing and not self.player._paused
                and not self.player.is_playing()
                and not self._seeking):
            # A música pode ter terminado — verificar se get_pos retorna -1
            raw_pos = self.player.get_position()
            # get_position retorna 0 quando parado; mixer.music.get_busy() é mais confiável
            import pygame
            if not pygame.mixer.music.get_busy():
                self._auto_next()
        self.after(500, self._check_music_end)

    def _auto_next(self) -> None:
        """Avança automaticamente para a próxima música."""
        if self._current_index < len(self._playlist) - 1:
            self._on_next()
        else:
            # Fim da playlist — parar
            self.player.stop()
            self.player._playing = False
            self.btn_play.configure(text=self.ICON_PLAY)
            self.slider_progress.set(0)
            self.lbl_elapsed.configure(text="00:00")
            self._elapsed_offset = 0.0

    # ==================================================================
    # Cleanup
    # ==================================================================

    def on_closing(self) -> None:
        """Libera recursos ao fechar a janela."""
        self.player.cleanup()
        self.destroy()
