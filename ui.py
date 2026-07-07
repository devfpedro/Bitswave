import json
import os
import random
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Callable

import customtkinter as ctk
import pygame

from player import AudioPlayer

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "player_config.json")


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
    ICON_SHUFFLE = "🔀"
    ICON_REPEAT = "🔁"
    ICON_REPEAT_ONE = "🔂"

    _ACTIVE_COLOR = ("#3B82F6", "#2563EB")

    def __init__(self, player: AudioPlayer):
        super().__init__()

        self.player = player

        # --- Estado interno ---
        self._playlist: list[str] = []          # caminhos completos dos MP3
        self._current_index: int = -1           # índice da música atual
        self._seeking: bool = False             # True enquanto o usuário arrasta o slider
        self._elapsed_offset: float = 0.0       # offset acumulado para seek
        self._current_duration: float = 0.0     # duração da música atual
        self._shuffle: bool = False             # modo aleatório
        self._repeat_mode: str = "off"          # "off" | "all" | "one"

        # --- Configuração da janela ---
        self.title("audioPlayer")
        self.geometry("520x640")
        self.minsize(440, 560)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._build_ui()
        self._bind_shortcuts()
        self._load_saved_state()
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
        mode_btn_cfg = dict(
            width=36, height=36, corner_radius=18, font=ctk.CTkFont(size=14),
            fg_color="transparent", text_color=("gray30", "gray70"),
        )

        self.btn_shuffle = ctk.CTkButton(
            btn_frame, text=self.ICON_SHUFFLE, command=self._on_toggle_shuffle, **mode_btn_cfg,
        )
        self.btn_shuffle.pack(side="left", padx=(0, 8))

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

        self.btn_repeat = ctk.CTkButton(
            btn_frame, text=self.ICON_REPEAT, command=self._on_cycle_repeat, **mode_btn_cfg,
        )
        self.btn_repeat.pack(side="left", padx=(8, 0))

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

    # ------------------------------------------------------------------
    # Atalhos de teclado
    # ------------------------------------------------------------------

    def _bind_shortcuts(self) -> None:
        """Espaço = play/pause, setas = seek, Ctrl+setas = faixa anterior/próxima."""
        self.bind("<space>", lambda e: self._on_play_pause())
        self.bind("<Left>", lambda e: self._on_seek_relative(-5))
        self.bind("<Right>", lambda e: self._on_seek_relative(5))
        self.bind("<Control-Left>", lambda e: self._on_prev())
        self.bind("<Control-Right>", lambda e: self._on_next())

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
        lbl.bind("<Button-3>", lambda e, idx=index: self._show_playlist_context_menu(e, idx))
        # Hover effect
        lbl.bind("<Enter>", lambda e, l=lbl: l.configure(fg_color=("gray80", "gray28")))
        lbl.bind("<Leave>", lambda e, l=lbl, idx=index: self._reset_label_color(l, idx))
        self._playlist_labels.append(lbl)

    def _show_playlist_context_menu(self, event, index: int) -> None:
        """Exibe menu de contexto (botão direito) com a opção de remover a faixa."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Remover da playlist", command=lambda: self._remove_from_playlist(index))
        menu.tk_popup(event.x_root, event.y_root)

    def _remove_from_playlist(self, index: int) -> None:
        """Remove uma faixa da playlist pelo índice, ajustando o estado de reprodução."""
        if not (0 <= index < len(self._playlist)):
            return
        removing_current = index == self._current_index
        del self._playlist[index]
        if removing_current:
            self.player.stop()
            self._current_index = -1
            self._current_duration = 0.0
            self._elapsed_offset = 0.0
            self.lbl_title.configure(text="Nenhuma música selecionada")
            self.lbl_artist.configure(text="")
            self.lbl_album.configure(text="")
            self.lbl_duration.configure(text="00:00")
            self.lbl_elapsed.configure(text="00:00")
            self.slider_progress.set(0)
            self.btn_play.configure(text=self.ICON_PLAY)
        elif index < self._current_index:
            self._current_index -= 1
        self._rebuild_playlist_ui()

    def _rebuild_playlist_ui(self) -> None:
        """Recria todos os labels da playlist (usado após remoção de faixas)."""
        for lbl in self._playlist_labels:
            lbl.destroy()
        self._playlist_labels = []
        for i, filepath in enumerate(self._playlist):
            self._add_playlist_label(filepath, i)
        self._highlight_current()

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
        if not self._load_track(index):
            return
        self.player.play()
        self.btn_play.configure(text=self.ICON_PAUSE)
        self._highlight_current()

    def _load_track(self, index: int) -> bool:
        """Carrega a faixa pelo índice da playlist.

        Retorna False (e remove a faixa da playlist) se o arquivo não existir
        mais ou estiver corrompido/inválido, em vez de derrubar a aplicação.
        """
        if not (0 <= index < len(self._playlist)):
            return False
        filepath = self._playlist[index]
        try:
            self.player.load(filepath)
        except (FileNotFoundError, pygame.error) as exc:
            messagebox.showerror(
                "Erro ao carregar música",
                f"Não foi possível carregar o arquivo:\n{filepath}\n\n{exc}",
            )
            self._remove_from_playlist(index)
            return False

        self._current_index = index
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
        return True

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
                if not self._load_track(0):
                    return
            self.player.play()
            self.btn_play.configure(text=self.ICON_PAUSE)

    def _on_stop(self) -> None:
        """Para a reprodução."""
        self.player.stop()
        self.btn_play.configure(text=self.ICON_PLAY)
        self.slider_progress.set(0)
        self.lbl_elapsed.configure(text="00:00")
        self._elapsed_offset = 0.0

    def _next_index_manual(self) -> int:
        """Índice da próxima faixa (aleatório se shuffle estiver ativo)."""
        if self._shuffle and len(self._playlist) > 1:
            choices = [i for i in range(len(self._playlist)) if i != self._current_index]
            return random.choice(choices)
        return (self._current_index + 1) % len(self._playlist)

    def _prev_index_manual(self) -> int:
        """Índice da faixa anterior (aleatório se shuffle estiver ativo)."""
        if self._shuffle and len(self._playlist) > 1:
            choices = [i for i in range(len(self._playlist)) if i != self._current_index]
            return random.choice(choices)
        return (self._current_index - 1) % len(self._playlist)

    def _on_prev(self) -> None:
        """Vai para a música anterior."""
        if not self._playlist:
            return
        if not self._load_track(self._prev_index_manual()):
            return
        self.player.play()
        self.btn_play.configure(text=self.ICON_PAUSE)

    def _on_next(self) -> None:
        """Vai para a próxima música."""
        if not self._playlist:
            return
        if not self._load_track(self._next_index_manual()):
            return
        self.player.play()
        self.btn_play.configure(text=self.ICON_PAUSE)

    def _on_volume_change(self, value: float) -> None:
        """Atualiza o volume."""
        self.player.set_volume(value)

    def _on_toggle_shuffle(self) -> None:
        """Ativa/desativa o modo aleatório."""
        self._shuffle = not self._shuffle
        self.btn_shuffle.configure(fg_color=self._ACTIVE_COLOR if self._shuffle else "transparent")

    def _on_cycle_repeat(self) -> None:
        """Alterna entre repetir desligado / playlist inteira / faixa atual."""
        order = ["off", "all", "one"]
        self._repeat_mode = order[(order.index(self._repeat_mode) + 1) % len(order)]
        icon = self.ICON_REPEAT_ONE if self._repeat_mode == "one" else self.ICON_REPEAT
        active = self._repeat_mode != "off"
        self.btn_repeat.configure(text=icon, fg_color=self._ACTIVE_COLOR if active else "transparent")

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

    def _on_seek_relative(self, delta: float) -> None:
        """Avança/retrocede a posição atual em `delta` segundos (atalhos de teclado)."""
        if not self.player.current_file or self._current_duration <= 0:
            return
        current = self._elapsed_offset + self.player.get_position()
        target = max(0.0, min(self._current_duration, current + delta))
        self._elapsed_offset = target
        self.player.seek(target)
        self.slider_progress.set(target / self._current_duration)
        self.lbl_elapsed.configure(text=_format_time(target))

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
        if not self._seeking and self.player.has_finished():
            self._auto_next()
        self.after(500, self._check_music_end)

    def _auto_next(self) -> None:
        """Avança automaticamente para a próxima música (respeitando repeat/shuffle)."""
        if self._repeat_mode == "one":
            if self._load_track(self._current_index):
                self.player.play()
                self.btn_play.configure(text=self.ICON_PAUSE)
            return
        if self._shuffle and len(self._playlist) > 1:
            if self._load_track(self._next_index_manual()):
                self.player.play()
                self.btn_play.configure(text=self.ICON_PAUSE)
            return
        if self._current_index < len(self._playlist) - 1:
            self._on_next()
        elif self._repeat_mode == "all" and self._playlist:
            if self._load_track(0):
                self.player.play()
                self.btn_play.configure(text=self.ICON_PAUSE)
        else:
            # Fim da playlist — parar
            self.player.stop()
            self.btn_play.configure(text=self.ICON_PLAY)
            self.slider_progress.set(0)
            self.lbl_elapsed.configure(text="00:00")
            self._elapsed_offset = 0.0

    # ==================================================================
    # Persistência entre sessões
    # ==================================================================

    def _load_saved_state(self) -> None:
        """Restaura playlist, faixa atual e volume salvos na sessão anterior."""
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
            self.player.set_volume(volume)

        for filepath in data.get("playlist", []):
            if isinstance(filepath, str) and os.path.isfile(filepath) and filepath not in self._playlist:
                self._playlist.append(filepath)
                self._add_playlist_label(filepath, len(self._playlist) - 1)

        last_index = data.get("current_index", -1)
        if isinstance(last_index, int) and 0 <= last_index < len(self._playlist):
            self._load_track(last_index)

    def _save_state(self) -> None:
        """Salva playlist, faixa atual e volume para a próxima sessão."""
        data = {
            "playlist": self._playlist,
            "current_index": self._current_index,
            "volume": self.slider_volume.get(),
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    # ==================================================================
    # Cleanup
    # ==================================================================

    def on_closing(self) -> None:
        """Salva o estado e libera recursos ao fechar a janela."""
        self._save_state()
        self.player.cleanup()
        self.destroy()
