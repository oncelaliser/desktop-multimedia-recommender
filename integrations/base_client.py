from __future__ import annotations

from abc import ABC


class BaseApiClient(ABC):
    provider_name: str
