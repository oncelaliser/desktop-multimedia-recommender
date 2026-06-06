from __future__ import annotations

import requests

from common.exceptions import RecommendationError
from data.models.media_item import MediaItem
from integrations.base_client import BaseApiClient

_BASE_URL = "https://www.omdbapi.com/"

# Curated seed titles per genre — ensures OMDb returns relevant results
# since OMDb is title-search only, not genre-search
_GENRE_SEEDS = {
    "crime":       ["Breaking Bad", "The Wire", "Narcos", "crime thriller"],
    "drama":       ["drama series", "award drama"],
    "comedy":      ["Seinfeld", "sitcom comedy", "Arrested Development"],
    "horror":      ["horror thriller", "supernatural horror"],
    "sci-fi":      ["science fiction series", "space exploration"],
    "action":      ["action thriller", "adventure series"],
    "mystery":     ["mystery detective", "whodunit thriller"],
    "romance":     ["romantic drama", "love story film"],
    "thriller":    ["psychological thriller", "suspense drama"],
    "animation":   ["animated series", "anime"],
    "documentary": ["documentary series", "nature documentary"],
    "chill":       ["feel good series", "slice of life"],
    "fantasy":     ["Game of Thrones", "fantasy epic", "Lord of the Rings"],
}


class OmdbClient(BaseApiClient):
    provider_name = "OMDb"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def search(self, query: str, **kwargs) -> list[MediaItem]:
        """Search by English keyword. Enriches top results with full metadata."""
        media_type = kwargs.get("media_type", "any")
        omdb_type = {"movie": "movie", "series": "series"}.get(media_type, "")
        params: dict = {"s": query, "apikey": self.api_key}
        if omdb_type:
            params["type"] = omdb_type
        data = self._get(params)
        if data.get("Response") == "False":
            return []
        stubs = data.get("Search", [])
        # Enrich top 8 results with full metadata (genres, plot, rating)
        enriched = []
        for stub in stubs[:8]:
            imdb_id = stub.get("imdbID")
            if imdb_id:
                full = self.get_by_imdb_id(imdb_id)
                if full and (full.rating is None or full.rating >= 7.0):
                    enriched.append(full)
                    continue
            item = self._normalize(stub)
            if item.rating is None or item.rating >= 7.0:
                enriched.append(item)
        return enriched

    def search_by_genre(self, genre: str, media_type: str = "any") -> list[MediaItem]:
        """Search using genre seed keywords to get relevant results."""
        seeds = _GENRE_SEEDS.get(genre.lower(), [genre])
        results: list[MediaItem] = []
        seen: set[str] = set()
        for seed in seeds[:2]:
            for item in self.search(seed, media_type=media_type):
                if item.id not in seen:
                    seen.add(item.id)
                    results.append(item)
        return results

    def get_by_imdb_id(self, imdb_id: str) -> MediaItem | None:
        data = self._get({"i": imdb_id, "apikey": self.api_key, "plot": "short"})
        if data.get("Response") == "False":
            return None
        return self._normalize(data)

    def _get(self, params: dict) -> dict:
        try:
            response = requests.get(_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise RecommendationError(f"OMDb request failed: {exc}") from exc

    def _normalize(self, raw: dict) -> MediaItem:
        title = raw.get("Title") or "Unknown"
        year_raw = raw.get("Year") or ""
        year = int(year_raw[:4]) if year_raw[:4].isdigit() else None
        media_type_raw = (raw.get("Type") or "movie").lower()
        media_type = "series" if media_type_raw == "series" else "movie"
        imdb_id = raw.get("imdbID") or ""
        rating_raw = raw.get("imdbRating", "N/A")
        try:
            rating = float(rating_raw)
        except (ValueError, TypeError):
            rating = None
        genre_str = raw.get("Genre") or ""
        genres = [g.strip().lower() for g in genre_str.split(",") if g.strip()]
        description = raw.get("Plot") or ""

        return MediaItem(
            id=f"omdb-{imdb_id}" if imdb_id else f"omdb-{title.lower().replace(' ', '-')}",
            title=title,
            media_type=media_type,
            description=description,
            release_year=year,
            genres=genres,
            moods=[],
            source="OMDb",
            external_id=imdb_id,
            rating=rating,
            popularity=None,
        )
