from __future__ import annotations

from integrations.base_client import BaseApiClient


class TmdbClient(BaseApiClient):
    provider_name = "TMDB"
