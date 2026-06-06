from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    tmdb_api_key: str | None
    omdb_api_key: str | None
    spotify_client_id: str | None
    spotify_client_secret: str | None
    openai_api_key: str | None
    openai_base_url: str
    openai_model: str
    lmstudio_base_url: str
    lmstudio_model: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            tmdb_api_key=os.getenv("TMDB_API_KEY") or None,
            omdb_api_key=os.getenv("OMDB_API_KEY") or None,
            spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID") or None,
            spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET") or None,
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            lmstudio_base_url=os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"),
            lmstudio_model=os.getenv("LMSTUDIO_MODEL", "local-model"),
        )
