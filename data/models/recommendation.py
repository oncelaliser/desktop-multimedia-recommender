from __future__ import annotations

from dataclasses import dataclass

from data.models.media_item import MediaItem


@dataclass(frozen=True)
class Recommendation:
    media: MediaItem
    score: float
    reason: str
