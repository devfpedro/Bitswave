import os
import pygame
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, ID3NoHeaderError


class AudioPlayer:
    """Gerencia a reprodução de arquivos MP3 usando pygame.mixer."""

    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        self._current_file: str | None = None
        self._paused: bool = False
        self._playing: bool = False
        self._seek_offset: float = 0.0  # posição pendente a aplicar no próximo play()
        # Evento customizado disparado quando a música termina
        self.MUSIC_END_EVENT = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.MUSIC_END_EVENT)

    # ------------------------------------------------------------------
    # Controles de reprodução
    # ------------------------------------------------------------------

    def load(self, filepath: str) -> None:
        """Carrega um arquivo MP3 para reprodução.

        Levanta FileNotFoundError se o caminho não existir, ou pygame.error
        se o arquivo existir mas não puder ser decodificado (corrompido/formato
        inválido). O chamador é responsável por tratar esses erros.
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        pygame.mixer.music.load(filepath)
        self._current_file = filepath
        self._paused = False
        self._playing = False
        self._seek_offset = 0.0

    def play(self) -> None:
        """Inicia a reprodução do arquivo carregado (respeitando um seek pendente)."""
        if self._current_file is None:
            return
        if self._paused:
            pygame.mixer.music.unpause()
            self._paused = False
        else:
            pygame.mixer.music.play(start=self._seek_offset)
            self._seek_offset = 0.0
        self._playing = True

    def pause(self) -> None:
        """Pausa a reprodução atual."""
        if self._playing and not self._paused:
            pygame.mixer.music.pause()
            self._paused = True

    def unpause(self) -> None:
        """Retoma a reprodução pausada."""
        if self._paused:
            pygame.mixer.music.unpause()
            self._paused = False

    def stop(self) -> None:
        """Para a reprodução completamente e reseta a posição."""
        pygame.mixer.music.stop()
        self._playing = False
        self._paused = False
        self._seek_offset = 0.0

    def set_volume(self, level: float) -> None:
        """Define o volume (0.0 a 1.0)."""
        pygame.mixer.music.set_volume(max(0.0, min(1.0, level)))

    def get_volume(self) -> float:
        """Retorna o volume atual."""
        return pygame.mixer.music.get_volume()

    def seek(self, position_sec: float) -> None:
        """Pula para uma posição específica (em segundos).

        Funciona mesmo se a reprodução estiver parada: a posição fica
        pendente e é aplicada no próximo play(), evitando que a barra de
        progresso fique dessincronizada da reprodução real.
        """
        if self._current_file is None:
            return
        self._seek_offset = position_sec
        if self._playing:
            pygame.mixer.music.play(start=position_sec)
            if self._paused:
                pygame.mixer.music.pause()

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------

    def get_position(self) -> float:
        """Retorna a posição atual da reprodução em segundos."""
        if self._playing and not self._paused:
            return pygame.mixer.music.get_pos() / 1000.0
        return 0.0

    def is_playing(self) -> bool:
        """Retorna True se há uma música sendo reproduzida (não pausada)."""
        return self._playing and not self._paused

    def is_paused(self) -> bool:
        """Retorna True se a reprodução está pausada."""
        return self._paused

    def has_finished(self) -> bool:
        """True se uma faixa estava tocando e o mixer parou sozinho (fim da música)."""
        return self._playing and not self._paused and not pygame.mixer.music.get_busy()

    @property
    def current_file(self) -> str | None:
        """Caminho do arquivo atualmente carregado."""
        return self._current_file

    # ------------------------------------------------------------------
    # Metadados
    # ------------------------------------------------------------------

    @staticmethod
    def get_duration(filepath: str) -> float:
        """Retorna a duração do arquivo MP3 em segundos."""
        try:
            audio = MP3(filepath)
            return audio.info.length
        except Exception:
            return 0.0

    @staticmethod
    def get_metadata(filepath: str) -> dict:
        """
        Retorna metadados ID3 do arquivo MP3.

        Returns:
            dict com chaves: title, artist, album.
            Valores padrão são o nome do arquivo / "Desconhecido".
        """
        basename = os.path.splitext(os.path.basename(filepath))[0]
        metadata = {
            "title": basename,
            "artist": "Artista desconhecido",
            "album": "Álbum desconhecido",
        }
        try:
            tags = ID3(filepath)
            if tags.get("TIT2"):
                metadata["title"] = str(tags["TIT2"])
            if tags.get("TPE1"):
                metadata["artist"] = str(tags["TPE1"])
            if tags.get("TALB"):
                metadata["album"] = str(tags["TALB"])
        except ID3NoHeaderError:
            pass
        except Exception:
            pass
        return metadata

    @staticmethod
    def get_cover_art(filepath: str) -> bytes | None:
        """Retorna os bytes da capa embutida (tag APIC) do MP3, se houver."""
        try:
            tags = ID3(filepath)
            apic_frames = tags.getall("APIC")
            if apic_frames:
                return apic_frames[0].data
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        """Libera recursos do mixer."""
        pygame.mixer.music.stop()
        pygame.mixer.quit()
