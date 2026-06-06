from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MediaItem:
    id: str
    title: str
    media_type: str
    description: str
    release_year: int | None
    genres: list[str] = field(default_factory=list)
    moods: list[str] = field(default_factory=list)
    source: str = "sample"
    external_id: str | None = None
    rating: float | None = None
    popularity: float | None = None
    language: str | None = None
