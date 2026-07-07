"""Camada de persistência das playlists do usuário (SQLite)."""
import os
import random
import sqlite3
from datetime import datetime

DB_FILENAME = "audioplayer.db"
ORDER_MODES = ("sequencial", "alfabetica", "aleatoria")


class PlaylistDB:
    """Acesso ao banco de dados de playlists (SQLite)."""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILENAME)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL DEFAULT '',
                order_mode TEXT NOT NULL DEFAULT 'sequencial',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS playlist_tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
                filepath TEXT NOT NULL,
                position INTEGER NOT NULL
            );
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ------------------------------------------------------------------
    # Playlists
    # ------------------------------------------------------------------

    def create_playlist(self, name: str, description: str = "") -> int:
        """Cria uma playlist e retorna seu id. Levanta ValueError em nome inválido/duplicado."""
        name = name.strip()
        if not name:
            raise ValueError("O nome da playlist não pode ser vazio.")
        try:
            cur = self._conn.execute(
                "INSERT INTO playlists (name, description, order_mode, created_at) "
                "VALUES (?, ?, 'sequencial', ?)",
                (name, description.strip(), datetime.now().isoformat(timespec="seconds")),
            )
        except sqlite3.IntegrityError:
            raise ValueError(f"Já existe uma playlist chamada '{name}'.")
        self._conn.commit()
        return cur.lastrowid

    def list_playlists(self) -> list[sqlite3.Row]:
        """Lista todas as playlists com a contagem de faixas, mais recente primeiro."""
        return self._conn.execute(
            """
            SELECT p.*, COUNT(t.id) AS track_count
            FROM playlists p
            LEFT JOIN playlist_tracks t ON t.playlist_id = p.id
            GROUP BY p.id
            ORDER BY p.created_at DESC
            """
        ).fetchall()

    def get_playlist(self, playlist_id: int) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM playlists WHERE id = ?", (playlist_id,)
        ).fetchone()

    def rename_playlist(self, playlist_id: int, new_name: str) -> None:
        new_name = new_name.strip()
        if not new_name:
            raise ValueError("O nome da playlist não pode ser vazio.")
        try:
            self._conn.execute("UPDATE playlists SET name = ? WHERE id = ?", (new_name, playlist_id))
        except sqlite3.IntegrityError:
            raise ValueError(f"Já existe uma playlist chamada '{new_name}'.")
        self._conn.commit()

    def update_description(self, playlist_id: int, description: str) -> None:
        self._conn.execute(
            "UPDATE playlists SET description = ? WHERE id = ?", (description.strip(), playlist_id)
        )
        self._conn.commit()

    def set_order_mode(self, playlist_id: int, order_mode: str) -> None:
        if order_mode not in ORDER_MODES:
            raise ValueError(f"Modo de ordenação inválido: {order_mode}")
        self._conn.execute(
            "UPDATE playlists SET order_mode = ? WHERE id = ?", (order_mode, playlist_id)
        )
        self._conn.commit()

    def delete_playlist(self, playlist_id: int) -> None:
        self._conn.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
        self._conn.commit()

    # ------------------------------------------------------------------
    # Faixas
    # ------------------------------------------------------------------

    def add_track(self, playlist_id: int, filepath: str) -> int:
        """Adiciona uma faixa ao final da playlist."""
        row = self._conn.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 AS next_pos FROM playlist_tracks WHERE playlist_id = ?",
            (playlist_id,),
        ).fetchone()
        cur = self._conn.execute(
            "INSERT INTO playlist_tracks (playlist_id, filepath, position) VALUES (?, ?, ?)",
            (playlist_id, filepath, row["next_pos"]),
        )
        self._conn.commit()
        return cur.lastrowid

    def remove_track(self, track_id: int) -> None:
        self._conn.execute("DELETE FROM playlist_tracks WHERE id = ?", (track_id,))
        self._conn.commit()

    def get_tracks(self, playlist_id: int) -> list[sqlite3.Row]:
        """Faixas na ordem em que foram adicionadas (ordem de exibição na lista)."""
        return self._conn.execute(
            "SELECT * FROM playlist_tracks WHERE playlist_id = ? ORDER BY position ASC",
            (playlist_id,),
        ).fetchall()

    def get_playback_queue(self, playlist_id: int) -> list[str]:
        """Caminhos das faixas já ordenados conforme order_mode da playlist, prontos para tocar."""
        playlist = self.get_playlist(playlist_id)
        order_mode = playlist["order_mode"] if playlist else "sequencial"
        filepaths = [row["filepath"] for row in self.get_tracks(playlist_id)]
        if order_mode == "alfabetica":
            filepaths.sort(key=lambda f: os.path.splitext(os.path.basename(f))[0].lower())
        elif order_mode == "aleatoria":
            random.shuffle(filepaths)
        return filepaths
