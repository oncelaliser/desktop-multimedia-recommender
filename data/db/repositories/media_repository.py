from __future__ import annotations

import json
import sqlite3

from data.models.media_item import MediaItem

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS media_items (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    media_type TEXT NOT NULL,
    description TEXT,
    release_year INTEGER,
    genres_json TEXT,
    moods_json TEXT,
    source TEXT,
    external_id TEXT,
    rating REAL,
    popularity REAL
)
"""

_CREATE_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS api_cache (
    cache_key TEXT PRIMARY KEY,
    provider TEXT,
    response_json TEXT,
    created_at TEXT DEFAULT (datetime('now'))
)
"""


class MediaRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection
        self._conn.execute(_CREATE_TABLE)
        self._conn.execute(_CREATE_CACHE_TABLE)
        self._conn.commit()

    def save(self, item: MediaItem) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO media_items
              (id, title, media_type, description, release_year,
               genres_json, moods_json, source, external_id, rating, popularity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.id, item.title, item.media_type, item.description,
                item.release_year, json.dumps(item.genres), json.dumps(item.moods),
                item.source, item.external_id, item.rating, item.popularity,
            ),
        )
        self._conn.commit()

    def save_many(self, items: list[MediaItem]) -> None:
        self._conn.executemany(
            """
            INSERT OR REPLACE INTO media_items
              (id, title, media_type, description, release_year,
               genres_json, moods_json, source, external_id, rating, popularity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.id, item.title, item.media_type, item.description,
                    item.release_year, json.dumps(item.genres), json.dumps(item.moods),
                    item.source, item.external_id, item.rating, item.popularity,
                )
                for item in items
            ],
        )
        self._conn.commit()

    def list_media(self, media_type: str | None = None) -> list[MediaItem]:
        if media_type:
            rows = self._conn.execute(
                "SELECT * FROM media_items WHERE media_type = ?", (media_type,)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM media_items").fetchall()
        return [self._row_to_item(row) for row in rows]

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM media_items").fetchone()[0]

    def cache_get(self, cache_key: str) -> str | None:
        row = self._conn.execute(
            "SELECT response_json FROM api_cache WHERE cache_key = ?", (cache_key,)
        ).fetchone()
        return row[0] if row else None

    def cache_set(self, cache_key: str, provider: str, response_json: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO api_cache (cache_key, provider, response_json) VALUES (?, ?, ?)",
            (cache_key, provider, response_json),
        )
        self._conn.commit()

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> MediaItem:
        return MediaItem(
            id=row["id"],
            title=row["title"],
            media_type=row["media_type"],
            description=row["description"] or "",
            release_year=row["release_year"],
            genres=json.loads(row["genres_json"] or "[]"),
            moods=json.loads(row["moods_json"] or "[]"),
            source=row["source"] or "unknown",
            external_id=row["external_id"],
            rating=row["rating"],
            popularity=row["popularity"],
        )
