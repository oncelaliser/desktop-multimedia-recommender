from __future__ import annotations

from integrations.base_client import BaseApiClient


class OmdbClient(BaseApiClient):
    provider_name = "OMDb"
