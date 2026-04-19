CREATE TABLE IF NOT EXISTS media_items (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    media_type TEXT NOT NULL,
    description TEXT NOT NULL,
    release_year INTEGER,
    genres_json TEXT NOT NULL DEFAULT '[]',
    moods_json TEXT NOT NULL DEFAULT '[]',
    source TEXT NOT NULL,
    external_id TEXT,
    rating REAL,
    popularity REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS media_embeddings (
    media_id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    embedding_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (media_id) REFERENCES media_items(id)
);

CREATE TABLE IF NOT EXISTS api_cache (
    cache_key TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    response_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
