import wave

import pytest

from player import AudioPlayer


def _make_silent_wav(path: str, duration_sec: float = 1.0, framerate: int = 8000) -> None:
    n_frames = int(duration_sec * framerate)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        wf.writeframes(b"\x00\x00" * n_frames)


@pytest.fixture
def silent_wav(tmp_path):
    path = str(tmp_path / "silence.wav")
    _make_silent_wav(path)
    return path


@pytest.fixture
def player():
    p = AudioPlayer()
    yield p
    p.cleanup()


def test_load_missing_file_raises(player):
    with pytest.raises(FileNotFoundError):
        player.load("does_not_exist.mp3")


def test_get_duration_invalid_file_returns_zero(tmp_path):
    bogus = tmp_path / "not_audio.mp3"
    bogus.write_text("not an mp3")
    assert AudioPlayer.get_duration(str(bogus)) == 0.0


def test_get_metadata_defaults_to_filename(tmp_path):
    bogus = tmp_path / "My Song.mp3"
    bogus.write_text("not really an mp3")
    meta = AudioPlayer.get_metadata(str(bogus))
    assert meta["title"] == "My Song"
    assert meta["artist"] == "Artista desconhecido"
    assert meta["album"] == "Álbum desconhecido"


def test_play_pause_stop_state_machine(player, silent_wav):
    player.load(silent_wav)
    assert player.current_file == silent_wav
    assert not player.is_playing()

    player.play()
    assert player.is_playing()
    assert not player.is_paused()

    player.pause()
    assert player.is_paused()
    assert not player.is_playing()

    player.unpause()
    assert player.is_playing()

    player.stop()
    assert not player.is_playing()
    assert not player.is_paused()


def test_seek_while_stopped_is_applied_on_next_play(player, silent_wav):
    """Regressão: seek() enquanto parado não pode ser perdido no próximo play()."""
    player.load(silent_wav)
    player.seek(0.5)  # parado -- não deve levantar erro nem iniciar reprodução
    assert not player.is_playing()

    player.play()
    assert player.is_playing()
    assert player._seek_offset == 0.0  # offset pendente foi consumido


def test_stop_resets_pending_seek_offset(player, silent_wav):
    player.load(silent_wav)
    player.seek(0.5)
    player.stop()
    assert player._seek_offset == 0.0


def test_volume_get_set(player):
    player.set_volume(0.3)
    assert player.get_volume() == pytest.approx(0.3, abs=0.01)
    player.set_volume(1.5)  # clamp acima de 1.0
    assert player.get_volume() == pytest.approx(1.0, abs=0.01)
    player.set_volume(-1.0)  # clamp abaixo de 0.0
    assert player.get_volume() == pytest.approx(0.0, abs=0.01)


def test_has_finished_false_when_never_played(player, silent_wav):
    player.load(silent_wav)
    assert not player.has_finished()
