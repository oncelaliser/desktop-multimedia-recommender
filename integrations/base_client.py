from __future__ import annotations

from abc import ABC, abstractmethod

from data.models.media_item import MediaItem


class BaseApiClient(ABC):
    provider_name: str

    @abstractmethod
    def search(self, query: str, **kwargs) -> list[MediaItem]:
        """Search for media items matching the given query."""
