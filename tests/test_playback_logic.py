"""Testes da lógica de avanço de faixa (T6: Aleatório e Repetir).

Exercita _next_index_manual/_prev_index_manual como funções puras (via método
não-ligado sobre um stub), sem precisar instanciar a UI Tk real -- esses métodos
dependem apenas de self._shuffle, self._queue e self._index.
"""
import types
from unittest import mock

from ui.playback_view import PlaybackView


def _stub(queue, index, shuffle):
    s = types.SimpleNamespace()
    s._queue = list(queue)
    s._index = index
    s._shuffle = shuffle
    return s


def test_sequential_next_without_shuffle():
    s = _stub(["a", "b", "c"], index=0, shuffle=False)
    assert PlaybackView._next_index_manual(s) == 1
    s._index = 2
    assert PlaybackView._next_index_manual(s) == 0  # dá a volta


def test_sequential_prev_without_shuffle():
    s = _stub(["a", "b", "c"], index=0, shuffle=False)
    assert PlaybackView._prev_index_manual(s) == 2  # dá a volta para trás


def test_shuffle_never_repeats_current_and_stays_in_range():
    """Aleatório em playlist de 3+ faixas: 30 sorteios nunca caem no índice atual."""
    s = _stub(["a", "b", "c", "d"], index=1, shuffle=True)
    seen = set()
    for _ in range(30):
        nxt = PlaybackView._next_index_manual(s)
        assert 0 <= nxt < len(s._queue)
        assert nxt != s._index
        seen.add(nxt)
    assert seen == {0, 2, 3}  # cobre todas as outras faixas, nenhuma sequencial fixa


def test_shuffle_not_purely_sequential_over_many_advances():
    """Critério T6: com Aleatório, 10 avanços não seguem a ordem sequencial original."""
    s = _stub(["a", "b", "c", "d", "e"], index=0, shuffle=True)
    results = []
    for _ in range(10):
        s._index = PlaybackView._next_index_manual(s)
        results.append(s._index)
    sequential = [(i + 1) % 5 for i in range(10)]  # 1,2,3,4,0,1,2,3,4,0
    assert results != sequential


def test_shuffle_single_track_is_noop():
    """Faixa única (sem playlist): Aleatório não muda o comportamento -- fica na faixa 0."""
    s = _stub(["only"], index=0, shuffle=True)
    assert PlaybackView._next_index_manual(s) == 0
    assert PlaybackView._prev_index_manual(s) == 0


def _auto_next_stub(queue, index, repeat_mode, shuffle=False):
    s = types.SimpleNamespace()
    s._queue = list(queue)
    s._index = index
    s._repeat_mode = repeat_mode
    s._shuffle = shuffle
    s._load_track = mock.Mock(return_value=True)
    s.player = mock.Mock()
    s.waveform = mock.Mock()
    s._set_play_icon = mock.Mock()
    s._on_next = mock.Mock()
    s.slider_progress = mock.Mock()
    s.lbl_elapsed = mock.Mock()
    s._elapsed_offset = 0.0
    return s


def test_repeat_one_restarts_current_track_five_cycles():
    """Critério T6: com Repetir ativo, a faixa atual reinicia >=5 vezes sem avançar."""
    s = _auto_next_stub(["a", "b", "c"], index=1, repeat_mode="one")
    for _ in range(5):
        PlaybackView._auto_next(s)
    # sempre recarregou a MESMA faixa (índice 1); nunca chamou o avanço sequencial
    assert s._load_track.call_count == 5
    assert all(call.args == (1,) for call in s._load_track.call_args_list)
    s._on_next.assert_not_called()


def test_no_repeat_advances_to_next_track():
    """Sem Repetir, ao terminar uma faixa no meio da fila, avança para a próxima."""
    s = _auto_next_stub(["a", "b", "c"], index=0, repeat_mode="off")
    PlaybackView._auto_next(s)
    s._on_next.assert_called_once()


def test_no_repeat_stops_at_end_of_queue():
    """Sem Repetir, ao terminar a última faixa, para (não reinicia a playlist)."""
    s = _auto_next_stub(["a", "b", "c"], index=2, repeat_mode="off")
    PlaybackView._auto_next(s)
    s._on_next.assert_not_called()
    s.player.stop.assert_called_once()


def _spectrum_stub(playing, seeking, duration, offset, position):
    s = types.SimpleNamespace()
    s.player = mock.Mock()
    s.player.is_playing.return_value = playing
    s.player.get_position.return_value = position
    s._seeking = seeking
    s._current_duration = duration
    s._elapsed_offset = offset
    s.waveform = mock.Mock()
    s.after = mock.Mock()
    s._update_spectrum = mock.Mock()  # referenciado no reagendamento self.after(...)
    return s


def test_spectrum_position_fed_at_high_rate_when_playing():
    """T1: a posição do espectro é alimentada e reagendada a 50 ms (não a 200 ms)."""
    s = _spectrum_stub(playing=True, seeking=False, duration=100.0, offset=10.0, position=3.0)
    PlaybackView._update_spectrum(s)
    s.waveform.set_position.assert_called_once_with(13.0)
    assert s.after.call_args.args[0] == 50  # cadência alta, desacoplada do loop de 200 ms


def test_spectrum_position_clamped_to_duration():
    """A posição nunca ultrapassa a duração da faixa (evita indexar quadro inexistente)."""
    s = _spectrum_stub(playing=True, seeking=False, duration=5.0, offset=4.0, position=10.0)
    PlaybackView._update_spectrum(s)
    s.waveform.set_position.assert_called_once_with(5.0)


def test_spectrum_position_not_fed_when_paused_or_seeking():
    """Pausado ou arrastando o slider: não empurra posição (barras ficam paradas/estáveis)."""
    paused = _spectrum_stub(playing=False, seeking=False, duration=100.0, offset=0.0, position=1.0)
    PlaybackView._update_spectrum(paused)
    paused.waveform.set_position.assert_not_called()

    seeking = _spectrum_stub(playing=True, seeking=True, duration=100.0, offset=0.0, position=1.0)
    PlaybackView._update_spectrum(seeking)
    seeking.waveform.set_position.assert_not_called()
