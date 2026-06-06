from __future__ import annotations

import base64

import requests

from common.exceptions import RecommendationError
from data.models.media_item import MediaItem
from integrations.base_client import BaseApiClient

_AUTH_URL = "https://accounts.spotify.com/api/token"
_BASE_URL = "https://api.spotify.com/v1"

_GENRE_MOOD_MAP = {
    "chill": ["chill", "ambient", "sleep"],
    "energetic": ["workout", "party", "dance"],
    "dark": ["metal", "gothic", "industrial"],
    "nostalgic": ["80s", "90s", "classic"],
    "calm": ["acoustic", "classical", "piano"],
}


class SpotifyClient(BaseApiClient):
    provider_name = "Spotify"

    def __init__(self, client_id: str, client_secret: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token: str | None = None

    def search(self, query: str, **kwargs) -> list[MediaItem]:
        self._ensure_token()
        limit = kwargs.get("limit", 20)
        params = {"q": query, "type": "track,artist", "limit": limit}
        data = self._get("/search", params)
        tracks = data.get("tracks", {}).get("items", [])
        return [self._normalize_track(t) for t in tracks if t]

    def search_by_mood(self, mood: str, limit: int = 20) -> list[MediaItem]:
        genres = _GENRE_MOOD_MAP.get(mood.lower(), [mood])
        query = " OR ".join(f'genre:"{g}"' for g in genres[:2])
        return self.search(query, limit=limit)

    def get_recommendations(self, seed_genres: list[str], limit: int = 20) -> list[MediaItem]:
        self._ensure_token()
        valid_genres = seed_genres[:5] if seed_genres else ["pop"]
        params = {"seed_genres": ",".join(valid_genres), "limit": limit}
        data = self._get("/recommendations", params)
        tracks = data.get("tracks", [])
        return [self._normalize_track(t) for t in tracks if t]

    def _ensure_token(self) -> None:
        if self._access_token:
            return
        credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        try:
            resp = requests.post(
                _AUTH_URL,
                data={"grant_type": "client_credentials"},
                headers={"Authorization": f"Basic {credentials}"},
                timeout=10,
            )
            resp.raise_for_status()
            self._access_token = resp.json()["access_token"]
        except requests.RequestException as exc:
            raise RecommendationError(f"Spotify auth failed: {exc}") from exc

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        try:
            resp = requests.get(
                f"{_BASE_URL}{endpoint}",
                params=params,
                headers={"Authorization": f"Bearer {self._access_token}"},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            raise RecommendationError(f"Spotify request failed: {exc}") from exc

    def _normalize_track(self, raw: dict) -> MediaItem:
        title = raw.get("name") or "Unknown"
        artists = raw.get("artists") or []
        artist_names = ", ".join(a.get("name", "") for a in artists)
        full_title = f"{title} — {artist_names}" if artist_names else title
        album = raw.get("album") or {}
        release_date = album.get("release_date") or ""
        year = int(release_date[:4]) if release_date[:4].isdigit() else None
        popularity_raw = raw.get("popularity") or 0
        track_id = raw.get("id") or ""

        return MediaItem(
            id=f"spotify-track-{track_id}",
            title=full_title,
            media_type="music",
            description=f"By {artist_names}" if artist_names else "",
            release_year=year,
            genres=[],
            moods=[],
            source="Spotify",
            external_id=track_id,
            rating=None,
            popularity=popularity_raw / 100.0,
        )
