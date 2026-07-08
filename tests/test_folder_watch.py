"""Testes da resolução de pastas monitoradas (T4: remoção deve persistir)."""
import os

from folder_watch import default_watch_folders, resolve_saved_folders


def test_default_watch_folders_are_existing_dirs():
    """Multiplataforma (T8): retorna uma lista de diretórios existentes, sem duplicatas."""
    folders = default_watch_folders()
    assert isinstance(folders, list)
    assert all(os.path.isdir(f) for f in folders)
    assert len(folders) == len(set(folders))


def test_key_absent_uses_defaults():
    """Sem preferência salva, cai nas pastas padrão (comportamento de primeira execução)."""
    defaults = [os.getcwd()]
    assert resolve_saved_folders({}, defaults) == defaults


def test_empty_list_is_respected(tmp_path):
    """Lista vazia salva = usuário removeu todas; NÃO deve voltar às padrão (bug T4)."""
    defaults = [str(tmp_path)]
    assert resolve_saved_folders({"watch_folders": []}, defaults) == []


def test_saved_folders_win_over_defaults(tmp_path):
    """Uma pasta salva substitui as padrão e caminhos inexistentes são descartados."""
    kept = tmp_path / "Musica"
    kept.mkdir()
    missing = str(tmp_path / "nao_existe")
    result = resolve_saved_folders(
        {"watch_folders": [str(kept), missing]}, [os.getcwd()]
    )
    assert result == [str(kept)]


def test_removal_survives_repeated_reloads(tmp_path):
    """Remover uma pasta e recarregar 3x seguidas não a traz de volta (critério de aceite T4)."""
    keep = tmp_path / "Downloads"
    keep.mkdir()
    remove = tmp_path / "Musicas"
    remove.mkdir()
    defaults = [str(keep), str(remove)]

    # usuário removeu "Musicas", sobrou só "Downloads" na preferência salva
    saved = {"watch_folders": [str(keep)]}
    for _ in range(3):
        result = resolve_saved_folders(saved, defaults)
        assert str(remove) not in result
        assert result == [str(keep)]
