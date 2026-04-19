from __future__ import annotations

from data.models.media_item import MediaItem


class MediaRepository:
    """SQLite implementation will be added after the demo data model is approved."""

    def list_media(self) -> list[MediaItem]:
        raise NotImplementedError
