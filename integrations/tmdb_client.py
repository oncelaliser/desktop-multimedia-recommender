from __future__ import annotations

import requests

from common.exceptions import RecommendationError
from data.models.media_item import MediaItem
from integrations.base_client import BaseApiClient

_BASE_URL = "https://api.themoviedb.org/3"

_MOVIE_GENRE_MAP = {
    28: "action", 12: "adventure", 16: "animation", 35: "comedy", 80: "crime",
    99: "documentary", 18: "drama", 10751: "family", 14: "fantasy", 36: "history",
    27: "horror", 10402: "music", 9648: "mystery", 10749: "romance",
    878: "sci-fi", 53: "thriller", 10752: "war", 37: "western",
}
_TV_GENRE_MAP = {
    10759: "action", 16: "animation", 35: "comedy", 80: "crime",
    99: "documentary", 18: "drama", 10751: "family",
    10765: "fantasy",  # Sci-Fi & Fantasy (TV)
    27: "horror", 9648: "mystery", 10749: "romance",
    53: "thriller", 10768: "war",
}
_GENRE_MAP = {**_MOVIE_GENRE_MAP, **_TV_GENRE_MAP}

_MOVIE_NAME_TO_ID = {v: k for k, v in _MOVIE_GENRE_MAP.items()}
_TV_NAME_TO_ID = {v: k for k, v in _TV_GENRE_MAP.items()}

_GENRE_MOOD_MAP = {
    "horror": ["dark"], "thriller": ["dark"], "crime": ["dark"],
    "comedy": ["calm"], "animation": ["calm"], "documentary": ["calm"],
    "sci-fi": ["energetic", "surreal"], "action": ["energetic"],
    "fantasy": ["energetic"], "romance": ["calm"],
    "mystery": ["dark", "surreal"], "drama": [],
}


class TmdbClient(BaseApiClient):
    provider_name = "TMDB"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._session = requests.Session()
        self._session.params = {"api_key": api_key, "language": "en-US"}  # type: ignore[assignment]

    def search(self, query: str, media_type: str = "any", page: int = 1) -> list[MediaItem]:
        movies = self._search_movies(query, page) if media_type in ("movie", "any") else []
        series = self._search_tv(query, page) if media_type in ("series", "any") else []
        return movies + series

    def discover_by_genre(
        self,
        genre: str,
        media_type: str = "movie",
        page: int = 1,
        year_from: int | None = None,
        year_to: int | None = None,
        language: str | None = None,
    ) -> list[MediaItem]:
        genre_id = self._genre_name_to_id(genre, media_type)
        if not genre_id:
            return []
        is_tv = media_type == "tv"
        endpoint = f"/discover/{'tv' if is_tv else 'movie'}"
        params: dict = {
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "page": page,
            "vote_count.gte": 50 if language else (100 if is_tv else 200),
        }
        if language:
            params["with_original_language"] = language
        if year_from and year_to:
            if is_tv:
                params["first_air_date.gte"] = f"{year_from}-01-01"
                params["first_air_date.lte"] = f"{year_to}-12-31"
            else:
                params["primary_release_date.gte"] = f"{year_from}-01-01"
                params["primary_release_date.lte"] = f"{year_to}-12-31"
        data = self._get(endpoint, params)
        kind = "series" if is_tv else "movie"
        return [
            self._normalize(item, kind)
            for item in data.get("results", [])
            if item.get("title") or item.get("name")
        ]

    def _search_movies(self, query: str, page: int) -> list[MediaItem]:
        data = self._get("/search/movie", {"query": query, "page": page})
        return [self._normalize(item, "movie") for item in data.get("results", []) if item.get("title")]

    def _search_tv(self, query: str, page: int) -> list[MediaItem]:
        data = self._get("/search/tv", {"query": query, "page": page})
        return [self._normalize(item, "series") for item in data.get("results", []) if item.get("name")]

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        try:
            response = self._session.get(f"{_BASE_URL}{endpoint}", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise RecommendationError(f"TMDB request failed: {exc}") from exc

    def _normalize(self, raw: dict, media_type: str) -> MediaItem:
        title = raw.get("title") or raw.get("name") or "Unknown"
        description = raw.get("overview") or ""
        release_date = raw.get("release_date") or raw.get("first_air_date") or ""
        year = int(release_date[:4]) if release_date and release_date[:4].isdigit() else None
        genre_ids: list[int] = raw.get("genre_ids") or []
        genres = list(dict.fromkeys(_GENRE_MAP[gid] for gid in genre_ids if gid in _GENRE_MAP))
        moods: list[str] = []
        for g in genres:
            moods.extend(_GENRE_MOOD_MAP.get(g, []))
        moods = list(dict.fromkeys(moods))
        rating = raw.get("vote_average") or None
        popularity_raw = raw.get("popularity") or 0.0
        popularity = min(popularity_raw / 100.0, 1.0)
        external_id = str(raw.get("id", ""))

        return MediaItem(
            id=f"tmdb-{media_type}-{external_id}",
            title=title,
            media_type=media_type,
            description=description,
            release_year=year,
            genres=genres,
            moods=moods,
            source="TMDB",
            external_id=external_id,
            rating=rating,
            popularity=popularity,
        )

    def _genre_name_to_id(self, genre_name: str, media_type: str) -> int | None:
        lookup = _TV_NAME_TO_ID if media_type == "tv" else _MOVIE_NAME_TO_ID
        return lookup.get(genre_name.lower())
