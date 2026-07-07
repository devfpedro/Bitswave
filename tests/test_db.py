import pytest

from db import PlaylistDB


@pytest.fixture
def db():
    store = PlaylistDB(":memory:")
    yield store
    store.close()


def test_create_and_list_playlist(db):
    pid = db.create_playlist("Rock Clássico", "Minhas favoritas")
    playlists = db.list_playlists()
    assert len(playlists) == 1
    assert playlists[0]["name"] == "Rock Clássico"
    assert playlists[0]["description"] == "Minhas favoritas"
    assert playlists[0]["order_mode"] == "sequencial"
    assert playlists[0]["track_count"] == 0
    assert playlists[0]["id"] == pid


def test_create_playlist_empty_name_raises(db):
    with pytest.raises(ValueError):
        db.create_playlist("   ")


def test_create_playlist_duplicate_name_raises(db):
    db.create_playlist("Favoritas")
    with pytest.raises(ValueError):
        db.create_playlist("Favoritas")


def test_rename_playlist(db):
    pid = db.create_playlist("Antigo Nome")
    db.rename_playlist(pid, "Novo Nome")
    assert db.get_playlist(pid)["name"] == "Novo Nome"


def test_rename_playlist_duplicate_raises(db):
    db.create_playlist("A")
    pid_b = db.create_playlist("B")
    with pytest.raises(ValueError):
        db.rename_playlist(pid_b, "A")


def test_update_description(db):
    pid = db.create_playlist("Playlist")
    db.update_description(pid, "Nova descrição")
    assert db.get_playlist(pid)["description"] == "Nova descrição"


def test_delete_playlist_removes_tracks(db):
    pid = db.create_playlist("Para Excluir")
    db.add_track(pid, "a.mp3")
    db.delete_playlist(pid)
    assert db.get_playlist(pid) is None
    assert db.get_tracks(pid) == []


def test_add_and_list_tracks_in_position_order(db):
    pid = db.create_playlist("Ordenada")
    db.add_track(pid, "c.mp3")
    db.add_track(pid, "a.mp3")
    db.add_track(pid, "b.mp3")
    tracks = db.get_tracks(pid)
    assert [t["filepath"] for t in tracks] == ["c.mp3", "a.mp3", "b.mp3"]


def test_remove_track(db):
    pid = db.create_playlist("Playlist")
    tid = db.add_track(pid, "a.mp3")
    db.add_track(pid, "b.mp3")
    db.remove_track(tid)
    tracks = db.get_tracks(pid)
    assert len(tracks) == 1
    assert tracks[0]["filepath"] == "b.mp3"


def test_playback_queue_sequencial_matches_position_order(db):
    pid = db.create_playlist("Playlist")
    db.add_track(pid, "c.mp3")
    db.add_track(pid, "a.mp3")
    assert db.get_playback_queue(pid) == ["c.mp3", "a.mp3"]


def test_playback_queue_alfabetica_sorts_by_filename(db):
    pid = db.create_playlist("Playlist")
    db.add_track(pid, "c.mp3")
    db.add_track(pid, "a.mp3")
    db.add_track(pid, "b.mp3")
    db.set_order_mode(pid, "alfabetica")
    assert db.get_playback_queue(pid) == ["a.mp3", "b.mp3", "c.mp3"]


def test_playback_queue_aleatoria_contains_same_items(db):
    pid = db.create_playlist("Playlist")
    for name in ("a.mp3", "b.mp3", "c.mp3", "d.mp3"):
        db.add_track(pid, name)
    db.set_order_mode(pid, "aleatoria")
    queue = db.get_playback_queue(pid)
    assert sorted(queue) == ["a.mp3", "b.mp3", "c.mp3", "d.mp3"]


def test_set_order_mode_invalid_raises(db):
    pid = db.create_playlist("Playlist")
    with pytest.raises(ValueError):
        db.set_order_mode(pid, "invalido")
