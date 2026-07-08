"""Testes de resolução de caminhos gravável/persistente (bug do AppImage read-only)."""
import os
import sys

import paths


def test_data_path_uses_project_root_when_not_frozen(monkeypatch):
    """Rodando de fonte (dev/testes), continua na raiz do projeto -- sem mudança de comportamento."""
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert paths.data_path("audioplayer.db") == os.path.join(paths._PROJECT_ROOT, "audioplayer.db")


def test_data_path_uses_user_data_dir_when_frozen(monkeypatch, tmp_path):
    """Empacotado, usa o diretório de dados do usuário -- nunca a pasta do executável
    (que no AppImage é um mount somente-leitura ou uma extração temporária)."""
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr(sys, "executable", "/tmp/.mount_readonly/usr/bin/bitswave")

    result = paths.data_path("audioplayer.db")
    assert result == os.path.join(str(tmp_path), "Bitswave", "audioplayer.db")
    assert "readonly" not in result  # nunca deriva de sys.executable


def test_user_data_dir_is_created_and_writable(monkeypatch, tmp_path):
    """O diretório retornado existe e aceita escrita (é isso que falhava no AppImage)."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))

    d = paths.user_data_dir()
    assert os.path.isdir(d)
    probe = os.path.join(d, "_write_probe.tmp")
    with open(probe, "w") as f:
        f.write("ok")
    os.remove(probe)
