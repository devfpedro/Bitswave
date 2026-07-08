"""Testes do lock de instância única (Windows e Linux)."""
import os

from single_instance import _held_handles, acquire_single_instance_lock


def test_first_instance_gets_the_lock(tmp_path):
    lock = str(tmp_path / "a.lock")
    assert acquire_single_instance_lock(lock) is True


def test_second_instance_is_blocked(tmp_path):
    """Segunda tentativa sobre o mesmo lock (outra 'instância') deve ser barrada."""
    lock = str(tmp_path / "b.lock")
    assert acquire_single_instance_lock(lock) is True
    assert acquire_single_instance_lock(lock) is False


def test_lock_released_when_handle_closed(tmp_path):
    """Liberado o handle (simula fim do processo), uma nova instância consegue o lock de novo."""
    lock = str(tmp_path / "c.lock")
    assert acquire_single_instance_lock(lock) is True
    # simula a morte do processo anterior: fecha e descarta o handle mantido
    handle = _held_handles.pop()
    handle.close()
    assert acquire_single_instance_lock(lock) is True


def test_creates_lock_file(tmp_path):
    lock = str(tmp_path / "d.lock")
    acquire_single_instance_lock(lock)
    assert os.path.isfile(lock)
